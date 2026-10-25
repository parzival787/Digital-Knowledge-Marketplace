import { formatUnits } from "viem";
import type { PurchaseQuote } from "@/lib/api/quotes";

export default function PurchaseQuoteSummary({ quote }: { quote: PurchaseQuote }) {
  const t = quote.terms;
  const amount = (v: string) => formatUnits(BigInt(v), t.decimals);
  return <div className="space-y-1 rounded border bg-slate-50 p-3 text-sm" aria-label="Purchase quote">
    <p className="font-semibold">Review before signing</p>
    <p>You pay: {amount(t.buyer_token_total_base_units)} {t.symbol} plus wallet gas.</p>
    <p>Extra DKM buyer fee: {amount(t.buyer_dkm_fee_base_units)}.</p>
    <p>Seller gross: {amount(t.seller_gross_base_units)}; platform deduction: {amount(t.platform_fee_base_units)}; royalties: {amount(t.royalty_total_base_units)}.</p>
    <p>Seller net: {amount(t.seller_net_base_units)} {t.symbol}.</p>
    <p>Seller payout preference: {t.seller_payout_preference}. Conversion is separate and is not included.</p>
    <p>{t.external_cost_notice}</p>
    <p>Quote expires: {new Date(quote.expires_at).toLocaleTimeString()}. This does not reserve the asset.</p>
  </div>;
}
