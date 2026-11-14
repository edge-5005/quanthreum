/**
 * Quanthreum (QTH) - Web3 Portal & Explorer
 * Connects directly to the native Quanthreum Node REST API (Port 8545).
 */

const API_BASE = window.location.origin;

// State
let currentHeight = -1;
let isNodeOnline = false;
let current48Mnemonic = "";
let currentGeneratedWallet = null;
let walletPassword = "";

// DOM Elements - Metrics
const nodeStatusBadge = document.getElementById("nodeStatusBadge");
const nodeStatusText = document.getElementById("nodeStatusText");
const statHeight = document.getElementById("statHeight");
const statBlocksCount = document.getElementById("statBlocksCount");
const statCirculating = document.getElementById("statCirculating");
const statBurned = document.getElementById("statBurned");
const statBaseFee = document.getElementById("statBaseFee");
const blocksTableBody = document.getElementById("blocksTableBody");

// Create QTH Wallet Wizard Elements
const tabCreateNew = document.getElementById("tabCreateNew");
const tabRestore = document.getElementById("tabRestore");
const flowCreateNew = document.getElementById("flowCreateNew");
const flowRestore = document.getElementById("flowRestore");

// Step 1: Password Creation
const stepPasswordCreation = document.getElementById("stepPasswordCreation");
const inputNewPassword = document.getElementById("inputNewPassword");
const inputConfirmPassword = document.getElementById("inputConfirmPassword");
const btnToggleNewPass = document.getElementById("btnToggleNewPass");
const btnToggleConfirmPass = document.getElementById("btnToggleConfirmPass");
const passwordErrorMsg = document.getElementById("passwordErrorMsg");
const btnSetPasswordProceed = document.getElementById("btnSetPasswordProceed");

// Step 2: Reveal Seed Phrase
const stepRevealPhrase = document.getElementById("stepRevealPhrase");
const revealShieldBox = document.getElementById("revealShieldBox");
const btnRevealWordsAction = document.getElementById("btnRevealWordsAction");
const revealedContentBox = document.getElementById("revealedContentBox");
const mnemonicGrid = document.getElementById("mnemonicGrid");
const btnToggleBlur = document.getElementById("btnToggleBlur");
const btnCopy48Words = document.getElementById("btnCopy48Words");
const btnDownloadBackup = document.getElementById("btnDownloadBackup");
const chkSavedWords = document.getElementById("chkSavedWords");
const btnActivateWallet = document.getElementById("btnActivateWallet");
const createdWalletSummary = document.getElementById("createdWalletSummary");
const newWalletAddr = document.getElementById("newWalletAddr");
const newWalletPub = document.getElementById("newWalletPub");

// Restore QTH Wallet Elements
const restoreInput = document.getElementById("restoreInput");
const restoreWordCounter = document.getElementById("restoreWordCounter");
const restoreValidationStatus = document.getElementById("restoreValidationStatus");
const restorePassword = document.getElementById("restorePassword");
const restoreConfirmPassword = document.getElementById("restoreConfirmPassword");
const btnRestoreSubmit = document.getElementById("btnRestoreSubmit");

// Account Lookup Elements
const lookupAddressInput = document.getElementById("lookupAddressInput");
const btnLookupAddress = document.getElementById("btnLookupAddress");
const accountLookupResult = document.getElementById("accountLookupResult");
const lookupResAddr = document.getElementById("lookupResAddr");
const lookupResBal = document.getElementById("lookupResBal");
const lookupResNonce = document.getElementById("lookupResNonce");
const lookupResType = document.getElementById("lookupResType");
const lookupResStake = document.getElementById("lookupResStake");
const lookupResStorageBox = document.getElementById("lookupResStorageBox");
const lookupResStorage = document.getElementById("lookupResStorage");

// Active QTH Wallet Dashboard Elements
const walletAddressInput = document.getElementById("walletAddressInput");
const walletSeedInput = document.getElementById("walletSeedInput");
const walletBalance = document.getElementById("walletBalance");
const walletNonce = document.getElementById("walletNonce");
const btnCopyAddress = document.getElementById("btnCopyAddress");
const btnToggleSeed = document.getElementById("btnToggleSeed");
const btnRefreshBalance = document.getElementById("btnRefreshBalance");

// Send Elements
const sendRecipientInput = document.getElementById("sendRecipientInput");
const sendAmountInput = document.getElementById("sendAmountInput");
const btnSubmitSend = document.getElementById("btnSubmitSend");

// Contract Elements
const contractTemplateSelect = document.getElementById("contractTemplateSelect");
const contractCodeInput = document.getElementById("contractCodeInput");
const btnDeployContract = document.getElementById("btnDeployContract");
const callContractAddrInput = document.getElementById("callContractAddrInput");
const callActionInput = document.getElementById("callActionInput");
const callParamsInput = document.getElementById("callParamsInput");
const btnCallContract = document.getElementById("btnCallContract");

