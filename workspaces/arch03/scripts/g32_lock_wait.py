"""Wait for the original shared lock; never clear or replace any lock."""
import time


def acquire_wait(ledger,acquire=None,sleep=time.sleep):
    acquire=ledger.acquire if acquire is None else acquire
    reason=None
    while True:
        if ledger.lock.exists():
            if reason!='busy':print('G32_WAIT_ORIGINAL_TEAM_LOCK',flush=True)
            reason='busy';sleep(5);continue
        try:return acquire()
        except OSError as error:
            # A partially written owner must be preserved for explicit review.
            if error.errno!=28 or ledger.lock.exists():raise
            if reason!='storage':print('G32_WAIT_ORIGINAL_LOCK_STORAGE',flush=True)
            reason='storage';sleep(5)
