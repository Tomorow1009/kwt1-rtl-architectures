param(
    [ValidateSet('all','smoke','software')][string]$Mode='all',
    [ValidateSet('both','iverilog','xsim')][string]$Simulator='both',
    [ValidateSet('behavioral','pin_mock','vendor')][string]$Backend='behavioral',
    [string]$VendorFilelist='', [string]$SramConfig='', [string[]]$VendorInclude=@(),
    [string]$DataRoot='', [string]$VivadoBin='', [string]$IcarusBin='', [string]$Python='python'
)
$ErrorActionPreference='Stop'
$argv=@("$PSScriptRoot/run.py",'--mode',$Mode,'--simulator',$Simulator,'--backend',$Backend)
if($VendorFilelist) {$argv+=@('--vendor-filelist',$VendorFilelist)}
if($SramConfig) {$argv+=@('--sram-config',$SramConfig)}
foreach($inc in $VendorInclude) {$argv+=@('--vendor-include',$inc)}
if($DataRoot) {$argv+=@('--data-root',$DataRoot)}
if($VivadoBin) {$argv+=@('--vivado-bin',$VivadoBin)}
if($IcarusBin) {$argv+=@('--icarus-bin',$IcarusBin)}
& $Python @argv
if($LASTEXITCODE -ne 0) {throw 'Architecture 2 verification failed; inspect the printed run directory'}
