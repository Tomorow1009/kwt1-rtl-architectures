"""Generate a port-only DMA16 monitor candidate; never patches frozen files.

Actual mapped hierarchy must be probed separately. The default paths are for
offline RTL fixtures only. A generated file is not a gate-simulation acceptance.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MEM='u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems'
DEFAULT_BINDINGS=dict(accel=MEM+'.u_arch03_accel',core=MEM+'.u_arch03_accel.core',
                      shared=MEM+'.u_arch03_shared',arb=MEM+'.u_arch03_arb',router=MEM+'.u_arch03_router')
FIELDS=('cmd_valid','cmd_ready','cmd_addr','cmd_read','cmd_wdata','cmd_wmask',
        'rsp_valid','rsp_ready','rsp_rdata','rsp_err')


def generate(source,bindings):
    if set(bindings)!=set(DEFAULT_BINDINGS):raise ValueError('Exactly accel/core/shared/arb/router bindings required')
    for role,path in bindings.items():
        if not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+',path):
            raise ValueError('Binding needs a simple probed instance path: '+role)
    text=source
    for line in ('`define A3MEM '+MEM,'`define A3DMA `A3MEM.u_arch03_accel','`undef A3DMA','`undef A3MEM'):
        if text.count(line)!=1:raise ValueError('Production monitor macro changed: '+line)
        text=text.replace(line,'')
    mapping={'`A3MEM.clk':bindings['accel']+'.clk','`A3MEM.rst_n':bindings['accel']+'.rst_n',
             '`A3MEM.a3_arb_pending || `A3MEM.a3_router_pending':'a3_gate_global_pending',
             '`A3DMA.fifo_count_q==0 && !`A3DMA.half_q && !`A3DMA.load_word_q':'a3_gate_fifo_empty',
             '`A3DMA.core_done_q':'a3_gate_core_done','`A3DMA.error_q!=0':'a3_gate_proof_failed'}
    core_names=dict(core_out_valid='out_valid',core_out_ready='out_ready',core_row='out_row',
                    core_col='out_column',core_result='result',core_sat='saturated')
    for old,new in core_names.items():mapping['`A3DMA.'+old]=bindings['core']+'.'+new
    for name in FIELDS:
        mapping['`A3MEM.expl_axi_icb_'+name]=bindings['accel']+'.'+name
        mapping['`A3MEM.a3_dma_'+name]=bindings['accel']+'.dma_'+name
        mapping['`A3MEM.a3_mem_'+name]=bindings['shared']+'.'+name
    for old in sorted(mapping,key=len,reverse=True):text=text.replace(old,mapping[old])
    if '`A3MEM' in text or '`A3DMA' in text:raise ValueError('Unmapped production monitor dependency')
    # Every successful mailbox must require the actual final MMIO proof, even
    # if an earlier response observer happened to publish a timing window.
    guard='if(!a3_window_finished || a3_window_failed || a3_window_active)'
    if text.count(guard)!=1:raise ValueError('Production mailbox guard changed')
    text=text.replace(guard,'if(!a3_window_finished || a3_window_failed || a3_window_active ||\n                           !a3_gate_proof_complete || a3_gate_proof_failed)')
    connections=['.clk(a3_mon_clk)','.rst_n(a3_mon_rst_n)']
    connections+=['.mmio_%s(%s.%s)'%(name,bindings['accel'],name) for name in FIELDS]
    connections+=['.dma_cmd_valid(%s.dma_cmd_valid)'%bindings['accel'],
                  '.core_output_fire(%s.out_valid && %s.out_ready)'%(bindings['core'],bindings['core']),
                  '.output_acks(a3_output_acks)']
    for role in ('arb','router'):
        connections+=['.%s_%s(%s.%s)'%(role,name,bindings[role],name)
                      for name in ('cmd_valid','cmd_ready','rsp_valid','rsp_ready')]
    connections+=['.global_pending(a3_gate_global_pending)','.fifo_empty_proven(a3_gate_fifo_empty)',
                  '.core_done_proven(a3_gate_core_done)','.proof_complete(a3_gate_proof_complete)',
                  '.proof_failed(a3_gate_proof_failed)']
    prefix='// Generated offline candidate. Real mapped hierarchy/proof remains unverified.\n'
    prefix+='wire a3_gate_global_pending,a3_gate_fifo_empty,a3_gate_core_done;\n'
    prefix+='wire a3_gate_proof_complete,a3_gate_proof_failed;\n'
    # Declare a3_mon_* and a3_output_acks through the original monitor before
    # the instance, avoiding accidental implicit 1-bit nets in older tools.
    suffix='\narch03_dma16_gate_proof a3_gate_proof(\n    '+',\n    '.join(connections)+'\n);\n'
    return prefix+text+suffix


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--monitor',type=Path,default=Path(__file__).resolve().parents[1]/'tb/arch03_dma16_monitor.svh')
    parser.add_argument('--bindings',type=Path,help='JSON accel/core/shared/arb/router instance paths from an independent probe')
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Refusing to overwrite an existing generated monitor')
    bindings=json.loads(args.bindings.read_text()) if args.bindings else DEFAULT_BINDINGS
    source=args.monitor.read_bytes();generated=generate(source.decode('utf8'),bindings)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(generated)
    manifest=dict(status='offline_candidate',gate_simulation_verified=False,
                  binding_paths_require_actual_mapped_probe=True,bindings=bindings,
                  original_monitor_sha256=hashlib.sha256(source).hexdigest(),
                  generated_monitor_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                  additional_module='arch03_dma16_gate_proof',
                  proof='post-output-ACK real MMIO STATUS/PENDING/COMPLETION/ERROR responses; endpoint stays last DMA ACK')
    args.output.with_suffix(args.output.suffix+'.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('DMA16_GATE_MONITOR_CANDIDATE '+str(args.output))


if __name__=='__main__':main()
