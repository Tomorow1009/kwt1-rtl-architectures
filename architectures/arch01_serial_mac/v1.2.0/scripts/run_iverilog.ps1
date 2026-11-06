param([string]$ToolBin = '')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$build = Join-Path $root 'sim\iverilog'
New-Item -ItemType Directory -Force $build | Out-Null
function Find-Tool([string]$Name) {
    if ($ToolBin) { return Join-Path $ToolBin "$Name.exe" }
    return (Get-Command $Name -ErrorAction Stop).Source
}
$compiler = Find-Tool 'iverilog'
$runner = Find-Tool 'vvp'
Push-Location $build
try {
    & $compiler -g2012 -Wall -I "$root\vectors" -s tb_dot64 -o dot64.vvp "$root\rtl\requantize.sv" "$root\rtl\dot64.sv" "$root\tb\tb_dot64.sv" 2>&1 | Tee-Object compile.log
    if ($LASTEXITCODE -ne 0) { throw 'Icarus compilation failed' }
    & $runner dot64.vvp '+VCD' 2>&1 | Tee-Object simulation.log
    if ($LASTEXITCODE -ne 0) { throw 'Icarus simulation failed' }
    if (-not (Select-String -Path simulation.log -Pattern '^PASS:')) { throw 'Missing final PASS' }
} finally { Pop-Location }
