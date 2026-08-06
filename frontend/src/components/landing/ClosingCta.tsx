import { Link } from 'react-router-dom'


export function ClosingCta() {
  return (
    <section className="py-24 px-4 text-center border-t border-hairline">
      <h2 className="font-display text-4xl font-bold mb-6 text-ink">Ready to initialize?</h2>
      <p className="font-body text-slate max-w-xl mx-auto mb-10">
        Stop managing applications. Start operating a system that works for you.
      </p>
      <Link to="/register">
        <button className="px-8 py-3 bg-emerald-500 hover:bg-emerald-400 text-black font-mono font-bold rounded-lg shadow-[0_0_25px_rgba(16,185,129,0.4)] transition-all duration-300 hover:scale-105">
          BOOT SYSTEM &rarr;
        </button>
      </Link>
    </section>
  )
}
