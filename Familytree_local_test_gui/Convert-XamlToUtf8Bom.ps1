[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [string]$Path = ".",
    [switch]$Backup,
    [switch]$Recurse = $true
)

function Convert-FileToUtf8Bom {
    param(
        [System.IO.FileInfo]$File,
        [switch]$Backup
    )

    $utf8Bom = New-Object System.Text.UTF8Encoding $true

    try {
        # 使用 StreamReader 自动识别 BOM
        $sr = New-Object System.IO.StreamReader($File.FullName, $true)
        $text = $sr.ReadToEnd()
        $sr.Close()

        if ($Backup) {
            $bakPath = "$($File.FullName).bak"
            Copy-Item -LiteralPath $File.FullName -Destination $bakPath -Force
        }

        [System.IO.File]::WriteAllText($File.FullName, $text, $utf8Bom)
        Write-Host "Converted: $($File.FullName)"
    }
    catch {
        Write-Warning "Failed to convert $($File.FullName): $($_.Exception.Message)"
    }
}

# 收集文件
if ($Recurse) {
    $files = Get-ChildItem -Path $Path -Filter "*.xaml" -File -Recurse -ErrorAction SilentlyContinue
} else {
    $files = Get-ChildItem -Path $Path -Filter "*.xaml" -File -ErrorAction SilentlyContinue
}

if (-not $files -or $files.Count -eq 0) {
    Write-Host "No .xaml files found under path: $Path"
    return
}

foreach ($f in $files) {
    if ($PSCmdlet.ShouldProcess($f.FullName, "Convert to UTF-8 with BOM")) {
        Convert-FileToUtf8Bom -File $f -Backup:$Backup.IsPresent
    }
}