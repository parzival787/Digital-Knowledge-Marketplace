"use client";
import { usePaymentCapabilities } from "@/lib/api/capabilities";

const names: Record<string, string> = { fixed_price: "Wallet purchase", auction: "Auctions" };
export default function PaymentCapabilities() {
  const { data, isError } = usePaymentCapabilities();
  return <section className="space-y-3 rounded-xl border p-5" aria-label="Payment availability">
    <h2 className="text-xl font-semibold">Available payment routes</h2>
    {!data && <p role="status">{isError ? "Availability could not be verified. Payment options remain disabled; retry shortly." : "Checking supported routes…"}</p>}
    {data && Object.entries(data.routes).filter(([id]) => id in names).map(([id, route]) => <div key={id} className="border-t pt-2">
      <h3 className="font-semibold">{names[id] || id}: {route.state.replaceAll("_", " ")}</h3><p>{route.message}</p>
    </div>)}
    <p className="text-sm">Pay with the marketplace payment token on Polygon Amoy. Test POL is needed separately for gas.</p>
  </section>;
}
