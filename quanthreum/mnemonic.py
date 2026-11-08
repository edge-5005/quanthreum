"""
Quanthreum (QTH) - 48-Word Post-Quantum Mnemonic Seed Engine
Implements:
  - 512-bit Quantum Entropy Mnemonic Generation (48 Words)
  - 16-bit Checksum Verification (BIP-39 math extended to 512-bit entropy)
  - PBKDF2-HMAC-SHA512 Quantum Seed Derivation
  - Full phrase validation and restoration
"""

import hashlib
import os
import secrets
import unicodedata
from typing import List, Tuple

WORDLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bip39_words.txt")

_WORDS: List[str] = []
_WORD_INDEX: dict = {}


def _load_wordlist():
    global _WORDS, _WORD_INDEX
    if not _WORDS:
        with open(WORDLIST_PATH, "r", encoding="utf-8") as f:
            _WORDS = [line.strip() for line in f if line.strip()]
        if len(_WORDS) != 2048:
            raise ValueError(f"Expected 2048 words, loaded {len(_WORDS)}")
        _WORD_INDEX = {w: i for i, w in enumerate(_WORDS)}


def generate_48_word_mnemonic(passphrase: str = "") -> Tuple[str, bytes]:
    """
    Generate a 48-word Post-Quantum mnemonic phrase.
    Entropy: 512 bits (64 bytes)
    Checksum: 16 bits (SHA-256(entropy)[:2] bytes)
    Total bits: 528 bits = 48 words * 11 bits
    """
    _load_wordlist()
    # 512 bits of cryptographically secure entropy
    entropy = secrets.token_bytes(64)

    # 16-bit checksum from SHA-256
    checksum = hashlib.sha256(entropy).digest()[:2]
    data = entropy + checksum  # 66 bytes = 528 bits

    # Convert to 528 bits binary string
    bits = "".join(f"{byte:08b}" for byte in data)

    # Split into 48 chunks of 11 bits
    words = []
    for i in range(0, 528, 11):
        idx = int(bits[i : i + 11], 2)
        words.append(_WORDS[idx])

    mnemonic = " ".join(words)
    seed = mnemonic_to_seed(mnemonic, passphrase)
    return mnemonic, seed


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """
    Derive 512-bit Quantum Master Seed from 48-word mnemonic using PBKDF2-HMAC-SHA512.
    """
    words = mnemonic.strip().split()
    if len(words) != 48:
        raise ValueError(f"Quanthreum requires exactly 48 words (got {len(words)})")

    # Normalize unicode
    norm_mnemonic = unicodedata.normalize("NFKD", " ".join(words))
    norm_salt = unicodedata.normalize("NFKD", "mnemonic" + passphrase)

    # 2048 iterations of PBKDF2-HMAC-SHA512
    return hashlib.pbkdf2_hmac(
        "sha512",
        norm_mnemonic.encode("utf-8"),
        norm_salt.encode("utf-8"),
        iterations=2048,
        dklen=64
    )


def validate_mnemonic(mnemonic: str) -> Tuple[bool, str]:
    """
    Validate that a 48-word mnemonic has valid words and correct checksum.
    """
    _load_wordlist()
    words = mnemonic.strip().split()
    if len(words) != 48:
        return False, f"Expected 48 words for Post-Quantum wallet, got {len(words)}"

    bits = []
    for w in words:
        if w not in _WORD_INDEX:
            return False, f"Unknown word '{w}' in mnemonic"
        idx = _WORD_INDEX[w]
        bits.append(f"{idx:011b}")

    bit_str = "".join(bits)
    if len(bit_str) != 528:
        return False, "Bit length mismatch"

    entropy_bits = bit_str[:512]
    checksum_bits = bit_str[512:]

    # Convert entropy bits back to bytes
    entropy_bytes = bytearray()
    for i in range(0, 512, 8):
        entropy_bytes.append(int(entropy_bits[i : i + 8], 2))

    expected_checksum_bytes = hashlib.sha256(bytes(entropy_bytes)).digest()[:2]
    expected_checksum_bits = "".join(f"{b:08b}" for b in expected_checksum_bytes)

    if checksum_bits != expected_checksum_bits:
        return False, "Invalid mnemonic checksum. Please check your words."

    return True, "Valid 48-word Post-Quantum mnemonic"
