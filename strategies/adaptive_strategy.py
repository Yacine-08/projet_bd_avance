"""
Stratégie Adaptative (Réaliste)
Balance intelligemment entre C et A selon le contexte
"""

import time
from typing import Dict
from models.node import Node
from services.transfer_service import TransferService
from services.balance_service import BalanceService
from services.history_service import HistoryService
from services.payment_service import PaymentService

class AdaptiveStrategy:
    """
    Stratégie adaptative intelligente
    
    Caractéristiques:
    - Opérations critiques: CP (transferts, gros paiements)
    - Opérations consultatives: AP (solde, historique)
    - Paiements: Adaptatif selon montant
    - Graceful degradation durant partition
    """
    
    def __init__(self, transfer_service: TransferService,
                 balance_service: BalanceService,
                 history_service: HistoryService,
                 payment_service: PaymentService):
        self.transfer = transfer_service
        self.balance = balance_service
        self.history = history_service
        self.payment = payment_service
        
        print("[Strategy] Adaptive Strategy initialized")
    
    def execute_transfer(self, from_user: str, to_user: str, amount: float,
                        node: Node, master_node: Node, replica_nodes: list) -> Dict:
        """
        Transfert: TOUJOURS CP (cohérence critique)
        Mais message utilisateur amélioré
        """
        # Vérifier connectivité master
        if not node.can_reach_master(master_node):
            return {
                'success': False,
                'error': 'Transferts temporairement indisponibles',
                'reason': 'Problème de connexion réseau détecté',
                'message': (
                    'Pour votre sécurité, les transferts sont temporairement suspendus.\n'
                    'Vous pouvez toujours consulter votre solde et historique.\n'
                    'Réessayez dans quelques minutes.'
                ),
                'available_actions': ['consulter_solde', 'voir_historique'],
                'strategy': 'ADAPTIVE_CP'
            }

        # Exécuter transfert (CP strict)
        return self.transfer.transfer(
            from_user, to_user, amount,
            master_node, replica_nodes,
            strategy='CP'
        )

    def execute_balance_query(self, user_id: str, node: Node,
                             master_node: Node, context: str = 'display') -> Dict:
        """
        Consultation solde: AP ou CP selon contexte

        Args:
            context: 'display' (AP) ou 'pre_transfer' (CP)
        """
        if context == 'pre_transfer':
            # Avant transfert: nécessite exactitude (CP)
            if not node.can_reach_master(master_node):
                return {
                    'success': False,
                    'error': 'Cannot verify balance',
                    'strategy': 'ADAPTIVE_CP'
                }

            return self.balance.get_balance(
                user_id, node, master_node,
                strategy='CP'
            )
        else:
            # Simple affichage: AP (cache/replica local)
            # Fonctionne même en partition!
            result = self.balance.get_balance(
                user_id, node, master_node,
                strategy='AP'
            )

            # Ajouter indication si partition
            if not node.can_reach_master(master_node):
                result['warning'] = (
                    'Données locales affichées. '
                    'Peuvent avoir quelques minutes de retard.'
                )
                result['partition_mode'] = True

            return result

    def execute_history_query(self, user_id: str, node: Node,
                             master_node: Node) -> Dict:
        """
        Historique: TOUJOURS AP (disponibilité prioritaire)
        Fonctionne même en partition
        """
        # Lire depuis replica local (AP)
        result = self.history.get_history(user_id, node)

        # Indiquer mode partition si applicable
        if not node.can_reach_master(master_node):
            result['warning'] = (
                'Mode dégradé: transactions récentes peuvent ne pas apparaître'
            )
            result['partition_mode'] = True

        return result

    def execute_payment(self, user_id: str, provider: str, amount: float,
                       node: Node, master_node: Node, replica_nodes: list) -> Dict:
        """
        Paiement: Adaptatif selon montant
        - Petit montant (<5000): Queue (AP toléré) - fonctionne même en partition
        - Gros montant: CP strict
        """
        # Vérifier connectivité master
        if not node.can_reach_master(master_node):
            if amount < 5000:
                # Petit montant: mettre en queue locale (AP)
                # Simuler queue - fonctionnera même en partition
                return {
                    'success': True,
                    'transaction_id': f'queue_{int(time.time())}',
                    'status': 'queued',
                    'message': f'Paiement de {amount} FCFA mis en file d\'attente',
                    'warning': 'Traitement différé jusqu\'à reconnexion réseau',
                    'partition_mode': True,
                    'strategy': 'ADAPTIVE_AP_QUEUE'
                }
            else:
                # Gros montant: impossible sans master
                return {
                    'success': False,
                    'error': 'Paiements gros montants temporairement indisponibles',
                    'reason': 'Problème de connexion réseau',
                    'message': (
                        f'Les paiements >=5000 FCFA nécessitent une connexion sécurisée.\n'
                        'Vous pouvez effectuer des paiements plus petits en attendant.'
                    ),
                    'strategy': 'ADAPTIVE'
                }

        # Utiliser stratégie adaptative (master disponible)
        return self.payment.pay_bill(
            user_id, provider, amount,
            master_node, replica_nodes,
            strategy='ADAPTIVE'
        )
    
    def get_name(self) -> str:
        return "Adaptive (Smart Balance)"
    
    def get_description(self) -> Dict:
        return {
            'name': self.get_name(),
            'consistency': 'Strong for writes, Eventual for reads',
            'availability': 'High (70%+ during partition)',
            'transfer': 'CP - Blocked if partition (safety)',
            'balance': 'AP - Local replica (display) | CP - Master (verification)',
            'history': 'AP - Always available from local',
            'payment': 'Adaptive - Queue if <5000, CP if >=5000',
            'pros': [
                'Best user experience',
                'High availability for consultations',
                'Safe for critical operations',
                'Graceful degradation'
            ],
            'cons': [
                'Slightly complex logic',
                'Eventual consistency for some data',
                'User needs to understand warnings'
            ]
        }