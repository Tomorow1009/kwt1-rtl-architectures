"""Complete four-transfer task accounting; never reuse the N1 three-transfer gate."""
from decimal import Decimal
import re
import soc_power


def window_values(window):
    """Validate the P80 four-transfer contract before sharing timing utilities."""
    encoded = window.get('encoded_bytes')
    require(type(encoded) is int and 32 <= encoded <= 47008 and encoded % 4 == 0,
            'Invalid P80 encoded size')
    require(window.get('boundary') == 'first_source_valid_to_final_write_response_ack_with_drain_proof'
            and window.get('transfer_bytes') == encoded * 3 + 50688
            and window.get('transfer_transactions') == 3 * (encoded // 4) + 12672,
            'P80 power requires source read, shared write, shared read and output write')
    require(Decimal(str(window['period_ns'])) == Decimal('6.666666'), 'P80 clock mismatch')
    values = soc_power.window_values(window)
    start, end, cycles = (int(window[k]) for k in ('start_cycle', 'end_cycle', 'cycles'))
    require(start >= 0 and end - start == cycles and cycles >= window['transfer_transactions']
            and int(window['finished_cycle']) >= end, 'P80 cycle/drain proof mismatch')
    finished = Decimal(str(window['finished_ns']))
    require(finished.is_finite() and finished >= Decimal(values[1]), 'P80 drain precedes final ACK')
    return values


def require(value, message):
    if not value:
        raise ValueError(message)


def read_window(text, result, encoded_bytes):
    lines = [s for s in text.splitlines() if s.startswith('ICB32_TASK_WINDOW ')]
    require(len(lines) == 1, 'Expected one P80 complete window')
    pairs = re.findall(r'(\w+)=([^ ]+)', lines[0])
    fields = dict(pairs)
    require(len(pairs) == len(fields), 'Duplicate window fields')
    require(type(encoded_bytes) is int and 32 <= encoded_bytes <= 47008 and
            encoded_bytes % 4 == 0, 'P80 encoded length')
    for key, value in dict(finished=1, failed=0, failure_code=0,
            source_bytes=encoded_bytes, input_write_bytes=encoded_bytes,
            input_read_bytes=encoded_bytes, output_bytes=50688).items():
        require(int(fields[key]) == value, 'Invalid P80 window ' + key)
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
