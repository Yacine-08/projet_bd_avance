
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import time
from typing import Optional

class TransactionType(Enum):
    # Types de transaction
    TRANSFER = "transfer"
    PAYMENT = "payment"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class TransactionStatus(Enum):
    # Statuts de transaction
    PENDING = "pending"
    PREPARED = "prepared"  # Phase 1 du 2PC
    COMMITTED = "committed"
    ABORTED = "aborted"
    FAILED = "failed"

@dataclass
class Transaction:
    transaction_id: str
    type: TransactionType
    from_user: str
    to_user: Optional[str]
    amount: float
    currency: str = "XOF"
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.created_at is None:
            # Use a safer timestamp approach
            try:
                self.created_at = datetime.fromtimestamp(time.time())
            except (OSError, OverflowError):
                # Fallback for platform-specific timestamp issues
                self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self):
        completed_at_str = None
        if self.completed_at:
            try:
                completed_at_str = self.completed_at.isoformat()
            except Exception as e:
                completed_at_str = str(self.completed_at)
        
        return {
            'transaction_id': self.transaction_id,
            'type': self.type.value,
            'from_user': self.from_user,
            'to_user': self.to_user,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': completed_at_str,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
    
    def mark_prepared(self):
        # Marquer comme préparé (phase 1 du 2PC)
        self.status = TransactionStatus.PREPARED
    
    def mark_committed(self):
        # Marquer comme commité
        self.status = TransactionStatus.COMMITTED
        try:
            self.completed_at = datetime.fromtimestamp(time.time())
        except (OSError, OverflowError):
            self.completed_at = datetime.now()
    
    def mark_aborted(self, reason: str):
        # Marquer comme abort
        self.status = TransactionStatus.ABORTED
        self.error_message = reason
        try:
            self.completed_at = datetime.fromtimestamp(time.time())
        except (OSError, OverflowError):
            self.completed_at = datetime.now()
    
    def mark_failed(self, error: str):
        # Marquer comme failed
        self.status = TransactionStatus.FAILED
        self.error_message = error
        try:
            self.completed_at = datetime.fromtimestamp(time.time())
        except (OSError, OverflowError):
            self.completed_at = datetime.now()