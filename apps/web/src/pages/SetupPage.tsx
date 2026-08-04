import { FormEvent, useState } from 'react'
import { api } from '../lib/api'
import type { Project } from '../types'

export function SetupPage({ onCreated }: { onCreated: (project: Project) => void }) {
  const [form, setForm] = useState({
    name: 'New diagnosis',
    brand_name: '',
    market: 'Egypt',
    product_or_service: '',
    target_buying_decision: '',
    purchase_type: 'first_purchase',
    primary_segment: '',
    primary_bottleneck: 'unknown',
  })
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    try {
      setError('')
      onCreated(await api.createProject(form))
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <main className="shell narrow">
      <h1>Guided setup</h1>
      <p>Create one diagnosis around one buying decision and one primary segment.</p>
      <form onSubmit={submit} className="form-grid">
        {Object.entries(form).map(([key, value]) => (
          <label key={key}>
            <span>{key.replaceAll('_', ' ')}</span>
            {key === 'primary_bottleneck' ? (
              <select value={value} onChange={(e) => setForm({ ...form, [key]: e.target.value })}>
                <option value="unknown">Unknown</option>
                <option value="attention">Attention</option>
                <option value="desire">Desire</option>
                <option value="persuasion">Persuasion</option>
                <option value="friction">Friction</option>
              </select>
            ) : (
              <input dir="auto" value={value} onChange={(e) => setForm({ ...form, [key]: e.target.value })} required />
            )}
          </label>
        ))}
        {error && <p className="error">{error}</p>}
        <button type="submit">Create project</button>
      </form>
    </main>
  )
}
