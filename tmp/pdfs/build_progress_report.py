from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf/DKM_Project_Progress_From_Start_2026-10-11.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleDKM',fontName='Helvetica-Bold',fontSize=29,leading=34,textColor=colors.HexColor('#12304A'),spaceAfter=18))
styles.add(ParagraphStyle(name='SectionDKM',fontName='Helvetica-Bold',fontSize=19,leading=24,textColor=colors.HexColor('#12304A'),spaceAfter=15))
styles.add(ParagraphStyle(name='SubDKM',fontName='Helvetica-Bold',fontSize=11.5,leading=15,textColor=colors.HexColor('#117C83'),spaceBefore=12,spaceAfter=5))
styles.add(ParagraphStyle(name='BodyDKM',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=7))
styles.add(ParagraphStyle(name='SmallDKM',fontName='Helvetica',fontSize=8.4,leading=11,spaceAfter=4))
styles.add(ParagraphStyle(name='BulletDKM',parent=styles['BodyDKM'],leftIndent=11,firstLineIndent=-9,spaceAfter=6))
story=[]
def p(text,style='BodyDKM'):story.append(Paragraph(text,styles[style]))
def sub(text):p(text,'SubDKM')
def bullet(text):p('- '+text,'BulletDKM')
def page(num,title):
    if story:story.append(PageBreak())
    p(f'PROJECT RECORD / {num:02d}','SmallDKM');p(title,'SectionDKM')