// Staking & Dual-Key Onboarding Elements
const onboardValidatorAddrInput = document.getElementById("onboardValidatorAddrInput");
const onboardDepositorAddrInput = document.getElementById("onboardDepositorAddrInput");
const onboardPaymentRefInput = document.getElementById("onboardPaymentRefInput");
const onboardAutoStakeInput = document.getElementById("onboardAutoStakeInput");
const btnOnboardValidator = document.getElementById("btnOnboardValidator");
const btnDownloadValidatorBackup = document.getElementById("btnDownloadValidatorBackup");
const onboardResultBox = document.getElementById("onboardResultBox");
const onboardResValAddr = document.getElementById("onboardResValAddr");
const onboardResDepAddr = document.getElementById("onboardResDepAddr");
const onboardResStake = document.getElementById("onboardResStake");

const stakeAmountInput = document.getElementById("stakeAmountInput");
const btnSubmitStake = document.getElementById("btnSubmitStake");
const sealValidatorAddrInput = document.getElementById("sealValidatorAddrInput");
const btnSealBlock = document.getElementById("btnSealBlock");

// Contract Templates
const TEMPLATES = {
  qrc20: JSON.stringify({
    "standard": "QRC-20",
    "name": "QuantumUSD",
    "symbol": "QUSD",
    "init_storage": {
      "name": "Quantum USD Token",
      "symbol": "QUSD",
      "decimals": 18,
      "balances": {}
    }
  }, null, 2),
  vault: JSON.stringify({
    "standard": "QuantumVault",
    "init_storage": {
      "vault_name": "Quanthreum Yield Vault",
      "stakes": {}
    }
  }, null, 2),
  storage: JSON.stringify({
    "standard": "KeyValueRegistry",
    "init_storage": {
      "version": "1.0.0",
      "records": {}
    }
  }, null, 2)
};

// ==========================================
// Toast Notifications
// ==========================================
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// ==========================================
// Node Polling & Metrics
// ==========================================
async function fetchNodeInfo() {
  try {
    const res = await fetch(`${API_BASE}/api/info`);
    if (!res.ok) throw new Error("Node error");
    const data = await res.json();

    isNodeOnline = true;
    if (nodeStatusBadge) {
      const dot = nodeStatusBadge.querySelector(".status-dot");
      if (dot) dot.style.background = "#10b981";
    }
    if (nodeStatusText) {
      nodeStatusText.innerHTML = `<span class="node-status-full">Quanthreum Online (Block #${data.height})</span><span class="node-status-mobile">Block #${data.height}</span>`;
    }

    if (statHeight) statHeight.innerText = `#${data.height}`;
    if (statBlocksCount) statBlocksCount.innerText = `${data.total_blocks} block${data.total_blocks === 1 ? '' : 's'} synced`;
    if (statCirculating) {
      const circFormatted = Number(data.circulating_supply).toLocaleString('en-US', {maximumFractionDigits: 2});
      statCirculating.innerHTML = `<span class="stat-num">${circFormatted}</span> <span class="unit">QTH</span>`;
    }
    if (statBurned) {
      const burnedFormatted = Number(data.burned_fees).toFixed(6);
      statBurned.innerHTML = `<span class="stat-num font-mono accent-rose">${burnedFormatted}</span> <span class="unit">QTH</span>`;
    }
    if (statBaseFee) {
      const baseFeeFormatted = Number(data.base_fee).toFixed(8);
      statBaseFee.innerHTML = `<span class="stat-num font-mono">${baseFeeFormatted}</span> <span class="unit">QTH</span>`;
    }

    if (data.height !== currentHeight) {
      currentHeight = data.height;
      if (blocksTableBody) fetchRecentBlocks();
      if (walletAddressInput && walletAddressInput.value) {
        fetchAccountState(walletAddressInput.value);
      }
    }
  } catch (err) {
    isNodeOnline = false;
    if (nodeStatusBadge) {
      const dot = nodeStatusBadge.querySelector(".status-dot");
      if (dot) dot.style.background = "#f43f5e";
    }
    if (nodeStatusText) {
      nodeStatusText.innerHTML = `<span class="node-status-full">Node Disconnected</span><span class="node-status-mobile">Offline</span>`;
    }
  }
}

async function fetchRecentBlocks() {
  if (!blocksTableBody) return;
  try {
    const res = await fetch(`${API_BASE}/api/blocks?limit=10`);
    if (!res.ok) return;
    const data = await res.json();
    renderBlocksTable(data.blocks || []);
  } catch (err) {
    console.error("Failed to fetch blocks:", err);
  }
}

