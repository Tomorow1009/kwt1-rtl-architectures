param(
    [string]$DataRoot = 'D:\FPGA芯片赛道',
    [string]$Model = '',
    [string]$Audio = '',
    [ValidateRange(1, 200000)][int]$Count = 100,
    [ValidateSet('training', 'validation', 'testing')][string]$Split = 'validation',
    [string]$SampleList = '',
    [string]$FromFloat = '',
    [string]$RtlRepo = '',
    [string]$Output = '',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
if (-not $Python) {
    $kwtCandidates = @(
        (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'),
        (Join-Path $PSScriptRoot '..\kwt-export\.venv\Scripts\python.exe')
    )
    foreach ($kwtCandidate in $kwtCandidates) {
        if (Test-Path -LiteralPath $kwtCandidate -PathType Leaf) {
            $Python = (Resolve-Path -LiteralPath $kwtCandidate).Path
            break
        }
    }
    if (-not $Python) {
        $kwtCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($kwtCommand) { $Python = $kwtCommand.Source }
    }
}
if (-not $Python) { throw 'Provide -Python with a Python 3.8 environment; see README.txt.' }
$kwtArguments = @('-B', (Join-Path $PSScriptRoot 'kwt_to_hex.py'))
if ($FromFloat) {
    if ($PSBoundParameters.ContainsKey('Count') -or $SampleList -or $Model -or $Audio) {
        throw '-FromFloat cannot be combined with raw input/count options.'
    }
    $kwtArguments += @('--from-float', $FromFloat)
} else {
    $kwtArguments += @('--data-root', $DataRoot, '--split', $Split)
    if ($PSBoundParameters.ContainsKey('Count') -or -not $SampleList) { $kwtArguments += @('--count', $Count) }
    if ($Model) { $kwtArguments += @('--model', $Model) }
    if ($Audio) { $kwtArguments += @('--audio', $Audio) }
    if ($SampleList) { $kwtArguments += @('--sample-list', $SampleList) }
}
if ($RtlRepo) { $kwtArguments += @('--rtl-repo', $RtlRepo) }
if ($Output) { $kwtArguments += @('--output', $Output) }
& $Python @kwtArguments
if ($LASTEXITCODE -ne 0) { throw "KWT export failed (exit $LASTEXITCODE); retain logs for diagnosis." }
