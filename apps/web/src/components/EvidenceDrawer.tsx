interface Props {
  open: boolean
  onClose: () => void
  evidence: Array<{ id: string; verbatim_text: string; normalized_summary: string; review_status: string }>
}

export function EvidenceDrawer({ open, onClose, evidence }: Props) {
  if (!open) return null
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(event) => event.stopPropagation()}>
        <button onClick={onClose}>Close</button>
        <h2>Evidence</h2>
        {evidence.length === 0 ? <p>No linked evidence.</p> : evidence.map((item) => (
          <article key={item.id} className="evidence-card" dir="auto">
            <strong>{item.review_status}</strong>
            <blockquote>{item.verbatim_text}</blockquote>
            <p>{item.normalized_summary}</p>
          </article>
        ))}
      </aside>
    </div>
  )
}
