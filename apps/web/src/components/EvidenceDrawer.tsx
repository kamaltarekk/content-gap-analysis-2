import type { Evidence } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  evidence: Evidence[]
  urls: Record<string, string>
}

export function EvidenceDrawer({ open, onClose, evidence, urls }: Props) {
  if (!open) return null
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(event) => event.stopPropagation()}>
        <button onClick={onClose}>Close</button>
        <h2>Evidence</h2>
        {evidence.length === 0 ? <p>No linked evidence.</p> : evidence.map((item) => {
          const url = urls[item.content_item_id]
          return (
            <article key={item.id} className="evidence-card" dir="auto">
              <strong>{item.review_status}</strong>
              <blockquote>{item.verbatim_text}</blockquote>
              <p>{item.normalized_summary}</p>
              {url && <a href={url} target="_blank" rel="noreferrer">source</a>}
            </article>
          )
        })}
      </aside>
    </div>
  )
}
