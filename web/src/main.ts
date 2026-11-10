import './style.css';
import {awareMeeting, reportView, Submission} from './api';
import {dictionary, type Key, type Language} from './i18n';
let uiLanguage: Language = 'en';
const t = (key: Key) => dictionary[uiLanguage][key];
const submission = new Submission();
const app = document.querySelector<HTMLDivElement>('#app');
if (!app) throw new Error('App container missing');
app.innerHTML = `<main><header><span class="mark">D<span>✳</span></span><span class="brand">DiscoveryBrief</span><span class="badge">WORKSPACE</span></header><section class="hero"><div><p class="eyebrow">PERSIAPAN MEETING YANG LEBIH TERARAH</p><h1>Mulai percakapan<br><em>dengan konteks.</em></h1><p>Ubah riset perusahaan dan kebutuhan pelanggan menjadi pertanyaan discovery yang tepat, dengan bukti yang dapat diperiksa.</p></div></section><section class="card"><div class="section-head"><div><p class="eyebrow">01 / KONTEKS MEETING</p><h2>Siapkan brief baru</h2><p>Isi detail dasar untuk memulai persiapan.</p></div><span class="pill">Draft awal</span></div><form id="brief-form"><div class="grid"><label>Nama perusahaan <span>*</span><input name="company_name" placeholder="Contoh: Sagara Insurance" required minlength="2" maxlength="160"></label><label>Domain perusahaan <small>opsional</small><input name="company_domain" placeholder="contoh.com"></label><label>Tanggal meeting <span>*</span><input name="date" type="date" required></label><label>Waktu meeting (WIB) <span>*</span><input name="time" type="time" required></label></div><label>Tujuan meeting <small>opsional</small><input name="meeting_goal" maxlength="500" placeholder="Contoh: klarifikasi scope dan integrasi portal"></label><details><summary>Tambahkan konteks RFP dan catatan <span>+</span></summary><label>Potongan RFP <small>opsional · teks saja</small><textarea name="rfp_text" maxlength="12000" rows="5" placeholder="Tempelkan kebutuhan yang ingin diklarifikasi"></textarea></label><label>Catatan meeting <small>opsional</small><textarea name="notes" maxlength="4000" rows="3"></textarea></label><p class="notice">RFP dan catatan dapat diproses oleh penyedia model yang dikonfigurasi. Informasi ini tidak dimasukkan ke pencarian publik.</p></details><div class="actions"><p><span class="dot"></span> Aplikasi dalam tahap pengembangan</p><button disabled type="submit">Buat discovery brief <span>↗</span></button></div></form></section><footer><span>DISCOVERYBRIEF / EVIDENCE FIRST</span><span>Dirancang untuk percakapan yang lebih bermakna.</span></footer></main>`;

