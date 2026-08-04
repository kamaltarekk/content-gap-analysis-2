import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import type { Gap } from '../types'
import { StatusBadge } from './StatusBadge'

const GAP_TYPES = ['all', 'sales_element_gap', 'comparative_gap', 'non_content_blocker']

export function GapExplorer({ projectId }: { projectId: string }) {
  const [gaps, setGaps] = useState<Gap[]>([])
  const [typeFilter, setTypeFilter] = useState('all')
  const [reviewer, setReviewer] = useState('user')
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState('')

  async function refresh() {
    setGaps(await api.gaps(projectId))
  }

  useEffect(() => { void refresh() }, [projectId])

  const visible = useMemo(
    () => (typeFilter === 'all' ? gaps : gaps.filter((g) => g.gap_type === typeFilter)),
    [gaps, typeFilter],
  )

  async function decide(gap: Gap, status: 'confirmed' | 'rejected') {
    if (reviewer.trim() === '') {
      setError('A reviewer name is required to record a decision.')
      return
    }
    setError('')
    setBusy(gap.id)
    try {
      await api.reviewGap(gap.id, { status, reviewer })
      await refresh()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="panel">
      <div className="section-title">
        <h2>Gap explorer</h2>
        <label className="reviewer-field">
          <span>Reviewer</span>
          <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} required />
        </label>
      </div>
      <p className="muted">
        Competitor presence alone never confirms a gap, and non-content blockers stay separate.
        A gap is confirmed only by a recorded review decision.
      </p>
      <div className="inline-form">
        <label>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            {GAP_TYPES.map((t) => <option key={t} value={t}>{t.replaceAll('_', ' ')}</option>)}
          </select>
        </label>
      </div>
      {error && <p className="error">{error}</p>}

      <div className="list">
        {visible.length === 0 ? <p>No gaps for this filter.</p> : visible.map((gap) => (
          <article key={gap.id} className="review-card" dir="auto">
            <div className="review-tags">
              <StatusBadge value={gap.gap_type} />
              <StatusBadge value={gap.status} />
              <span className="badge">severity: {gap.severity}</span>
              <span className="badge">confidence: {gap.confidence}</span>
              <StatusBadge value={gap.root_cause} />
            </div>
            <strong>{gap.title}</strong>
            {gap.alternative_explanations.length > 0 && (
              <ul className="muted">
                {gap.alternative_explanations.map((alt, i) => <li key={i} dir="auto">{alt}</li>)}
              </ul>
            )}
            {gap.reviewer && (
              <small>
                {gap.status} by {gap.reviewer}
                {gap.reviewed_at ? ` · ${new Date(gap.reviewed_at).toLocaleString()}` : ''}
              </small>
            )}
            <div className="review-actions">
              <button disabled={busy === gap.id} onClick={() => decide(gap, 'confirmed')}>Confirm</button>
              <button className="danger" disabled={busy === gap.id} onClick={() => decide(gap, 'rejected')}>Reject</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
