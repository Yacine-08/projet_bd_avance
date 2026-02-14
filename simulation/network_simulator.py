
import time
import random
from typing import Dict, Tuple, Optional
from config.network_config import NetworkConfig

class NetworkSimulator:
    # Simule les conditions réseau entre nœuds
    
    def __init__(self, network_mode: str = 'normal'):
        """
        Args:
            network_mode: 'normal', 'congested', ou 'partitioned'
        """
        self.mode = network_mode
        self.latencies = NetworkConfig.LATENCIES[network_mode]
        self.packet_loss = NetworkConfig.PACKET_LOSS[network_mode]
        
        # Historique des communications
        self.communication_log = []
        
        print(f"[Network] Initialized in {network_mode} mode")
    
    def set_mode(self, mode: str):
        # Changer le mode réseau
        self.mode = mode
        self.latencies = NetworkConfig.LATENCIES[mode]
        self.packet_loss = NetworkConfig.PACKET_LOSS[mode]
        print(f"[Network] Mode changed to {mode}")
    
    def send_message(self, from_node: str, to_node: str, 
                    message_type: str, payload: dict = None) -> Optional[Dict]:
        """
        Simule l'envoi d'un message entre nœuds
        
        Args:
            from_node: ID du nœud source
            to_node: ID du nœud destination
            message_type: Type de message (heartbeat, query, write, etc.)
            payload: Données du message
        
        Returns:
            Réponse si succès, None si échec
        """
        start_time = time.time()
        
        # Obtenir latence
        latency_ms = self._get_latency(from_node, to_node)
        
        # Vérifier si message perdu
        if self._is_packet_lost():
            self._log_communication(
                from_node, to_node, message_type, 
                success=False, latency_ms=0, 
                error="Packet lost"
            )
            return None
        
        # Simuler latence réseau
        try:
            time.sleep(latency_ms / 1000.0)
        except OverflowError:
            # Si timestamp out of range, utiliser une latence minimale
            time.sleep(0.001)
        
        # Message reçu
        actual_latency = (time.time() - start_time) * 1000  # en ms
        
        self._log_communication(
            from_node, to_node, message_type,
            success=True, latency_ms=actual_latency
        )
        
        # Retourner réponse simulée
        return {
            'status': 'success',
            'latency_ms': actual_latency,
            'payload': payload
        }
    
    def _get_latency(self, from_node: str, to_node: str) -> float:
    
        # Même nœud = pas de latence
        if from_node == to_node:
            return 0
        
        # Chercher latence configurée
        key1 = (from_node, to_node)
        key2 = (to_node, from_node)  # Bidirectionnel
        
        base_latency = self.latencies.get(key1, self.latencies.get(key2, 100))
        
        # Ajouter jitter (variation aléatoire ±20%)
        jitter = random.uniform(-0.2, 0.2)
        actual_latency = base_latency * (1 + jitter)
        
        return max(0, actual_latency)
    
    def _is_packet_lost(self) -> bool:
        return random.random() * 100 < self.packet_loss
    
    def _log_communication(self, from_node: str, to_node: str,
                          message_type: str, success: bool,
                          latency_ms: float, error: str = None):
        # Logger une communication
        log_entry = {
            'timestamp': time.time(),
            'from': from_node,
            'to': to_node,
            'type': message_type,
            'success': success,
            'latency_ms': latency_ms,
            'error': error
        }
        self.communication_log.append(log_entry)
    
    def get_statistics(self) -> Dict:
        # Obtenir statistiques du réseau
        if not self.communication_log:
            return {}
        
        total = len(self.communication_log)
        successful = sum(1 for log in self.communication_log if log['success'])
        failed = total - successful
        
        latencies = [log['latency_ms'] for log in self.communication_log 
                    if log['success']]
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0
        
        return {
            'total_messages': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'avg_latency_ms': avg_latency,
            'min_latency_ms': min_latency,
            'max_latency_ms': max_latency
        }
    
    def simulate_partition(self, node1: str, node2: str):
        # Simuler une partition réseau entre deux nœuds
        key1 = (node1, node2)
        key2 = (node2, node1)
        self.latencies[key1] = float('inf')
        self.latencies[key2] = float('inf')
        print(f"[Network] Partition créée entre {node1} et {node2}")
    
    def heal_partition(self, node1: str, node2: str):
        # Résoudre une partition réseau
        
        # Revenir aux latences normales
        normal_latencies = NetworkConfig.LATENCIES['normal']
        key1 = (node1, node2)
        key2 = (node2, node1)
        
        if key1 in normal_latencies:
            self.latencies[key1] = normal_latencies[key1]
        if key2 in normal_latencies:
            self.latencies[key2] = normal_latencies[key2]
        
        print(f"[Network] Partition résolue entre {node1} et {node2}")