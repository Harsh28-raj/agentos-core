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
          <div key={i} className="p-6 bg-surface border border-hairline rounded-base flex flex-col hover:border-signal transition-colors">
            <h3 className="font-body font-bold text-ink mb-2">{c.title}</h3>
            <p className="font-body text-slate text-sm">{c.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
