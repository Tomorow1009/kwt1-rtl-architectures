param(
    [ValidateSet('iverilog','xsim')][string]$Simulator = 'iverilog',
    [string]$DataDir = '',
    [string]$ToolBin = ''
)
$ErrorActionPreference = 'Stop'
$root = (Split-Path $PSScriptRoot -Parent).Replace('\','/')
if (-not $DataDir) { $DataDir = "$root/examples/single_dot" }
$DataDir = (Resolve-Path -LiteralPath $DataDir).Path.Replace('\','/')
$build = "$root/sim/single_$Simulator"
New-Item -ItemType Directory -Force $build | Out-Null
New-Item -ItemType Directory -Force "$build/input" | Out-Null
foreach ($name in @('x','w','bias','shift','total','result','saturated')) {
    Copy-Item -LiteralPath "$DataDir/$name.hex" -Destination "$build/input/$name.hex" -Force
}
function Tool([string]$Name,[string]$Extension) {
    if ($ToolBin) { return Join-Path $ToolBin "$Name.$Extension" }
    return (Get-Command $Name -ErrorAction Stop).Source
}
Push-Location $build
try {
    if ($Simulator -eq 'iverilog') {
        & (Tool 'iverilog' 'exe') -g2012 -s tb_single_hex -o single.vvp "$root/rtl/requantize.sv" "$root/rtl/dot64.sv" "$root/tb/tb_single_hex.sv"
        if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
        & (Tool 'vvp' 'exe') single.vvp "+DATA_DIR=$DataDir" '+VCD' 2>&1 | Tee-Object simulation.log
    } else {
        & (Tool 'xvlog' 'bat') --sv "$root/rtl/requantize.sv" "$root/rtl/dot64.sv" "$root/tb/tb_single_hex.sv"
        if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
        & (Tool 'xelab' 'bat') tb_single_hex -debug typical -s single_sim
        if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
        & (Tool 'xsim' 'bat') single_sim -tclbatch "$root/scripts/single_xsim.tcl" -wdb single.wdb 2>&1 | Tee-Object simulation.log
    }
    if ($LASTEXITCODE -ne 0) { throw 'Simulation failed' }
    if (-not (Select-String -Path simulation.log -Pattern '^PASS:')) { throw 'Missing final PASS' }
} finally { Pop-Location }
