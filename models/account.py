#   Modèle de compte utilisateur

from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Account:
    # Compte utilisateur Wave
    user_id: str
    phone: str
    name: str
    balance: float
    currency: str = "XOF"
    created_at: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self):
        # Convertir en dictionnaire
        return {
            'user_id': self.user_id,
            'phone': self.phone,
            'name': self.name,
            'balance': self.balance,
            'currency': self.currency,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        # Créer depuis un dictionnaire
        return cls(
            user_id=data['user_id'],
            phone=data['phone'],
            name=data['name'],
            balance=data['balance'],
            currency=data.get('currency', 'XOF'),
            created_at=datetime.fromisoformat(data['created_at']),
            is_active=data.get('is_active', True)
        )