export function UseCaseGrid() {
  const cases = [
    { title: 'Personal Research Assistant', desc: 'Synthesizes papers, articles, and long-form content into actionable briefs.' },
    { title: 'Workflow Automation', desc: 'Handles repetitive tasks across web applications, spreadsheets, and databases.' },
    { title: 'Calendar Management', desc: 'Proactively resolves scheduling conflicts and prepares briefing materials for upcoming meetings.' },
    { title: 'Data Extraction', desc: 'Pulls structured data from unstructured sources and populates tracking systems.' },
    { title: 'Code Context Retention', desc: 'Maintains context across multiple projects, providing intelligent, codebase-aware completions.' }
  ]

  return (
    <section className="py-20 px-4 max-w-7xl mx-auto border-t border-hairline">
      <h2 className="font-display text-3xl font-bold mb-10 text-center">Use Cases</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cases.map((c, i) => (
          <div key={i} className="p-6 bg-surface border border-hairline rounded-base flex flex-col hover:-translate-y-1 hover:border-neutral-700 hover:bg-neutral-900/60 hover:shadow-[0_0_20px_rgba(16,185,129,0.1)] transition-all duration-300 group">
            <div className="w-8 h-8 rounded bg-emerald-950/40 border border-emerald-800/50 flex items-center justify-center mb-4">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
            </div>
            <h3 className="font-body font-bold text-ink mb-2 group-hover:text-emerald-400 transition-colors">{c.title}</h3>
            <p className="font-body text-slate text-sm group-hover:text-neutral-300 transition-colors">{c.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
