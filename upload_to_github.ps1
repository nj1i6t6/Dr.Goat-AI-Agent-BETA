# --- 自動上傳到 GitHub 的 PowerShell 腳本 ---

# 提示用戶輸入本次更新的說明
$commitMessage = Read-Host "請輸入本次更新的簡要說明 (例如: '完成羊群總覽頁面')，然後按 Enter"

# 檢查用戶是否輸入了說明
if (-not $commitMessage) {
    # 如果沒有輸入，使用一個預設的說明
    $commitMessage = "Routine update at $(Get-Date)"
    Write-Host "未提供說明，使用預設訊息: $commitMessage"
}

# 執行 Git 命令
Write-Host "-----------------------------------------"
Write-Host "Step 1: 將所有變更加入暫存區..."
git add .

Write-Host "-----------------------------------------"
Write-Host "Step 2: 提交變更，說明為 '$commitMessage'..."
git commit -m "$commitMessage"

Write-Host "-----------------------------------------"
Write-Host "Step 3: 將變更推送到 GitHub..."
git push -u origin main

Write-Host "-----------------------------------------"
Write-Host "====== 操作完成！程式碼已成功上傳到 GitHub。 ======"