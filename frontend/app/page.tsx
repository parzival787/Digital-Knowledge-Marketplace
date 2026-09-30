import Link from "next/link";

export default function Home() {
  return <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-16 text-white">
    <section className="w-full max-w-2xl text-center" aria-labelledby="welcome-title">
      <div className="mx-auto mb-8 grid h-16 w-16 place-items-center rounded-2xl border border-blue-400/30 bg-blue-400/10 text-xl font-bold text-blue-200" aria-hidden="true">DKM</div>
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-blue-300">Decentralized Knowledge Marketplace</p>
      <h1 id="welcome-title" className="mt-6 text-4xl font-bold tracking-tight sm:text-6xl">Welcome to DKM.</h1>
      <p className="mx-auto mt-6 max-w-lg text-lg leading-8 text-slate-300">Your space to discover, create and share knowledge. Create an account or log in to enter your workspace.</p>
      <div className="mx-auto mt-10 flex max-w-sm flex-col gap-3 sm:flex-row">
        <Link href="/signup" className="flex-1 rounded-xl bg-blue-500 px-6 py-3 font-semibold text-white hover:bg-blue-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300">Create an account</Link>
        <Link href="/login" className="flex-1 rounded-xl border border-slate-600 px-6 py-3 font-semibold hover:bg-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300">Log in</Link>
      </div>
      <p className="mt-8 text-sm text-slate-400">Your account. Your knowledge. Your workspace.</p>
    </section>
  </main>;
}
