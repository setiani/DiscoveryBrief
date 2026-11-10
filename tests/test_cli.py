import json

from discoverybrief.cli import app
from discoverybrief.fixture import FIXTURES
from typer.testing import CliRunner


def test_cli_runs_only_the_synthetic_sample(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path / "cli-data"))
    runner = CliRunner()
    result = runner.invoke(
        app, ["run", "--input", str(FIXTURES / "request.json"), "--mode", "fixture"]
    )
    assert result.exit_code == 0
    assert json.loads(result.output)["synthetic"] is True
    data = json.loads((FIXTURES / "request.json").read_text(encoding="utf-8"))
    data["company_name"] = "Another Company"
    path = tmp_path / "other.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert (
        runner.invoke(app, ["run", "--input", str(path), "--mode", "fixture"]).exit_code
        != 0
    )
