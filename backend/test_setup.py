import asyncio
from services.pgvector_client import setup_tables

asyncio.run(setup_tables())