function renderBlocksTable(blocks) {
  if (!blocksTableBody) return;
  if (!blocks || blocks.length === 0) {
    blocksTableBody.innerHTML = `<tr><td colspan="7" class="loading-cell">No blocks mined yet.</td></tr>`;
    return;
  }

  blocksTableBody.innerHTML = blocks.map(b => {
    const h = b.header;
    const shortHash = b.hash ? `${b.hash.substring(0, 10)}...${b.hash.substring(b.hash.length - 6)}` : "-";
    const shortValidator = h.validator ? `${h.validator.substring(0, 8)}...${h.validator.substring(h.validator.length - 6)}` : "-";
    const shortStateRoot = h.state_root ? `${h.state_root.substring(0, 8)}...` : "-";

    return `
      <tr>
        <td class="font-mono font-bold">#${h.number}</td>
        <td class="font-mono" title="${b.hash}">${shortHash}</td>
        <td class="font-mono" title="${h.validator}">${shortValidator}</td>
        <td class="font-mono">${Number(h.gas_used).toLocaleString()}</td>
        <td class="font-mono">${Number(h.base_fee).toFixed(6)}</td>
        <td class="font-mono" title="${h.state_root}">${shortStateRoot}</td>
        <td>${b.transactions ? b.transactions.length : 0}</td>
      </tr>
    `;
  }).join("");
}

// ==========================================
// Create QTH Wallet Flow (Password First -> Reveal)
// ==========================================

function handlePasswordProceed() {
  const p1 = inputNewPassword.value;
  const p2 = inputConfirmPassword.value;

  passwordErrorMsg.style.display = "none";

  if (!p1 || p1.length < 8) {
    passwordErrorMsg.innerText = "Password must be at least 8 characters long.";
    passwordErrorMsg.style.display = "block";
    return;
  }

  if (p1 !== p2) {
    passwordErrorMsg.innerText = "Passwords do not match. Please verify.";
    passwordErrorMsg.style.display = "block";
    return;
  }

  walletPassword = p1;

  // Generate the 48-word wallet via API if not already fetched
  btnSetPasswordProceed.disabled = true;
  btnSetPasswordProceed.innerText = "Generating 512-Bit Keypair...";

  fetch(`${API_BASE}/api/wallet/create`, { method: "POST" })
    .then(r => r.json())
    .then(data => {
      currentGeneratedWallet = data;
      current48Mnemonic = data.mnemonic;

      // Switch to Step 2
      stepPasswordCreation.style.display = "none";
      stepRevealPhrase.style.display = "block";

      // Show the Reveal Shield (words are hidden until reveal button is pressed)
      revealShieldBox.style.display = "block";
      revealedContentBox.style.display = "none";

      showToast("Password set! Click the reveal button to view your 48-word phrase.", "info");
    })
    .catch(err => {
      passwordErrorMsg.innerText = "Generation error: " + err.message;
      passwordErrorMsg.style.display = "block";
    })
    .finally(() => {
      btnSetPasswordProceed.disabled = false;
      btnSetPasswordProceed.innerText = "Set Password & Proceed to Seed Phrase →";
    });
}

function handleRevealWords() {
  if (!current48Mnemonic || !currentGeneratedWallet) return;

  // Immediately display the newly generated QTH address
  const addrElem = document.getElementById("revealedWalletAddress");
  if (addrElem) {
    addrElem.innerText = currentGeneratedWallet.address;
  }

  renderMnemonicGrid(current48Mnemonic);
  revealShieldBox.style.display = "none";
  revealedContentBox.style.display = "block";

  showToast(`New Address Generated: ${currentGeneratedWallet.address.substring(0, 14)}...`, "success");
}

function resetCreateWalletWizard() {
  inputNewPassword.value = "";
  inputConfirmPassword.value = "";
  stepPasswordCreation.style.display = "block";
  stepRevealPhrase.style.display = "none";
  revealShieldBox.style.display = "block";
  revealedContentBox.style.display = "none";
  currentGeneratedWallet = null;
  current48Mnemonic = "";
  passwordErrorMsg.style.display = "none";
  if (chkSavedWords) chkSavedWords.checked = false;
  if (btnActivateWallet) btnActivateWallet.disabled = true;
  if (createdWalletSummary) createdWalletSummary.style.display = "none";
  showToast("Ready to generate a new QTH wallet.", "info");
}

function renderMnemonicGrid(mnemonic) {
  if (!mnemonic) return;
  const words = mnemonic.trim().split(/\s+/);
  mnemonicGrid.innerHTML = words.map((w, idx) => `
    <div class="word-pill">
      <span class="word-idx">#${idx + 1}</span>
      <span class="word-text">${w}</span>
    </div>
  `).join("");
}

function copyAll48Words() {
  if (!current48Mnemonic) return;
  navigator.clipboard.writeText(current48Mnemonic);
  showToast("All 48 seed words copied to clipboard!", "success");
}

function downloadPaperBackup() {
  if (!currentGeneratedWallet) return;
  const content = `=============================================================
QUANTHREUM (QTH) 48-WORD MASTER PAPER BACKUP
=============================================================
Network: Quanthreum (QTH)
Generated At: ${new Date().toISOString()}
Security Standard: Winternitz W-OTS+ (512-bit Quantum Entropy)
Quanthreum Address: ${currentGeneratedWallet.address}
Post-Quantum Public Key: ${currentGeneratedWallet.public_key}

-------------------------------------------------------------
48-WORD RECOVERY SEED PHRASE (STORE OFFLINE SECURELY):
-------------------------------------------------------------
${current48Mnemonic}

-------------------------------------------------------------
WARNING: Anyone with these 48 words controls all QTH funds.
Never share this phrase. It is immune to quantum attacks.
=============================================================`;

  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `quanthreum-48words-${currentGeneratedWallet.address.substring(0, 10)}.txt`;
  a.click();
  showToast("Paper backup downloaded!", "info");
}

