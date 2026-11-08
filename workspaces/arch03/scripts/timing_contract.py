"""Strict 150 MHz constraint, compatible with the server's Python 3.6."""
from decimal import Decimal, InvalidOperation

# DC T-2022.03 stored requested 6.666666666 as 6.666667000000 in the actual
# period attribute. Request a slightly shorter representable value and retain
# the strict measured-period check; do not relax it to tolerate rounding up.
CLOCK_PERIOD_NS = '6.666666'
# Simulation uses an explicit 1 fs precision; round down to a representable
# half-period. Report the measured waveform period, never substitute 6.667 ns.
TB_HALF_PERIOD_NS = '3.333333'
TB_PERIOD_NS = '6.666666'


def validate_period(value):
    try:
        period = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid clock period')
    if not period.is_finite() or period <= 0 or period > Decimal(20)/Decimal(3):
        raise ValueError('Clock period does not meet strict 150 MHz')
    return float(period)
