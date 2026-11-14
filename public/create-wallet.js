/**
 * Quanthreum (QTH) - Dedicated Wallet Creation & Restoration Engine
 */

const API_BASE = window.location.origin;

let current48Mnemonic = "";
let currentGeneratedWallet = null;
let walletPassword = "";

// Elements
const tabCreateNew = document.getElementById("tabCreateNew");
const tabRestore = document.getElementById("tabRestore");
const flowCreateNew = document.getElementById("flowCreateNew");
const flowRestore = document.getElementById("flowRestore");

// Step 1: Password
const stepPasswordCreation = document.getElementById("stepPasswordCreation");
const inputNewPassword = document.getElementById("inputNewPassword");
const inputConfirmPassword = document.getElementById("inputConfirmPassword");
const btnToggleNewPass = document.getElementById("btnToggleNewPass");
const btnToggleConfirmPass = document.getElementById("btnToggleConfirmPass");
const passwordErrorMsg = document.getElementById("passwordErrorMsg");
const btnSetPasswordProceed = document.getElementById("btnSetPasswordProceed");

// Step 2: Reveal & Backup
const stepRevealPhrase = document.getElementById("stepRevealPhrase");
const revealShieldBox = document.getElementById("revealShieldBox");
const btnRevealWordsAction = document.getElementById("btnRevealWordsAction");
const revealedContentBox = document.getElementById("revealedContentBox");
const mnemonicGrid = document.getElementById("mnemonicGrid");
const btnToggleBlur = document.getElementById("btnToggleBlur");
const btnCopy48Words = document.getElementById("btnCopy48Words");
const btnDownloadBackup = document.getElementById("btnDownloadBackup");
const btnCreateAnotherNew = document.getElementById("btnCreateAnotherNew");
const chkSavedWords = document.getElementById("chkSavedWords");
const btnActivateWallet = document.getElementById("btnActivateWallet");
const createdWalletSummary = document.getElementById("createdWalletSummary");
const newWalletAddr = document.getElementById("newWalletAddr");
const newWalletPub = document.getElementById("newWalletPub");

// Restore
const restoreInput = document.getElementById("restoreInput");
const restoreWordCounter = document.getElementById("restoreWordCounter");
const restoreValidationStatus = document.getElementById("restoreValidationStatus");
const restorePassword = document.getElementById("restorePassword");
const restoreConfirmPassword = document.getElementById("restoreConfirmPassword");
const btnRestoreSubmit = document.getElementById("btnRestoreSubmit");

// Toast helper
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function createToastContainer() {
  const c = document.createElement("div");
  c.id = "toastContainer";
  c.className = "toast-container";
  document.body.appendChild(c);
  return c;
}

// Mode Switcher
tabCreateNew.addEventListener("click", () => {
  tabCreateNew.classList.add("active");
  tabRestore.classList.remove("active");
  flowCreateNew.style.display = "block";
  flowRestore.style.display = "none";
});

tabRestore.addEventListener("click", () => {
  tabRestore.classList.add("active");
  tabCreateNew.classList.remove("active");
  flowRestore.style.display = "block";
  flowCreateNew.style.display = "none";
});

// Password toggles
btnToggleNewPass.addEventListener("click", () => {
  inputNewPassword.type = inputNewPassword.type === "password" ? "text" : "password";
});

btnToggleConfirmPass.addEventListener("click", () => {
  inputConfirmPassword.type = inputConfirmPassword.type === "password" ? "text" : "password";
});

