"""Full-address boot loader test with an independent physical-layout substitute."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from asic_boot import prepare,loader_include
from local_verify import A3,ROOT,run,sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True)
    args=p.parse_args()
    folder=ROOT/'local_runs'/('asic_boot_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    image=folder/'source.verilog'
    image.write_text(''.join('%02x\n'%((i*37+(i>>8)*13+(i>>16)*19)&255) for i in range(262144)),encoding='ascii')
    prepare(image,folder/'boot')
    (folder/'arch03_asic_boot.svh').write_text(loader_include())
    lines=[]
    for key,width,value in [('CEN_LOW',1,1),('GWEN_LOW',1,1),('WEN_LOW',1,1),('EMA',3,2),('EMAW',2,0),('RET1N',1,1)]:
        lines.append("`define A02_4096_%s %d'd%d"%(key,width,value))
    (folder/'arch02_sram_config.vh').write_text('\n'.join(lines)+'\n')
    files=[A3/'rtl/arch03_shared_sram.sv',A3/'rtl/arch03_tcm_ram.sv',
           A3/'tb/tcm_physical_pin_mock.sv',A3/'tb/tb_arch03_asic_boot.sv']
    tracked=files+[Path(__file__).resolve(),A3/'scripts/asic_boot.py',folder/'arch03_asic_boot.svh',folder/'arch02_sram_config.vh',image]
    before={p:sha(p) for p in tracked}
    tool=lambda name:args.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-i',folder]+files,folder,'compile.log')
    run([tool('xelab'),'tb_arch03_asic_boot','-debug','typical','-s','boot'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    def simulate(name,boot):
        options=folder/(name+'.options')
        options.write_text('-testplusarg BOOT_DIR='+boot.as_posix()+'\n-testplusarg IMAGE='+image.as_posix()+'\n')
        return run([tool('xsim'),'boot','-tclbatch','run.tcl','-f',options],folder,name+'.log')
    text=simulate('positive',folder/'boot')
    marker='ARCH03_BOOT_MAPPING_PASS bytes=262144 words=32768 macros=32 cpu_executed=false vendor_verified=false'
    if marker not in text:raise ValueError('Boot mapping readback did not complete')
    # A missing macro file must fail before CPU reset would be released.
    missing=folder/'missing';missing.mkdir()
    for p in (folder/'boot').glob('*.hex'):
        if p.name!='itcm_b07_h3.hex':(missing/p.name).write_bytes(p.read_bytes())
    failed=False
    try:text=simulate('missing_macro',missing)
    except RuntimeError:failed=True
    log=(folder/'missing_macro.log').read_text(errors='replace')
    if 'Incomplete ITCM boot macro b7 h3' not in log or marker in log:
        raise ValueError('Missing boot macro did not fail safely')
    for path,digest in before.items():
        if sha(path)!=digest:raise ValueError('Boot test input changed')
    result=dict(status='passed',words=32768,bytes=262144,macros=32,missing_macro_rejected=True,
                cpu_executed=False,vendor_verified=False,scope='physical_layout_substitute_only',
                source_sha256={p.relative_to(ROOT).as_posix():v for p,v in before.items()},
                logs={name:sha(folder/name) for name in ('positive.log','missing_macro.log')})
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('LOCAL_BOOT_MAPPING_PASS',folder)


if __name__=='__main__':main()
