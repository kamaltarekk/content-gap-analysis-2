import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Comparison, ComparisonCell } from '../types'
import { StatusBadge } from './StatusBadge'

function cellText(cell: ComparisonCell | undefined): string {
  if (!cell || cell.presence_status === null) return '—'
  if (cell.computed_score !== null) return String(cell.computed_score)
  return '·' // present but not scored (unknown / SE01)
}

function cellTitle(cell: ComparisonCell | undefined): string {
  if (!cell || cell.presence_status === null) return 'no assessment'
  return [cell.presence_status, cell.note].filter(Boolean).join(' · ')
}

export function ComparisonMatrix({ projectId }: { projectId: string }) {
  const [data, setData] = useState<Comparison | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.comparison(projectId).then(setData).catch((e) => setError(String(e)))
  }, [projectId])

  if (error) return <section className="panel"><h2>Competitor comparison</h2><p className="error">{error}</p></section>
  if (!data) return <section className="panel"><h2>Competitor comparison</h2><p>Loading…</p></section>

  return (
    <section className="panel">
      <div className="section-title"><h2>Competitor comparison</h2></div>
      <p className="muted">
        A total requires at least {data.min_pages} collected pages — a single homepage cannot be scored
        as comparable. Absences are “not found within the analyzed sample”.
      </p>
      {data.entities.length === 0 ? (
        <p>No entities yet.</p>
      ) : (
        <div className="matrix-scroll">
          <table className="matrix">
            <thead>
              <tr>
                <th className="sticky-col">Entity</th>
                {data.elements.map((el) => (
                  <th key={el.canonical_element_id} title={el.canonical_key}>{el.canonical_element_id}</th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {data.entities.map((row) => (
                <tr key={row.entity_id}>
                  <th className="sticky-col" dir="auto">
                    <div>{row.name}</div>
                    <small>{row.entity_type} · {row.page_count}p</small>
                    <div><StatusBadge value={row.comparable_status} /></div>
                  </th>
                  {data.elements.map((el) => {
                    const cell = row.cells[el.canonical_element_id]
                    return (
                      <td key={el.canonical_element_id} title={cellTitle(cell)} className={cell?.note ? 'absent' : ''}>
                        {cellText(cell)}
                      </td>
                    )
                  })}
                  <td className="total">
                    {row.total === null ? (
                      <span className="blocked" title={row.total_blocked_reason ?? ''}>blocked</span>
                    ) : (
                      row.total
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
