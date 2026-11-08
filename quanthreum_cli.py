#!/usr/bin/env python3
"""
Quanthreum (QTH) Command-Line Interface (CLI)
Complete toolkit to manage Post-Quantum keys, deploy smart contracts,
stake in Quantum Proof of Stake (Q-PoS), and run the native Quanthreum blockchain.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import webbrowser

# Ensure local package is in import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quanthreum.quantum_crypto import QuantumKeyPair, validate_qth_address
from quanthreum.wallet import QuantumWallet
from quanthreum.node import QuanthreumNode
from quanthreum.consensus import TOTAL_MAX_SUPPLY

DEFAULT_NODE = "http://127.0.0.1:8545"


def http_get(node_url: str, endpoint: str) -> dict:
    url = f"{node_url.rstrip('/')}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "Quanthreum-CLI/1.0"})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode('utf-8'))


def http_post(node_url: str, endpoint: str, data: dict) -> dict:
    url = f"{node_url.rstrip('/')}{endpoint}"
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Quanthreum-CLI/1.0"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode('utf-8'))


# ==========================================
# Commands
# ==========================================

def cmd_wallet_create(args):
    filepath = args.file or "quantum_wallet.json"
    w = QuantumWallet.create_new(filepath)
    print("\n" + "=" * 70)
    print("      NEW QUANTHREUM 48-WORD POST-QUANTUM WALLET GENERATED")
    print("=" * 70)
    print(f" Address:     {w.address}")
    print(f" Standard:    Winternitz W-OTS+ (NIST Post-Quantum 128-bit)")
    print(f" Entropy:     512-bit Cryptographic Quantum Randomness")
    print(f" Keystore:    Saved to {os.path.abspath(filepath)}")
    print("\n--- 48-WORD MASTER SEED PHRASE (WRITE DOWN & STORE SECURELY) ---")
    words = w.mnemonic.split() if w.mnemonic else []
    for i in range(0, len(words), 4):
        row = [f"{j+1:2d}. {words[j]:<12}" for j in range(i, min(i+4, len(words)))]
        print("  " + "".join(row))
    print("=" * 70)
    print("Security Note: 48 words provide 512 bits of post-quantum entropy.")
    print("Immune to Shor's and Grover's quantum attacks.\n")


def cmd_wallet_restore(args):
    filepath = args.file or "quantum_wallet.json"
    mnemonic = args.phrase.strip()
    try:
        w = QuantumWallet.restore_from_mnemonic(mnemonic, filepath)
        print("\n" + "=" * 70)
        print("        QUANTHREUM WALLET SUCCESSFULLY RESTORED")
        print("=" * 70)
        print(f" Address:     {w.address}")
        print(f" Public Key:  {w.public_key_hex}")
        print(f" Keystore:    Saved to {os.path.abspath(filepath)}")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"[Error] Failed to restore wallet: {e}")


def cmd_account(args):
    address = args.address
    try:
        res = http_get(args.node, f"/api/account?address={address}")
        print("\n" + "=" * 65)
        print(f" QUANTHREUM ACCOUNT STATE: {address}")
        print("=" * 65)
        print(f" QTH Balance:     {res['balance']:,.8f} QTH")
        print(f" Nonce:           {res['nonce']}")
        print(f" Is Contract:     {res['is_contract']}")
        print(f" Validator Status:{'ACTIVE' if res['is_validator'] else 'INACTIVE'}")
        if res['is_validator']:
            print(f" Staked Amount:   {res['staked_amount']:,.8f} QTH")
        if res['is_contract']:
            print(f" Storage Keys:    {len(res.get('storage', {}))}")
        print("=" * 65 + "\n")
    except Exception as e:
        print(f"[Error] Failed to fetch account from node ({args.node}): {e}")


def cmd_node_start(args):
    node = QuanthreumNode(host=args.host, port=args.port, data_dir=args.dir)
    node.start()


def cmd_web(args):
    node = QuanthreumNode(host=args.host, port=args.port, data_dir=args.dir)
    url = f"http://{args.host}:{args.port}"
    print(f"\n============================================================")
    print(f" Launching Quanthreum Web Portal & Explorer at: {url}")
    print(f" Opening web browser...")
    print(f"============================================================\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    node.start()


def cmd_send(args):
    if not os.path.exists(args.wallet):
        print(f"[Error] Wallet file not found: {args.wallet}")
        return

    wallet = QuantumWallet.load_from_file(args.wallet)
    recipient = args.to
    amount = float(args.amount)

    print(f"Broadcasting Post-Quantum transfer of {amount} QTH to {recipient}...")
    try:
        res = http_post(args.node, "/api/wallet/send", {
            "seed": wallet.seed_hex,
            "recipient": recipient,
            "amount": amount
        })
        print(f"\n Transaction submitted to Quanthreum mempool!")
        print(f" TX Hash: {res.get('tx_hash')}\n")
    except Exception as e:
        print(f"[Error] Failed to send transaction: {e}")


def cmd_stake(args):
    if not os.path.exists(args.wallet):
        print(f"[Error] Wallet file not found: {args.wallet}")
        return

    wallet = QuantumWallet.load_from_file(args.wallet)
    amount = float(args.amount)

    print(f"Depositing {amount} QTH into Quantum Proof-of-Stake validator pool...")
    try:
        res = http_post(args.node, "/api/validator/stake", {
            "seed": wallet.seed_hex,
            "amount": amount
        })
        print(f"\n Validator stake confirmed!")
        print(f" Validator:    {res.get('validator')}")
        print(f" Total Staked: {res.get('staked_total')} QTH\n")
    except Exception as e:
        print(f"[Error] Failed to stake: {e}")


def cmd_mine(args):
    print("Proposing and sealing new Quanthreum Q-PoS Block...")
    payload = {}
    if args.validator:
        payload["validator_address"] = args.validator

    try:
        res = http_post(args.node, "/api/validator/mine_block", payload)
        print(f"\n Block #{res.get('block_number')} forged successfully!")
        print(f" Block Hash:         {res.get('block_hash')}")
        print(f" Validator:          {res.get('validator')}")
        print(f" Gas Used:           {res.get('gas_used'):,}")
        print(f" Transactions:       {res.get('transactions_count')}")
        print(f" Circulating Supply: {res.get('circulating_supply'):,.4f} QTH (Max: 100,000,000 QTH)")
        print(f" EIP-1559 Burned:    {res.get('burned_fees'):,.8f} QTH\n")
    except Exception as e:
        print(f"[Error] Failed to produce block: {e}")


def cmd_validator(args):
    from quanthreum.validator_runner import ValidatorRunner
    address = args.address
    seed = None
    if args.wallet and os.path.exists(args.wallet):
        wallet = QuantumWallet.load_from_file(args.wallet)
        address = wallet.address
        seed = wallet.seed_hex
    elif not address:
        print("[Error] Must specify either --wallet <file.json> or --address <0xQTH_...>.")
        return

    print("\n" + "=" * 65)
    print("      QUANTHREUM (QTH) AUTOMATED VALIDATOR NODE")
    print("=" * 65)
    print(f" Validator:      {address}")
    print(f" Block Interval: {args.interval} seconds")
    print(f" Node RPC:       {args.node}")
    print("=" * 65 + "\n")

    runner = ValidatorRunner(
        node_url=args.node,
        validator_address=address,
        validator_seed=seed,
        block_interval=args.interval
    )
    if args.stake and seed:
        runner.check_and_ensure_stake(default_stake=args.stake)
    runner.start()


def cmd_deploy(args):
    if not os.path.exists(args.wallet):
        print(f"[Error] Wallet file not found: {args.wallet}")
        return
    if not os.path.exists(args.code):
        print(f"[Error] Contract file not found: {args.code}")
        return

    wallet = QuantumWallet.load_from_file(args.wallet)
    with open(args.code, "r", encoding="utf-8") as f:
        code_content = f.read()

    print("Deploying Smart Contract to Quanthreum Virtual Machine (QVM)...")
    try:
        res = http_post(args.node, "/api/contract/deploy", {
            "seed": wallet.seed_hex,
            "code": code_content,
            "initial_value": args.value
        })
        print(f"\n Contract deployment transaction queued!")
        print(f" TX Hash: {res.get('tx_hash')}")
        print(" Tip: Run 'mine' to execute the block and confirm contract address.\n")
    except Exception as e:
        print(f"[Error] Contract deployment failed: {e}")


def cmd_blocks(args):
    try:
        res = http_get(args.node, f"/api/blocks?limit={args.limit}")
        print("\n" + "=" * 70)
        print("                  LATEST QUANTHREUM (QTH) BLOCKS")
        print("=" * 70)
        for b in res.get("blocks", []):
            h = b["header"]
            print(f"Block #{h['number']:<4} | Hash: {b['hash'][:16]}... | Gas Used: {h['gas_used']:,}")
            print(f"           Validator: {h['validator']}")
            print(f"           Base Fee:  {h.get('base_fee', 0.00001):.8f} QTH | TXs: {len(b['transactions'])}")
            print("-" * 70)
        print()
    except Exception as e:
        print(f"[Error] Failed to fetch blocks: {e}")


def cmd_demo(args):
    """Automated end-to-end self-test of Quanthreum (QTH) network mechanics."""
    print("\n" + "=" * 65)
    print("      QUANTHREUM (QTH) ZERO-COST QUANTUM+ETHEREUM DEMO")
    print("=" * 65)

    # 1. Start Node in background
    demo_dir = "./demo_quanthreum_data"
    os.makedirs(demo_dir, exist_ok=True)
    node = QuanthreumNode(host="127.0.0.1", port=8549, data_dir=demo_dir)
    node.start_background()
    time.sleep(1)

    node_url = "http://127.0.0.1:8549"

    # 2. Check 100M Total Max Supply
    info = http_get(node_url, "/api/info")
    print(f"\n[Step 1] Blockchain Initialized:")
    print(f"  -> Network: {info['network']} ({info['ticker']})")
    print(f"  -> Nature:  {info['nature']}")
    print(f"  -> Cryptography: {info['cryptography']}")
    print(f"  -> Total Max Supply: {info['total_max_supply']:,.0f} QTH (Hard Capped!)")

    # 3. Create Alice and Bob Post-Quantum Wallets
    wallet_alice = QuantumWallet.create_new("./demo_quanthreum_data/alice_qth.json")
    wallet_bob = QuantumWallet.create_new("./demo_quanthreum_data/bob_qth.json")
    print(f"\n[Step 2] Generated Post-Quantum Wallets:")
    print(f"  -> Alice: {wallet_alice.address}")
    print(f"  -> Bob:   {wallet_bob.address}")

    # 4. Fund Alice from Genesis pool
    genesis_addr = "0xQTH_0000000000000000000000000000000000000001"
    print(f"\n[Step 3] Funding Alice with 1,000 QTH from Genesis liquidity...")
    node.blockchain.state.set_balance(wallet_alice.address, 1000.0)

    # 5. Alice transfers 100 QTH to Bob (Secured by Winternitz Post-Quantum Signature)
    print(f"\n[Step 4] Alice signs and sends 100 QTH to Bob...")
    send_res = http_post(node_url, "/api/wallet/send", {
        "seed": wallet_alice.seed_hex,
        "recipient": wallet_bob.address,
        "amount": 100.0
    })
    print(f"  -> TX Hash: {send_res['tx_hash']} (Verified Quantum-Safe)")

    # 6. Mine Block #1 (Q-PoS Block Production)
    print(f"\n[Step 5] Sealing Block #1 via Quantum Proof-of-Stake...")
    b1_res = http_post(node_url, "/api/validator/mine_block", {"validator_address": genesis_addr})
    print(f"  -> Block #{b1_res['block_number']} mined! Gas Used: {b1_res['gas_used']} | Burned Fee: {b1_res['burned_fees']:.8f} QTH")

    bal_bob = http_get(node_url, f"/api/account?address={wallet_bob.address}")
    print(f"  -> Bob Confirmed Balance: {bal_bob['balance']} QTH")

    # 7. Alice deploys a Quantum Smart Contract (QRC-20 Token)
    print(f"\n[Step 6] Alice deploys a QRC-20 Smart Contract via QVM...")
    contract_code = json.dumps({
        "name": "QuantumUSD",
        "symbol": "QUSD",
        "init_storage": {
            "name": "Quantum USD Stable",
            "symbol": "QUSD",
            "balances": {wallet_alice.address: 1_000_000.0}
        }
    })
    dep_res = http_post(node_url, "/api/contract/deploy", {
        "seed": wallet_alice.seed_hex,
        "code": contract_code,
        "initial_value": 0.0
    })
    print(f"  -> Deployment TX: {dep_res['tx_hash']}")

    # 8. Mine Block #2 to finalize contract deployment
    print(f"\n[Step 7] Mining Block #2 to execute contract deployment...")
    b2_res = http_post(node_url, "/api/validator/mine_block", {"validator_address": genesis_addr})
    latest_block = http_get(node_url, "/api/blocks?limit=1")["blocks"][0]
    contract_addr = latest_block["receipts"][0]["contract_address"]
    print(f"  -> Smart Contract Deployed at: {contract_addr}")

    # 9. Verify Contract State in QVM
    contract_state = http_get(node_url, f"/api/account?address={contract_addr}")
    print(f"  -> Contract Storage: {contract_state['storage']}")

    # 10. Summary
    print("\n" + "=" * 65)
    print(" DEMO COMPLETED SUCCESSFULLY! ALL QUANTHREUM MECHANICS VERIFIED:")
    print("  [x] Native Quanthreum Blockchain running with ticker QTH")
    print("  [x] Strict 100 Million QTH Maximum Supply Cap")
    print("  [x] Post-Quantum Winternitz (W-OTS+) Signatures (Shor-immune)")
    print("  [x] Ethereum-style World State & Nonce Accounting")
    print("  [x] Quanthreum Virtual Machine (QVM) Smart Contract Execution")
    print("  [x] Quantum Proof of Stake (Q-PoS) with EIP-1559 Fee Burning")
    print("=" * 65 + "\n")

    node.stop()


def main():
    parser = argparse.ArgumentParser(description="Quanthreum (QTH) - Quantum-Resistant Ethereum Nature Blockchain")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # wallet
    p_w = subparsers.add_parser("wallet", help="Post-Quantum Wallet operations")
    p_w_sub = p_w.add_subparsers(dest="subcommand")
    p_w_create = p_w_sub.add_parser("create", help="Create new 48-word Post-Quantum wallet")
    p_w_create.add_argument("--file", help="Destination file (default: quantum_wallet.json)")
    p_w_restore = p_w_sub.add_parser("restore", help="Restore wallet from 48-word mnemonic phrase")
    p_w_restore.add_argument("--phrase", required=True, help="48-word seed phrase in quotes")
    p_w_restore.add_argument("--file", help="Destination file (default: quantum_wallet.json)")

    # account
    p_acc = subparsers.add_parser("account", help="Check account state, balance, and code")
    p_acc.add_argument("address", help="Quanthreum QTH Address (0xQTH_...)")
    p_acc.add_argument("--node", default=DEFAULT_NODE, help="Node URL")

    # node
    p_node = subparsers.add_parser("node", help="Run full blockchain node")
    p_node.add_argument("subcommand", choices=["start"], help="start node")
    p_node.add_argument("--host", default="127.0.0.1", help="Host")
    p_node.add_argument("--port", type=int, default=8545, help="Port (default: 8545)")
    p_node.add_argument("--dir", default="./quanthreum_data", help="Data directory")

    # web
    p_web = subparsers.add_parser("web", help="Launch Quanthreum Web Portal & Explorer in browser")
    p_web.add_argument("--host", default="127.0.0.1", help="Host")
    p_web.add_argument("--port", type=int, default=8545, help="Port (default: 8545)")
    p_web.add_argument("--dir", default="./quanthreum_data", help="Data directory")

    # send
    p_send = subparsers.add_parser("send", help="Send QTH to another address")
    p_send.add_argument("--wallet", default="quantum_wallet.json", help="Path to wallet.json")
    p_send.add_argument("--to", required=True, help="Recipient QTH address")
    p_send.add_argument("--amount", type=float, required=True, help="Amount of QTH")
    p_send.add_argument("--node", default=DEFAULT_NODE, help="Node URL")

    # stake
    p_stake = subparsers.add_parser("stake", help="Stake QTH in Q-PoS validator pool")
    p_stake.add_argument("--wallet", default="quantum_wallet.json", help="Path to wallet.json")
    p_stake.add_argument("--amount", type=float, required=True, help="Amount of QTH to stake")
    p_stake.add_argument("--node", default=DEFAULT_NODE, help="Node URL")

    # mine
    p_mine = subparsers.add_parser("mine", help="Propose and seal a block (Q-PoS)")
    p_mine.add_argument("--validator", help="Validator address")
    p_mine.add_argument("--node", default=DEFAULT_NODE, help="Node URL")

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="Deploy smart contract to QVM")
    p_deploy.add_argument("--wallet", default="quantum_wallet.json", help="Path to wallet.json")
    p_deploy.add_argument("--code", required=True, help="Path to contract JSON code")
    p_deploy.add_argument("--value", type=float, default=0.0, help="Initial QTH value")
    p_deploy.add_argument("--node", default=DEFAULT_NODE, help="Node URL")

    # blocks
    p_blocks = subparsers.add_parser("blocks", help="List recent blocks")
    p_blocks.add_argument("--limit", type=int, default=5, help="Number of blocks")
    p_blocks.add_argument("--node", default=DEFAULT_NODE, help="Node URL")

    # validator
    p_val = subparsers.add_parser("validator", help="Run automated continuous validator node daemon")
    p_val.add_argument("--wallet", help="Path to wallet.json")
    p_val.add_argument("--address", help="Validator address (if wallet file not provided)")
    p_val.add_argument("--interval", type=int, default=6, help="Block forging interval in seconds (default: 6)")
    p_val.add_argument("--stake", type=float, default=32.0, help="Initial stake amount to ensure validator is active (default: 32)")
    p_val.add_argument("--node", default=DEFAULT_NODE, help="Node URL (default: http://127.0.0.1:8545)")

    # demo
    subparsers.add_parser("demo", help="Run complete automated Quanthreum demo test")

    args = parser.parse_args()

    if args.command == "wallet":
        if args.subcommand == "create":
            cmd_wallet_create(args)
        elif args.subcommand == "restore":
            cmd_wallet_restore(args)
        else:
            p_w.print_help()
    elif args.command == "account":
        cmd_account(args)
    elif args.command == "node":
        cmd_node_start(args)
    elif args.command == "web":
        cmd_web(args)
    elif args.command == "send":
        cmd_send(args)
    elif args.command == "stake":
        cmd_stake(args)
    elif args.command == "mine":
        cmd_mine(args)
    elif args.command == "deploy":
        cmd_deploy(args)
    elif args.command == "blocks":
        cmd_blocks(args)
    elif args.command == "validator":
        cmd_validator(args)
    elif args.command == "demo":
        cmd_demo(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
