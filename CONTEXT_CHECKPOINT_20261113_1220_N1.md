# N1 checkpoint 2026-11-13 12:20

Continue N1 precision/power acceptance, then N2 automatically. Read active N1_N2_D1_D2 plan, AGENTS, STATUS.narrow_execution, and1155/1145 checkpoints. No N2 RTL yet.

## Completed since1155

All12 powers complete. Final report exported, ownASIC1200 total33/result/sat cross-joined to fresh FLOAT100/HEX successfully. Fixed12 fresh precision also verified. Report OPS02/final_report01/report.json SHA8f778dd1f201855ae6b0fad815e3e3b0e258a64a694fab4cc538569ee522c2e1. At12:17:32 raw mean29711 cycles/5048.6351856 task/s; weightedP0.0617773489406039289609334365 W, energy0.0000122364442055173459727 J/task. Not yet system-power acceptance. Original B0 .06983707336109641885320248724 W and .0000142012898511016506547 J retained. Report flags precision/fixed12/final1200/ASIC14/gate14/activity12/power12 true; scope review flags false deliberately.

Read-only power12 post audit OPS02/power12_post_audit.json SHA25431a40ada4589e21c745d349eafbf5a6dc443be66690d8010512a554bbd471. Actual clocks6.666666ns/66ns; disabled flags each C72460,c12145,d201,p60113, no l/L/u/U. SRAM leakage consistent92small/128large. First compact audit failed nonexistent condensed field before writing anything; v2 derives histograms from original cell numbers. Local evidence N1_POWER12_POST_AUDIT_20261113.json and stage handoff updated.

## Current jobs

Original exporter118695 still collecting12-layer N1 unknown inventory at12:15, seen layer03 open. Observer116442 remains its parent. Control final_export_control02. Do not duplicate. Recovery84627 complete; do not rerun powers/precision/SAIF1200.

B0 linked unknown query completed12:00:50.880477; driver131347/child131427 ended, original sharedlock released. Session0f62/runs/n1_unknown_b0_01, stage n1_unknown_b0. Query11722B SHAa1b11e3e9366d2f5539d8f0f114a7630d7e723afc220e947b2b3a62b39b669d7 deployed OPS02/linked_unknown_tools_f5a8751. Launch control OPS02/linked_b0_control_1159. 41441targets,39133resolved/leafconnected,2308unresolved,1159resolved without receiving leaf,37974with receiving leaf. No blanket no-load exemption. Unique leaf endpoints62814; include SRAMQ, flops and logic. Unresolved examplesdebugdcsr_r bits. This is collection PASS only, not power PASS. New N1 linked query not yet launched.

## Newly prepared, not yet deployed/run

saif_static_probability_review.py plus2 tests passed; Python3.6 syntax passed. Reads pinned original B0/N1 reports and original power scripts. Runs fresh diagnostics changing only power_enable_saif_all_state_static_probability from verified initialfalse totrue before read_saif, keeps original netlist/activity/clocks/loads. Uses original sharedlock/privateledger, output24stages, compares original numbers; never overwrites original reports or claims physical bound. Needs review/freeze/deploy/request/launch.

Installed manual confirms actual option and formula: doc/pt/man/cat3/power_enable_saif_all_state_static_probability.3 in /eda/synopsys/prime/prime_2022.03-SP5-1. Default uses only known0/1 residence; true incorporates unknown/Z/B residence withprobability.5. Thus useful targeted same-activity sensitivity unlike blindly applying oldVCD X-transition settings. Manualviews n1_pt_saif_static.png and n1_pt_man_x.png. No manual/library copied intoGit.

Need finalunknown impact analysis and independent scope review. Existing B0 control12/globalconnection evidence remains. Do not treat sensitivity as strictphysicalbound; declaredprelayoutmodelonly. Preserve B0/R4 backup and all failed paths. No new cleanup thisturn.

## Sync/access

Latest verifiedcloudf5a87513ece379ca87d3b72a6bb9286ff848b866. It includes observer and linkedquery/tests,1155checkpoint. Current edits add powerpost audit, stagehandoff and new sensitivitytool. VNC18874435/workspace3idle, FZclosed; workspace4untouched. No outstanding typing before next action. OPS02=/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-precisionops02-20261113_090845; 0f62=/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-v4-20261113_045945-0f62e4120790.
