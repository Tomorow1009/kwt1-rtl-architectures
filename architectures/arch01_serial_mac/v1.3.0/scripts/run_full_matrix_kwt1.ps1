param(
    [string]$DataRoot = '',
    [ValidateSet('software','all','layer')][string]$Mode = 'all',
    [int]$Layer = 0,
    [ValidateSet('both','iverilog','xsim')][string]$Simulator = 'both',
    [string]$VivadoBin = '', [string]$IcarusBin = '', [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$argv = @("$PSScriptRoot/run_full_matrix.py", '--mode', $Mode, '--simulator', $Simulator)
if($DataRoot) { $argv += @('--data-root', $DataRoot) }
if($Layer) { $argv += @('--layer', "$Layer") }
if($VivadoBin) { $argv += @('--vivado-bin', $VivadoBin) }
if($IcarusBin) { $argv += @('--icarus-bin', $IcarusBin) }
& $Python @argv
if($LASTEXITCODE -ne 0) { throw 'Full matrix verification failed; inspect the printed run directory' }
