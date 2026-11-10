param([ValidateSet('install','test','api','web','doctor','evaluate')][string]$Task='doctor')
$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
  switch ($Task) {
    install {
      uv sync --extra dev --extra pdf --frozen
      if ($LASTEXITCODE -ne 0) { throw 'Python install failed' }
      uv run playwright install chromium
      npm --prefix web ci
    }
    test {
      uv run pytest -q
      if ($LASTEXITCODE -ne 0) { throw 'Python tests failed' }
      uv run ruff check .
      if ($LASTEXITCODE -ne 0) { throw 'Lint failed' }
      uv run ruff format --check .
      if ($LASTEXITCODE -ne 0) { throw 'Formatting failed' }
      npm --prefix web run test
      if ($LASTEXITCODE -ne 0) { throw 'Frontend tests failed' }
      npm --prefix web run build
      if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
    }
    api { uv run uvicorn discoverybrief.api.main:app --host 127.0.0.1 --port 8000 --workers 1 }
    web { npm --prefix web run dev }
    doctor { uv run discoverybrief doctor }
    evaluate { uv run discoverybrief evaluate --dataset eval/dataset.json --mode fixture }
  }
} finally { Pop-Location }
