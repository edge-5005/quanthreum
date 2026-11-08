"""
Quanthreum (QTH) - Automated Validator Worker Daemon
Runs a continuous Q-PoS validator node:
  - Validates transactions from mempool
  - Mints and seals blocks every block cycle
  - Collects block rewards and gas tips (EIP-1559)
  - Enforces the 100 Million QTH Total Supply Cap
"""

import json
import time
import urllib.error
import urllib.request
from typing import Callable, Optional


class ValidatorRunner:
    """Automated validator daemon for Windows and server environments."""

    def __init__(
        self,
        node_url: str,
        validator_address: str,
        validator_seed: Optional[str] = None,
        block_interval: int = 6,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        self.node_url = node_url.rstrip('/')
        self.validator_address = validator_address
        self.validator_seed = validator_seed
        self.block_interval = block_interval
        self.log_callback = log_callback or print
        self.is_running = False

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        self.log_callback(formatted)

    def _http_get(self, endpoint: str) -> dict:
        url = f"{self.node_url}{endpoint}"
        req = urllib.request.Request(url, headers={"User-Agent": "Quanthreum-Validator/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def _http_post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.node_url}{endpoint}"
        payload = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Quanthreum-Validator/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def check_and_ensure_stake(self, default_stake: float = 32.0):
        """Ensure validator has active stake registered in consensus."""
        try:
            acc = self._http_get(f"/api/account?address={self.validator_address}")
            if not acc.get("is_validator"):
                balance = acc.get("balance", 0.0)
                self.log(f"Account {self.validator_address[:12]}... is not yet an active validator.")
                if balance >= default_stake and self.validator_seed:
                    self.log(f"Auto-staking {default_stake} QTH into Q-PoS validator pool...")
                    stake_res = self._http_post("/api/validator/stake", {
                        "seed": self.validator_seed,
                        "amount": default_stake
                    })
                    if stake_res.get("status") == "success":
                        self.log(f"Stake confirmed! Validator is now ACTIVE ({default_stake} QTH staked).")
                    else:
                        self.log(f"Staking failed: {stake_res.get('error')}")
                else:
                    self.log(f"Current balance: {balance} QTH. (Minimum 10 QTH stake required).")
            else:
                self.log(f"Validator is ACTIVE with {acc.get('staked_amount')} QTH staked.")
        except Exception as e:
            self.log(f"Could not verify validator stake: {e}")

    def produce_block_round(self) -> Optional[dict]:
        """Propose and seal one block in Q-PoS consensus."""
        try:
            payload = {
                "validator_address": self.validator_address,
                "extra_data": f"Validated by {self.validator_address[:12]}..."
            }
            res = self._http_post("/api/validator/mine_block", payload)
            if res.get("status") == "success":
                num = res.get("block_number")
                txs = res.get("transactions_count", 0)
                gas = res.get("gas_used", 0)
                circ = res.get("circulating_supply", 0)
                burned = res.get("burned_fees", 0)
                self.log(f"Sealed Block #{num} | TXs: {txs} | Gas: {gas:,} | Burned: {burned:.6f} QTH | Supply: {circ:,.2f} / 100M QTH")
                return res
            else:
                self.log(f"Proposal rejected: {res.get('error')}")
                return None
        except Exception as e:
            self.log(f"Block proposal error: {e}")
            return None

    def start(self):
        """Run continuous validator loop."""
        self.is_running = True
        self.log(f"Starting Quanthreum Validator Daemon for {self.validator_address}...")
        self.log(f"Connected to node at: {self.node_url} (Interval: {self.block_interval}s)")
        self.check_and_ensure_stake()

        while self.is_running:
            try:
                self.produce_block_round()
                time.sleep(self.block_interval)
            except KeyboardInterrupt:
                self.log("Validator stopped by user.")
                break
            except Exception as e:
                self.log(f"Validator loop exception: {e}")
                time.sleep(self.block_interval)

    def stop(self):
        self.is_running = False
        self.log("Stopping validator daemon...")
