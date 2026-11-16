"""N1 mapped result/saturation observer using independently probed ports.

Internal totals are intentionally outside this mapped functional check. No
reference total is copied into a capture. ASIC RTL keeps its strict total33
observer; mapped cases use an explicit four-field result/saturation contract.
"""
from p80_mapped_aliases import generate as base_generate, DEFAULT_BINDINGS, once

PROOF = ('ARCH03_C80_GATE_PROOF count=25344 numeric=000e0c20 shift=10 '
         'fields=result,saturated internal_total_observable=false')


def generate(source, bindings, depth):
    if depth!=2:raise ValueError('C80 freezes metadata depth2')
    if bindings.get('decoder') != bindings.get('accel', '')+'.decoder':
        raise ValueError('N1 gate requires the actual decoder instance')
    source = once(source,
        'if(a3_layout!=32\'h00100006)$fatal(1,"Unsupported observer layout");',
        'if(a3_layout!=32\'h00100006)$fatal(1,"N1 gate requires explicit numeric layout6");')
    for line in ('reg signed [32:0] n1_expected_total[0:25343],n1_actual_total[0:25343];',
                 'reg n1_total_seen[0:25343];',
                 'integer n1_total_count=0,n1_pe,n1_slot,n1_index;',
                 '    $readmemh({a3_dir,"/total.hex"},n1_expected_total);',
                 "        n1_total_seen[a3_i]=0;n1_actual_total[a3_i]='bx;"):
        source = once(source, line, '')
    source = once(source, "(^n1_expected_total[a3_i])===1'bx || ", '')
    begin = '        // Passive pre-requantization audit:'
    end = '        if(`A3DMA.core_out_valid && `A3DMA.core_out_ready)begin'
    if source.count(begin)!=1 or source.count(end)!=1 or source.index(begin)>=source.index(end):
        raise ValueError('N1 production total-observer block changed')
    source = source[:source.index(begin)]+source[source.index(end):]
    source = once(source, '!n1_total_seen[a3_index] || ', '')
    source = once(source, 'n1_total_count!=25344 || ', '')
    source = once(source,
        '$fdisplay(a3_file,"%0d,%0d,%0d,%0d,%0d",a3_index/256,a3_index%256,$signed(a3_value),a3_actual_sat[a3_index],n1_actual_total[a3_index]);',
        '$fdisplay(a3_file,"%0d,%0d,%0d,%0d",a3_index/256,a3_index%256,$signed(a3_value),a3_actual_sat[a3_index]);')
    source = once(source,
        '$display("ARCH03_N1_TOTAL_PROOF count=%0d numeric=000e0c20 shift=10 coordinates=unique",n1_total_count);',
        '$display("'+PROOF+'");')
    if any(token in source for token in ('n1_total', 'n1_expected_total', 'n1_actual_total', 'converted_total')):
        raise ValueError('Mapped observer still references an unprobed internal total')
    return ('// N1 mapped functional scope: actual result/saturation at write ACK.\n'
            '// internal_total_observable=false; total_checked=false; no reference-total substitution.\n'
            +base_generate(source, bindings, depth))
