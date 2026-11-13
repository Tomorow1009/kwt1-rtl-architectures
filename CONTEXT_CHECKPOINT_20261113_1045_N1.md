# N1 checkpoint 2026-11-13 10:45

Active plan: workspaces/arch03/IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md. Production9305 unchanged. N2 not started.

N1 precision100 passed:1200 tasks/30412800 outputs, zero integer/HEX differences or clipping/saturation; max aggregate layer NRMSE0.1933721614699203%. ASIC1200, gate14 and SAIF12 completed; final independent join and power influence review pending.

Original queue237710 FAILED at power03 due to ENOSPC creating original shared lock. Finished10:35:46.296408; /proc absent at10:45. Failed state SHA4fe0eaf9d00d31293e99d3ee1f27ac945b1bedb014e0023aeb834d09d1ce2f2d. Shared lock absent. Precision/power01/power02 passed, p03 has no directory. Do not rerun old queue or passed stages.

Actual p01 mean0.0615478829W/0.0000125340199395732140358J; p02 mean0.0617446564W/0.0000123254670780211689432J. Both averaged, Xderate0.5, initialXfalse. Not twelve-layer results or accepted system power.

Two exact duplicate upload ZIPs9305/0f62 copied/hash verified and fuser checked, then original shared ZIPs removed10:43:28.754255.17823954 bytes saved; free18874368B. Retained local and private copies under precisionOPS02/retained_input_zip_1040. copied.json SHA00f6056a64d5f0924e933ad968c38ca67a7bde2d835c43b360e4e67eae58d22d; removed.json SHAb9ab643387c47c87f4359f3fb68f55bc94ae0135f7d98a6442fb7e51c6740e92. No unique result removed. See screenshots n1_zip2_removed_1044.png and n1_resume_1047.png.

NEXT: fresh recovery control under precisionOPS02, run only n1_acceptance02_p03 throughp12 using original lock/runtime/netlist/activity. Not yet launched. Preserve original failed state. Existing final_request/export tools assume original queue finished13, now invalid; prepare recovery-aware final join. Final report/N1unknown review/acceptance incomplete. Original identities in1030/1000/0900 checkpoints.

VNC18874436/workspace3 idle, FZclosed. No unfinished command. Cloud b9fc9d6 verified, current documentation not yet pushed.

## 11:09 recovery increment

Twenty old DMA16 upload ZIPs330959830B were retained/hash-matched to local originals and private copies, then shared duplicates removed10:57:07.702076. Shared free331350016B at that moment. All runs/waves/results retained. Evidence N1_POWER_RECOVERY_STORAGE_20261113.json.

Recovery01 preflight failed on raw-versus-formatted JSON digest; semantic equality confirmed. Recovery02 preflight failed on 63-character transcription of failed state hash. Correct hash (groups of8):4fe0eaf9 d00d3129 3e99d3ee 1f27ac94 5b1bedb0 14e0023a eb834d09 d1ce2f2d. Both retained and no children launched.

Recovery03 tool in OPS02/recovery_tools_1103 passes original identity checks. Its new power_recovery01 control created, but n1_acceptance02_p03 failed again before creating shared lock: ENOSPC. Do not restart this control. Shared free20MB at11:05 and89MB shortly after, inode free185817 (97%used), so not inode exhaustion. Shared NFS fluctuates quickly. Actual power03 never ran; passed prefix still precision/p01/p02 only.

Root is now read-only listing actual large old VCD/gzip/archive files under project, excluding dangling links. That walk is still running in VNC foreground at11:08; do not type new shell commands until prompt returns. N2 not started. Need recover sufficient shared space then fresh power continuation preserving both failed queue records. Existing final report helper remains incompatible with split completion; adjust after storage restored.
