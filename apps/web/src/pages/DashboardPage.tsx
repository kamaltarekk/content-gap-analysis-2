import { FormEvent, useEffect, useState } from 'react'
import { EvidenceDrawer } from '../components/EvidenceDrawer'
import { StatusBadge } from '../components/StatusBadge'
import { api } from '../lib/api'
import type { Dashboard } from '../types'

export function DashboardPage({ projectId }: { projectId: string }) {
  const [data, setData] = useState<Dashboard | null>(null)
  const [brandEntityId, setBrandEntityId] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [drawer, setDrawer] = useState(false)
  const [message, setMessage] = useState('')

  async function refresh() {
    const next = await api.dashboard(projectId)
    setData(next)
    const brand = next.entities.find((entity) => entity.entity_type === 'brand')
    if (brand) setBrandEntityId(brand.id)
  }

  useEffect(() => { void refresh() }, [projectId])

  async function addBrand() {
    const entity = await api.createEntity(projectId, { name: data?.project.brand_name, entity_type: 'brand' })
    setBrandEntityId(entity.id)
    await refresh()
  }

  async function addSource(event: FormEvent) {
    event.preventDefault()
    if (!brandEntityId) return
    await api.createSource(projectId, { entity_id: brandEntityId, source_type: 'website', url: sourceUrl, max_items: 20 })
    setSourceUrl('')
    await refresh()
  }

  async function run(action: () => Promise<unknown>, label: string) {
    setMessage(label)
    try { await action(); await refresh() } finally { setMessage('') }
  }

  if (!data) return <main className="shell">Loading…</main>

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <h1 dir="auto">{data.project.brand_name}</h1>
          <p dir="auto">{data.project.target_buying_decision}</p>
        </div>
        <StatusBadge value={data.project.status} />
      </header>

      <section className="metrics">
        <article><strong>{data.sources.length}</strong><span>Sources</span></article>
        <article><strong>{data.content_items.length}</strong><span>Content items</span></article>
        <article><strong>{data.evidence.length}</strong><span>Evidence</span></article>
        <article><strong>{data.gaps.length}</strong><span>Gap candidates</span></article>
      </section>

      <section className="panel">
        <h2>Sources</h2>
        {!brandEntityId && <button onClick={addBrand}>Create brand entity</button>}
        {brandEntityId && (
          <form className="inline-form" onSubmit={addSource}>
            <input type="url" placeholder="Exact website URL" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} required />
            <button>Add source</button>
          </form>
        )}
        <div className="list">
          {data.sources.map((source) => (
            <article key={source.id}>
              <a href={source.url} target="_blank" rel="noreferrer">{source.url}</a>
              <StatusBadge value={source.status} />
              <small>{source.accessible_count} accessible / {source.failed_count} failed</small>
            </article>
          ))}
        </div>
        <div className="actions">
          <button disabled={!data.sources.length || !!message} onClick={() => run(() => api.collect(projectId), 'Starting collection…')}>Collect</button>
          <button disabled={data.project.status !== 'COLLECTED' || !!message} onClick={() => run(() => api.prepareReview(projectId), 'Preparing review…')}>Prepare review</button>
          <button disabled={data.project.status !== 'READY_FOR_REVIEW' || !!message} onClick={() => run(() => api.analyze(projectId), 'Starting analysis…')}>Approve & analyze</button>
          <button onClick={refresh}>Refresh</button>
        </div>
        {message && <p>{message}</p>}
      </section>

      <section className="panel">
        <div className="section-title"><h2>Sales Elements</h2><button onClick={() => setDrawer(true)}>Evidence drawer</button></div>
        <div className="element-grid">
          {data.sales_elements.length === 0 ? <p>Run analysis to create candidate assessments.</p> : data.sales_elements.map((item) => (
            <article key={item.id}>
              <strong>{item.canonical_element_id}</strong>
              <h3 dir="auto">{item.canonical_key}</h3>
              <StatusBadge value={item.presence_status} />
              <p>Score: {item.computed_score ?? '—'}</p>
              <small>{item.confidence} confidence · {item.review_status}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Gap candidates</h2>
        <div className="list">
          {data.gaps.length === 0 ? <p>No gap candidates yet.</p> : data.gaps.map((gap) => (
            <article key={gap.id} dir="auto">
              <div><strong>{gap.title}</strong><p>{gap.root_cause}</p></div>
              <div><StatusBadge value={gap.status} /><small>{gap.severity} severity · {gap.confidence} confidence</small></div>
            </article>
          ))}
        </div>
      </section>

      <EvidenceDrawer open={drawer} onClose={() => setDrawer(false)} evidence={data.evidence} />
    </main>
  )
}
