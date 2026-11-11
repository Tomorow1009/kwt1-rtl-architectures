"""Run the pinned 100-sample HEX dataset through real E203 (Python 3.6).

Uses an independent immutable input snapshot and the existing team lock.
Resume is explicit and rechecks completed captures; it never clears stale locks.
This verifies matrix arithmetic, not end-to-end speech classification.
"""
import argparse,datetime,hashlib,importlib.util,json,os,re,socket,struct,sys
from pathlib import Path
import audit
import server_run as server

ROOT=Path(__file__).resolve().parents[3]
FILES={'expected.npz','load.hex','result.hex','saturated.hex','total.hex'}
sha=audit.sha
read=audit.read
require=audit.require
save=server.save

def dataset(root,digest):
    require(sha(root/'manifest.json')==digest,'External dataset manifest changed')
    m=read(root/'manifest.json')
    require(m['schema']=='kwt1-full-arch02-q12-v1','Unsupported dataset format')
    require(m['numeric_format']['input']=='signed16 Q12' and
            m['numeric_format']['weight']=='signed16 Q12' and
            m['numeric_format']['bias']=='signed40 Q24' and
            m['numeric_format']['result']=='signed16 Q12','Unexpected numeric format')
    samples=m['samples'];ids=[s['sample'] for s in samples]
    require(len(samples)==100 and sorted(ids)==list(range(1,101)),'Expected 100 unique samples')
    require(len({s['wav'] for s in samples})==100,'Duplicate speech sample identifiers')
    tasks=[];files={'manifest.json':digest}
    for sample in sorted(samples,key=lambda s:s['sample']):
        layers=sample['layers']
        require(sorted(x['layer_number'] for x in layers)==list(range(1,13)),'Expected 12 unique layers')
        for layer in sorted(layers,key=lambda x:x['layer_number']):
            rel='sample_%06d/layer_%02d'%(sample['sample'],layer['layer_number'])
            folder=root/rel;layout=read(folder/'layout.json')
            require(sha(folder/'layout.json')==layer['layout_sha256'],'Layout hash mismatch '+rel)
            require(layout['schema']=='arch02-hex-v1' and layout['load_words']==23488 and
                    layout['outputs']==layer['outputs']==25344 and
                    layout['layer_number']==layer['layer_number'] and
                    layout['shift']==layer['shift']==12,'Invalid layout '+rel)
            require(set(layout['sha256'])==FILES and layout['sha256']==layer['sha256'],'Incomplete input hashes '+rel)
            files[rel+'/layout.json']=layer['layout_sha256']
            for name,h in sorted(layout['sha256'].items()):
                require(sha(folder/name)==h,'Data file changed '+rel+'/'+name)
                files[rel+'/'+name]=h
            tasks.append(dict(key=rel.replace('/','_'),relative_path=rel,
                              sample=sample['sample'],wav=sample['wav'],layer=layer['layer_number']))
    require(len(tasks)==1200,'Expected 1200 complete matrices')
    return tasks,files

def image_base(elf):
    raw=elf.read_bytes()
    require(raw[:7]==b'\x7fELF\x01\x01\x01','Expected ELF32 little endian')
    h=struct.unpack_from('<HHIIIIIHHHHHH',raw,16)
    require(h[1]==243 and h[3]==0x80000000,'Unexpected firmware architecture/entry')
    image=bytearray(262144)
    for i in range(h[9]):
        typ,off,va,pa,filesz,memsz,flags,align=struct.unpack_from('<IIIIIIII',raw,h[4]+i*h[8])
        if typ!=1 or not filesz:continue
        require(0x80000000<=pa<pa+filesz<=0x8000fff0 and off+filesz<=len(raw),'Invalid ELF segment')
        image[pa-0x80000000:pa-0x80000000+filesz]=raw[off:off+filesz]
    return image

def firmware(image,task):
    words=[int(x,16) for x in (task/'load.hex').read_text().split()]
    require(len(words)==23488 and all(0<=x<=65535 for x in words),'Invalid firmware input')
    memory=bytearray(image)
    struct.pack_into('<I',memory,0xfff0,read(task/'layout.json')['shift'])
    struct.pack_into('<23488H',memory,0x10000,*words)
    # The accepted images were built on Windows. Preserve their bytes exactly.
    return ''.join('%02x\r\n'%x for x in memory).encode('ascii')