function activateQTHWallet() {
  if (!currentGeneratedWallet) return;

  setWallet(currentGeneratedWallet.address, currentGeneratedWallet.seed, current48Mnemonic);
  newWalletAddr.innerText = currentGeneratedWallet.address;
  newWalletPub.innerText = currentGeneratedWallet.public_key;
  createdWalletSummary.style.display = "block";

  showToast("QTH Wallet Activated Successfully!", "success");
}

// Restore from 48 Words
async function restoreFrom48Words() {
  const phrase = restoreInput.value.trim();
  const p1 = restorePassword.value;
  const p2 = restoreConfirmPassword.value;
  const words = phrase.split(/\s+/);

  if (words.length !== 48) {
    return showToast(`Quanthreum requires exactly 48 words (currently entered: ${words.length})`, "error");
  }

  if (!p1 || p1.length < 8) {
    return showToast("Please set a wallet password with at least 8 characters", "error");
  }

  if (p1 !== p2) {
    return showToast("Passwords do not match", "error");
  }

  btnRestoreSubmit.disabled = true;
  btnRestoreSubmit.innerText = "Verifying 512-bit Checksum...";

  try {
    const res = await fetch(`${API_BASE}/api/wallet/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mnemonic: phrase })
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      walletPassword = p1;
      setWallet(data.address, data.seed, phrase);

      // Disable Create Wallet tab in wizard
      if (tabCreate) {
        tabCreate.disabled = true;
        tabCreate.classList.add("disabled");
        tabCreate.style.opacity = "0.5";
        tabCreate.style.cursor = "not-allowed";
        tabCreate.title = "QTH Wallet already active.";
      }

      // Populate and highlight Validator address
      if (sealValidatorAddrInput) {
        sealValidatorAddrInput.value = data.address;
      }

      showToast("QTH Wallet Successfully Restored! Redirecting to Validator...", "success");
      window.location.hash = "#validator";
    } else {
      showToast(data.error || "Restoration failed", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnRestoreSubmit.disabled = false;
    btnRestoreSubmit.innerText = "Verify & Restore QTH Wallet";
  }
}

// ==========================================
// Account Inspector
// ==========================================
async function inspectAccount(address) {
  if (!address) return;
  try {
    const res = await fetch(`${API_BASE}/api/account?address=${encodeURIComponent(address)}`);
    if (!res.ok) throw new Error("Account not found");
    const data = await res.json();

    accountLookupResult.style.display = "block";
    lookupResAddr.innerText = data.address;
    lookupResBal.innerText = data.balance.toFixed(4);
    lookupResNonce.innerText = data.nonce;
    lookupResType.innerText = data.is_contract ? "Smart Contract (QVM)" : "Externally Owned Account (EOA)";
    lookupResStake.innerText = data.staked_amount.toFixed(4);

    if (data.is_contract && data.storage && Object.keys(data.storage).length > 0) {
      lookupResStorageBox.style.display = "block";
      lookupResStorage.innerText = JSON.stringify(data.storage, null, 2);
    } else {
      lookupResStorageBox.style.display = "none";
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ==========================================
// Active QTH Wallet Operations
// ==========================================
function setWallet(address, seed, mnemonic = "") {
  if (walletAddressInput) walletAddressInput.value = address;
  if (walletSeedInput) walletSeedInput.value = seed;
  if (sealValidatorAddrInput) sealValidatorAddrInput.value = address;
  if (onboardValidatorAddrInput && !onboardValidatorAddrInput.value) {
    onboardValidatorAddrInput.value = address;
  }
  if (onboardDepositorAddrInput && !onboardDepositorAddrInput.value) {
    onboardDepositorAddrInput.value = address;
  }

  localStorage.setItem("qth_wallet_address", address);
  localStorage.setItem("qth_wallet_seed", seed);
  if (mnemonic) {
    localStorage.setItem("qth_wallet_mnemonic", mnemonic);
  }

  fetchAccountState(address);
}

function loadSavedWallet() {
  const savedAddr = localStorage.getItem("qth_wallet_address");
  const savedSeed = localStorage.getItem("qth_wallet_seed");
  const savedMnemonic = localStorage.getItem("qth_wallet_mnemonic");
  if (savedAddr && savedSeed) {
    setWallet(savedAddr, savedSeed, savedMnemonic || "");
  }
}

async function fetchAccountState(address) {
  if (!address) return;
  try {
    const res = await fetch(`${API_BASE}/api/account?address=${encodeURIComponent(address)}`);
    if (!res.ok) return;
    const data = await res.json();

    if (walletBalance) walletBalance.innerText = `${data.balance.toFixed(4)} QTH`;
    if (walletNonce) walletNonce.innerText = data.nonce;
  } catch (err) {
    console.error("Failed to fetch account balance:", err);
  }
}

// Send Transfer
async function submitSendTransaction() {
  const seed = walletSeedInput.value.trim();
  const recipient = sendRecipientInput.value.trim();
  const amount = parseFloat(sendAmountInput.value);

  if (!seed) return showToast("Active QTH Wallet master seed required", "error");
  if (!recipient || !recipient.startsWith("0xQTH_")) return showToast("Valid 0xQTH_ recipient address required", "error");
  if (isNaN(amount) || amount <= 0) return showToast("Enter a valid amount", "error");

  btnSubmitSend.disabled = true;
  btnSubmitSend.innerText = "Signing & Broadcasting...";

  try {
    const res = await fetch(`${API_BASE}/api/wallet/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed, recipient, amount })
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      showToast(`Sent ${amount} QTH! TX: ${data.tx_hash.substring(0, 10)}...`, "success");
      sendAmountInput.value = "";
      fetchNodeInfo();
      fetchAccountState(walletAddressInput.value);
    } else {
      showToast(data.error || "Transaction rejected", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnSubmitSend.disabled = false;
    btnSubmitSend.innerText = "Sign & Broadcast QTH Transfer";
  }
}

