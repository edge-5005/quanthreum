"""
Quanthreum (QTH) - Full Node HTTP REST & Web Portal Server
Hosts:
  - Ethereum-style Account & State Queries
  - Post-Quantum Transaction Ingestion & Mempool
  - Smart Contract Deployment & Execution APIs
  - Quantum Proof of Stake (Q-PoS) Block Production
  - Web3 Explorer & Wallet static frontend
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse
from typing import Optional

from .blockchain import Blockchain
from .consensus import MIN_VALIDATOR_STAKE, TOTAL_MAX_SUPPLY
from .quantum_crypto import QuantumKeyPair, validate_qth_address
from .transaction import Transaction
from .wallet import QuantumWallet
from .security_service import scan_address_quantum_vulnerability, verify_enterprise_transaction
import hashlib


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class NodeRequestHandler(BaseHTTPRequestHandler):
    """Handles incoming REST API requests and web static files for the Quanthreum node."""

    def log_message(self, format, *args):
        return  # Suppress default server logs for clean terminal output

    def _send_json(self, status_code: int, data: dict):
        response = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _serve_file(self, filepath: str, content_type: str):
        if not os.path.exists(filepath):
            self._send_json(404, {"error": f"File not found: {os.path.basename(filepath)}"})
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        blockchain: Blockchain = self.server.blockchain
        web_dir = self.server.web_dir

        # Static Web Portal serving
        if path == "/" or path == "/index.html":
            self._serve_file(os.path.join(web_dir, "index.html"), "text/html; charset=utf-8")
            return
        elif path == "/styles.css":
            self._serve_file(os.path.join(web_dir, "styles.css"), "text/css; charset=utf-8")
            return
        elif path == "/app.js":
            self._serve_file(os.path.join(web_dir, "app.js"), "application/javascript; charset=utf-8")
            return

        # API Endpoints
        if path == "/api/info":
            info = {
                "network": "Quanthreum",
                "ticker": "QTH",
                "nature": "Quantum-Resistant + Ethereum State & QVM",
                "cryptography": "Winternitz W-OTS+ (NIST Post-Quantum 128-bit)",
                "total_max_supply": TOTAL_MAX_SUPPLY,
                "circulating_supply": blockchain.get_circulating_supply(),
                "burned_fees": blockchain.consensus.total_burned_fees,
                "height": blockchain.height,
                "tip_hash": blockchain.tip.block_hash,
                "state_root": blockchain.tip.header.state_root,
                "base_fee": blockchain.current_base_fee,
                "mempool_size": len(blockchain.mempool),
                "total_blocks": len(blockchain.chain),
                "total_validators": len(blockchain.consensus.validators),
                "total_staked": blockchain.consensus.total_staked,
                "target_block_time_seconds": 6,
            }
            self._send_json(200, info)

        elif path == "/api/account":
            address = query.get("address", [""])[0]
            if not address:
                self._send_json(400, {"error": "Missing 'address' parameter"})
                return

            acc = blockchain.state.get_account(address)
            self._send_json(200, {
                "address": address,
                "balance": acc.balance,
                "nonce": acc.nonce,
                "is_contract": acc.is_contract,
                "code": acc.code,
                "storage": acc.storage,
                "is_validator": address in blockchain.consensus.validators,
                "staked_amount": blockchain.consensus.validators.get(address, 0.0),
            })

        elif path == "/api/blocks":
            limit = int(query.get("limit", [10])[0])
            blocks = [b.to_dict() for b in blockchain.chain[-limit:]]
            self._send_json(200, {"count": len(blocks), "blocks": list(reversed(blocks))})

        elif path.startswith("/api/block/"):
            param = path[len("/api/block/"):]
            found = None
            if param.isdigit():
                h = int(param)
                if 0 <= h < len(blockchain.chain):
                    found = blockchain.chain[h]
            else:
                for b in blockchain.chain:
                    if b.block_hash == param:
                        found = b
                        break
            if found:
                self._send_json(200, found.to_dict())
            else:
                self._send_json(404, {"error": "Block not found"})

        elif path in ("/api/security/scan", "/api/security/scan/"):
            target_addr = query.get("address", [""])[0]
            chain = query.get("chain", ["ethereum"])[0]
            if not target_addr:
                self._send_json(400, {"error": "Missing 'address' parameter to scan"})
                return
            report = scan_address_quantum_vulnerability(target_addr, chain=chain)
            self._send_json(200, report)

        else:
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        blockchain: Blockchain = self.server.blockchain

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        data = {}
        if content_length > 0:
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                self._send_json(400, {"error": "Invalid JSON payload"})
                return

        # 1. Raw Transaction Submission
        if path == "/api/tx/submit":
            try:
                tx = Transaction.from_dict(data)
                success, msg = blockchain.add_transaction(tx)
                if success:
                    self._send_json(200, {"status": "success", "tx_hash": tx.tx_hash, "message": msg})
                else:
                    self._send_json(400, {"status": "rejected", "error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 2. Wallet Generation (48-Word Post-Quantum Seed)
        elif path == "/api/wallet/create":
            try:
                kp = QuantumKeyPair()
                self._send_json(200, {
                    "address": kp.address,
                    "mnemonic": kp.mnemonic,
                    "seed": kp.seed_hex,
                    "public_key": kp.public_key_hex,
                    "word_count": 48,
                    "standard": "Winternitz W-OTS+ (NIST 128-bit Post-Quantum)"
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path == "/api/wallet/restore":
            try:
                from .mnemonic import validate_mnemonic
                mnemonic = data.get("mnemonic", "").strip()
                valid, msg = validate_mnemonic(mnemonic)
                if not valid:
                    self._send_json(400, {"error": msg})
                    return

                kp = QuantumKeyPair.from_mnemonic(mnemonic)
                self._send_json(200, {
                    "status": "success",
                    "address": kp.address,
                    "mnemonic": mnemonic,
                    "seed": kp.seed_hex,
                    "public_key": kp.public_key_hex,
                    "word_count": 48
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 3. Web Send Transfer
        elif path == "/api/wallet/send":
            try:
                seed = data.get("seed")
                recipient = data.get("recipient")
                amount = float(data.get("amount", 0))

                kp = QuantumKeyPair.from_seed_hex(seed)
                wallet = QuantumWallet(kp)
                nonce = blockchain.state.get_nonce(wallet.address)

                tx = wallet.create_transfer_tx(
                    recipient_address=recipient,
                    amount=amount,
                    nonce=nonce,
                    gas_price=blockchain.current_base_fee
                )
                success, msg = blockchain.add_transaction(tx)
                if success:
                    self._send_json(200, {"status": "success", "tx_hash": tx.tx_hash, "message": msg})
                else:
                    self._send_json(400, {"status": "rejected", "error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 4. Smart Contract Deployment
        elif path == "/api/contract/deploy":
            try:
                seed = data.get("seed")
                code = data.get("code")
                initial_value = float(data.get("initial_value", 0.0))

                kp = QuantumKeyPair.from_seed_hex(seed)
                wallet = QuantumWallet(kp)
                nonce = blockchain.state.get_nonce(wallet.address)

                tx = wallet.create_deploy_tx(
                    contract_code=code,
                    nonce=nonce,
                    initial_value=initial_value,
                    gas_price=blockchain.current_base_fee
                )
                success, msg = blockchain.add_transaction(tx)
                if success:
                    self._send_json(200, {"status": "success", "tx_hash": tx.tx_hash, "message": msg})
                else:
                    self._send_json(400, {"status": "rejected", "error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 5. Smart Contract Call
        elif path == "/api/contract/call":
            try:
                seed = data.get("seed")
                contract = data.get("contract")
                action = data.get("action")
                params = data.get("params", {})
                value = float(data.get("value", 0.0))

                kp = QuantumKeyPair.from_seed_hex(seed)
                wallet = QuantumWallet(kp)
                nonce = blockchain.state.get_nonce(wallet.address)

                tx = wallet.create_call_tx(
                    contract_address=contract,
                    action=action,
                    params=params,
                    nonce=nonce,
                    value=value,
                    gas_price=blockchain.current_base_fee
                )
                success, msg = blockchain.add_transaction(tx)
                if success:
                    self._send_json(200, {"status": "success", "tx_hash": tx.tx_hash, "message": msg})
                else:
                    self._send_json(400, {"status": "rejected", "error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 6. Q-PoS Validator Staking
        elif path == "/api/validator/stake":
            try:
                seed = data.get("seed")
                amount = float(data.get("amount", 0.0))

                kp = QuantumKeyPair.from_seed_hex(seed)
                addr = kp.address
                balance = blockchain.state.get_balance(addr)

                if balance < amount:
                    self._send_json(400, {"error": f"Insufficient balance: have {balance} QTH, need {amount} QTH"})
                    return

                # Deduct from spendable and lock in consensus
                blockchain.state.sub_balance(addr, amount)
                success, msg = blockchain.consensus.register_validator(addr, amount)
                blockchain.save()

                if success:
                    self._send_json(200, {
                        "status": "success",
                        "validator": addr,
                        "staked_total": blockchain.consensus.validators[addr],
                        "message": msg
                    })
                else:
                    self._send_json(400, {"error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 7. Propose and Mine Block (Q-PoS)
        elif path == "/api/validator/mine_block":
            try:
                validator = data.get("validator_address")
                if not validator:
                    # Select from active validators or default
                    if blockchain.consensus.validators:
                        validator = list(blockchain.consensus.validators.keys())[0]
                    else:
                        validator = "0xQTH_0000000000000000000000000000000000000001"

                success, block, msg = blockchain.propose_and_mine_block(
                    validator_address=validator,
                    extra_data=data.get("extra_data", "Quanthreum Q-PoS Block")
                )

                if success:
                    self._send_json(200, {
                        "status": "success",
                        "block_number": block.header.number,
                        "block_hash": block.block_hash,
                        "state_root": block.header.state_root,
                        "validator": validator,
                        "gas_used": block.header.gas_used,
                        "transactions_count": len(block.transactions),
                        "circulating_supply": blockchain.get_circulating_supply(),
                        "burned_fees": blockchain.consensus.total_burned_fees,
                        "message": msg
                    })
                else:
                    self._send_json(400, {"status": "rejected", "error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 8. Security Gateway: Quantum Signature Verification (B2B API)
        elif path == "/api/security/verify":
            payload_hash = data.get("payload_hash")
            pub_key = data.get("public_key")
            sig = data.get("signature")
            if not payload_hash or not pub_key or not sig:
                self._send_json(400, {"error": "Missing required fields: payload_hash, public_key, signature"})
                return
            result = verify_enterprise_transaction(payload_hash, pub_key, sig)
            self._send_json(200, result)

        # 9. Security Gateway: Quantum Payload Signing (B2B API Sandbox)
        elif path == "/api/security/sign":
            seed = data.get("seed")
            payload = data.get("payload", "")
            if not seed:
                self._send_json(400, {"error": "Missing 'seed' parameter"})
                return
            try:
                kp = QuantumKeyPair.from_seed_hex(seed)
                digest = hashlib.sha256(payload.encode("utf-8")).digest()
                signature = kp.sign(digest)
                self._send_json(200, {
                    "status": "success",
                    "address": kp.address,
                    "public_key": kp.public_key_hex,
                    "payload_hash": digest.hex(),
                    "signature": signature,
                    "algorithm": "Winternitz W-OTS+ (SHA3-256)",
                    "standard": "NIST Post-Quantum 128-bit"
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        else:
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})


class QuanthreumNode:
    """Full Quanthreum Node controller with embedded Web Portal."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8545, data_dir: str = "./quanthreum_data"):
        self.host = host
        self.port = port
        self.blockchain = Blockchain(data_dir=data_dir)
        self.web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
        self.server = ThreadedHTTPServer((self.host, self.port), NodeRequestHandler)
        self.server.blockchain = self.blockchain
        self.server.web_dir = self.web_dir
        self.is_running = False

    def start(self):
        self.is_running = True
        print(f"============================================================")
        print(f"  QUANTHREUM (QTH) FULL NODE & WEB PORTAL")
        print(f"  --> Web Portal & Explorer: http://{self.host}:{self.port}")
        print(f"  --> REST API Base:         http://{self.host}:{self.port}/api/info")
        print(f"  Architecture: Quantum-Resistant (W-OTS+) + Ethereum QVM")
        print(f"  Total Max Supply: 100,000,000 QTH")
        print(f"  Current Block Height: #{self.blockchain.height}")
        print(f"  Circulating Supply: {self.blockchain.get_circulating_supply():,.4f} QTH")
        print(f"============================================================")
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.stop()

    def start_background(self):
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.server.shutdown()
            self.server.server_close()
            print("Quanthreum Node stopped.")
