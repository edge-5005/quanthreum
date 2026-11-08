// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Quanthreum (QTH) Token
 * @dev Quantum-Resistant & Ethereum Nature ERC-20 counterpart.
 * Total Supply: 100,000,000 QTH (Hard Cap).
 * Can be deployed 100% FOR FREE on Sepolia / BSC Testnet / Polygon Amoy.
 */

contract QuanthreumToken {
    string public name = "Quanthreum";
    string public symbol = "QTH";
    uint8 public decimals = 18;
    uint256 public constant TOTAL_MAX_SUPPLY = 100_000_000 * 10**18; // Exactly 100 Million QTH
    uint256 public totalSupply;

    address public owner;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // Quantum Proof of Stake (Q-PoS) Staking Registry
    mapping(address => uint256) public stakedValidators;
    uint256 public totalStaked;
    uint256 public totalBurnedFees; // EIP-1559 Burn Tracking

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event ValidatorStaked(address indexed validator, uint256 amount);
    event ValidatorUnstaked(address indexed validator, uint256 amount);
    event EIP1559Burned(uint256 amount);

    constructor() {
        owner = msg.sender;
        totalSupply = TOTAL_MAX_SUPPLY;
        balanceOf[msg.sender] = TOTAL_MAX_SUPPLY;
        emit Transfer(address(0), msg.sender, TOTAL_MAX_SUPPLY);
    }

    function transfer(address to, uint256 value) public returns (bool) {
        require(to != address(0), "Invalid recipient");
        require(balanceOf[msg.sender] >= value, "Insufficient balance");

        // Simulate 0.01% EIP-1559 deflationary fee burn
        uint256 burnFee = (value * 1) / 10000;
        uint256 sendAmount = value - burnFee;

        balanceOf[msg.sender] -= value;
        balanceOf[to] += sendAmount;

        if (burnFee > 0) {
            totalSupply -= burnFee;
            totalBurnedFees += burnFee;
            emit Transfer(msg.sender, address(0), burnFee);
            emit EIP1559Burned(burnFee);
        }

        emit Transfer(msg.sender, to, sendAmount);
        return true;
    }

    function approve(address spender, uint256 value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Allowance exceeded");

        balanceOf[from] -= value;
        allowance[from][msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
        return true;
    }

    /**
     * @dev Quantum Proof of Stake (Q-PoS) Validator deposit.
     */
    function stakeValidator(uint256 amount) public returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient QTH balance to stake");
        require(amount >= 10 * 10**18, "Minimum stake is 10 QTH");

        balanceOf[msg.sender] -= amount;
        stakedValidators[msg.sender] += amount;
        totalStaked += amount;

        emit ValidatorStaked(msg.sender, amount);
        return true;
    }

    /**
     * @dev Unstake validator QTH.
     */
    function unstakeValidator(uint256 amount) public returns (bool) {
        require(stakedValidators[msg.sender] >= amount, "Amount exceeds staked balance");

        stakedValidators[msg.sender] -= amount;
        totalStaked -= amount;
        balanceOf[msg.sender] += amount;

        emit ValidatorUnstaked(msg.sender, amount);
        return true;
    }
}
