"""Exact full-file C++ streaming scan plus SHA256, without dropping activity."""
import hashlib,json,subprocess
from decimal import Decimal
from pathlib import Path
from activity import TOP


def audit_vcd_fast(path,window,binary,call=None,run=None):
    path=Path(path);binary=Path(binary)
    before=path.stat()
    if call is None:
        p=subprocess.run([str(binary),str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        if p.returncode:raise ValueError(p.stderr.strip())
        text=p.stdout
    else:text=call([binary,path],run,path.stem+'_activity_scan.log')
    scanned=json.loads(text)
    scale=Decimal(scanned.pop('scale_fs'))/Decimal(1000000)
    begin=Decimal(scanned.pop('begin_tick'))*scale;end=Decimal(scanned.pop('end_tick'))*scale
    expected0=Decimal(str(window['start_ns']));expected1=Decimal(str(window['end_ns']))
    if not expected0.is_finite() or not expected1.is_finite() or expected1<=expected0:
        raise ValueError('Invalid measured task boundary')
    if abs(begin-expected0)>Decimal('0.000002') or abs(end-expected1)>Decimal('0.000002'):
        raise ValueError('VCD dumping interval differs from measured task')
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):digest.update(chunk)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('VCD changed during audit')
    result=dict(status='scope_and_window_verified',file=path.name,sha256=digest.hexdigest(),bytes=after.st_size,
        scope='.'.join(TOP),timescale_ns=str(scale),start_ns=str(begin),end_ns=str(end),
        mapped_netlist_annotation_verified=False,power_estimated=False,
        review_required='Unknown/static activity and mapped gate/SRAM coverage must be reviewed before power acceptance.')
    result.update(scanned)
    return result


def build_scanner(run,call):
    source=Path(__file__).resolve().with_name('activity_scan.cpp')
    binary=run/'activity_scan'
    call(['g++','-O2','-std=c++11',source,'-o',binary],run,'activity_compile.log')
    return binary


def audit_activity(path,window,run,call):
    source=Path(__file__).resolve().with_name('activity_scan.cpp')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    binary=build_scanner(run,call)
    result=audit_vcd_fast(path,window,binary,call,run)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:raise ValueError('Activity scanner source changed')
    result['auditor']={'kind':'complete_native_stream_scan_and_SHA256','source_sha256':digest,
                       'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
    return result
