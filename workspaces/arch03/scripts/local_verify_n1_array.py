"""Python-integer-referenced N1 array stress; does not claim SRAM/CPU/PPA."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import random
import re
import time
from local_verify_linear16x4 import ROOT, A3, run, sha

SEED = 0x7834a9f1
DIRECTED = 32
BOUNDARIES = [0, 511, 512, 513, -511, -512, -513, 1023,
              -1023, 1024, -1024, 1535, 1536, -1535, -1536, 1]
LIMITS = [(32767 << 10)-1, 32767 << 10, (32767 << 10)+511,
          (32767 << 10)+512, (32767 << 10)+513, 32768 << 10,
          -(32768 << 10)+1, -(32768 << 10), -(32768 << 10)-511,
          -(32768 << 10)-512, -(32768 << 10)-513, -(32769 << 10),
          (1 << 31)-1, -(1 << 31), 2, -2]


def requantize(total):
    """Unbounded Python integers: half away from zero, then signed16 clamp."""
    rounded = (abs(total)+512)//1024
    if total < 0:
        rounded = -rounded
    saturated = int(not -32768 <= rounded <= 32767)
    return max(-32768, min(32767, rounded)), saturated


def values(block, rng):
    if block < 4:
        xv, wv = [(-8192, -2048), (-8192, 2047), (8191, -2048), (8191, 2047)][block]
        x = [[xv]*64 for _ in range(5)]
        w = [[wv]*16 for _ in range(64)]
        bias = [(-(1 << 31) if (c+block)%2 else (1 << 31)-1) for c in range(16)]
    elif block in (4, 5, 10, 11):
        x = [[0]*64 for _ in range(5)]
        w = [[0]*16 for _ in range(64)]
        bias = ([(-1 << 31)]*16 if block == 4 else [(1 << 31)-1]*16 if block == 5
                else BOUNDARIES[:] if block == 10 else LIMITS[:])
    elif block in (6, 7, 8, 9):
        x = [[(8191 if k%2 else -8191) if block in (6, 9) else (-8192 if k%2 else 8191)
              for k in range(64)] for _ in range(5)]
        w = [[((-2048 if c%2 else 2047) if block == 6 else
               (-2048 if k%2 else 2047) if block == 7 else
               (k-rng.randrange(64)) if block == 8 else (2 if c%2 else -2))
              for c in range(16)] for k in range(64)]
        bias = BOUNDARIES[:]
    elif block < DIRECTED:
        x = [[1 if block%2 else -1 for _ in range(64)] for _ in range(5)]
        w = [[(c-8) for c in range(16)] for _ in range(64)]
        targets = BOUNDARIES if block%2 else LIMITS
        bias = []
        for c in range(16):
            dot = sum(x[0][k]*w[k][c] for k in range(64))
            bias.append(max(-(1 << 31), min((1 << 31)-1, targets[(c+block)%16]-dot)))
    else:
        i = block-DIRECTED
        xr, wr = ((-127, 127), (-127, 127)) if i%4 == 1 else ((-8192, 8191), (-2048, 2047))
        x = [[rng.randint(*xr) for _ in range(64)] for _ in range(5)]
        w = [[rng.randint(*wr) for _ in range(16)] for _ in range(64)]
        if i%4 == 0:
            bias = [rng.randint(-(1 << 31), (1 << 31)-1) for _ in range(16)]
        elif i%4 == 1:
            bias = [rng.randint(-1048576, 1048576) for _ in range(16)]
        elif i%4 == 2:
            targets = BOUNDARIES if i%8 == 2 else LIMITS
            bias = []
            for c in range(16):
                dot = sum(x[0][k]*w[k][c] for k in range(64))
                bias.append(max(-(1 << 31), min((1 << 31)-1, targets[c]-dot)))
        else:
            bias = [rng.randint(-(1 << 25), (1 << 25)-1) for _ in range(16)]
    return x, w, bias


def generate(folder, blocks):
    rng = random.Random(SEED)
    expected_outputs = DIRECTED*80+blocks*80-(blocks//20)*16
    stats = dict(valid_outputs=0, saturated=0, nonsaturated=0,
                 sum_min=0, sum_max=0, total_min=0, total_max=0)
    with (folder/'tokens.mem').open('w', newline='\n') as tokens, \
            (folder/'bias.mem').open('w', newline='\n') as biases, \
            (folder/'expected.mem').open('w', newline='\n') as expected:
        for block in range(DIRECTED+blocks):
            x, w, bias = values(block, rng)
            active_rows = 4 if block >= DIRECTED and (block-DIRECTED+1)%20 == 0 else 5
            for k in range(64):
                xx = sum((x[r][k] & 0x3fff) << (r*14) for r in range(5))
                ww = sum((w[k][c] & 0xfff) << (c*12) for c in range(16))
                tokens.write('%066x\n' % ((xx << 192) | ww))
            for b in bias:
                assert -(1 << 31) <= b < (1 << 31)
                biases.write('%08x\n' % (b & 0xffffffff))
            for r in range(5):
                for c in range(16):
                    # Deliberately independent of the RTL arithmetic and codec.
                    dot = 0
                    for k in range(64):
                        product = x[r][k]*w[k][c]
                        assert -(1 << 25) <= product < (1 << 25)
                        dot += product
                        assert -(1 << 31) <= dot < (1 << 31), 'Intermediate accumulator overflow'
                    total = dot+bias[c]
                    assert -(1 << 32) <= total < (1 << 32)
                    result, sat = requantize(total)
                    packed = ((dot & 0xffffffff) << 50) | ((total & 0x1ffffffff) << 17) | ((result & 65535) << 1) | sat
                    expected.write('%021x\n' % packed)
                    if r < active_rows:
                        stats['valid_outputs'] += 1
                        stats['saturated' if sat else 'nonsaturated'] += 1
                        stats['sum_min'] = min(stats['sum_min'], dot);stats['sum_max'] = max(stats['sum_max'], dot)
                        stats['total_min'] = min(stats['total_min'], total);stats['total_max'] = max(stats['total_max'], total)
    assert stats['valid_outputs'] == expected_outputs
    (folder/'n1_array_config.vh').write_text('`define N1_DIRECTED_BLOCKS %d\n`define N1_RANDOM_BLOCKS %d\n' % (DIRECTED, blocks))
    manifest = dict(schema='n1-array-independent-python-reference-v1',seed=SEED,seed_hex=hex(SEED),
                    random_blocks=blocks,directed_blocks=DIRECTED,random_outputs=blocks*80-(blocks//20)*16,
                    stats=stats,integer_reference='unbounded Python int; each partial sum range checked',
                    format=dict(x_bits=14,w_bits=12,product_bits=26,accumulator_bits=32,bias_bits=32,
                                total_bits=33,result_bits=16,shift=10),
                    files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in folder.glob('*.mem')})
    (folder/'vectors.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vivado-bin',required=True,type=Path)
    parser.add_argument('--blocks',type=int,default=10000)
    parser.add_argument('--generate-only',action='store_true')
    args = parser.parse_args()
    if args.blocks < 1:
        parser.error('--blocks must be positive; official stress acceptance requires at least10000')
    folder = ROOT/'local_runs'/('n1_systolic_array_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    started = time.time()
    manifest = generate(folder,args.blocks)
    print('N1_ARRAY_VECTORS_READY',folder,flush=True)
    if args.generate_only:
        return
    files = [A3/'rtl/arch03_n1_systolic5x16.sv',A3/'rtl/arch03_n1_requantize.sv',
             A3/'tb/tb_arch03_n1_systolic5x16.sv']
    hashes = {str(p.relative_to(ROOT)):sha(p) for p in files+[Path(__file__).resolve()]}
    tool = lambda n:args.vivado_bin/(n+'.bat')
    try:
        run([tool('xvlog'),'--sv','-i',folder]+files,folder,'compile.log')
        run([tool('xelab'),'tb_arch03_n1_systolic5x16','-debug','typical','-s','n1_array'],folder,'elaborate.log')
        (folder/'run.tcl').write_text('run all\nquit\n')
        text = run([tool('xsim'),'n1_array','-tclbatch','run.tcl'],folder,'simulate.log')
        found = re.search(r'N1_ARRAY_PASS random_blocks=(\d+) directed_blocks=(\d+) outputs=(\d+) continuous_II=64 pauses=(\d+) cancels=(\d+) resets=(\d+) cycles=(\d+)',text)
        if not found:
            raise ValueError('Missing complete N1 array PASS')
        random_blocks,directed,outputs,pauses,cancels,resets,cycles = map(int,found.groups())
        if (random_blocks,directed,outputs)!=(args.blocks,DIRECTED,manifest['stats']['valid_outputs']):
            raise ValueError('Wrong stress test counts')
        if any(sha(ROOT/p)!=digest for p,digest in hashes.items()):
            raise ValueError('Test/RTL source changed during simulation')
        for name,spec in manifest['files'].items():
            if sha(folder/name)!=spec['sha256']:
                raise ValueError('Independent reference changed during simulation')
        report = dict(status='passed',scope='N1_standalone_array_and_requant_only',
            full_10000_random_stress_passed=args.blocks>=10000,random_blocks=args.blocks,
            directed_blocks=DIRECTED,random_outputs=manifest['random_outputs'],outputs=outputs,
            seed=SEED,seed_hex=hex(SEED),sum_total_result_saturation_checked=True,
            exactly64_MAC_per_valid_output=True,continuous_II=64,global_pause_cycles=pauses,
            partial_block_cancels=cancels,partial_block_resets=resets,tag_wrap=args.blocks+DIRECTED>512,
            cpu_executed=False,sram_tested=False,output_fifo_backpressure_tested=False,
            PPA_verified=False,host_seconds=time.time()-started,simulation_cycles=cycles,
            source_sha256=hashes,vector_manifest_sha256=sha(folder/'vectors.json'),
            tool_directory=str(args.vivado_bin),tool_version='Vivado2018.3 configured; see compile/elaboration/simulation logs')
        (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print('N1_ARRAY_LOCAL_PASS',folder,flush=True)
    except Exception as exc:
        (folder/'failure.json').write_text(json.dumps(dict(status='failed',error=str(exc),source_sha256=hashes,
            host_seconds=time.time()-started,scope='standalone_array_only'),indent=2)+'\n')
        raise


if __name__=='__main__':
    main()
