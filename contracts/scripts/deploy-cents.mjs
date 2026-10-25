import fs from 'node:fs';
import dotenv from 'dotenv';
import { Contract, ContractFactory, JsonRpcProvider, Wallet, formatEther, getCreateAddress, keccak256 } from 'ethers';
dotenv.config({quiet:true});
const path = 'cents-deployment.json';
const OLD = '0x2C16409A3db9880f9A70e71B5b131A17db533Fc9';
const OLD_MARKET = '0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d';
const OLD_SPLIT = '0x43cE72CEd667bDe9252044451b07ecA1aec2D300';
const TOKEN = '0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719';
const artifact = name => JSON.parse(fs.readFileSync(`artifacts/contracts/${name}.sol/${name}.json`, 'utf8'));
async function main() {
  if (fs.existsSync(path)) throw Error('Existing journal: inspect it before any retry');
  const provider = new JsonRpcProvider(process.env.ALCHEMY_AMOY_URL);
  if ((await provider.getNetwork()).chainId !== 80002n) throw Error('Wrong network');
  const wallet = new Wallet(process.env.PRIVATE_KEY, provider);
  const old = new Contract(OLD, artifact('KnowledgeAsset').abi, provider);
  const oldMarket = new Contract(OLD_MARKET, artifact('Marketplace').abi, provider);
  const oldSplit = new Contract(OLD_SPLIT, artifact('RoyaltySplitter').abi, provider);
  if ((await oldMarket.knowledgeAsset()).toLowerCase() !== OLD.toLowerCase() || (await oldMarket.usdc()).toLowerCase() !== TOKEN.toLowerCase()) throw Error('Old deployment mismatch');
  const limit = await old.totalMinted();
  if (limit !== 6n) throw Error('Legacy inventory changed; re-review transition');
  const snapshots = [];
  for (let id=1; id<=Number(limit); id++) snapshots.push({id, owner:await old.ownerOf(id), asset:Array.from(await old.getAsset(id)).map(String)});
  const block = await provider.getBlock('latest');
  const feeData = await provider.getFeeData();
  const tip = feeData.maxPriorityFeePerGas > 25_000_000_000n ? feeData.maxPriorityFeePerGas : 25_000_000_000n;
  const fees = {maxPriorityFeePerGas:tip, maxFeePerGas:block.baseFeePerGas*2n+tip};
  let nonce = await provider.getTransactionCount(wallet.address, 'pending');
  const registryAddress = getCreateAddress({from:wallet.address, nonce});
  const splitAddress = getCreateAddress({from:wallet.address, nonce:nonce+1});
  const marketAddress = getCreateAddress({from:wallet.address, nonce:nonce+2});
  const treasury = await oldSplit.treasury();
  const platformFee = await oldSplit.platformFeeBps();
  const specs = [['KnowledgeAssetSuccessor',[OLD]], ['RoyaltySplitter',[TOKEN,treasury,platformFee]], ['Marketplace',[registryAddress,splitAddress,TOKEN]]];
  const prepared = [];
  for (const [name,args] of specs) {
    const a = artifact(name), factory = new ContractFactory(a.abi,a.bytecode,wallet);
    const tx = await factory.getDeployTransaction(...args);
    const gasLimit = (await provider.estimateGas({...tx,from:wallet.address,...fees}))*120n/100n;
    prepared.push({name, factory, args, gasLimit});
  }
  const budget = (prepared.reduce((n,p)=>n+p.gasLimit,0n)+150_000n)*fees.maxFeePerGas;
  if (budget > await provider.getBalance(wallet.address)) throw Error('Insufficient deployer POL');
  console.log(JSON.stringify({chain:80002,deployer:wallet.address,maximumEstimatedPOL:formatEther(budget),legacyTokens:Number(limit)}));
  if (process.env.DKM_DEPLOY_CENTS !== 'true') return;
  const journal = {status:'deploying',chain_id:80002,deployer:wallet.address,legacy_registry:OLD,legacy_marketplace:OLD_MARKET,legacy_splitter:OLD_SPLIT,token:TOKEN,legacy_token_limit:Number(limit),snapshots,contracts:{}};
  const save=()=>fs.writeFileSync(path,JSON.stringify(journal,null,2)+'\n'); save();
  for (const {name,factory,args,gasLimit} of prepared) {
    const contract=await factory.deploy(...args,{...fees,gasLimit,nonce:nonce++});
    const tx=contract.deploymentTransaction();
    journal.contracts[name]={address:await contract.getAddress(),transaction_hash:tx.hash}; save();
    const receipt=await tx.wait(2);
    if (receipt?.status!==1) throw Error('Deployment not confirmed');
    journal.contracts[name].block=receipt.blockNumber;
    journal.contracts[name].code_hash=keccak256(await provider.getCode(await contract.getAddress())); save();
  }
  const split=new Contract(splitAddress,artifact('RoyaltySplitter').abi,wallet);
  const gasLimit=(await split.updateMarketplace.estimateGas(marketAddress,{...fees}))*120n/100n;
  const tx=await split.updateMarketplace(marketAddress,{...fees,gasLimit,nonce});
  journal.wiring_transaction=tx.hash; save();
  if ((await tx.wait(2))?.status!==1) throw Error('Wiring not confirmed');
  const registry=new Contract(registryAddress,artifact('KnowledgeAssetSuccessor').abi,provider);
  const market=new Contract(marketAddress,artifact('Marketplace').abi,provider);
  if (await registry.MIN_PRICE_USDC()!==10_000n || await registry.legacyTokenLimit()!==limit || (await registry.legacyRegistry()).toLowerCase()!==OLD.toLowerCase() || await market.knowledgeAsset()!==registryAddress || await market.royaltySplitter()!==splitAddress || (await market.usdc()).toLowerCase()!==TOKEN.toLowerCase() || await split.marketplace()!==marketAddress || await split.treasury()!==treasury || await split.platformFeeBps()!==platformFee) throw Error('New wiring mismatch');
  if (await old.totalMinted()!==limit) throw Error('Legacy inventory changed during deployment');
  for (const snapshot of snapshots) {
    if (await registry.ownerOf(snapshot.id)!==snapshot.owner || JSON.stringify(Array.from(await registry.getAsset(snapshot.id)).map(String))!==JSON.stringify(snapshot.asset)) throw Error('Legacy data changed');
  }
  if ((await oldSplit.marketplace()).toLowerCase()!==OLD_MARKET.toLowerCase()) throw Error('Old wiring changed');
  journal.status='verified'; save(); console.log('Verified deployment saved. Application switch remains separate.');
}
main().catch(error=>{console.error('Deployment stopped:', error.shortMessage || (error.message?.includes('http') ? 'RPC error; inspect journal' : error.message));process.exitCode=1;});
