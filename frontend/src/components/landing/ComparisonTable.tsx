export function ComparisonTable() {
  const comparisons = [
    { category: 'AI IDEs', difference: 'Focused on code generation; AgentOS is a general-purpose digital surrogate.' },
    { category: 'MCP', difference: 'A protocol for tool access; AgentOS is the runtime and memory environment that uses it.' },
    { category: 'Code Agents', difference: 'Build software; AgentOS manages your daily workflows, tasks, and information.' },
    { category: 'Chatbots', difference: 'Wait for prompts; AgentOS acts autonomously in the background.' },
    { category: 'Automation tools', difference: 'Require rigid logic chains; AgentOS reasons through fuzzy or broken workflows.' }
  ]

  return (
    <section className="py-20 px-4 max-w-5xl mx-auto border-t border-hairline">
      <h2 className="font-display text-3xl font-bold mb-10 text-center">System Context</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[600px]">
          <thead>
            <tr className="border-b-2 border-ink">
              <th className="pb-4 font-mono text-xs uppercase text-slate w-1/3">Alternative</th>
              <th className="pb-4 font-mono text-xs uppercase text-slate w-2/3">AgentOS Difference</th>
            </tr>
          </thead>
          <tbody>
            {comparisons.map((c, i) => (
              <tr key={i} className="border-b border-hairline hover:bg-surface transition-colors group">
                <td className="py-5 font-body font-bold text-ink">{c.category}</td>
                <td className="py-5 font-body text-slate group-hover:text-ink transition-colors">{c.difference}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
