# Local college demo — TRNSK sandbox

Run AFTER approved deployment, verified activation and test funding. These steps
are not yet evidence of completed interactive tests. Use only sandbox details.
Record step, PASS/FAIL, S/B1/B2 account label, asset ID and public transaction hash.
Never record passwords, private keys, KYC or bank/card details.

1. Open localhost:3000 in three separate browser profiles: seller S, buyers B1/B2.
   Welcome must show only login/signup. Create separate accounts, log in and verify
   each own MetaMask wallet on Polygon Amoy 80002. Cross-account actions must fail.
2. As S, open Create/Mint. Analyze a NEW harmless file, upload/encrypt, mint and link.
   Confirm it appears in search and marketplace with useful, non-secret metadata.
3. Review the USDC reference separately from the sandbox TRNSK listing price.
   Enter TRNSK amount, tick seller confirmation and sign listing on the NEW market.
4. As B1, open the listing and Fund this TRNSK purchase. Select an offered currency
   and method; click Get funding quote. Review total fiat, included provider fees,
   output and freshness. There is no additional 5% buyer fee. Accept and open
   Transak staging; use documented test details. Never use real money.
5. Return to DKM; enter provider order ID and Verify provider and blockchain
   delivery. COMPLETED alone is insufficient: require canonical TRNSK Transfer to
   B1. Missing evidence stays unverified. Wallet funded must NOT unlock the asset.
6. Review the separate purchase quote and seller deductions. Approve required
   TRNSK, then buy. Verify canonical receipt, hasPurchased(B1), S retained NFT
   ownership, 5% treasury deduction, separate royalties and exact seller net.
   B1 downloads/reviews; B2 is denied.
7. As S, dashboard payout settings: choose offered fiat preference, save, select
   this verified TRNSK sale and payout method, review quote, open SELL staging.
   Send only requested test tokens using documented test payout details.
   Verify the saved order. Provider status and outgoing chain verification must
   be shown separately. B1 access stays unchanged. Record unavailable routes
   honestly; do not claim real bank payout.
8. Mint a separate asset. Confirm TRNSK reserve and create auction. B1 approves/
   bids, B2 outbids, B1 withdraws refund on the same market. After expiry finalize.
   Verify B2 access, S retained NFT, exact payouts and public transaction hashes.
9. If Razorpay test is configured/required: use a separate listing, review INR
   test quote and test capture. Prefunded signer performs buyAssetFor using TRNSK.
   Verify one canonical settlement and beneficiary access; repeat verification
   must not spend twice. This is test-mode prefunded settlement, not real FX.
10. After recorder is separately approved/funded, inspect audit receipt against
    actual purchase amounts/token. Prove registry/funding alone cannot unlock
    access. No raw provider IDs, email, KYC or card/bank data may be on-chain.
11. Verify old-market purchased asset download/review. Old cancellation/refund/
    finalization must use original market. Token totals must remain separate.
12. Show /research and existing reports: QAOA 17.60% mean optimality gap;
    VQC NDCG@10 0.6093 versus MiniLM 0.9053 and PCA4 0.7027.
    Explain simulator/synthetic scope; do not claim quantum advantage.
13. Capture sanitized screenshots/public receipts and update FINAL_STATUS.md with
    observed results only. Leave unrun/failed items open.

Official staging mapping/test details:
https://docs.transak.com/guides/sandbox-credentials
The current lookup offered USD/EUR cards, not INR/UPI. Recheck the actual account,
IP and quote. UPI must remain unavailable unless explicitly offered at runtime.
