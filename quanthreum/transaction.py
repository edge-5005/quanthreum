"""
Quanthreum (QTH) - Ethereum-Style Quantum Transactions
Handles:
  - Account-based transactions (nonce, from, to, value, gas_limit, gas_price, data)
  - Smart contract deployment & function execution payloads
  - Post-Quantum Winternitz signature verification (Immune to quantum cracking)
  - Deterministic Contract Address derivation (Keccak256(sender + nonce))
"""

import json
import time
from typing import Any, Dict, Optional
from .quantum_crypto import (
    QuantumKeyPair,
    keccak256,
    sha3_256,
    validate_qth_address,
    verify_quantum_signature,
)


def derive_contract_address(sender_address: str, nonce: int) -> str:
    """
    Ethereum-style deterministic contract address derivation:
    0xQTH_ + Last 20 bytes of Keccak256(sender_address + nonce) with EIP-55 checksum.
    """
    raw = f"{sender_address}:{nonce}".encode('utf-8')
    pub_hash = keccak256(raw)[12:]
    hex_addr = pub_hash.hex()

    hash_check = keccak256(hex_addr.encode('ascii')).hex()
    checksummed = ""
    for i, ch in enumerate(hex_addr):
        if int(hash_check[i], 16) >= 8:
            checksummed += ch.upper()
        else:
            checksummed += ch.lower()

    return f"0xQTH_{checksummed}"


class Transaction:
    """Represents an Ethereum-nature transaction secured by Post-Quantum Cryptography."""

    def __init__(
        self,
        from_address: str,
        to_address: Optional[str],
        value: float,
        nonce: int,
        gas_limit: int = 100_000,
        gas_price: float = 0.00001,
        data: str = "",
        public_key: str = "",
        signature: str = "",
        timestamp: Optional[float] = None,
        tx_hash: Optional[str] = None,
    ):
        self.from_address = from_address
        self.to_address = to_address  # None when deploying a contract
        self.value = round(float(value), 8)
        self.nonce = int(nonce)
        self.gas_limit = int(gas_limit)
        self.gas_price = round(float(gas_price), 8)
        self.data = data or ""
        self.public_key = public_key
        self.signature = signature
        self.timestamp = timestamp or time.time()
        self.tx_hash = tx_hash or self.calculate_hash()

    @property
    def is_contract_creation(self) -> bool:
        return self.to_address is None or self.to_address == ""

    def get_signing_data(self) -> bytes:
        """Data that is hashed and cryptographically signed by the sender."""
        d = {
            "from": self.from_address,
            "to": self.to_address,
            "value": self.value,
            "nonce": self.nonce,
            "gas_limit": self.gas_limit,
            "gas_price": self.gas_price,
            "data": self.data,
            "timestamp": self.timestamp,
        }
        return json.dumps(d, sort_keys=True).encode('utf-8')

    def calculate_hash(self) -> str:
        """Unique Transaction ID (SHA3-256)."""
        d = {
            "from": self.from_address,
            "to": self.to_address,
            "value": self.value,
            "nonce": self.nonce,
            "gas_limit": self.gas_limit,
            "gas_price": self.gas_price,
            "data": self.data,
            "timestamp": self.timestamp,
            "public_key": self.public_key,
            "signature": self.signature,
        }
        raw = json.dumps(d, sort_keys=True).encode('utf-8')
        return sha3_256(raw).hex()

    def sign(self, keypair: QuantumKeyPair):
        """Sign transaction using sender's Post-Quantum KeyPair."""
        sign_hash = sha3_256(self.get_signing_data())
        self.signature = keypair.sign(sign_hash)
        self.public_key = keypair.public_key_hex
        self.tx_hash = self.calculate_hash()

    def verify_signature(self) -> bool:
        """Verify Post-Quantum signature against sender address."""
        if not self.signature or not self.public_key:
            return False

        # Verify public key matches sender address
        pub_bytes = bytes.fromhex(self.public_key)
        pub_hash = keccak256(pub_bytes)[12:].hex()
        if pub_hash.lower() != self.from_address[6:].lower():
            return False

        sign_hash = sha3_256(self.get_signing_data())
        return verify_quantum_signature(self.public_key, sign_hash, self.signature)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.tx_hash,
            "from": self.from_address,
            "to": self.to_address,
            "value": self.value,
            "nonce": self.nonce,
            "gas_limit": self.gas_limit,
            "gas_price": self.gas_price,
            "data": self.data,
            "public_key": self.public_key,
            "signature": self.signature,
            "timestamp": self.timestamp,
            "is_contract_creation": self.is_contract_creation,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Transaction":
        return cls(
            from_address=d["from"],
            to_address=d.get("to"),
            value=d.get("value", 0.0),
            nonce=d.get("nonce", 0),
            gas_limit=d.get("gas_limit", 100_000),
            gas_price=d.get("gas_price", 0.00001),
            data=d.get("data", ""),
            public_key=d.get("public_key", ""),
            signature=d.get("signature", ""),
            timestamp=d.get("timestamp"),
            tx_hash=d.get("hash"),
        )
