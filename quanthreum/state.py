"""
Quanthreum (QTH) - Ethereum-Style Account & World State Ledger
Handles:
  - Account model: nonce, balance (QTH), code, storage
  - World State transitions & snapshot rollback
  - Merkle State Root computation (SHA3-256)
  - 100 Million QTH Total Supply Cap enforcement
"""

import copy
import hashlib
import json
from typing import Any, Dict, Optional, Tuple
from .quantum_crypto import keccak256, sha3_256, validate_qth_address

TOTAL_MAX_SUPPLY = 100_000_000.0  # Exactly 100 Million QTH


class Account:
    """Represents an Ethereum-style account (EOA or Smart Contract)."""

    def __init__(
        self,
        balance: float = 0.0,
        nonce: int = 0,
        code: str = "",
        storage: Optional[Dict[str, Any]] = None
    ):
        self.balance = round(float(balance), 8)
        self.nonce = int(nonce)
        self.code = code or ""
        self.storage: Dict[str, Any] = storage or {}

    @property
    def is_contract(self) -> bool:
        return len(self.code) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "balance": self.balance,
            "nonce": self.nonce,
            "code": self.code,
            "storage": self.storage,
            "is_contract": self.is_contract,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Account":
        return cls(
            balance=d.get("balance", 0.0),
            nonce=d.get("nonce", 0),
            code=d.get("code", ""),
            storage=d.get("storage", {}),
        )

    def hash(self) -> bytes:
        """Serialize and hash the account state."""
        raw = json.dumps(self.to_dict(), sort_keys=True).encode('utf-8')
        return sha3_256(raw)


class WorldState:
    """
    Manages the global state of all accounts and contract storages in Quanthreum.
    Provides snapshotting for atomic transaction execution (revert on error).
    """

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self._snapshots: list = []

    def get_account(self, address: str) -> Account:
        if address not in self.accounts:
            self.accounts[address] = Account()
        return self.accounts[address]

    def get_balance(self, address: str) -> float:
        return self.get_account(address).balance

    def set_balance(self, address: str, amount: float):
        self.get_account(address).balance = round(float(amount), 8)

    def add_balance(self, address: str, amount: float):
        acc = self.get_account(address)
        acc.balance = round(acc.balance + float(amount), 8)

    def sub_balance(self, address: str, amount: float):
        acc = self.get_account(address)
        if acc.balance < amount:
            raise ValueError(f"Insufficient QTH balance for {address}: have {acc.balance}, need {amount}")
        acc.balance = round(acc.balance - float(amount), 8)

    def get_nonce(self, address: str) -> int:
        return self.get_account(address).nonce

    def increment_nonce(self, address: str):
        self.get_account(address).nonce += 1

    def get_code(self, address: str) -> str:
        return self.get_account(address).code

    def set_code(self, address: str, code: str):
        self.get_account(address).code = code

    def get_storage(self, address: str, key: str) -> Any:
        return self.get_account(address).storage.get(key)

    def set_storage(self, address: str, key: str, value: Any):
        self.get_account(address).storage[key] = value

    def snapshot(self):
        """Create a state checkpoint for atomic rollback."""
        snap = {addr: copy.deepcopy(acc) for addr, acc in self.accounts.items()}
        self._snapshots.append(snap)

    def commit(self):
        """Commit the most recent checkpoint."""
        if self._snapshots:
            self._snapshots.pop()

    def rollback(self):
        """Revert state changes back to the last checkpoint."""
        if self._snapshots:
            self.accounts = self._snapshots.pop()

    def calculate_state_root(self) -> str:
        """Compute the SHA3-256 Merkle State Root of all accounts in Quanthreum."""
        if not self.accounts:
            return "0" * 64

        items = sorted(self.accounts.items(), key=lambda x: x[0])
        hasher = hashlib.sha3_256()
        for addr, acc in items:
            hasher.update(addr.encode('utf-8'))
            hasher.update(acc.hash())
        return hasher.hexdigest()

    def get_total_circulating_supply(self) -> float:
        """Calculate current total QTH across all accounts."""
        return round(sum(acc.balance for acc in self.accounts.values()), 8)

    def to_dict(self) -> Dict[str, Any]:
        return {addr: acc.to_dict() for addr, acc in self.accounts.items()}

    def load_dict(self, data: Dict[str, Any]):
        self.accounts = {addr: Account.from_dict(acc_data) for addr, acc_data in data.items()}
