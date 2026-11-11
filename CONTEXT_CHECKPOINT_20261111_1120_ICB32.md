# 2026-11-11 11:20：十二层功耗、真实计数复现完成，最终1200运行中

压缩后先读AGENTS、当前有效`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点、STATUS及EXECUTION_CHECKPOINT的`icb32_c64_execution`。用户要求持续推进，不逐步等确认。硬件不再新增结构，18:00冻结、11/12 17:16交付准备、用户11/13晚上截止不变。

## 实际完成及限制

- 原唯一队列285397完成12层功耗与964干净目录真实ASIC/E20314例，11:16:49.095754正在`icb32_r4_finish01_final1200`，driver292229，completed stages13，error=None。批量105/1200任务、2661120输出、零失败，实际宿主482.2015秒，含20%余量预计剩余6034.4075秒；只是当时估计，不保证完工时间。原队列会写最终request，禁止重复批量。
- 十二层加权整机平均71.8126318538mW，平均16.5724387711µJ/task；完整周期均值34616、150MHz折算4333.2562977task/s，未达5000。相对原fcd平均44.5930996895µJ，估算能耗降低62.8363%；平均功耗约2.42386倍。全部为布局前估算，`system_power_verified=false`。
- 全12层活动362618网exact、未标注0、清单空，averaged/X转换系数0.5/initial-X=false。原库、224宏泄漏、端口和任务模式约束已读；未知活动影响尚未完整批准。详细范围见功耗/时序说明，不自动把映射通过当功耗验收。
- metrics14：964/runs/icb32_r4_finish01_metrics14/icb32_soc，14例354816输出，真实IRQ/WFI通过，ASICtrue/FPGAfalse。摘要SHA `bb0ee4cf23b31730d72c196bfc5101f3d2f49e7d1dea33b49e366a72de54e576`，11:11:48.348269独立匹配队列与阶段记录通过。每例MAC更新1622016、X读101376/写6336、W读409600/写16384；首层利用率73.166%、事务/总周期90.609%，三段接受至响应平均1周期不等于发起间隔。证据`ICB32_METRICS14_20261111.json`。
- e65 ASIC14/综合、497真实竞争恢复及同网表14功能门级/12活动已通过，不重跑，无SDF。面积保守上界0.9265616712mm²，DC精确周期6.666666ns，setup+0.0000715256ns/hold+0.000253469ns；完整时序审核标记仍false。原fcd的1200和功耗保留，不继承为新候选通过。
- 新正式报告、最终批量、提交材料收尾仍未完成。R1真实ASIC/PPA和原8完整功耗次优先，不并发重EDA。官方600样本和物理签核未验证。

## 已准备的后继操作

当前VNC cwd：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261111_043048-96443c284a1c`（简称964）。原state为`runs/icb32_r4_finish01_queue/state.json`，批量progress为`runs/icb32_r4_finish01_final1200/icb32_batch/batch_progress.json`。

所有报告工具已上传并服务器核验，**不要再上传**：cedb报告包8文件/8检查通过；ff181锁包装器4文件/2检查通过。精确交付SDC已导出一次，SHA9f49557c4aee558232cdb90f65c50ef6264250eb1f9c61e95747394e0348195d，receipt7777a8850e91d5283cfd3093bd59173fce3285de01f4a583d0ff16d449850dbb。原PT导入6.66667ns历史不改，不宣称重新PT。

原队列终态`reports_ready_review_required`后，核原批量与锁状态，再依序执行本机`E:/fpga_race-two/takeover_local`：

1. `icb32_final_request_prepare.txt`：核原request SHA，排他建立reviewed request，绑定SDC。
2. `icb32_final_request_history.txt`：原37组用户停止、8192诊断前提错误后4096修复的历史。
3. **`icb32_final_report_locked_launch.txt`**：ff181独立wrapper取得共享锁，session `icb32_r4_export01`，输出`runs/icb32_r4_final_report01`，外层`runs/icb32_r4_export01_launch.log`。禁止旧无锁`icb32_final_report_launch.txt`。

三条均尚未执行，遇存在目录先检查，不能原地重试或清别人锁。包完整身份与失败路径见[10:30检查点](CONTEXT_CHECKPOINT_20261111_1030_ICB32.md)及其指向09:56记录。

## 本地记录与恢复注意

- 当前云端已独立核对42216334f43deca045884d25cf764110399592b2；本检查点和11:20证据正在准备同步。`progress_1120.py`已成功执行一次，不重复追加L12。
- 本轮独立Decimal重算发现此前本地截图转录两处功耗数字和一个能量末位有误；11:19直接读取服务器L02/L04/L06精确值并验证E=Pt后已更正本地证据：L04为72.0976442mW，L06为71.4346394mW；原服务器文件从未修改。重算完整均值与服务器一致。首次记录脚本在写入前被断言阻止，无半写入；修正转录后一次执行通过。
- STATUS/EXECUTION、验收表、设计及功耗说明已更新，两个新增证据为METRICS14及FINAL1200_PROGRESS。不涉及RTL更改或重测。
- 板端helper `F:/linux_fpga_try/ac820.ps1`，恢复先windows。11:16确认VNC20971587、800×450；FileZilla关闭。最后VNC命令是**power246_exact**精确核对，不是实时进度。查询统一type已核文本再Return，禁止Up+Return历史重执行。
- 下一步明确type `icb32_finish_live.txt`检查原批量，完善报告材料；不要误启动旧队列。无本地长任务、无CUA会话。所有服务器操作仍走板端VNC，文件上传仍仅FileZilla，私有Git同范围同步已授权。