const form = document.querySelector<HTMLFormElement>('#brief-form');
const formCard = document.querySelector<HTMLElement>('.card');
if (form && formCard) {
  const languageLabel = document.createElement('label');
  languageLabel.textContent = 'Interface ';
  const languageSelect = document.createElement('select');
  for (const [value, title] of [['id','Indonesia'],['en','English']]) {
    const option = document.createElement('option'); option.value = value; option.textContent = title; languageSelect.append(option);
  }
  languageSelect.value = uiLanguage;
  languageLabel.append(languageSelect); document.querySelector('header')!.append(languageLabel);
  const translate = () => {
    document.documentElement.lang = uiLanguage;
    const replacements: Record<string, string> = {
      'Siapkan brief baru': t('form'), 'Nama perusahaan': t('company'), 'Domain perusahaan':t('domain'),
      'Tanggal meeting':t('date'),'Waktu meeting (WIB)':t('time'),'Tujuan meeting':t('goal'),
      'Tambahkan konteks RFP dan catatan':t('optional'),'Potongan RFP':t('rfp'),'Catatan meeting':t('notes'),
      'Buat discovery brief':t('submit'),'Jenis meeting':t('type'),'Bahasa laporan':t('reportLanguage'),
      'Negara':t('country'),'Industri':t('industry'),'Peserta, satu per baris (nama | jabatan) · opsional':t('participants'),
      'Topik riset publik':t('topics'),'Lihat contoh sintetis':t('sample'),'Jalankan contoh offline':t('runSample'),
      'PERSIAPAN MEETING YANG LEBIH TERARAH':t('eyebrow'),'Isi detail dasar untuk memulai persiapan.':t('subtitle'),
      'Zona waktu (IANA)':t('timezone'),'opsional':uiLanguage==='en'?'optional':'opsional',
      '01 / KONTEKS MEETING':uiLanguage==='en'?'01 / MEETING CONTEXT':'01 / KONTEKS MEETING',
      'Ubah riset perusahaan dan kebutuhan pelanggan menjadi pertanyaan discovery yang tepat, dengan bukti yang dapat diperiksa.':t('subtitle'),
      'Riset live menggunakan Tavily dan model melalui Bifrost':uiLanguage==='en'?'Live research uses Tavily and inference through Bifrost':'Riset live menggunakan Tavily dan model melalui Bifrost',
      'Aplikasi dalam tahap pengembangan':t('unavailable'),
      'Draft awal':uiLanguage==='en'?'Initial draft':'Draft awal',
      'Dirancang untuk percakapan yang lebih bermakna.':uiLanguage==='en'?'Designed for more meaningful conversations.':'Dirancang untuk percakapan yang lebih bermakna.',
      'Klarifikasi RFP':uiLanguage==='en'?'RFP clarification':'Klarifikasi RFP',
      'Kemitraan':uiLanguage==='en'?'Partnership':'Kemitraan',
      'pilih maksimal tiga':uiLanguage==='en'?'select up to three':'pilih maksimal tiga',
      'Integrasi':uiLanguage==='en'?'Integration':'Integrasi',
      'Identitas / SSO':uiLanguage==='en'?'Identity / SSO':'Identitas / SSO',
      'Pencarian':uiLanguage==='en'?'Search':'Pencarian',
      'opsional · teks saja':uiLanguage==='en'?'optional · plain text':'opsional · teks saja',
    };
    app.querySelectorAll<HTMLElement>('[data-i18n]').forEach(element => { element.textContent=t(element.dataset.i18n as Key); });
    const walk = document.createTreeWalker(app, NodeFilter.SHOW_TEXT);
    const nodes: Text[] = []; while (walk.nextNode()) nodes.push(walk.currentNode as Text);
    for (const node of nodes) {
      if (node.parentElement?.closest('[data-generated]')) continue;
      const base = (node as any)._original ?? node.textContent?.trim(); (node as any)._original = base;
      if (base && replacements[base]) node.textContent = replacements[base];
      else {
        const key=(Object.keys(dictionary.id) as Key[]).find(key=>dictionary.id[key]===base || dictionary.en[key]===base);
        if(key) node.textContent=t(key);
      }
    }
    const notice=form.querySelector<HTMLElement>('.notice'); if (notice) notice.textContent=t('disclosure');
    const hero=document.querySelector<HTMLElement>('.hero h1'); if(hero) hero.textContent=t('title');
    const placeholders: Record<string, [string, string]> = {
      company_name:['Contoh: Sagara Insurance','Example: Sagara Insurance'],
      company_domain:['contoh.com','example.com'],
      meeting_goal:['Contoh: klarifikasi scope dan integrasi portal','Example: clarify portal scope and integrations'],
      rfp_text:['Tempelkan kebutuhan yang ingin diklarifikasi','Paste requirements you want to clarify'],
      participants:['Contoh: Rina | Head of IT','Example: Rina | Head of IT'],
    };
    for (const [name, values] of Object.entries(placeholders)) {
      const field=form.querySelector<HTMLInputElement | HTMLTextAreaElement>(`[name="${name}"]`);
      if(field) field.placeholder=values[uiLanguage==='en'?1:0];
    }
  };
  languageSelect.addEventListener('change',()=>{uiLanguage=languageSelect.value as Language; translate();});
  const timezoneLabel=document.createElement('label'); timezoneLabel.textContent=t('timezone');
  const timezone=document.createElement('input'); timezone.name='timezone'; timezone.value='Asia/Jakarta'; timezone.required=true;
  timezoneLabel.append(timezone); form.querySelector('.grid')!.append(timezoneLabel);
  const extra = document.createElement('div');
  extra.className = 'grid';
  extra.innerHTML = `<label>Jenis meeting<select name="meeting_type"><option value="discovery">Discovery</option><option value="rfp_clarification">Klarifikasi RFP</option><option value="partnership">Kemitraan</option></select></label><label>Bahasa laporan<select name="language"><option value="id">Bahasa Indonesia</option><option value="en">English</option></select></label><label>Negara <small>opsional</small><input name="company_country" maxlength="80"></label><label>Industri <small>opsional</small><input name="company_industry" maxlength="100"></label>`;
  form.insertBefore(extra, form.querySelector('details'));
  form.querySelector<HTMLSelectElement>('select[name="language"]')!.value = 'en';
  const additional = form.querySelector<HTMLDetailsElement>('details')!;
  const participantLabel = document.createElement('label');
  participantLabel.textContent = 'Peserta, satu per baris (nama | jabatan) · opsional';
  const participants = document.createElement('textarea');
  participants.name = 'participants'; participants.rows = 3;
  participants.placeholder = 'Contoh: Rina | Head of IT';
  participantLabel.append(participants);
  additional.insertBefore(participantLabel, additional.querySelector('.notice'));
  const topicGroup = document.createElement('fieldset');
  topicGroup.className = 'topics';
  topicGroup.innerHTML = `<legend>Topik riset publik <small>pilih maksimal tiga</small></legend><label><input type="checkbox" name="topic" value="portal"> Portal</label><label><input type="checkbox" name="topic" value="integration"> Integrasi</label><label><input type="checkbox" name="topic" value="identity"> Identitas / SSO</label><label><input type="checkbox" name="topic" value="search"> Pencarian</label><label><input type="checkbox" name="topic" value="devops"> DevOps</label>`;
  additional.insertBefore(topicGroup, additional.querySelector('.notice'));
  const submit = form.querySelector<HTMLButtonElement>('button[type=submit]')!;
  const statusText = form.querySelector<HTMLElement>('.actions p')!;
  const formError=document.createElement('p'); formError.id='form-error'; formError.setAttribute('role','alert'); formError.tabIndex=-1; form.append(formError);
  const resultView = document.createElement('section');
  resultView.className = 'sample';
  resultView.dataset.generated='true';
  resultView.hidden = true;
  resultView.setAttribute('aria-live', 'polite');
  formCard.after(resultView);
  fetch('/api/config/public').then(r => r.json()).then(config => {
    if (config.mode === 'public_demo') { formCard.hidden=true; const notice=document.createElement('p'); notice.className='notice'; notice.textContent=t('demo'); formCard.before(notice); }
    if (config.mode === 'local' && config.live_enabled === true) {
      submit.disabled = false;
      statusText.textContent = t('live');
    }
  }).catch(() => { submit.disabled = true; });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (submit.disabled || !form.reportValidity()) return;
    const fields = new FormData(form);
    const value = (key: string) => String(fields.get(key) || '').trim();
    const topics = fields.getAll('topic').map(String);
    const people = value('participants').split('\n').map(line => line.trim()).filter(Boolean).map(line => {
      const [name, ...role] = line.split('|');
      return {name: name.trim(), role: role.join('|').trim() || null};
    });
    if (topics.length > 3 || people.length > 6) {
      resultView.hidden = false;
      resultView.textContent = t('limit');
      return;
    }
    let meetingAt: string;
    try { meetingAt=awareMeeting(value('date'),value('time'),value('timezone')); }
    catch(error) { formError.textContent=error instanceof Error?error.message:t('failure'); formError.focus(); return; }
    const payload = submission.request({company_name: value('company_name'),
      company_domain: value('company_domain') || null, company_country: value('company_country') || null,
      company_industry: value('company_industry') || null, meeting_at: meetingAt,
      meeting_timezone: value('timezone'), meeting_type: value('meeting_type'), language: value('language'),
      meeting_goal: value('meeting_goal'), rfp_text: value('rfp_text'), notes: value('notes'),
      participants: people, public_topics: topics});
    submit.disabled = true;
    resultView.hidden = false;
    resultView.textContent = t('loading');
    let cancel: HTMLButtonElement | null = null;
    try {
      const response = await fetch('/api/runs', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const created = await response.json();
      if (!response.ok) throw new Error(created.error?.message || t('failure'));
      const runId = encodeURIComponent(created.run_id);
      const started=performance.now();
      resultView.replaceChildren();
      const progress = document.createElement('p');
      progress.textContent = t('queued');
      cancel = document.createElement('button');
      cancel.type = 'button'; cancel.className = 'secondary'; cancel.textContent = t('cancel');
      cancel.addEventListener('click', async () => {
        cancel!.disabled = true;
        await fetch(`/api/runs/${runId}/cancel`, {method:'POST'});
      });
      resultView.append(progress, cancel);
      let completed = false;
      let artifactNames: string[] = [];
      for (let attempt = 0; attempt < 240; attempt++) {
        const statusResponse = await fetch(`/api/runs/${runId}`);
        if (!statusResponse.ok) throw new Error(t('failure'));
        const status = await statusResponse.json();
        progress.textContent = `${dictionary[uiLanguage][status.stage as Key] || t('loading')} · ${t('elapsed')}: ${Math.round((performance.now()-started)/1000)}s`;
        if (status.status === 'completed') { completed = true; artifactNames = status.artifacts || []; break; }
        if (status.status === 'needs_input') {
          submission.complete();
          formError.textContent=t('ambiguity');
          for (const company of status.entity?.candidate_companies || []) {
            const button=document.createElement('button'); button.type='button'; button.className='secondary'; button.textContent=`${company.name} · ${company.domain}`;
            button.addEventListener('click',()=>{(form.elements.namedItem('company_domain') as HTMLInputElement).value=company.domain; (form.elements.namedItem('company_domain') as HTMLInputElement).focus();});
            formError.append(button);
          }
          formError.focus(); return;
        }
        if (status.status === 'cancelled') { submission.complete(); throw new Error(t('cancelled')); }
        if (status.status === 'failed') { submission.complete(); throw new Error(t('failure')); }
        await new Promise(resolve => window.setTimeout(resolve, 1500));
      }
      if (!completed) throw new Error(t('timeout'));
      const briefResponse = await fetch(`/api/runs/${runId}/brief`);
      if (!briefResponse.ok) throw new Error(t('failure'));
      const brief = reportView(await briefResponse.json());
      submission.complete();
      const ledger: any = await fetch(`/api/runs/${runId}/evidence`).then(r=>r.ok?r.json():{}).catch(()=>({}));
      resultView.replaceChildren();
      const title = document.createElement('h2'); title.textContent = `${brief.company_name} · Discovery brief`; resultView.append(title);
      const meta = document.createElement('p'); meta.textContent = `${t('quality')}: ${brief.quality} · ${t('cutoff')}: ${brief.knowledge_cutoff} · ${t('mode')}: ${brief.research_mode}`; resultView.append(meta);
      for (const note of brief.coverage_notes || []) { const p=document.createElement('p'); p.textContent=note; resultView.append(p); }
      if (brief.window_start) { const p=document.createElement('p'); p.textContent=`${t('window')}: ${brief.window_start} — ${brief.window_end}`; resultView.append(p); }
      if (brief.context_summary?.length) {
        const heading = document.createElement('h3'); heading.textContent = t('context'); resultView.append(heading);
        const list = document.createElement('ul');
        for (const item of brief.context_summary) { const li = document.createElement('li'); li.textContent = item.text; list.append(li); }
        resultView.append(list);
      }
      if (brief.warnings?.length) {
        const warning = document.createElement('p');
        warning.className = 'notice';
        warning.textContent = t('limited');
        resultView.append(warning);
      }
      for (const [heading, items, key] of [
        [t('findings'), brief.claims, 'statement'], [t('requirements'), brief.requirements, 'summary'],
        [t('questions'), brief.questions, 'text'], [t('hypotheses'), brief.hypotheses, 'text'],
        [t('unknowns'), brief.unknowns, 'text'],
      ] as [string, Record<string, string>[], string][]) {
        const h = document.createElement('h3'); h.textContent = heading; resultView.append(h);
        const list = document.createElement('ul');
        for (const item of items) { const li = document.createElement('li'); li.textContent = item[key]; list.append(li); }
        if (!items.length) { const li = document.createElement('li'); li.textContent = t('empty'); list.append(li); }
        resultView.append(list);
      }
      const details = document.createElement('details');
      const summary = document.createElement('summary'); summary.textContent = t('evidence'); details.append(summary);
      for (const claim of brief.claims) for (const evidence of claim.evidence || []) {
        const temporal=document.createElement('p'); temporal.textContent=`${t('event')}: ${claim.event_on || t('unknown')} · ${t('basis')}: ${claim.temporal_basis || t('unknown')}`; details.append(temporal);
        const quote = document.createElement('blockquote'); quote.textContent = evidence.quote; details.append(quote);
        const source = brief.sources.find((s: {source_id:string}) => s.source_id === evidence.source_id);
        if (source) {
          try { const url = new URL(source.url); if (['http:', 'https:'].includes(url.protocol)) {
            const link = document.createElement('a'); link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = source.title || url.hostname; details.append(link);
            const dates = document.createElement('p'); dates.textContent = `${t('published')}: ${source.published_on || t('unknown')} · ${t('retrieved')}: ${source.retrieved_at || t('unknown')}`; details.append(dates);
          }} catch { /* Invalid links are never rendered. */ }
        }
      }
      for (const requirement of brief.requirements) { const quote = document.createElement('blockquote'); quote.textContent = `RFP: ${requirement.quote}`; details.append(quote); }
      resultView.append(details);
      const excluded=document.createElement('details'); const excludedTitle=document.createElement('summary'); excludedTitle.textContent=t('excluded'); excluded.append(excludedTitle);
      for (const rejection of ledger.rejections || []) {
        const candidate=[...(ledger.candidates||[]),...(ledger.requirement_candidates||[])].find((c:any)=>(c.candidate_id||c.requirement_id)===(rejection.candidate_id||rejection.requirement_id));
        const p=document.createElement('p'); p.textContent=`${candidate?.statement || candidate?.summary || rejection.candidate_id || rejection.requirement_id}: ${rejection.reason}`; excluded.append(p);
      }
      resultView.append(excluded);
      const trace = document.createElement('details');
      const traceTitle = document.createElement('summary'); traceTitle.textContent = t('usage'); trace.append(traceTitle);
      const usage = document.createElement('p');
      const metrics = brief.metrics || {};
      usage.textContent = `${t('searchCalls')}: ${metrics.search_requests ?? t('unknown')} · ${t('extractCalls')}: ${metrics.extract_requests ?? t('unknown')} · ${t('modelCalls')}: ${metrics.llm_requests ?? t('unknown')} · ${t('inputTokens')}: ${metrics.llm_input_tokens ?? t('unknown')} · ${t('outputTokens')}: ${metrics.llm_output_tokens ?? t('unknown')} · ${t('reportedCredits')}: ${metrics.tavily_credits_reported ?? t('unknown')} · ${t('reservedCredits')}: ${metrics.tavily_credits_reserved ?? t('unknown')}`;
      trace.append(usage); resultView.append(trace);
      const downloads = document.createElement('p');
      downloads.className = 'downloads';
      for (const [name, label] of [['brief.pdf', 'PDF'], ['brief.html', 'HTML'], ['brief.md', 'Markdown'], ['brief.json', 'JSON'], ['evidence.json', t('evidenceJson')], ['trace.json', t('traceJson')]]) {
        if (!artifactNames.includes(name)) continue;
        const link = document.createElement('a'); link.href = `/api/runs/${runId}/artifacts/${name}`; link.textContent = label; downloads.append(link);
      }
      resultView.append(downloads);
      if (!artifactNames.includes('brief.pdf')) { const notice=document.createElement('p'); notice.textContent=t('noPdf'); resultView.append(notice); }
    } catch (err) {
      resultView.textContent = err instanceof Error ? err.message : t('failure');
    } finally { submit.disabled = false; }
  });
  translate();
}

