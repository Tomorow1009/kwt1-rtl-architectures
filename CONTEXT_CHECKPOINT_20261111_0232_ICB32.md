# 2026-11-11 02:32 ICB32 持续执行检查点

用户要求持续推进，压缩前保存、压缩后重读。本轮已重读AGENTS、有效计划、01:41检查点全部增量、根交接和两个JSON的icb32_c64_execution，没有重开旧任务。

## 当前目标及已完成

- 有效计划：`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`。原32位ICB、压缩输入真实落库、成功ACK后解码、16×4 MAC；Q12/完整冷启动计时/原16位输出不变。11/11 18:00冻结、11/12 17:16准备交付、11/13晚上截止。
- e65 R4真实ASIC/E20314例354816输出、IRQ/WFI全部通过，12层平均34616周期/150MHz折算4333.2562977 task/s。证据`handoff/team/evidence/ICB32_ASIC14_20261111.json`。新150MHz/面积/功耗仍未通过。
- 原ecf队列01:35自然完成，旧8门级14/12活动及MAC L02–L12有效样本扫描通过；旧8完整功耗仍缺。证据`OLD_QUEUE_RECOVERED_20261111.json`。
- R1本地14例与R4全部354816输出逐坐标一致，平均116280周期，局部加速3.359140×；R1尚无服务器ASIC/PPA。
- 本轮没有改RTL/固件或增加测试。核对现有synth/gate/diagnostic/batch入口；独立polling诊断不混作IRQ性能/功耗。

## 唯一运行任务，禁止重复

共同父目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

e65包`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`的`runs/icb32_r4_first01_queue`为唯一队列PID75421；综合位于`runs/icb32_r4_first01/icb32_synth`，最后已核owner125556/child128047。

**最新实际02:31:33.454047：running icb32_synth，error=None，METRICS_NOT_READY。** 02:19进入Mapping Optimization，02:25/02:28/02:31日志继续推进。中间时序违例仍在优化，不能判作最终失败或通过；最终需核224宏、面积和时序。不可清锁、重启或并发新EDA。

## 桌面和同步

- 已重新inventory确认VNC window20971587，第三终端仍在**f95 R1包根**。最后终端命令是相邻e65的只读综合查询，可Up Return重复；执行其他命令后不可盲目Up。
- 查询文本`E:/fpga_race-two/takeover_local/icb32_server_status.txt`；使用板端`F:/linux_fpga_try/ac820.ps1 type --window 20971587 --expect-class Vncviewer --text-file ...`，Return后截图`icb32_live_status.png`。服务器只通过可见VNC，不SSH/隐藏上传。
- FileZilla关闭、原代理保持，无本地仿真/构建。最后已核云端`dbe913320a23b73366929d54be5578a7258d2420`；本检查点及02:14增量待提交。
- 三包身份和完整SHA详见01:41检查点：e65受测ASIC/synth；497诊断/报告（630输入/三固件已服务器预检）；f95 R1（607输入预检，未执行）。不要混用。
- 本地KWT1_HEX_handoff/vectors清单为5bb8…，不是固定100样本清单，未用作验收、未改数据。最终仍用服务器`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest 0eaa4abf…（01:46已重核）。
- 历史Tcl环境/NumPy环境、8192超时失败/4096修复见01:12及01:41检查点。不要重跑旧adapt生成器覆盖正确4096版本。

## 未完成及立即下一步

1. 等当前综合结束，读实际summary SHA、metrics、check_timing/constraints/关键路径和area_inventory。报告就绪不等于严格STA批准；失败保留原目录，按实际问题修复后用新包/session。
2. 当前队列结束且锁正常释放后切497包`light-light126-icb32-r4-20261111_011258-49759e108719`，顺序执行：
   - `python3 workspaces/arch03/scripts/server_run.py icb32_contention --session icb32_r4_contention01 --cases layer_01 extremes`
   - `python3 workspaces/arch03/scripts/server_run.py icb32_sequence --session icb32_r4_sequence01 --cases layer_01 rounding`
   这两个session至02:32尚未启动。497生产IRQ固件与e65相同，诊断固件独立。
3. 同网表gate14/12完整活动、严格STA范围审核、12功耗、最终1200真实ASIC/E203/30412800输出、干净复现及交付报告均未完成。按batch_progress实际端到端耗时加20%余量，不把2.2–2.8秒仿真子进程时间当完整墙钟。
4. R1 ASIC/PPA和旧8完整功耗在主候选硬性验收后串行安排。旧fcd 664.393 task/s/1200通过退路保留；旧29.6273mW不能套给新RTL，系统功耗审核仍未完成。
5. 继续执行，无需用户再催。用户暂停时保存并关闭板端两个客户端，远端队列保持。
