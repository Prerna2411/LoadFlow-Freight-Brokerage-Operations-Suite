export function StatusPill({ label, danger = false }: { label: string; danger?: boolean }) {
  return <span className={`pill ${danger ? 'danger' : 'good'}`}>{label}</span>;
}
