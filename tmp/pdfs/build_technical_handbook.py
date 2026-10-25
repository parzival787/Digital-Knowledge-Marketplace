"""Create a credential-free, source-indexed DKM handbook from the local snapshot."""
from pathlib import Path
from collections import Counter
import ast, re, json, subprocess, hashlib, textwrap, html
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Preformatted, Table, TableStyle, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/DKM_Complete_Technical_Handbook.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
DATE = '22 October 2026'
SKIP = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', '.next', '.pytest_cache', 'artifacts', 'cache', '.cache', 'dist', 'build'}
raw = subprocess.check_output(['rg', '--files', '--hidden'], cwd=ROOT, text=True).splitlines()
paths = []
excluded = Counter()
for name in raw:
    p = Path(name)
    if any(x in SKIP for x in p.parts):
        excluded['dependency/build/cache'] += 1; continue
    if p.parts[0] in ('tmp', 'output'):
        excluded['working/output artifacts'] += 1; continue
    if p.name.startswith('.env') or p.suffix.lower() in ('.pem', '.key', '.log', '.db', '.sqlite', '.sqlite3'):
        excluded['private/runtime files'] += 1; continue
    paths.append(p.as_posix())
paths = sorted(set(paths), key=str.lower)
assert 'backend/main.py' in paths and 'contracts/contracts/Marketplace.sol' in paths

def read(p):
    try: return (ROOT/p).read_text(encoding='utf-8-sig')
    except (UnicodeError, OSError): return ''

