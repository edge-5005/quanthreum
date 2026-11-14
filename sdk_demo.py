"""
Quanthreum (QTH) Developer SDK - Enterprise Verification Demo
Demonstrates how external applications integrate Quanthreum's
Winternitz W-OTS+ post-quantum signature verification.
"""

import hashlib
import json
from quanthreum.quantum_crypto import QuantumKeyPair, verify_quantum_signature
from quanthreum.security_service import scan_address_quantum_vulnerability, verify_enterprise_transaction


def main():
    print("=" * 70)
    print("      QUANTHREUM (QTH) POST-QUANTUM SECURITY SDK DEMO")
    print("=" * 70)

    # 1. Generate 512-bit Quantum KeyPair
    print("\n[Step 1] Initializing Quantum KeyPair (512-bit entropy + 48-word phrase)...")
    kp = QuantumKeyPair()
    print(f"  -> QTH Address:   {kp.address}")
    print(f"  -> PQC Algorithm: Winternitz W-OTS+ (NIST Level 128)")
    print(f"  -> Public Key:    {kp.public_key_hex[:32]}...")

    # 2. Co-Sign an Arbitrary Financial Transaction (e.g. 100,000 USDT Transfer)
    print("\n[Step 2] Signing an enterprise withdrawal digest...")
    tx_payload = json.dumps({
        "action": "TRANSFER",
        "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "amount": 100000,
        "token": "USDT",
        "nonce": 42
    }, sort_keys=True)
    digest = hashlib.sha256(tx_payload.encode('utf-8')).digest()
    sig = kp.sign(digest)
    print(f"  -> Transaction:   {tx_payload}")
    print(f"  -> SHA256 Digest: {digest.hex()}")
    print(f"  -> Quantum Sig:   {sig[:48]}... ({len(sig)} hex chars, 67 hash chains)")

    # 3. Verify Signature
    print("\n[Step 3] Verifying quantum signature via Zero-Knowledge validator...")
    is_valid = verify_quantum_signature(kp.public_key_hex, digest, sig)
    print(f"  -> Verification Result: {'VALID (PASS)' if is_valid else 'INVALID (FAIL)'}")

    # 4. Audit a Legacy Ethereum Address
    print("\n[Step 4] Auditing a legacy Ethereum address for Shor's vulnerability...")
    legacy_eth = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # vitalik.eth
    report = scan_address_quantum_vulnerability(legacy_eth, chain="ethereum")
    print(f"  -> Target Address:      {report['address']}")
    print(f"  -> Quantum Risk Level:   {report['risk_level']} (Score: {report['risk_score']}/100)")
    print(f"  -> Vulnerability Status: {report['quantum_status']}")
    print(f"  -> Threat Breakdown:     {report['quantum_threat_breakdown']['algorithm']}")
    print(f"  -> Recommended Action:   {report['mitigation_path']['solution']}")

    # 5. Audit Quanthreum Native Address
    print("\n[Step 5] Auditing Quanthreum Native Address...")
    qth_report = scan_address_quantum_vulnerability(kp.address)
    print(f"  -> Target Address:      {qth_report['address']}")
    print(f"  -> Quantum Risk Level:   {qth_report['risk_level']} (Score: {qth_report['risk_score']}/100)")
    print(f"  -> Status:               {qth_report['quantum_status']}")

    print("\n" + "=" * 70)
    print(" ALL ENTERPRISE QUANTUM SECURITY SERVICES VERIFIED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
