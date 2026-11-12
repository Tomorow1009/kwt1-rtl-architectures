"""ASCII SAIF lexical details observed in installed VCS region output."""
from decimal import Decimal
import re


def without_comments(lines):
    block=False;quoted=False;escaped=False
    for line in lines:
        out=[];i=0
        while i<len(line):
            ch=line[i]
            if block:
                if line[i:i+2]=='*/':block=False;out.append(' ');i+=2
                else:
                    if ch=='\n':out.append(ch)
                    i+=1
            elif quoted:
                out.append(ch);i+=1
                if escaped:escaped=False
                elif ch=='\\':escaped=True
                elif ch=='"':quoted=False
            elif line[i:i+2]=='/*':block=True;out.append(' ');i+=2
            else:
                out.append(ch);i+=1
                if ch=='"':quoted=True
        yield ''.join(out)
    if block:raise ValueError('Unterminated SAIF comment')
    if quoted:raise ValueError('Unterminated SAIF quote')


def integer_ticks(value,positive=False):
    # VCS emits integral duration as e.g. 60000000.00. Never round a
    # fractional tick or permit NaN/Infinity/scientific ambiguity in counts.
    if not re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.0+)?',value):
        raise ValueError('Nonintegral or invalid SAIF tick count')
    result=int(Decimal(value))
    if positive and result<=0:raise ValueError('Nonpositive SAIF duration')
    return result
