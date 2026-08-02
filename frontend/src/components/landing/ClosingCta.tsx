import { Link } from 'react-router-dom'
import { Button } from '../common/Button'

export function ClosingCta() {
  return (
    <section className="py-24 px-4 text-center border-t border-hairline">
      <h2 className="font-display text-4xl font-bold mb-6 text-ink">Ready to initialize?</h2>
      <p className="font-body text-slate max-w-xl mx-auto mb-10">
        Stop managing applications. Start operating a system that works for you.
      </p>
      <Link to="/register">
        <Button className="px-8 py-3 text-lg font-bold uppercase tracking-wider font-mono">
          Boot System
        </Button>
      </Link>
    </section>
  )
}
