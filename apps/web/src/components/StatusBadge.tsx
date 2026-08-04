export function StatusBadge({ value }: { value: string }) {
  return <span className="badge" dir="auto">{value.replaceAll('_', ' ')}</span>
}
