export function FeatureGrid() {
  const features = [
    { label: 'Autonomous execution', desc: 'Give a high-level goal, and the system breaks it down into executable steps.', tag: 'SYS_CORE' },
    { label: 'Three-tier memory', desc: 'Short-term context, episodic events, and long-term semantic retrieval.', tag: 'MEM_ARCH' },
    { label: 'Proactive background triggers', desc: 'Schedules and runs tasks while you are offline, notifying you only when necessary.', tag: 'CRON_EVT' },
    { label: 'Multi-modal processing', desc: 'Understands voice, reads documents, and processes visual information seamlessly.', tag: 'IO_STREAM' },
    { label: 'Local privacy mode', desc: 'Keep your most sensitive data entirely on your device with local models.', tag: 'SEC_ISOL' },
    { label: 'Transparent dashboard', desc: 'See exactly what the agent is thinking, doing, and planning at all times.', tag: 'UI_STATE' }
  ]

  return (
    <section className="py-20 px-4 max-w-7xl mx-auto border-t border-hairline">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((f, i) => (
          <div key={i} className="p-6 bg-surface border border-hairline rounded-base flex flex-col h-full hover:-translate-y-1 hover:border-neutral-700 hover:bg-neutral-900/60 hover:shadow-[0_0_20px_rgba(16,185,129,0.1)] transition-all duration-300 group">
            <span className="font-mono text-xs text-emerald-400 mb-4 border border-emerald-800/50 bg-emerald-950/40 self-start px-2.5 py-1 rounded-md">
              {f.tag}
            </span>
            <h3 className="font-display font-bold text-lg mb-2 text-ink group-hover:text-emerald-400 transition-colors">{f.label}</h3>
            <p className="font-body text-slate text-sm flex-1">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
