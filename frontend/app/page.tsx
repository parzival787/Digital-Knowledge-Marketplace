import Navbar from "@/components/layout/Navbar";
import BlockchainTest from "@/components/marketplace/BlockchainTest";

export default function Home() {
  return (
    <>
      <Navbar />

      <main className="mx-auto max-w-7xl px-6 py-20">

        <section className="text-center">

          <p className="mb-4 text-sm font-medium">
            DECENTRALIZED KNOWLEDGE MARKETPLACE
          </p>

          <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
            Buy, Sell & Auction
            <br />
            Knowledge Assets
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            A decentralized marketplace for research datasets,
            knowledge assets, and intellectual resources.
          </p>

          <div className="mt-8 flex justify-center gap-4">

            <a
              href="/marketplace"
              className="rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground"
            >
              Explore Marketplace
            </a>

            <a
              href="/mint"
              className="rounded-md border px-6 py-3 text-sm font-medium"
            >
              Create Asset
            </a>

          </div>

        </section>
        <BlockchainTest />
      </main>
    </>
  );
}