PURPOSE = {
'backend/main.py': 'FastAPI composition root: registers routers, starts database setup/workers, validates uploads, performs Pinata storage, search, access/download, recovery and provider-order endpoints. The central bridge between HTTP requests and services.',
'backend/services/auth.py': 'Password accounts with scrypt, hashed revocable cookie sessions, exact-origin checks, rate limiting, Google OAuth plumbing and signed wallet challenges. Account identity and wallet identity are separate until proof is verified.',
'backend/services/pgvector_client.py': 'PostgreSQL schema setup, compatible column migrations, asset persistence, duplicate protection, vector decoding and cosine candidate queries. Owns the knowledge_assets catalog and initial payment/review tables.',
'backend/services/quantum_hash.py': 'Classical BLAKE3 digest and integrity comparison. The historical quantum_hash name does not make the implementation a quantum algorithm.',
'backend/services/content_security.py': 'AES-256-GCM envelope encryption and decryption. Uses independent random nonces for document encryption and key wrapping, with the plaintext digest as associated authenticated data.',
'backend/services/embedding.py': 'Lazy local-cache loading of all-MiniLM-L6-v2; produces normalized 384-dimensional summary/query vectors. It does not call Ollama to produce embeddings.',
'backend/services/text_extractor.py': 'Converts supported uploaded formats into bounded text excerpts for analysis. Extraction is partial, not a complete document-understanding guarantee.',
'backend/services/llm_enrichment.py': 'Calls Ollama through the OpenAI-compatible client, validates structured metadata and four evidence-backed criteria, then computes quality on the server. Rejects fabricated or malformed support rather than manufacturing a fallback score.',
'backend/services/fraud_detector.py': 'Checks persisted BLAKE3 duplicates and files smaller than 100 bytes. Despite its class name, this is a classical rule-based screen, not learned fraud or plagiarism detection.',
'backend/services/quantum_search.py': 'Current cosine-candidate plus deterministic MMR search, with legacy graph propagation and annealing helpers retained separately. Production search does not call QAOA or VQC.',
'backend/services/blockchain.py': 'RPC contract reads and current/legacy registry and entitlement lookup. Keeps legacy access bounded to the preserved token prefix.',
'backend/services/mint_recovery.py': 'Finds already minted registrations for a saved upload and prevents an immediate blind retry when completion can be recovered. Uses creator/content matching and bounded scanning.',
'backend/services/asset_price.py': 'Validates exact decimal asset prices and rejects invalid precision/range instead of relying on binary floating-point money calculations.',
'backend/services/reviews.py': 'Review APIs bound to verified wallet/account and purchase entitlement; includes legacy entitlement compatibility.',
'backend/services/positions.py': 'Reads wallet-specific on-chain positions including owned assets, listings, auctions and refundable bids, preserving market/registry identity.',
'backend/services/activity.py': 'Builds sanitized account activity from available persisted/indexed records. Incomplete indexing cannot establish complete lifetime history.',
'backend/services/event_indexer.py': 'Persists chain-event sources, checkpoints and derived activity. Handles idempotency and chain consistency; source availability and backlog determine coverage.',
'backend/services/research_results.py': 'Authenticated API exposing retained experiment reports/results without executing quantum experiments on every request.',
'backend/services/payments/models.py': 'Typed payment methods, statuses and request/order models. Defines the vocabulary used by persistence and provider state transitions.',
'backend/services/payments/provider.py': 'Provider interface separating external payment operations from order orchestration.',
'backend/services/payments/mock_provider.py': 'Non-spending payment simulator for tests. Its confirmation must not become blockchain entitlement. Distinct from the real on-testnet MockERC20 contract.',
'backend/services/payments/razorpay_provider.py': 'Retained Razorpay test-mode creation/signature/status integration. Razorpay collection itself is not INR-to-USDC conversion.',
'backend/services/payments/service.py': 'Persists and transitions payment orders and coordinates providers; retains idempotency and confirmation/settlement separation.',
'backend/services/payments/settlement.py': 'Verifies configured chain/contract and performs controlled funded on-chain settlement, with receipt/state verification. A prefunded treasury is not currency exchange.',
'backend/services/payments/recovery.py': 'Operator reconciliation helpers for unsettled/captured orders, retries and refund-related state; execution can have external effects.',
'backend/services/payments/quotes.py': 'Builds purchase terms and validates buyer, market, token, amount and expiry. A quote is not an asset reservation or a payment receipt.',
'backend/services/payments/capabilities.py': 'Reads deployed market/token wiring and reports route availability. Fails closed when chain/profile verification is unavailable.',
'backend/services/payments/market_profiles.py': 'Reads token symbol/decimals and market wiring from deployed contracts rather than assuming every token called USDC is identical.',
'backend/services/payments/transak.py': 'Retained Transak staging order/session verification and durable workflow code. Not the current wallet-only UI payment route.',
'backend/services/payments/transak_discovery.py': 'Retained provider discovery and quote coverage lookup. Returned methods depend on the provider; no universal currency support is implied.',
'backend/services/payments/token_delivery.py': 'Checks actual canonical token delivery evidence separately from provider completion status.',
'backend/services/payments/asset_funding.py': 'Binds funding intent to asset/market/token context; funding alone must not grant access.',
'backend/services/payments/payouts.py': 'Retained seller payout preferences and order tracking; preferences do not themselves perform conversion or bank payment.',
'backend/services/payments/sale_payouts.py': 'Binds payout eligibility to verified canonical sales, correct seller, token and positive proceeds.',
'backend/services/payments/recording.py': 'Optional blockchain receipt recorder workflow with durable transaction management. Receipt logging is not a source of NFT access entitlement.',
'backend/services/payments/recording_sources.py': 'Validates external/provider/chain source evidence before an optional recording job may assert a receipt.',
'backend/research/run_embeddings.py': 'Constructs the authored corpus/query splits, runs comparable embedding methods and saves per-query metrics/artifacts.',
'backend/research/vqc_embeddings.py': 'PCA/angle preprocessing, variational quantum feature circuit, training and ridge reconstruction for the separate VQC benchmark.',
'backend/research/qaoa_pricing.py': 'Synthetic demand objective, diagonal QAOA cost/mixer circuit, sampled selection and classical/exact comparators.',
'backend/research/run_pricing.py': 'Executes the seeded synthetic pricing experiment and writes per-case data and report.',
'contracts/contracts/KnowledgeAsset.sol': 'ERC-721 knowledge registration: content/metadata CIDs, creator, price, license, quality and active status. Minting registers content; it is not an asset purchase.',
'contracts/contracts/KnowledgeAssetSuccessor.sol': 'Successor registry reads the fixed original prefix 1-6 and creates new tokens from 7 onward. Preserves original NFTs without copying their ownership.',
'contracts/contracts/Marketplace.sol': 'Fixed-price listings, entitlement purchases, funded purchases, auctions, bids, finalization and refunds. Payment token is immutable; buyAsset transfers ERC-20 tokens and grants access, not NFT ownership.',
'contracts/contracts/RoyaltySplitter.sol': 'Restricted marketplace caller distributes token proceeds to treasury, royalty recipients and seller with validated basis-point limits.',
'contracts/contracts/MockERC20.sol': 'Test ERC-20 with configured decimals and externally callable mint. Creates test currency; never treat its unrestricted issuance as a production stablecoin.',
'contracts/contracts/PaymentReceiptRegistry.sol': 'Optional restricted receipt-recording contract. Records evidence identifiers without replacing marketplace entitlement rules.',
'contracts/scripts/deploy-cents.mjs': 'Successor/market/splitter transition script and verification journal for the live one-cent Amoy deployment. Running it is a deployment action, not a harmless diagnostic.',
'contracts/scripts/deploy-trnsk-sandbox.ts': 'Historical alternative-token sandbox deployment path; does not describe the active MockUSDC market.',
'contracts/scripts/deploy.ts': 'Deployment entry point for the earlier contract suite; verify target network and existing-state preservation before running.',
'contracts/scripts/deploy-knowledge-asset.ts': 'Knowledge registry deployment utility; a new address does not migrate old entitlements automatically.',
'contracts/scripts/verify-deployment.ts': 'Checks deployed contract configuration and wiring against expected values.',
'contracts/scripts/check-balance.ts': 'Read-only native POL balance diagnostic for the configured signer; not an ERC-20 balance or faucet.',
'contracts/scripts/checkAsset.ts': 'Asset contract/state inspection utility.',
'contracts/scripts/checkCode.ts': 'Deployment bytecode-presence diagnostic; bytecode presence alone is not full configuration validation.',
'contracts/scripts/decode-error.ts': 'Contract error decoding helper for revert diagnostics.',
'contracts/scripts/send-op-tx.ts': 'Operational transaction helper. Review its exact payload and signer before running; not a generic read-only command.',
'frontend/app/layout.tsx': 'Root Next.js layout, global styling and providers; wraps page rendering.',
'frontend/app/page.tsx': 'Unauthenticated welcome entry point; app functions become available after authentication.',
'frontend/app/login/page.tsx': 'Login route using the shared authentication form.',
'frontend/app/signup/page.tsx': 'Account creation route using the shared authentication form.',
'frontend/app/dashboard/page.tsx': 'Account workspace, uploaded drafts, mint recovery and activity/positions entry points.',
'frontend/app/mint/page.tsx': 'File analysis/upload, price/license entry, wallet mint, receipt confirmation and upload/token linking. Resumes saved uploads and pending transaction hashes.',
'frontend/app/marketplace/page.tsx': 'Marketplace asset catalog and asset-card interactions.',
'frontend/app/auctions/page.tsx': 'Auction discovery and interaction page using market contracts.',
'frontend/app/search/page.tsx': 'Semantic query/filter UI and useful catalog results linking to published assets.',
'frontend/app/account/page.tsx': 'Account and wallet-related settings/view.',
'frontend/app/research/page.tsx': 'Explains QAOA/VQC and displays retained experiment results and limitations.',
'frontend/app/status/page.tsx': 'Service/capability diagnostics; healthy configuration is not proof of a completed purchase.',
'frontend/app/backend-test/page.tsx': 'Development API diagnostic page, not the normal customer workflow.',
'frontend/app/funding/page.tsx': 'Redirects directly to /marketplace. Historical provider funding UI is not the active purchase path.',
'frontend/providers/AuthProvider.tsx': 'Shared account/session state and authentication actions.',
'frontend/providers/Web3Provider.tsx': 'Wagmi/RainbowKit/query providers for wallet and chain interactions.',
'frontend/components/layout/AppShell.tsx': 'Session-aware navigation gate: welcome/login/signup before authentication; dashboard/workspace after authentication. Backend remains the actual authorization boundary.',
'frontend/components/layout/Navbar.tsx': 'Authenticated application navigation.',
'frontend/components/auth/AuthForm.tsx': 'Shared signup/login form and Google-method availability handling.',
'frontend/components/wallet/WalletButton.tsx': 'Wallet connection control; connection alone does not prove account-wallet ownership.',
'frontend/components/marketplace/AssetCard.tsx': 'Main asset interface: listing/cancel, quotes, token balance/allowance checks, purchase, access and download controls.',
'frontend/components/marketplace/AuctionPanel.tsx': 'Auction creation, bids, finalization and refund interactions with matching market/token.',
'frontend/components/marketplace/LegacyListing.tsx': 'Operations for previous-market positions, maintaining original contract identity.',
'frontend/components/marketplace/PurchaseQuoteSummary.tsx': 'Displays purchase total and seller deductions; keeps conversion/funding separate from asset purchase.',
'frontend/components/marketplace/PaymentCapabilities.tsx': 'Displays verified route availability and prevents unsupported payment promises.',
'frontend/components/marketplace/Positions.tsx': 'Wallet-specific positions and actions based on backend/on-chain reads.',
'frontend/components/marketplace/AccountActivity.tsx': 'Sanitized account history display.',
'frontend/components/marketplace/IndexedActivity.tsx': 'Indexed blockchain activity with coverage limitations.',
'frontend/components/marketplace/Reviews.tsx': 'Read/write review interface with backend entitlement enforcement.',
'frontend/components/marketplace/ReviewHistory.tsx': 'Account review history display.',
'frontend/components/marketplace/BlockchainTest.tsx': 'Development chain connection diagnostic component.',
'frontend/lib/blockchain/amoyFees.ts': 'Checks chain ID and computes EIP-1559 fee bounds with the observed 25-gwei priority floor.',
'frontend/lib/blockchain/purchaseSafety.ts': 'Shared listing/ownership/entitlement, receipt and gas preflight protections reused across wallet writes.',
'frontend/lib/blockchain/useMarketplace.ts': 'React hooks for market reads/writes and token approval; callers still need fresh state and receipt verification.',
'frontend/lib/blockchain/useKnowledgeAssets.ts': 'Registry read hooks for asset metadata, ownership and totals on Amoy.',
'frontend/lib/blockchain/contracts.ts': 'Typed contract address/ABI bindings for wallet/RPC operations.',
'frontend/lib/blockchain/wagmi.ts': 'Wallet connector and supported-chain configuration.',
'frontend/lib/blockchain/paymentToken.ts': 'Verified market token binding, decimal formatting and exact unit parsing.',
'frontend/lib/api/client.ts': 'Shared authenticated backend request handling and normalized errors.',
'frontend/lib/api/backend.ts': 'Typed backend request/response helpers for upload, search, download and other app operations.',
'frontend/lib/api/capabilities.ts': 'Polling query for chain-verified market profiles and route gating.',
'frontend/lib/api/quotes.ts': 'Validates accepted terms against buyer, chain, token, amount, asset and listing before signing.',
'frontend/contracts/addresses/index.ts': 'Current and legacy public contract addresses and registry identity helpers.',
'backend/acceptance.py': 'Runs consolidated acceptance commands and records outcomes; execution can require databases/services and should use isolated test state.',
'backend/check_restore.py': 'Database backup/restore verification helper; inspect disposable target controls before running.',
'backend/init_content_key.py': 'Generates/provisions backend encryption master-key material. Output is secret and must never be pasted into this handbook.',
'backend/check_demo_readiness.py': 'Checks configured dependencies and deployment readiness, not a substitute for interactive end-to-end purchase/download.',
'backend/migration_inventory.py': 'Snapshots old deployment/state for safe transition planning.',
'backend/sync_history.py': 'Backfills event history from chain with bounded/checkpointed progress.',
'backend/payment_recovery.py': 'Operator CLI for payment reconciliation; may change financial workflow state.',
'backend/payout_recovery.py': 'Operator CLI for seller payout reconciliation.',
'backend/operator_roles.sql': 'Database role/privilege setup for operational separation.',
'backend/verify_transak_token.py': 'Historical provider test-token chain verification, not verification of the current MockUSDC purchase.',
'backend/verify_transak_coverage.py': 'Historical staging route/quote discovery evidence capture; offers and quotes can expire.',
'PROJECT_CONTEXT.md': 'Chronological continuation record. Newer entries supersede older deployment/UI status; read newest first.',
'TEST_EVIDENCE.md': 'Recorded test and verification history, including failures and evidence boundaries. Counts belong to separate dated runs.',
'DEMO_RUNBOOK.md': 'Historical TRNSK/provider-oriented runbook. Superseded for current wallet-only MockUSDC flow; do not follow its provider steps as current instructions.',
'contracts/cents-deployment.json': 'Current Amoy successor deployment receipts, original-state snapshot and wiring verification.',
'contracts/deployment.json': 'Earlier deployment record; compare with the current cents manifest before using addresses.',
'research_results/vqc_embeddings.json': 'Retained VQC corpus/split/configuration, per-query rankings, metrics, versions and training trace.',
'research_results/qaoa_pricing.json': 'Retained QAOA per-case outcomes, configuration, objective gaps, runtimes and simulator provenance.',
'research_results/vqc_model.npz': 'Fitted VQC/PCA/decoder arrays; binary experiment artifact, not a production search model.',
'acceptance_results.json': 'Saved consolidated command outcomes from a past acceptance run; not a fresh test execution for this handbook.',
'SLITHER_AUDIT.json': 'Saved static-analysis findings. Source analysis is not an independent audit or proof that every deployed bytecode version was analyzed.',
'restore_drill_evidence.json': 'Saved local database restore comparison; external IPFS and independent key-backup recovery were not tested.',
}