def verified_case(run,task,reference):
    record=read(run/'summary.json')
    require(record['status']=='passed' and record['outputs']==25344 and
            record['cpu_executed'] is True,'Case did not pass')
    for name,h in record['artifacts'].items():
        require(name in ('capture.csv','cpu.log','firmware.verilog'),'Unexpected artifact name')
        require(sha(run/name)==h,'Case artifact changed '+str(run/name))
    require(set(record['artifacts'])=={'capture.csv','cpu.log','firmware.verilog'},'Missing case artifact')
    require(record['input_sha256']==sha(task/'load.hex'),'Case inputs changed')
    _,values,sats=reference
    audit.capture(run/'capture.csv',values,sats,2)
    marker=re.search(r'ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=(\d+) saturated=(\d+)',
                     (run/'cpu.log').read_text(errors='replace'))
    require(marker is not None and int(marker.group(1))==record['cycles']>0 and
            int(marker.group(2))==record['saturated']==sum(sats),'CPU counters changed')
    return record

def check_compile(folder,expected):
    require(sha(folder/'simv')==expected,'Compiled executable changed')
    for path,h in read(folder/'source_inputs.json').items():
        require(sha(Path(path))==h,'Compiled input changed '+path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--baseline-audit',type=Path,required=True)
    p.add_argument('--baseline-audit-sha256',required=True)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--data-manifest-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--resume',action='store_true')
    a=p.parse_args();baseline=a.baseline.resolve();out=a.output.resolve();data=a.data.resolve()
    out.relative_to(ROOT)
    require(out!=ROOT and out.parent==ROOT/'runs','Output must be an immediate child of bundle/runs')
    own=audit.manifest(ROOT);target=audit.manifest(baseline)
    require({k:v for k,v in own['files'].items() if audit.runtime(k)}==
            {k:v for k,v in target['files'].items() if audit.runtime(k)},'Runtime differs from accepted hardware')
    require(sha(a.baseline_audit)==a.baseline_audit_sha256,'Baseline audit changed')
    accepted=read(a.baseline_audit)
    require(accepted['status']=='passed' and accepted['target_bundle']==str(baseline) and
            accepted['target_source_commit']==target['source_commit'],'Wrong baseline acceptance')
    for name in ('soc','icb','dc_accel','dc_shared'):
        run,report=audit.stage(baseline,accepted['session'],name)
        require(sha(run/'summary.json')==accepted['stages'][name]['summary_sha256'],'Baseline stage changed')
        if name.startswith('dc_'):
            for rel,h in report['artifacts'].items():
                artifact=(run/rel).resolve();artifact.relative_to(run)
                require(sha(artifact)==h,'Reused DC artifact changed')
            for path,h in report['library_inputs'].items():require(sha(Path(path))==h,'Reused DC library changed')
    identity=dict(tool_source_commit=own['source_commit'],script_sha256=sha(Path(__file__)),
                  runtime_source_commit=target['source_commit'],baseline=str(baseline),
                  baseline_audit_sha256=a.baseline_audit_sha256,data=str(data),
                  data_manifest_sha256=a.data_manifest_sha256)
    cfg=read(ROOT/'handoff/team/server_config.json');lock=Path(cfg['server_root'])/'.arch02_team_lock'
    lock.mkdir();server.LOCK=lock
    save(lock/'owner.json',dict(pid=os.getpid(),host=socket.gethostname(),bundle=str(ROOT),session=out.name))
    state=None
    try:
        if a.resume:
            candidate=read(out/'state.json')
            require(candidate['identity']==identity,'Resume identity changed; create a new run')
            require(candidate['status']!='passed','Already passed; use the existing record')
            state=candidate
        else:
            out.mkdir(parents=True,exist_ok=False)
            state=dict(status='running',phase='input_validation',identity=identity,pid=os.getpid(),
                       started=datetime.datetime.now().isoformat(),total_cases=1200,completed_cases=0,
                       software_cases=0,outputs=0,physical_signoff=False,official_precision_verified=False)
        state.update(status='running',pid=os.getpid(),phase='input_validation');save(out/'state.json',state)
        tasks,files=dataset(data,a.data_manifest_sha256)
        snapshot=out/'inputs';snapshot.mkdir(exist_ok=True)
        for rel,h in files.items():
            dst=snapshot/rel
            if dst.exists():require(sha(dst)==h,'Snapshot changed '+rel)
            else:
                require(not a.resume,'Resume missing snapshot '+rel)
                raw=(data/rel).read_bytes();require(hashlib.sha256(raw).hexdigest()==h,'Source changed while copying')
                dst.parent.mkdir(parents=True,exist_ok=True)
                with dst.open('xb') as f:f.write(raw)
        snapshot_files=read(out/'input_files.json') if a.resume else files
        require(snapshot_files==files,'Input file set changed')
        if not a.resume:save(out/'input_files.json',files)
        spec=importlib.util.spec_from_file_location('batch_reference',ROOT/'workspaces/arch02/vcs_run.py')
        ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
        fw=read(ROOT/'firmware/manifest.json');require(sha(ROOT/'firmware/driver.elf')==fw['elf_sha256'],'Firmware ELF changed')
        base=image_base(ROOT/'firmware/driver.elf')
        # Reproduce every previously CPU-tested image before using the packer for new data.
        for case,meta in fw['images'].items():
            require(hashlib.sha256(firmware(base,ROOT/'validated_data'/case)).hexdigest()==meta['sha256'],
                    'Firmware image generator differs from tested images')
        state['phase']='software';state['software_cases']=0;save(out/'state.json',state)
        for task in tasks:
            ref.reference(snapshot/task['relative_path'])
            state['software_cases']+=1
            if state['software_cases']%12==0:
                save(out/'state.json',state);print('BATCH_SOFTWARE',state['software_cases'],flush=True)
        compile_dir=out/'compile'
        if a.resume:
            check_compile(compile_dir,state['simv_sha256'])
        else:
            state['phase']='compile';save(out/'state.json',state);compile_dir.mkdir()
            # Same committed compiler/platform flow; empty cases means compile only.
            server.vcs('soc',cfg,compile_dir,Path('/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master'),[])
            state['simv_sha256']=sha(compile_dir/'simv');save(out/'state.json',state)
        state['phase']='cpu';state['completed_cases']=0;state['outputs']=0
        cases=out/'cases';cases.mkdir(exist_ok=True);records=[]
        for task in tasks:
            folder=snapshot/task['relative_path'];reference=ref.reference(folder)
            run=cases/task['key'];state['current_case']=task['key'];save(out/'state.json',state)
            if (run/'summary.json').is_file():
                require(a.resume,'Unexpected existing case')
                record=verified_case(run,folder,reference)
                require(record['task']==task,'Completed case identity changed')
            else:
                # Preserve any incomplete attempt; a resume gets a new attempt directory.
                if run.exists():
                    require(a.resume,'Unexpected incomplete case')
                    n=1
                    while (cases/(task['key']+'_attempt_%03d'%n)).exists():n+=1
                    run.rename(cases/(task['key']+'_attempt_%03d'%n))
                run.mkdir();(run/'firmware.verilog').write_bytes(firmware(base,folder))
                text=server.call([compile_dir/'simv','+DATA_DIR='+str(folder),'+CAPTURE='+str(run/'capture.csv'),
                                  '+SHIFT=12','+TESTCASE='+str(run/'firmware')],run,'cpu.log')
                match=re.search(r'ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=(\d+) saturated=(\d+)',text)
                require(match is not None,'Missing E203 acceptance '+task['key'])
                _,values,sats=reference;audit.capture(run/'capture.csv',values,sats,2)
                require(int(match.group(2))==sum(sats),'CPU saturation mismatch')
                record=dict(status='passed',task=task,outputs=25344,cpu_executed=True,cycles=int(match.group(1)),
                            saturated=int(match.group(2)),input_sha256=sha(folder/'load.hex'),
                            artifacts={name:sha(run/name) for name in ('capture.csv','cpu.log','firmware.verilog')})
                save(run/'summary.json',record);verified_case(run,folder,reference)
            records.append(dict(task=task,summary_sha256=sha(run/'summary.json'),cycles=record['cycles'],
                                saturated=record['saturated'],outputs=record['outputs']))
            state['completed_cases']+=1;state['outputs']+=25344;save(out/'state.json',state)
            print('BATCH_CPU_PASS',state['completed_cases'],task['key'],flush=True)
        require(state['completed_cases']==1200 and state['outputs']==30412800,'Incomplete batch')
        check_compile(compile_dir,state['simv_sha256']);audit.manifest(ROOT);audit.manifest(baseline)
        require(dataset(data,a.data_manifest_sha256)[1]==files,'External data changed during run')
        for rel,h in files.items():require(sha(snapshot/rel)==h,'Snapshot changed during run')
        state.update(status='passed',phase='complete',finished=datetime.datetime.now().isoformat())
        save(out/'summary.json',dict(state=state,cases=records,
             scope='100_sample_1200_matrix_real_e203_not_speech_classification',reused_dc=accepted['stages']))
        state['summary_sha256']=sha(out/'summary.json');save(out/'state.json',state)
        print('ARCH03_BATCH_PASS samples=100 cases=1200 outputs=30412800 cpu_executed=true',flush=True)
    except BaseException as exc:
        if state is not None:
            state.update(status='failed',error=str(exc),finished=datetime.datetime.now().isoformat())
            save(out/'state.json',state)
        raise
    finally:
        owner=read(lock/'owner.json')
        if (server.ACTIVE_CHILD is None or server.ACTIVE_CHILD.poll() is not None) and owner.get('pid')==os.getpid():
            (lock/'owner.json').unlink();lock.rmdir()

if __name__=='__main__':main()
