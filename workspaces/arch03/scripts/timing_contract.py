"""Strict 150 MHz constraint, compatible with the server's Python 3.6."""
from decimal import Decimal, InvalidOperation

# Round DOWN: 6.667 ns and even rounding 20/3 upward are not 150 MHz evidence.
CLOCK_PERIOD_NS = '6.666666666'


def validate_period(value):
    try:
        period = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid clock period')
    if not period.is_finite() or period <= 0 or period > Decimal(20)/Decimal(3):
        raise ValueError('Clock period does not meet strict 150 MHz')
    return float(period)
