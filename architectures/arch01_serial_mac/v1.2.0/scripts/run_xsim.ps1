param([string]$VivadoBin = '')
$ErrorActionPreference = 'Stop'
$root = (Split-Path $PSScriptRoot -Parent).Replace('\', '/')
$build = Join-Path $root 'sim\xsim'
New-Item -ItemType Directory -Force $build | Out-Null
function Find-Tool([string]$Name) {
    if ($VivadoBin) { return Join-Path $VivadoBin "$Name.bat" }
    return (Get-Command $Name -ErrorAction Stop).Source
}
$xvlog = Find-Tool 'xvlog'
$xelab = Find-Tool 'xelab'
$xsim = Find-Tool 'xsim'
Push-Location $build
try {
    & $xvlog --sv -i "$root\vectors" "$root\rtl\requantize.sv" "$root\rtl\dot64.sv" "$root\tb\tb_dot64.sv" 2>&1 | Tee-Object compile.log
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & $xelab tb_dot64 -debug typical -s dot64_sim 2>&1 | Tee-Object elaborate.log
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & $xsim dot64_sim -tclbatch "$root/scripts/run_xsim.tcl" -wdb dot64.wdb 2>&1 | Tee-Object simulation.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    if (-not (Select-String -Path simulation.log -Pattern '^PASS:')) { throw 'Missing final PASS' }
} finally { Pop-Location }
