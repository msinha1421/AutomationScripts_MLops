# ============================================================
# CONFIGURATION — Fill these in
# ============================================================
$srcAccount = "ffaimlstorage"
$srcKey     = ""

$dstAccount = "gkffaimlstorage"
$dstKey     = ""
$expiry = (Get-Date).AddDays(5).ToString("yyyy-MM-ddTHH:mm:ssZ")
# ============================================================

$shares = @(
    "poctest",
    "testshare",
    "training-checkpoint",
    "yotta-sync"
)
# ============================================================

# Generate SAS tokens
$srcSAS = az storage account generate-sas `
    --account-name $srcAccount `
    --account-key $srcKey `
    --services f `
    --resource-types sco `
    --permissions racwdlup `
    --expiry $expiry `
    --https-only `
    --output tsv

$dstSAS = az storage account generate-sas `
    --account-name $dstAccount `
    --account-key $dstKey `
    --services f `
    --resource-types sco `
    --permissions racwdlup `
    --expiry $expiry `
    --https-only `
    --output tsv

# Verify both keys upfront
Write-Host "Verifying source account..." -ForegroundColor Yellow
az storage share list --account-name $srcAccount --account-key $srcKey --output none 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Source key is wrong!" -ForegroundColor Red; exit }
Write-Host "Source OK" -ForegroundColor Green

Write-Host "Verifying destination account..." -ForegroundColor Yellow
az storage share list --account-name $dstAccount --account-key $dstKey --output none 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Destination key is wrong!" -ForegroundColor Red; exit }
Write-Host "Destination OK" -ForegroundColor Green

$successCount = 0
$failCount = 0

$env:AZCOPY_CONCURRENCY_VALUE = "512"

foreach ($shareName in $shares) {
    Write-Host "`n----------------------------------------" -ForegroundColor Gray
    Write-Host " Processing: $shareName" -ForegroundColor Yellow

    # Create share in destination
    Write-Host "  [1/2] Creating share..." -NoNewline
    az storage share create `
        --name $shareName `
        --account-name $dstAccount `
        --account-key $dstKey `
        --output none 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host " Created!" -ForegroundColor Green
    } else {
        Write-Host " Already exists — continuing" -ForegroundColor DarkYellow
    }

    # Copy with AzCopy
    Write-Host "  [2/2] Copying with AzCopy..."
    $srcUrl = "https://$srcAccount.file.core.windows.net/${shareName}?$srcSAS"
    $dstUrl = "https://$dstAccount.file.core.windows.net/${shareName}?$dstSAS"

    azcopy copy $srcUrl $dstUrl --recursive=true --overwrite=false

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SUCCESS: $shareName" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  FAILED: $shareName" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n==============================" -ForegroundColor Cyan
Write-Host " Successful : $successCount" -ForegroundColor Green
Write-Host " Failed     : $failCount" -ForegroundColor Red
Write-Host "==============================" -ForegroundColor Cyan