const card = document.querySelector<HTMLElement>('.card');
if (card) {
  const sampleSection = document.createElement('section');
  sampleSection.className = 'sample';
  let selectedSample='sagara';
  const sampleSelect=document.createElement('select'); sampleSelect.setAttribute('aria-label','Synthetic sample');
  const initial=document.createElement('option'); initial.value='sagara'; initial.textContent='Sagara · limited'; sampleSelect.append(initial);
  fetch('/api/samples').then(r=>r.json()).then(data=>{
    sampleSelect.replaceChildren();
    for (const sample of data.items) { const option=document.createElement('option'); option.value=sample.sample_id; option.textContent=sample.description; sampleSelect.append(option); }
  }).catch(()=>{});
  sampleSelect.addEventListener('change',()=>{selectedSample=sampleSelect.value;});
  const sampleButton = document.createElement('button');
  sampleButton.type = 'button';
  sampleButton.className = 'secondary';
  sampleButton.textContent = t('sample');
  sampleButton.dataset.i18n = 'sample';
  const output = document.createElement('div');
  output.dataset.generated='true';
  output.setAttribute('aria-live', 'polite');
  sampleButton.addEventListener('click', async () => {
    sampleButton.disabled = true;
    output.textContent = t('sampleLoading');
    try {
      const response = await fetch(`/api/samples/${encodeURIComponent(selectedSample)}`);
      if (!response.ok) throw new Error('sample unavailable');
      const data = await response.json();
      output.replaceChildren();
      const title = document.createElement('h2');
      title.textContent = `${data.company_name} · ${t('sampleTitle')}`;
      output.append(title);
      const disclaimer = document.createElement('p');
      disclaimer.textContent = `${t('synthetic')} · ${t('mode')}: ${data.research_mode}`;
      output.append(disclaimer);
      for (const [heading, items, key] of [
        [t('findings'), data.findings, 'statement'],
        [t('requirements'), data.requirements, 'summary'],
        [t('questions'), data.questions, 'text'],
        [t('hypotheses'), data.hypotheses, 'text'],
        [t('unknowns'), data.unknowns, 'text'],
      ] as [string, Record<string, string>[], string][]) {
        const h = document.createElement('h3'); h.textContent = heading; output.append(h);
        const list = document.createElement('ul');
        for (const item of items) { const li = document.createElement('li'); li.textContent = item[key]; list.append(li); }
        output.append(list);
      }
      const detail = document.createElement('p');
      detail.textContent = `${t('sampleOrigin')} ${t('cutoff')}: ${data.knowledge_cutoff}.`;
      output.append(detail);
      const evidence = document.createElement('details');
      const heading = document.createElement('summary');
      heading.textContent = t('evidence');
      evidence.append(heading);
      for (const finding of data.findings) {
        for (const item of finding.evidence || []) {
          const quote = document.createElement('blockquote');
          quote.textContent = item.quote;
          evidence.append(quote);
          const source = data.sources.find((s: {source_id: string}) => s.source_id === item.source_id);
          const caption = document.createElement('p');
          caption.textContent = source ? `${t('fictionalSource')}: ${source.title}` : t('missingSource');
          evidence.append(caption);
        }
      }
      for (const requirement of data.requirements) {
        const quote = document.createElement('blockquote');
        quote.textContent = `${t('sampleRfp')}: ${requirement.quote}`;
        evidence.append(quote);
      }
      output.append(evidence);
      const print = document.createElement('a');
      print.href = '/api/samples/sagara/brief.html';
      print.target = '_blank';
      print.rel = 'noopener noreferrer';
      print.textContent = `${t('sampleReport')} ↗`;
      output.append(print);
    } catch {
      output.textContent = t('sampleFailure');
    } finally { sampleButton.disabled = false; }
  });
  const runButton = document.createElement('button');
  runButton.type = 'button';
  runButton.className = 'secondary run-sample';
  runButton.textContent = t('runSample');
  runButton.dataset.i18n = 'runSample';
  runButton.disabled = true;
  const runOutput = document.createElement('div');
  runOutput.dataset.generated='true';
  runOutput.setAttribute('aria-live', 'polite');
  let sampleMode: 'fixture' | 'replay' = 'fixture';
  fetch('/api/config/public').then(r => r.json()).then(config => {
    sampleMode = config.mode === 'local' && config.research_mode === 'fixture' ? 'fixture' : 'replay';
    runButton.disabled = false;
  }).catch(() => { runButton.disabled = true; });
  runButton.addEventListener('click', async () => {
    runButton.disabled = true;
    runOutput.textContent = t('sampleLoading');
    try {
      let create: Response;
      if (sampleMode === 'replay' || selectedSample !== 'sagara') {
        create = await fetch(`/api/samples/${encodeURIComponent(selectedSample)}/replay`, {method: 'POST'});
      } else {
        const requestResponse = await fetch('/api/samples/sagara/request');
        if (!requestResponse.ok) throw new Error('sample request unavailable');
        const example = await requestResponse.json();
        example.request.client_request_id = crypto.randomUUID();
        create = await fetch('/api/runs', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(example.request)});
      }
      if (!create.ok) throw new Error('run unavailable');
      const run = await create.json();
      let done = false;
      let artifactNames: string[] = [];
      for (let attempt = 0; attempt < 120; attempt++) {
        const statusResponse = await fetch(`/api/runs/${encodeURIComponent(run.run_id)}`);
        if (!statusResponse.ok) throw new Error('status unavailable');
        const status = await statusResponse.json();
        runOutput.textContent = `${t('sampleTitle')} · ${status.status}`;
        if (status.status === 'completed') { done = true; artifactNames = status.artifacts || []; break; }
        if (['failed', 'cancelled', 'needs_input'].includes(status.status)) throw new Error('run failed');
        await new Promise(resolve => window.setTimeout(resolve, 1500));
      }
      if (!done) throw new Error('run timeout');
      const briefResponse = await fetch(`/api/runs/${encodeURIComponent(run.run_id)}/brief`);
      if (!briefResponse.ok) throw new Error('brief unavailable');
      const brief = reportView(await briefResponse.json());
      runOutput.replaceChildren();
      const title = document.createElement('h2');
      title.textContent = `${brief.company_name} · ${uiLanguage==='en'?'Synthetic example':'Contoh sintetis'}`;
      runOutput.append(title);
      const state = document.createElement('p');
      state.textContent = `${t('mode')}: ${brief.research_mode} · ${t('quality')}: ${brief.quality} · ${t('cutoff')}: ${brief.knowledge_cutoff}`;
      runOutput.append(state);
      if (brief.original_metrics) {
        const provenance=document.createElement('p'); provenance.textContent=`${t('demo')} Original: ${brief.original_research_mode}; model requests: ${brief.original_metrics.llm_requests ?? t('unknown')}`; runOutput.append(provenance);
      }
      for (const [heading, items, key] of [
        [t('findings'), brief.claims, 'statement'],
        [t('requirements'), brief.requirements, 'summary'],
        [t('questions'), brief.questions, 'text'],
        [t('hypotheses'), brief.hypotheses, 'text'],
        [t('unknowns'), brief.unknowns, 'text'],
      ] as [string, Record<string, string>[], string][]) {
        const h = document.createElement('h3'); h.textContent = heading; runOutput.append(h);
        const list = document.createElement('ul');
        for (const item of items) { const li = document.createElement('li'); li.textContent = item[key]; list.append(li); }
        runOutput.append(list);
      }
      const sources = document.createElement('p');
      sources.textContent = uiLanguage==='en' ? `${brief.sources.length} synthetic sources. This offline run/replay makes no external calls.` : `${brief.sources.length} sumber sintetis. Run offline/pemutaran ulang ini tidak membuat panggilan eksternal.`;
      runOutput.append(sources);
      const evidence = document.createElement('details');
      const evidenceTitle = document.createElement('summary');
      evidenceTitle.textContent = t('evidenceRfp');
      evidence.append(evidenceTitle);
      for (const claim of brief.claims) {
        for (const item of claim.evidence || []) {
          const quote = document.createElement('blockquote');
          quote.textContent = item.quote;
          evidence.append(quote);
          const source = brief.sources.find((s: {source_id: string}) => s.source_id === item.source_id);
          const caption = document.createElement('p');
          caption.textContent = source ? `${t('fictionalSource')}: ${source.title}` : t('missingSource');
          evidence.append(caption);
        }
      }
      for (const requirement of brief.requirements) {
        const quote = document.createElement('blockquote');
        quote.textContent = `${t('sampleRfp')}: ${requirement.quote}`;
        evidence.append(quote);
      }
      runOutput.append(evidence);
      const downloads = document.createElement('p');
      downloads.className = 'downloads';
      for (const [name, label] of [['brief.pdf', 'PDF'], ['brief.html', 'HTML'], ['brief.md', 'Markdown'], ['brief.json', 'JSON'], ['evidence.json', t('evidenceJson')], ['trace.json', t('traceJson')]]) {
        if (!artifactNames.includes(name)) continue;
        const link = document.createElement('a'); link.href = `/api/runs/${encodeURIComponent(run.run_id)}/artifacts/${name}`; link.textContent = label; downloads.append(link);
      }
      runOutput.append(downloads);
    } catch {
      runOutput.textContent = t('sampleFailure');
    } finally { runButton.disabled = false; }
  });
  sampleSection.append(sampleSelect, sampleButton, runButton, output, runOutput);
  card.after(sampleSection);
}
