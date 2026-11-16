"""Own C80 RTL decoder: every mode, Rice bound, malformed input and restart.

Expected halves come from independently assembled original matrix coordinates,
not from reshaping the RTL stream. No CPU/SRAM or full-stage PASS is implied.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct

import c80_codec as codec
import c80_codec_candidate as c
import n1_codec
from local_verify import ROOT,A3,run,sha


def forced_modes(rice_k):
    x=[]
    for row in range(99):
        x.append([-8192,8191]+[((row+k)%17)-8 for k in range(62)])
    weights=[];biases=[]
    for tile in range(16):
        weights.append([0 if i%16==0 else -2048 if i==1 else 2047 if i==2 else (i%7)-3 for i in range(1024)])
        biases.append([[-(1<<31),(1<<31)-1,-1,0,1][i%5] for i in range(16)])
    canonical=[v&65535 for row in x for v in row]
    body=b'';x_offsets=[];w_offsets=[]
    for tile in range(16):
        w=weights[tile];b=biases[tile];mode=tile%5
        canonical.extend(v&65535 for v in w)
        for v in b:
            canonical.extend(((v&((1<<40)-1))>>s)&65535 for s in (0,16,32))
        w_offsets.append(len(body)+32)
        if mode==0:p=c.descriptor(0,12)+c.pack((v,12) for v in w)
        elif mode in (1,2):
            table=[c.width(w[i::16] if mode==1 else w[i*64:(i+1)*64]) for i in range(16)]
            p=c.descriptor(mode)+c.pack((v,4) for v in table)+c.pack((v,table[i%16 if mode==1 else i//64]) for i,v in enumerate(w))
        elif mode==3:p=c.descriptor(3,rice_k)+c.pack(f for v in w for f in c.rice_fields(v,rice_k,12))
        else:p=c.descriptor(4)+c.pack((rice_k,4) for _ in range(16))+c.pack(f for v in w for f in c.rice_fields(v,rice_k,12))
        body+=p+struct.pack('<16i',*b)
        if tile==0:
            for row,v in enumerate(x):
                mode=row%7
                if row%8==0 and mode in (4,6):mode=0
                x_offsets.append(len(body)+32)
                adjacent=[v[i]-v[i-1] for i in range(1,64)]
                previous=[a-b for a,b in zip(v,x[row-1])] if row else []
                if mode==0:p=c.descriptor(0,14)+c.pack((a,14) for a in v)
                elif mode==1:p=c.descriptor(1,14)+c.pack((a,14) for a in v)
                elif mode==2:p=c.descriptor(2,14)+struct.pack('<h',min(v))+c.pack((a-min(v),14) for a in v)
                elif mode==3:p=c.descriptor(3,15)+struct.pack('<h',v[0])+c.pack((a,15) for a in adjacent)
                elif mode==4:p=c.descriptor(4,15)+c.pack((a,15) for a in previous)
                elif mode==5:p=c.descriptor(5,rice_k)+struct.pack('<h',v[0])+c.pack(f for a in adjacent for f in c.rice_fields(a,rice_k,15))
                else:p=c.descriptor(6,rice_k)+c.pack(f for a in previous for f in c.rice_fields(a,rice_k,15))
                body+=p
    body+=b'\0'*((-len(body))%4)
    encoded=struct.pack('<8I',codec.MAGIC,codec.VERSION,codec.LAYOUT,0,len(body)+32,23232,46464,codec.NUMERIC_FORMAT)+body
    raw=struct.pack('<23488H',*canonical)
    assert codec.decode(encoded)==raw
    return raw,encoded,x_offsets,w_offsets


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--vivado-bin',required=True,type=Path)
    ap.add_argument('--data',required=True,type=Path)
    ap.add_argument('--quick',action='store_true')
    ap.add_argument('--only-cases',nargs='+',help='Explicit supplemental scenarios; never reported as the full suite')
    args=ap.parse_args()
    out=ROOT/'local_runs'/('c80_decoder_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'));out.mkdir(parents=True)
    sources=[A3/'rtl/arch03_c80_decoder.sv',A3/'tb/tb_arch03_c80_decoder.sv']
    tracked=sources+[Path(__file__).resolve(),Path(codec.__file__),Path(c.__file__),Path(n1_codec.__file__)]
    hashes={p:sha(p) for p in tracked};tool=lambda n:args.vivado_bin/(n+'.bat')
    run([tool('xvlog'),'--sv']+sources,out,'compile.log')
    run([tool('xelab'),'tb_arch03_c80_decoder','-debug','typical','-s','decoder'],out,'elaborate.log')
    (out/'run.tcl').write_text('run all\nquit\n')
    cases=[]
    names=['layer_01'] if args.quick else ['layer_%02d'%i for i in range(1,13)]+['extremes','rounding']
    for name in names:
        raw=(args.data/name/'load.bin').read_bytes();cases.append((name,raw,codec.encode(raw),0))
    raw=(args.data/'extremes/load.bin').read_bytes();forced=codec.encode(raw,force_raw=True)
    cases.append(('forced_raw_extremes',raw,forced,0))
    for k in ([0] if args.quick else range(12)):
        modes_raw,modes,x_at,w_at=forced_modes(k);cases.append(('all_modes_k%d'%k,modes_raw,modes,0))
    def mutate(name,blob,offset,value,code,fmt='<I',reference=raw):
        b=bytearray(blob);struct.pack_into(fmt,b,offset,value);cases.append((name,reference,bytes(b),code))
    if not args.quick:
        for i in range(8):mutate('bad_header%d'%i,forced,i*4,0xdeadbeef,2)
        mutate('raw_w_sign',forced,32,0x0800,8,'<H')
        mutate('raw_x_sign',forced,32+2048+64,0x2000,8,'<H')
        for name,at,value in [('weight_mode',32,0x000f),('weight_table',w_at[1]+2,0xffff),
                              ('x_first_prediction',x_at[0],4),('x_descriptor_reserved',x_at[0],0x01e0)]:
            mutate(name,modes,at,value,3,'<H',modes_raw)
        mutate('x_initial_out_of_range',modes,x_at[2]+2,0x2000,8,'<H',modes_raw)
        mutate('x_padding',modes,x_at[4]-1,modes[x_at[4]-1]|0x80,5,'<B',modes_raw)
        mutate('x_previous_overflow',modes,x_at[4]+2,0x7fff,8,'<H',modes_raw)
        mutate('x_delta_overflow',modes,x_at[2]+2,8191,8,'<H',modes_raw)
        shortened=bytearray(modes[:-4]);struct.pack_into('<I',shortened,16,len(shortened))
        cases.append(('truncated',modes_raw,bytes(shortened),6))
        longer=bytearray(modes+b'\0'*4);struct.pack_into('<I',longer,16,len(longer))
        cases.append(('excess',modes_raw,bytes(longer),5))
        zero_raw=bytes(46976);cases.append(('all_zero_zero_width',zero_raw,codec.encode(zero_raw),0))
    if args.only_cases:
        assert set(args.only_cases)<={row[0] for row in cases},'Unknown selected scenario'
        cases=[row for row in cases if row[0] in args.only_cases]
    results=[]
    for name,raw,encoded,error in cases:
        case=out/name;case.mkdir();wire=n1_codec.base.wire_raw(raw)
        if not error:assert codec.decode_wire(encoded)==wire
        (case/'load32.hex').write_text(''.join('%08x\n'%v[0] for v in struct.iter_unpack('<I',encoded)))
        (case/'raw16.hex').write_text(''.join('%04x\n'%v[0] for v in struct.iter_unpack('<H',wire)))
        opts=out/(name+'.options')
        opts.write_text('decoder\n-tclbatch run.tcl\n-testplusarg DATA=%s\n-testplusarg WORDS=%d\n-testplusarg BAD=%d\n'%(case.as_posix(),len(encoded)//4,error))
        text=run([tool('xsim'),'-f',opts],out,name+'.log')
        expected='C80_DECODER_ERROR_PASS code=%d'%error if error else 'C80_DECODER_SUITE_PASS'
        if expected not in text:raise ValueError('Missing C80 decoder result '+name)
        results.append(dict(case=name,expected_error=error,words=len(encoded)//4,encoded_sha256=hashlib.sha256(encoded).hexdigest(),log_sha256=sha(out/(name+'.log'))))
        print('PASS C80 decoder '+name,flush=True)
    assert all(sha(p)==h for p,h in hashes.items()),'Source changed during run'
    report=dict(status='passed',quick=args.quick,only_cases=args.only_cases,cpu_executed=False,dma_executed=False,
        scope='standalone_c80_decoder_no_e203_no_sram',layout=codec.LAYOUT,cases=results,
        good_tasks_per_case=2,cancellation_points=[32,3111],reset_point=211,long_backpressure_cycles=187,
        source_sha256={str(p):h for p,h in hashes.items()})
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_C80_DECODER_PASS '+str(out),flush=True)


if __name__=='__main__':main()
