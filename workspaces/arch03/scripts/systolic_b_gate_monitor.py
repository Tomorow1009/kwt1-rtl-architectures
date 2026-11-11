"""B/v3 paired-result gate observer, bound only to independently probed ports.

The legacy generator provides the MMIO/fabric drain proof; the B production
observer provides five-row coordinates, paired saturation and v3 stream order.
This entry deliberately rejects v2: a different active decoder needs its own
explicit binding, never an implicit alias to the inactive v3 decoder.
"""
from icb32_gate_monitor import generate as base_generate, DEFAULT_BINDINGS as BASE_BINDINGS

DEFAULT_BINDINGS=dict(BASE_BINDINGS)
DEFAULT_BINDINGS['decoder']=DEFAULT_BINDINGS['accel']+'.decoder_v3'


def generate(source,bindings):
    if bindings.get('decoder')!=bindings.get('accel','')+'.decoder_v3':
        raise ValueError('B/v3 gate observer requires the actual selected decoder_v3 instance')
    old='if(a3_layout!=32\'h00100002 && a3_layout!=32\'h00100003)$fatal(1,"Unsupported observer layout");'
    if source.count(old)!=1:raise ValueError('B observer layout guard changed')
    source=source.replace(old,'if(a3_layout!=32\'h00100003)$fatal(1,"B gate observer requires explicit v3 layout");')
    return base_generate(source,bindings)
