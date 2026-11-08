"""Exercise escaped mapped SRAM paths using a storage-only local substitute.

This verifies loader binding and all 16384 physical rows, not CPU or gates.
"""
import argparse,json,re
from datetime import datetime
from pathlib import Path
from asic_boot import prepare
from gate_soc import mapped_loader,escaped_hierarchy
from local_verify import ROOT,A3,run,sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--vivado-bin',type=Path,required=True);a=p.parse_args()
    folder=ROOT/'local_runs'/('gate_loader_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'));folder.mkdir()
    root='u_e203_subsys_top/u_e203_subsys_main/u_e203_cpu_top/u_e203_srams/u_e203_itcm_ram/u_e203_itcm_gnrl_ram'
    rows=[dict(kind='sram',owner='itcm',reference='RAMSP4096X16',
               instance=root+'/banks[%d].halves[%d].memory/memory'%(b,h)) for b in range(8) for h in range(4)]
    image=folder/'source.verilog'
    image.write_text(''.join('%02x\n'%((i*37+(i>>8)*13+(i>>16)*19)&255) for i in range(262144)),encoding='ascii')
    prepared=prepare(image,folder/'boot')
    loader=folder/'arch03_asic_boot.svh';loader.write_text(mapped_loader({'rows':rows}))
    modules=['`timescale 1ns/1fs\nmodule RAMSP4096X16; reg [127:0] mem[0:511]; endmodule',
             'module half; RAMSP4096X16 memory(); endmodule']
    banks='module itcm;\n'+''.join('half \\banks[%d].halves[%d].memory ();\n'%(b,h) for b in range(8) for h in range(4))+'endmodule'
    modules.append(banks)
    parts=root.split('/');child='itcm'
    for i in reversed(range(len(parts))):
        parent='e203_soc_top' if i==0 else 'level%d'%i
        modules.append('module %s; %s %s(); endmodule'%(parent,child,parts[i]));child=parent
    checks=[]
    for row in rows:
        path='u_e203_soc_top.'+escaped_hierarchy(row['instance'])+'.mem'
        bank,half=map(int,re.search(r'banks\[(\d+)\]\.halves\[(\d+)\]',row['instance']).groups())
        values=(folder/'boot'/('itcm_b%02d_h%d.hex'%(bank,half))).read_text().split()
        for index,value in enumerate(values):
            checks.append('if(%s[%d] !== 128\'h%s) $fatal(1,"Mapped row mismatch");'%(path,index,value))
    modules.append('''`timescale 1ns/1fs
module tb_top;
reg rst_n=0;
e203_soc_top u_e203_soc_top();
`include "arch03_asic_boot.svh"
initial begin
  #1;
  if(!arch03_boot_ready) $fatal(1,"Not ready");
  @CHECKS@
  rst_n=1;
  #1;
  $display("ARCH03_MAPPED_LOADER_LOCAL_PASS rows=16384 cpu_executed=false vendor_verified=false");
  $finish;
end
endmodule
'''.replace('@CHECKS@','\n'.join(checks)))
    tb=folder/'tb_top.sv';tb.write_text('\n'.join(modules))
    tool=lambda name:a.vivado_bin/(name+'.bat')
    run([tool('xvlog'),'--sv','-i',folder,tb],folder,'compile.log')
    run([tool('xelab'),'tb_top','-debug','typical','-s','mapped_loader'],folder,'elaborate.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    options=folder/'run.options';options.write_text('-testplusarg BOOT_DIR='+(folder/'boot').as_posix()+'\n')
    text=run([tool('xsim'),'mapped_loader','-tclbatch','run.tcl','-f',options],folder,'simulate.log')
    if 'ARCH03_MAPPED_LOADER_LOCAL_PASS rows=16384 cpu_executed=false vendor_verified=false' not in text:
        raise ValueError('Mapped loader substitute failed')
    result=dict(status='passed',scope='escaped_path_storage_substitute_only',cpu_executed=False,vendor_verified=False,
                rows=16384,macros=32,preparation=prepared,inputs={str(p.relative_to(ROOT)):sha(p) for p in (loader,tb,A3/'scripts/gate_soc.py')})
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('LOCAL_MAPPED_LOADER_PASS',folder)


if __name__=='__main__':main()
