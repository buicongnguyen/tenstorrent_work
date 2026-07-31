param(
    [string]$Commit = "main"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$destination = Join-Path $repoRoot "upstream\tt-metal"
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ("tt-metal-" + [guid]::NewGuid())

try {
    git clone --depth 1 --filter=blob:none --sparse `
        https://github.com/tenstorrent/tt-metal.git $temporary
    git -C $temporary sparse-checkout set --no-cone `
        /tech_reports/ /METALIUM_GUIDE.md /LICENSE

    if ($Commit -ne "main") {
        git -C $temporary fetch --depth 1 origin $Commit
        git -C $temporary checkout --detach FETCH_HEAD
    }

    $resolvedCommit = git -C $temporary rev-parse HEAD
    $commitDate = git -C $temporary log -1 --format=%cI

    Write-Host "Resolved upstream commit: $resolvedCommit ($commitDate)"
    Write-Host "Review the diff before replacing: $destination"
    Write-Host "This script intentionally does not overwrite the existing snapshot."
}
finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -Recurse -Force -LiteralPath $temporary
    }
}

