# Sonny ONE Voice — Windows 11 read-only preflight
# Does not install software, download models, modify system settings, or access the microphone.
$ErrorActionPreference = "Stop"
Write-Host "Sonny ONE Voice: Windows 11 read-only diagnostics"
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$memoryGiB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$drives = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    [pscustomobject]@{Drive=$_.DeviceID;FreeGiB=[math]::Round($_.FreeSpace/1GB,2)}
})
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name })
$python = Get-Command py -ErrorAction SilentlyContinue
$git = Get-Command git -ErrorAction SilentlyContinue
$result = [ordered]@{
    DiagnosticVersion = 1
    OperatingSystem = $os.Caption
    OSBuild = $os.BuildNumber
    CPU = $cpu.Name
    RAMGiB = $memoryGiB
    GPUs = $gpus
    Drives = $drives
    PythonLauncherFound = [bool]$python
    GitFound = [bool]$git
    ModelInstalledVerified = $false
    AudioDeviceTested = $false
    NetworkIsolationVerified = $false
}
$result | ConvertTo-Json -Depth 5
Write-Host "Diagnostics complete. No installation or microphone test performed."
