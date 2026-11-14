"""
Quanthreum (QTH) - Blockchain & Ledger Engine
Integrates:
  - Ethereum Account-based World State
  - Post-Quantum Cryptographic verification
  - Quanthreum Virtual Machine (QVM) execution
  - Quantum Proof of Stake (Q-PoS) Consensus
  - 100 Million QTH Hard Cap Enforcement
  - EIP-1559 Fee Burning Mechanism
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .block import Block, BlockHeader, calculate_merkle_root
from .consensus import INITIAL_BASE_FEE, MIN_VALIDATOR_STAKE, QPoSConsensus, TOTAL_MAX_SUPPLY
from .state import WorldState
from .transaction import Transaction, derive_contract_address
from .vm import QVM, VMExecutionResult


class Blockchain:
    """The Quanthreum Blockchain Ledger."""

    def __init__(self, data_dir: str, genesis_alloc_address: Optional[str] = None):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.chain_file = os.path.join(data_dir, "quanthreum_chain.json")
        self.state_file = os.path.join(data_dir, "quanthreum_state.json")

        self.chain: List[Block] = []
        self.state = WorldState()
        self.consensus = QPoSConsensus()
        self.mempool: Dict[str, Transaction] = {}
        self.vm = QVM(self.state)

        self.current_base_fee = INITIAL_BASE_FEE
        self.load_or_initialize(genesis_alloc_address)

    def load_or_initialize(self, genesis_alloc_address: Optional[str]):
        """Load blockchain from disk or create Genesis block."""
        if os.path.exists(self.chain_file) and os.path.exists(self.state_file):
            try:
                with open(self.chain_file, "r", encoding="utf-8") as f:
                    chain_data = json.load(f)
                    self.chain = [Block.from_dict(b) for b in chain_data.get("blocks", [])]

                with open(self.state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    self.state.load_dict(state_data.get("accounts", {}))
                    self.consensus.validators = state_data.get("validators", {})
                    self.consensus.total_staked = sum(self.consensus.validators.values())
                    self.consensus.total_burned_fees = state_data.get("burned_fees", 0.0)
                    self.consensus.validator_daily_earnings = state_data.get("daily_earnings", {})
                    self.consensus.validator_depositors = state_data.get("validator_depositors", {})
                    self.current_base_fee = state_data.get("base_fee", INITIAL_BASE_FEE)

                print(f"Loaded Quanthreum chain with {len(self.chain)} blocks.")
                return
            except Exception as e:
                print(f"Failed to load chain ({e}), creating fresh Genesis block.")

        # Fresh Genesis Initialization
        alloc_addr = genesis_alloc_address or "0xQTH_0000000000000000000000000000000000000001"
        # Genesis allocation: 10,000,000 QTH (10% of 100M total max supply for initial liquidity/faucets)
        self.state.set_balance(alloc_addr, 10_000_000.0)
        # Register initial validator with 100 QTH stake
        self.consensus.register_validator(alloc_addr, 100.0)

        genesis_state_root = self.state.calculate_state_root()
        genesis_block = Block.create_genesis(initial_validator=alloc_addr, state_root=genesis_state_root)
        self.chain = [genesis_block]
        self.save()
        print("Created Quanthreum Genesis Block with 100M Total Max Supply.")

    def save(self):
        """Persist blockchain and world state to disk."""
        chain_data = {"blocks": [b.to_dict() for b in self.chain]}
        with open(self.chain_file, "w", encoding="utf-8") as f:
            json.dump(chain_data, f, indent=2)

        state_data = {
            "accounts": self.state.to_dict(),
            "validators": self.consensus.validators,
            "burned_fees": self.consensus.total_burned_fees,
            "base_fee": self.current_base_fee,
            "daily_earnings": self.consensus.validator_daily_earnings,
            "validator_depositors": self.consensus.validator_depositors,
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

    @property
    def tip(self) -> Block:
        return self.chain[-1]

    @property
    def height(self) -> int:
        return self.tip.header.number

    def get_circulating_supply(self) -> float:
        return self.state.get_total_circulating_supply()

    def add_transaction(self, tx: Transaction) -> Tuple[bool, str]:
        """Validate and insert transaction into the mempool."""
        if tx.tx_hash in self.mempool:
            return False, "Transaction already in mempool"

        # 1. Verify Post-Quantum Signature
        if not tx.verify_signature():
            return False, "Invalid Post-Quantum Winternitz signature"

        # 2. Check Nonce
        expected_nonce = self.state.get_nonce(tx.from_address)
        if tx.nonce < expected_nonce:
            return False, f"Nonce too low: expected {expected_nonce}, got {tx.nonce}"

        # 3. Check Balance
        required = tx.value + (tx.gas_limit * tx.gas_price)
        balance = self.state.get_balance(tx.from_address)
        if balance < required:
            return False, f"Insufficient balance: have {balance} QTH, need {required} QTH"

        # 4. Check Gas Price meets base fee
        if tx.gas_price < self.current_base_fee:
            return False, f"Gas price ({tx.gas_price}) below current base fee ({self.current_base_fee})"

        self.mempool[tx.tx_hash] = tx
        return True, "Transaction accepted into mempool"

    def propose_and_mine_block(
        self,
        validator_address: str,
        extra_data: str = "Quanthreum QTH Block"
    ) -> Tuple[bool, Optional[Block], str]:
        """
        Produce and validate a new Quanthreum block:
          - Executes transactions via QVM
          - Enforces EIP-1559 base fee burn
          - Mints block reward capped at 100 Million QTH
          - Updates World State and Merkle roots
        """
        next_number = self.height + 1
        block_gas_limit = 15_000_000
        block_gas_used = 0

        executed_txs: List[Transaction] = []
        receipts: List[Dict[str, Any]] = []
        total_burned_in_block = 0.0
        total_tips_to_validator = 0.0

        # Sort mempool by gas_price descending (MEV/Priority order)
        sorted_mempool = sorted(self.mempool.values(), key=lambda t: t.gas_price, reverse=True)

        for tx in sorted_mempool:
            if (block_gas_used + tx.gas_limit) > block_gas_limit:
                continue  # Skip if exceeds block gas limit

            # Derive contract address if creating contract
            contract_addr = None
            if tx.is_contract_creation:
                contract_addr = derive_contract_address(tx.from_address, tx.nonce)

            # Execute transaction in QVM
            exec_res = self.vm.execute_transaction(
                from_address=tx.from_address,
                to_address=tx.to_address,
                value=tx.value,
                gas_limit=tx.gas_limit,
                gas_price=tx.gas_price,
                data=tx.data,
                contract_address=contract_addr
            )

            # Increment sender nonce
            self.state.increment_nonce(tx.from_address)

            # Fee distribution & EIP-1559 burning
            actual_gas = exec_res.gas_used
            block_gas_used += actual_gas

            burned_fee = round(actual_gas * self.current_base_fee, 8)
            tip_fee = round(actual_gas * (tx.gas_price - self.current_base_fee), 8)
            total_burned_in_block += burned_fee
            total_tips_to_validator += tip_fee

            # Deduct actual gas fee from sender
            actual_gas_fee = round(actual_gas * tx.gas_price, 8)
            self.state.sub_balance(tx.from_address, actual_gas_fee)

            receipts.append({
                "tx_hash": tx.tx_hash,
                "success": exec_res.success,
                "gas_used": actual_gas,
                "burned_fee": burned_fee,
                "tip_fee": tip_fee,
                "contract_address": contract_addr if exec_res.success else None,
                "return_data": exec_res.return_data,
                "logs": exec_res.logs,
                "error": exec_res.error,
            })

            executed_txs.append(tx)
            self.mempool.pop(tx.tx_hash, None)

        # Validator Reward calculation (strictly enforces 100M supply cap and 50 QTH daily limit)
        now_ts = time.time()
        circulating = self.get_circulating_supply()
        mint_reward = self.consensus.calculate_block_reward(
            circulating, validator_address=validator_address, block_timestamp=now_ts
        )
        self.consensus.record_validator_reward(validator_address, mint_reward, block_timestamp=now_ts)

        # Credit validator or cold depositor: mint_reward + gas tips
        total_validator_payout = round(mint_reward + total_tips_to_validator, 8)
        payout_recipient = self.consensus.validator_depositors.get(validator_address, validator_address)
        self.state.add_balance(payout_recipient, total_validator_payout)

        # Track burned fees (deflationary EIP-1559)
        self.consensus.total_burned_fees = round(self.consensus.total_burned_fees + total_burned_in_block, 8)

        # Build Merkle Roots & Block Header
        state_root = self.state.calculate_state_root()
        tx_hashes = [t.tx_hash for t in executed_txs]
        tx_root = calculate_merkle_root(tx_hashes)
        receipt_hashes = [r["tx_hash"] for r in receipts]
        receipt_root = calculate_merkle_root(receipt_hashes)

        header = BlockHeader(
            number=next_number,
            parent_hash=self.tip.block_hash,
            state_root=state_root,
            transactions_root=tx_root,
            gas_used=block_gas_used,
            gas_limit=block_gas_limit,
            base_fee=self.current_base_fee,
            timestamp=time.time(),
            validator=validator_address,
            extra_data=extra_data
        )

        new_block = Block(header=header, transactions=executed_txs, receipts=receipts)
        self.chain.append(new_block)

        # Adjust next base fee according to block gas utilization
        self.current_base_fee = self.consensus.calculate_next_base_fee(self.current_base_fee, block_gas_used)

        self.save()
        return True, new_block, f"Block #{next_number} produced successfully"

    def mine_pending_transactions(
        self,
        validator_address: str,
        extra_data: str = "Quanthreum QTH Block"
    ) -> Optional[Block]:
        """Convenience alias for propose_and_mine_block used by REST API."""
        ok, block, _ = self.propose_and_mine_block(validator_address=validator_address, extra_data=extra_data)
        return block if ok else None

    def onboard_validator_with_payment(
        self,
        validator_address: str,
        depositor_address: Optional[str] = None,
        payment_ref: str = "",
        payment_usd: float = 300.0,
        auto_stake: float = 100.0,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Processes confirmed receipt of the $300 validator registration fee.
        Credits 1,000 QTH to the validator/depositor account and registers their initial stake.
        Supports dual-key security (cold depositor address vs hot operator node address).
        """
        ok, msg, credit_qth = self.consensus.verify_and_onboard_validator(
            validator_address=validator_address,
            depositor_address=depositor_address,
            payment_ref=payment_ref,
            payment_amount_usd=payment_usd,
        )
        if not ok:
            return False, msg, {}

        recipient = depositor_address or validator_address

        # Credit the 1,000 QTH onboarding allocation
        self.state.add_balance(recipient, credit_qth)

        # Allocate initial stake bond if requested
        stake_amount = min(auto_stake, credit_qth)
        if stake_amount >= MIN_VALIDATOR_STAKE and self.state.get_balance(recipient) >= stake_amount:
            self.state.sub_balance(recipient, stake_amount)
            self.consensus.register_validator(validator_address, stake_amount)

        self.save()
        details = {
            "validator_address": validator_address,
            "depositor_address": recipient,
            "payment_ref": payment_ref,
            "payment_usd": payment_usd,
            "credited_qth": credit_qth,
            "staked_qth": stake_amount,
            "liquid_balance_qth": self.state.get_balance(recipient),
            "daily_reward_cap_qth": 50.0,
        }
        return (
            True,
            f"Successfully onboarded validator {validator_address}. Credited {credit_qth} QTH (Staked: {stake_amount} QTH).",
            details,
        )
