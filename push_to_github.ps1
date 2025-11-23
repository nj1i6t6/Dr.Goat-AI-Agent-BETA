# GitHub 推送腳本
# 請將 YOUR_GITHUB_USERNAME 替換為您的實際 GitHub 用戶名

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$RepositoryName = "goat-nutrition-app"
)

Write-Host "🐐 領頭羊博士 - GitHub 推送腳本" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# 設定變數
$RepoUrl = "https://github.com/$GitHubUsername/$RepositoryName.git"

Write-Host "目標存儲庫: $RepoUrl" -ForegroundColor Cyan
Write-Host ""

# 檢查是否在正確的目錄
if (-not (Test-Path ".git")) {
    Write-Host "❌ 錯誤: 當前目錄不是 Git 存儲庫" -ForegroundColor Red
    exit 1
}

# 添加遠端存儲庫
Write-Host "📡 設定遠端存儲庫..." -ForegroundColor Yellow
git remote add origin $RepoUrl
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  遠端存儲庫可能已存在，嘗試更新..." -ForegroundColor Yellow
    git remote set-url origin $RepoUrl
}

# 檢查遠端連接
Write-Host "🔍 檢查遠端連接..." -ForegroundColor Yellow
git remote -v

# 推送到主分支
Write-Host "🚀 推送到 GitHub..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 成功推送到 GitHub!" -ForegroundColor Green
    Write-Host "🌐 存儲庫地址: https://github.com/$GitHubUsername/$RepositoryName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 後續步驟建議:" -ForegroundColor Yellow
    Write-Host "1. 前往 GitHub 檢查您的專案" -ForegroundColor White
    Write-Host "2. 設定存儲庫描述和標籤" -ForegroundColor White
    Write-Host "3. 啟用 Issues 和 Discussions (可選)" -ForegroundColor White
    Write-Host "4. 考慮添加 GitHub Actions 自動化部署" -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 恭喜！您的領頭羊博士專案已成功上傳到 GitHub!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 推送失敗" -ForegroundColor Red
    Write-Host "可能原因:" -ForegroundColor Yellow
    Write-Host "1. GitHub 存儲庫不存在，請先在 GitHub 上創建" -ForegroundColor White
    Write-Host "2. 沒有推送權限，請檢查身份驗證" -ForegroundColor White
    Write-Host "3. 網路連接問題" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 解決方案:" -ForegroundColor Yellow
    Write-Host "1. 確保已在 GitHub 上創建存儲庫: https://github.com/new" -ForegroundColor White
    Write-Host "2. 配置 Git 身份驗證: git config --global credential.helper manager-core" -ForegroundColor White
    Write-Host "3. 或使用 Personal Access Token 進行身份驗證" -ForegroundColor White
}

Write-Host ""
Write-Host "按任意鍵退出..." -ForegroundColor Gray
Read-Host