def purpose(p, text):
    if p in PURPOSE: return PURPOSE[p]
    name=Path(p).name; stem=Path(p).stem
    if p.startswith('contracts /'): return 'Legacy/scaffold duplicate under a directory whose name ends in a space. Do not confuse this with the active contracts/ project. ' + ('Counter demonstration code.' if 'Counter' in p else 'Inspect before use; not the current deployment entry point.')
    if '/.agents/' in p or '/.claude/' in p or name in ('AGENTS.md','CLAUDE.md'): return 'Developer/agent workflow instructions and tooling guidance; not executed as an application feature.'
    if '/tests/' in p or '/test/' in p or name.startswith('test_'): return 'Test or diagnostic coverage for ' + stem.replace('test_','').replace('.test','').replace('_',' ') + '. The extracted cases below describe intended checks; file presence alone does not prove that they passed.'
    if '/interfaces/' in p: return 'Solidity interface defining the cross-contract callable surface and shared types; implementation lives in the corresponding contract.'
    if '/components/ui/' in p: return 'Reusable '+stem+' UI primitive. Supplies presentation/interaction behavior, not payment or authorization policy.'
    if '/abi/' in p or 'abi' in name.lower(): return 'Contract ABI/interface data used to encode calls and decode outputs/events. An ABI is not a deployment or evidence of a successful transaction.'
    if name in ('package-lock.json','pnpm-lock.yaml'): return 'Dependency lockfile: exact resolved dependency graph and integrity metadata. Used for reproducible installation; not application business logic.'
    if name=='package.json': return 'Node package manifest: scripts and direct dependencies. Version ranges are not necessarily the versions resolved in the lockfile.'
    if name.startswith('requirements'): return 'Python dependency constraints for '+('research simulation' if 'research' in name else 'backend runtime')+'. Installed versions and saved benchmark versions may differ.'
    if name=='__init__.py': return 'Python package initializer; may be intentionally empty.'
    if name.endswith('.md'): return 'Project documentation for '+stem.replace('_',' ').replace('-',' ')+'. Treat dated plans and old status notes as historical unless confirmed by current code/deployment.'
    if name.endswith('.json'): return 'Structured '+stem.replace('_',' ').replace('-',' ')+' configuration/evidence. Top-level structure is listed below; its existence alone is not live-state proof.'
    if name.endswith(('.woff','.ico','.png','.svg')): return 'Static visual/font asset, consumed by frontend rendering; no executable business logic.'
    if 'config' in name or name.endswith(('.yaml','.yml')): return 'Build/runtime/tooling configuration for '+stem+'. Review this alongside its package manifest; secrets are deliberately excluded.'
    if name.startswith('.'): return 'Repository/tooling metadata controlling ignores, linting or project behavior; not user-facing application logic.'
    if name.endswith('.css'): return 'Shared style definitions and visual tokens for the application.'
    if 'Counter' in p: return 'Hardhat starter counter example/scaffold, not the DKM marketplace implementation.'
    if name.endswith('.txt'): return 'Auxiliary text file; inspect its actual content before treating it as an executable project entry point.'
    return 'Supporting '+stem.replace('_',' ').replace('-',' ')+' module. Its directly extracted symbols and references below identify its concrete scope.'

