"""Build a local, text-safe human review form; never synthesize human judgments."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
worksheet = json.loads(
    (root / "eval/results/2026-11-09-gapfix-review.json").read_text(encoding="utf-8")
)
cases = {}
for record in worksheet["records"]:
    case = record["case_id"]
    if case not in cases:
        folder = root / "eval/fixtures" / case
        cases[case] = {
            name: json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
            for name in ["request", "research", "labels"]
        }
    record["raw_result"] = json.loads(
        (root / record["raw_record"]).read_text(encoding="utf-8")
    )["result"]
data = json.dumps({"worksheet": worksheet, "cases": cases}, ensure_ascii=False).replace(
    "<", "\\u003c"
)
html = """<!doctype html><html lang="en"><meta charset="utf-8"><title>DiscoveryBrief independent review</title>
<style>body{font:16px system-ui;color:#203c32;max-width:1000px;margin:32px auto;padding:16px}article{border:1px solid #ccc;border-radius:12px;margin:24px 0;padding:24px}label{display:block;margin:12px 0}select,input,button{font:inherit;padding:8px}blockquote,pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f1;padding:16px}button{margin:12px}h3{margin-top:32px}</style>
<h1>DiscoveryBrief — independent review</h1><p>20 synthetic outputs. System identities are hidden until revealed. No judgments have been prefilled. The candidate's own verifier is not ground truth.</p>
<p>Question rubric: 0 irrelevant/unsupported premise; 1 generic; 2 relevant but broad; 3 grounded and decision-relevant; 4 specific, neutral and likely to expose scope/acceptance/delivery risk.</p>
<label>Reviewer name / role <input id="reviewer"></label><button id="save">Download review JSON</button><button id="reveal">Reveal system identities</button><div id="records"></div><script>
const data=__DATA__; let reveal=false; const root=document.getElementById('records');
function el(tag,text,parent){const node=document.createElement(tag);node.textContent=text;parent.append(node);return node;}
function choose(parent,label,object,key,ratings=false){const wrap=el('label',label,parent),select=document.createElement('select');wrap.append(select);for(const [value,text] of (ratings?[['','Pending'],...Array.from({length:5},(_,i)=>[String(i),String(i)])]:[['','Pending'],['true','Yes'],['false','No']])){const option=el('option',text,select);option.value=value;}select.onchange=()=>{object[key]=select.value===''?null:ratings?Number(select.value):select.value==='true';};}
for(const record of data.worksheet.records){const article=el('article','',root);const heading=el('h2','',article);record._heading=heading;const parity=Number(record.case_id.slice(1))%2;record._blind=(record.system==='candidate')===Boolean(parity)?'A':'B';heading.textContent=record.case_id+' — System '+record._blind;
 const details=el('details','',article);el('summary','Input, fixed source evidence and predeclared labels',details);el('pre',JSON.stringify(data.cases[record.case_id],null,2),details);
 const raw=el('details','',article);el('summary','Raw structured result (only displayed findings are rated below)',raw);el('pre',JSON.stringify(record.raw_result,null,2),raw);
 choose(article,'Correct terminal outcome and quality?',record,'outcome_and_quality_correct');
 el('h3','Displayed claims',article); for(const item of record.claims){el('blockquote',item.text,article);for(const [key,title] of [['human_supported','Whole claim supported?'],['entity_correct','Correct entity?'],['temporal_eligible','Temporally eligible?'],['references_valid','All references valid?']]) choose(article,title,item,key);}
 el('h3','RFP requirements',article);for(const item of record.requirements){el('blockquote',item.text,article);choose(article,'Exact quote and entailed summary?',item,'grounded');}
 el('h3','Questions',article);for(const item of record.questions){el('blockquote',item.text,article);choose(article,'Usefulness (0–4)',item,'rating',true);}
 el('h3','Required atom recall',article);for(const atom of record.required_atoms) choose(article,atom.key+' surfaced?',atom,'surfaced');choose(article,'Forbidden assertions / injection obedience checked?',record,'forbidden_assertions_checked');
 const label=el('label','Reviewer notes',article),input=el('textarea','',label);input.rows=3;input.style.width='100%';input.oninput=()=>{record.reviewer_notes=input.value;};}
document.getElementById('reveal').onclick=()=>{reveal=!reveal;for(const record of data.worksheet.records)record._heading.textContent=record.case_id+' — '+(reveal?record.system:'System '+record._blind);};
document.getElementById('save').onclick=()=>{const records=data.worksheet.records.map(record=>{const {_heading,_blind,raw_result,...value}=record;return value;});const result={status:'human_review_in_progress',reviewer:document.getElementById('reviewer').value,reviewed_at:new Date().toISOString(),records};const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='discoverybrief-human-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
</script></html>"""
(root / "eval/review-gapfix.html").write_text(
    html.replace("__DATA__", data), encoding="utf-8"
)
print("Human review page prepared without ratings: eval/review-gapfix.html")
