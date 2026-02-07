"""
Simulateur de partition réseau
"""

import time
from typing import List, Dict
from models.node import Node, NodeState
from simulation.network_simulator import NetworkSimulator

class PartitionSimulator:
    """Simule des partitions réseau entre nœuds"""
    
    def __init__(self, network: NetworkSimulator, nodes: List[Node]):
        self.network = network
        self.nodes = {node.id: node for node in nodes}
        self.partition_active = False
        self.partition_start_time = None
        
        print("[PartitionSim] Initialized")
    
    def create_partition(self, node1_id: str, node2_id: str):
        """
        Créer une partition entre deux nœuds
        """
        print(f"\n{'='*60}")
        print(f"[PartitionSim] Creating partition between {node1_id} and {node2_id}")
        print(f"{'='*60}")
        
        # Modifier réseau
        self.network.simulate_partition(node1_id, node2_id)
        
        # Mettre à jour états des nœuds
        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]
        
        node1.can_reach[node2_id] = False
        node2.can_reach[node1_id] = False
        
        node1.state = NodeState.ISOLATED
        node2.state = NodeState.ISOLATED
        
        self.partition_active = True
        self.partition_start_time = time.time()
        
        print(f"[PartitionSim] ⚠️ {node1_id} and {node2_id} are now ISOLATED")
        print(f"{'='*60}\n")
    
    def heal_partition(self, node1_id: str, node2_id: str):
        """
        Résoudre une partition
        """
        print(f"\n{'='*60}")
        print(f"[PartitionSim] Healing partition between {node1_id} and {node2_id}")
        print(f"{'='*60}")
        
        # Restaurer réseau
        self.network.heal_partition(node1_id, node2_id)
        
        # Mettre à jour états
        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]
        
        node1.can_reach[node2_id] = True
        node2.can_reach[node1_id] = True
        
        node1.state = NodeState.HEALTHY
        node2.state = NodeState.HEALTHY
        
        self.partition_active = False
        
        duration = time.time() - self.partition_start_time if self.partition_start_time else 0
        
        print(f"[PartitionSim] ✓ Partition healed after {duration:.1f} seconds")
        print(f"[PartitionSim] Starting synchronization...")
        
        # Simuler sync
        self._synchronize_nodes(node1, node2)
        
        print(f"[PartitionSim] ✓ Nodes synchronized")
        print(f"{'='*60}\n")
    
    def _synchronize_nodes(self, node1: Node, node2: Node):
        """Synchroniser données entre nœuds après partition"""
        # Simuler délai de sync
        time.sleep(0.5)
        
        # En réalité, on synchroniserait les données
        # Ici, on simule juste
        print(f"[PartitionSim]   Syncing accounts...")
        print(f"[PartitionSim]   Syncing transactions...")
        print(f"[PartitionSim]   Invalidating caches...")
    
    def simulate_partition_scenario(self, node1_id: str, node2_id: str,
                                    duration_seconds: float = 10):
        """
        Simuler un scénario complet de partition
        
        Args:
            node1_id: Premier nœud
            node2_id: Deuxième nœud
            duration_seconds: Durée de la partition
        """
        print(f"\n[PartitionSim] Starting partition scenario")
        print(f"[PartitionSim] Duration: {duration_seconds} seconds")
        
        # Créer partition
        self.create_partition(node1_id, node2_id)
        
        # Attendre
        print(f"[PartitionSim] Waiting {duration_seconds}s...")
        time.sleep(duration_seconds)
        
        # Résoudre partition
        self.heal_partition(node1_id, node2_id)
        
        print(f"[PartitionSim] Scenario complete\n")