records=[]; all_routes=[]; tables={}; envrefs={}
for p in paths:
    text=read(p); suffix=Path(p).suffix.lower(); symbols=[]; tests=[]; routes=[]; imports=[]
    if suffix=='.py' and text:
        try:
            tree=ast.parse(text)
            def walk(nodes, prefix=''):
                for n in nodes:
                    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                        label=prefix+n.name
                        symbols.append((label,n.lineno))
                        if n.name.startswith('test_'): tests.append(label)
                        if isinstance(n,ast.ClassDef): walk(n.body,label+'.')
                    if isinstance(n,(ast.Import,ast.ImportFrom)):
                        if isinstance(n,ast.ImportFrom): imports.append(n.module or '.')
                        else: imports.extend(x.name for x in n.names)
            walk(tree.body)
        except SyntaxError: pass
        prefixmatch=re.search(r'APIRouter\([^\n]*prefix=["\']([^"\']+)',text)
        prefix=prefixmatch.group(1) if prefixmatch else ''
        for m in re.finditer(r'@(app|router)\.(get|post|put|patch|delete)\(["\']([^"\']*)["\']',text):
            endpoint=(prefix if m.group(1)=='router' else '')+m.group(3)
            routes.append(m.group(2).upper()+' '+endpoint)
            all_routes.append((m.group(2).upper(),endpoint,p,text[:m.start()].count('\n')+1))
    elif suffix in ('.ts','.tsx','.js','.mjs','.sol'):
        declarations=re.sub(r'/\*[\s\S]*?\*/|//[^\n]*',lambda m: '\n'*m.group(0).count('\n'),text)
        for m in re.finditer(r'\b(?:function|class|interface|contract|library)\s+([A-Za-z_$][\w$]*)',declarations):
            symbols.append((m.group(1),declarations[:m.start()].count('\n')+1))
        for m in re.finditer(r'\b(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(',declarations):
            symbols.append((m.group(1),declarations[:m.start()].count('\n')+1))
        tests=re.findall(r'\b(?:it|test)\s*\(\s*["\']([^"\'\n]+)',text)
        imports=re.findall(r'\bfrom\s+["\']([^"\']+)',text)
    for m in re.finditer(r'CREATE TABLE IF NOT EXISTS\s+([a-zA-Z_][a-zA-Z_0-9]*)',text,re.I): tables.setdefault(m.group(1),set()).add(p)
    # Names only; never values or defaults.
    for key in re.findall(r'(?:getenv|environ\.get)\(\s*["\']([A-Z][A-Z0-9_]+)',text)+re.findall(r'(?:process\.env\.|environ\[["\'])([A-Z][A-Z0-9_]+)',text): envrefs.setdefault(key,set()).add(p)
    records.append(dict(path=p,text=text,purpose=purpose(p,text),symbols=list(dict.fromkeys(symbols)),tests=tests,routes=routes,imports=list(dict.fromkeys(imports)),lines=len(text.splitlines()),size=(ROOT/p).stat().st_size))

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=9.3,leading=13.8,spaceAfter=7,textColor=colors.HexColor('#203047')))
styles.add(ParagraphStyle(name='SmallBody',parent=styles['Body'],fontSize=8,leading=11,spaceAfter=5))
styles.add(ParagraphStyle(name='File',fontName='Helvetica-Bold',fontSize=10,leading=14,spaceBefore=13,spaceAfter=5,textColor=colors.HexColor('#126a78'),keepWithNext=True,splitLongWords=True))
styles.add(ParagraphStyle(name='Chapter',fontName='Helvetica-Bold',fontSize=21,leading=26,spaceAfter=16,textColor=colors.HexColor('#12394a')))
styles.add(ParagraphStyle(name='Cover',parent=styles['Chapter']))
styles.add(ParagraphStyle(name='Section',fontName='Helvetica-Bold',fontSize=12,leading=16,spaceBefore=12,spaceAfter=7,textColor=colors.HexColor('#12394a'),keepWithNext=True))
styles.add(ParagraphStyle(name='CodeBlock',fontName='Courier',fontSize=7.2,leading=10,spaceBefore=4,spaceAfter=10,backColor=colors.HexColor('#edf3f6'),borderPadding=7))
story=[]
def clean(s): return str(s).replace('\u2014',' - ').replace('\u2013','-').replace('\u2019',"'").replace('\u2192',' -> ').replace('\u00d7',' x ').replace('\u2260',' != ').replace('\u2264',' <= ').replace('\u2265',' >= ')
def para(s,style='Body'): story.append(Paragraph(html.escape(clean(s)).replace('\n','<br/>'),styles[style]))
def section(t): para(t,'Section')
def chapter(t):
    if story: story.append(PageBreak())
    para(t,'Chapter')
def code(s):
    lines=[]
    for line in clean(s).splitlines(): lines.extend(textwrap.wrap(line,95,replace_whitespace=False,drop_whitespace=False) or [''])
    # Separate blocks keep long code excerpts splittable.
    for start in range(0,len(lines),35): story.append(Preformatted('\n'.join(lines[start:start+35]),styles['CodeBlock']))
def bullets(items):
    for item in items: para('- '+item)
def table(rows,widths=None):
    cells=[[Paragraph(html.escape(clean(v)),styles['SmallBody']) for v in row] for row in rows]
    t=Table(cells,colWidths=widths or [475/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe9ee')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#6c98a5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f8')])]))
    story.extend([t,Spacer(1,10)])

class Handbook(BaseDocTemplate):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.counter=0
    def beforeDocument(self): self.counter=0
    def afterFlowable(self,flow):
        if isinstance(flow,Paragraph) and flow.style.name=='Chapter':
            text=flow.getPlainText();key='chapter'+str(self.counter);self.counter+=1
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,0)
            self.notify('TOCEntry',(0,text,self.page,key))

para('DKM','Cover');para('COMPLETE TECHNICAL HANDBOOK','Cover')
para('Architecture, source-file atlas, algorithms, contract flows, security boundaries and verification evidence','Section')
para('Decentralized Knowledge Marketplace | Local college demonstration | Polygon Amoy')
para('Snapshot date: '+DATE)
para(f'{len(paths)} repository files inventoried; {len(all_routes)} HTTP route declarations extracted; {len(tables)} database table names identified from schema creation code.')
para('Prepared from the current working tree, retained experiment artifacts and recorded engineering evidence. This is a technical explanation and source map, not a claim that all code has been independently audited or all features executed live.')
section('How to use this handbook')
bullets(['Read Chapters 1-12 for the complete system story and evidence boundaries.', 'Use the route, schema and configuration catalogs to trace data across layers.', 'Use the file atlas for each file\'s role, code entry points with line numbers, dependencies and test cases.', 'Use the code excerpts and runbook to connect conceptual explanations to the implementation.'])
para('Credentials, private keys, environment values, database dumps, installed third-party package source, generated build/cache trees and transient logs are not reproduced. Source line numbers refer to this snapshot. Environment variable names are documented without values.')
chapter('Contents')
toc=TableOfContents();toc.levelStyles=[ParagraphStyle(name='TOC',fontName='Helvetica',fontSize=10,leading=16,spaceBefore=4,leftIndent=0,firstLineIndent=0)]
story.append(toc)

chapter('1. System purpose and architectural boundaries')
para('DKM connects user accounts, wallet-verified identity, knowledge-document registration, searchable descriptions and licensed access to encrypted content. It runs a local Next.js frontend and FastAPI backend, with PostgreSQL/pgvector and Ollama services, Pinata-hosted IPFS data, and public Polygon Amoy contracts.')
code('Browser / MetaMask\n  |-- Next.js pages, wallet transactions, query cache\n  |-- FastAPI: sessions, metadata, uploads, search, access checks\n        |-- PostgreSQL + pgvector: catalog, accounts, vectors, wrapped keys\n        |-- Ollama: structured excerpt assessment / descriptions\n        |-- MiniLM: normalized 384D embeddings\n        |-- Pinata / IPFS: encrypted document + public metadata\n        |-- Amoy RPC: registry, market, entitlements, receipts\n\nSeparate research path: PennyLane simulator -> QAOA/VQC results -> /research')
para('A blockchain makes relevant contract state inspectable; it does not decentralize the local application server, its database or its master decryption key. An NFT registration is not proof of legal copyright, truth or scientific quality. In the current marketplace, a purchase grants access entitlement while the creator retains NFT ownership.')
table([['Layer','Responsibility','Trust / failure boundary'],['Frontend','Input, catalog display, wallet signing','Browser state is untrusted; UI hiding is not authorization'],['Backend','Validation, identity, storage, access and orchestration','Trusted with plaintext and decryption material'],['Database','Account/catalog/workflow state and vectors','Must preserve wrapped keys, ownership links and backups'],['IPFS / Pinata','Content-addressed encrypted storage','Pinning/gateway availability is not guaranteed permanence'],['Amoy contracts','Registration, settlement and entitlement state','Testnet gas/tokens; deployed code differs from local source'],['Research','Controlled comparative experiments','Simulated circuits, synthetic/authored data; no advantage claim']],[75,190,210])
section('Active versus retained scope')
para('The current customer UI is wallet-only. Transak, Razorpay, payout and receipt-recorder modules remain in the repository for historical work and optional future integration. Their existence does not mean those provider routes are enabled, funded, live or production-ready. Older TRNSK demo documents are superseded for the active MockUSDC purchase path.')