// Deploy Contract
async function deploySmartContract() {
  const seed = walletSeedInput.value.trim();
  const code = contractCodeInput.value.trim();

  if (!seed) return showToast("Active QTH Wallet seed required to deploy", "error");
  if (!code) return showToast("Contract code payload required", "error");

  btnDeployContract.disabled = true;
  btnDeployContract.innerText = "Deploying to QVM...";

  try {
    const res = await fetch(`${API_BASE}/api/contract/deploy`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed, code, initial_value: 0.0 })
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      showToast(`Contract deployment queued! TX: ${data.tx_hash.substring(0, 10)}... Seal a block to finalize.`, "success");
      fetchNodeInfo();
    } else {
      showToast(data.error || "Deployment failed", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnDeployContract.disabled = false;
    btnDeployContract.innerText = "Deploy to Quanthreum (QVM)";
  }
}

// Call Contract Method
async function callSmartContract() {
  const seed = walletSeedInput.value.trim();
  const contract = callContractAddrInput.value.trim();
  const action = callActionInput.value.trim();
  let params = {};

  try {
    if (callParamsInput.value.trim()) {
      params = JSON.parse(callParamsInput.value.trim());
    }
  } catch (e) {
    return showToast("Parameters must be valid JSON", "error");
  }

  if (!seed) return showToast("Active QTH Wallet seed required", "error");
  if (!contract || !contract.startsWith("0xQTH_")) return showToast("Valid 0xQTH_ contract address required", "error");
  if (!action) return showToast("Action name required", "error");

  btnCallContract.disabled = true;
  btnCallContract.innerText = "Executing Call...";

  try {
    const res = await fetch(`${API_BASE}/api/contract/call`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed, contract, action, params, value: 0.0 })
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      showToast(`Contract execution queued! TX: ${data.tx_hash.substring(0, 10)}... Seal a block to confirm.`, "success");
      fetchNodeInfo();
    } else {
      showToast(data.error || "Call failed", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnCallContract.disabled = false;
    btnCallContract.innerText = "Execute Smart Contract Method";
  }
}

