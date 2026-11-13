# N1 checkpoint — 2026-11-13 13:05

Read AGENTS.md, the active N1_N2_D1_D2 plan, this checkpoint and STATUS.narrow_execution after compaction. Continue N1 precision/power acceptance, then N2 automatically. No N2 RTL has been implemented. Production remains 9305c6948c764fed01fe86b20bb3db94170299ab; runtime tools 0f62e41207909904efd544992013c1244b0fd63b. Cloud 49c1b9ab020259a1aae33f385b4939668fdcdee0 was verified at 12:50.

## Completed since 12:47

- All 76 obsolete Nov10 build files (172,474,566 bytes) were copied and individually hash/size checked in OPS02/retained_old_build_1242. Manifest SHA ad4d31168e30a0e0c40b13a8ad153b4743428536a17e2c9f53b4f3e5e8bf72a8. Only their exact original duplicates were removed after path/owner/stamp/hash/fuser/terminal-stage checks. Receipt removed_original_duplicates.json SHA f97d197d0bc867c58277b37e0b4d3836559d98a3b7e4acbaa58684aaa486a5d2. Completed at observed 12:50:26; free snapshot 1,992,294,400 bytes. Do not repeat cleanup. Historical reports, source, inputs and B0/R4/N1 evidence remain intact. Not all free-space change came from this cleanup.
- The existing SAIF diagnostic driver 187134 acquired the original lock at 12:47:43.738454 and resumed without duplicate launch. Actual 13:04:23: ten B0 cases complete, B0 L11 running, no failure reported. Largest absolute relative change among those ten is 1.06457748303649e-6. This compares two PT SAIF static-probability settings, not a physical unknown-state bound. Original activity/netlist/constraints/results unchanged.
- Both linked unknown queries finished: B0 41,441 targets/39,133 resolved/2,308 unresolved; N1 40,580/38,142/2,438. Cached endpoint query at 12:58:45 found zero unknown receiving endpoints in the explicit CK/CKN/CLK/CP/CPN/RDN/SDN, CLKLAN ICG, and SRAM CEN/GWEN/RET1N/WEN pin set. Unique endpoints 62,814 B0 and 64,816 N1. This is a specified pin-set check, not blanket proof of all unknown impact. Unresolved aliases and data influence still require review.
- Final N1 report is already exported and ASIC/FLOAT1200 join passed. Report SHA 8f778dd1f201855ae6b0fad815e3e3b0e258a64a694fab4cc538569ee522c2e1. Own 1200/30,412,800 outputs and totals, ASIC14/recovery/contention, gate14, SAIF12, fresh full FLOAT precision and power12 numbers are complete. No reruns required.

## Remaining

Complete existing 24-case diagnostic, cached unknown-alias/control review, independent declared-mode timing/area/power admission, stage report and durable archive. N1 preliminary weighted power 61.7773489406 mW, 12.2364442055 µJ/task; power acceptance still pending. Precision max aggregated layer NRMSE 0.1933721614699203%; internal, not official600. Area conservative 0.9511486879005002 mm². N1 mean 29,711 cycles/5048.6351856 task/s at 150MHz.

All12 actual no_clock sets contain 189 pins solely in static task-mode JTAG debug logic; actual clock periods and disabled-arc scopes were checked. Review scope remains pre-layout declared task mode, not physical signoff.

## Resume identities

ROOT=/tmp/s4_21usr_n1_20261113_0210. OPS02=ROOT/light-light126-n1-precisionops02-20261113_090845. Runtime0f62=ROOT/light-light126-n1-v4-20261113_045945-0f62e4120790.

Active driver187134: OPS02/saif_static_control_1225; runtime0f62/runs/n1_saif_static_01. Do not restart. B0 and N1 linked proofs: runtime0f62/runs/n1_unknown_b0_01/n1_unknown_b0 and n1_unknown_n1_01/n1_unknown_n1. Final report OPS02/final_report01/report.json. Full N1 unknown inventory OPS02/n1_unknown_review01.

VNC18874435 workspace3, FileZilla closed, workspace4 untouched. Fresh window inventory and screenshot checked 13:03. Terminal idle after read-only diagnostic query. Local query E:/fpga_race-two/takeover_local/n1_sp_compact_00.txt is a complete 590-character command; no _01 chunk exists (attempting to read it failed locally, no remote effect). All tool sessions reaped. Durable archive not started; preserve /tmp runtime outputs.

User ETA update: N1 about40–60 minutes from13:05 if remaining review stable; N2 additional10–15 hours including full verification, fixes extra. Continue work without step confirmation; do not stop after status answers.
