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

## 11:35增量：稳定任务模式时序/面积审阅完成，批量291通过

- 11:31:04.607624实际：原285397/292229继续final1200，291/1200、7375104输出、零失败，completed stages13/errorNone，宿主1337.0145秒；含20%余量预计剩余5011.7367秒（约84分钟）。未手工重启，report request和最终导出仍未执行。
- 706条LINT-2已沿当前2014模块真实层级逐条解析driver pin，集合与706个此前已证实只有声明的LINT-8输入完全相等，多余/缺失0。独立保存964/runs/icb32_lint2_01.json，SHA **8a67d41bf37ecff3e16986c8f6e134782f7d7eb3617358c907974d891b576371**。11:28:24.051386再核集合和原mapped.v/check_design_mapped.rpt SHA全部通过，无新EDA。
- 依据新网表完整check_timing、实际SDC/189静态JTAG对象/全部禁用弧、结构告警及同网表14例功能，已在`handoff/team/evidence/ICB32_SCOPED_REVIEW_20261111.json`接受**声明的稳定任务模式综合时序和项目面积保守上界**。新增`task_mode_timing_verified=true`及`project_area_upper_bound_verified=true`；原始阶段摘要/宽泛strict字段不改。系统功耗未知活动仍false，官方面积归属/精度及物理签核不批准。该独立审阅需在最终交付索引中与原报告一同提供，不改原历史数据。
- 11:32:16.247669十二层分量汇总：internal51.2389631887mW、switch13.3048352474mW、leak7.2688340783mW；模块总量按原层级舍入为accel47.7916409079、CPU无TCM1.87、ITCM/DTCM各1.49、shared9.4258332611、arb0.0255499456、router0.0498167153、other9.6697910239mW。已补功耗说明。只读原小JSON，不重扫VCD、不新跑功耗。
- 当前云端已独立核对 **fd91f9e77b82bd77182f2924810029829e0f5253**（含12层功耗/metrics14及11:20检查点），本增量和独立审阅待同步。验收/运行手册/交付索引/设计/创新/时序说明已消除当前顶部的过期待办；历史段落仍保留。
- 一次LINT2查询首次超过板端1000字符限制，在输入前被helper拒绝，没有远端命令执行；缩到935后成功，再964字符保存回执、713字符核验。后续每条先检查长度≤1000，type成功后才Return。最后VNC为 **power12_modules** 汇总，不是实时进度；FileZilla仍关闭，无本地长任务。下一步明确输入finish_live，继续原批量→reviewed request/history→locked export，所有后继包都已服务器就绪，无需上传。

## 11:40增量：只读进度显示正在终端中运行

- 11:39:25实际原批量400/1200、10137600输出、零失败，含20%余量预计余73.0分钟。没有重启原队列。
- VNC第三终端现在运行一个**轻量只读monitor**（不是shell提示符）：每30秒读取原state/batch_progress并显示时间、状态、通过数、失败数、输出数、余量ETA、error；原队列离开running时自行退出，最长360次。命令来源`takeover_local/icb32_batch_readonly_monitor.txt`，608字符，已于11:36:25实际启动。**不要向正在运行的monitor直接type shell命令**；正常等其自动退出即可。需要其他查询时可只停止这个前台monitor（不能中断原队列）再用明确文本。当前只需截图读取进度。
- 第一次monitor命令使用嵌套引号，被远端shell以`Unmatched '`拒绝，未启动Python或改变任何作业；已改成无嵌套引号的单行lambda，正常运行。此失败仅查询工具，不是回归失败。
- 云端 **961a658547fad191cb42c7ff36618b94aae9b292** 已独立核对，包含11:35时序/面积审阅。首次push遇TLS EOF，保持TLS校验重试成功，无待同步阻塞。本增量暂为本地记录。FileZilla关闭，无CUA或本地长任务。后继仍为原队列终态后prepare/history/locked_launch；三个命令尚未执行。

## 11:57增量：最终1200已过半，继续原队列

- **11:56:26实际：610/1200任务、15459840输出、0失败，原queue running/errorNone，monitor显示含20%余量ETA55.7分钟。** 当前只读monitor仍在前台，每30秒更新；正常等待其终态退出，不能直接往它输入shell命令。VNC字体已通过Ctrl+Shift+plus放大一次，窗口仍800×450/20971587，只有显示改变。
- 已核当前五份核心报告44个本地链接和独立审阅7份证据引用全部存在。创新说明已补fcd与R4完整窗口对照：6.522倍总体加速、面积上界2.131倍、平均功耗2.424倍、能耗降62.84%，两版功耗均保留布局前/未知影响限制；不归因给单个改动，不冒充R1完整PPA。
- 全十二层功耗、metrics14、同网表gate14/activity12、真实CPU诊断、精确SDC和声明任务模式时序/项目面积审阅均已完成。**仍缺当前批量余590任务、锁内最终报告、最终交付收尾；系统功耗未知影响不自动批准。** 所有报告操作包已在服务器，禁止重传/重启旧作业/使用无锁report入口。
- 云端最后独立确认仍961a658547fad191cb42c7ff36618b94aae9b292，本11:40/11:57增量和创新对照准备同步。当前没有本地长任务和CUA会话，FileZilla关闭。下一步只需截图原monitor；终态后按本检查点“已准备的后继操作”顺序执行prepare/history/locked_launch，三个入口均未执行。

## 12:05增量：723任务通过，继续最终批量

- 12:04:57实际monitor显示running、723/1200、18323712输出、0失败、errorNone，含20%余量ETA44.4分钟。只读monitor仍前台运行，字体已放大；只截图观察，不往monitor输入新命令，正常等原队列结束后自动返回shell。
- 云端 **87f517b0f2ee1090941737eec8a87b764c8cb1d8** 已独立确认，包含11:40/11:57检查点和完整窗口创新对照。本增量随后再同步。
- 无新RTL或EDA、无新增失败；既有源/网表/固件不变。仍等全部1200/30412800及锁内报告；readied prepare/history/locked_launch三入口均未执行，所有工具已在服务器，无需FileZilla重传。后续工程审阅与原始报告分开绑定，不篡改原stage false字段。

## 12:12增量：807任务通过

- **12:11:27实际：807/1200、20452608输出、0失败、queue running/errorNone，含余量ETA36.6分钟。** 原30秒只读monitor仍在前台，没有重新启动原队列或新EDA。最终报告还未运行，三个prepared命令均未执行。
- 上次云端已独立确认87f517b0f2ee1090941737eec8a87b764c8cb1d8；本次把12:05及12:12进度一起提交同步。工作只推进既定最终批量和交付，不再扩架构。恢复时先读有效计划和本检查点全部增量，VNC当前只能截图监视，等其终态自动退出再读锁/原request并执行后继。
