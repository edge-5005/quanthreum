#!/usr/bin/env pythonw
"""
Quanthreum (QTH) - Windows Validator Node & QTH Wallet Studio
A native desktop GUI tool for Windows to create 48-word QTH wallets,
stake in Quantum Proof of Stake (Q-PoS), and run full validator nodes.
"""

import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quanthreum.quantum_crypto import QuantumKeyPair, validate_qth_address
from quanthreum.wallet import QuantumWallet
from quanthreum.mnemonic import validate_mnemonic
from quanthreum.node import QuanthreumNode
from quanthreum.validator_runner import ValidatorRunner
from quanthreum.consensus import TOTAL_MAX_SUPPLY


class QuanthreumWindowsStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quanthreum (QTH) - Validator Node & Wallet Studio (Windows)")
        self.geometry("1020x720")
        self.minsize(860, 600)
        self.configure(bg="#080c18")

        # Runtime State
        self.active_wallet = None
        self.wallet_password = ""
        self.generated_keypair = None
        self.node_instance = None
        self.node_thread = None
        self.validator_runner = None
        self.validator_thread = None
        self.node_port = 8545

        # Try to load existing wallet
        default_wallet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_qth_wallet.json")
        if os.path.exists(default_wallet_path):
            try:
                self.active_wallet = QuantumWallet.load_from_file(default_wallet_path)
            except Exception:
                pass

        self._setup_styles()
        self._build_ui()
        self._check_auto_load()

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Color Palette
        self.c_bg = "#080c18"
        self.c_card = "#10162a"
        self.c_card_border = "#1f2a48"
        self.c_cyan = "#00f2fe"
        self.c_blue = "#3b82f6"
        self.c_violet = "#8b5cf6"
        self.c_emerald = "#10b981"
        self.c_rose = "#f43f5e"
        self.c_text = "#f8fafc"
        self.c_muted = "#94a3b8"

        # Notebook tabs
        self.style.configure("TNotebook", background=self.c_bg, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#151d38", foreground=self.c_muted,
                             padding=[18, 9], font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("TNotebook.Tab",
                       background=[("selected", "#1e294b")],
                       foreground=[("selected", self.c_cyan)])

    def _build_ui(self):
        # Top Header Bar
        header_frame = tk.Frame(self, bg="#0d1326", height=65)
        header_frame.pack(fill="x", side="top")

        brand_lbl = tk.Label(header_frame, text="Quanthreum (QTH)", font=("Segoe UI", 15, "bold"),
                             fg="#ffffff", bg="#0d1326")
        brand_lbl.pack(side="left", padx=(20, 8), pady=14)

        tag_lbl = tk.Label(header_frame, text="512-Bit Post-Quantum • 100M Supply • Q-PoS Node",
                           font=("Segoe UI", 9), fg=self.c_cyan, bg="#0d1326")
        tag_lbl.pack(side="left", pady=16)

        self.status_lbl = tk.Label(header_frame, text="● Node Offline", font=("Segoe UI", 9, "bold"),
                                   fg=self.c_rose, bg="#0d1326")
        self.status_lbl.pack(side="right", padx=20, pady=16)

        # Tab Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=12)

        # Create Tabs
        self.tab_wallet = tk.Frame(self.notebook, bg=self.c_bg)
        self.tab_validator = tk.Frame(self.notebook, bg=self.c_bg)
        self.tab_network = tk.Frame(self.notebook, bg=self.c_bg)

        self.notebook.add(self.tab_wallet, text="  Create QTH Wallet  ")
        self.notebook.add(self.tab_validator, text="  Validator Node Manager  ")
        self.notebook.add(self.tab_network, text="  Blockchain & Transfers  ")

        self._build_wallet_tab()
        self._build_validator_tab()
        self._build_network_tab()

    # =======================================================
    # TAB 1: CREATE QTH WALLET & RESTORE
    # =======================================================
    def _build_wallet_tab(self):
        pane = tk.PanedWindow(self.tab_wallet, orient="horizontal", bg=self.c_bg, sashwidth=6)
        pane.pack(fill="both", expand=True, padx=10, pady=10)

        # Left Column: Creation / Password / Reveal Wizard
        left_card = tk.Frame(pane, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        pane.add(left_card, minsize=460)

        lbl_step1 = tk.Label(left_card, text="Step 1: Create Wallet Password", font=("Segoe UI", 12, "bold"),
                             fg=self.c_cyan, bg=self.c_card)
        lbl_step1.pack(anchor="w", padx=16, pady=(16, 4))

        lbl_info = tk.Label(left_card, text="Protect your QTH Wallet with a password before generating the 48-word seed.",
                            font=("Segoe UI", 8), fg=self.c_muted, bg=self.c_card)
        lbl_info.pack(anchor="w", padx=16, pady=(0, 10))

        # Passwords
        tk.Label(left_card, text="Password (min 8 chars):", font=("Segoe UI", 9), fg="#fff", bg=self.c_card).pack(anchor="w", padx=16)
        self.entry_pass = tk.Entry(left_card, show="*", font=("Segoe UI", 10), bg="#090d18", fg="#fff", insertbackground="#fff")
        self.entry_pass.pack(fill="x", padx=16, pady=(3, 8))

        tk.Label(left_card, text="Confirm Password:", font=("Segoe UI", 9), fg="#fff", bg=self.c_card).pack(anchor="w", padx=16)
        self.entry_confirm = tk.Entry(left_card, show="*", font=("Segoe UI", 10), bg="#090d18", fg="#fff", insertbackground="#fff")
        self.entry_confirm.pack(fill="x", padx=16, pady=(3, 10))

        btn_reveal = tk.Button(left_card, text="Set Password & Reveal 48-Word Seed Phrase",
                               font=("Segoe UI", 10, "bold"), bg=self.c_violet, fg="#fff",
                               activebackground=self.c_blue, cursor="hand2", command=self._action_generate_and_reveal)
        btn_reveal.pack(fill="x", padx=16, pady=(0, 10))

        # New Generated Address Display Card (Visible immediately on generation)
        new_addr_frame = tk.Frame(left_card, bg="#0a0f21", bd=1, relief="solid", highlightbackground=self.c_card_border)
        new_addr_frame.pack(fill="x", padx=16, pady=(0, 10))

        na_head = tk.Frame(new_addr_frame, bg="#0a0f21")
        na_head.pack(fill="x", padx=10, pady=(6, 2))

        tk.Label(na_head, text="New Generated QTH Address:", font=("Segoe UI", 9, "bold"),
                 fg=self.c_cyan, bg="#0a0f21").pack(side="left")

        self.lbl_new_badge = tk.Label(na_head, text="READY TO GENERATE", font=("Segoe UI", 8, "bold"),
                                      fg=self.c_muted, bg="#151d38", padx=6, pady=1)
        self.lbl_new_badge.pack(side="right")

        na_row = tk.Frame(new_addr_frame, bg="#0a0f21")
        na_row.pack(fill="x", padx=10, pady=(0, 6))

        self.entry_new_addr = tk.Entry(na_row, font=("Consolas", 10, "bold"), bg="#050811", fg="#00f2fe", relief="flat")
        self.entry_new_addr.insert(0, "Click [Set Password & Reveal] to generate a new address")
        self.entry_new_addr.configure(state="readonly")
        self.entry_new_addr.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_copy_new_addr = tk.Button(na_row, text="📋 Copy", font=("Segoe UI", 8, "bold"),
                                          bg="#1f2a48", fg="#fff", cursor="hand2", command=self._action_copy_new_address)
        self.btn_copy_new_addr.pack(side="left")

        # 48-Word Seed Display Box
        tk.Label(left_card, text="48-Word Post-Quantum Seed Phrase (Hidden until revealed):",
                 font=("Segoe UI", 9, "bold"), fg="#fff", bg=self.c_card).pack(anchor="w", padx=16)

        self.txt_seed = tk.Text(left_card, height=7, font=("Consolas", 9), bg="#050811", fg="#a7f3d0",
                                wrap="word", relief="flat", padx=8, pady=8)
        self.txt_seed.insert("1.0", "--- Click [Set Password & Reveal] above to unveil your 48-word phrase ---")
        self.txt_seed.configure(state="disabled")
        self.txt_seed.pack(fill="both", expand=True, padx=16, pady=(4, 10))

        btn_row = tk.Frame(left_card, bg=self.c_card)
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        btn_copy = tk.Button(btn_row, text="📋 Copy 48 Words", font=("Segoe UI", 9),
                             bg="#1f2a48", fg="#fff", cursor="hand2", command=self._action_copy_words)
        btn_copy.pack(side="left", padx=(0, 6))

        btn_backup = tk.Button(btn_row, text="💾 Save Paper Backup (.txt)", font=("Segoe UI", 9),
                               bg="#1f2a48", fg="#fff", cursor="hand2", command=self._action_download_backup)
        btn_backup.pack(side="left", padx=(0, 6))

        self.btn_go_val_after_create = tk.Button(btn_row, text="🚀 Open Validator Node", font=("Segoe UI", 9, "bold"),
                                                bg=self.c_emerald, fg="#000", cursor="hand2",
                                                command=self._action_lock_and_go_validator)
        self.btn_go_val_after_create.pack(side="left", padx=(0, 6))

        btn_reset = tk.Button(btn_row, text="✨ New / Reset", font=("Segoe UI", 8),
                              bg="#151d38", fg=self.c_muted, cursor="hand2", command=self._action_reset_creation_card)
        btn_reset.pack(side="left")

        # Right Column: Active QTH Wallet Status & Restore
        right_card = tk.Frame(pane, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        pane.add(right_card, minsize=420)

        tk.Label(right_card, text="Active QTH Wallet Status", font=("Segoe UI", 12, "bold"),
                 fg=self.c_cyan, bg=self.c_card).pack(anchor="w", padx=16, pady=(16, 12))

        # Address Box
        tk.Label(right_card, text="Quanthreum Address (0xQTH_...):", font=("Segoe UI", 9), fg=self.c_muted, bg=self.c_card).pack(anchor="w", padx=16)
        self.lbl_active_addr = tk.Entry(right_card, font=("Consolas", 10), bg="#090d18", fg=self.c_cyan, relief="flat")
        self.lbl_active_addr.insert(0, "No active wallet loaded")
        self.lbl_active_addr.configure(state="readonly")
        self.lbl_active_addr.pack(fill="x", padx=16, pady=(2, 10))

        # Stats Card
        stat_box = tk.Frame(right_card, bg="#0a0f21", bd=1, relief="solid", highlightbackground=self.c_card_border)
        stat_box.pack(fill="x", padx=16, pady=(0, 16))

        self.lbl_bal_val = tk.Label(stat_box, text="0.0000 QTH", font=("Segoe UI", 14, "bold"), fg=self.c_emerald, bg="#0a0f21")
        self.lbl_bal_val.pack(anchor="w", padx=12, pady=(10, 2))

        self.lbl_stat_sub = tk.Label(stat_box, text="Spendable Balance • Nonce: 0 • Validator: INACTIVE",
                                     font=("Segoe UI", 8), fg=self.c_muted, bg="#0a0f21")
        self.lbl_stat_sub.pack(anchor="w", padx=12, pady=(0, 10))

        # Restore Section
        tk.Label(right_card, text="Restore QTH Wallet from 48 Words", font=("Segoe UI", 11, "bold"),
                 fg="#fff", bg=self.c_card).pack(anchor="w", padx=16, pady=(10, 4))

        self.txt_restore = tk.Text(right_card, height=4, font=("Consolas", 8), bg="#090d18", fg="#fff",
                                   wrap="word", padx=6, pady=6)
        self.txt_restore.insert("1.0", "Paste all 48 words separated by spaces...")
        self.txt_restore.pack(fill="x", padx=16, pady=(2, 8))

        btn_restore = tk.Button(right_card, text="Verify & Restore QTH Wallet", font=("Segoe UI", 9, "bold"),
                                bg=self.c_blue, fg="#fff", cursor="hand2", command=self._action_restore_wallet)
        btn_restore.pack(fill="x", padx=16, pady=(0, 10))

    def _action_generate_and_reveal(self):
        p1 = self.entry_pass.get()
        p2 = self.entry_confirm.get()
        if len(p1) < 8:
            messagebox.showerror("Password Error", "Password must be at least 8 characters long.")
            return
        if p1 != p2:
            messagebox.showerror("Password Error", "Passwords do not match. Please verify.")
            return

        self.wallet_password = p1

        # ALWAYS GENERATE A FRESH, BRAND-NEW POST-QUANTUM KEYPAIR WITH NEW 512-BIT RANDOM ENTROPY
        self.generated_keypair = QuantumKeyPair()
        self.active_wallet = QuantumWallet(self.generated_keypair)

        # Save to default keystore file
        wallet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_qth_wallet.json")
        self.active_wallet.save_to_file(wallet_path)

        # Update the dedicated New Address display in Creation card
        self.entry_new_addr.configure(state="normal")
        self.entry_new_addr.delete(0, "end")
        self.entry_new_addr.insert(0, self.active_wallet.address)
        self.entry_new_addr.configure(state="readonly")
        self.lbl_new_badge.configure(text="● NEW ADDRESS GENERATED", fg=self.c_emerald, bg="#0a2a1d")

        # Format 48 words nicely in text widget
        words = self.generated_keypair.mnemonic.split()
        lines = []
        for i in range(0, len(words), 4):
            chunk = [f"#{j+1:2d}: {words[j]:<12}" for j in range(i, min(i+4, len(words)))]
            lines.append("  ".join(chunk))
        formatted_words = "\n".join(lines)

        self.txt_seed.configure(state="normal")
        self.txt_seed.delete("1.0", "end")
        self.txt_seed.insert("1.0", formatted_words)
        self.txt_seed.configure(state="disabled")

        # Update all active UI components (Tab 1 active address & Tab 2 validator address)
        self._update_wallet_ui()

        messagebox.showinfo("New QTH Wallet Generated",
                            f"Brand-New QTH Wallet Generated Successfully!\n\n"
                            f"New Address: {self.active_wallet.address}\n\n"
                            f"512-bit post-quantum entropy produced this unique address.\n"
                            f"Please copy and safely backup all 48 seed words.")

    def _action_copy_new_address(self):
        if self.active_wallet and self.active_wallet.address:
            self.clipboard_clear()
            self.clipboard_append(self.active_wallet.address)
            messagebox.showinfo("Address Copied", f"New QTH Wallet Address copied to clipboard:\n{self.active_wallet.address}")
        else:
            messagebox.showwarning("Copy Address", "No new wallet generated yet.")

    def _action_reset_creation_card(self):
        self.entry_pass.delete(0, "end")
        self.entry_confirm.delete(0, "end")
        self.entry_new_addr.configure(state="normal")
        self.entry_new_addr.delete(0, "end")
        self.entry_new_addr.insert(0, "Click [Set Password & Reveal] to generate a new address")
        self.entry_new_addr.configure(state="readonly")
        self.lbl_new_badge.configure(text="READY TO GENERATE", fg=self.c_muted, bg="#151d38")
        self.txt_seed.configure(state="normal")
        self.txt_seed.delete("1.0", "end")
        self.txt_seed.insert("1.0", "--- Click [Set Password & Reveal] above to unveil your 48-word phrase ---")
        self.txt_seed.configure(state="disabled")

    def _action_copy_words(self):
        if not self.generated_keypair or not self.generated_keypair.mnemonic:
            messagebox.showwarning("Copy", "Please generate a QTH Wallet first.")
            return
        self.clipboard_clear()
        self.clipboard_append(self.generated_keypair.mnemonic)
        messagebox.showinfo("Copied", "All 48 seed words copied to clipboard!")

    def _action_download_backup(self):
        if not self.active_wallet or not self.active_wallet.mnemonic:
            messagebox.showwarning("Backup", "No active 48-word wallet to backup.")
            return

        fpath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt")],
            initialfile=f"quanthreum-48words-{self.active_wallet.address[:10]}.txt"
        )
        if fpath:
            content = f"""=============================================================
QUANTHREUM (QTH) 48-WORD MASTER PAPER BACKUP
=============================================================
Network: Quanthreum (QTH)
Generated At: {time.ctime()}
Security: Winternitz W-OTS+ (512-bit Quantum Entropy)
Quanthreum Address: {self.active_wallet.address}
Post-Quantum Public Key: {self.active_wallet.public_key_hex}

48-WORD RECOVERY SEED PHRASE:
{self.active_wallet.mnemonic}

WARNING: Anyone with these 48 words controls all QTH funds.
Store this paper backup in a secure offline location.
============================================================="""
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Paper backup saved to:\n{fpath}")

    def _action_restore_wallet(self):
        phrase = self.txt_restore.get("1.0", "end").strip()
        words = phrase.split()
        if len(words) != 48:
            messagebox.showerror("Invalid Phrase", f"Quanthreum requires exactly 48 words (got {len(words)}).")
            return

        valid, msg = validate_mnemonic(phrase)
        if not valid:
            messagebox.showerror("Checksum Error", msg)
            return

        wallet_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_qth_wallet.json")
        self.active_wallet = QuantumWallet.restore_from_mnemonic(phrase, wallet_path)
        self.generated_keypair = self.active_wallet.keypair
        self._update_wallet_ui()

        # Disable "Create QTH Wallet" tab and switch immediately to "Validator Node Manager" tab
        self.notebook.tab(self.tab_wallet, state="disabled")
        self.notebook.select(self.tab_validator)

        messagebox.showinfo(
            "QTH Wallet Restored",
            f"QTH Wallet successfully restored!\n\n"
            f"Address: {self.active_wallet.address}\n\n"
            f"Switched to Validator Node Manager tab.\n"
            f"The Create Wallet tab is now locked."
        )

    def _action_lock_and_go_validator(self):
        if not self.active_wallet:
            messagebox.showwarning("Wallet Required", "Please generate or restore a QTH Wallet first.")
            return
        self.notebook.tab(self.tab_wallet, state="disabled")
        self.notebook.select(self.tab_validator)

    def _action_copy_val_address(self):
        if self.active_wallet and self.active_wallet.address:
            self.clipboard_clear()
            self.clipboard_append(self.active_wallet.address)
            messagebox.showinfo("Address Copied", f"Copied QTH Wallet Address to clipboard:\n{self.active_wallet.address}")
        else:
            messagebox.showwarning("Copy Address", "No active QTH wallet loaded.")

    def _action_unlock_wallet_tab(self):
        self.notebook.tab(self.tab_wallet, state="normal")
        self.notebook.select(self.tab_wallet)

    def _update_wallet_ui(self):
        if not self.active_wallet:
            return
        # Tab 1 active address
        self.lbl_active_addr.configure(state="normal")
        self.lbl_active_addr.delete(0, "end")
        self.lbl_active_addr.insert(0, self.active_wallet.address)
        self.lbl_active_addr.configure(state="readonly")

        # Tab 2 validator address
        if hasattr(self, "entry_val_addr"):
            self.entry_val_addr.configure(state="normal")
            self.entry_val_addr.delete(0, "end")
            self.entry_val_addr.insert(0, self.active_wallet.address)
            self.entry_val_addr.configure(state="readonly")

        self._refresh_account_balance()

    def _check_auto_load(self):
        if self.active_wallet:
            self._update_wallet_ui()

    # =======================================================
    # TAB 2: VALIDATOR NODE MANAGER
    # =======================================================
    def _build_validator_tab(self):
        # Top Validator QTH Wallet Card
        val_wallet_card = tk.Frame(self.tab_validator, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        val_wallet_card.pack(fill="x", padx=10, pady=(10, 6))

        vw_top = tk.Frame(val_wallet_card, bg=self.c_card)
        vw_top.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(vw_top, text="Validator QTH Wallet Address:", font=("Segoe UI", 10, "bold"),
                 fg=self.c_cyan, bg=self.c_card).pack(side="left")

        self.lbl_val_status_badge = tk.Label(vw_top, text="● VALIDATOR INACTIVE", font=("Segoe UI", 9, "bold"),
                                             fg=self.c_rose, bg="#231320", padx=10, pady=3)
        self.lbl_val_status_badge.pack(side="right")

        self.lbl_val_balance = tk.Label(vw_top, text="Spendable: 0.0000 QTH", font=("Segoe UI", 9, "bold"),
                                        fg=self.c_emerald, bg="#0d1b2a", padx=10, pady=3)
        self.lbl_val_balance.pack(side="right", padx=(0, 10))

        # Address Input & Action Row
        vw_addr_row = tk.Frame(val_wallet_card, bg=self.c_card)
        vw_addr_row.pack(fill="x", padx=16, pady=(0, 12))

        self.entry_val_addr = tk.Entry(vw_addr_row, font=("Consolas", 10, "bold"), bg="#090d18", fg=self.c_cyan, relief="flat")
        initial_addr = self.active_wallet.address if self.active_wallet else "No QTH Wallet Loaded - Restore or Create Wallet First"
        self.entry_val_addr.insert(0, initial_addr)
        self.entry_val_addr.configure(state="readonly")
        self.entry_val_addr.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_copy_val = tk.Button(vw_addr_row, text="📋 Copy Address", font=("Segoe UI", 9),
                                 bg="#1f2a48", fg="#fff", cursor="hand2", command=self._action_copy_val_address)
        btn_copy_val.pack(side="left", padx=(0, 6))

        self.btn_unlock_wallet = tk.Button(vw_addr_row, text="🔓 Switch / Unlock Wallet", font=("Segoe UI", 9),
                                          bg="#1b243b", fg=self.c_muted, cursor="hand2", command=self._action_unlock_wallet_tab)
        self.btn_unlock_wallet.pack(side="left")

        # Top Controls Bar
        ctrl_card = tk.Frame(self.tab_validator, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        ctrl_card.pack(fill="x", padx=10, pady=(0, 6))

        row1 = tk.Frame(ctrl_card, bg=self.c_card)
        row1.pack(fill="x", padx=16, pady=12)

        self.btn_start_node = tk.Button(row1, text="▶ Start Validator Node", font=("Segoe UI", 10, "bold"),
                                       bg=self.c_emerald, fg="#000", cursor="hand2", command=self._action_start_validator_node)
        self.btn_start_node.pack(side="left", padx=(0, 10))

        self.btn_stop_node = tk.Button(row1, text="⏹ Stop Node", font=("Segoe UI", 10, "bold"),
                                      bg="#1f2a48", fg="#fff", state="disabled", cursor="hand2", command=self._action_stop_validator_node)
        self.btn_stop_node.pack(side="left", padx=(0, 15))

        tk.Label(row1, text="Block Interval (s):", font=("Segoe UI", 9), fg=self.c_muted, bg=self.c_card).pack(side="left")
        self.entry_interval = tk.Entry(row1, width=4, font=("Segoe UI", 9), bg="#090d18", fg="#fff")
        self.entry_interval.insert(0, "6")
        self.entry_interval.pack(side="left", padx=(4, 20))

        # Staking Input
        tk.Label(row1, text="Stake Deposit (QTH):", font=("Segoe UI", 9), fg=self.c_muted, bg=self.c_card).pack(side="left")
        self.entry_stake_amt = tk.Entry(row1, width=6, font=("Segoe UI", 9), bg="#090d18", fg="#fff")
        self.entry_stake_amt.insert(0, "32.0")
        self.entry_stake_amt.pack(side="left", padx=(4, 8))

        btn_stake = tk.Button(row1, text="Stake in Q-PoS", font=("Segoe UI", 9, "bold"),
                              bg=self.c_violet, fg="#fff", cursor="hand2", command=self._action_deposit_stake)
        btn_stake.pack(side="left")

        # Validator Real-time Console Log
        log_frame = tk.Frame(self.tab_validator, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        log_frame.pack(fill="both", expand=True, padx=10, pady=6)

        log_head = tk.Frame(log_frame, bg="#0d1326", height=32)
        log_head.pack(fill="x")

        tk.Label(log_head, text="Real-Time Validator Node Engine Log", font=("Segoe UI", 9, "bold"),
                 fg=self.c_cyan, bg="#0d1326").pack(side="left", padx=12, pady=6)

        btn_clear = tk.Button(log_head, text="Clear", font=("Segoe UI", 8), bg="#1f2a48", fg="#fff",
                              command=lambda: self.log_box.delete("1.0", "end"))
        btn_clear.pack(side="right", padx=12, pady=4)

        self.log_box = tk.Text(log_frame, bg="#04060d", fg="#a7f3d0", font=("Consolas", 9),
                               padx=10, pady=10, wrap="word", relief="flat")
        self.log_box.pack(fill="both", expand=True)

        self._append_log("Ready. Click [▶ Start Validator Node] to launch the local Quanthreum network.")

    def _append_log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def _action_start_validator_node(self):
        if not self.active_wallet:
            messagebox.showwarning("Wallet Required", "Please create or load a QTH Wallet first in the 'Create QTH Wallet' tab.")
            return

        # Start Node in background if not already started
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quanthreum_data")
        if not self.node_instance:
            self.node_instance = QuanthreumNode(host="127.0.0.1", port=self.node_port, data_dir=data_dir)
            self.node_thread = threading.Thread(target=self.node_instance.start, daemon=True)
            self.node_thread.start()
            self._append_log(f"Quanthreum Core Node listening at http://127.0.0.1:{self.node_port}")
            time.sleep(1)

        # Start Validator Worker Runner
        interval = int(self.entry_interval.get()) if self.entry_interval.get().isdigit() else 6
        self.validator_runner = ValidatorRunner(
            node_url=f"http://127.0.0.1:{self.node_port}",
            validator_address=self.active_wallet.address,
            validator_seed=self.active_wallet.seed_hex,
            block_interval=interval,
            log_callback=lambda m: self.after(0, self._append_log, m)
        )
        self.validator_thread = threading.Thread(target=self.validator_runner.start, daemon=True)
        self.validator_thread.start()

        self.btn_start_node.configure(state="disabled")
        self.btn_stop_node.configure(state="normal")
        self.status_lbl.configure(text="● Validator ACTIVE", fg=self.c_emerald)
        self._refresh_account_balance()

    def _action_stop_validator_node(self):
        if self.validator_runner:
            self.validator_runner.stop()
        self.btn_start_node.configure(state="normal")
        self.btn_stop_node.configure(state="disabled")
        self.status_lbl.configure(text="● Node Stopped", fg=self.c_rose)
        self._append_log("Validator Node stopped.")

    def _action_deposit_stake(self):
        if not self.active_wallet:
            messagebox.showwarning("Wallet Required", "Please create or load a QTH Wallet first.")
            return

        amt = float(self.entry_stake_amt.get()) if self.entry_stake_amt.get() else 10.0
        if amt < 10.0:
            messagebox.showerror("Minimum Stake", "Minimum validator stake is 10.0 QTH.")
            return

        if self.validator_runner:
            self.validator_runner.check_and_ensure_stake(amt)
        else:
            messagebox.showinfo("Staking", "Start the validator node to deposit stake and seal blocks.")

    # =======================================================
    # TAB 3: BLOCKCHAIN EXPLORER & TRANSFERS
    # =======================================================
    def _build_network_tab(self):
        net_frame = tk.Frame(self.tab_network, bg=self.c_bg)
        net_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Quick Transfer Box
        tx_box = tk.Frame(net_frame, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        tx_box.pack(fill="x", pady=(0, 10))

        tk.Label(tx_box, text="Send QTH Transfer", font=("Segoe UI", 12, "bold"), fg=self.c_cyan, bg=self.c_card).pack(anchor="w", padx=16, pady=(12, 8))

        row = tk.Frame(tx_box, bg=self.c_card)
        row.pack(fill="x", padx=16, pady=(0, 12))

        tk.Label(row, text="Recipient (0xQTH_...):", font=("Segoe UI", 9), fg=self.c_muted, bg=self.c_card).pack(side="left")
        self.entry_send_to = tk.Entry(row, font=("Consolas", 9), bg="#090d18", fg="#fff", width=42)
        self.entry_send_to.pack(side="left", padx=(6, 16))

        tk.Label(row, text="Amount (QTH):", font=("Segoe UI", 9), fg=self.c_muted, bg=self.c_card).pack(side="left")
        self.entry_send_amt = tk.Entry(row, font=("Segoe UI", 9), bg="#090d18", fg="#fff", width=8)
        self.entry_send_amt.insert(0, "5.0")
        self.entry_send_amt.pack(side="left", padx=(6, 16))

        btn_send = tk.Button(row, text="Sign & Send QTH", font=("Segoe UI", 9, "bold"),
                             bg=self.c_blue, fg="#fff", cursor="hand2", command=self._action_send_transfer)
        btn_send.pack(side="left")

        # Network Status Card
        info_card = tk.Frame(net_frame, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        info_card.pack(fill="both", expand=True)

        tk.Label(info_card, text="Quanthreum Blockchain Network State", font=("Segoe UI", 12, "bold"),
                 fg="#fff", bg=self.c_card).pack(anchor="w", padx=16, pady=(16, 10))

        self.txt_net_info = tk.Text(info_card, height=10, font=("Consolas", 9), bg="#050811", fg="#fff",
                                    relief="flat", padx=10, pady=10)
        self.txt_net_info.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        btn_open_web = tk.Button(info_card, text="🌐 Open Full Web3 Explorer & Dashboard in Browser",
                                 font=("Segoe UI", 10, "bold"), bg=self.c_violet, fg="#fff",
                                 cursor="hand2", command=self._action_open_web_explorer)
        btn_open_web.pack(fill="x", padx=16, pady=(0, 16))

    def _action_send_transfer(self):
        if not self.active_wallet:
            messagebox.showwarning("Wallet Required", "Please create or load a QTH Wallet first.")
            return

        to_addr = self.entry_send_to.get().strip()
        amt = float(self.entry_send_amt.get()) if self.entry_send_amt.get() else 0.0

        if not to_addr.startswith("0xQTH_"):
            messagebox.showerror("Address Error", "Recipient must start with 0xQTH_")
            return
        if amt <= 0:
            messagebox.showerror("Amount Error", "Enter a positive amount of QTH.")
            return

        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{self.node_port}/api/wallet/send",
                data=json.dumps({"seed": self.active_wallet.seed_hex, "recipient": to_addr, "amount": amt}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            res = json.loads(urllib.request.urlopen(req, timeout=5).read().decode("utf-8"))
            if res.get("status") == "success":
                messagebox.showinfo("Transfer Sent", f"Successfully broadcast transfer!\nTX: {res.get('tx_hash')}")
                self._refresh_account_balance()
            else:
                messagebox.showerror("Transfer Rejected", res.get("error", "Unknown error"))
        except Exception as e:
            messagebox.showerror("Network Error", f"Cannot send transaction: {e}\n(Is validator node running?)")

    def _action_open_web_explorer(self):
        url = f"http://127.0.0.1:{self.node_port}"
        webbrowser.open(url)

    def _refresh_account_balance(self):
        if not self.active_wallet:
            return
        try:
            url = f"http://127.0.0.1:{self.node_port}/api/account?address={self.active_wallet.address}"
            req = urllib.request.urlopen(url, timeout=2)
            data = json.loads(req.read().decode("utf-8"))
            bal = data.get("balance", 0.0)
            nonce = data.get("nonce", 0)
            is_val = "ACTIVE" if data.get("is_validator") else "INACTIVE"
            stake = data.get("staked_amount", 0.0)

            self.lbl_bal_val.configure(text=f"{bal:.4f} QTH")
            self.lbl_stat_sub.configure(text=f"Spendable: {bal:.4f} QTH • Nonce: {nonce} • Validator: {is_val} ({stake} QTH staked)")

            # Update Validator tab widgets
            if hasattr(self, "lbl_val_balance"):
                self.lbl_val_balance.configure(text=f"Spendable: {bal:.4f} QTH")
            if hasattr(self, "lbl_val_status_badge"):
                if is_val == "ACTIVE":
                    self.lbl_val_status_badge.configure(text=f"● VALIDATOR ACTIVE ({stake} QTH)", fg=self.c_emerald, bg="#0a2a1d")
                else:
                    self.lbl_val_status_badge.configure(text="● VALIDATOR INACTIVE", fg=self.c_rose, bg="#2a1219")

            # Also update network info box
            info_url = f"http://127.0.0.1:{self.node_port}/api/info"
            info_data = json.loads(urllib.request.urlopen(info_url, timeout=2).read().decode("utf-8"))
            net_text = f"""Network:              {info_data.get('network')} ({info_data.get('ticker')})
Block Height:         #{info_data.get('height')}
Total Max Supply:     {info_data.get('total_max_supply'):,.0f} QTH (Strict Hard Cap)
Circulating Supply:   {info_data.get('circulating_supply'):,.4f} QTH
EIP-1559 Burned:      {info_data.get('burned_fees'):,.8f} QTH (Deflationary)
Base Fee:             {info_data.get('base_fee'):.8f} QTH
Active Validators:    {info_data.get('total_validators')} ({info_data.get('total_staked')} QTH total staked)
Mempool Pending:      {info_data.get('mempool_size')} transactions"""

            self.txt_net_info.delete("1.0", "end")
            self.txt_net_info.insert("1.0", net_text)

        except Exception:
            pass


def main():
    app = QuanthreumWindowsStudio()
    app.mainloop()


if __name__ == "__main__":
    main()
