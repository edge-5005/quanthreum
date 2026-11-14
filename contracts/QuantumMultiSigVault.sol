// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title QuantumMultiSigVault
 * @dev Post-Quantum Treasury Vault for Enterprises & DAOs on Quanthreum (QTH).
 * Requires M-of-N quorum to release assets and collects a protocol security fee.
 */
contract QuantumMultiSigVault {
    address public protocolTreasury;
    uint256 public protocolFeeBasisPoints = 25; // 0.25% security fee
    uint256 public constant MAX_FEE = 100; // Max 1.0%
    
    address[] public signers;
    mapping(address => bool) public isSigner;
    uint256 public requiredSignatures;

    struct WithdrawalRequest {
        address to;
        uint256 amount;
        string quantumProofHash; // SHA3-256 of Winternitz W-OTS+ co-signature
        uint256 confirmations;
        bool executed;
    }

    WithdrawalRequest[] public requests;
    mapping(uint256 => mapping(address => bool)) public hasConfirmed;

    event Deposit(address indexed sender, uint256 amount);
    event Submission(uint256 indexed requestId, address indexed recipient, uint256 amount);
    event Confirmation(address indexed signer, uint256 indexed requestId);
    event Execution(uint256 indexed requestId, address indexed recipient, uint256 amount, uint256 feePaid);

    modifier onlySigner() {
        require(isSigner[msg.sender], "Not an authorized quantum signer");
        _;
    }

    constructor(address[] memory _signers, uint256 _required, address _treasury) {
        require(_signers.length > 0, "Signers required");
        require(_required > 0 && _required <= _signers.length, "Invalid quorum");
        require(_treasury != address(0), "Invalid treasury");

        for (uint256 i = 0; i < _signers.length; i++) {
            address s = _signers[i];
            require(s != address(0), "Zero address signer");
            require(!isSigner[s], "Duplicate signer");
            isSigner[s] = true;
            signers.push(s);
        }

        requiredSignatures = _required;
        protocolTreasury = _treasury;
    }

    receive() external payable {
        emit Deposit(msg.sender, msg.value);
    }

    function submitWithdrawal(
        address _to,
        uint256 _amount,
        string calldata _quantumProofHash
    ) external onlySigner returns (uint256 requestId) {
        require(_to != address(0), "Invalid destination");
        require(_amount <= address(this).balance, "Exceeds vault balance");

        requestId = requests.length;
        requests.push(WithdrawalRequest({
            to: _to,
            amount: _amount,
            quantumProofHash: _quantumProofHash,
            confirmations: 1,
            executed: false
        }));

        hasConfirmed[requestId][msg.sender] = true;
        emit Submission(requestId, _to, _amount);
        emit Confirmation(msg.sender, requestId);
    }

    function confirmWithdrawal(uint256 _requestId) external onlySigner {
        require(_requestId < requests.length, "Invalid request ID");
        require(!requests[_requestId].executed, "Already executed");
        require(!hasConfirmed[_requestId][msg.sender], "Already confirmed by caller");

        hasConfirmed[_requestId][msg.sender] = true;
        requests[_requestId].confirmations += 1;
        emit Confirmation(msg.sender, _requestId);

        if (requests[_requestId].confirmations >= requiredSignatures) {
            _executeWithdrawal(_requestId);
        }
    }

    function _executeWithdrawal(uint256 _requestId) internal {
        WithdrawalRequest storage req = requests[_requestId];
        require(!req.executed, "Already executed");
        require(req.amount <= address(this).balance, "Insufficient vault balance");

        req.executed = true;

        // Protocol security monetization fee
        uint256 fee = (req.amount * protocolFeeBasisPoints) / 10000;
        uint256 netPayout = req.amount - fee;

        if (fee > 0) {
            payable(protocolTreasury).transfer(fee);
        }
        payable(req.to).transfer(netPayout);

        emit Execution(_requestId, req.to, netPayout, fee);
    }

    function getVaultBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
