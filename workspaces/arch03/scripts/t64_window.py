"""Complete four-transfer task accounting; never reuse the N1 three-transfer gate."""
from decimal import Decimal
import re


def require(value, message):
    if not value:
        raise ValueError(message)


def read_window(text, result, encoded_bytes):
    lines = [s for s in text.splitlines() if s.startswith('ICB32_TASK_WINDOW ')]
    require(len(lines) == 1, 'Expected one T64 complete window')
    pairs = re.findall(r'(\w+)=([^ ]+)', lines[0])
    fields = dict(pairs)
    require(len(pairs) == len(fields), 'Duplicate window fields')
    require(type(encoded_bytes) is int and 32 <= encoded_bytes <= 47008 and
            encoded_bytes % 4 == 0, 'T64 encoded length')
    for key, value in dict(finished=1, failed=0, failure_code=0,
            source_bytes=encoded_bytes, input_write_bytes=encoded_bytes,
            input_read_bytes=encoded_bytes, output_bytes=50688).items():
        require(int(fields[key]) == value, 'Invalid T64 window ' + key)
    start, end, cycles = [int(fields[k]) for k in ('start_cycle', 'end_cycle', 'cycles')]
    require(start >= 0 and end > start and end-start == cycles, 'Invalid window cycle range')
    require((start, end, cycles) == (result['first_request_cycle'],
            result['final_response_cycle'], result['cycles']), 'Result/window mismatch')
    t0, t1, tf = [Decimal(fields[k]) for k in ('start_ns', 'end_ns', 'finished_ns')]
    require(all(t.is_finite() for t in (t0, t1, tf)), 'Non-finite window time')
    require(abs(t1-t0-Decimal(cycles)*Decimal('6.666666')) <= Decimal('.000002'),
            'Time/cycle mismatch')
    require(int(fields['finished_cycle']) >= end and tf >= t1, 'Drain proof precedes final ACK')
    return dict(start_cycle=start, end_cycle=end, cycles=cycles, start_ns=str(t0), end_ns=str(t1),
        finished_cycle=int(fields['finished_cycle']), finished_ns=str(tf), period_ns='6.666666',
        encoded_bytes=encoded_bytes, transfer_bytes=encoded_bytes*3+50688,
        transfer_transactions=3*(encoded_bytes//4)+12672, task_per_second=150000000.0/cycles,
        mmac_per_second=1622016.0*150.0/cycles,
        boundary='first_source_valid_to_final_write_response_ack_with_drain_proof')