chapter('2. Technology stack and why each part exists')
table([['Technology','Use in DKM'],['Python / FastAPI / Uvicorn','HTTP APIs, typed validation, async I/O and service lifecycle'],['Pydantic / httpx / asyncpg','Boundary schemas, outbound HTTP and PostgreSQL access'],['PostgreSQL + pgvector','Durable relational state and cosine vector candidate search'],['Next.js 14.2.35 / React 18 / TypeScript','Page routing and typed interactive frontend'],['Tailwind / reusable UI primitives / Lucide','Styling, accessible interaction primitives and icons'],['Wagmi / RainbowKit / viem','Wallet connection, chain-aware reads/writes, gas and receipt handling'],['Solidity / OpenZeppelin / Hardhat','Contract implementation, standard tokens/access guards and local tests'],['Ethers / Web3.py','Deployment/operational scripts and backend RPC reads'],['BLAKE3','Plaintext fingerprint and exact-byte integrity checks'],['cryptography AESGCM','Authenticated content encryption and key wrapping'],['Pinata / IPFS','Storage upload and retrieval of content-addressed objects'],['Ollama + OpenAI-compatible SDK','Local structured metadata and rubric scoring; SDK use does not imply OpenAI-hosted inference'],['Sentence Transformers / MiniLM','384D normalized semantic embeddings'],['NumPy / SciPy / scikit-learn','Vector math, optimization, PCA and ridge reconstruction'],['PennyLane','QAOA and VQC circuit simulation for experiments'],['NetworkX / dimod','Retained legacy graph/annealing helpers, inactive in production retrieval']],[160,315])
para('Version evidence has different meanings: requirements files pin intended backend dependencies, package manifests may contain ranges, lockfiles resolve Node dependencies, and experiment JSON records the environment of a particular run. For example, current backend requirements pin NumPy 2.4.6 while retained VQC evidence records NumPy 2.5.1. Do not collapse these into one asserted runtime version.')

chapter('3. Accounts, signup, login and wallet identity')
para('The welcome page leads to login/signup. AppShell waits for the session before mounting protected application pages, and redirects authenticated users to the dashboard. API authorization is enforced independently on the backend. Signup data is stored in PostgreSQL app_users; if PostgreSQL runs in Docker, Docker hosts the database service, while persistence depends on its configured volume. Blockchain and Pinata are not the signup database.')
para('Passwords use salted scrypt (n=2^17, r=8, p=1). The stored value contains a salt and derived key, not the plaintext password. A semaphore limits concurrent expensive password hashing per worker. Session cookies carry tokens whose SHA-256 digests are stored in app_sessions with expiry. HTTPS selects secure __Host- cookies; localhost uses the development cookie name. Exact Origin and X-DKM-Request checks protect state-changing account requests.')
para('Wallet connection and wallet verification are different. MetaMask connection exposes an address; the backend challenge/signature flow proves control and binds a wallet to the logged-in account. Expiry and consumed challenges mitigate replay. Account-scoped uploads, recovery and reviews must not accept another user\'s identifiers simply because the browser submitted them.')
para('Google OAuth plumbing exists, including state/PKCE-related persisted flows. Its availability depends on correct provider configuration; the historical checks recorded setup pending. This handbook does not certify a successful live Google login.')

chapter('4. Upload, analysis, storage and NFT minting')
bullets(['1. The authenticated user chooses a supported document and requests analysis.', '2. The backend reads bounded bytes and extracts an excerpt. It calls Ollama for descriptions and the rubric.', '3. Upload re-analyzes the actual bytes server-side; browser-supplied quality cannot replace the server assessment.', '4. The quality threshold is checked; the summary is embedded and exact duplicate/tiny-file checks run.', '5. A BLAKE3 plaintext digest is computed, a random content key encrypts the file, and the master key wraps that content key.', '6. Pinata receives encrypted content and public metadata. Their CIDs and protected catalog fields are persisted in PostgreSQL.', '7. MetaMask signs KnowledgeAsset mint with CIDs, price, license and quality. This costs test POL gas, not the asset purchase price.', '8. The frontend waits for a confirmed receipt, then the backend validates creator/CIDs/price and links the saved upload to the token.'])
para('The current minimum is 0.01 USDC = 10,000 base units of the six-decimal test token. Pricing is user-selected, not an LLM market valuation. Contract storage also carries license and active state; an inactive asset is not eligible for ordinary content access.')
section('Why a file can exist on Pinata before minting succeeds')
para('IPFS upload and wallet minting are separate operations. Rejecting or failing the wallet transaction does not undo an already completed upload. The dashboard preserves the draft and offers resume without requiring a mysterious code. A token ID exists only after a successful mint; manual linking is an advanced recovery option. Pending hashes are kept per upload/registry in browser storage. Matching completed mints are checked before another attempt, and backend recovery is account/wallet scoped. Automatic scanning is bounded to 100 tokens; cross-device concurrent requests are not a global exactly-once protocol.')

chapter('5. BLAKE3 hashing and encryption in detail')
para('quantum_hash(data) calls blake3.blake3(data).hexdigest(). With the default output it produces a 32-byte digest rendered as 64 hexadecimal characters. It is deterministic for the same bytes. Changing a file\'s formatting or metadata can change its digest even when the document looks similar. It is a classical cryptographic hash, not encryption and not a quantum circuit.')
para('The digest is used for exact duplicate lookup, stored as blake3_hash, and bound into AES-GCM associated authenticated data. On protected download, the server decrypts and recomputes BLAKE3; a mismatch rejects the content. This does not detect paraphrased plagiarism, establish authorship or guarantee that uploaded scientific claims are true.')
section('Envelope encryption')
bullets(['A fresh 256-bit random data key is generated for each upload.', 'A fresh 12-byte nonce encrypts the plaintext with AES-GCM. Stored ciphertext is nonce || encrypted bytes/tag.', 'A separate random 12-byte nonce wraps the data key under the 32-byte backend master key. The wrapped envelope is base64-encoded for database storage.', 'Both operations authenticate the ASCII content digest as associated data, binding ciphertext and wrapped key to the expected content identity.', 'The master key is not stored in public IPFS metadata or frontend code. Losing it prevents decryption of protected content; compromising it threatens all wrapped keys accessible to the attacker.'])
para('AES-GCM provides authentication under correct nonce/key use. The application additionally checks the plaintext digest. Neither mechanism prevents an authorized recipient from redistributing downloaded plaintext. Older unencrypted IPFS assets remain publicly retrievable to anyone who has their CID; they are not retroactively made confidential.')

chapter('6. IPFS, Pinata and the database')
para('Pinata is the upload/pinning service used by backend/main.py through its files API. The encrypted document is stored as one object, public catalog metadata as another. IPFS addresses objects by content-derived identifiers; the encrypted-object CID is different from the plaintext BLAKE3 fingerprint. Encryption randomness means repeated encryption can produce a different CID for identical plaintext.')
para('The database connects account ownership, vector ID, token ID, file CID, metadata CID, title/domain/tags/summary, quality, exact price, embedding, plaintext hash, original filename and wrapped content key. Public metadata must not contain the key or private assessment excerpts. The browser receives useful catalog fields rather than raw internal storage details.')
para('On download, the backend checks current entitlement or creator access and active state, matches the on-chain CIDs to a protected database row, retrieves bounded ciphertext through configured gateways, decrypts and verifies it, and returns a no-store attachment with a sanitized filename. Gateway failures or authentication/integrity failures do not become successful downloads.')
section('Backup boundary')
para('The retained restore drill checked local PostgreSQL table counts and digests after restoration. It did not prove external IPFS recovery or independent master-key restoration. A complete recovery plan needs database + key backup + durable content availability + deployment references. Never publish any backup containing credentials or user records.')

