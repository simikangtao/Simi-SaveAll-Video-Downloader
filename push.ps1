# ============================================================
# Simi-SaveAll Video Downloader - Quick Push Script (PowerShell)
# Usage: .\push.ps1 "commit message"
# Or just: .\push.ps1  (uses auto-generated message)
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Simi-SaveAll - Push to GitHub" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if inside a git repo
if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
    Write-Host "ERROR: Not a git repository!" -ForegroundColor Red
    Write-Host "Run this from C:\Users\spiderman\Desktop\Video-Downloader" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Set git user info
git config user.name "simikangtao"
git config user.email "simikangtao@users.noreply.github.com"

# Ensure remote is set
try {
    git remote get-url origin | Out-Null
} catch {
    Write-Host "Setting up remote..." -ForegroundColor Yellow
    git remote add origin https://github.com/simikangtao/Simi-SaveAll-Video-Downloader.git
}

# Show current status
Write-Host "--- Git Status ---" -ForegroundColor Gray
$status = git status --short
if ($status) {
    $status | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "(nothing changed)" -ForegroundColor Gray
}
Write-Host ""

# Get commit message
$msg = $args[0]
if ([string]::IsNullOrWhiteSpace($msg)) {
    $dateStr = Get-Date -Format "yyyy-MM-dd"
    $msg = "Update on $dateStr"
    Write-Host "No message provided. Using: '$msg'" -ForegroundColor Yellow
}

# Stage all changes
Write-Host "Staging changes..." -ForegroundColor Green
git add -A

# Check if there are changes
if (-not (git diff --cached --quiet 2>$null)) {
    Write-Host "No changes to commit. Nothing to push." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 0
}

# Commit
Write-Host "Committing: '$msg'" -ForegroundColor Green
git commit -m $msg

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Green
Write-Host "(This may take a moment...)" -ForegroundColor Gray

# Use curl + REST API as fallback since git HTTPS has schannel issues in some contexts
# But try git push first (works with credential manager)
$pushSuccess = $false
try {
    & git push origin main 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pushSuccess = $true
    }
} catch {
    # If git push fails, try using GitHub REST API via curl
    Write-Host "Git push failed, trying alternative method..." -ForegroundColor Yellow
    
    $line = Get-Content "$env:USERPROFILE\.git-credentials" | Where-Object { $_ -match "github.com" } | Select-Object -First 1
    $token = ""
    if ($line -match "https://[^:]+:([^@]+)@github\.com") {
        $token = $matches[1]
    }
    
    if ($token) {
        # Create tree and commit via REST API
        $blobIds = @()
        git ls-files -s | ForEach-Object {
            $parts = $_ -split "`t"
            $mode = $parts[0].Substring(0,4)
            $type = if ($mode -like "04*") { "tree" } elseif ($mode -like "16*") { "blob" } else { "blob" }
            $sha = $parts[1]
            $path = $parts[3]
            $blobIds += @{ mode=$mode; type=$type; path=$path; sha=$sha }
        }
        
        $treeJson = $blobIds | ConvertTo-Json -Depth 5
        $treeJson | Set-Content "$env:TEMP\push_tree.json" -Encoding ascii
        
        $treeResult = & curl.exe -s -X POST "https://api.github.com/repos/simikangtao/Simi-SaveAll-Video-Downloader/git/trees" `
            -H "Authorization: token $token" `
            -H "User-Agent: dsh-script" `
            -H "Accept: application/vnd.github+json" `
            -H "Content-Type: application/json" `
            --data-binary "@$env:TEMP\push_tree.json"
        
        $treeObj = $treeResult | ConvertFrom-Json
        $treeSha = $treeObj.sha
        
        # Get parent commit
        $parentCommit = $(git log -1 --format=%H)
        
        $commitBody = @{
            message = $msg
            tree    = @{ sha = $treeSha }
            parents = @(@{ sha = $parentCommit })
        } | ConvertTo-Json -Depth 10
        
        $commitBody | Set-Content "$env:TEMP\push_commit.json" -Encoding ascii
        
        $commitResult = & curl.exe -s -X POST "https://api.github.com/repos/simikangtao/Simi-SaveAll-Video-Downloader/git/commits" `
            -H "Authorization: token $token" `
            -H "User-Agent: dsh-script" `
            -H "Accept: application/vnd.github+json" `
            -H "Content-Type: application/json" `
            --data-binary "@$env:TEMP\push_commit.json"
        
        $commitObj = $commitResult | ConvertFrom-Json
        $newSha = $commitObj.sha
        
        # Update main branch ref
        $refBody = @{ sha = $newSha } | ConvertTo-Json
        $refBody | Set-Content "$env:TEMP\push_ref.json" -Encoding ascii
        
        $refResult = & curl.exe -s -X PATCH "https://api.github.com/repos/simikangtao/Simi-SaveAll-Video-Downloader/refs/heads/main" `
            -H "Authorization: token $token" `
            -H "User-Agent: dsh-script" `
            -H "Accept: application/vnd.github+json" `
            -H "Content-Type: application/json" `
            --data-binary "@$env:TEMP\push_ref.json"
        
        $refObj = $refResult | ConvertFrom-Json
        if ($refObj.ref) {
            $pushSuccess = $true
            Write-Host "Pushed via REST API! SHA: $($commitObj.short_sha)" -ForegroundColor Green
        }
    }
}

if ($pushSuccess) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Code pushed to GitHub" -ForegroundColor Green
    Write-Host "  https://github.com/simikangtao/Simi-SaveAll-Video-Downloader" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "  PUSH FAILED" -ForegroundColor Red
    Write-Host "  Check your internet connection and try again." -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
}

Read-Host "Press Enter to exit"