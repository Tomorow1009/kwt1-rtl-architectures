"""Generate a port-bound ICB32 gate observer without retained RTL aliases."""
import re
from dma16_gate_monitor import MEM,FIELDS

DEFAULT_BINDINGS=dict(accel=MEM+'.u_arch03_accel',core=MEM+'.u_arch03_accel.core',
    decoder=MEM+'.u_arch03_accel.decoder',shared=MEM+'.u_arch03_shared',
    arb=MEM+'.u_arch03_arb',router=MEM+'.u_arch03_router')


def once(text,old,new):
    if text.count(old)!=1:raise ValueError('ICB32 production observer changed: '+old)
    return text.replace(old,new)


def generate(source,bindings):
    if set(bindings)!=set(DEFAULT_BINDINGS):raise ValueError('Expected six probed ICB32 modules')
    for role,path in bindings.items():
        if not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+',path):
            raise ValueError('Unsupported probed instance path: '+role)
    text=source
    for line in ('`define A3MEM '+MEM,'`define A3DMA `A3MEM.u_arch03_accel','`undef A3DMA','`undef A3MEM'):
        text=once(text,line,'')
    # Passive counts are advanced in the SAME observer block after comparison,
    # avoiding a simulator scheduling race between separate posedge observers.
    text=once(text,'$fatal(1,"Decoder consumed a word before successful SRAM ACK or with wrong data");',
        '$fatal(1,"Decoder consumed a word before successful SRAM ACK or with wrong data");\n'
        '            a3_gate_committed_words=a3_gate_committed_words+1;')
    text=once(text,'if(`A3DMA.load_fire) begin',
        'if(`A3DMA.load_fire) begin\n'
        '            if(`A3DMA.core_load_count<1 || `A3DMA.core_load_count>4 ||\n'
        '                a3_gate_decoded_halfwords+`A3DMA.core_load_count>23488)$fatal(1,"Gate decoder count");')
    text=once(text,'$fatal(1,"Decoder halfword differs from original layout");',
        '$fatal(1,"Decoder halfword differs from original layout");\n'
        '            a3_gate_decoded_halfwords=a3_gate_decoded_halfwords+`A3DMA.core_load_count;')
    text=once(text,'if(!a3_window_finished || a3_window_failed || a3_window_active)',
        'if(!a3_window_finished || a3_window_failed || a3_window_active ||\n'
        '                           !a3_gate_proof_complete || a3_gate_proof_failed ||\n'
        '                           a3_gate_committed_words!=a3_encoded_words || a3_gate_decoded_halfwords!=23488)')
    mapping={'`A3MEM.clk':bindings['accel']+'.clk','`A3MEM.rst_n':bindings['accel']+'.rst_n',
        '`A3MEM.a3_arb_pending || `A3MEM.a3_router_pending':'a3_gate_global_pending',
        '`A3DMA.transport.empty && !`A3DMA.half_q':'a3_gate_fifo_empty',
        '`A3DMA.core_done_q':'a3_gate_core_done',
        '`A3DMA.error_q!=0':'(a3_gate_proof_failed || '+bindings['core']+'.error || '+bindings['decoder']+'.error)',
        '`A3DMA.input_bytes_q':bindings['decoder']+'.encoded_bytes',
        '`A3DMA.decoded_words':'a3_gate_committed_words',
        '`A3DMA.load_count_q':'a3_gate_decoded_halfwords',
        '`A3DMA.load_fire':'('+bindings['core']+'.load_valid && '+bindings['core']+'.load_ready)'}
    for old,new in dict(core_out_valid='out_valid',core_out_ready='out_ready',core_row='out_row',
        core_col='out_column',core_result='result',core_sat='saturated',
        core_load_count='load_count',core_load_data='load_data').items():
        mapping['`A3DMA.'+old]=bindings['core']+'.'+new
    for old,new in dict(committed_valid='in_valid',committed_ready='in_ready',committed_data='in_data').items():
        mapping['`A3DMA.'+old]=bindings['decoder']+'.'+new
    for name in FIELDS:
        mapping['`A3MEM.expl_axi_icb_'+name]=bindings['accel']+'.'+name
        mapping['`A3MEM.a3_dma_'+name]=bindings['accel']+'.dma_'+name
        mapping['`A3MEM.a3_mem_'+name]=bindings['shared']+'.'+name
    for old in sorted(mapping,key=len,reverse=True):text=text.replace(old,mapping[old])
    if '`A3MEM' in text or '`A3DMA' in text:raise ValueError('Unmapped ICB32 observer alias')
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
    return ('// Generated observer: actual mapped ports must be independently probed.\n'
        'wire a3_gate_global_pending,a3_gate_fifo_empty,a3_gate_core_done;\n'
        'wire a3_gate_proof_complete,a3_gate_proof_failed;\n'
        'integer a3_gate_committed_words=0,a3_gate_decoded_halfwords=0;\n'+text+
        '\narch03_icb32_gate_proof a3_gate_proof(\n    '+',\n    '.join(connections)+'\n);\n')
