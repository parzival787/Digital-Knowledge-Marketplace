"use client";
import { usePaymentCapabilities } from "@/lib/api/capabilities";

const names: Record<string, string> = { fixed_price: "Fixed-price purchase", auction: "Auctions", transak_buy: "Transak funding",
  transak_sell: "Transak withdrawal", razorpay: "Razorpay test checkout", upi: "UPI", crypto_route: "Other cryptocurrency", receipt_registry: "Blockchain audit receipt" };
export default function PaymentCapabilities() {
  const { data, isError } = usePaymentCapabilities();
  return <section className="space-y-3 rounded-xl border p-5" aria-label="Payment availability">
    <h2 className="text-xl font-semibold">Available payment routes</h2>
    {!data && <p role="status">{isError ? "Availability could not be verified. Payment options remain disabled; retry shortly." : "Checking supported routes…"}</p>}
    {data && Object.entries(data.routes).map(([id, route]) => <div key={id} className="border-t pt-2">
      <h3 className="font-semibold">{names[id] || id}: {route.state.replaceAll("_", " ")}</h3><p>{route.message}</p>
    </div>)}
    <p className="text-sm">All routes are test-only. Funding, marketplace purchase and seller payout are separate steps.</p>
  </section>;
}
