param(
    [string]$DataRoot = '',
    [ValidateSet('both','iverilog','xsim','software')][string]$Simulator = 'both',
    [string]$VivadoBin = '',
    [string]$IcarusBin = '',
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$root = (Split-Path $PSScriptRoot -Parent).Replace('\','/')
if (-not $DataRoot) { $DataRoot = "$root/KWT1/model_data/outputs/real_sample_001" }
$DataRoot = (Resolve-Path -LiteralPath $DataRoot).Path.Replace('\','/')
$runId = (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [guid]::NewGuid().ToString('N').Substring(0,8)
$run = "$root/sim/real_kwt1/$runId"
New-Item -ItemType Directory -Path $run -Force | Out-Null
Write-Output "Run directory: $run"
function Find-Tool([string]$Name,[string]$Bin,[string]$Extension) {
    if ($Bin) { return (Resolve-Path -LiteralPath (Join-Path $Bin "$Name.$Extension")).Path }
    return (Get-Command $Name -ErrorAction Stop).Source
}
$summary = [ordered]@{status='running'; run=$run; data_root=$DataRoot; simulator=$Simulator; results=@(); sources=@()}
foreach ($file in @('rtl/dot64.sv','rtl/requantize.sv','tb/tb_single_hex.sv','scripts/verify_real_hex.py','scripts/run_real_kwt1.ps1','scripts/real_kwt1_waves.tcl')) {
    $summary.sources += @{path="$root/$file"; sha256=(Get-FileHash -LiteralPath "$root/$file" -Algorithm SHA256).Hash}
}
try {
    & $Python "$root/scripts/verify_real_hex.py" $DataRoot --report "$run/software.json" *> "$run/software.log"
    if ($LASTEXITCODE -ne 0) { throw "Software check failed: $run/software.log" }
    $software = Get-Content -LiteralPath "$run/software.json" -Raw | ConvertFrom-Json
    if ($software.passed -ne 12) { throw 'Software coverage is not 12/12' }
    $summary.software_passed = $software.passed
    $engines = @()
    if ($Simulator -eq 'both') { $engines = @('iverilog','xsim') }
    elseif ($Simulator -ne 'software') { $engines = @($Simulator) }
    foreach ($engine in $engines) {
        $build = "$run/$engine"
        New-Item -ItemType Directory -Path $build | Out-Null
        Push-Location $build
        try {
            if ($engine -eq 'iverilog') {
                $compiler = Find-Tool 'iverilog' $IcarusBin 'exe'
                $runner = Find-Tool 'vvp' $IcarusBin 'exe'
                & $compiler -g2012 -Wall -s tb_single_hex -o single.vvp "$root/rtl/requantize.sv" "$root/rtl/dot64.sv" "$root/tb/tb_single_hex.sv" *> compile.log
                if ($LASTEXITCODE -ne 0) { throw 'Icarus compilation failed' }
            } else {
                $compiler = Find-Tool 'xvlog' $VivadoBin 'bat'
                $elaborator = Find-Tool 'xelab' $VivadoBin 'bat'
                $runner = Find-Tool 'xsim' $VivadoBin 'bat'
                & $compiler --sv "$root/rtl/requantize.sv" "$root/rtl/dot64.sv" "$root/tb/tb_single_hex.sv" *> compile.log
                if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
                & $elaborator tb_single_hex -debug typical -s real_dot_sim *> elaborate.log
                if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
            }
            foreach ($layer in $software.layers) {
                $tag = 'layer_{0:D2}' -f [int]$layer.layer
                $data = $layer.hex_dir.Replace('\','/')
                $log = "$build/$tag.log"
                if ($engine -eq 'iverilog') {
                    & $runner single.vvp "+DATA_DIR=$data" '+VCD' *> $log
                    $simulationExit = $LASTEXITCODE
                    if (Test-Path -LiteralPath 'single.vcd') { Move-Item -LiteralPath 'single.vcd' -Destination "$tag.vcd" }
                } else {
                    @("log_wave -r /tb_single_hex/dut/*", "source {$root/scripts/real_kwt1_waves.tcl}", "save_wave_config $tag.wcfg", 'run all', 'quit') | Set-Content -LiteralPath "$tag.tcl" -Encoding ascii
                    @("-testplusarg `"DATA_DIR=$data`"", "-tclbatch $tag.tcl", "-wdb $tag.wdb") | Set-Content -LiteralPath "$tag.options" -Encoding ascii
                    & $runner real_dot_sim -f "$tag.options" *> $log
                    $simulationExit = $LASTEXITCODE
                }
                if ($simulationExit -ne 0) { throw "$engine $tag failed: $log" }
                $pass = @(Select-String -LiteralPath $log -Pattern '^PASS: single HEX dot result=(-?\d+) saturated=([01]) total=(-?\d+)')
                if ($pass.Count -ne 1) { throw "$engine $tag missing/duplicate final PASS: $log" }
                $match = $pass[0].Matches[0]
                if ([long]$match.Groups[1].Value -ne [long]$layer.result -or [int]$match.Groups[2].Value -ne [int]$layer.saturated -or [long]$match.Groups[3].Value -ne [long]$layer.total) {
                    throw "$engine $tag differs from software result"
                }
                $summary.results += @{simulator=$engine; layer=$layer.layer; passed=$true; result=$layer.result; total=$layer.total; saturated=$layer.saturated; log=$log}
                Write-Output "$engine $tag $($pass[0].Line)"
            }
        } finally { Pop-Location }
    }
    $summary.status = 'passed'
    Write-Output "PASS: software 12/12; completed $($summary.results.Count) RTL runs ($Simulator)"
} catch {
    $summary.status = 'failed'
    $summary.error = $_.Exception.Message
    throw
} finally {
    $summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath "$run/summary.json" -Encoding utf8
}
