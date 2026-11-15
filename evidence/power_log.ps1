# Logs the laptop battery's reported discharge rate once per second.
#   powershell -File evidence/power_log.ps1 <out.csv> <stop-file>
# Runs until <stop-file> exists. DischargeRate is whole-system power drawn
# from the battery in mW; it reads 0 while the charger is connected.
param([string]$Out, [string]$Stop)
"unix_ms,power_online,discharge_mw,remaining_mwh" | Out-File -FilePath $Out -Encoding ascii
while (-not (Test-Path $Stop)) {
    $b = Get-CimInstance -Namespace root\wmi -ClassName BatteryStatus | Select-Object -First 1
    $t = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    "$t,$([int]$b.PowerOnline),$($b.DischargeRate),$($b.RemainingCapacity)" | Out-File -FilePath $Out -Append -Encoding ascii
    Start-Sleep -Milliseconds 1000
}
