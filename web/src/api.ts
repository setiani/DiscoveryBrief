export function awareMeeting(date: string, time: string, timezone: string): string {
  const target = `${date}T${time}:00`;
  const wall = Date.parse(target + 'Z');
  if (!Number.isFinite(wall)) throw new Error('Invalid meeting time');
  const formatter = new Intl.DateTimeFormat('sv-SE', {timeZone: timezone, year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit', hourCycle:'h23'});
  const local = (instant: number) => formatter.format(new Date(instant)).replace(' ', 'T');
  let instant = wall;
  for (let i = 0; i < 4; i++) instant += wall - Date.parse(local(instant) + 'Z');
  if (local(instant) !== target) throw new Error('This local time does not exist in the selected timezone');
  const minutes = Math.round((wall - instant) / 60000);
  return target + (minutes < 0 ? '-' : '+') + String(Math.floor(Math.abs(minutes)/60)).padStart(2,'0') + ':' + String(Math.abs(minutes)%60).padStart(2,'0');
}

export class Submission {
  private signature = '';
  private id = '';
  request(payload: Record<string, unknown>) {
    const signature = JSON.stringify(payload);
    if (signature !== this.signature || !this.id) { this.signature = signature; this.id = crypto.randomUUID(); }
    return {...payload, client_request_id: this.id};
  }
  complete() { this.id = ''; this.signature = ''; }
}

// Canonical API uses a Brief envelope; the renderer displays only selected IDs.
export function reportView(bundle: any): any {
  if (!bundle.brief) return bundle;
  const b = bundle.brief;
  const evidence = new Map<string, any>(bundle.evidence.map((e: any) => [e.evidence_id, e]));
  return {...b, metrics: bundle.metrics, warnings: bundle.warnings, synthetic: bundle.synthetic,
    original_metrics:bundle.original_metrics,original_research_mode:bundle.original_research_mode,
    claims: bundle.claims.filter((c: any) => b.finding_ids.includes(c.claim_id)).map((c: any) => ({...c, evidence:c.evidence_ids.map((id: string) => evidence.get(id))})),
    requirements: bundle.requirements.filter((r: any) => b.requirement_ids.includes(r.requirement_id)),
    sources: bundle.sources.map((s: any) => ({...s, url:s.canonical_url})),
  };
}

export const terminal = (status: string) => ['completed','needs_input','failed','cancelled'].includes(status);

export function safeLink(url: string): string | null {
  try { const parsed = new URL(url); return ['http:', 'https:'].includes(parsed.protocol) && !parsed.username && !parsed.password ? parsed.href : null; } catch { return null; }
}
