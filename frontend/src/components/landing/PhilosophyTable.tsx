export function PhilosophyTable() {
  const components = [
    { traditional: 'Processor', agentOS: 'LLM', role: 'Reasoning and decision making' },
    { traditional: 'RAM', agentOS: 'Redis', role: 'Short-term context window and session state' },
    { traditional: 'Hard Drive', agentOS: 'ChromaDB & Postgres', role: 'Episodic memory and long-term storage' },
    { traditional: 'Applications', agentOS: 'Tools', role: 'Capabilities like search, calendar, and weather' },
    { traditional: 'Kernel', agentOS: 'LangGraph', role: 'ReAct loop managing the execution flow' }
  ]

  return (
    <section className="py-20 px-4 max-w-5xl mx-auto border-t border-hairline">
      <h2 className="font-display text-3xl font-bold mb-10 text-center">A New Operating Paradigm</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[600px]">
          <thead>
            <tr className="border-b-2 border-ink">
              <th className="pb-4 font-mono text-xs uppercase text-slate w-1/3">Traditional OS</th>
              <th className="pb-4 font-mono text-xs uppercase text-slate w-1/3">AgentOS</th>
              <th className="pb-4 font-mono text-xs uppercase text-slate w-1/3">Role</th>
            </tr>
          </thead>
          <tbody>
            {components.map((comp, i) => (
              <tr key={i} className="border-b border-hairline hover:bg-surface transition-colors group">
                <td className="py-5 font-body font-medium text-slate group-hover:text-ink transition-colors">{comp.traditional}</td>
                <td className="py-5 font-body font-bold text-ink">{comp.agentOS}</td>
                <td className="py-5 font-body text-slate">{comp.role}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
