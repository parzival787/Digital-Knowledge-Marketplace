from pathlib import Path
p=Path('frontend/components/marketplace/AuctionPanel.tsx')
s=p.read_text(encoding='utf-8').replace('disabled={busy || !address}', 'disabled={busy || !address || !auctionAvailable}').replace('disabled={busy}', 'disabled={busy || !auctionAvailable}')
s=s.replace('aria-label="Auction">', 'aria-label="Auction">\n    {!auctionAvailable && <p role="status">Auction availability could not be verified. Actions are disabled until the deployment is checked.</p>}')
p.write_text(s,encoding='utf-8')
p=Path('frontend/tests/legacyAuction.test.mjs');s=p.read_text();s=s.replace('if (name === "@/providers/AuthProvider")', 'if (name === "@/lib/api/capabilities") return { usePaymentCapabilities: () => ({data:{},isError:false}), marketRouteAvailable: () => true };\n    if (name === "@/providers/AuthProvider")');p.write_text(s)
