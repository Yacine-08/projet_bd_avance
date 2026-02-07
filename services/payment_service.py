
import time
import uuid
from typing import Dict
from models.transaction import Transaction, TransactionType
from models.node import Node
from simulation.network_simulator import NetworkSimulator
from config.network_config import NetworkConfig

class PaymentService:
    # Service de paiement de factures avec deux stratégies: CP (cohérence) et ADAPTIVE (adaptative)
    
    def __init__(self, network: NetworkSimulator):
        self.network = network
        self.payment_count = 0
        self.success_count = 0
        self.failed_count = 0
    
    def pay_bill(self, user_id: str, provider: str, amount: float,
                master_node: Node, replica_nodes: list,
                strategy: str = 'CP') -> Dict:
        """
        Payer une facture
        
        Args:
            user_id: ID utilisateur
            provider: Fournisseur (SENELEC, SENEAU, etc.)
            amount: Montant
            master_node: Nœud master
            replica_nodes: Replicas
            strategy: 'CP' (strict) ou 'ADAPTIVE'
        
        Returns:
            Résultat du paiement
        """
        self.payment_count += 1
        
        tx_id = f"PAY_{uuid.uuid4().hex[:8]}"
        transaction = Transaction(
            transaction_id=tx_id,
            type=TransactionType.PAYMENT,
            from_user=user_id,
            to_user=provider,
            amount=amount,
            metadata={'provider': provider}
        )
        
        print(f"\n[Payment] Starting {tx_id}: {user_id} → {provider} : {amount} FCFA")
        
        start_time = time.time()
        
        try:
            # Vérifier solde
            balance = master_node.get_balance(user_id)
            if balance is None or balance < amount:
                return self._fail_payment(transaction, "Insufficient balance", start_time)
            
            if strategy == 'CP':
                return self._pay_bill_cp_strict(transaction, master_node, replica_nodes, start_time)
            else:
                return self._pay_bill_adaptive(transaction, master_node, replica_nodes, start_time)
        
        except Exception as e:
            return self._fail_payment(transaction, str(e), start_time)
    
    def _pay_bill_cp_strict(self, transaction: Transaction, master_node: Node,
                           replica_nodes: list, start_time: float) -> Dict:
        # Stratégie CP stricte: tout doit réussir
        
        print(f"[Payment]   Strategy: CP STRICT")
        
        # Débiter utilisateur
        balance = master_node.get_balance(transaction.from_user)
        master_node.set_balance(transaction.from_user, balance - transaction.amount)
        print(f"[Payment]   User debited: {balance} → {balance - transaction.amount}")
        
        # Notifier fournisseur 
        print(f"[Payment]   Notifying provider {transaction.to_user}...")
        
        # Simuler appel API externe 
        provider_response = self._call_provider_api(transaction)
        
        if not provider_response['success']:
            # ROLLBACK
            master_node.set_balance(transaction.from_user, balance)
            print(f"[Payment]   Provider API failed, ROLLBACK")
            return self._fail_payment(transaction, "Provider API failed", start_time)
        
        print(f"[Payment]   Provider confirmed: {provider_response['receipt_id']}")
        
        # Logger transaction
        master_node.add_transaction(transaction.to_dict())
        
        # Réplication
        for node in replica_nodes:
            response = self.network.send_message(
                from_node=master_node.id,
                to_node=node.id,
                message_type='payment_replicate',
                payload=transaction.to_dict()
            )
            
            if response:
                node.set_balance(transaction.from_user, 
                               node.get_balance(transaction.from_user) - transaction.amount)
                node.add_transaction(transaction.to_dict())
        
        latency = (time.time() - start_time) * 1000
        transaction.mark_committed()
        self.success_count += 1
        
        print(f"[Payment] {transaction.transaction_id} COMMITTED ({latency:.0f}ms)")
        
        return {
            'success': True,
            'transaction_id': transaction.transaction_id,
            'receipt_id': provider_response['receipt_id'],
            'latency_ms': latency,
            'new_balance': master_node.get_balance(transaction.from_user)
        }
    
    def _pay_bill_adaptive(self, transaction: Transaction, master_node: Node,
                          replica_nodes: list, start_time: float) -> Dict:
        # Stratégie adaptative: queue si petit montant
        
        print(f"[Payment]   Strategy: ADAPTIVE")
        
        # Si petit montant (<5000), utiliser queue
        if transaction.amount < 5000:
            print(f"[Payment]   Small amount → QUEUE mode")
            
            # Débiter immédiatement
            balance = master_node.get_balance(transaction.from_user)
            master_node.set_balance(transaction.from_user, balance - transaction.amount)
            
            # Notifier en asynchrone
            print(f"[Payment]   Queuing provider notification...")
            
            latency = (time.time() - start_time) * 1000
            transaction.metadata['queued'] = True
            transaction.mark_committed()
            self.success_count += 1
            
            print(f"[Payment] {transaction.transaction_id} QUEUED ({latency:.0f}ms)")
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'status': 'pending',
                'message': 'Paiement en cours de traitement (2-5 minutes)',
                'latency_ms': latency,
                'new_balance': master_node.get_balance(transaction.from_user)
            }
        else:
            # Gros montant → CP strict
            print(f"[Payment]   Large amount → CP STRICT mode")
            return self._pay_bill_cp_strict(transaction, master_node, replica_nodes, start_time)
    
    def _call_provider_api(self, transaction: Transaction) -> Dict:
        # Simuler appel API fournisseur externe
        
        # Simuler latence API externe (2-3 secondes)
        api_latency = 2.0 + (1.0 * (hash(transaction.transaction_id) % 10) / 10)
        time.sleep(api_latency)
        
        # Simuler succès/échec (95% succès)
        import random
        success = random.random() > 0.05
        
        if success:
            return {
                'success': True,
                'receipt_id': f"RCPT_{uuid.uuid4().hex[:8]}",
                'latency_ms': api_latency * 1000
            }
        else:
            return {
                'success': False,
                'error': 'Provider timeout',
                'latency_ms': api_latency * 1000
            }
    
    def _fail_payment(self, transaction: Transaction, reason: str, 
                     start_time: float) -> Dict:
        
        latency = (time.time() - start_time) * 1000
        transaction.mark_failed(reason)
        self.failed_count += 1
        
        print(f"[Payment] {transaction.transaction_id} FAILED: {reason} ({latency:.0f}ms)")
        
        return {
            'success': False,
            'transaction_id': transaction.transaction_id,
            'error': reason,
            'latency_ms': latency
        }
    
    def get_statistics(self) -> Dict:

        success_rate = (self.success_count / self.payment_count * 100
                       if self.payment_count > 0 else 0)
        
        return {
            'total_payments': self.payment_count,
            'successful': self.success_count,
            'failed': self.failed_count,
            'success_rate': success_rate
        }