chapter('7. Ollama scoring and semantic retrieval')
para('The default scoring model is llama3.2:3b via Ollama\'s OpenAI-compatible endpoint. Structured output uses temperature 0 and seed 31. Criteria are clarity, specificity, completeness and evidence, each an integer 0-4. Backend quality is their sum divided by 16; the acceptance threshold is 0.4. Positive criterion scores require supporting excerpt quotations, and invalid output is rejected rather than assigned invented quality.')
para('Extraction is capped at 4,000 characters, with format-specific bounds such as five PDF pages or 51 CSV lines. Consequently, quality describes the available excerpt, not an exhaustive peer review. A quotation matching the excerpt does not prove that the assessment is justified. Two retained sanity examples scored 0.5625 (detailed, repeated) and 0.125 (vague); this is illustrative, not calibrated accuracy or deterministic behavior across all environments.')
section('Embedding and search path')
para('MiniLM is loaded lazily from the local cache. model.encode(..., normalize_embeddings=True) produces a 384D vector. Upload indexing uses the generated summary; query embedding uses the same encoder. pgvector stores VECTOR(384), with an IVFFlat cosine index and metadata filters. Candidate retrieval requests up to 60 published linked assets; deduplication excludes repeated content/token identities and drafts without useful token links.')
code('For candidate d and already selected results S:\nMMR(d) = 0.85 * cosine(query, d)\n         - 0.15 * max(0, max cosine(d, s) for s in S)\n\nChoose the largest MMR repeatedly, up to 10 results.\nFirst result uses redundancy = 0.\nStable initial ordering uses descending query score and vector_id.')
para('This is classical maximum marginal relevance. It reduces redundant results while retaining relevance; it is not a guarantee that every returned document is useful. The score is not a percentage probability. Legacy graph/quantum_walk_discover/QUBO helpers are retained but inactive in the production route. The old propagation is not unitary quantum evolution, and its annealing solver is classical.')

chapter('8. Contracts, listings, purchases and auctions')
table([['Contract','Primary role'],['KnowledgeAsset','ERC-721 registration and mutable asset metadata/state within contract rules'],['KnowledgeAssetSuccessor','Read-through legacy prefix plus new registrations at a lower minimum'],['Marketplace','Listings, access purchases, funded settlement, auctions and refunds'],['RoyaltySplitter','Treasury fee, configured royalties and seller remainder'],['MockERC20','Unrestricted test-token mint and ERC-20 balances/allowances'],['PaymentReceiptRegistry','Optional audit receipt recording, not access entitlement']],[155,320])
para('A listing checks ownership and the required approvals and records sale terms. Fixed-price buyAsset validates the listing is active and fixed-price, rejects a seller buying their own listing, and checks the seller still owns the NFT. It deactivates the listing and increments the buyer\'s purchase count, then transfers the ERC-20 price to RoyaltySplitter and distributes it. All effects revert if token transfer/distribution fails. PurchaseCompleted records the sale. The NFT is not transferred by this purchase path.')
para('Auctions add reserve/start/end constraints, bids, outbid refund accounting, settlement and cancellation/finalization rules. Time-based eligibility requires block-time comparisons and careful expiry tests. Refund withdrawals are distinct transactions. A frontend button is not proof that any particular live auction has completed.')
section('Current deployment and legacy compatibility')
table([['Component','Current Amoy address'],['KnowledgeAssetSuccessor','0xCA6f1E6C08Dddda08e4288B8eFE07bF54f67AeD7'],['Marketplace','0xc1cfA63fDA41cD1Ee76B24F1D1B2b993661a67A5'],['RoyaltySplitter','0x36CAa5b59825a378664E75b5EFB30988F71901c0'],['MockUSDC','0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719']],[150,325])
para('Original registry: 0x2C16409A3db9880f9A70e71B5b131A17db533Fc9. Previous marketplace: 0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d. Previous splitter: 0x43cE72CEd667bDe9252044451b07ecA1aec2D300. Existing IDs 1-6 are read from the original registry; new NFTs start at 7. Entitlement lookups only consult legacy markets for that fixed prefix, preventing future legacy ID collisions from granting access to a new-registry asset.')
para('Source was compiled with Solidity 0.8.37, optimizer runs 200 and Shanghai target for the successor transition. Do not assume older deployments use the same compiler. contracts/cents-deployment.json records deployment receipts and verification; locally editing MIN_PRICE_USDC would not change an old deployed contract by itself.')

chapter('9. Exact current payment flow and test funding')
para('The active market is Polygon Amoy chain 80002. Test MockUSDC pays the asset price; test POL pays gas. Native POL and ERC-20 MockUSDC are distinct balances. A wallet\'s dollar display is not an ERC-20 balance and does not automatically convert test POL into test USDC. Minting/listing NFTs normally needs gas only, while buying additionally needs the price in MockUSDC.')
bullets(['Read the chain-verified market profile and exact six-decimal token amount.', 'Create and accept a fresh buyer/asset/listing/token-bound quote; a quote does not reserve a listing.', 'Recheck listing eligibility and read balanceOf(buyer). Reject insufficient payment-token funds.', 'Read allowance; if needed, approve the marketplace for the required price and wait for confirmation.', 'Estimate the purchase call, check test POL gas balance, recheck terms/listing and submit buyAsset.', 'Confirm the receipt and query entitlement before exposing protected download access.'])
para('Shared Amoy fee preparation enforces chain ID, uses a 25-gwei priority-fee floor, estimates the actual call, adds 20% gas margin and checks the balance against the maximum fee. It rejects estimates beyond the observed RPC/block bounds. Lowering a fee below the RPC minimum does not save a successful transaction; it causes rejection.')
section('Fee example at 0.01 USDC')
table([['Item','Amount'],['Buyer asset price','0.010000 test MockUSDC'],['Extra DKM buyer fee','0'],['Platform deduction at 500 bps (5%)','0.000500 test MockUSDC from seller gross'],['Seller remainder with no royalties','0.009500 test MockUSDC'],['Wallet gas','Separate variable test POL cost']],[280,195])
para('Configured royalty recipients, when present, change the seller remainder according to RoyaltySplitter. Integer base units and basis points avoid floating-point payment arithmetic. A seller payout preference does not itself execute FX.')
section('Confirmed test-token funding in this session')
para('At block 50772211, mint(address,uint256) issued 2,000,000 base units to 0x9202BfF93f8A46f7D9BAe982CB1c021e34E8dc66. The confirmed balance at that block was 2.0 MockUSDC. Gas spent was 0.002247510007042198 test POL. Transaction: 0x321780e016a918f8fe48b789f9176c7c5a17f7e6e29390cb92589b957fa5ea20. This proves test funding, not a subsequent purchase or download; later balances can change.')
section('Retained external-provider architecture')
para('Retained Razorpay collection requires separate prefunded settlement; it is not INR-to-USDC conversion. Transak completion and optional receipt recording cannot independently grant access. MockPaymentProvider is a non-spending workflow simulator, unlike the actual test-chain MockERC20. Neither retained provider code nor a successful test-token mint proves real UPI/card checkout or arbitrary cryptocurrency conversion.')
para('Persisted order states include CREATED, PENDING, PROVIDER_CONFIRMED, SETTLEMENT_PENDING, SETTLED, ENTITLEMENT_GRANTED and FAILED. Idempotency and canonical receipt checks protect settlement. These retained paths are separate from the active wallet-only demo.')

