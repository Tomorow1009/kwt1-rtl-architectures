"""Validate an exited, zero-work ENOSPC retry before a fresh C80 queue."""
from pathlib import Path


def validate(followup, precision, export, alive, lock_path):
    error = "[Errno 28] No space left on device: '"+str(lock_path)+"'"
    def need(ok, message):
        if not ok:
            raise ValueError(message)
    need(followup.get('pid') == 314678 and followup.get('status') == 'failed' and
         followup.get('error') == error and followup.get('finished') and
         followup.get('source_sha256') ==
         '62c6114e559b0dac3686e3c9e7d039e200a052735b6fd43e8afa9f787e79181b',
         'Not the exact original C80 followup ENOSPC failure')
    need(precision.get('pid') == 314678 and precision.get('status') == 'failed' and
         precision.get('error') == error and precision.get('finished') and
         precision.get('schema') == 'c80-precision-only-recovery-v1' and
         precision.get('completed') == [] and not precision.get('stage') and
         not precision.get('current_run'), 'Precision already dispatched or failed differently')
    need(export.get('pid') == 4047 and export.get('status') == 'failed_preserved' and
         export.get('finished') and export.get('source_sha256') ==
         '01547cb992b2f8ca716a132baa09c2ac1f1eab52eeb4afb88a468f8e65491656',
         'Original export has not terminated with preserved failure')
    need(not any(alive(pid) for pid in (279630,314678,4047)),
         'An original owner is still present; no new dispatch')
    return dict(original_failed_attempts_preserved=True, precision_children_dispatched=0,
                hardware_rerun=False, lock_override=False)
