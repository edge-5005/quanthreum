# Quanthreum (QTH) Whitepaper
**A Post-Quantum EVM-Compatible Layer-1 Blockchain with Winternitz Cryptography & Deflationary Tokenomics**

*Technical Specification — Version 1.0*  

---

## 1. Abstract
As fault-tolerant quantum computers approach commercial realization, the cryptographic foundations of existing distributed ledgers face an existential crisis. Standard public-key cryptosystems—including RSA, ECDSA (used in Bitcoin and Ethereum), and Ed25519 (used in Solana and Cardano)—are mathematically vulnerable to polynomial-time factorization and discrete logarithm extraction via Shor's algorithm. 

**Quanthreum (QTH)** is an enterprise Layer-1 blockchain engineered to deliver absolute post-quantum security without sacrificing smart contract programmability or developer interoperability. Quanthreum replaces elliptic curve cryptography with **Winternitz One-Time Signatures Plus (W-OTS+)** over 67 iterative SHA3-256 hash chains, providing 512-bit master entropy and NIST-standardized post-quantum resistance. Coupled with an EVM-compatible execution engine (QVM), Quantum Proof-of-Stake (Q-PoS) consensus, an EIP-1559 deflationary burn mechanism, and a hard supply cap of 100,000,000 QTH, Quanthreum provides a permanent, scalable safe harbor for decentralized digital assets.

---

## 2. The Quantum Cryptographic Threat

### 2.1 The Vulnerability of Discrete Logarithms & Elliptic Curves
Modern blockchains secure transactions using Elliptic Curve Digital Signature Algorithm (ECDSA) on the `secp256k1` curve. The security of this mechanism rests entirely on the hardness of the Elliptic Curve Discrete Logarithm Problem (ECDLP):
$$Q = d \cdot G$$
where $d$ is the 256-bit private scalar and $Q$ is the public curve point.

On a classical computer, finding $d$ given $Q$ requires Pollard’s rho algorithm with exponential time complexity:
$$\mathcal{O}(\sqrt{n}) \approx 2^{128} \text{ operations}$$

However, Peter Shor's quantum algorithm solves the discrete logarithm problem in bounded polynomial time:
$$\mathcal{O}((\log N)^3)$$
Executing Shor's algorithm on an elliptic curve requires approximately **2,048 to 4,096 logical qubits**. Estimates from global quantum research institutions indicate this threshold could be reached within the 2030s.

### 2.2 The Public Key Exposure Attack Vector
Many blockchains rely on address hashing (e.g., $Address = \text{Keccak-256}(Q)[12..31]$). While an unspent address only reveals a hash, **the moment an outgoing transaction is broadcast, the unhashed public point $Q$ is published in the global mempool**. A quantum adversary can intercept this broadcast, compute $d$ before the block is mined, forge a competing transaction with higher gas fees, and drain the wallet.

---

## 3. The Quanthreum Cryptographic Framework

Quanthreum eliminates elliptic curves entirely, building its cryptographic identity and authentication on hash-based, information-theoretically secure primitives.

### 3.1 Winternitz One-Time Signatures Plus (W-OTS+)
Quanthreum implements the W-OTS+ scheme parameterized over SHA3-256 / Keccak-256:
* **Winternitz Parameter ($w$):** $16$ (nibble decomposition, $\log_2(w) = 4$).
* **Message Length ($l_1$):** $64$ nibbles (representing a 256-bit SHA3 digest).
* **Checksum Nibbles ($l_2$):** $3$ nibbles to prevent bit-tampering.
* **Total Hash Chains ($l$):** $l_1 + l_2 = 67$ iterative chains.

#### Key Generation:
$$\text{Private Key: } sk = (sk_1, sk_2, \dots, sk_{67}), \quad sk_i \in \{0, 1\}^{256}$$
$$\text{Public Key: } pk_i = H^{w-1}(sk_i) = H^{15}(sk_i), \quad pk = H(pk_1 \parallel pk_2 \parallel \dots \parallel pk_{67})$$

#### Signing Algorithm:
For any message digest $M = H_{SHA3}(\text{Transaction})$, $M$ is parsed as 64 4-bit integers $(m_1, \dots, m_{64})$ with checksum $C = \sum_{i=1}^{64} (15 - m_i)$:
$$\sigma_i = H^{m_i}(sk_i), \quad \text{for } i \in [1, 67]$$

#### Verification:
The verifier does not need the private key; they complete the remaining $(15 - m_i)$ hash iterations to reconstruct the public key root:
$$pk'_i = H^{15 - m_i}(\sigma_i)$$
The transaction is valid if and only if $H(pk'_1 \parallel \dots \parallel pk'_{67}) == pk$.

### 3.2 512-Bit Master Entropy & 48-Word Mnemonics
To exceed classical 128-bit or 256-bit seed limitations, Quanthreum derives all hierarchical deterministic keypairs from **512 bits of cryptographically secure pseudo-random entropy (CSPRNG)**, encoded into a standardized **48-word mnemonic phrase** using the BIP-39 English dictionary.

---

## 4. Quanthreum Virtual Machine (QVM) & EVM Compatibility

Quanthreum maintains full state-machine compatibility with EVM architecture while substituting the cryptographic verification layer:

* **State Storage:** Accounts are identified by `0xQTH_<20_byte_hex>`. Each account tracks `balance`, `nonce`, `code`, and a persistent key-value `storage` map.
* **Smart Contract Standards:**
  * **QRC-20:** Quantum-resistant fungible tokens with post-quantum approval allowances.
  * **Quantum Multi-Sig Vaults:** $M$-of-$N$ threshold governance requiring zero-knowledge W-OTS+ proofs before fund release.
  * **KeyValueRegistry:** Decentralized on-chain data storage and identity mapping.

