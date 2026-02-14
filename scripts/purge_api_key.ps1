<#
purge_api_key.ps1

Clone a mirror of the repository and purge `scripts/test_google_key.py`
from git history using `git filter-repo`.

Usage (PowerShell):
  .\scripts\purge_api_key.ps1

Notes:
- This script rewrites history in a local mirror only. It will NOT push
  to the remote automatically. After verifying the mirrored rewrite, you
  can push the changes with `git push --force --all` and `git push --force --tags`.
- If `git-filter-repo` is not installed, the script exits with install guidance.
#>

$ErrorActionPreference = 'Stop'

# Configuration - adjust if needed
# Use HTTPS clone to avoid interactive SSH host key prompt in automated runs
$repo = 'https://github.com/anitaweso/Gebaeudebrueter.git'
$pathToRemove = 'scripts/test_google_key.py'
$timestamp = (Get-Date -Format yyyyMMddHHmmss)
$mirrorDir = Join-Path $env:TEMP ("Gebaeudebrueter-mirror-$timestamp")

Write-Host "Mirror directory: $mirrorDir"
Write-Host "Repository: $repo"
Write-Host "Path to remove from history: $pathToRemove"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is not installed or not in PATH. Aborting."
    exit 1
}

Write-Host "Cloning mirror..."
git clone --mirror $repo $mirrorDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "git clone --mirror failed. Check repository URL and network access."
    exit 1
}

Push-Location $mirrorDir
try {
    # Create a backup bundle in parent directory
    $bundlePath = Join-Path '..' ("backup-$timestamp.bundle")
    Write-Host "Creating backup bundle: $bundlePath"
    git bundle create $bundlePath --all

    # Check for git-filter-repo
    Write-Host "Checking for git-filter-repo..."
    $hasFilterRepo = $false
    try {
        git filter-repo --version > $null 2>&1
        $hasFilterRepo = $true
    } catch {
        $hasFilterRepo = $false
    }

    if (-not $hasFilterRepo) {
        Write-Warning "git-filter-repo not found."
        Write-Host "Install instructions: https://github.com/newren/git-filter-repo"
        Write-Host 'On Windows, you can pip-install: python -m pip install git-filter-repo'
        Write-Host "Or download the script and place it in your PATH. Aborting." 
        exit 2
    }

    Write-Host "Running git-filter-repo to remove path: $pathToRemove"
    git filter-repo --invert-paths --path $pathToRemove
    if ($LASTEXITCODE -ne 0) {
        Write-Error "git-filter-repo failed."; exit 3
    }

    Write-Host "Expiring reflog and running GC..."
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive

    Write-Host "Rewrite complete in mirror repo: $mirrorDir"
    Write-Host "To update remote run (careful - force push):"
    Write-Host "  cd '$mirrorDir'"
    Write-Host "  git push --force --all"
    Write-Host "  git push --force --tags"
    Write-Host "Then coordinate with collaborators to reclone or reset local clones." 

} finally {
    Pop-Location
}

Write-Host "Script finished. Mirror preserved at: $mirrorDir"
