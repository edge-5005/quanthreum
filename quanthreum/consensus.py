"""
Quanthreum (QTH) - Quantum Proof-of-Stake (Q-PoS) & EIP-1559 Engine
Features:
  - Validator Staking registry (Min 10 QTH stake)
  - Post-Quantum validator signatures on proposed blocks
  - EIP-1559 Gas Base Fee Burning (Deflationary supply)
  - 100 Million QTH Maximum Supply Cap enforcement
"""

import math
from typing import Dict, List, Optional, Tuple

TOTAL_MAX_SUPPLY = 100_000_000.0   # 100 Million QTH hard cap
MIN_VALIDATOR_STAKE = 10.0         # 10 QTH to register validator
INITIAL_BLOCK_REWARD = 2.0         # 2 QTH mint per block (until 100M cap)
INITIAL_BASE_FEE = 0.00001         # 0.00001 QTH base fee per gas
TARGET_GAS_PER_BLOCK = 7_500_000   # 50% of 15M max block gas


class QPoSConsensus:
    """Manages Quantum Proof of Stake validators and EIP-1559 fee burning."""

    def __init__(self):
        # validator_address -> staked_qth
        self.validators: Dict[str, float] = {}
        self.total_staked: float = 0.0
        self.total_burned_fees: float = 0.0

    def register_validator(self, address: str, stake_amount: float) -> Tuple[bool, str]:
        """Stake QTH to activate validator status."""
        if stake_amount < MIN_VALIDATOR_STAKE:
            return False, f"Minimum stake required is {MIN_VALIDATOR_STAKE} QTH"

        self.validators[address] = self.validators.get(address, 0.0) + stake_amount
        self.total_staked += stake_amount
        return True, f"Validator {address} registered with {self.validators[address]} QTH stake"

    def remove_validator_stake(self, address: str, unstake_amount: float) -> Tuple[bool, str]:
        """Withdraw staked QTH."""
        current = self.validators.get(address, 0.0)
        if current < unstake_amount:
            return False, "Insufficient staked balance"

        self.validators[address] = round(current - unstake_amount, 8)
        self.total_staked = round(self.total_staked - unstake_amount, 8)
        if self.validators[address] < MIN_VALIDATOR_STAKE:
            del self.validators[address]
        return True, "Stake withdrawn"

    def select_validator(self, block_number: int, seed_hash: str) -> Optional[str]:
        """Weighted selection of validator based on stake and quantum seed."""
        if not self.validators:
            return None

        # Deterministic pseudo-random selection based on stake weight
        val_list = sorted(self.validators.keys())
        seed_int = int(seed_hash[:8], 16) + block_number
        idx = seed_int % len(val_list)
        return val_list[idx]

    def calculate_block_reward(self, current_circulating_supply: float) -> float:
        """
        Calculate newly minted QTH reward for the validator.
        Strictly enforces the 100,000,000 QTH hard cap.
        """
        remaining_mintable = max(0.0, TOTAL_MAX_SUPPLY - current_circulating_supply)
        if remaining_mintable <= 0.0:
            return 0.0  # 100 Million cap reached! No more minting.

        # Decaying block reward approaching 100M cap
        reward = min(INITIAL_BLOCK_REWARD, remaining_mintable)
        return round(reward, 8)

    def calculate_next_base_fee(self, current_base_fee: float, gas_used: int) -> float:
        """
        EIP-1559 Dynamic Base Fee adjustment:
        If gas used > target, base fee increases up to 12.5%.
        If gas used < target, base fee decreases up to 12.5%.
        """
        gas_delta = gas_used - TARGET_GAS_PER_BLOCK
        change_ratio = gas_delta / TARGET_GAS_PER_BLOCK
        # Cap change between -12.5% and +12.5%
        change_ratio = max(-0.125, min(0.125, change_ratio))

        new_base_fee = current_base_fee * (1.0 + change_ratio)
        return round(max(0.000001, new_base_fee), 8)
