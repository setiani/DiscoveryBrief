"""Build a reviewable draft pitch deck; requires python-pptx in the chosen Python."""

import argparse
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--output", type=Path, default=ROOT / "submission/DiscoveryBrief-review.pptx"
)
args = parser.parse_args()
OUT = args.output
SUMMARY = json.loads(
    (ROOT / "eval/results/2026-11-09-gapfix/summary.json").read_text(encoding="utf-8")
)
NAVY = RGBColor(19, 36, 44)
GREEN = RGBColor(28, 91, 72)
INK = RGBColor(30, 47, 48)
MUTED = RGBColor(95, 113, 110)
WHITE = RGBColor(255, 255, 255)


def textbox(slide, text, x, y, w, h, size, color=INK, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = 0
    for index, line in enumerate(text.split("\n")):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = line
        p.font.name, p.font.size, p.font.bold, p.font.color.rgb = (
            "Aptos",
            Pt(size),
            bold,
            color,
        )
        p.space_after = Pt(12)
    return box


def slide(title, eyebrow, body, takeaway):
    page = deck.slides.add_slide(deck.slide_layouts[6])
    page.background.fill.solid()
    page.background.fill.fore_color.rgb = RGBColor(246, 248, 245)
    stripe = page.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.18), deck.slide_height
    )
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = GREEN
    stripe.line.fill.background()
    textbox(page, eyebrow.upper(), 0.65, 0.38, 11.9, 0.28, 10, GREEN, True)
    textbox(page, title, 0.65, 0.82, 12, 0.8, 30, NAVY, True)
    textbox(page, body, 0.7, 1.9, 11.8, 3.8, 20)
    line = page.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(6.1), Inches(11.8), Inches(0.04)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = GREEN
    line.line.fill.background()
    textbox(page, takeaway, 0.7, 6.32, 10.8, 0.42, 12, GREEN, True)
    footer = textbox(
        page,
        f"DISCOVERYBRIEF  •  REVIEW  •  {len(deck.slides):02}",
        10.3,
        7.08,
        2.4,
        0.2,
        8,
        MUTED,
    )
    footer.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT


deck = Presentation()
deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
slide(
    "DiscoveryBrief",
    "Geek Room Global AI Hackathon 2026",
    "Walk into a discovery meeting with evidence, not a blank page.\nA research-assisted briefing for enterprise sales and solution teams.",
    "Local application + reproducible synthetic demos • Independent human quality review pending",
)
slide(
    "The preparation gap",
    "Problem",
    "• Research is scattered across news, company pages and meeting notes.\n• Teams must separate public evidence from assumptions and customer-provided context.\n• RFP details are easy to paraphrase beyond what the customer actually said.",
    "The result should help a team ask better questions, with traceable evidence.",
)
slide(
    "From context to a bounded brief",
    "Product",
    "1  Enter the company, meeting context and optional RFP.\n2  Research recent public developments and review each proposed claim.\n3  Generate a one-page brief, source evidence and grounded questions.\n4  Export and revisit a clearly labeled result.",
    "When evidence is insufficient, the brief explicitly says so.",
)
slide(
    "Tavily + Bifrost in the workflow",
    "Sponsor integrations",
    "Tavily Search + Extract → public source discovery and article text.\nBifrost → the single gateway for structured Planner, Analyst, Verifier, Composer and Auditor calls.\nDeterministic checks → exact quotes, dates, source references, RFP offsets and bounded outputs.",
    "No direct model-provider calls from the application.",
)
slide(
    "Trust is designed into the flow",
    "Evidence and uncertainty",
    "• Public facts are displayed only after verification and reference checks.\n• User-provided RFP and participant context retain their attribution.\n• Ambiguous identity can require clarification; empty evidence remains context-only.\n• Fixed-evidence and replay modes are labeled separately from live research.",
    "The verifier is a safeguard, not a guarantee of factual accuracy.",
)
slide(
    "What has been observed",
    "Development test • 9 November 2026",
    "A public-company / synthetic-RFP API run completed with quality limited.\nIt returned two referenced claims, two requirements and two questions.\nSynthetic fixed-evidence E01 returned ready with three distinct developments.",
    "One development run is not an accuracy benchmark.",
)
slide(
    "Evaluation and limitations",
    "Measured operations; human quality review pending",
    f"• Ten fixed-evidence cases produced 20 baseline/candidate outputs.\n• {SUMMARY['mechanical_outcome_matches']}/10 expected candidate outcomes matched; this is not factual accuracy.\n• Model calls: baseline {SUMMARY['model_calls']['baseline']} vs candidate {SUMMARY['model_calls']['candidate']}.\n• Median latency: baseline {SUMMARY['latency_median_seconds']['baseline']:.1f}s vs candidate {SUMMARY['latency_median_seconds']['candidate']:.1f}s.\n• Precision, recall and question ratings remain unjudged; model cost unknown.",
    "Results and failures must be disclosed before submission.",
)
slide(
    "Next steps",
    "Submission readiness",
    "Complete independent human judgments using the supplied review form.\nInspect this deck and the three synthetic replay demonstrations.\nConfirm public repository and submission links under the owner's authorization.\nLimits: single worker, model semantic errors, approximate event clustering, no verified fallback.",
    "Evidence-first discovery preparation, with uncertainty made visible.",
)
page = deck.slides.add_slide(deck.slide_layouts[6])
textbox(page, "A brief with inspectable evidence", 0.65, 0.55, 12, 0.8, 30, NAVY, True)
textbox(
    page,
    "Synthetic ready example\n\nThree separate developments.\nLiteral RFP requirements.\nQuestions and labeled hypotheses.\n\nReplay performs no new research; original fixed-evidence/model metrics remain separate.",
    0.7,
    1.7,
    5.1,
    4.7,
    20,
)
picture = ROOT / "submission/demo/ready-ui-1280.png"
if picture.is_file():
    from PIL import Image

    with Image.open(picture) as preview:
        width, height = preview.size
    scale = min(6.0 / width, 5.2 / height)
    page.shapes.add_picture(
        str(picture),
        Inches(6.4),
        Inches(1.5),
        width=Inches(width * scale),
        height=Inches(height * scale),
    )
page = deck.slides.add_slide(deck.slide_layouts[6])
textbox(page, "Run and review", 0.65, 0.65, 12, 0.8, 30, NAVY, True)
textbox(
    page,
    "Source package: discoverybrief/README.md\nArchitecture: docs/architecture.md\nEvaluation: eval/results.md and eval/review-gapfix.html\nDemo reports: submission/demo/\n\nPublic GitHub URL: not published in this session.\nNo deployment or submission receipt is claimed.",
    0.7,
    1.8,
    11.8,
    4.6,
    22,
)
OUT.parent.mkdir(parents=True, exist_ok=True)
deck.save(OUT)
print(f"Review deck written: {OUT}")