def table(headers,rows,widths):
    data=[[Paragraph(str(c),styles['SmallDKM']) for c in row] for row in [headers]+rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DFEEF1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#117C83')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#DCE3E8'))]))
    story.append(t)

p('DKM / COLLEGE CAPSTONE','SubDKM')
p('Project progress<br/>from the start','TitleDKM')
p('Decentralized Knowledge Marketplace','SectionDKM')
p('Report date: 11 October 2026 | Local college demonstration')
story.append(Spacer(1,14))
sub('What this report covers')
p('A cumulative account of the work carried out in this collaboration: repository review, frontend and account access, marketplace and auction integration, protected knowledge files, Web2/Web3 payment engineering, research experiments, reliability checks and the current handoff. It separates the existing project foundation from changes added or hardened during the collaboration.')
sub('Current conclusion')
p('<b>A substantial implementation is complete and locally tested, but the entire project is not yet verified end to end.</b> The remaining gates include signed wallet journeys, completed hosted provider transactions, approved compatible contract deployment and full historical indexing. No universal cryptocurrency or fiat-conversion capability is claimed.')
table(['Evidence','Latest recorded result'],[
('Backend / frontend / contracts','68 backend tests; 12 frontend regressions; 128 contract tests passed.'),
('Additional checks','Six index/source follow-up tests passed. Frontend production build and contract typecheck passed.'),
('Browser verification','Welcome/signup, disposable-account login, dashboard, six APIs, direct Amoy positions and logout checked.'),
('Delivery','Existing PR #1 remains draft and unmerged. Latest recorded commit: 83e8ea2.'),
('Deployment and funds','No new public contract deployment or funds spending was performed in this continuation.')],[133,366])
sub('How to read the status')
p('<b>Implemented</b> means code exists. <b>Locally tested</b> means the stated test scope passed. <b>Provider verified</b> means an actual provider response was checked. <b>Interactive E2E verified</b> requires the full user journey, including signatures and settlement. These labels are not interchangeable.','SmallDKM')
p('Scope anchor: feature branch codex/dkm-payment-persistence; existing draft PR #1. This report records available repository and test evidence, not a production certification.','SmallDKM')

page(2,'Work history and milestones')
p('Milestones below follow repository history, from the existing foundation through the latest work. Grouped entries avoid treating every small commit as a separate feature.')
table(['Stage / reference','Work completed or advanced'],[
('Existing foundation\na2066bf and earlier','FastAPI/pgvector backend, Next.js interface, KnowledgeAsset, Marketplace, royalty splitting and initial contract integration already existed. This foundation was preserved.'),
('Durable payments\n9c58e61','Replaced fragile payment handling with database persistence, verified test captures, funded settlement source and marketplace/auction controls.'),
('Accounts and UI\n06b1222 - 195ad63','Added account authentication, connected backend features to UI, hid app navigation on auth screens, added Google login code and readable marketplace descriptions.'),
('Access and recovery\ne117c79 - 0cfd760','Hardened encrypted downloads, duplicate detection, reviews, search filtering and account boundaries; added reviewed payment recovery and production payment design notes.'),
('Welcome and checkout\n9d2c57a - 2110dd9','Added welcome-first flow, funding readiness, safer wallet checks, fee review and refreshed checkout preconditions.'),
('Legacy compatibility\n0c50cee','Preserved old-market entitlements and operations; verified canonical settlement receipts.'),
('Hosted provider flow\neb343cf - c2eb3d0','Added authenticated Transak staging sessions, saved verified BUY orders and seller payout preferences/SELL sandbox entry.'),
('Audit and capabilities\n6612caf - 1ef81aa','Added audit-registry source/tests, server-derived route availability and expiring account-bound fixed-price quotes.'),
('Required research\nb49d5f6','Implemented and benchmarked QAOA/VQC, published measured results in the app, and added durable BUY reconciliation.'),
('Latest engineering\nb871557','Added SELL verification/conflict audit, durable recording jobs, persistent indexing, accounting and direct account positions; reviewed compiler/security/recovery.'),
('Evidence and handoff\ne1360cf / 83e8ea2','Added demo runbook, final status, migration/security evidence and exact human actions; documented verified historical RPC restrictions.')],[137,362])
p('PR: <link href="https://github.com/parzival787/capstone-project/pull/1" color="#117C83">github.com/parzival787/capstone-project/pull/1</link>. Existing unrelated user edits were left outside these commits.','SmallDKM')

page(3,'Accounts, interface and knowledge files')
sub('Application entry and account isolation')
bullet('Organized navigation as Welcome -> Sign up / Log in -> authenticated workspace. Marketplace, auctions, search, creation, dashboard and service tools appear after authentication.')
bullet('Implemented password accounts with hashed passwords, revocable sessions, logout, origin/CSRF protection and authentication rate limiting. Signup/account data is stored in PostgreSQL, which runs locally in Docker.')
bullet('Added Google OAuth login code. The browser currently reports setup pending; Google configuration and interactive login are not claimed as complete.')
bullet('Bound wallets to accounts using signed challenges with expiry/replay protection. Account-specific uploads, payment histories and protected operations use the authenticated identity.')
sub('Content creation, privacy and recovery')
bullet('Connected the document analysis/upload/mint/link flow to the existing architecture. Preserved Pinata, BLAKE3, 384-dimensional embeddings and the working search pipeline.')
bullet('Implemented persistent duplicate-file detection and concurrent-insert protection. Failed uploads do not become false successful records.')
bullet('Encrypted new protected files with AES-GCM before IPFS upload; wrapped file keys remain server-side. Downloads recheck purchase entitlement, decrypt with integrity checks and use no-store responses.')
bullet('Added authenticated token-link verification and dashboard mint recovery. A linked token must match the upload and verified creator. The user can resume an unfinished mint or link a completed mint.')
bullet('Reworked asset descriptions to show useful knowledge information rather than presenting raw file identifiers/hashes as the main content. Technical chain references remain where needed for transaction verification.')
sub('Search, reviews and dashboard')
bullet('Connected search/filtering, including domain, price and minimum quality. Added purchaser reviews, self-review rejection, rating validation, duplicate/update handling and public aggregates.')
bullet('Dashboard now brings together uploads, licenses, listings, auctions/highest bids, refundable balances, orders, reviews, seller preference, verified payout history and audit status.')
p('<b>Limits:</b> Previously public IPFS content cannot become secret retroactively. Authorized downloads are not DRM. Password recovery is not configured. Rich coherence/completeness/originality scoring and review summarization are not implemented.','SmallDKM')

page(4,'Marketplace, auctions and contract safety')
sub('Ownership and access model')
p('The creator retains the KnowledgeAsset NFT. A marketplace purchase grants a license/access entitlement through Marketplace.hasPurchased; it does not transfer NFT ownership. Neither a mock payment, provider confirmation nor an audit-registry entry can unlock files by itself.')
sub('Fixed-price Web3 checkout')
bullet('Added or hardened listing/buyer/wallet validation, Amoy network checks, balance and allowance checks, purchase recovery, receipt verification and entitlement display.')
bullet('Persisted five-minute account-bound quotes using integer token units and contract rounding. The buyer sees gross asset price, seller-paid platform fee, royalties and seller net.')
bullet('Revalidate listing identity, price, active state, wallet, expiry and existing current/legacy access before approval and again before purchase. A stale or changed quote must be reviewed again.')
sub('Auction workflow')
bullet('Connected creation, bidding, countdown, finalization, winner access and outbid refund controls. Reads and writes retain the selected marketplace address, including old-market operations.')
bullet('Added persistent auction-related history and direct current positions. Bid deposits are not counted as completed seller revenue. Ended auctions remain discoverable rather than relying only on a cleared token-to-auction mapping.')
sub('Funded settlement and migration protection')
bullet('Implemented and locally tested buyAssetFor: a payer supplies the full token amount while the named buyer receives entitlement. Payer-scoped references and replay checks prevent duplicate settlement.')
bullet('Preserved KnowledgeAsset, existing purchases and configured legacy-market access. Added regression coverage for old downloads/reviews, duplicate purchase prevention, cancellation, finalization and refunds.')
bullet('Recorded a read-only migration inventory at Amoy block 49870192: five listings, zero auctions, and matching frontend/backend legacy configuration. Unknown historical buyers are not fully enumerated while indexing is incomplete.')
p('<b>Deployment boundary:</b> The current on-chain Marketplace does not acquire the new funded interface merely because local source compiles. A reviewed new Marketplace/splitter deployment and separate registry deployment require approval. Old splitter/market operations and entitlements must remain available.','BodyDKM')
p('<b>Remaining purchase risk:</b> The deployed buyAsset method does not atomically bind an accepted quote hash. Revalidation reduces stale-checkout risk but is not a listing reservation or an atomic expected-price guarantee.','SmallDKM')

page(5,'Web2, Web3 and provider payment work')
table(['Route','What is implemented','What is not proven'],[
('Direct Web3','MetaMask/Amoy checks, configured token purchase, on-chain receipt and entitlement verification.','Final signed seller/buyer/two-bidder acceptance.'),
('Razorpay test','Persistent INR test quote/order, signature checks, server-side captured-payment verification, settlement/recovery state.','Actual INR-to-USDC conversion; deployed funded checkout and full live-provider E2E.'),
('Transak BUY','Authenticated staging session, bound wallet/order checks, durable account history and reconciliation.','Completed hosted sandbox checkout; TRNSK becoming Amoy MockUSDC.'),
('Transak SELL','Currency preference, staging session, account references, server verification, history and conflict audit.','Completed bank payout or automatic conversion of each DKM sale.'),
('Other crypto / fiat','Explicit capability flags and disabled unavailable routes; provider alternatives investigated.','Universal cryptocurrency payment, arbitrary payout currencies, verified UPI or executable Amoy swap/bridge route.')],[90,211,198])
sub('Reliability and safeguards added')
bullet('Persisted order state, timestamps, provider identifiers and transaction hashes; serialized competing confirmation/settlement actions and made callbacks/retries repeat-safe.')
bullet('Required captured provider evidence with exact order, amount and currency. Authorized-but-not-captured payments remain pending; client redirects are not payment proof.')
bullet('Checkpoint signed settlement transactions before broadcast and reuse them after interruption. Verify transaction identity, confirmation depth, canonical block and entitlement independently.')
bullet('Added review holds and operator recovery for captured-but-unsettled payments. Full test refunds are verified server-side; signed transaction evidence is retained. Refund submission and listing reservations are not automated.')
bullet('Added BUY/SELL polling, duplicate evidence handling, outage recovery, terminal-regression and changed-amount conflict detection. SELL uses account references rather than incorrectly treating the provider deposit wallet as seller identity.')
sub('Fee policy retained')
p('The existing DKM platform cut is seller-paid from the gross asset fee (the configured 5% policy), with royalties also accounted for. A second DKM 5% is not added to the buyer. Provider/FX/bridge/gas charges are separate and must come from a supported quote; missing charges are not displayed as zero. No guaranteed all-in FX price is claimed.')

page(6,'Audit recording, indexing and accounting')
sub('PaymentReceiptRegistry integration')
p('Added a separate audit-evidence system, with contract source/tests and a backend recording layer. It is deliberately separate from money movement and asset access.')
bullet('Persist immutable normalized payment evidence and durable jobs, with buyer/seller/asset/token, payment and payout denominations, integer amounts and sandbox classification.')
bullet('Use provider-reference commitments and privately salted evidence hashes. Raw provider IDs, KYC, bank/card information, emails, keys and full provider payloads are not written to the public registry.')
bullet('Require a dedicated recorder signer; serialize nonce allocation and persist signed bytes before broadcast. Restart retries reuse the checkpoint rather than creating another payment.')
bullet('Verify the original payment remains canonical, then verify registry transaction target/sender/calldata, receipt, emitted event and stored payment hash. Conflicts or changed canonical evidence require review.')
bullet('Link full refunds/reversals to original evidence. The model supports terminal chargeback linkage, but automatic provider dispute ingestion and partial reversal processing are not implemented.')
bullet('Expose sanitized recording status to the buyer and verified seller. Recording is disabled until a separately approved registry deployment and recorder-role setup.')
sub('Persistent event history and exact proceeds')
bullet('Index current and configured legacy listings, purchases, cancellations, auction creation/bids/finalization/winners and refunds with durable checkpoints and idempotent database keys.')
bullet('Sort event ingestion, derive outbid information and preserve progress across restart. Changed canonical checkpoints hold affected history instead of presenting stale totals.')
bullet('Compute gross, platform fee, royalty amounts and seller net from historical payout events. Do not apply today\'s fee setting retroactively or count deposits as revenue.')
bullet('Expose indexed activity/accounting and independent paginated current licenses, seller listings, auction positions and refundable balances in the dashboard.')
p('<b>Coverage limitation:</b> Historical backfill remains incomplete. Current RPC page limits make millions of older blocks slow to scan. The retired Polygon public RPC failed DNS; the documented dRPC fallback rejected the historical request. Indexed-range totals are not lifetime earnings.','SmallDKM')

page(7,'Required research and security work')
sub('QAOA pricing - implemented and measured')
p('Implemented a genuine alternating cost/mixer circuit simulation with parameter optimization and seeded sampling. Evaluated 64 synthetic pricing cases using 7 qubits, depth 2 and 2,048 samples per case. Saved parameters, assumptions, outputs and a report; recommendations do not silently change seller prices.')
table(['Metric','Measured result'],[('Mean QAOA revenue gap from exact optimum','17.60%'),('Exact price matches','QAOA: 1 of 64; classical optimization: 64 of 64')],[280,219])
sub('VQC embeddings - implemented and measured')
p('Implemented training-only compression, a trainable quantum-circuit representation and classical expansion for comparison with the existing 384D embeddings. Used 64 training documents, 96 retrieval documents and 32 held-out queries in a controlled authored corpus.')
table(['Retrieval method','Test NDCG@10'],[('Original MiniLM','0.9053'),('PCA4 classical baseline','0.7027'),('Untrained circuit','0.6050'),('Trained VQC','0.6093')],[280,219])
p('Both required experiments are available through the authenticated Research page. Neither outperformed its principal classical baseline. These are simulator results on controlled data, not quantum-hardware execution or proof of quantum advantage. Existing production search is unchanged.','SmallDKM')
sub('Security, compiler and recovery evidence')
bullet('Reviewed session/origin/CORS protections, signature expiry/replay, authentication abuse, payment concurrency/idempotency, encryption, worker restart and error redaction.')
bullet('Reviewed compiler known bugs; tested Solidity 0.8.30 and 0.8.37, each with 128 passing contract tests. Adopted local 0.8.37 with Shanghai target. Existing deployed bytecode was not changed.')
bullet('Slither included the receipt registry: 0 high, 0 medium, 4 low timestamp findings and 1 informational pragma finding. Reviewed timestamp usage; this is not an independent audit.')
bullet('Completed a PostgreSQL restore drill in a disposable database: all 12 public tables matched by row counts/content digests. Removed the copy. Separate encryption-key custody and IPFS recovery were not proven by this drill.')

page(8,'Verification and remaining work')
table(['Evidence level','What can honestly be stated'],[
('Implemented','Core account/content/marketplace/auction code, payment persistence, BUY/SELL verification, registry backend, indexing/accounting, dashboards and required research.'),
('Locally tested','68 backend tests; 12 frontend regressions; 128 contract tests; production build and contract typecheck. Follow-up index/source suite: six passed, including two newer cases. These counts overlap and are not added together.'),
('Provider verified','Previously verified real Transak staging authentication and BUY/EUR SELL session creation only. Completed checkout/payout is not verified.'),
('Browser checked','Welcome/signup boundaries; disposable-account login/dashboard/logout; six APIs returned 200; direct Amoy positions resolved. Test account removed.'),
('Interactive E2E pending','Real signed mint/list/purchase/download/review, two-bidder auction/refund/finalization and hosted provider acceptance.'),
('Production-only deferred','Mainnet/hosting, live fiat onboarding/KYB, independent audit, managed signing/key custody and sustained production load validation.')],[124,375])
sub('What still needs to happen')
bullet('Run the human wallet and provider acceptance matrix; investigate and fix any defects revealed. Successful unit tests cannot replace those signed journeys.')
bullet('Approve and deploy compatible sandbox contracts only after migration review, then configure roles/signers and verify actual deployed wiring. No automatic deployment or spending is authorized.')
bullet('Obtain adequate historical RPC access, finish backfill and refresh inventory before claiming full-history coverage or signing off migration safety.')
bullet('Configure and exercise Google login if it is required for the presentation. Keep encryption keys backed up and rotate any previously exposed RPC credential safely.')
bullet('If actual multi-currency conversion is required, establish a supported provider/network/token route and verified quote/payout process. Current sandbox restrictions are unresolved, not a finished feature.')
p('<b>Engineering still owned by Codex:</b> validating saved configuration, running backfill/migrations/tests, checking deployment wiring after approval, verifying final integration and correcting acceptance failures. The owner is not being asked to code, manage database schemas or write tests.','SmallDKM')

page(9,'Your next steps and report references')
p('These are human/external actions. Detailed click-by-click acceptance is in DEMO_RUNBOOK.md; the exact action format is in HUMAN_ACTION_REQUIRED.md. Use only test funds and official sandbox details.')
table(['No.','Action','Evidence to return'],[
('1','Prepare seller S and buyers B1/B2 in separate browser profiles. Verify their MetaMask wallets on Amoy 80002.','Account labels and readiness; never passwords or keys.'),
('2','Seller uploads/analyzes/encrypts/mints/links and lists an asset. Buyer purchases, downloads and reviews.','Asset ID, PASS/FAIL per step, public transaction hashes.'),
('3','Use a separate auction asset: B1 bids, B2 outbids, B1 withdraws refund, then finalize after expiry.','Bid/refund/finalization hashes and winning-account access result.'),
('4','Complete supported Transak BUY/SELL sandbox steps. Verify saved order status in DKM; prove funding alone grants no asset access.','Selected route, safe order reference, status or sanitized provider limitation.'),
('5','Configure Google test users/callback locally if required. Back up the existing content key; save replacement RPC credentials locally if needed.','"Saved locally" and non-secret setup outcome. Do not overwrite the content key.'),
('6','Review the exact migration/deployment proposal before approving contracts or test-gas spending. Arrange historical RPC support if full coverage is required.','Explicit scoped approval, or provider/plan log limits and local configuration readiness.')],[33,297,169])
sub('Do not share')
p('Seed phrases, private keys, passwords, OTPs, API secrets, credential-bearing URLs, real card/bank details or KYC documents. The report intentionally includes no secrets.')
sub('Repository evidence used')
p('Current status and plan: PROJECT_CONTEXT.md, FINAL_STATUS.md, MASTER_TODO.md, ENGINEERING_PLAN.md and ROADMAP_STATUS.md.<br/>Validation: TEST_EVIDENCE.md, acceptance_results.json and restore_drill_evidence.json.<br/>Payments and safety: PAYMENT_RECORDING.md, LOCAL_PAYMENT_DEMO.md, MIGRATION_PLAN.md, migration_inventory.json and SECURITY_NOTES.md.<br/>Research: RESEARCH_PLAN.md and retained research_results artifacts.<br/>Owner handoff: HUMAN_ACTION_REQUIRED.md and DEMO_RUNBOOK.md. Git history anchors the milestone chronology.','SmallDKM')
p('Implementation/evidence commits: b871557, e1360cf, 83e8ea2. Latest known draft PR: <link href="https://github.com/parzival787/capstone-project/pull/1" color="#117C83">DKM PR #1</link>. Earlier project code is credited as the starting foundation; this report does not claim the entire original repository was created during this collaboration.','SmallDKM')
p('<b>Completion condition:</b> All agreed local-demo requirements must have implementation and appropriate acceptance evidence. Until then, the project remains partly verified and externally blocked, not fully complete.','SmallDKM')

def footer(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setStrokeColor(colors.HexColor('#DCE3E8'));canvas.line(48,45,w-48,45)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526574'))
    canvas.drawString(48,31,'DKM | Cumulative project progress | 11 October 2026')
    canvas.drawRightString(w-48,31,f'{doc.page} / 9');canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=43,bottomMargin=61,title='DKM - Cumulative Project Progress',author='DKM project collaboration')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
reader=PdfReader(OUT)
assert len(reader.pages)==9,f'Unexpected pagination: {len(reader.pages)}'
for i,page_obj in enumerate(reader.pages,1):
    text=page_obj.extract_text()
    assert text and f'{i} / 9' in text
print(f'Created {OUT} | {len(reader.pages)} pages')

