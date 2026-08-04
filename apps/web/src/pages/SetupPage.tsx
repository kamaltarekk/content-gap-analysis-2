import { useMemo, useState } from 'react'
import { api } from '../lib/api'
import type { Bottleneck, Project } from '../types'

type FormState = {
  name: string
  target_buying_decision: string
  market: string
  purchase_type: string
  brand_name: string
  product_or_service: string
  primary_segment: string
  primary_bottleneck: Bottleneck
}

const INITIAL: FormState = {
  name: 'New diagnosis',
  target_buying_decision: '',
  market: 'Egypt',
  purchase_type: 'first_purchase',
  brand_name: '',
  product_or_service: '',
  primary_segment: '',
  primary_bottleneck: 'unknown',
}

const PURCHASE_TYPES = ['first_purchase', 'considered', 'repeat', 'subscription', 'high_ticket']
const BOTTLENECKS: Bottleneck[] = ['unknown', 'attention', 'desire', 'persuasion', 'friction']

// Each step lists the required text fields it owns (bottleneck always has a valid default).
const STEPS: { title: string; hint: string; fields: (keyof FormState)[] }[] = [
  {
    title: 'Buying decision',
    hint: 'One diagnosis maps to one buying decision.',
    fields: ['name', 'target_buying_decision', 'market', 'purchase_type'],
  },
  {
    title: 'Offer & segment',
    hint: 'Describe the brand, its offer, and the one primary segment.',
    fields: ['brand_name', 'product_or_service', 'primary_segment'],
  },
  {
    title: 'Primary bottleneck',
    hint: 'If you are not sure, keep “unknown”. It stays allowed but flagged conditional.',
    fields: [],
  },
]

const LABELS: Record<keyof FormState, string> = {
  name: 'Project name',
  target_buying_decision: 'Target buying decision',
  market: 'Market',
  purchase_type: 'Purchase type',
  brand_name: 'Brand name',
  product_or_service: 'Product or service',
  primary_segment: 'Primary segment',
  primary_bottleneck: 'Primary bottleneck',
}

export function SetupPage({ onCreated }: { onCreated: (project: Project) => void }) {
  const [form, setForm] = useState<FormState>(INITIAL)
  const [step, setStep] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const current = STEPS[step]
  const isLast = step === STEPS.length - 1

  const stepIncomplete = useMemo(
    () => current.fields.filter((field) => String(form[field]).trim() === ''),
    [current, form],
  )

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function next() {
    if (stepIncomplete.length > 0) {
      setError(`Please complete: ${stepIncomplete.map((f) => LABELS[f]).join(', ')}`)
      return
    }
    setError('')
    setStep((s) => Math.min(s + 1, STEPS.length - 1))
  }

  async function submit() {
    setBusy(true)
    setError('')
    try {
      onCreated(await api.createProject(form))
    } catch (e) {
      setError(String(e))
      setBusy(false)
    }
  }

  return (
    <main className="shell narrow">
      <h1>Guided setup</h1>
      <p>Create one diagnosis around one buying decision and one primary segment.</p>

      <ol className="wizard-steps">
        {STEPS.map((s, index) => (
          <li key={s.title} className={index === step ? 'active' : index < step ? 'done' : ''}>
            <span className="wizard-index">{index + 1}</span>
            <span dir="auto">{s.title}</span>
          </li>
        ))}
      </ol>

      <section className="panel">
        <h2 dir="auto">{current.title}</h2>
        <p dir="auto">{current.hint}</p>

        <div className="form-grid">
          {step === 0 && (
            <>
              <Field label={LABELS.name} value={form.name} onChange={(v) => set('name', v)} />
              <label>
                <span>{LABELS.target_buying_decision}</span>
                <textarea
                  dir="auto"
                  rows={3}
                  value={form.target_buying_decision}
                  onChange={(e) => set('target_buying_decision', e.target.value)}
                  required
                />
              </label>
              <Field label={LABELS.market} value={form.market} onChange={(v) => set('market', v)} />
              <label>
                <span>{LABELS.purchase_type}</span>
                <select value={form.purchase_type} onChange={(e) => set('purchase_type', e.target.value)}>
                  {PURCHASE_TYPES.map((t) => (
                    <option key={t} value={t}>{t.replaceAll('_', ' ')}</option>
                  ))}
                </select>
              </label>
            </>
          )}

          {step === 1 && (
            <>
              <Field label={LABELS.brand_name} value={form.brand_name} onChange={(v) => set('brand_name', v)} />
              <Field label={LABELS.product_or_service} value={form.product_or_service} onChange={(v) => set('product_or_service', v)} />
              <Field label={LABELS.primary_segment} value={form.primary_segment} onChange={(v) => set('primary_segment', v)} />
            </>
          )}

          {step === 2 && (
            <>
              <label>
                <span>{LABELS.primary_bottleneck}</span>
                <select
                  value={form.primary_bottleneck}
                  onChange={(e) => set('primary_bottleneck', e.target.value as Bottleneck)}
                >
                  {BOTTLENECKS.map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </label>
              {form.primary_bottleneck === 'unknown' && (
                <p className="notice" dir="auto">
                  Bottleneck is unresolved. Collection can still start, but the project will be flagged
                  conditional until you resolve it.
                </p>
              )}
              <ReviewSummary form={form} />
            </>
          )}
        </div>

        {error && <p className="error">{error}</p>}

        <div className="actions">
          <button type="button" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0 || busy}>
            Back
          </button>
          {isLast ? (
            <button type="button" onClick={submit} disabled={busy}>
              {busy ? 'Creating…' : 'Create project'}
            </button>
          ) : (
            <button type="button" onClick={next} disabled={busy}>
              Next
            </button>
          )}
        </div>
      </section>
    </main>
  )
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label>
      <span>{label}</span>
      <input dir="auto" value={value} onChange={(e) => onChange(e.target.value)} required />
    </label>
  )
}

function ReviewSummary({ form }: { form: FormState }) {
  return (
    <div className="review">
      <h3>Review</h3>
      <dl>
        {(Object.keys(form) as (keyof FormState)[]).map((key) => (
          <div key={key}>
            <dt>{LABELS[key]}</dt>
            <dd dir="auto">{String(form[key])}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
