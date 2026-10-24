"""Verify the disposable local drill copy without outputting rows or credentials."""
import asyncio
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from dotenv import load_dotenv
load_dotenv()
import asyncpg
from services import pgvector_client as db


async def main():
    target='dkm_restore_drill_20261011'
    parsed=urlsplit(db.DB_URL)
    restored=urlunsplit((parsed.scheme,parsed.netloc,'/'+target,parsed.query,parsed.fragment))
    source=await asyncpg.connect(db.DB_URL);copy=await asyncpg.connect(restored)
    report=[]
    try:
        tables=await source.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        for row in tables:
            table='"'+row['tablename'].replace('"','""')+'"'
            query=f"SELECT count(*) AS count,md5(COALESCE(string_agg(md5(t::text),'' ORDER BY md5(t::text)),'')) AS digest FROM public.{table} t"
            a,b=await source.fetchrow(query),await copy.fetchrow(query)
            report.append({'table':row['tablename'],'rows':a['count'],'matches':dict(a)==dict(b)})
        if not all(r['matches'] for r in report): raise ValueError('Restore contents mismatch')
        result={'scope':'local PostgreSQL dump/restore; all public-table row counts and content digests matched',
            'external_ipfs_restore_tested':False,'independent_key_backup_tested':False,'tables':report}
        Path('../restore_drill_evidence.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'tables_verified':len(report),'all_match':True}))
    finally:
        await source.close();await copy.close()


if __name__=='__main__':
    try:asyncio.run(main())
    except Exception:raise SystemExit('Restore verification failed; no data or credentials printed.') from None
