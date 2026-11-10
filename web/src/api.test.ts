import {describe, expect, it} from 'vitest';
import {awareMeeting, reportView, safeLink, Submission, terminal} from './api';

describe('request and output boundaries',()=>{
  it('serializes IANA offsets including daylight saving',()=>{
    expect(awareMeeting('2026-11-12','10:30','Asia/Jakarta')).toBe('2026-11-12T10:30:00+07:00');
    expect(awareMeeting('2026-07-12','10:30','America/New_York')).toBe('2026-07-12T10:30:00-04:00');
    expect(()=>awareMeeting('2026-03-08','02:30','America/New_York')).toThrow();
  });
  it('reuses a request ID after lost response; editing or completion creates a new one',()=>{
    const submission=new Submission();
    const first=submission.request({company:'A'}).client_request_id;
    expect(submission.request({company:'A'}).client_request_id).toBe(first);
    expect(submission.request({company:'B'}).client_request_id).not.toBe(first);
    submission.complete(); expect(submission.request({company:'A'}).client_request_id).not.toBe(first);
  });
  it('renders selected IDs while retaining the full approved ledger',()=>{
    const bundle={brief:{finding_ids:['c1'],requirement_ids:[],questions:[]},claims:[{claim_id:'c1',evidence_ids:['e1']},{claim_id:'c2',evidence_ids:[]}],requirements:[],sources:[{source_id:'s1',canonical_url:'https://example.com'}],evidence:[{evidence_id:'e1',source_id:'s1',quote:'literal'}]};
    const view=reportView(bundle); expect(view.claims).toHaveLength(1); expect(view.claims[0].evidence[0].quote).toBe('literal'); expect(bundle.claims).toHaveLength(2);
  });
  it('stops polling on every terminal state and rejects active URLs',()=>{
    for(const status of ['completed','failed','needs_input','cancelled']) expect(terminal(status)).toBe(true);
    expect(terminal('running')).toBe(false); expect(safeLink('javascript:alert(1)')).toBeNull(); expect(safeLink('https://u:p@example.com')).toBeNull();
  });
});
