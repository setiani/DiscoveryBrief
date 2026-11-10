"""Escaped reporting for the explicitly synthetic demonstration."""

from jinja2 import Environment, select_autoescape

TEMPLATE = """<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>DiscoveryBrief - contoh sintetis</title>
<style>@page{size:A4;margin:12mm}body{font:11pt Arial,sans-serif;color:#203b31}
h1{font-size:20pt}h2{font-size:12pt;margin:14pt 0 5pt}p,li{line-height:1.35}
.meta{color:#567467;font-size:9pt}li{margin:4pt 0}</style></head><body>
<h1>{{ brief.company_name }} · DiscoveryBrief</h1>
<p class="meta">CONTOH SINTETIS · FIXTURE OFFLINE · CAKUPAN TERBATAS<br>
Meeting {{ brief.meeting_at }} · Batas pengetahuan {{ brief.knowledge_cutoff }}</p>
{% for title, items, key in sections %}<h2>{{ title }}</h2><ul>
{% for item in items %}<li>{{ item[key] }}</li>{% endfor %}</ul>{% endfor %}
<p class="meta">Perusahaan, sumber, dan peristiwa pada contoh ini fiktif.</p>
</body></html>"""


def render_sample_html(brief: dict) -> str:
    env = Environment(autoescape=select_autoescape(default_for_string=True))
    sections = [
        ("Perkembangan", brief["findings"], "statement"),
        ("Kebutuhan dalam RFP", brief["requirements"], "summary"),
        ("Pertanyaan prioritas", brief["questions"], "text"),
        ("Hipotesis untuk dikonfirmasi", brief["hypotheses"], "text"),
        ("Hal yang belum diketahui", brief["unknowns"], "text"),
    ]
    return env.from_string(TEMPLATE).render(brief=brief, sections=sections)


BUNDLE_TEMPLATE = """<!doctype html><html lang="{{ brief.language }}"><head><meta charset="utf-8">
<title>DiscoveryBrief</title><style>@page{size:A4;margin:12mm}body{font:10pt Arial,sans-serif;color:#1d352c}
h1{font-size:19pt;margin:0 0 5pt}h2{font-size:11pt;margin:10pt 0 3pt}p,li{line-height:1.25;margin:2pt 0}
ul{padding-left:16pt;margin:2pt 0}.meta,.sources{font-size:9pt;color:#4b6257}.sources a{color:inherit;overflow-wrap:anywhere}
.warning{font-weight:bold}.label{font-weight:bold}</style></head><body>
<h1>{{ brief.company_name }} · DiscoveryBrief</h1>
<p class="meta">{{ labels.meeting }}: {{ brief.meeting_at }} · {{ labels.as_of }}: {{ brief.knowledge_cutoff }}<br>
{{ labels.mode }}: {{ brief.research_mode }} · {{ labels.quality }}: {{ brief.quality }}</p>
{% if brief.window_start %}<p class="meta">{{ brief.window_start }} — {{ brief.window_end }} · {{ brief.meeting_timezone }}</p>{% endif %}
{% for note in brief.coverage_notes %}<p class="meta">{{ note }}</p>{% endfor %}
{% if brief.research_mode in ('fixture', 'replay') %}<p class="warning">{{ labels.synthetic }}</p>{% endif %}
{% if brief.warnings %}<p class="meta">{{ labels.limited }}</p>{% endif %}
{% if brief.context_summary %}<h2>{{ labels.context }}</h2><ul>{% for item in brief.context_summary %}<li>{{ item.text }}</li>{% endfor %}</ul>{% endif %}
<h2>{{ labels.findings }}</h2><ul>{% for claim in claims %}<li>{{ claim.statement }} {% for n in claim.references %}[{{ n }}]{% endfor %}</li>{% else %}<li>{{ labels.empty }}</li>{% endfor %}</ul>
<h2>{{ labels.requirements }}</h2><ul>{% for item in brief.requirements %}<li>{{ item.summary }}</li>{% else %}<li>{{ labels.empty }}</li>{% endfor %}</ul>
<h2>{{ labels.questions }}</h2><ul>{% for item in brief.questions %}<li>{{ item.text }}</li>{% else %}<li>{{ labels.empty }}</li>{% endfor %}</ul>
{% if brief.hypotheses %}<h2>{{ labels.hypotheses }}</h2><ul>{% for item in brief.hypotheses %}<li>{{ item.text }}</li>{% endfor %}</ul>{% endif %}
{% if brief.unknowns %}<h2>{{ labels.unknowns }}</h2><ul>{% for item in brief.unknowns %}<li>{{ item.text }}</li>{% endfor %}</ul>{% endif %}
{% if brief.overflow_note %}<p class="meta">{{ brief.overflow_note }}</p>{% endif %}
{% if references %}<h2>{{ labels.sources }}</h2><div class="sources">{% for item in references %}<p>[{{ item.number }}] {{ item.source.title }} · <a href="{{ item.source.url }}">{{ item.source.url }}</a></p>{% endfor %}</div>{% endif %}
</body></html>"""


def render_bundle_html(brief: dict) -> str:
    labels = {
        "id": {
            "meeting": "Meeting",
            "as_of": "Batas pengetahuan",
            "mode": "Mode",
            "quality": "Kualitas",
            "synthetic": "CONTOH SINTETIS",
            "limited": "Cakupan dan pemeriksaan memiliki keterbatasan.",
            "context": "Konteks dari pengguna",
            "findings": "Perkembangan terbaru",
            "requirements": "Kebutuhan dari RFP",
            "questions": "Pertanyaan prioritas",
            "hypotheses": "Hipotesis untuk dikonfirmasi",
            "unknowns": "Hal yang belum diketahui",
            "empty": "Belum ada informasi yang dapat ditampilkan.",
            "sources": "Sumber",
        },
        "en": {
            "meeting": "Meeting",
            "as_of": "Knowledge cutoff",
            "mode": "Mode",
            "quality": "Quality",
            "synthetic": "SYNTHETIC EXAMPLE",
            "limited": "Coverage and verification have limitations.",
            "context": "User-provided context",
            "findings": "Recent developments",
            "requirements": "RFP requirements",
            "questions": "Priority questions",
            "hypotheses": "Hypotheses to confirm",
            "unknowns": "Unknowns",
            "empty": "No information available.",
            "sources": "Sources",
        },
    }[brief["language"]]
    source_map = {item["source_id"]: item for item in brief["sources"]}
    numbers, claims = {}, []
    for claim in brief["claims"]:
        references = []
        for evidence in claim["evidence"]:
            sid = evidence["source_id"]
            if sid not in source_map:
                raise ValueError("unresolved source reference")
            if sid not in numbers:
                numbers[sid] = len(numbers) + 1
            if numbers[sid] not in references:
                references.append(numbers[sid])
        claims.append({"statement": claim["statement"], "references": references})
    references = [
        {"number": number, "source": source_map[sid]} for sid, number in numbers.items()
    ]
    env = Environment(autoescape=select_autoescape(default_for_string=True))
    return env.from_string(BUNDLE_TEMPLATE).render(
        brief=brief, labels=labels, claims=claims, references=references
    )
