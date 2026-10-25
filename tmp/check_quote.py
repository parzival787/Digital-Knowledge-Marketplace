from dotenv import load_dotenv
load_dotenv()
from services.payments.quotes import purchase_terms
from services.payments.settlement import SETTLEMENT_ABI,function_abi
from services import blockchain
from web3 import Web3
try:
    market=blockchain.w3.eth.contract(address=blockchain.marketplace.address,abi=SETTLEMENT_ABI+[function_abi('totalListingsCreated',[],['uint256'])])
    count=market.functions.totalListingsCreated().call()
    for listing_id in range(1,min(count,25)+1):
        listing=market.functions.listings(listing_id).call()
        if listing[4] and listing[3]==0:
            terms=purchase_terms(listing[0],Web3.to_checksum_address('0x'+'12'*20))
            print({'read_only_quote_verified':True,'token_id':terms['token_id'],'price_base_units':terms['asset_price_base_units'],'platform_fee_base_units':terms['platform_fee_base_units'],'royalty_base_units':terms['royalty_total_base_units'],'seller_net_base_units':terms['seller_net_base_units']})
            break
    else:
        print({'read_only_quote_verified':False,'reason':'No active fixed listing in bounded sample'})
except Exception:
    print({'read_only_quote_verified':False,'reason':'RPC or deployed quote-interface check failed; no raw diagnostic exposed'})
