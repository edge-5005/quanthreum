import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Ensure repository root is on sys.path so quanthreum package is importable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from quanthreum.blockchain import Blockchain
from quanthreum.consensus import TOTAL_MAX_SUPPLY
from quanthreum.quantum_crypto import QuantumKeyPair
from quanthreum.transaction import Transaction
from quanthreum.wallet import QuantumWallet
from quanthreum.mnemonic import validate_mnemonic

# Initialize singleton blockchain in writable /tmp (Vercel serverless environment)
DATA_DIR = "/tmp/quanthreum_data" if os.environ.get("VERCEL") else os.path.join(BASE_DIR, "quanthreum_data")
os.makedirs(DATA_DIR, exist_ok=True)

_blockchain_instance = None


def get_blockchain():
    global _blockchain_instance
    if _blockchain_instance is None:
        _blockchain_instance = Blockchain(data_dir=DATA_DIR)
    return _blockchain_instance


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # Suppress default log messages

    def _get_path_and_query(self):
        # Vercel passes the original requested URL in x-forwarded-uri, x-vercel-original-url, or x-matched-path
        raw_url = (
            self.headers.get("x-forwarded-uri")
            or self.headers.get("x-vercel-original-url")
            or self.headers.get("x-matched-path")
            or self.path
        )
        parsed = urlparse(raw_url)
        return parsed.path, parse_qs(parsed.query)

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
        path, query = self._get_path_and_query()
        blockchain = get_blockchain()

        # Static files fallback
        web_dirs = [
            os.path.join(BASE_DIR, "public"),
            os.path.join(BASE_DIR, "web"),
        ]
        if path in ("/", "/index.html", "/web/index.html"):
            for wd in web_dirs:
                fp = os.path.join(wd, "index.html")
                if os.path.exists(fp):
                    return self._serve_file(fp, "text/html; charset=utf-8")
        elif path in ("/styles.css", "/web/styles.css"):
            for wd in web_dirs:
                fp = os.path.join(wd, "styles.css")
                if os.path.exists(fp):
                    return self._serve_file(fp, "text/css; charset=utf-8")
        elif path in ("/app.js", "/web/app.js"):
            for wd in web_dirs:
                fp = os.path.join(wd, "app.js")
                if os.path.exists(fp):
                    return self._serve_file(fp, "application/javascript; charset=utf-8")

        # API Endpoints
        if path in ("/api/info", "/api/info/"):
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

        elif path in ("/api/account", "/api/account/"):
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

        elif path in ("/api/blocks", "/api/blocks/"):
            limit = int(query.get("limit", [10])[0])
            blocks = [b.to_dict() for b in blockchain.chain[-limit:]]
            self._send_json(200, {"count": len(blocks), "blocks": list(reversed(blocks))})

        elif path.startswith("/api/block/"):
            param = path[len("/api/block/"):].rstrip("/")
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

        else:
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})

    def do_POST(self):
        path, _ = self._get_path_and_query()
        path = path.rstrip("/")
        blockchain = get_blockchain()

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
                    initial_value=initial_value,
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

        # 5. Smart Contract Execution
        elif path == "/api/contract/call":
            try:
                seed = data.get("seed")
                contract_address = data.get("contract_address")
                calldata = data.get("calldata", {})
                call_value = float(data.get("value", 0.0))

                kp = QuantumKeyPair.from_seed_hex(seed)
                wallet = QuantumWallet(kp)
                nonce = blockchain.state.get_nonce(wallet.address)

                tx = wallet.create_call_tx(
                    contract_address=contract_address,
                    calldata=calldata,
                    value=call_value,
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

        # 6. Q-PoS Validator Staking
        elif path == "/api/validator/stake":
            try:
                seed = data.get("seed")
                amount = float(data.get("amount", 0.0))

                kp = QuantumKeyPair.from_seed_hex(seed)
                wallet = QuantumWallet(kp)
                nonce = blockchain.state.get_nonce(wallet.address)

                tx = wallet.create_stake_tx(
                    staked_amount=amount,
                    nonce=nonce,
                    gas_price=blockchain.current_base_fee
                )
                success, msg = blockchain.add_transaction(tx)
                if success:
                    self._send_json(200, {
                        "status": "success",
                        "tx_hash": tx.tx_hash,
                        "validator": wallet.address,
                        "staked_total": blockchain.consensus.validators.get(wallet.address, 0.0) + amount,
                        "message": "Stake transaction submitted to mempool."
                    })
                else:
                    self._send_json(400, {"status": "rejected", "error": msg})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        # 7. Block Sealing (Q-PoS)
        elif path == "/api/validator/mine_block":
            try:
                validator = data.get("validator_address")
                extra_data = data.get("extra_data", "Quanthreum Block Sealed")
                block = blockchain.mine_pending_transactions(validator_address=validator, extra_data=extra_data)
                if block:
                    self._send_json(200, {
                        "status": "success",
                        "block_number": block.header.number,
                        "block_hash": block.block_hash,
                        "validator": block.header.validator,
                        "transactions_count": len(block.transactions),
                        "gas_used": block.header.gas_used,
                        "burned_fees": block.header.burned_fees,
                        "circulating_supply": blockchain.get_circulating_supply()
                    })
                else:
                    self._send_json(400, {"status": "failed", "error": "Consensus rejected block proposal or invalid validator."})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        else:
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})
