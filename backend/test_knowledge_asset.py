from services.blockchain import get_knowledge_asset

TOKEN_ID = 1

try:
    asset = get_knowledge_asset(TOKEN_ID)

    print("KnowledgeAsset connection successful!")
    print("Token ID:", TOKEN_ID)
    print("IPFS CID:", asset["ipfs_cid"])
    print("Metadata CID:", asset["metadata_cid"])
    print("Creator:", asset["creator"])
    print("Owner:", asset["owner"])
    print("Price USDC:", asset["price_usdc"])
    print("License:", asset["license"])
    print("Quality:", asset["quality_score"])
    print("Active:", asset["active"])

except Exception as e:
    print("KnowledgeAsset test failed:")
    print(type(e).__name__, str(e))