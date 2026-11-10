"""Immutable lossless task preparation and independent capture checks, Python 3.6."""
import json
import re
import struct
from decimal import Decimal
from pathlib import Path
import dma16_batch as legacy
import icb32_codec as codec

require, read, save, sha = legacy.require, legacy.read, legacy.save, legacy.sha
CASES14 = legacy.CASES14


def prepare_case(source, destination, force_raw=False):
    destination = Path(destination)
    layout = legacy.prepare_case(source, destination)
    raw = (destination/'load.bin').read_bytes()
    encoded = codec.encode(raw, force_raw=force_raw)
    require(codec.decode(encoded) == raw, 'Lossless encode/decode mismatch')
    binary, words = destination/'codec.bin', destination/'codec32.hex'
    binary.write_bytes(encoded)
    words.write_text(''.join('%08x\n' % v[0] for v in struct.iter_unpack('<I', encoded)), encoding='ascii')
    record = codec.describe(encoded)
    record.update(schema='arch03-icb32-case-v2', shift=layout['shift'],
        source_layout_sha256=layout['source_layout_sha256'],
        tile_layout_sha256=sha(destination/'layout_manifest.json'),
        source_sha256=sha(destination/'load.bin'), force_raw=force_raw,
        runtime_inputs=['codec32.hex'],
        files={'codec.bin':sha(binary),'codec32.hex':sha(words)},
        codec_script_sha256=sha(codec.__file__),preparation_script_sha256=sha(__file__))
    save(destination/'codec.json', record)
    return record


def verify_prepared(source, destination):
    destination = Path(destination)
    layout = legacy.verify_prepared(source, destination)
    record = read(destination/'codec.json')
    require(record['schema']=='arch03-icb32-case-v2' and
        record['tile_layout_sha256']==sha(destination/'layout_manifest.json') and
        record['source_layout_sha256']==layout['source_layout_sha256'] and
        record['source_sha256']==sha(destination/'load.bin') and record['shift']==layout['shift'] and
        record['codec_script_sha256']==sha(codec.__file__) and
        record['preparation_script_sha256']==sha(__file__), 'Codec identity changed')
    legacy.check_hashes(destination,record['files'])
    encoded=(destination/'codec.bin').read_bytes()
    require(codec.decode(encoded)==(destination/'load.bin').read_bytes(),'Codec no longer reconstructs raw task')
    require(list(struct.unpack('<%dI'%(len(encoded)//4),encoded))==
            legacy.hex_values(destination/'codec32.hex',len(encoded)//4,32),'Encoded word byte order')
    for key,value in codec.describe(encoded).items():
        require(record[key]==value,'Codec descriptor changed: '+key)
    return record


def parse_result(text, saturated, required_markers=()):
    require('MONITOR_FIXTURE' not in text, 'A procedural fixture is not real E203 evidence')
    require('ARCH03_DMA16_BATCH_RESULT ' not in text,'Legacy result in new run')
    # The proven generic result parser checks counts, final ACK, cycles and
    # actual CPU evidence. Only the explicitly versioned marker is translated.
    return legacy.parse_result(text.replace('ARCH03_ICB32_BATCH_RESULT ',
                                            'ARCH03_DMA16_BATCH_RESULT '),saturated,required_markers)


def read_window(text, result, encoded_bytes):
    lines=[s for s in text.splitlines() if s.startswith('ICB32_TASK_WINDOW ')]
    require(len(lines)==1,'Expected one full ICB32 task window')
    fields=dict(re.findall(r'(\w+)=([^ ]+)',lines[0]))
    for key,value in dict(finished=1,failed=0,failure_code=0,source_bytes=encoded_bytes,
        input_write_bytes=encoded_bytes,input_read_bytes=0,output_bytes=50688).items():
        require(int(fields[key])==value,'Invalid ICB32 window '+key)
    start,end,cycles=[int(fields[k]) for k in ('start_cycle','end_cycle','cycles')]
    require((start,end,cycles)==(result['first_request_cycle'],result['final_response_cycle'],result['cycles']),
            'Result/window mismatch')
    t0,t1=Decimal(fields['start_ns']),Decimal(fields['end_ns'])
    require(abs(t1-t0-Decimal(cycles)*Decimal('6.666666'))<=Decimal('0.000002'),'Time/cycle mismatch')
    require(int(fields['finished_cycle'])>=end and Decimal(fields['finished_ns'])>=t1,'Drain proof before final ACK')
    return dict(start_cycle=start,end_cycle=end,cycles=cycles,start_ns=str(t0),end_ns=str(t1),
        finished_cycle=int(fields['finished_cycle']),finished_ns=fields['finished_ns'],period_ns='6.666666',
        encoded_bytes=encoded_bytes,transfer_bytes=encoded_bytes*2+50688,
        transfer_transactions=encoded_bytes//2+12672,task_per_second=150000000.0/cycles,
        mmac_per_second=1622016.0*150.0/cycles,
        boundary='first_source_valid_to_final_write_response_ack_with_drain_proof')


check_capture=legacy.check_capture
