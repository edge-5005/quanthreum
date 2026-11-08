"""
Quanthreum Virtual Machine (QVM) - Ethereum-Compatible Contract Engine
Executes state-transition smart contracts with strict gas metering and sandboxing.
Supports:
  - Smart Contract Deployment & Execution
  - QRC-20 Quantum Token Contracts (Ethereum ERC-20 equivalent)
  - Quantum Staking & Escrow Contracts
  - Gas computation and revert mechanics
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple
from .state import WorldState

GAS_BASE_TX = 21_000
GAS_CONTRACT_CREATE = 53_000
GAS_STORAGE_WRITE = 5_000
GAS_STORAGE_READ = 800
GAS_OP_BASE = 100


class VMExecutionResult:
    """Outcome of smart contract or transaction execution."""

    def __init__(
        self,
        success: bool,
        gas_used: int,
        return_data: Any = None,
        error: Optional[str] = None,
        logs: Optional[List[Dict[str, Any]]] = None
    ):
        self.success = success
        self.gas_used = gas_used
        self.return_data = return_data
        self.error = error
        self.logs = logs or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "gas_used": self.gas_used,
            "return_data": self.return_data,
            "error": self.error,
            "logs": self.logs,
        }


class QVM:
    """Quanthreum Virtual Machine."""

    def __init__(self, state: WorldState):
        self.state = state

    def execute_transaction(
        self,
        from_address: str,
        to_address: Optional[str],
        value: float,
        gas_limit: int,
        gas_price: float,
        data: str,
        contract_address: Optional[str] = None
    ) -> VMExecutionResult:
        """Execute a state transition with gas tracking and atomic rollback on failure."""
        gas_used = GAS_BASE_TX
        logs: List[Dict[str, Any]] = []

        # Check sender has enough balance to cover value + max gas fee
        max_gas_fee = gas_limit * gas_price
        sender_balance = self.state.get_balance(from_address)
        if sender_balance < (value + max_gas_fee):
            return VMExecutionResult(
                success=False,
                gas_used=gas_used,
                error=f"Insufficient funds for transfer + gas fee: have {sender_balance}, need {value + max_gas_fee}"
            )

        # Take atomic snapshot in case execution reverts
        self.state.snapshot()

        try:
            # 1. Deduct value from sender and add to recipient
            self.state.sub_balance(from_address, value)

            # 2. Case A: Contract Deployment
            if to_address is None or to_address == "":
                gas_used += GAS_CONTRACT_CREATE
                if gas_used > gas_limit:
                    raise ValueError("Out of gas during contract deployment")

                new_contract_addr = contract_address
                # Deploy code into state
                self.state.set_code(new_contract_addr, data)
                self.state.add_balance(new_contract_addr, value)

                # Initialize contract if constructor JSON is present
                init_result = self._initialize_contract(new_contract_addr, from_address, data)
                gas_used += init_result.get("gas", 0)
                if gas_used > gas_limit:
                    raise ValueError("Out of gas during contract initialization")

                logs.append({
                    "event": "ContractCreated",
                    "contract": new_contract_addr,
                    "deployer": from_address,
                })

                self.state.commit()
                return VMExecutionResult(
                    success=True,
                    gas_used=gas_used,
                    return_data={"contract_address": new_contract_addr},
                    logs=logs
                )

            # 3. Case B: Call to Smart Contract or EOA
            target_acc = self.state.get_account(to_address)
            self.state.add_balance(to_address, value)

            if target_acc.is_contract and data:
                # Contract call execution
                call_res = self._execute_contract_call(
                    contract_addr=to_address,
                    caller=from_address,
                    call_value=value,
                    call_data=data,
                    remaining_gas=gas_limit - gas_used
                )
                gas_used += call_res["gas_used"]
                logs.extend(call_res.get("logs", []))

                if not call_res["success"]:
                    raise ValueError(call_res.get("error", "Contract execution reverted"))

                self.state.commit()
                return VMExecutionResult(
                    success=True,
                    gas_used=gas_used,
                    return_data=call_res.get("return_data"),
                    logs=logs
                )

            # Standard EOA Transfer
            self.state.commit()
            return VMExecutionResult(success=True, gas_used=gas_used, logs=logs)

        except Exception as e:
            # Revert state changes upon failure
            self.state.rollback()
            return VMExecutionResult(
                success=False,
                gas_used=min(gas_limit, gas_used + 5000),
                error=str(e),
                logs=[]
            )

    def _initialize_contract(self, contract_addr: str, deployer: str, code: str) -> dict:
        """Parse and execute constructor payload."""
        try:
            parsed = json.loads(code)
            storage = parsed.get("init_storage", {})
            storage["_owner"] = deployer
            storage["_created_at"] = time.time()
            for k, v in storage.items():
                self.state.set_storage(contract_addr, k, v)
            return {"gas": len(storage) * GAS_STORAGE_WRITE}
        except Exception:
            return {"gas": GAS_OP_BASE}

    def _execute_contract_call(
        self,
        contract_addr: str,
        caller: str,
        call_value: float,
        call_data: str,
        remaining_gas: int
    ) -> dict:
        """
        Execute smart contract methods (QRC-20 token, Staking, Vaults).
        """
        gas_used = GAS_OP_BASE
        logs = []

        try:
            payload = json.loads(call_data)
            action = payload.get("action")
            params = payload.get("params", {})
        except Exception:
            return {"success": False, "error": "Invalid JSON call data", "gas_used": gas_used}

        # QRC-20 Standard Token Contract Actions
        if action == "qrc20_transfer":
            recipient = params.get("to")
            amount = float(params.get("amount", 0))

            balances = self.state.get_storage(contract_addr, "balances") or {}
            sender_bal = float(balances.get(caller, 0))

            if sender_bal < amount:
                return {"success": False, "error": f"QRC-20 balance insufficient: {sender_bal} < {amount}", "gas_used": gas_used}

            balances[caller] = round(sender_bal - amount, 8)
            balances[recipient] = round(float(balances.get(recipient, 0)) + amount, 8)
            self.state.set_storage(contract_addr, "balances", balances)

            gas_used += (GAS_STORAGE_WRITE * 2)
            logs.append({"event": "Transfer", "from": caller, "to": recipient, "amount": amount})
            return {"success": True, "gas_used": gas_used, "return_data": {"new_balance": balances[caller]}, "logs": logs}

        # Quantum Staking Action
        elif action == "stake":
            if call_value <= 0:
                return {"success": False, "error": "Must stake a positive amount of QTH", "gas_used": gas_used}

            stakes = self.state.get_storage(contract_addr, "stakes") or {}
            current_staked = float(stakes.get(caller, 0))
            stakes[caller] = round(current_staked + call_value, 8)
            self.state.set_storage(contract_addr, "stakes", stakes)

            gas_used += GAS_STORAGE_WRITE
            logs.append({"event": "Staked", "staker": caller, "amount": call_value})
            return {"success": True, "gas_used": gas_used, "return_data": {"staked": stakes[caller]}, "logs": logs}

        elif action == "unstake":
            amount = float(params.get("amount", 0))
            stakes = self.state.get_storage(contract_addr, "stakes") or {}
            current_staked = float(stakes.get(caller, 0))

            if current_staked < amount:
                return {"success": False, "error": "Unstake amount exceeds staked balance", "gas_used": gas_used}

            stakes[caller] = round(current_staked - amount, 8)
            self.state.set_storage(contract_addr, "stakes", stakes)

            # Contract sends QTH back to caller
            self.state.sub_balance(contract_addr, amount)
            self.state.add_balance(caller, amount)

            gas_used += GAS_STORAGE_WRITE
            logs.append({"event": "Unstaked", "staker": caller, "amount": amount})
            return {"success": True, "gas_used": gas_used, "return_data": {"remaining_staked": stakes[caller]}, "logs": logs}

        # Generic Key-Value Storage Write
        elif action == "set_value":
            key = params.get("key")
            val = params.get("value")
            self.state.set_storage(contract_addr, key, val)
            gas_used += GAS_STORAGE_WRITE
            return {"success": True, "gas_used": gas_used, "return_data": "stored", "logs": logs}

        return {"success": False, "error": f"Unknown contract action: {action}", "gas_used": gas_used}
