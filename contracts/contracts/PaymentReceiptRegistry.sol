// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/// @notice Authorized payment attestations, not proof of bank settlement or asset entitlement.
contract PaymentReceiptRegistry is AccessControl {
    bytes32 public constant RECORDER_ROLE = keccak256("RECORDER_ROLE");
    bool public immutable sandbox;

    enum Status { None, Paid, Refunded, ChargedBack }

    struct Payment {
        address assetContract;
        uint256 tokenId;
        address buyer;
        address seller;
        bytes32 paymentCurrency;
        uint256 paymentAmount;
        bytes32 payoutCurrency;
        uint256 payoutAmount;
        bytes32 providerReference;
        bytes32 evidenceHash;
    }

    struct Record {
        bytes32 paymentHash;
        Status status;
    }

    mapping(bytes32 => Record) public records;
    mapping(bytes32 => bool) public recordedProviderReferences;

    event PaymentRecorded(bytes32 indexed paymentRef, address indexed buyer, address indexed seller,
        bytes32 paymentHash, Payment payment);
    event PaymentReversed(bytes32 indexed paymentRef, Status status, bytes32 evidenceHash);

    constructor(address recorder, bool isSandbox) {
        require(recorder != address(0), "Zero recorder");
        sandbox = isSandbox;
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(RECORDER_ROLE, recorder);
    }

    /// @dev Currency IDs commit to denomination, units, and chain/token where relevant.
    /// Use deterministic keyed provider commitments and salted evidence, never personal data.
    function recordPayment(bytes32 paymentRef, Payment calldata payment) external onlyRole(RECORDER_ROLE) {
        require(paymentRef != bytes32(0), "Empty reference");
        require(records[paymentRef].status == Status.None, "Already recorded");
        require(payment.assetContract != address(0) && payment.tokenId != 0, "Invalid asset");
        require(payment.buyer != address(0) && payment.seller != address(0)
            && payment.buyer != payment.seller, "Invalid parties");
        require(payment.paymentCurrency != bytes32(0) && payment.payoutCurrency != bytes32(0), "Invalid currency");
        require(payment.paymentAmount > 0 && payment.payoutAmount > 0, "Invalid amount");
        require(payment.providerReference != bytes32(0) && payment.evidenceHash != bytes32(0), "Missing evidence");
        require(!recordedProviderReferences[payment.providerReference], "Provider reference reused");

        bytes32 paymentHash = keccak256(abi.encode(payment));
        records[paymentRef] = Record(paymentHash, Status.Paid);
        recordedProviderReferences[payment.providerReference] = true;
        emit PaymentRecorded(paymentRef, payment.buyer, payment.seller, paymentHash, payment);
    }

    /// @notice Record a verified full refund or chargeback; original evidence stays immutable.
    function recordReversal(bytes32 paymentRef, Status status, bytes32 evidenceHash)
        external onlyRole(RECORDER_ROLE)
    {
        require(records[paymentRef].status == Status.Paid, "Payment not reversible");
        require(status == Status.Refunded || status == Status.ChargedBack, "Invalid reversal");
        require(evidenceHash != bytes32(0), "Missing evidence");
        records[paymentRef].status = status;
        emit PaymentReversed(paymentRef, status, evidenceHash);
    }
}
