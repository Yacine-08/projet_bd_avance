
# noeud = serveur dans le système distribué

import time
import random
from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime

class NodeRole(Enum):
    # Rôles possibles d'un nœud
    MASTER = "master"
    REPLICA_RW = "replica_rw"  # Read-Write
    REPLICA_RO = "replica_ro"  # Read-Only
    REPLICA_ANALYTICS = "replica_analytics"

class NodeState(Enum):
    # États possibles d'un nœud
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ISOLATED = "isolated"  # Partition réseau
    DOWN = "down"

class Node:
    # Représente un serveur dans le système
    
    def __init__(self, node_id: str, name: str, role: NodeRole, location: tuple):
        self.id = node_id
        self.name = name
        self.role = role
        self.location = location
        self.state = NodeState.HEALTHY
        
        # Données locales (base de données simulée)
        self.accounts: Dict[str, float] = {}  # user_id -> balance
        self.transactions: List[Dict] = []
        self.cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        
        # Métriques
        self.last_heartbeat = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0
        
        # Partition tracking
        self.can_reach: Dict[str, bool] = {}  # node_id -> reachable
        
        print(f"[Node] {self.name} ({self.role.value}) initialized")
    
    def is_master(self) -> bool:
        # Vérifie si ce nœud est le master
        return self.role == NodeRole.MASTER
    
    def can_write(self) -> bool:
        # Vérifie si ce nœud peut effectuer des écritures
        return self.role in [NodeRole.MASTER, NodeRole.REPLICA_RW]
    
    def can_reach_master(self, master_node) -> bool:
        # Vérifie si ce nœud peut atteindre le master
        if self.is_master():
            return True
        
        return self.can_reach.get(master_node.id, True)
    
    def update_heartbeat(self):
        # Met à jour le timestamp du dernier heartbeat
        self.last_heartbeat = time.time()
    
    def is_healthy(self) -> bool:
        # Vérifie si le nœud est en bonne santé
        # Timeout après 3 secondes sans heartbeat
        if time.time() - self.last_heartbeat > 3:
            self.state = NodeState.ISOLATED
            return False
        return self.state == NodeState.HEALTHY
    
    def get_balance(self, user_id: str, from_cache: bool = False) -> Optional[float]:
        # Récupère le solde d'un utilisateur
        """
        Args:
            user_id: ID utilisateur
            from_cache: Si True, essayer cache d'abord
        
        Returns:
            Solde ou None si non trouvé
        """
        self.request_count += 1
        
        # Essayer cache d'abord 
        if from_cache:
            cached = self._get_from_cache(f"balance:{user_id}")
            if cached is not None:
                return cached
        
        # Sinon lire depuis base de données
        return self.accounts.get(user_id)
    
    def set_balance(self, user_id: str, balance: float):
        # Définir le solde d'un utilisateur
        self.accounts[user_id] = balance
        # Invalider cache
        self._invalidate_cache(f"balance:{user_id}")
    
    def add_transaction(self, transaction: Dict):
        # Ajouter une transaction à l'historique
        self.transactions.append({
            **transaction,
            'node_id': self.id,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_transactions(self, user_id: str, from_cache: bool = False) -> List[Dict]:
        # Récupérer l'historique des transactions d'un utilisateur
        self.request_count += 1
        
        if from_cache:
            cached = self._get_from_cache(f"history:{user_id}")
            if cached is not None:
                return cached
        
        # Filtrer transactions de l'utilisateur
        user_txs = [
            tx for tx in self.transactions
            if tx.get('from_user') == user_id or tx.get('to_user') == user_id
        ]
        
        return user_txs
    
    def _get_from_cache(self, key: str) -> Optional[any]:
        # Récupérer une valeur du cache
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                # Cache expiré
                del self.cache[key]
        return None
    
    def _set_cache(self, key: str, value: any, ttl: int):
        # Mettre en cache une valeur
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    def _invalidate_cache(self, key: str):
        # Invalider une entrée du cache
        if key in self.cache:
            del self.cache[key]
    
    def get_metrics(self) -> Dict:
        # Obtenir les métriques du nœud
        avg_latency = (self.total_latency / self.request_count 
                      if self.request_count > 0 else 0)
        
        error_rate = (self.error_count / self.request_count * 100 
                     if self.request_count > 0 else 0)
        
        return {
            'node_id': self.id,
            'name': self.name,
            'role': self.role.value,
            'state': self.state.value,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': error_rate,
            'avg_latency_ms': avg_latency,
            'cache_size': len(self.cache)
        }
    
    def __repr__(self):
        return f"Node({self.name}, {self.role.value}, {self.state.value})"