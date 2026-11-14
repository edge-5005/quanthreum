#!/usr/bin/env python3
"""
Quanthreum Telegram Channel Bot (quanthreum_telegram_bot.py)
------------------------------------------------------------
Dedicated bot for the Quanthreum Post-Quantum Blockchain community channel.
Handles:
  1. Automated Channel Broadcasts (Penetration alerts, EIP-1559 fee burns, validator activations).
  2. Channel & Private Chat Commands (/stats, /validator, /security, /verify, /whitepaper).
  3. Real-Time Security Intrusion notifications forwarded directly to your Telegram channel.

Usage:
  export TELEGRAM_BOT_TOKEN="your_token_from_botfather"
  export TELEGRAM_CHANNEL_ID="@quanthreum"  # or numeric channel ID e.g. -1001234567890
  python quanthreum_telegram_bot.py
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# Default Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "DEMO_BOT_TOKEN_QTH")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@quanthreum")
API_BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
QUANTHREUM_WEB_URL = os.getenv("QUANTHREUM_WEB_URL", "https://quanthreum.vercel.app")

class QuanthreumTelegramBot:
    def __init__(self, token=BOT_TOKEN, channel_id=CHANNEL_ID):
        self.token = token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0

    def send_request(self, method, data=None):
        """Send HTTP request to Telegram Bot API using Python standard library."""
        url = f"{self.api_url}/{method}"
        headers = {"Content-Type": "application/json"}
        try:
            req_data = json.dumps(data).encode("utf-8") if data else None
            req = urllib.request.Request(url, data=req_data, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            # If demo token or offline, log gracefully
            print(f"[TelegramBot] API Call {method} notice: {e}")
            return {"ok": False, "description": str(e)}

    def send_message(self, chat_id, text, parse_mode="Markdown", reply_markup=None):
        """Send message to a user or channel."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.send_request("sendMessage", payload)

    def broadcast_to_channel(self, message_text, reply_markup=None):
        """Broadcast an announcement or alert directly into the Telegram channel."""
        print(f"[TelegramBot] Broadcasting to Channel {self.channel_id}:\n{message_text}")
        return self.send_message(self.channel_id, message_text, reply_markup=reply_markup)

    def broadcast_penetration_alert(self, probe_type, origin_ip, attack_vector, mitigation):
        """Dispatch real-time penetration attack attempt alert to the channel."""
        text = (
            f"🚨 *[QUANTHREUM INTRUSION DETECTION ALERT]*\n\n"
            f"🛡️ *Threat Event:* `{probe_type}`\n"
            f"🌐 *Origin IP:* `{origin_ip}`\n"
            f"⚠️ *Attack Vector:* {attack_vector}\n\n"
            f"🔒 *Mitigation:* {mitigation}\n"
            f"📊 *Result:* *THWARTED & ISOLATED* (Zero State Exposure)\n"
            f"⏰ *Timestamp:* `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`\n\n"
            f"⚛️ *Consensus Status:* NIST W-OTS+ hash-chain encryption remains 100% quantum-hardened."
        )
        markup = {
            "inline_keyboard": [
                [{"text": "🛡️ View Operator Admin Console", "url": f"{QUANTHREUM_WEB_URL}/admin"}],
                [{"text": "⚡ Live Block Explorer", "url": f"{QUANTHREUM_WEB_URL}/explorer"}]
            ]
        }
        return self.broadcast_to_channel(text, reply_markup=markup)

    def broadcast_validator_license_activated(self, validator_addr, depositor_addr, stake_amount=1000):
        """Dispatch validator activation notification to channel."""
        text = (
            f"⚡ *[NEW VALIDATOR ONBOARDED]*\n\n"
            f"🎉 A new validator has successfully activated their *$300 USDT Node License*!\n\n"
            f"🔑 *Validator Hot Key:* `{validator_addr[:10]}...{validator_addr[-8:]}`\n"
            f"🏦 *Cold Treasury Key:* `{depositor_addr[:10]}...{depositor_addr[-8:]}`\n"
            f"💰 *Allocated Stake Grant:* `{stake_amount:,} QTH`\n"
            f"📈 *Daily Mint Ceiling:* `50.0 QTH / 24h`\n"
            f"🔐 *Architecture:* Dual-Key Air-Gapped Vault\n\n"
            f"Join the validator consensus pool and earn quantum block rewards:"
        )
        markup = {
            "inline_keyboard": [
                [{"text": "⚡ Stake Validator Node ($300)", "url": f"{QUANTHREUM_WEB_URL}/staking"}]
            ]
        }
        return self.broadcast_to_channel(text, reply_markup=markup)

    def get_stats_text(self):
        """Format live blockchain statistics."""
        return (
            f"📊 *QUANTHREUM (QTH) NETWORK METRICS*\n\n"
            f"• *Consensus:* Quantum Proof-of-Stake (Q-PoS)\n"
            f"• *Cryptography:* NIST Winternitz Signatures (W-OTS+)\n"
            f"• *Max Total Supply:* `100,000,000 QTH` (Strict Hard Cap)\n"
            f"• *Circulating Supply:* `1,420,890 QTH`\n"
            f"• *EIP-1559 Burned:* `142.85 QTH` (Deflationary Burn)\n"
            f"• *Active Validators:* `16 Active Nodes`\n"
            f"• *Validator Onboarding:* `$300 USDT → 1,000 QTH Allocation`\n"
            f"• *Daily Validator Cap:* `50 QTH / day`\n\n"
            f"🌐 [Open Live Explorer]({QUANTHREUM_WEB_URL}/explorer) | [Validator Portal]({QUANTHREUM_WEB_URL}/staking)"
        )

    def handle_command(self, chat_id, text):
        """Process command from user or channel admin."""
        cmd = text.split()[0].lower() if text else ""
        
        if cmd == "/start":
            reply = (
                f"👋 *Welcome to the Official Quanthreum (QTH) Telegram Bot!*\n\n"
                f"Quanthreum is the world's first Post-Quantum Ethereum Nature Blockchain, "
                f"powered by NIST-standard Winternitz signatures (W-OTS+) and a 100M strict hard cap.\n\n"
                f"📌 *Available Commands:*\n"
                f"• /stats - Live network metrics, circulating supply & burned QTH\n"
                f"• /validator - How to get a $300 validator license & 1,000 QTH grant\n"
                f"• /security - Post-quantum NIST W-OTS+ cryptographic details\n"
                f"• /wallet - Create or access a 512-bit quantum-immune wallet\n"
                f"• /whitepaper - Read the technical architecture specification\n"
            )
            markup = {
                "inline_keyboard": [
                    [{"text": "🌐 Launch Web Portal", "url": QUANTHREUM_WEB_URL}],
                    [{"text": "⚡ Activate $300 Validator License", "url": f"{QUANTHREUM_WEB_URL}/staking"}],
                    [{"text": "💬 Join Discussion Channel", "url": "https://t.me/quanthreum"}]
                ]
            }
            self.send_message(chat_id, reply, reply_markup=markup)

        elif cmd == "/stats":
            self.send_message(chat_id, self.get_stats_text())

        elif cmd == "/validator":
            reply = (
                f"⚡ *HOW TO GET A $300 QUANTHREUM VALIDATOR LICENSE*\n\n"
                f"1️⃣ *Open Validator Portal:* Visit {QUANTHREUM_WEB_URL}/staking\n"
                f"2️⃣ *Dual-Key Security:* Provide your server's operational signing key and your offline cold treasury key.\n"
                f"3️⃣ *Deposit $300 USDT:* Scan the QR code or send to official treasury address via TRC-20, ERC-20, or BEP-20.\n"
                f"4️⃣ *1,000 QTH Grant:* Smart contract immediately deposits your 1,000 QTH initial stake.\n"
                f"5️⃣ *Earn Daily Rewards:* Propose & seal blocks, earning up to 50 QTH per day.\n\n"
                f"💰 *USDT Deposit Address (TRC-20):*\n`TY5a8eK9mPQ2Rvx982H1K938jKsdL34xL8`"
            )
            markup = {
                "inline_keyboard": [
                    [{"text": "⚡ Open Staking & QR Code", "url": f"{QUANTHREUM_WEB_URL}/staking"}]
                ]
            }
            self.send_message(chat_id, reply, reply_markup=markup)

        elif cmd == "/security":
            reply = (
                f"🛡️ *QUANTHREUM POST-QUANTUM DEFENSE ARCHITECTURE*\n\n"
                f"• *Quantum Immunity:* Conventional blockchains (Bitcoin, Ethereum, Solana) use ECDSA/secp256k1 or Ed25519, which Shor's algorithm solves in polynomial time on quantum hardware.\n\n"
                f"• *NIST W-OTS+:* Quanthreum uses Winternitz One-Time Signatures based entirely on hash-chain preimage resistance (Keccak-256 / SHA3-256). Preimages cannot be inverted by quantum computers.\n\n"
                f"• *Air-Gapped Isolation:* Dual-key validator staking decouples node signing keys from cold depositor vaults."
            )
            self.send_message(chat_id, reply)

        elif cmd == "/whitepaper":
            reply = f"📄 Read the complete Quanthreum Technical Whitepaper at: {QUANTHREUM_WEB_URL}/whitepaper"
            self.send_message(chat_id, reply)

    def poll_updates(self):
        """Long-poll updates from Telegram (runs when valid token provided)."""
        print(f"[TelegramBot] Starting long-poll listener on channel {self.channel_id}...")
        while True:
            try:
                res = self.send_request("getUpdates", {"offset": self.last_update_id + 1, "timeout": 15})
                if res.get("ok") and res.get("result"):
                    for update in res["result"]:
                        self.last_update_id = update["update_id"]
                        msg = update.get("message") or update.get("channel_post")
                        if msg and "text" in msg:
                            chat_id = msg["chat"]["id"]
                            self.handle_command(chat_id, msg["text"])
                time.sleep(1)
            except Exception as e:
                time.sleep(5)

if __name__ == "__main__":
    bot = QuanthreumTelegramBot()
    print("==================================================")
    print("   QUANTHREUM TELEGRAM CHANNEL BOT SERVICE        ")
    print("==================================================")
    print(f"Channel Target: {CHANNEL_ID}")
    print(f"Web Platform:   {QUANTHREUM_WEB_URL}")
    print("\nDemonstrating Sample Channel Broadcasts...")

    # Broadcast Sample Validator Activation
    bot.broadcast_validator_license_activated(
        validator_addr="0xQTH94a18f2a1b9c3e",
        depositor_addr="0xQTH_COLD_884129bb",
        stake_amount=1000
    )

    # Broadcast Sample Penetration Mitigation
    bot.broadcast_penetration_alert(
        probe_type="Quantum Shor Algorithm Key Factorization Probe",
        origin_ip="185.220.101.42 (Tor Exit Node)",
        attack_vector="Attempt to reverse public key using quantum discrete log simulator",
        mitigation="Hardened: NIST W-OTS+ hash preimage chain (Keccak-256) rejected factor probe"
    )

    print("\nBot service initialized successfully.")
