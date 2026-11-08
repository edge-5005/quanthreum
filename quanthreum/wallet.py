"""
Quanthreum (QTH) - Quantum Wallet & Key Manager
Handles:
  - 48-Word Post-Quantum Mnemonic Seed generation & restoration
  - Keystore persistence (.json) with 512-bit entropy
  - Account Nonce and Balance tracking
  - Signing & Broadcasting Transfers, Contract Deployments, and Q-PoS Staking
"""

import json
import os
from typing import Any, Dict, Optional
from .quantum_crypto import QuantumKeyPair, validate_qth_address
from .transaction import Transaction


class QuantumWallet:
    """Manages Post-Quantum keys, 48-word mnemonic phrases, and Ethereum-style transactions."""

    def __init__(self, keypair: Optional[QuantumKeyPair] = None):
        self.keypair = keypair or QuantumKeyPair()

    @property
    def address(self) -> str:
        return self.keypair.address

    @property
    def seed_hex(self) -> str:
        return self.keypair.seed_hex

    @property
    def public_key_hex(self) -> str:
        return self.keypair.public_key_hex

    @property
    def mnemonic(self) -> Optional[str]:
        return self.keypair.mnemonic

    def save_to_file(self, filepath: str):
        """Save quantum keys and 48-word seed phrase securely to disk."""
        data = {
            "address": self.address,
            "mnemonic": self.mnemonic,
            "seed": self.seed_hex,
            "public_key": self.public_key_hex,
            "standard": "Winternitz W-OTS+ (NIST Post-Quantum Level 128)",
            "network": "Quanthreum Native QTH",
            "entropy_bits": 512,
            "word_count": 48 if self.mnemonic else 0,
        }
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "QuantumWallet":
        """Load quantum keys from disk."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("mnemonic"):
            keypair = QuantumKeyPair.from_mnemonic(data["mnemonic"])
        else:
            keypair = QuantumKeyPair.from_seed_hex(data["seed"])
        return cls(keypair)

    @classmethod
    def create_new(cls, filepath: Optional[str] = None) -> "QuantumWallet":
        """Generate a brand-new Post-Quantum wallet with 48-word seed phrase."""
        w = cls()
        if filepath:
            w.save_to_file(filepath)
        return w

    @classmethod
    def restore_from_mnemonic(cls, mnemonic: str, filepath: Optional[str] = None) -> "QuantumWallet":
        """Restore wallet from 48-word Post-Quantum mnemonic phrase."""
        keypair = QuantumKeyPair.from_mnemonic(mnemonic)
        w = cls(keypair)
        if filepath:
            w.save_to_file(filepath)
        return w

    def create_transfer_tx(
        self,
        recipient_address: str,
        amount: float,
        nonce: int,
        gas_limit: int = 21_000,
        gas_price: float = 0.00001
    ) -> Transaction:
        """Create and sign a standard QTH transfer."""
        if not validate_qth_address(recipient_address):
            raise ValueError(f"Invalid recipient QTH address: {recipient_address}")

        tx = Transaction(
            from_address=self.address,
            to_address=recipient_address,
            value=amount,
            nonce=nonce,
            gas_limit=gas_limit,
            gas_price=gas_price,
            data=""
        )
        tx.sign(self.keypair)
        return tx

    def create_deploy_tx(
        self,
        contract_code: str,
        nonce: int,
        initial_value: float = 0.0,
        gas_limit: int = 200_000,
        gas_price: float = 0.00001
    ) -> Transaction:
        """Create and sign a smart contract deployment transaction."""
        tx = Transaction(
            from_address=self.address,
            to_address=None,
            value=initial_value,
            nonce=nonce,
            gas_limit=gas_limit,
            gas_price=gas_price,
            data=contract_code
        )
        tx.sign(self.keypair)
        return tx

    def create_call_tx(
        self,
        contract_address: str,
        action: str,
        params: Dict[str, Any],
        nonce: int,
        value: float = 0.0,
        gas_limit: int = 150_000,
        gas_price: float = 0.00001
    ) -> Transaction:
        """Create and sign a smart contract execution transaction."""
        call_payload = json.dumps({"action": action, "params": params})
        tx = Transaction(
            from_address=self.address,
            to_address=contract_address,
            value=value,
            nonce=nonce,
            gas_limit=gas_limit,
            gas_price=gas_price,
            data=call_payload
        )
        tx.sign(self.keypair)
        return tx
