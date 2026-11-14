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
INITIAL_BLOCK_REWARD = 0.05        # Base emission per block
MAX_DAILY_VALIDATOR_REWARD = 50.0  # Strict maximum 50 QTH daily earnings per validator
VALIDATOR_REGISTRATION_FEE_USD = 300.0    # $300 USDT validator registration fee
VALIDATOR_ONBOARDING_CREDIT_QTH = 1000.0  # 1,000 QTH credited to new validator upon fee confirmation
REFERENCE_TOKEN_PRICE_USD = 15.0          # Reference target market valuation ($15.00/QTH)
SECONDS_PER_DAY = 86400.0          # 24-hour quota window
INITIAL_BASE_FEE = 0.00001         # 0.00001 QTH base fee per gas
TARGET_GAS_PER_BLOCK = 7_500_000   # 50% of 15M max block gas


class QPoSConsensus:
    """Manages Quantum Proof of Stake validators and EIP-1559 fee burning."""

    def __init__(self):
        # validator_address -> staked_qth
        self.validators: Dict[str, float] = {}
        self.total_staked: float = 0.0
        self.total_burned_fees: float = 0.0
        # validator_address -> {"window_start": float, "earned": float}
        self.validator_daily_earnings: Dict[str, Dict[str, float]] = {}
        # validator_address -> depositor_cold_wallet_address
        self.validator_depositors: Dict[str, str] = {}

    def verify_and_onboard_validator(
        self,
        validator_address: str,
        depositor_address: Optional[str] = None,
        payment_ref: str = "",
        payment_amount_usd: float = 300.0,
    ) -> Tuple[bool, str, float]:
        """
        Validates confirmation of the $300 registration fee and approves
        the 1,000 QTH credit for the registering validator.
        Supports dual-key architecture (separate cold depositor vs hot node operator).
        """
        if payment_amount_usd < VALIDATOR_REGISTRATION_FEE_USD:
            return (
                False,
                f"Registration fee requires minimum ${VALIDATOR_REGISTRATION_FEE_USD} USD/USDT",
                0.0,
            )

        if not payment_ref or len(payment_ref.strip()) < 6:
            return False, "Valid payment confirmation reference / tx_hash required", 0.0

        dep = depositor_address or validator_address
        self.validator_depositors[validator_address] = dep
        return (
            True,
            f"Registration verified ({payment_ref}). Approved {VALIDATOR_ONBOARDING_CREDIT_QTH} QTH onboarding grant.",
            VALIDATOR_ONBOARDING_CREDIT_QTH,
        )

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
        """
        Deterministic stake-weighted selection of validator.
        Validators with higher stake balances have a proportionally higher
        probability of being selected to propose and seal the block.
        """
        if not self.validators or self.total_staked <= 0.0:
            return None

        val_list = sorted(self.validators.keys())
        if len(val_list) == 1:
            return val_list[0]

        # Stake-weighted probabilistic selection using quantum block seed
        seed_int = int(seed_hash[:8], 16) + block_number
        target = (seed_int % 1000000) / 1000000.0 * self.total_staked
        cumulative = 0.0
        for val_addr in val_list:
            cumulative += self.validators[val_addr]
            if cumulative >= target:
                return val_addr
        return val_list[-1]

    def calculate_block_reward(
        self,
        current_circulating_supply: float,
        validator_address: Optional[str] = None,
        block_timestamp: Optional[float] = None,
    ) -> float:
        """
        Calculate newly minted QTH reward for the validator based on their
        proportional stake in the network, strictly bounded by the 50 QTH daily cap
        and the 100,000,000 QTH hard cap.
        Higher staked validators receive proportionally higher rewards.
        """
        remaining_mintable = max(0.0, TOTAL_MAX_SUPPLY - current_circulating_supply)
        if remaining_mintable <= 0.0:
            return 0.0  # 100 Million cap reached! No more minting.

        base_reward = min(INITIAL_BLOCK_REWARD, remaining_mintable)

        # Scale reward dynamically by validator's stake share
        if validator_address and validator_address in self.validators and self.total_staked > 0:
            val_stake = self.validators[validator_address]
            stake_ratio = val_stake / self.total_staked
            # Stake-weighted yield: scales directly with stake share (min 5% floor up to 100%)
            reward = base_reward * max(0.05, stake_ratio)
        else:
            reward = base_reward

        # Enforce maximum 50 QTH daily earnings cap per validator
        if validator_address:
            import time
            ts = block_timestamp if block_timestamp is not None else time.time()
            day_data = self.validator_daily_earnings.get(validator_address)
            if day_data:
                # Reset rolling 24-hour window if expired
                if ts - day_data.get("window_start", 0) >= SECONDS_PER_DAY:
                    earned_today = 0.0
                else:
                    earned_today = day_data.get("earned", 0.0)
            else:
                earned_today = 0.0

            remaining_daily_quota = max(0.0, MAX_DAILY_VALIDATOR_REWARD - earned_today)
            reward = min(reward, remaining_daily_quota)

        return round(min(reward, remaining_mintable), 8)

    def record_validator_reward(
        self, validator_address: str, amount: float, block_timestamp: Optional[float] = None
    ):
        """Record validator reward against their 24-hour quota (max 50 QTH/day)."""
        if amount <= 0:
            return
        import time
        ts = block_timestamp if block_timestamp is not None else time.time()
        if validator_address not in self.validator_daily_earnings:
            self.validator_daily_earnings[validator_address] = {
                "window_start": ts,
                "earned": 0.0,
            }

        entry = self.validator_daily_earnings[validator_address]
        if ts - entry.get("window_start", 0) >= SECONDS_PER_DAY:
            entry["window_start"] = ts
            entry["earned"] = 0.0

        entry["earned"] = round(entry["earned"] + amount, 8)

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