// ==========================================
// Validator Onboarding & Dual-Key Security
// ==========================================
async function onboardValidator() {
  const valAddr = (onboardValidatorAddrInput.value || walletAddressInput.value || "").trim();
  const depAddr = (onboardDepositorAddrInput.value || valAddr).trim();
  let payRef = (onboardPaymentRefInput.value || "").trim();
  const autoStake = parseFloat(onboardAutoStakeInput.value) || 100.0;

  if (!valAddr || !valAddr.startsWith("0xQTH_")) {
    return showToast("Valid Quanthreum validator address (0xQTH_...) required", "error");
  }

  if (!payRef) {
    payRef = `USDT-VERIFIED-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
    onboardPaymentRefInput.value = payRef;
  }

  btnOnboardValidator.disabled = true;
  btnOnboardValidator.innerText = "Verifying $300 Fee & Crediting 1,000 QTH...";

  try {
    const res = await fetch(`${API_BASE}/api/validator/onboard`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        validator_address: valAddr,
        depositor_address: depAddr,
        payment_ref: payRef,
        payment_usd: 300.0,
        auto_stake: autoStake
      })
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      showToast("Validator Onboarded! 1,000 QTH Credited & 50 QTH/day Cap Active.", "success");
      
      if (onboardResultBox) {
        onboardResultBox.style.display = "block";
        onboardResValAddr.innerText = valAddr;
        onboardResDepAddr.innerText = depAddr;
        onboardResStake.innerText = autoStake.toFixed(2);
      }

      if (sealValidatorAddrInput) {
        sealValidatorAddrInput.value = valAddr;
      }

      fetchNodeInfo();
      fetchAccountState(depAddr);
      if (valAddr !== depAddr) fetchAccountState(valAddr);
    } else {
      showToast(data.error || "Onboarding failed", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnOnboardValidator.disabled = false;
    btnOnboardValidator.innerText = "⚡ Activate Validator License ($300 → 1,000 QTH)";
  }
}

function downloadValidatorBackup() {
  const valAddr = (onboardValidatorAddrInput.value || walletAddressInput.value || "").trim();
  const depAddr = (onboardDepositorAddrInput.value || valAddr).trim();
  const payRef = (onboardPaymentRefInput.value || "USDT-GENESIS-FEE").trim();
  const autoStake = parseFloat(onboardAutoStakeInput.value) || 100.0;

  if (!valAddr) {
    return showToast("Please enter a Validator Node address first", "error");
  }

  const backupData = {
    network: "Quanthreum Mainnet (QTH)",
    version: "1.0.0",
    export_timestamp: new Date().toISOString(),
    security_architecture: "Dual-Key Cold/Hot Isolation",
    keys: {
      validator_node_address: valAddr,
      depositor_cold_address: depAddr,
      key_role_isolation: "Validator Node signs block proposals; Depositor retains fund custody and receives yields."
    },
    economics: {
      registration_fee_usd: 300.0,
      payment_reference: payRef,
      onboarding_credit_qth: 1000.0,
      initial_stake_qth: autoStake,
      daily_reward_cap_qth: 50.0,
      emission_type: "Stake-Proportional Yield (Max 50 QTH/24h)",
      reference_market_target_usd: 15.0
    },
    node_daemon_config: {
      rpc_endpoint: window.location.origin,
      chain_id: 1337,
      target_block_time_seconds: 2,
      base_fee_burn_ratio: 1.0,
      p2p_port: 8545
    },
    cold_storage_recommendation: "Save this backup file directly to an encrypted USB drive, removable physical media, or printed cold vault in a safe. Never store raw private keys on public servers."
  };

  const jsonStr = JSON.stringify(backupData, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const filename = `quanthreum_validator_backup_${valAddr.substring(0, 12)}_${Date.now()}.json`;
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast(`Backup downloaded: ${filename}. Please save to removable drive or safe!`, "success");
}

// Stake Q-PoS
async function submitValidatorStake() {
  const seed = walletSeedInput.value.trim();
  const amount = parseFloat(stakeAmountInput.value);

  if (!seed) return showToast("Active QTH Wallet seed required", "error");
  if (isNaN(amount) || amount < 10.0) return showToast("Minimum stake is 10.0 QTH", "error");

  btnSubmitStake.disabled = true;
  btnSubmitStake.innerText = "Staking into Q-PoS...";

  try {
    const res = await fetch(`${API_BASE}/api/validator/stake`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed, amount })
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      showToast(`Validator Active! Staked ${data.staked_total} QTH`, "success");
      fetchNodeInfo();
      fetchAccountState(walletAddressInput.value);
    } else {
      showToast(data.error || "Staking failed", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnSubmitStake.disabled = false;
    btnSubmitStake.innerText = "Deposit Stake into Q-PoS Pool";
  }
}

// Propose & Seal Block
async function sealBlockNow() {
  const validator = sealValidatorAddrInput.value.trim();
  btnSealBlock.disabled = true;
  btnSealBlock.innerText = "Sealing Block...";

  try {
    const res = await fetch(`${API_BASE}/api/validator/mine_block`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ validator_address: validator })
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      showToast(`Block #${data.block_number} Sealed! Gas Used: ${data.gas_used}`, "success");
      fetchNodeInfo();
      fetchRecentBlocks();
      if (walletAddressInput.value) {
        fetchAccountState(walletAddressInput.value);
      }
    } else {
      showToast(data.error || "Block proposal rejected", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnSealBlock.disabled = false;
    btnSealBlock.innerText = "Propose & Seal Block Now";
  }
}

// ==========================================
// Quantum Security Services & Risk Scanner
// ==========================================
async function runQuantumSecurityAudit() {
  const addrInput = document.getElementById("scanAddressInput");
  const chainSelect = document.getElementById("scanChainSelect");
  const resultCard = document.getElementById("scanResultCard");
  const riskBadge = document.getElementById("scanRiskBadge");
  const statusText = document.getElementById("scanStatusText");
  const threatText = document.getElementById("scanThreatText");
  const recText = document.getElementById("scanRecText");
  const btnScan = document.getElementById("btnScanAddress");

  const address = addrInput ? addrInput.value.trim() : "";
  if (!address) {
    return showToast("Please enter an address to scan.", "error");
  }

  btnScan.disabled = true;
  btnScan.innerText = "Analyzing Quantum Vulnerability...";

  try {
    const chain = chainSelect ? chainSelect.value : "ethereum";
    const res = await fetch(`${API_BASE}/api/security/scan?address=${encodeURIComponent(address)}&chain=${encodeURIComponent(chain)}`);
    const data = await res.json();

    if (res.ok) {
      resultCard.style.display = "block";
      if (data.risk_level === "IMMUNE") {
        riskBadge.innerText = "0/100 (IMMUNE)";
        riskBadge.style.background = "#10b981";
        riskBadge.style.color = "#000";
      } else {
        riskBadge.innerText = `${data.risk_score}/100 (${data.risk_level})`;
        riskBadge.style.background = "#f43f5e";
        riskBadge.style.color = "#fff";
      }
      statusText.innerText = data.quantum_status;
      threatText.innerText = data.shor_vulnerable 
        ? `${data.quantum_threat_breakdown.algorithm} (~2,048 logical qubits to compromise)` 
        : "Immune to Shor's algorithm (512-bit entropy)";
      recText.innerText = data.recommendation || (data.mitigation_path ? data.mitigation_path.solution : "");
      showToast("Quantum security audit completed!", "success");
    } else {
      showToast(data.error || "Audit failed", "error");
    }
  } catch (err) {
    showToast("Audit network error: " + err.message, "error");
  } finally {
    btnScan.disabled = false;
    btnScan.innerText = "Run Quantum Security Audit";
  }
}

async function simulateEnterpriseCoSign() {
  const digestInput = document.getElementById("verifyDigestInput");
  const resultCard = document.getElementById("verifyResultCard");
  const detailsText = document.getElementById("verifyDetailsText");
  const btnSim = document.getElementById("btnTestQuantumSign");

  const message = digestInput ? digestInput.value.trim() : "Transfer 100,000 USDT";
  btnSim.disabled = true;
  btnSim.innerText = "Generating Quantum Proof...";

  try {
    let seed = walletSeedInput.value.trim();
    if (!seed) {
      seed = "0000000000000000000000000000000000000000000000000000000000000001";
    }

    const signRes = await fetch(`${API_BASE}/api/security/sign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed: seed, payload: message })
    });
    const signData = await signRes.json();

    if (!signRes.ok || signData.status !== "success") {
      throw new Error(signData.error || "Signing failed");
    }

    const verifyRes = await fetch(`${API_BASE}/api/security/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        payload_hash: signData.payload_hash,
        public_key: signData.public_key,
        signature: signData.signature
      })
    });
    const verifyData = await verifyRes.json();

    if (verifyRes.ok && verifyData.verified) {
      resultCard.style.display = "block";
      detailsText.innerHTML = `
        <div><strong>Standard:</strong> ${verifyData.security_standard}</div>
        <div><strong>Hash Chains:</strong> 67 iterative chains over SHA3-256</div>
        <div><strong>Quantum Co-Signer:</strong> ${signData.address}</div>
        <div><strong>Digest:</strong> ${signData.payload_hash.substring(0, 24)}...</div>
        <div><strong>Proof Size:</strong> ${signData.signature.length / 2} bytes (Winternitz OTS+)</div>
      `;
      showToast("Enterprise Quantum Proof verified!", "success");
    } else {
      showToast("Verification failed: " + (verifyData.error || "Invalid proof"), "error");
    }
  } catch (err) {
    showToast("Simulation error: " + err.message, "error");
  } finally {
    btnSim.disabled = false;
    btnSim.innerText = "Simulate Enterprise Co-Sign & Verify";
  }
}

