import time
from typing import Dict, List
from models.node import Node
from simulation.network_simulator import NetworkSimulator
from config.network_config import NetworkConfig

class HistoryService:
    # Service de consultation de l'historique des transactions d'un utilisateur (AP)
    
    def __init__(self, network: NetworkSimulator):
        self.network = network
        self.query_count = 0
    
    def get_history(self, user_id: str, node: Node, limit: int = 50) -> Dict:
        """
        Récupérer l'historique des transactions
        
        Strategy: TOUJOURS AP (disponibilité prioritaire)
        
        Args:
            user_id: ID utilisateur
            node: Nœud local
            limit: Nombre max de transactions
        
        Returns:
            Historique des transactions
        """
        self.query_count += 1
        start_time = time.time()
        
        print(f"\n[History] Query history for {user_id} (AP strategy)")
        
        # Étape 1: Essayer cache
        print(f"[History]   Checking cache...")
        cached_history = node._get_from_cache(f"history:{user_id}")
        
        if cached_history is not None:
            latency = (time.time() - start_time) * 1000
            print(f"[History]   Cache HIT: {len(cached_history)} transactions ({latency:.0f}ms)")
            
            return {
                'success': True,
                'transactions': cached_history[:limit],
                'count': len(cached_history),
                'source': 'cache',
                'latency_ms': latency
            }
        
        print(f"[History]   Cache MISS")
        
        # Étape 2: Lire depuis replica local
        print(f"[History]   Reading from local replica {node.name}...")
        
        # Simuler latence lecture (historique = données volumineuses)
        time.sleep(0.15)  
        
        transactions = node.get_transactions(user_id, from_cache=False)
        
        latency = (time.time() - start_time) * 1000
        
        if transactions:
            # Mettre en cache
            node._set_cache(f"history:{user_id}", transactions,
                          NetworkConfig.CACHE_TTL['history'])
            
            print(f"[History]   Found {len(transactions)} transactions ({latency:.0f}ms)")
            
            return {
                'success': True,
                'transactions': transactions[:limit],
                'count': len(transactions),
                'source': 'replica_local',
                'latency_ms': latency,
                'warning': 'Les transactions très récentes peuvent ne pas apparaître'
            }
        else:
            print(f"[History]   No transactions found ({latency:.0f}ms)")
            
            return {
                'success': True,
                'transactions': [],
                'count': 0,
                'source': 'replica_local',
                'latency_ms': latency
            }
    
    def get_statistics(self) -> Dict:
        return {
            'total_queries': self.query_count
        }