import json
from pathlib import Path

from discoverybrief.roles import (
    AnalystOutput,
    ComposerOutput,
    PremiseAudit,
    ResearchPlan,
    VerifierOutput,
)


def test_synthetic_role_payloads_validate():
    fixture = Path(__file__).parent / "fixtures" / "role-outputs.json"
    outputs = json.loads(fixture.read_text(encoding="utf-8"))
    for name, cls in [
        ("planner", ResearchPlan),
        ("analyst", AnalystOutput),
        ("verifier", VerifierOutput),
        ("composer", ComposerOutput),
        ("auditor", PremiseAudit),
    ]:
        assert cls.model_validate(outputs[name])
