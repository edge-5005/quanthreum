# Quanthreum (QTH)

**Quanthreum** is a decentralized cryptocurrency blockchain featuring a hybrid of **Post-Quantum Cryptographic Security** and **Ethereum's Account-Based Virtual Machine**.

- **Blockchain Name:** Quanthreum
- **Ticker Symbol:** **QTH**
- **Address Format:** `0xQTH_<checksummed_hex>` (EIP-55 compliant)
- **Mnemonic Security:** **48-Word Post-Quantum Seed Phrase** (512-bit entropy + 16-bit checksum)
- **Total Max Supply:** **100,000,000 QTH** (Strict 100 Million hard cap)
- **Consensus:** Quantum Proof-of-Stake (Q-PoS) with EIP-1559 Base Fee Burn

---

## Windows Tools (Native Desktop GUI & Batch Launchers)

Quanthreum comes with dedicated Windows tools to create QTH Wallets and run validator nodes:

### 1. Quanthreum Windows Desktop Studio (GUI)
A full-featured native Windows desktop application built with Tkinter (`quanthreum_validator_app.pyw`):
- **Double-click:** [`Launch-Quanthreum-Studio.bat`](Launch-Quanthreum-Studio.bat)
- **Features:**
  - **Create QTH Wallet Tab:** Password setup and verification, hidden seed shield with interactive reveal button for 48 words, 1-click clipboard copy, and `.txt` paper backup.
  - **Validator Node Manager Tab:** 1-click node start/stop, configurable block forging interval (default: 6 seconds), Q-PoS staking input, and streaming live console output.
  - **Blockchain & Transfers Tab:** Send quantum transfers, monitor live network metrics (height, 100M supply cap, burned fees), and open the web explorer.

### 2. Interactive Windows Command Menu
- **Double-click:** [`Quanthreum-Node-Manager.bat`](Quanthreum-Node-Manager.bat)
- Interactive Windows menu with numeric options to launch the GUI, create/restore wallets, run validator nodes, stake QTH, and open the web dashboard.

### 3. Continuous Validator Node CLI
```powershell
python quanthreum_cli.py validator --wallet my_qth_wallet.json --interval 6 --stake 32.0
```

---

## 48-Word Post-Quantum Mnemonic Seed

While legacy cryptocurrencies (Bitcoin, Ethereum) rely on 12 or 24 words (128 or 256 bits of entropy) vulnerable to quantum Shor's algorithm, Quanthreum uses a **48-word mnemonic phrase**:

- **Entropy:** 512 bits of cryptographically secure quantum randomness.
- **Checksum:** 16-bit SHA-256 validation bits ($512 + 16 = 528$ bits).
- **Word Encoding:** 48 words $\times$ 11 bits per BIP-39 word.
- **Immunity:** Immune to Grover's quantum search ($2^{256}$ quantum operations required) and completely immune to Shor's discrete-log factorization.

---

## Quick Start (100% Free)

### 1. Launch the Web Portal with the "Create QTH Wallet" Wizard
```powershell
python quanthreum_cli.py web
```
This opens **`http://127.0.0.1:8545`** in your browser.

#### Features of the Web Portal:
1. **Interactive Create QTH Wallet Flow:**
   - **Step 1 (Password First):** Prompts the user to create and confirm a password (min 8 characters).
   - **Step 2 (Reveal Shield):** Hides the phrase behind a locked shield until the user clicks **"👁️ Click to Reveal 48-Word Seed Phrase"**.
   - **Step 3 (Backup & Activation):** Displays the 48 words in an interactive grid with privacy toggle, one-click copy, and paper backup download (`.txt`). Activating loads the QTH Wallet directly.
2. **Restore QTH Wallet Portal:**
   - Input your 48 words and create a password to restore your QTH Wallet on any device.
3. **Active QTH Wallet Dashboard:**
   - Real-time spendable balance, account nonce, and quantum transfer broadcast form.
4. **Live Blockchain Explorer & Account Inspector:**
   - Real-time block inspection and storage state viewer.
5. **QVM Smart Contract Deployer:**
   - 1-click deployment of QRC-20 tokens, vaults, and registries.
6. **Q-PoS Validator Portal:**
   - Stake QTH and propose/seal blocks.

---

### 2. Command Line Operations

#### Create a 48-Word QTH Wallet
```powershell
python quanthreum_cli.py wallet create --file my_qth_wallet.json
```

#### Restore QTH Wallet from 48-Word Seed Phrase
```powershell
python quanthreum_cli.py wallet restore --phrase "word1 word2 ... word48" --file restored_qth_wallet.json
```

#### Start the Full Blockchain Node
```powershell
python quanthreum_cli.py node start --port 8545
```

#### Run the 1-Click Automated Self-Test Demo
```powershell
python quanthreum_cli.py demo
```

#### Send QTH Transfer
```powershell
python quanthreum_cli.py send --wallet my_qth_wallet.json --to 0xQTH_... --amount 50.0
```

#### Stake in Quantum Proof-of-Stake (Min 10 QTH)
```powershell
python quanthreum_cli.py stake --wallet my_qth_wallet.json --amount 32.0
```

#### Propose & Seal a Block (Earn Yield + Gas Tips)
```powershell
python quanthreum_cli.py mine
```

---

## 🌐 Website & Node Hosting Guide

The Quanthreum full node is self-contained: it serves both the **interactive Web Portal & Explorer** and all **REST API / RPC endpoints** from port `8545`. You have four flexible hosting options:

### Method 1: Production Cloud VPS (Ubuntu 22.04 / 24.04 LTS)
Deploy to DigitalOcean, AWS EC2, Linode, or Hetzner with Nginx and free Let's Encrypt SSL:

1. Clone or upload the repository to your server:
   ```bash
   git clone <repo_url> /var/www/quanthreum
   cd /var/www/quanthreum
   ```
2. Run the automated 1-click deployment script:
   ```bash
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```
3. Secure with free HTTPS via Certbot:
   ```bash
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   ```
The node will run 24/7 managed by `systemd` (`quanthreum.service`) and reverse-proxied through Nginx on port 80/443.

---

### Method 2: Docker / Docker Compose
Deploy in seconds on any system with Docker installed:
```bash
docker compose up -d
```
The node and web UI will be live at `http://<server-ip>:8545`.

---

### Method 3: 100% Free Public Hosting from Windows (Cloudflare Tunnel)
Host directly from your Windows PC with a public HTTPS URL without purchasing a server or opening router ports:

1. Start your local Quanthreum node in Windows:
   ```powershell
   python quanthreum_cli.py node start --port 8545
   ```
2. Install Cloudflare Tunnel (via PowerShell):
   ```powershell
   winget install Cloudflare.cloudflared
   ```
3. Start the tunnel:
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8545
   ```
Cloudflare will give you an instant public HTTPS URL (e.g. `https://random-name.trycloudflare.com`) accessible worldwide with free DDoS protection.

---

### Method 4: Static Hosting (GitHub Pages, Vercel, Netlify)
If you wish to host only the frontend static UI on a global CDN:
- The `web/` folder contains pure HTML, CSS, and vanilla JS (`index.html`, `styles.css`, `app.js`).
- Upload the `web/` directory to GitHub Pages, Cloudflare Pages, or Vercel.
- Configure `API_BASE` in `web/app.js` to point to your public RPC node address.