// ==========================================
// Event Listeners & Initialization
// ==========================================
function setupEventListeners() {
  // Wizard Mode Switcher
  if (tabCreateNew) {
    tabCreateNew.addEventListener("click", () => {
      tabCreateNew.classList.add("active");
      if (tabRestore) tabRestore.classList.remove("active");
      if (flowCreateNew) flowCreateNew.style.display = "block";
      if (flowRestore) flowRestore.style.display = "none";
    });
  }

  if (tabRestore) {
    tabRestore.addEventListener("click", () => {
      tabRestore.classList.add("active");
      if (tabCreateNew) tabCreateNew.classList.remove("active");
      if (flowRestore) flowRestore.style.display = "block";
      if (flowCreateNew) flowCreateNew.style.display = "none";
    });
  }

  // Password Flow
  if (btnSetPasswordProceed) btnSetPasswordProceed.addEventListener("click", handlePasswordProceed);
  if (btnToggleNewPass && inputNewPassword) {
    btnToggleNewPass.addEventListener("click", () => {
      inputNewPassword.type = inputNewPassword.type === "password" ? "text" : "password";
    });
  }
  if (btnToggleConfirmPass && inputConfirmPassword) {
    btnToggleConfirmPass.addEventListener("click", () => {
      inputConfirmPassword.type = inputConfirmPassword.type === "password" ? "text" : "password";
    });
  }

  // Reveal Button
  if (btnRevealWordsAction) btnRevealWordsAction.addEventListener("click", handleRevealWords);

  // 48-word Grid Tools
  if (btnToggleBlur && mnemonicGrid) {
    btnToggleBlur.addEventListener("click", () => {
      mnemonicGrid.classList.toggle("blurred");
    });
  }

  if (btnCopy48Words) btnCopy48Words.addEventListener("click", copyAll48Words);
  if (btnDownloadBackup) btnDownloadBackup.addEventListener("click", downloadPaperBackup);

  const btnCopyRevealed = document.getElementById("btnCopyRevealedAddress");
  if (btnCopyRevealed) {
    btnCopyRevealed.addEventListener("click", () => {
      if (currentGeneratedWallet && currentGeneratedWallet.address) {
        navigator.clipboard.writeText(currentGeneratedWallet.address);
        showToast("New QTH Address copied to clipboard!", "success");
      }
    });
  }

  const btnCreateAnother = document.getElementById("btnCreateAnotherNew");
  if (btnCreateAnother) {
    btnCreateAnother.addEventListener("click", resetCreateWalletWizard);
  }

  if (chkSavedWords && btnActivateWallet) {
    chkSavedWords.addEventListener("change", (e) => {
      btnActivateWallet.disabled = !e.target.checked;
    });
  }

  if (btnActivateWallet) btnActivateWallet.addEventListener("click", activateQTHWallet);

  // Restore Input word counter
  if (restoreInput && restoreWordCounter && restoreValidationStatus) {
    restoreInput.addEventListener("input", (e) => {
      const text = e.target.value.trim();
      const count = text ? text.split(/\s+/).length : 0;
      restoreWordCounter.innerText = `${count} / 48 words`;
      if (count === 48) {
        restoreValidationStatus.innerText = "✓ 48 words entered";
        restoreValidationStatus.className = "validation-status valid";
      } else {
        restoreValidationStatus.innerText = "";
      }
    });
  }

  if (btnRestoreSubmit) btnRestoreSubmit.addEventListener("click", restoreFrom48Words);

  // Active Wallet Copy & Toggle
  if (btnCopyAddress) {
    btnCopyAddress.addEventListener("click", () => {
      if (walletAddressInput && walletAddressInput.value) {
        navigator.clipboard.writeText(walletAddressInput.value);
        showToast("Address copied to clipboard!", "info");
      }
    });
  }

  if (btnToggleSeed && walletSeedInput) {
    btnToggleSeed.addEventListener("click", () => {
      walletSeedInput.type = walletSeedInput.type === "password" ? "text" : "password";
    });
  }

  if (btnRefreshBalance && walletAddressInput) {
    btnRefreshBalance.addEventListener("click", () => {
      fetchAccountState(walletAddressInput.value);
      showToast("Account balance refreshed", "info");
    });
  }

  if (walletAddressInput) {
    walletAddressInput.addEventListener("change", () => {
      fetchAccountState(walletAddressInput.value);
    });
  }

  // Transfer
  if (btnSubmitSend) {
    btnSubmitSend.addEventListener("click", submitSendTransaction);
  }

  // Inspector
  if (btnLookupAddress && lookupAddressInput) {
    btnLookupAddress.addEventListener("click", () => {
      inspectAccount(lookupAddressInput.value.trim());
    });
  }

  // Template select
  if (contractTemplateSelect && contractCodeInput) {
    contractTemplateSelect.addEventListener("change", (e) => {
      const tmpl = TEMPLATES[e.target.value];
      if (tmpl) contractCodeInput.value = tmpl;
    });
  }

  // Contract actions
  if (btnDeployContract) btnDeployContract.addEventListener("click", deploySmartContract);
  if (btnCallContract) btnCallContract.addEventListener("click", callSmartContract);

  // Staking & Mining
  if (btnOnboardValidator) {
    btnOnboardValidator.addEventListener("click", onboardValidator);
  }
  if (btnDownloadValidatorBackup) {
    btnDownloadValidatorBackup.addEventListener("click", downloadValidatorBackup);
  }
  if (btnSubmitStake) btnSubmitStake.addEventListener("click", submitValidatorStake);
  if (btnSealBlock) btnSealBlock.addEventListener("click", sealBlockNow);

  const btnRefreshBlocks = document.getElementById("btnRefreshBlocks");
  if (btnRefreshBlocks) {
    btnRefreshBlocks.addEventListener("click", () => {
      fetchRecentBlocks();
      showToast("Block feed refreshed", "info");
    });
  }

  // Enterprise Quantum Security Services
  const btnScanAddress = document.getElementById("btnScanAddress");
  if (btnScanAddress) {
    btnScanAddress.addEventListener("click", runQuantumSecurityAudit);
  }
  const btnTestQuantumSign = document.getElementById("btnTestQuantumSign");
  if (btnTestQuantumSign) {
    btnTestQuantumSign.addEventListener("click", simulateEnterpriseCoSign);
  }
}

// Bootstrap
window.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  if (contractCodeInput && TEMPLATES && TEMPLATES.qrc20) {
    contractCodeInput.value = TEMPLATES.qrc20;
  }
  loadSavedWallet();

  fetchNodeInfo();
  setInterval(fetchNodeInfo, 3000);
});
