import { api } from "./client";

export type PurchaseQuote = {
  id: string; expires_at: string; accepted_at: string | null;
  terms: { chain_id: number; marketplace: string; payment_token: string; buyer: string;
    token_id: string; listing_id: string; asset_price_base_units: string; buyer_token_total_base_units: string;
    buyer_dkm_fee_base_units: string; platform_fee_base_units: string; royalty_total_base_units: string;
    seller_gross_base_units: string; seller_net_base_units: string; seller_payout_preference: string;
    external_cost_notice: string; decimals: number };
};
export async function acceptPurchaseQuote(quote: PurchaseQuote, expected: {
  buyer: string; market: string; token: string; tokenId: bigint; listingId: bigint; amount: bigint;
}) {
  const terms = quote.terms;
  if (Date.parse(quote.expires_at) <= Date.now() || !Number.isFinite(Date.parse(quote.expires_at)) ||
      terms.chain_id !== 80002 || terms.decimals !== 6 || terms.buyer.toLowerCase() !== expected.buyer.toLowerCase() ||
      terms.marketplace.toLowerCase() !== expected.market.toLowerCase() || terms.payment_token.toLowerCase() !== expected.token.toLowerCase() ||
      BigInt(terms.token_id) !== expected.tokenId || BigInt(terms.listing_id) !== expected.listingId ||
      BigInt(terms.asset_price_base_units) !== expected.amount || BigInt(terms.buyer_token_total_base_units) !== expected.amount ||
      terms.buyer_dkm_fee_base_units !== "0") throw new Error("Quote changed or expired. Review the current terms before paying.");
  const accepted = await api<PurchaseQuote>(`/api/purchase-quotes/${quote.id}/accept`, { method: "POST" });
  if (accepted.id !== quote.id || !accepted.accepted_at || JSON.stringify(accepted.terms) !== JSON.stringify(terms))
    throw new Error("Quote changed. Review the current terms before paying.");
  return accepted;
}
