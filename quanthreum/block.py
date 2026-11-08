"""
Quanthreum (QTH) - Ethereum-Style Block & Receipts Engine
Handles:
  - Block header with State Root, Gas Used, Base Fee (EIP-1559), and Validator
  - Transaction receipts and execution logs
  - SHA3-256 Block Hashing & Merkle Trees
"""

import json
import time
from typing import Any, Dict, List, Optional
from .quantum_crypto import sha3_256
from .transaction import Transaction


def calculate_merkle_root(hashes: List[str]) -> str:
    """Calculate Merkle Tree Root using SHA3-256 pairs."""
    if not hashes:
        return "0" * 64
    current_level = [bytes.fromhex(h) for h in hashes]

    while len(current_level) > 1:
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])
        next_level = []
        for i in range(0, len(current_level), 2):
            combined = current_level[i] + current_level[i + 1]
            next_level.append(sha3_256(combined))
        current_level = next_level

    return current_level[0].hex()


class BlockHeader:
    """Ethereum-nature Block Header with State Root and EIP-1559 Base Fee."""

    def __init__(
        self,
        number: int,
        parent_hash: str,
        state_root: str,
        transactions_root: str,
        gas_used: int,
        gas_limit: int,
        base_fee: float,
        timestamp: float,
        validator: str,
        extra_data: str = "Quanthreum QTH"
    ):
        self.number = number
        self.parent_hash = parent_hash
        self.state_root = state_root
        self.transactions_root = transactions_root
        self.gas_used = gas_used
        self.gas_limit = gas_limit
        self.base_fee = round(float(base_fee), 8)
        self.timestamp = timestamp
        self.validator = validator
        self.extra_data = extra_data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "parent_hash": self.parent_hash,
            "state_root": self.state_root,
            "transactions_root": self.transactions_root,
            "gas_used": self.gas_used,
            "gas_limit": self.gas_limit,
            "base_fee": self.base_fee,
            "timestamp": self.timestamp,
            "validator": self.validator,
            "extra_data": self.extra_data,
        }

    def serialize(self) -> bytes:
        return json.dumps(self.to_dict(), sort_keys=True).encode('utf-8')

    def calculate_hash(self) -> str:
        return sha3_256(self.serialize()).hex()


class Block:
    """Quanthreum Block containing header, transactions, and execution receipts."""

    def __init__(
        self,
        header: BlockHeader,
        transactions: List[Transaction],
        receipts: Optional[List[Dict[str, Any]]] = None,
        block_hash: Optional[str] = None
    ):
        self.header = header
        self.transactions = transactions
        self.receipts = receipts or []
        self.block_hash = block_hash or header.calculate_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.block_hash,
            "header": self.header.to_dict(),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "receipts": self.receipts,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Block":
        h_data = d["header"]
        header = BlockHeader(
            number=h_data["number"],
            parent_hash=h_data["parent_hash"],
            state_root=h_data["state_root"],
            transactions_root=h_data["transactions_root"],
            gas_used=h_data["gas_used"],
            gas_limit=h_data["gas_limit"],
            base_fee=h_data.get("base_fee", 0.00001),
            timestamp=h_data["timestamp"],
            validator=h_data["validator"],
            extra_data=h_data.get("extra_data", ""),
        )
        txs = [Transaction.from_dict(t) for t in d.get("transactions", [])]
        return cls(header=header, transactions=txs, receipts=d.get("receipts", []), block_hash=d.get("hash"))

    @classmethod
    def create_genesis(cls, initial_validator: str, state_root: str) -> "Block":
        """Initialize the Quanthreum Genesis Block (Block #0)."""
        header = BlockHeader(
            number=0,
            parent_hash="0" * 64,
            state_root=state_root,
            transactions_root="0" * 64,
            gas_used=0,
            gas_limit=15_000_000,
            base_fee=0.00001,
            timestamp=1700000000.0,
            validator=initial_validator,
            extra_data="Quanthreum Genesis: Quantum-Resistant Ethereum Nature, 100M QTH Supply"
        )
        return cls(header=header, transactions=[], receipts=[])
