import { useState } from 'react'
import { api } from '../lib/api'
import type { Evidence, ReviewStatus } from '../types'
import { StatusBadge } from './StatusBadge'

export function ReviewQueue({ evidence, onReviewed }: { evidence: Evidence[]; onReviewed: () => Promise<void> | void }) {
  const [reviewer, setReviewer] = useState('user')
  const [editing, setEditing] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState('')

  const pending = evidence.filter((item) => item.review_status === 'pending_review')
  const reviewed = evidence.filter((item) => item.review_status !== 'pending_review')

  async function decide(item: Evidence, status: ReviewStatus, editedValue?: string) {
    if (reviewer.trim() === '') {
      setError('A reviewer name is required to record a decision.')
      return
    }
    setError('')
    setBusy(item.id)
    try {
      await api.reviewEvidence(item.id, { status, reviewer, edited_value: editedValue })
      setEditing((prev) => {
        const next = { ...prev }
        delete next[item.id]
        return next
      })
      await onReviewed()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  if (evidence.length === 0) {
    return (
      <section className="panel">
        <h2>Review queue</h2>
        <p>No candidate evidence yet. Run “Prepare review” after collection to populate the queue.</p>
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="section-title">
        <h2>Review queue</h2>
        <label className="reviewer-field">
          <span>Reviewer</span>
          <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} required />
        </label>
      </div>
      <p className="muted">
        {pending.length} pending · {reviewed.length} reviewed. Candidates are never auto-approved.
      </p>
      {error && <p className="error">{error}</p>}

      <div className="list">
        {[...pending, ...reviewed].map((item) => {
          const isEditing = item.id in editing
          return (
            <article key={item.id} className="review-card" dir="auto">
              <div className="review-tags">
                <StatusBadge value={item.category} />
                <StatusBadge value={item.finding_status} />
                <StatusBadge value={item.review_status} />
              </div>
              <blockquote>{item.verbatim_text}</blockquote>
              {isEditing ? (
                <textarea
                  rows={2}
                  dir="auto"
                  value={editing[item.id]}
                  onChange={(e) => setEditing((prev) => ({ ...prev, [item.id]: e.target.value }))}
                />
              ) : (
                <p className="muted">{item.normalized_summary}</p>
              )}
              {item.reviewer && (
                <small>
                  Decided by {item.reviewer}
                  {item.reviewed_at ? ` · ${new Date(item.reviewed_at).toLocaleString()}` : ''}
                </small>
              )}

              <div className="review-actions">
                {isEditing ? (
                  <>
                    <button disabled={busy === item.id} onClick={() => decide(item, 'approved', editing[item.id])}>
                      Save &amp; approve
                    </button>
                    <button
                      className="ghost"
                      disabled={busy === item.id}
                      onClick={() =>
                        setEditing((prev) => {
                          const next = { ...prev }
                          delete next[item.id]
                          return next
                        })
                      }
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button disabled={busy === item.id} onClick={() => decide(item, 'approved')}>Approve</button>
                    <button
                      className="ghost"
                      disabled={busy === item.id}
                      onClick={() => setEditing((prev) => ({ ...prev, [item.id]: item.normalized_summary }))}
                    >
                      Edit
                    </button>
                    <button className="ghost" disabled={busy === item.id} onClick={() => decide(item, 'hypothesis')}>
                      Hypothesis
                    </button>
                    <button className="danger" disabled={busy === item.id} onClick={() => decide(item, 'rejected')}>
                      Reject
                    </button>
                  </>
                )}
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
