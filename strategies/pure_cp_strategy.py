"""
Stratégie CP Pure (Rigide)
Cohérence absolue, sacrifie disponibilité
"""

from typing import Dict
from models.node import Node
from services.transfer_service import TransferService
from services.balance_service import BalanceService
from services.history_service import HistoryService
from services.payment_service import PaymentService

class PureCPStrategy:
    """
    Stratégie CP stricte
    
    Caractéristiques:
    - Toutes opérations nécessitent master accessible
    - Timeouts courts
    - Aucune tolérance aux incohérences
    - Bloque tout en cas de partition
    """
    
    def __init__(self, transfer_service: TransferService,
                 balance_service: BalanceService,
                 history_service: HistoryService,
                 payment_service: PaymentService):
        self.transfer = transfer_service
        self.balance = balance_service
        self.history = history_service
        self.payment = payment_service
        
        print("[Strategy] Pure CP Strategy initialized")
    
    def execute_transfer(self, from_user: str, to_user: str, amount: float,
                        node: Node, master_node: Node, replica_nodes: list) -> Dict:
        """
        Transfert en mode CP strict
        Bloque si partition détectée
        """
        # Vérifier connectivité master
        if not node.can_reach_master(master_node):
            return {
                'success': False,
                'error': 'Service temporarily unavailable',
                'reason': 'Cannot reach master node (network partition)',
                'strategy': 'CP_STRICT'
            }
        
        # Exécuter transfert normal (CP strict)
        return self.transfer.transfer(
            from_user, to_user, amount,
            master_node, replica_nodes,
            strategy='CP'
        )
    
    def execute_balance_query(self, user_id: str, node: Node, 
                             master_node: Node) -> Dict:
        """
        Consultation solde en mode CP strict
        TOUJOURS lire depuis master
        """
        # Vérifier connectivité master
        if not node.can_reach_master(master_node):
            return {
                'success': False,
                'error': 'Service temporarily unavailable',
                'reason': 'Cannot reach master node',
                'strategy': 'CP_STRICT'
            }
        
        # Lire depuis master uniquement (CP)
        return self.balance.get_balance(
            user_id, node, master_node,
            strategy='CP'
        )

    def execute_history_query(self, user_id: str, node: Node,
                             master_node: Node) -> Dict:
        """
        Historique en mode CP strict
        Même l'historique nécessite master!
        """
        # Vérifier connectivité master
        if not node.can_reach_master(master_node):
            return {
                'success': False,
                'error': 'Service temporarily unavailable',
                'reason': 'Cannot reach master node',
                'strategy': 'CP_STRICT'
            }

        # En CP pur, même l'historique vient du master
        # (inefficace mais cohérent à 100%)
        return self.history.get_history(user_id, master_node)
    
    def execute_payment(self, user_id: str, provider: str, amount: float,
                       node: Node, master_node: Node, replica_nodes: list) -> Dict:
        """
        Paiement en mode CP strict
        """
        # Vérifier connectivité master
        if not node.can_reach_master(master_node):
            return {
                'success': False,
                'error': 'Service temporarily unavailable',
                'reason': 'Cannot reach master node',
                'strategy': 'CP_STRICT'
            }
        
        return self.payment.pay_bill(
            user_id, provider, amount,
            master_node, replica_nodes,
            strategy='CP'
        )
    
    def get_name(self) -> str:
        return "Pure CP (Strict Consistency)"
    
    def get_description(self) -> Dict:
        return {
            'name': self.get_name(),
            'consistency': 'Strong (100%)',
            'availability': 'Low during partition',
            'transfer': 'CP - Blocked if partition',
            'balance': 'CP - Master only',
            'history': 'CP - Master only',
            'payment': 'CP - Blocked if partition',
            'pros': [
                'Perfect consistency',
                'No data conflicts',
                'Regulatory compliant'
            ],
            'cons': [
                'Poor availability during partition',
                'High latency (always master)',
                'Bad user experience in unstable network'
            ]
        }