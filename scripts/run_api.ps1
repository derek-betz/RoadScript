param(
    [int]$Port = 9001,
    [string]$Host = "0.0.0.0"
)

$env:PYTHONPATH = (Resolve-Path ".").Path
python -m uvicorn roadscript.api.main:app --host $Host --port $Port
