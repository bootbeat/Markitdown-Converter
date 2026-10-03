# Contributing

## Set up

```powershell
git clone https://github.com/bootbeat/universal-markitdown-converter.git
Set-Location universal-markitdown-converter
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

If activation is already permitted, omit the execution-policy command. The policy change is limited to the current PowerShell process.

## Run and test

```powershell
python app.py
python -m pytest -q
```

## Contribution expectations

- Keep changes focused and preserve the existing converter/core separation.
- Do not commit source documents, conversion outputs, extracted assets, credentials, or virtual environments.
- Keep raw MarkItDown output intact; make cleanup conservative and preserve source content when structure is ambiguous.
- Add or update tests for behavior changes. Describe format-specific limitations accurately; do not claim lossless conversion.
- Do not modify the installed MarkItDown package to alter this application's behavior.
