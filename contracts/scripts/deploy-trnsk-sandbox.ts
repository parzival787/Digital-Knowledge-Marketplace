// Prepare by default. Public deployment requires a separately approved address file and explicit opt-in.
import { network } from "hardhat";
import { readFileSync, writeFileSync, existsSync } from "node:fs";

const { ethers } = await network.connect();
const ASSET = "0x2C16409A3db9880f9A70e71B5b131A17db533Fc9";
const OLD_MARKET = "0xDe7bdacb8B3ff631dbcdb09C81c0de7421475A5d";
const OLD_SPLITTER = "0x43cE72CEd667bDe9252044451b07ecA1aec2D300";
const OLD_TOKEN = "0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719";
const TRNSK = "0x0c86A754A29714C4Fe9C6F1359fa7099eD174c0b";
const output = "../trnsk-deployment-manifest.json";

async function main() {
  if ((await ethers.provider.getNetwork()).chainId !== 80002n) throw new Error("Only Amoy chain 80002 is allowed");
  const roles = JSON.parse(readFileSync("../sandbox-deployment-addresses.json", "utf8"));
  for (const key of ["treasury", "admin", "settlement", "recorder"])
    if (!ethers.isAddress(roles[key]) || roles[key] === ethers.ZeroAddress) throw new Error(`Missing valid public ${key} address`);
  if (new Set([roles.admin, roles.settlement, roles.recorder].map((a:string)=>a.toLowerCase())).size !== 3)
    throw new Error("Admin, settlement and recorder must be separate addresses");
  const block = await ethers.provider.getBlockNumber();
  const oldMarket = await ethers.getContractAt("Marketplace", OLD_MARKET);
  const oldSplitter = await ethers.getContractAt("RoyaltySplitter", OLD_SPLITTER);
  const token = new ethers.Contract(TRNSK, ["function symbol() view returns(string)", "function decimals() view returns(uint8)"], ethers.provider);
  const hashes:Record<string,string> = {};
  for (const address of [ASSET, OLD_MARKET, OLD_SPLITTER, OLD_TOKEN, TRNSK]) {
    const code = await ethers.provider.getCode(address, block);
    if (code === "0x") throw new Error("Required deployed contract missing");
    hashes[address] = ethers.keccak256(code);
  }
  if ((await oldMarket.knowledgeAsset()).toLowerCase() !== ASSET.toLowerCase() ||
      (await oldMarket.usdc()).toLowerCase() !== OLD_TOKEN.toLowerCase() ||
      (await oldMarket.royaltySplitter()).toLowerCase() !== OLD_SPLITTER.toLowerCase() ||
      (await oldSplitter.marketplace()).toLowerCase() !== OLD_MARKET.toLowerCase() ||
      (await oldSplitter.usdc()).toLowerCase() !== OLD_TOKEN.toLowerCase()) throw new Error("Legacy wiring changed");
  if (await token.getFunction("symbol")() !== "TRNSK" || await token.getFunction("decimals")() !== 18n)
    throw new Error("TRNSK metadata mismatch");
  const plan = { chain_id:80002, sandbox:true, verified_block:block, existing_code_hashes:hashes,
    preserved:{knowledge_asset:ASSET, marketplace:OLD_MARKET, splitter:OLD_SPLITTER, token:OLD_TOKEN},
    token:{address:TRNSK,symbol:"TRNSK",decimals:18}, roles, platform_fee_bps:500 };
  if (process.env.DKM_APPROVED_AMOY_DEPLOYMENT !== "true") {
    writeFileSync("../trnsk-deployment-plan.json", JSON.stringify(plan,null,2)+"\n");
    console.log("Read-only plan saved. No transactions sent.");
    return;
  }
  if (existsSync(output)) throw new Error("Deployment journal exists; inspect and recover it instead of deploying duplicates");
  const [admin] = await ethers.getSigners();
  if (!admin || admin.address.toLowerCase() !== roles.admin.toLowerCase()) throw new Error("Signer is not the approved admin");
  const journal:any = {...plan,status:"started",contracts:{}};
  const save = () => writeFileSync(output,JSON.stringify(journal,null,2)+"\n");
  save();
  async function record(name:string, contract:any) {
    const tx = contract.deploymentTransaction();
    journal.contracts[name]={address:await contract.getAddress(),transaction_hash:tx.hash};save();
    const receipt=await tx.wait(2);
    if (!receipt || receipt.status!==1) throw new Error("Deployment not confirmed");
    const code=await ethers.provider.getCode(await contract.getAddress());
    journal.contracts[name].block=receipt.blockNumber;
    journal.contracts[name].code_hash=ethers.keccak256(code);save();
  }
  const splitter=await ethers.deployContract("RoyaltySplitter",[TRNSK,roles.treasury,500],admin);await record("RoyaltySplitter",splitter);
  const market=await ethers.deployContract("Marketplace",[ASSET,await splitter.getAddress(),TRNSK],admin);await record("Marketplace",market);
  const wiring=await splitter.updateMarketplace(await market.getAddress());journal.wiring_transaction=wiring.hash;save();await wiring.wait(2);
  const registry=await ethers.deployContract("PaymentReceiptRegistry",[roles.recorder,true],admin);await record("PaymentReceiptRegistry",registry);
  if ((await market.usdc()).toLowerCase()!==TRNSK.toLowerCase() || (await market.knowledgeAsset()).toLowerCase()!==ASSET.toLowerCase() ||
      await market.royaltySplitter()!==await splitter.getAddress() || await splitter.marketplace()!==await market.getAddress() ||
      (await splitter.treasury()).toLowerCase()!==roles.treasury.toLowerCase() || await splitter.platformFeeBps()!==500n ||
      (await market.owner()).toLowerCase()!==roles.admin.toLowerCase() || (await splitter.owner()).toLowerCase()!==roles.admin.toLowerCase() ||
      !await registry.sandbox() || !await registry.hasRole(await registry.RECORDER_ROLE(),roles.recorder) ||
      !await registry.hasRole(await registry.DEFAULT_ADMIN_ROLE(),roles.admin)) throw new Error("Post-deployment verification failed");
  for (const address of [ASSET,OLD_MARKET,OLD_SPLITTER,OLD_TOKEN])
    if (ethers.keccak256(await ethers.provider.getCode(address))!==hashes[address]) throw new Error("Preserved code changed");
  journal.status="verified";save();
  console.log("Verified sandbox deployment manifest saved. Application addresses have not been switched.");
}

main().catch(()=>{console.error("Sandbox preparation/deployment stopped. Inspect the public journal and configuration; no automatic retry.");process.exitCode=1;});
