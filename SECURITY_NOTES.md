## TRNSK continuation checks — 2026-10-12

CONTENT_MASTER_KEY presence confirmed without revealing it. Settlement/recorder
keys are absent; workers disabled. Deployment requires distinct admin, settlement
and recorder public roles; existing runtime recorder separation guard remains.
Asset funding preserves prior verified delivery evidence on later conflict but
marks current verification unverified/review-required. A database unique delivery
transaction prevents reuse. BUY/SELL persist session attempts before provider
calls; uncertain attempts cannot silently create a duplicate session.
Canonical wrong-token/wallet/chain/hash/reverted/removed/malformed Transfer checks
and concurrent session checks pass. Local tests do not prove production capacity.
No Solidity source changed; previous Slither evidence remains unchanged. Existing
restore drill covers its original 12 tables, not a fresh drill of newly added
funding tables. Human content-key backup/RPC rotation and production audit/custody
remain separate. Review HUMAN_ACTION_REQUIRED.md before enabling signing.

# Local demo security evidence — 2026-10-11

This is an engineering review, not an independent security audit or production
approval. No public deployment or funds spending was performed.

## Compiler and static analysis

Solidity 0.8.30 and 0.8.37 each passed all 128 local Hardhat contract tests.
Adopted 0.8.37 for local builds with optimizer runs 200 and explicit Shanghai EVM
target. Existing deployed bytecode is unchanged. TypeScript checking passed.
The isolated compiler-review configuration preserves a reproducible comparison.

The official bug index lists seven issues for 0.8.20, including IR recursion,
memory-byte deletion, selector side effects and optimizer cases. Our source uses
the legacy pipeline, no custom optimizer sequence, no verbatim assembly, no
custom storage layout and no deletion of memory-byte elements. Those observations
are not a general proof of compiler safety; upgrading avoids the listed version
risks. The retrieved 0.8.37 entry has no listed bugs as of this review.

Sources: [official compiler bug list](https://docs.soliditylang.org/en/latest/bugs.html)
and [version index](https://github.com/argotorg/solidity/blob/develop/docs/bugs_by_version.json).

Slither on the rebuilt application (including PaymentReceiptRegistry): **0 high,
0 medium, 4 low timestamp findings, 1 informational pragma-range finding**.
The pragma still permits older compilers; the build configuration pins 0.8.37.
Slither's exit status reflects findings, not a clean audit.

Two timestamp findings concern the actual auction start/end comparisons. These
are intended chain-time boundaries, not randomness. Existing tests exercise bids
before start/at expiry and finalization timing. Do not advertise wall-clock exact
deadlines; pending bids can be mined after expiry. The listing findings follow
timestamp-tainted storage through existence/active checks; listing timestamps do
not decide price, identity or entitlement. No timestamp finding was emitted for
the receipt registry.

## Payments and workers

SELL observations require account-bound partner references from the authenticated
provider API. Browser redirects and provider deposit wallet addresses cannot
identify the seller. Unexpected terminal transitions and amounts are held.
Local conflict acceptance uses a compare-and-set evidence digest and records the
database-authenticated operator; wrong currency cannot be overridden.

The recorder is off by default, uses a separate signer and sandbox registry,
and persists signed bytes before broadcasting. It validates chain, target, sender,
calldata, value, canonical receipt, emitted evidence and registry state. Pending
or uncertain signed jobs block new nonce allocation. No receipt changes access.
On reorg the event indexer hides affected accounting and requires a derived-history
rebuild. This is fail-closed handling, not a claim of unlimited chain finality.

Provider/RPC worker errors are generic. Payment API exception text is no longer
returned verbatim. Provider payloads, signer keys, signed bytes and private salts
are excluded from public recording APIs. Credentials remain in ignored local
configuration. Production deployment still requires a restricted runtime database
role, separate operator login, external key custody and access-log redaction.

## Restore drill

Streamed pg_dump into a new disposable local database, then compared all 12 public
tables by row count and content digest: all matched. No row contents, credentials
or unencrypted dump file were printed/saved. Removed the disposable database.
See restore_drill_evidence.json. This verifies PostgreSQL restoration only;
independent CONTENT_MASTER_KEY custody and IPFS object recovery remain separate.

## Remaining acceptance boundaries

Signed wallet/provider interaction and a deployed registry are external gates.
Production-only work includes an independent audit, managed signer/key custody,
retention/monitoring policy and sustained production-scale load testing. The local
abuse/concurrency checks must not be presented as production capacity testing.
