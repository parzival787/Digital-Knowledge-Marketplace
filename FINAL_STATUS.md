# DKM status — engineering still in progress

This file is a current status record, not a completion declaration.

| Evidence level | Current state |
| --- | --- |
| IMPLEMENTED | Existing core marketplace/auth/content/auction flows; mandatory QAOA/VQC; BUY reconciliation; SELL account references/history/conflict audit; audit job persistence and recorder; confirmed event index; dashboard additions |
| LOCALLY TESTED | See TEST_EVIDENCE.md and acceptance_results.json; source-adapter, provider, recorder, indexer and contract tests cover simulated failure/concurrency boundaries |
| PROVIDER VERIFIED | Earlier Transak staging authentication and BUY/SELL session creation only; no completed SELL bank payout claimed |
| INTERACTIVE E2E VERIFIED | Final seller/buyer/two-bidder/provider acceptance not performed |
| HUMAN/EXTERNAL BLOCKED | Signed wallet interactions, provider-supported completed sandbox BUY/SELL, registry deployment approval and separate recorder custody |
| DEFERRED PRODUCTION-ONLY | Mainnet, hosting, independent audit, regulated live fiat route, managed signing/KYB and production-scale capacity |

Latest automated run passed 68 backend tests, 12 frontend tests, production build,
128 contract tests and contract typecheck. Welcome/signup were checked in-browser.
DEMO_RUNBOOK.md provides exact steps; HUMAN_ACTION_REQUIRED.md uses the requested
action format. Direct paginated positions now show current/legacy licenses,
seller listings, highest auction bids and refundable balances independently of
historical indexing.

The six-test index/source follow-up also passed, including both latest regressions.
The temporary approval-review quota is resolved. Signed-in dashboard and six APIs
were checked with a disposable account; direct Amoy positions resolved. Logout
restored the welcome screen, and the fixture account/sessions were removed.
Implementation milestone is committed as b871557 on the existing PR branch.
Documentation and evidence accompany it; PR #1 stays draft and unmerged.

External limits: completed Transak BUY/SELL evidence, Google setup, signed wallet
acceptance, approved registry/funded-market deployment, full historical RPC
backfill and migration sign-off. Chargeback linkage exists in the registry/job
model, but automatic provider dispute ingestion is unverified/unimplemented;
no arbitrary chargeback assertion can be submitted. Partial reversals unsupported.
The current bounded backfill must not be called lifetime history. No new provider
signup is requested, and no real fiat conversion or universal currency support is
claimed. The project is not yet complete.

QAOA/VQC are required and implemented; their honest underperformance against the
classical baselines remains documented. Production search is unchanged.
