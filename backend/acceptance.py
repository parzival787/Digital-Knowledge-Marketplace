"""Local automated acceptance; no public deployment, wallet signing or provider purchase."""
import json
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

root=Path(__file__).resolve().parents[1]
logs=root/'tmp'/'acceptance';logs.mkdir(parents=True,exist_ok=True)
checks=[
    ('backend',[sys.executable,'-m','unittest',
        'tests.test_auth','tests.test_payments','tests.test_transak','tests.test_payouts',
        'tests.test_recording','tests.test_recording_sources','tests.test_indexer',
        'tests.test_receipts','tests.test_activity','tests.test_legacy_access','tests.test_positions',
        'tests.test_capabilities','tests.test_quotes','tests.test_market_profiles','tests.test_token_delivery',
        'tests.test_asset_funding','tests.test_sale_payouts','tests.test_transak_discovery','tests.test_research_results','test_ipfs_gateway','-q'],root/'backend'),
    ('frontend-regressions',['node','--test',*[str(p) for p in sorted((root/'frontend/tests').glob('*.test.mjs'))]],root/'frontend'),
    ('frontend-build',['cmd','/c','npm','run','build'],root/'frontend'),
    ('contracts',['cmd','/c','node_modules\\.bin\\hardhat.cmd','test'],root/'contracts'),
    ('contract-types',['cmd','/c','node_modules\\.bin\\tsc.cmd','--noEmit'],root/'contracts'),
]
results=[]
for name,command,cwd in checks:
    started=time.monotonic()
    with (logs/(name+'.log')).open('w',encoding='utf-8') as output:
        completed=subprocess.run(command,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,check=False)
    result={'check':name,'exit_code':completed.returncode,'seconds':round(time.monotonic()-started,2)}
    results.append(result);print(json.dumps(result),flush=True)
    (root/'acceptance_results.json').write_text(json.dumps({'started_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'local automated checks; provider/chain boundaries simulated in backend tests; no interactive E2E claim',
        'checks':results},indent=2)+'\n')
raise SystemExit(0 if all(r['exit_code']==0 for r in results) else 1)
