param(
    [string]$DataRoot = '',
    [ValidateSet('software','smoke','shard','all','staged')][string]$Mode = 'staged',
    [ValidateSet('both','iverilog','xsim')][string]$Simulator = 'both',
    [string]$Shard = '', [int]$SkipTasks = 0, [int]$LimitTasks = 0,
    [string]$VivadoBin = '', [string]$IcarusBin = '', [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$root = (Split-Path $PSScriptRoot -Parent).Replace('\','/')
if (-not $DataRoot) { $DataRoot = "$root/KWT1/model_data/outputs/all_speech_dot00" }
$DataRoot = (Resolve-Path -LiteralPath $DataRoot).Path.Replace('\','/')
$manifest = Get-Content -LiteralPath "$DataRoot/manifest.json" -Raw | ConvertFrom-Json
if ($SkipTasks -lt 0 -or $LimitTasks -lt 0) { throw 'Invalid task range' }
if ($Mode -ne 'shard' -and ($Shard -or $SkipTasks -or $LimitTasks)) { throw 'Shard/range arguments require -Mode shard' }
$jobs = @()
function Add-Job($item,[int]$skip,[int]$limit,[string]$kind,[bool]$wave) {
    if ($skip -ge [int]$item.tasks) { throw 'SkipTasks exceeds shard task count' }
    $number=[int]$item.tasks-$skip
    if ($limit -gt 0) { $number=[Math]::Min($number,$limit) }
    return @{shard=$item.path; available=[int]$item.tasks; skip=$skip; tasks=$number; kind=$kind; wave=$wave}
}
if ($Mode -in @('smoke','staged')) {
    foreach($split in @('training','validation','testing')) {
        $items=@($manifest.shards | Where-Object split -eq $split)
        if ($items.Count -eq 0) { throw "Missing split $split" }
        $indices=@(0,[int][Math]::Floor($items.Count/2),($items.Count-1)) | Select-Object -Unique
        foreach($idx in $indices) {
            $item=$items[$idx]
            $jobs+=Add-Job $item 0 24 'smoke' ($idx -eq 0)
            if ($item.tasks -gt 24) { $jobs+=Add-Job $item ([int]$item.tasks-24) 24 'smoke' $false }
        }
    }
}
if ($Mode -eq 'staged') { $jobs+=Add-Job ($manifest.shards | Where-Object path -eq 'training/shard_0000') 0 0 'full_shard' $false }
if ($Mode -eq 'all') { foreach($item in $manifest.shards) { $jobs+=Add-Job $item 0 0 'all' $false } }
if ($Mode -eq 'shard') {
    $chosen=@($manifest.shards | Where-Object path -eq $Shard)
    if ($chosen.Count -ne 1) { throw 'Shard not found or ambiguous' }
    $jobs+=Add-Job $chosen[0] $SkipTasks $LimitTasks 'selected_shard' $false
}
$runId=(Get-Date -Format 'yyyyMMdd_HHmmss')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8)
$run="$root/sim/batch_kwt1/$runId"
New-Item -ItemType Directory -Path $run -Force | Out-Null
Write-Output "Run directory: $run"
$summary=[ordered]@{status='running'; run=$run; mode=$Mode; simulator=$Simulator; data_root=$DataRoot; jobs=$jobs; results=@(); sources=@()}
foreach($file in @('rtl/dot64.sv','rtl/requantize.sv','tb/tb_batch_hex.sv','scripts/verify_batch_hex.py','scripts/run_batch_kwt1.ps1')) {
    $summary.sources+=@{path="$root/$file";sha256=(Get-FileHash -LiteralPath "$root/$file" -Algorithm SHA256).Hash}
}
function Find-Tool([string]$name,[string]$bin,[string]$ext) {
    if($bin) { return (Resolve-Path -LiteralPath (Join-Path $bin "$name.$ext")).Path }
    return (Get-Command $name -ErrorAction Stop).Source
}
try {
    & $Python "$root/scripts/verify_batch_hex.py" $DataRoot --report "$run/software.json" *> "$run/software.log"
    if($LASTEXITCODE -ne 0) { throw "Software verification failed; see $run/software.log" }
    $software=Get-Content -LiteralPath "$run/software.json" -Raw | ConvertFrom-Json
    $summary.software_tasks=$software.tasks; $summary.manifest_sha256=$software.manifest_sha256
    $engines=if($Mode -eq 'software') { @() } elseif($Simulator -eq 'both') { @('iverilog','xsim') } else { @($Simulator) }
    foreach($engine in $engines) {
        $build="$run/$engine"; New-Item -ItemType Directory -Path $build | Out-Null
        Push-Location $build
        try {
            if($engine -eq 'iverilog') {
                $compiler=Find-Tool 'iverilog' $IcarusBin 'exe'; $runner=Find-Tool 'vvp' $IcarusBin 'exe'
                & $compiler -g2012 -Wall -s tb_batch_hex -o batch.vvp "$root/rtl/requantize.sv" "$root/rtl/dot64.sv" "$root/tb/tb_batch_hex.sv" *> compile.log
                if($LASTEXITCODE -ne 0) { throw 'Icarus compile failed' }
            } else {
                $compiler=Find-Tool 'xvlog' $VivadoBin 'bat'; $elab=Find-Tool 'xelab' $VivadoBin 'bat'; $runner=Find-Tool 'xsim' $VivadoBin 'bat'
                & $compiler --sv "$root/rtl/requantize.sv" "$root/rtl/dot64.sv" "$root/tb/tb_batch_hex.sv" *> compile.log
                if($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
                & $elab tb_batch_hex -debug typical -s batch_sim *> elaborate.log
                if($LASTEXITCODE -ne 0) { throw 'xelab failed' }
            }
            foreach($job in $jobs) {
                $tag=$job.shard.Replace('/','_')+"_skip$($job.skip)_count$($job.tasks)"
                $data="$DataRoot/$($job.shard)"; $log="$tag.log"
                if($engine -eq 'iverilog') {
                    $argv=@('batch.vvp',"+DATA_DIR=$data","+TASKS=$($job.available)","+SKIP_TASKS=$($job.skip)","+LIMIT_TASKS=$($job.tasks)")
                    if($job.wave) { $argv+='+VCD' }
                    & $runner @argv *> $log; $exit=$LASTEXITCODE
                    if($job.wave -and (Test-Path 'batch.vcd')) { Move-Item -LiteralPath 'batch.vcd' -Destination "$tag.vcd" }
                } else {
                    $tcl=@()
                    if($job.wave) { $tcl+=@('log_wave -r /tb_batch_hex/dut/*','log_wave /tb_batch_hex/n /tb_batch_hex/passed','add_wave -r /tb_batch_hex/dut/*',"save_wave_config $tag.wcfg") }
                    $tcl+=@('run all','quit'); $tcl | Set-Content -LiteralPath "$tag.tcl" -Encoding ascii
                    @("-testplusarg `"DATA_DIR=$data`"","-testplusarg `"TASKS=$($job.available)`"","-testplusarg `"SKIP_TASKS=$($job.skip)`"","-testplusarg `"LIMIT_TASKS=$($job.tasks)`"","-tclbatch $tag.tcl","-wdb $tag.wdb") | Set-Content -LiteralPath "$tag.options" -Encoding ascii
                    & $runner batch_sim -f "$tag.options" *> $log; $exit=$LASTEXITCODE
                }
                if($exit -ne 0) { throw "$engine $tag failed" }
                $matches=@(Select-String -LiteralPath $log -Pattern '^PASS: batch HEX tasks=(\d+) skip=(\d+) available=(\d+)')
                if($matches.Count -ne 1) { throw "$engine $tag missing/duplicate PASS" }
                $g=$matches[0].Matches[0].Groups
                if([int]$g[1].Value -ne $job.tasks -or [int]$g[2].Value -ne $job.skip -or [int]$g[3].Value -ne $job.available) { throw 'PASS task count mismatch' }
                $summary.results+=@{simulator=$engine;shard=$job.shard;skip=$job.skip;tasks=$job.tasks;kind=$job.kind;wave=$job.wave;passed=$true;log="$build/$log"}
                $summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath "$run/summary.json" -Encoding utf8
                Write-Output "$engine $tag $($matches[0].Line)"
            }
        } finally { Pop-Location }
    }
    $summary.status='passed'
    Write-Output "PASS: batch mode=$Mode software_tasks=$($software.tasks) rtl_jobs=$($summary.results.Count)"
} catch { $summary.status='failed'; $summary.error=$_.Exception.Message; throw }
finally { $summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath "$run/summary.json" -Encoding utf8 }