chapter('10. QAOA and VQC: implemented experiments')
section('VQC embedding experiment')
para('The authored corpus has 96 documents across eight domains, with four topics/domain and three variants/topic. There are 32 queries split 16 validation/16 test; 64 document vectors fit preprocessing/model parameters and 32 variants are held out from fitting. Topics still occur in fitting documents, so this is in-domain retrieval. Labels 3/1/0 are authored rules rather than independent assessor judgments.')
para('PCA reduces vectors to four components; arctan-scaled values encode into four qubits. Two layers of RY/RZ and ring CNOTs produce four Z and four adjacent ZZ expectations. Sixteen trainable parameters are optimized for 40 epochs using cosine-Gram alignment. Ridge expansion maps features back to 384 dimensions; it does not recreate discarded information. PennyLane executes exact classical statevector simulation.')
table([['Test NDCG@10 method','Result'],['Original MiniLM','0.905296'],['PCA4 + ridge expansion','0.702724'],['Untrained VQC + ridge','0.605030'],['Trained VQC + ridge','0.609317']],[330,145])
para('Training took about 1.027 seconds in the retained run. Loss decreased from 0.485185 to 0.098681, but retrieval still underperformed the classical baselines. NDCG is a ranking metric, not classification accuracy. Single-seed, small-corpus results do not establish broad superiority or significance.')
section('QAOA pricing experiment')
para('Sixty-four synthetic demand cases use 100 integer price choices, seven qubits, depth two, COBYLA with up to 80 evaluations and 2,048 seeded samples/case. The cost Hamiltonian encodes negative normalized expected revenue with invalid-state penalties. The most frequent feasible sampled price is selected. Classical bounded optimization and exhaustive enumeration are comparators.')
table([['Metric','Result'],['Mean QAOA relative revenue gap','17.6013%'],['Mean feasible probability','97.5540%'],['Exact-price matches: QAOA / classical','1 of 64 / 64 of 64'],['Mean elapsed: QAOA / classical','0.456721 s / 0.000505 s'],['Mean elapsed: exhaustive oracle','0.000051 s']],[330,145])
para('These are synthetic expected-revenue units, not actual sales. Small independent price problems favor classical optimization. Full statevector/diagonal simulation has exponential costs; no hardware quantum speedup or scalable oracle is established. Neither experiment changes production search vectors or live prices.')

chapter('11. Tests, evidence and what has actually been proved')
para('Evidence is separated into source implementation, local automated checks, simulation/read-only chain checks, confirmed public transactions and full user workflows. None implies all the others. This handbook does not rerun the entire suite.')
table([['Evidence','Supported conclusion','Not established'],['131 contract tests recorded after successor change','Local tested contract behavior at that snapshot','Every operation performed on Amoy'],['17 frontend tests + production build recorded','Covered regressions/build passed','All browser/wallet flows completed'],['3 recovery tests and 9 backend checks in separate runs','Targeted recovery/account/legacy/capability behavior','One combined fresh exhaustive test count'],['Six legacy cancel simulations','Calls estimated successfully at observed state','Actual cancellation receipt'],['Live one-cent mint estimate','Call was simulatable at given state','User NFT mint completion'],['Confirmed 2 MockUSDC mint','Token issuance and balance at block 50772211','Purchase entitlement or download'],['Retained VQC/QAOA JSON','Specific comparative experiment results','Quantum advantage / production retrieval quality'],['Local DB restore digest comparison','Restored tables matched captured data','IPFS/master-key disaster recovery'],['Saved Slither report','Recorded static findings at analyzed source','Independent production security audit']],[130,175,170])
para('Earlier acceptance evidence recorded 82 backend tests, 15 frontend regressions and 129 contract tests at a previous snapshot. Newer targeted counts supersede only their stated scope. Do not add overlapping counts. Saved static analysis reported zero high/medium, four low timestamp findings and one informational finding; retain the analyzed revision and tool output when citing it.')
section('Remaining final demonstration')
bullets(['Use a distinct seller and buyer account/wallet. Confirm buyer has MockUSDC and POL on Amoy.', 'Complete allowance approval and a real testnet purchase; save the successful receipt and verify purchaseCount/entitlement.', 'Download as buyer and compare the plaintext hash with the original upload.', 'Verify a third unrelated wallet is denied protected download.', 'If claiming live auctions/cancellation, record those receipts separately; do not substitute a simulation.', 'Document any failure and retry honestly, including gateway/RPC availability.'])

chapter('12. Contributions, limitations and security review')
para('Project-specific engineering contributions include integrating encrypted content with blockchain-backed access, account/wallet-scoped recovery, a legacy-preserving one-cent registry transition, duplicate-aware semantic retrieval, excerpt-grounded rubric validation, exact payment-unit handling and transparent quantum/classical comparison artifacts. These are integrations and implementations, not inventions of BLAKE3, AES-GCM, MiniLM, MMR, QAOA or variational circuits.')
bullets(['Implemented protections include session expiry/revocation, origin checks, signature verification, auth rate limits, encrypted content, transaction preflights, payment idempotency and account boundaries.', 'The backend is a trusted plaintext/key custodian. A stolen master key and database access can compromise protected files.', 'Public legacy files remain public. Decrypted content can be copied by authorized recipients.', 'Google/provider availability depends on configuration and external services; old evidence can expire.', 'Index backfill coverage is incomplete in retained evidence; do not assert complete lifetime totals.', 'No independent audit, production load proof, calibrated quality accuracy or universal payment support is claimed.', 'Post-quantum key release remains proposed, not implemented. The quantum_hash filename is not post-quantum protocol evidence.'])

chapter('13. API endpoint catalog')
para('Extracted directly from FastAPI app/router decorators. Prefixes are combined for routers with literal prefixes. Line numbers identify the declaration in this snapshot. Authentication and state guards must be read in the handler/dependencies; a route name alone does not establish who may call it.')
for method,route,p,line in all_routes:
    para(method+' '+route,'File');para(f'{p}:{line}','SmallBody')

chapter('14. Database and configuration catalog')
para('Table names below are extracted from CREATE TABLE IF NOT EXISTS statements, not from a live schema dump. Additional ALTER statements extend their columns. Source files are the authoritative place to inspect constraints and migrations.')
for name,refs in sorted(tables.items()):
    para(name,'File');para('Schema source: '+', '.join(sorted(refs)),'SmallBody')
section('Environment variable names only')
para('Values and defaults are intentionally withheld. These names are statically referenced in application/source files and may include inactive provider paths. Presence in this list does not mean configured, enabled or safe to expose. Server secrets must not receive NEXT_PUBLIC_ prefixes.')
for key,refs in sorted(envrefs.items()):
    para(key,'File');para('Referenced by: '+', '.join(sorted(refs)),'SmallBody')

chapter('15. Core source excerpts and how to read them')
para('The following are actual selected implementation excerpts, not a replacement implementation. Long lines are wrapped for print. The file atlas supplies the broader symbol map, including all functions/classes identified in each source file. Secrets and environment values are not reproduced.')
for p,names in [
    ('backend/services/quantum_hash.py',['quantum_hash','verify_integrity']),
    ('backend/services/content_security.py',['seal','unseal']),
    ('backend/services/embedding.py',['generate_embedding']),
    ('backend/services/quantum_search.py',['rank_results']),
    ('backend/services/auth.py',['password_hash','same_origin']),
]:
    text=read(p);tree=ast.parse(text)
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
            section(p+' :: '+node.name);code('\n'.join(text.splitlines()[node.lineno-1:node.end_lineno]))
for p,start,end in [
    ('contracts/contracts/MockERC20.sol','    function mint(', '    function decimals('),
    ('contracts/contracts/Marketplace.sol','    function _buyAsset(', '    /*//////////////////////////////////////////////////////////////'),
]:
    text=read(p);i=text.index(start);j=text.index(end,i+len(start));section(p);code(text[i:j].strip())

