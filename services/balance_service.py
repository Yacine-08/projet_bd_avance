import time
from typing import Dict, Optional
from models.node import Node
from simulation.network_simulator import NetworkSimulator
from config.network_config import NetworkConfig

class BalanceService:
    # Service de consultation de solde avec deux stratégies: AP (disponibilité) et CP (cohérence)
    def __init__(self, network: NetworkSimulator):
        self.network = network
        self.query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_balance(self, user_id: str, node: Node, 
                   master_node: Node = None,
                   strategy: str = 'AP') -> Dict:
        """
        Consulter le solde d'un utilisateur
        
        Args:
            user_id: ID utilisateur
            node: Nœud utilisé pour la requête
            master_node: Nœud master (pour stratégie CP)
            strategy: 'AP' (cache/replica) ou 'CP' (master strict)
        
        Returns:
            Résultat avec solde
        """
        self.query_count += 1
        start_time = time.time()
        
        print(f"\n[Balance] Query balance for {user_id} (strategy: {strategy})")
        
        if strategy == 'AP':
            # Stratégie AP: Cache puis replica local
            return self._get_balance_ap(user_id, node, start_time)
        else:
            # Stratégie CP: Lire depuis master
            return self._get_balance_cp(user_id, node, master_node, start_time)
    
    def _get_balance_ap(self, user_id: str, node: Node, start_time: float) -> Dict:
        # Stratégie AP: Disponibilité prioritaire
        
        # Essayer cache
        print(f"[Balance]   Checking cache...")
        balance = node.get_balance(user_id, from_cache=True)
        
        if balance is not None:
            self.cache_hits += 1
            latency = (time.time() - start_time) * 1000
            
            print(f"[Balance]   ✓ Cache HIT: {balance} FCFA ({latency:.0f}ms)")
            
            return {
                'success': True,
                'balance': balance,
                'source': 'cache',
                'latency_ms': latency,
                'freshness': 'cached'
            }
        
        self.cache_misses += 1
        print(f"[Balance]   ✗ Cache MISS")
        
        # Lire depuis replica local
        print(f"[Balance]  Reading from local replica {node.name}...")
        
        # Simuler latence lecture DB
        time.sleep(0.05)  # 50ms
        
        balance = node.get_balance(user_id, from_cache=False)
        
        if balance is not None:
            latency = (time.time() - start_time) * 1000
            
            # Mettre en cache pour prochaine fois
            node._set_cache(f"balance:{user_id}", balance, 
                          NetworkConfig.CACHE_TTL['balance'])
            
            print(f"[Balance]   Replica read: {balance} FCFA ({latency:.0f}ms)")
            
            return {
                'success': True,
                'balance': balance,
                'source': 'replica_local',
                'latency_ms': latency,
                'freshness': 'recent',
                'warning': 'Données peuvent avoir quelques secondes de retard'
            }
        
        # Échec total
        latency = (time.time() - start_time) * 1000
        print(f"[Balance]   Account not found ({latency:.0f}ms)")
        
        return {
            'success': False,
            'error': 'Account not found',
            'latency_ms': latency
        }
    
    def _get_balance_cp(self, user_id: str, node: Node, 
                       master_node: Node, start_time: float) -> Dict:
        # Stratégie CP: Cohérence prioritaire
        
        if master_node is None:
            return {
                'success': False,
                'error': 'Master node required for CP strategy'
            }
        
        print(f"[Balance]   Reading from MASTER {master_node.name}...")
        
        # Vérifier connectivité au master
        if not node.can_reach_master(master_node):
            latency = (time.time() - start_time) * 1000
            print(f"[Balance]   Cannot reach master (partition?) ({latency:.0f}ms)")
            
            return {
                'success': False,
                'error': 'Service temporarily unavailable',
                'reason': 'Cannot reach master node',
                'latency_ms': latency
            }
        
        # Simuler communication vers master
        response = self.network.send_message(
            from_node=node.id,
            to_node=master_node.id,
            message_type='balance_query',
            payload={'user_id': user_id}
        )
        
        if response is None:
            latency = (time.time() - start_time) * 1000
            print(f"[Balance]   Master unreachable ({latency:.0f}ms)")
            
            return {
                'success': False,
                'error': 'Service temporarily unavailable',
                'latency_ms': latency
            }
        
        # Lire depuis master
        time.sleep(0.05)
        balance = master_node.get_balance(user_id, from_cache=False)
        
        latency = (time.time() - start_time) * 1000
        
        if balance is not None:
            print(f"[Balance]   Master read: {balance} FCFA ({latency:.0f}ms)")
            
            return {
                'success': True,
                'balance': balance,
                'source': 'master',
                'latency_ms': latency,
                'freshness': 'guaranteed_accurate'
            }
        else:
            print(f"[Balance]   Account not found ({latency:.0f}ms)")
            
            return {
                'success': False,
                'error': 'Account not found',
                'latency_ms': latency
            }
    
    def get_statistics(self) -> Dict:

        cache_hit_rate = (self.cache_hits / self.query_count * 100 
                         if self.query_count > 0 else 0)
        
        return {
            'total_queries': self.query_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': cache_hit_rate
        }