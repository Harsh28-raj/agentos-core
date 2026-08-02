export function DayInTheLife() {
  const events = [
    { time: '08:00', event: 'System reviews overnight data, summarizes urgent emails, and prepares a morning briefing.' },
    { time: '14:00', event: 'Automatically negotiates a meeting time with a client based on calendar availability and preferences.' },
    { time: '20:00', event: 'Compiles the day\'s research, generates a draft report, and shuts down non-essential background processes.' }
  ]

  return (
    <section className="py-20 px-4 max-w-3xl mx-auto border-t border-hairline">
      <h2 className="font-display text-3xl font-bold mb-12 text-center">A Day in the Life</h2>
      <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-hairline">
        {events.map((e, i) => (
          <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-paper bg-signal text-signal-ink font-mono text-xs z-10 shrink-0 md:order-1 md:group-odd:-ml-5 md:group-even:-mr-5">
              {i + 1}
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-base bg-surface border border-hairline shadow-sm">
              <div className="font-mono text-[10px] text-signal uppercase tracking-wider mb-2">{e.time}</div>
              <p className="font-body text-slate text-sm group-hover:text-ink transition-colors">{e.event}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