---

## 5. Quantum Proof-of-Stake (Q-PoS) Consensus

Quanthreum replaces energy-intensive mining with a quantum-hardened Proof-of-Stake consensus:

1. **Validator Registry:** Any account holding $\ge 10.0$ QTH can stake tokens to become a registered validator node.
2. **Block Proposal & Sealing:** Validators are deterministically selected based on state root seed entropy and stake weight.
3. **Block Header Integrity:** Every block header incorporates:
   * Block Number (`height`)
   * Previous Block Hash (`prev_hash`)
   * Merkle State Root (`state_root`)
   * Transactions Root (`tx_root`)
   * Proposer QTH Address & W-OTS+ Signature
   * EIP-1559 Dynamic Base Fee & Gas Limit
4. **Target Cadence:** Optimized for 6-second block times with sub-second finality.

---

## 6. Tokenomics & Deflationary Economic Model

Quanthreum enforces a strict, mathematical tokenomic model designed for long-term store of value.

```
Total Max Supply: 100,000,000.0 QTH (Strict Hard Cap)
Genesis Liquidity: 10,000,000.0 QTH (10.0% Allocation)
Remaining Mintable: 90,000,000.0 QTH (Distributed via Q-PoS Block Rewards)
```

| Parameter | Specification | Purpose |
| :--- | :--- | :--- |
| **Ticker** | **QTH** | Native settlement asset |
| **Max Cap** | **100,000,000 QTH** | Strictly immutable in consensus rules |
| **Initial Block Reward** | **2.0 QTH** | Sustainable validator incentivization |
| **Halving / Decay** | Dynamic boundary clamp | Prevents minting beyond 100,000,000 QTH |
| **Base Gas Fee** | Dynamic EIP-1559 (starts at 0.00001 QTH) | Adjusted by block fullness |
| **Fee Burning** | **100% of Base Fee is Burned** | Introduces net-deflationary pressure under volume |

---

## 7. Protocol Security Services

Beyond native gas settlement, Quanthreum provides modular security mechanisms that interface with external networks:

### 7.1 Quantum Vulnerability Scanner
An algorithmic auditor that evaluates public key exposure on legacy networks including Ethereum, Bitcoin, and Solana.

### 7.2 Post-Quantum Co-Signing Gateway
DeFi protocols, cross-chain bridges, and institutional vaults integrate the Quanthreum verification engine as a dual-signature co-signer. High-value transactions require a Quanthreum W-OTS+ cryptographic validation proof before execution.

### 7.3 On-Chain Quantum Multi-Sig Vaults
Decentralized autonomous organizations and treasuries deploy threshold-governed multi-sig contracts on the QVM, requiring $M$-of-$N$ quantum signatures to authorize asset disbursement.

---

## 8. Comparative Matrix: Quanthreum vs. Major Blockchains

| Feature | Bitcoin (BTC) | Ethereum (ETH) | Quantum Resistant Ledger (QRL) | Quanthreum (QTH) |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Signature** | ECDSA (Secp256k1) | ECDSA (Secp256k1) | XMSS (Hash-based) | **Winternitz W-OTS+ (SHA3-256)** |
| **Shor's Algorithm Immunity** | ❌ Vulnerable | ❌ Vulnerable | ✅ Immune | **✅ Immune (128-bit NIST PQC)** |
| **EVM / Smart Contracts** | ❌ None | ✅ EVM (Solidity) | ❌ Limited / Non-EVM | **✅ Native QVM & State Model** |
| **Master Entropy** | 128 / 256 bits | 128 / 256 bits | 256 bits | **512 bits (48 Words)** |
| **Max Coin Supply** | 21,000,000 | Infinite (Burn dependent) | 105,000,000 | **100,000,000 QTH (Hard Cap)** |
| **Fee Burning Model** | ❌ None | ✅ EIP-1559 | ❌ None | **✅ EIP-1559 Deflationary Burn** |
| **External Security Gateway** | ❌ None | ❌ None | ❌ None | **✅ Live Dual-Signature API** |
| **Validator Tooling** | ASIC Hardware | Proof-of-Stake (32 ETH) | PoW / PoS Hybrid | **1-Click Studio & Q-PoS** |

---

## 9. Technical Roadmap

* **Phase 1 (Completed):** Core ledger, 512-bit mnemonic derivation, Winternitz W-OTS+ signature engine, QVM execution environment, Q-PoS validator consensus, and EIP-1559 fee burning.
* **Phase 2 (Completed):** 1-Click Validator Studio, interactive Web3 portal deployment, and public REST API.
* **Phase 3 (Current):** Quantum Co-Signing Gateway, Multi-Sig Treasury Vaults, live Address Vulnerability Scanner, and Developer SDK.
* **Phase 4 (Next):** Free listing submissions (CoinSniper, CoinCodex), wrapped ERC-20 token bridge (`wQTH`), and decentralized liquidity pool deployment.
* **Phase 5:** Formal NIST PQC validation audit and cross-chain zero-knowledge quantum state bridges.

---

## 10. Conclusion
Quanthreum bridges the critical gap between upcoming quantum computational capabilities and real-world Web3 usability. By integrating Winternitz W-OTS+ hash-based signatures directly with EVM smart contracts, deflationary tokenomics, and enterprise dual-signature gateways, Quanthreum provides the premier mathematical shield for the next century of decentralized digital assets.