// Step 1: Proceed
btnSetPasswordProceed.addEventListener("click", async () => {
  const p1 = inputNewPassword.value;
  const p2 = inputConfirmPassword.value;

  if (p1.length < 8) {
    showPasswordError("Password must be at least 8 characters long.");
    return;
  }
  if (p1 !== p2) {
    showPasswordError("Passwords do not match.");
    return;
  }

  passwordErrorMsg.style.display = "none";
  walletPassword = p1;

  btnSetPasswordProceed.disabled = true;
  btnSetPasswordProceed.innerText = "Generating 512-bit Entropy...";

  try {
    const res = await fetch(`${API_BASE}/api/wallet/create`, { method: "POST" });
    const data = await res.json();

    if (res.ok && data.mnemonic) {
      current48Mnemonic = data.mnemonic;
      currentGeneratedWallet = data;

      stepPasswordCreation.style.display = "none";
      stepRevealPhrase.style.display = "block";
      showToast("512-bit Quantum Seed Phrase Generated!", "success");
    } else {
      showToast(data.error || "Failed to generate wallet", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnSetPasswordProceed.disabled = false;
    btnSetPasswordProceed.innerText = "Set Password & Generate 48-Word Seed Phrase →";
  }
});

function showPasswordError(msg) {
  passwordErrorMsg.innerText = msg;
  passwordErrorMsg.style.display = "block";
}

// Step 2: Reveal Words
btnRevealWordsAction.addEventListener("click", () => {
  revealShieldBox.style.display = "none";
  revealedContentBox.style.display = "block";
  renderMnemonicGrid(current48Mnemonic);
});

function renderMnemonicGrid(phrase) {
  mnemonicGrid.innerHTML = "";
  const words = phrase.trim().split(/\s+/);
  words.forEach((w, idx) => {
    const pill = document.createElement("div");
    pill.className = "mnemonic-word-pill";
    pill.innerHTML = `<span class="word-idx">${idx + 1}</span><span class="word-val">${w}</span>`;
    mnemonicGrid.appendChild(pill);
  });
}

// Blur toggle
let isBlurred = false;
btnToggleBlur.addEventListener("click", () => {
  isBlurred = !isBlurred;
  mnemonicGrid.style.filter = isBlurred ? "blur(8px)" : "none";
  btnToggleBlur.innerText = isBlurred ? "👁️ Unblur Words" : "👁️ Privacy Blur";
});

// Copy 48 words
btnCopy48Words.addEventListener("click", () => {
  if (!current48Mnemonic) return;
  navigator.clipboard.writeText(current48Mnemonic).then(() => {
    showToast("Copied 48-word phrase to clipboard!", "success");
  }).catch(() => {
    showToast("Failed to copy phrase", "error");
  });
});

// Download JSON Keystore
btnDownloadBackup.addEventListener("click", () => {
  if (!currentGeneratedWallet) return;
  const backupData = {
    network: "Quanthreum Mainnet (QTH)",
    version: "1.0.0",
    created_at: new Date().toISOString(),
    address: currentGeneratedWallet.address,
    public_key: currentGeneratedWallet.public_key,
    word_count: 48,
    mnemonic: current48Mnemonic,
    seed_hex: currentGeneratedWallet.seed,
    cryptography: "Winternitz W-OTS+ (NIST Post-Quantum Level 128)",
    notice: "STORE THIS FILE ON AN ENCRYPTED REMOVABLE USB DRIVE OR PHYSICAL SAFE. NEVER DISCLOSE PRIVATE SEEDS."
  };

  const jsonStr = JSON.stringify(backupData, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `quanthreum_wallet_backup_${currentGeneratedWallet.address.substring(0, 12)}_${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast("Keystore backup file downloaded successfully!", "success");
});

// Generate another
btnCreateAnotherNew.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to discard this phrase and generate another?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/wallet/create`, { method: "POST" });
    const data = await res.json();
    if (res.ok && data.mnemonic) {
      current48Mnemonic = data.mnemonic;
      currentGeneratedWallet = data;
      renderMnemonicGrid(current48Mnemonic);
      chkSavedWords.checked = false;
      btnActivateWallet.disabled = true;
      createdWalletSummary.style.display = "none";
      showToast("Fresh 48-word phrase generated!", "info");
    }
  } catch (e) {
    showToast(e.message, "error");
  }
});

// Enable activation on checkbox
chkSavedWords.addEventListener("change", (e) => {
  btnActivateWallet.disabled = !e.target.checked;
});

// Activate Wallet
btnActivateWallet.addEventListener("click", () => {
  if (!currentGeneratedWallet) return;

  const addr = currentGeneratedWallet.address;
  const seed = currentGeneratedWallet.seed;

  localStorage.setItem("qth_wallet_address", addr);
  localStorage.setItem("qth_wallet_seed", seed);
  localStorage.setItem("qth_wallet_mnemonic", current48Mnemonic);

  newWalletAddr.innerText = addr;
  newWalletPub.innerText = currentGeneratedWallet.public_key;
  createdWalletSummary.style.display = "block";
  btnActivateWallet.disabled = true;
  chkSavedWords.disabled = true;

  showToast("QTH Wallet Activated! Ready for transactions and validator staking.", "success");
});

// Restore Flow
restoreInput.addEventListener("input", (e) => {
  const text = e.target.value.trim();
  const count = text ? text.split(/\s+/).length : 0;
  restoreWordCounter.innerText = `${count} / 48 words`;

  if (count === 48) {
    restoreValidationStatus.innerText = "✓ Valid 48-word structure";
    restoreValidationStatus.className = "validation-status valid";
  } else {
    restoreValidationStatus.innerText = count < 48 ? `Need ${48 - count} more words` : `${count - 48} words too many`;
    restoreValidationStatus.className = "validation-status invalid";
  }
});

btnRestoreSubmit.addEventListener("click", async () => {
  const phrase = restoreInput.value.trim();
  const words = phrase ? phrase.split(/\s+/) : [];
  if (words.length !== 48) {
    return showToast(`Mnemonic must contain exactly 48 words (currently ${words.length})`, "error");
  }

  const p1 = restorePassword.value;
  const p2 = restoreConfirmPassword.value;
  if (p1.length < 8) {
    return showToast("Password must be at least 8 characters", "error");
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
      localStorage.setItem("qth_wallet_address", data.address);
      localStorage.setItem("qth_wallet_seed", data.seed);
      localStorage.setItem("qth_wallet_mnemonic", phrase);

      showToast("QTH Wallet Successfully Restored! Redirecting to Dashboard...", "success");
      setTimeout(() => {
        window.location.href = "/#wallet";
      }, 1500);
    } else {
      showToast(data.error || "Restoration failed", "error");
    }
  } catch (err) {
    showToast("Network error: " + err.message, "error");
  } finally {
    btnRestoreSubmit.disabled = false;
    btnRestoreSubmit.innerText = "Verify & Restore QTH Wallet";
  }
});
