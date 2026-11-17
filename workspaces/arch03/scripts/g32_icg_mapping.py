"""Inventory actual mapped clock gates and their register clock endpoints.

The map is evidence, not an energy result. No synthesized file is changed.
Legal latches internal to characterized ICG library cells are not RTL latches.
"""
from collections import Counter
import re
from partition_synth_contract import require

CELL='CLKLANAQV4_12TR40'
TCL=r'''
set g32_icgs [get_cells -hierarchical -filter "ref_name == CLKLANAQV4_12TR40"]
set g32_register_clocks [all_registers -clock_pins]
array set g32_clock_names {}
foreach_in_collection p $g32_register_clocks {set g32_clock_names([get_object_name $p]) 1}
set g32_inventory [open g32_icg_mapping.tsv w]
puts $g32_inventory "schema\tg32-mapped-icg-v1"
foreach_in_collection cell $g32_icgs {
    set name [get_object_name $cell]
    puts $g32_inventory "cell\t$name\t[get_attribute $cell ref_name]"
    foreach pin {CK E TE Q} {
        set object [get_pins -of_objects $cell -filter "name == $pin"]
        if {[sizeof_collection $object] != 1} {error "G32 ICG pin missing/ambiguous: $name/$pin"}
        puts $g32_inventory "pin\t$name\t$pin\t[get_object_name $object]\t[get_attribute $object direction]"
    }
    if {![string match */u_arch03_accel/* $name]} {continue}
    set q [get_pins -of_objects $cell -filter "name == Q"]
    set endpoints [all_fanout -from $q -flat -endpoints_only]
    foreach_in_collection p $endpoints {
        set endpoint [get_object_name $p]
        set kind other
        if {[info exists g32_clock_names($endpoint)]} {set kind register_clock}
        puts $g32_inventory "endpoint\t$name\t$endpoint\t$kind"
    }
}
puts $g32_inventory "total\t[sizeof_collection $g32_icgs]"
close $g32_inventory
'''


def inventory(text):
    cells={};pins={};endpoints={};total=None
    lines=text.splitlines()
    require(lines and lines[0]=='schema\tg32-mapped-icg-v1','Missing mapped ICG schema')
    for line in lines[1:]:
        f=line.split('\t')
        if f[0]=='cell':
            require(len(f)==3 and f[1] not in cells and f[2]==CELL,'Malformed/duplicate ICG cell')
            cells[f[1]]=f[2];pins[f[1]]={};endpoints[f[1]]={}
        elif f[0]=='pin':
            require(len(f)==5 and f[1] in cells and f[2] not in pins[f[1]],'Unknown/duplicate ICG pin')
            require(f[2] in ('CK','E','TE','Q') and f[3]==f[1]+'/'+f[2] and
                    f[4]==('out' if f[2]=='Q' else 'in'),'ICG pin polarity/direction differs')
            pins[f[1]][f[2]]=f[3]
        elif f[0]=='endpoint':
            require(len(f)==4 and f[1] in cells and f[2] not in endpoints[f[1]] and
                    f[3] in ('register_clock','other'),'Unknown/duplicate gate endpoint')
            endpoints[f[1]][f[2]]=f[3]
        elif f[0]=='total':
            require(len(f)==2 and total is None and f[1].isdigit(),'Invalid ICG count')
            total=int(f[1])
        else:raise ValueError('Unrecognized ICG inventory record')
    require(total==len(cells) and total>0,'Missing/inconsistent ICG inventory')
    require(all(set(row)=={'CK','E','TE','Q'} for row in pins.values()),'Incomplete ICG pins')
    new={n:e for n,e in endpoints.items() if '/u_arch03_accel/' in n}
    require(new and all(e for e in new.values()),'Missing/unused mapped accelerator ICG')
    require(all(k=='register_clock' for e in new.values() for k in e.values()),
            'New ICG drives an unreviewed non-register-clock endpoint')
    all_pins=[p for e in new.values() for p in e]
    require(len(set(all_pins))==len(all_pins),'Register clock driven by multiple new ICGs')
    require(all('/u_arch03_accel/' in p for p in all_pins),'Accelerator gate reaches fixed SoC storage')
    forbidden=re.compile(r'(?:metadata|valid|accepted_count|active_block|error|owner|credit|irq|command|descriptor)',re.I)
    suspicious=[p for p in all_pins if forbidden.search(p)]
    require(not suspicious,'Control/valid register reached by data gate: '+repr(suspicious[:4]))
    domains=Counter()
    for name in new:
        domains['array' if '/array/' in name else 'core' if '/core/' in name else
                'transport' if '/transport/' in name else 'unclassified']+=1
    require(not domains.get('unclassified'),'Unclassified G32 clock gate hierarchy')
    return dict(schema='g32-mapped-clock-domain-v1',library_cell=CELL,
        actual_g32_cells=len(new),reused_platform_cells=total-len(new),total_cells=total,
        gated_register_clock_pins=len(all_pins),domains=dict(domains),rows=new,
        static_TE_verified=False,clock_gating_timing_verified=False,energy_verified=False)