chapter('16. Complete project file atlas')
para(f'The atlas covers {len(records)} repository-visible source, configuration, test, documentation and evidence files captured for this snapshot. Each entry identifies its role and available code symbols with source line numbers. Test cases are intended coverage, not newly executed results. Import lists describe direct static references, not a complete runtime call graph.')
para('A directory literally named "contracts " (with a trailing space) also exists in the listing. Its starter files are documented separately and are not assumed to be the active contracts project. Installed dependencies, generated build output and private runtime files are excluded from per-file business-logic explanations; their handling is specified in the final chapter.')
lastgroup=None
for r in records:
    p=r['path'];group=p.split('/')[0] if '/' in p else 'Root documentation and evidence'
    if group!=lastgroup:
        section('Directory: '+group);lastgroup=group
    para(p,'File');para(r['purpose'],'SmallBody')
    para(f"Size: {r['size']:,} bytes"+(f" | {r['lines']:,} text lines" if r['text'] else ' | binary/unreadable as UTF-8'),'SmallBody')
    if r['symbols']:
        for i in range(0,len(r['symbols']),22):
            para('Code entry points: '+ '; '.join(f'{s} (L{ln})' for s,ln in r['symbols'][i:i+22]),'SmallBody')
    if r['imports']:
        para('Direct imports: '+', '.join(r['imports']),'SmallBody')
    if r['routes']: para('HTTP surface: '+'; '.join(r['routes']),'SmallBody')
    if r['tests']:
        for i in range(0,len(r['tests']),12): para('Declared checks: '+'; '.join(r['tests'][i:i+12]),'SmallBody')
    if p.endswith('.sol'):
        for label,pattern in [('Events',r'\bevent\s+(\w+)'),('Custom errors',r'\berror\s+(\w+)')]:
            values=re.findall(pattern,r['text'])
            if values: para(label+': '+', '.join(values),'SmallBody')
    if p.endswith('.md'):
        heads=re.findall(r'^#{1,3}\s+(.+)',r['text'],re.M)
        # Headings only, no document body or potentially sensitive operational examples.
        if heads: para('Document sections: '+'; '.join(heads[:18])+(' (additional historical sections follow)' if len(heads)>18 else ''),'SmallBody')
    if p.endswith('.json') and r['text']:
        try:
            obj=json.loads(r['text'])
            if isinstance(obj,dict): para('Top-level fields: '+', '.join(str(k) for k in obj.keys()),'SmallBody')
            elif isinstance(obj,list): para(f'Structured array with {len(obj)} entries.','SmallBody')
        except ValueError: pass

chapter('17. Current local runbook and troubleshooting')
para('These instructions describe the existing local setup; they do not reinstall, reset, redeploy or alter saved data. Start Docker Desktop if your PostgreSQL service is containerized, and preserve its existing volume. Do not replace a database or regenerate the master key to fix a login/startup error.')
code('Backend (from backend/):\n  .\\venv\\Scripts\\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000\n\nFrontend (from frontend/):\n  npm run dev\n  # For a production preview, build first, then npm run start\n\nOpen: http://localhost:3000\nNetwork in MetaMask: Polygon Amoy, chain ID 80002')
para('Ensure the existing backend environment references the intended database, Ollama endpoint/model, Pinata credential, content master key and current deployment. Values are private and are not copied here. Provider and recorder workers should remain disabled for the wallet-only demonstration unless separately needed and configured. A successful health response may check configuration/presence rather than execute every external operation.')
table([['Symptom','Likely distinction / next check'],['Insufficient USDC with POL present','Read MockUSDC balance, not native POL or its displayed dollar estimate'],['Gas tip below minimum','Use shared Amoy fee preparation; do not reduce below required RPC floor'],['Gas limit above RPC cap','Estimate the actual call, avoid enormous fixed gas overrides'],['PriceTooLow on old registry','Confirm current successor address; changing local source cannot update old bytecode'],['Upload exists but mint failed','Resume the saved draft; check pending/completed mint before retry'],['Duplicate search entries / missing View','Published-only token links and content/token deduplication; do not delete source data blindly'],['Cancel listing fails','Use the original market for old listings; recheck owner/active state and gas'],['Purchase succeeded but no download','Verify confirmed entitlement, linked CID row, wrapped key and gateway availability'],['Ollama / embedding failure','Check local model availability; do not fabricate a fallback quality score'],['History incomplete','Check indexer coverage/checkpoints; partial history is not zero historical activity']],[185,290])

chapter('18. Scope, reproducibility and final handoff')
para('This snapshot documents every file returned by the repository-aware inventory after the stated exclusions. It is not a literal dump of every dependency, generated artifact, secret or temporary file on disk. The atlas includes file roles and main code symbols; selected core implementations are reproduced in Chapter 15. For exact full source, use the matching working-tree snapshot, not a reformatted PDF.')
table([['File category','Treatment'],['Project source/config/tests/docs/evidence','Per-file atlas, symbols, routes and source references'],['.env / private keys / credential files','Contents excluded; referenced variable names only'],['node_modules / Python virtual environments','Third-party dependency trees summarized by manifests/lockfiles'],['.next / artifacts / cache / bytecode build output','Generated derivatives; regenerate with the pinned build toolchain'],['tmp/','Transient investigation/rendering scripts and scratch files; not canonical app source'],['output/','Generated reports and plots; evidence sources referenced where used, handbook itself excluded from recursive inventory'],['Git internals / logs / database dumps','Not reproduced; may contain history, secrets or user data']],[210,265])
para('The current working branch is codex/dkm-payment-persistence; the handbook describes uncommitted working-tree changes as well as previously saved code. Before publishing research artifacts, freeze a commit, record lockfiles and exact environment, and remove secrets/user data from the release package. No code was pushed or deployed to create this document.')
section('Primary internal evidence')
bullets(['PROJECT_CONTEXT.md: latest implementation/deployment and test history.', 'TEST_EVIDENCE.md and acceptance_results.json: prior test outcomes and limitations.', 'contracts/cents-deployment.json: current deployment receipts and preserved legacy state.', 'research_results/vqc_embeddings.json and qaoa_pricing.json: experimental results; companion reports explain protocols.', 'restore_drill_evidence.json and SLITHER_AUDIT.json: bounded restore/static-analysis evidence.', 'output/research/ui_search_scoring_checks.json: retained retrieval/scoring sanity evidence.', 'Confirmed test-funding transaction shown in Chapter 9: receipt and balance verified during this session.'])
para('No new all-suite test run, real-money payment, complete purchase/download, independent security audit or quantum-hardware experiment was performed for this handbook. The last confirmed live step is test-token funding. The remaining demonstration must show the actual purchase entitlement and successful authorized download, with an unrelated wallet denied access.')

def footer(canvas,doc):
    canvas.saveState();w,h=A4
    canvas.setStrokeColor(colors.HexColor('#c5d7de'));canvas.line(50,h-40,w-50,h-40)
    canvas.setFillColor(colors.HexColor('#476574'));canvas.setFont('Helvetica',8)
    canvas.drawString(50,h-30,'DKM | Technical handbook | '+DATE)
    canvas.drawString(50,28,'Repository snapshot - testnet evidence, not production certification')
    canvas.drawRightString(w-50,28,str(doc.page));canvas.restoreState()

doc=Handbook(str(OUT),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=58,bottomMargin=48,title='DKM Complete Technical Handbook',author='DKM project documentation')
frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id='main')
doc.addPageTemplates(PageTemplate(id='all',frames=frame,onPage=footer))
doc.multiBuild(story)
reader=PdfReader(str(OUT));extracted='\n'.join(page.extract_text() or '' for page in reader.pages)
assert len(reader.pages)>25
for marker in ['backend/main.py','MockUSDC','BLAKE3','QAOA','VQC','50772211','Complete project file atlas']:
    assert marker in extracted,marker
assert 'PRIVATE_KEY=' not in extracted and 'Bearer ey' not in extracted
manifest={'date':DATE,'files':len(paths),'routes':len(all_routes),'tables':len(tables),'pages':len(reader.pages),'pdf_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'inventory':paths}
(ROOT/'tmp/pdfs/handbook_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='inventory'}))
