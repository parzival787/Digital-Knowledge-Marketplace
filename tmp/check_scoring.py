import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from dotenv import load_dotenv
load_dotenv('.env')
from services.llm_enrichment import enrich_document
from services.pgvector_client import get_conn

async def main():
    detailed = 'Rainfall measurements were collected daily at ten stations in Pune during June 2024. A calibrated tipping-bucket rain gauge recorded rainfall_mm at 09:00 local time. Each CSV row contains station_id, observation_date and rainfall_mm. Missing readings are marked NA and excluded from monthly means. Two stations missed three days due to power loss; coverage is limited to these stations. Raw records and calibration dates accompany the dataset. To reproduce the monthly result, group valid rows by station_id and calculate the arithmetic mean of rainfall_mm.'
    vague = 'This is a great study about science. It is useful and important. Our work is excellent and everyone should use it. We have good results and many things to share.'
    results = {}
    for name, text in [('detailed', detailed), ('detailed_repeat', detailed), ('vague', vague)]:
        try:
            result = await enrich_document(text)
            results[name] = {'score': result['quality_score'], 'criteria': result['quality_breakdown']}
            print(name, result['quality_score'], flush=True)
        except Exception as exc:
            results[name] = {'error': str(exc)}
            print(name, type(exc).__name__, flush=True)
    conn = await get_conn()
    try:
        results['catalog'] = dict(await conn.fetchrow('SELECT count(*) AS uploads, count(*) FILTER (WHERE token_id > 0) AS linked, count(DISTINCT token_id) AS distinct_tokens FROM knowledge_assets'))
    finally: await conn.close()
    Path('../output/research/ui_search_scoring_checks.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
asyncio.run(main())
