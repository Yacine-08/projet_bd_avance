
import time
import uuid
from typing import Dict, Optional
from models.transaction import Transaction, TransactionType, TransactionStatus
from models.node import Node
from simulation.network_simulator import NetworkSimulator
from config.network_config import NetworkConfig

class TransferService:
    # Gère les transferts P2P avec protocole 2PC
    
    def __init__(self, network: NetworkSimulator):
        self.network = network
        self.pending_transactions = {}
        self.committed_transactions = {}
        self.aborted_transactions = {}
        
    def transfer(self, from_user: str, to_user: str, amount: float,
                master_node: Node, replica_nodes: list,
                strategy: str = 'CP') -> Dict:
        """
        Effectue un transfert d'argent
        
        Args:
            from_user: ID utilisateur source
            to_user: ID utilisateur destination
            amount: Montant
            master_node: Nœud master
            replica_nodes: Liste des nœuds replicas
            strategy: 'CP' (strict) ou 'ADAPTIVE'
        
        Returns:
            Résultat de la transaction
        """
        # Créer transaction
        tx_id = f"TX_{uuid.uuid4().hex[:8]}"
        transaction = Transaction(
            transaction_id=tx_id,
            type=TransactionType.TRANSFER,
            from_user=from_user,
            to_user=to_user,
            amount=amount
        )
        
        print(f"\n[Transfer] Starting {tx_id}: {from_user} → {to_user} : {amount} FCFA")
        
        start_time = time.time()
        
        try:
            # PHASE 0: Vérifications préliminaires
            if not self._pre_checks(transaction, master_node):
                return self._abort_transaction(transaction, "Pre-checks failed")
            
            # PHASE 1: PREPARE (2PC)
            if not self._prepare_phase(transaction, master_node, replica_nodes):
                return self._abort_transaction(transaction, "Prepare phase failed")
            
            # PHASE 2: COMMIT (2PC)
            if not self._commit_phase(transaction, master_node, replica_nodes):
                return self._abort_transaction(transaction, "Commit phase failed")
            
            # Succès
            latency = (time.time() - start_time) * 1000
            transaction.mark_committed()
            self.committed_transactions[tx_id] = transaction
            
            print(f"[Transfer] ✓ {tx_id} COMMITTED in {latency:.0f}ms")
            
            return {
                'success': True,
                'transaction_id': tx_id,
                'latency_ms': latency,
                'new_balance_from': master_node.get_balance(from_user),
                'new_balance_to': master_node.get_balance(to_user)
            }
            
        except TimeoutError as e:
            return self._abort_transaction(transaction, f"Timeout: {str(e)}")
        except Exception as e:
            return self._abort_transaction(transaction, f"Error: {str(e)}")
    
    def _pre_checks(self, transaction: Transaction, master_node: Node) -> bool:

        # Vérifier solde suffisant
        balance = master_node.get_balance(transaction.from_user)
        
        if balance is None:
            print(f"[Transfer] ✗ Account {transaction.from_user} not found")
            return False
        
        if balance < transaction.amount:
            print(f"[Transfer] ✗ Insufficient balance: {balance} < {transaction.amount}")
            return False
        
        # Vérifier que destinataire existe
        to_balance = master_node.get_balance(transaction.to_user)
        if to_balance is None:
            print(f"[Transfer] ✗ Destination account {transaction.to_user} not found")
            return False
        
        print(f"[Transfer] ✓ Pre-checks passed")
        return True
    
    def _prepare_phase(self, transaction: Transaction, 
                      master_node: Node, replica_nodes: list) -> bool:
     
        print(f"[Transfer] PHASE 1: PREPARE")
        
        tx_id = transaction.transaction_id
        timeout = NetworkConfig.TIMEOUTS['transfer'] / 1000.0  # en secondes
        start_time = time.time()
        
        # Liste des participants
        participants = [master_node] + replica_nodes
        votes = {}
        
        for node in participants:
            # Timeout check
            if time.time() - start_time > timeout:
                print(f"[Transfer] ✗ PREPARE timeout after {timeout}s")
                raise TimeoutError("Prepare phase timeout")
            
            # Envoyer PREPARE
            print(f"[Transfer]   → Sending PREPARE to {node.name}")
            
            # Simuler communication réseau
            response = self.network.send_message(
                from_node=master_node.id,
                to_node=node.id,
                message_type='prepare',
                payload={'transaction_id': tx_id}
            )
            
            if response is None:
                # Communication échouée
                print(f"[Transfer]   {node.name} unreachable")
                votes[node.id] = 'NO'
            else:
                # Vérifier si nœud peut participer
                can_prepare = self._can_node_prepare(node, transaction)
                votes[node.id] = 'YES' if can_prepare else 'NO'
                
                status = '✓' if can_prepare else '✗'
                print(f"[Transfer]   {status} {node.name} voted {votes[node.id]}")
        
        # Vérifier votes
        all_yes = all(vote == 'YES' for vote in votes.values())
        
        if all_yes:
            transaction.mark_prepared()
            print(f"[Transfer] PREPARE successful (all voted YES)")
            return True
        else:
            no_voters = [nid for nid, vote in votes.items() if vote == 'NO']
            print(f"[Transfer] ✗ PREPARE failed (NO votes from: {no_voters})")
            return False
    
    def _can_node_prepare(self, node: Node, transaction: Transaction) -> bool:
        # Vérifie si un nœud peut participer au PREPARE

        # Vérifier que le nœud est sain
        if not node.is_healthy():
            return False
        
        # Si c'est le master, vérifier le solde
        if node.is_master():
            balance = node.get_balance(transaction.from_user)
            return balance >= transaction.amount
        
        # Les replicas peuvent toujours préparer
        return True
    
    def _commit_phase(self, transaction: Transaction,
                     master_node: Node, replica_nodes: list) -> bool:
        
        print(f"[Transfer] PHASE 2: COMMIT")
        
        tx_id = transaction.transaction_id
        timeout = NetworkConfig.TIMEOUTS['transfer'] / 1000.0
        start_time = time.time()
        
        participants = [master_node] + replica_nodes
        
        # Effectuer les modifications sur master d'abord
        from_balance = master_node.get_balance(transaction.from_user)
        to_balance = master_node.get_balance(transaction.to_user)
        
        master_node.set_balance(transaction.from_user, from_balance - transaction.amount)
        master_node.set_balance(transaction.to_user, to_balance + transaction.amount)
        master_node.add_transaction(transaction.to_dict())
        
        print(f"[Transfer]     MASTER committed")
        print(f"[Transfer]     {transaction.from_user}: {from_balance} → {from_balance - transaction.amount}")
        print(f"[Transfer]     {transaction.to_user}: {to_balance} → {to_balance + transaction.amount}")
        
        # Répliquer vers les replicas
        for node in replica_nodes:
            if time.time() - start_time > timeout:
                print(f"[Transfer]  COMMIT timeout, but master committed (eventual consistency)")
                return True  # Master déjà commité
            
            print(f"[Transfer]   Sending COMMIT to {node.name}")
            
            response = self.network.send_message(
                from_node=master_node.id,
                to_node=node.id,
                message_type='commit',
                payload={
                    'transaction_id': tx_id,
                    'from_user': transaction.from_user,
                    'to_user': transaction.to_user,
                    'amount': transaction.amount
                }
            )
            
            if response:
                # Appliquer sur replica
                from_bal = node.get_balance(transaction.from_user) or from_balance
                to_bal = node.get_balance(transaction.to_user) or to_balance
                
                node.set_balance(transaction.from_user, from_bal - transaction.amount)
                node.set_balance(transaction.to_user, to_bal + transaction.amount)
                node.add_transaction(transaction.to_dict())
                
                print(f"[Transfer]   {node.name} committed")
            else:
                print(f"[Transfer]   {node.name} unreachable (will sync later)")
        
        return True
    
    def _abort_transaction(self, transaction: Transaction, reason: str) -> Dict:
        transaction.mark_aborted(reason)
        self.aborted_transactions[transaction.transaction_id] = transaction
        
        print(f"[Transfer] {transaction.transaction_id} ABORTED: {reason}")
        
        return {
            'success': False,
            'transaction_id': transaction.transaction_id,
            'error': reason
        }
    
    def get_statistics(self) -> Dict:
        total = len(self.committed_transactions) + len(self.aborted_transactions)
        success = len(self.committed_transactions)
        failed = len(self.aborted_transactions)
        
        return {
            'total_transfers': total,
            'successful': success,
            'aborted': failed,
            'success_rate': (success / total * 100) if total > 0 else 0
        }