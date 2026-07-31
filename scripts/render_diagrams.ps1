param(
    [string]$BrowserExecutable = $env:PUPPETEER_EXECUTABLE_PATH
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sourceDirectory = Join-Path $repositoryRoot "diagram_sources"
$outputDirectory = Join-Path $repositoryRoot "docs\assets\diagrams"

if (-not $BrowserExecutable) {
    $browserCandidates = @(
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    )
    $BrowserExecutable = $browserCandidates |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
}

if (-not $BrowserExecutable -or -not (Test-Path -LiteralPath $BrowserExecutable)) {
    throw "Set PUPPETEER_EXECUTABLE_PATH to a Chrome or Edge executable."
}

$env:PUPPETEER_SKIP_DOWNLOAD = "true"
$env:PUPPETEER_EXECUTABLE_PATH = $BrowserExecutable
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null

foreach ($source in Get-ChildItem -LiteralPath $sourceDirectory -Filter "*.mmd" -File) {
    $output = Join-Path $outputDirectory ($source.BaseName + ".svg")
    & pnpm dlx "@mermaid-js/mermaid-cli@11.12.0" `
        -i $source.FullName `
        -o $output `
        -b white `
        -t neutral
    if ($LASTEXITCODE -ne 0) {
        throw "Diagram rendering failed for $($source.Name)."
    }
}
