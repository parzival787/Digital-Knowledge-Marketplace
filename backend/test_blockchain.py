from services.blockchain import check_blockchain_connection


result = check_blockchain_connection()

print("Blockchain connection successful!")
print("Chain ID:", result["chain_id"])
print("Latest block:", result["latest_block"])