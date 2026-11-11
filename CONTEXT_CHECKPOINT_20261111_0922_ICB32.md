# 2026-11-11 09:22持续执行：功耗4层完成，最终报告工具已就绪

用户持续推进指令有效，不因常规步骤停等。压缩后必须重读AGENTS、有效`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本文件、STATUS/EXECUTION_CHECKPOINT的icb32_c64_execution，核对已完成与未完成；更完整细节见[08:58检查点及09:10/09:14增量](CONTEXT_CHECKPOINT_20261111_0858_ICB32.md)和[08:35原队列入口](CONTEXT_CHECKPOINT_20261111_0835_ICB32.md)。

## 当前真实队列

**09:20:56.680507观测：原唯一后继285397 running，completed=4，error=None，当前`icb32_r4_finish01_power_l05`，driver175706。** 前4层整机功耗分别72.1431449、72.0979050、72.0774755、72.0976420mW；能耗分别16.6597743086、16.6339463255、16.6273109021、16.6281183445µJ。这不是12层平均，system_power_verified=false。

原队列顺序未改：12层功耗→`icb32_r4_finish01_metrics14`（真实ASIC14被动计数/干净复现）→`icb32_r4_finish01_final1200`→生成report_request。状态在964包`runs/icb32_r4_finish01_queue/state.json`，每层`layer_XX_numbers.json`。禁止另行重复启动、清锁、改运行包或同时运行大报告/VCD扫描。

## 已完成且不要重做

- e65真实ASIC14/354816输出及IRQ/WFI、497真实CPU竞争/恢复、同网表门级14/354816输出和12活动全部通过。门级03:08开始、08:29:52自然完成，无SDF；不要再查旧driver209764当实时作业。
- 12层平均34616周期，150MHz折算4333.256task/s，5000目标未达。SS/.99V/125°C，DC实际周期6.666666000000ns，setup+0.0000715256ns、hold+0.000253469ns。224宏、无锁存器/组合环；新增面积保守上界0.9265616712mm²，整机4.4487781712mm²。完整PPA审定仍需明确范围。
- 11138端口告警全量确认无逻辑引用。首层PT189个no_clock全部静态JTAG；78973禁用弧仅p/C/c/d，无user/loop/false-net标志。L01–L03活动来源/设置已轻量复核，362618个网络全exact，未标注清单空，averaged/X0.5/initial-Xfalse；未知值影响并未因此验收。首层详证`ICB32_POWER_L01_20261111.json`，中文`ICB32_POWER_REVIEW_20261111.md`。
- 原mapped.sdc序列化周期/下降沿6.66667/3.33333，PT历史功耗读取该文件。**精确交付SDC已经成功生成**，不是待做：964`runs/icb32_delivery_sdc01/mapped.precise.sdc`，周期/下降沿6.666666/3.333333，其余字节约束不变、网表与原报告未改，未重跑EDA。SDC SHA`9f49557c4aee558232cdb90f65c50ef6264250eb1f9c61e95747394e0348195d`，receipt SHA`7777a8850e91d5283cfd3093bd59173fce3285de01f4a583d0ff16d449850dbb`，09:07独立断言通过。见`ICB32_DELIVERY_SDC_20261111.json`。不要再次导出覆盖。

## 最终报告工具已经上传、服务器预检通过

- 源码/云端已核**cedb648f3b740d625d1c8857dda769f352eec6d8**，工具包`light-light126-icb32-report-20261111_091554-cedb648f3b74`，8文件/16942B，ZIP SHA`e939852693dc8ee09834e80b536e5c234d33f5e129aa07646e729f54a33bde54`，manifest SHA`4436e191de57d60ae8ebc08883c2d8a2bc9aca68d01c9f4ade413fc86bf6d037`。
- 本地干净包8项检查通过；09:19正常Linux FileZilla上传成功、队列空，Ctrl+D/Q关闭并确认窗口已消失。板端暂存`/home/root/icb32_report_0915`，GUI对应/home/board。服务器安全解包、manifest与8文件SHA通过，09:20服务器Python3的8项工具测试也通过；**最终大报告尚未启动**。
- 新`icb32_report.py`明确DC/波形精确周期与PT原SDC舍入周期的区别；可绑定`delivery_sdc: {run,sha256}`并逐字核对精确交付文件没有额外SDC修改。原综合审核提示单独保留为source_stage_review_prompts，不再误称已完成门级/活动或专用CPU诊断未执行。时序/功耗/官方面积归属不自动翻转PASS。
- 代码还有CRLF兼容修复：首次新增报告测试在Windows换行失败，保留CR后8项全部通过。原服务器LF导出工件完全不变，不需要重跑。
- 新报告包使用原964依赖：**PYTHONPATH设为964/workspaces/arch03/scripts，直接执行新操作包里的icb32_report.py**，这样新目录优先导入新report/delivery_sdc，其余依赖仍指原运行包。不修改964源码。其launch.json已记录argv/cwd/environment_updates。

## 下一步

1. 持续原power12队列。可用`takeover_local/icb32_finish_live.txt`和`icb32_power_numbers_live.txt`查询；`icb32_power_annotation_live.txt`只读已完成层的sources/settings/unannotated_after，不重扫VCD。12层齐后汇总，不提前称整机功耗验收。
2. 原metrics14及1200自动接续；按batch_progress实测宿主ETA留20%余量，不从芯片加速比估算宿主速度。新1200必须自己的30412800输出，不能继承fcd批量。
3. 原队列完成后，在**新文件**`runs/icb32_r4_finish01_queue/report_request.reviewed.json`复制自动基础请求，添加delivery_sdc（run=964/runs/icb32_delivery_sdc01，sha256=上述receipt SHA）与历史失败/停止/未验history，保留原request不变。
4. 使用新报告包launch.json中的环境/argv，在新目录`964/runs/icb32_r4_final_report01`串行导出，重新检查全部回执及VCD哈希。**这一步会读大型波形，不与重EDA并发。** 尚未生成reviewed request，不要现在直接执行launch。自动队列只生成原request，不执行新报告。
5. 补最终JSON/CSV/中文设计报告、同身份专用CPU诊断/复现说明、提交包及答辩材料。原8路完整功耗/R1正式PPA仍为后排对照；不得新增宽总线、INT8或其他架构。18:00冻结、11/12 17:16交付准备、用户截止11/13晚上不变。

## 恢复操作与失败路径

- 共同服务器bundles父目录`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。当前cwd为`light-light126-icb32-r4-20261111_043048-96443c284a1c`。固定100数据在`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest 0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507。
- 服务器只经开发板VNC，上传只用Linux FileZilla，不启用新隐藏通道。helper`F:/linux_fpga_try/ac820.ps1`、授权前缀保持；窗口最后VNC20971587，恢复先盘点。FileZilla现已关闭；原代理21036/VNCrelay23793保持。没有CUA会话或completion_summary欠项。
- **当前最后VNC命令为finish_live，可Up Return。** 若本地exec返回session先poll完成再读新截图；screenshot无expect-class。报告解包/预检已完成，不重复；尚无本地长任务。
- 手抄annotation SHA曾把873eae误写873aee，第一次断言拒绝，逐字符修正后09:07以前已独立验证。一次PowerShell嵌套引号生成查询失败已改apply_patch；一次多文件patch锚点失败分开重做；以上不是硬件失败。旧失败/停止路径全部保留。
- `progress_0858.py`、`progress_0910.py`已执行，`progress_0922.py`执行后也不可重复。新证据/本检查点待提交；持续同范围Git同步授权有效，未有自动审批拒绝。完成同步后继续工作，不发“等待你指示”的结束答复。

## 09:30增量：最终请求准备命令和串行锁要求

- 本检查点已提交并独立核对云端`1e09f2856d1dbb9a2029398e1ed4012f77994f66`。09:23:46实看仍L05，driver175706/PT wrapper176099；随后09:29截图保存在`takeover_local/icb32_finish_live_0929.png`。原队列继续，不重启。
- 已准备但**没有执行**三个本地VNC文本：`icb32_final_request_prepare.txt`711字（只在原queue reports_ready后核原request SHA并排他新建reviewed request，加入delivery_sdc）；`icb32_final_request_history.txt`956字（加入旧37批量用户停止和8192诊断前提失败两项已核历史）；`icb32_final_report_launch.txt`682字（新包manifest核验、队列终态后使用新包launch）。全部小于1000字符。原request尚未生成，不能提前执行。
- 两项历史路径已经再读证据确认：旧`light-light126-arch03-20261108/bundles/light-light126-lenovo-arch03-20261108_195108-63abe3d0b53d/runs/hex100_soc01`，37组后用户停止且功能TCM；本地`local_runs/icb32_sequence_fixture_20261111_010731_266143`是8192周期超时已进入计算的失败前提，4096修复后真实497序列通过。其它旧失败仍在交付索引/检查点，不当作新R4失败。
- **最终大报告还须补齐共享锁持有方式再运行。** 新包launch和当前launch文本只检查队列终态，没有原子取得`.arch02_team_lock`；不能仅凭此在队友可能开始工作时启动大型VCD重审。可以用独立操作包装一层轻量锁持有器，复用964 `server_run.call`的child_pid/log记录，并只释放自己PID/host/bundle/session的锁；若子进程仍在或所有权变化则保留，不自动清其他锁。当前未实现/未上传该包装器，也未启动报告。保持单重任务要求，不因工具预检PASS就跳过这一步。
- 已查看`icb32_batch.py`：按每个任务前后冻结哈希、一次ASIC编译、逐例输出回执、最终1200复核，batch_progress已有整体宿主耗时及剩余20%余量估计，不需要再加一套监测或推测芯片加速比。

## 09:34增量：最终报告锁包装器已本地完成

- 新增`workspaces/arch03/scripts/icb32_export_locked.py`，在验证新报告包manifest/8文件、queue终态、原request SHA与reviewed request（非空history+delivery_sdc）、全路径归属和PYTHONPATH后，原子创建既有team lock。独立控制目录记录state/report.log/child_pid，报告结束后核原输入未变及最终receipt/report SHA；只在子进程已结束且pid/host/bundle/session均仍归本进程时释放自己的锁。已有/遗留/其他人锁一律不清，失败不重试，子进程仍活跃则留锁供检查。
- `test_icb32_export_locked.py`两项本地检查通过：外人所有权、活跃子进程和意外锁目录内容均不得被清除，自己已完成才可释放。包装器尚未提交/打包/上传；原16KB报告工具包不用重传，可把这两个新脚本做独立小操作包，launcher指向已上传cedb报告包和相同964运行包。
- 仍未启动大报告，`takeover_local/icb32_final_report_launch.txt`是旧无锁直接入口，**禁止直接使用**，待新包装器上传后替换成包装器的后台启动。prepare/history两个请求文件仍可按前述终态条件使用，尚未执行。
- 最新截图`takeover_local/icb32_finish_live_0935.png`记录09:33实际状态，原队列不改；FileZilla关闭、当前最后VNC仍finish_live。压缩后继续先读计划/检查点，再上传包装器及持续当前原队列。


## 09:40增量：功耗5层完成；锁包装器包受FTP421暂阻

- **09:38:44.427857实际：原queue285397 running L06、completed=5、error=None，driver185674/PT wrapper186236。** L05为71.8645677mW、16.5705303632127979734µJ；尚不是12层均值。
- 新包装器已提交并push到ff181611dfaab7923546963e8411a7f1bbb781ee，本地及干净包2项锁检查通过。独立小包`light-light126-icb32-export-lock-20261111_093509-ff181611dfaa`，4文件/4777B，ZIP SHA`aab947a1a6a9939ad432bbc28f1f8b51a9221b3357ba344343a3450a4df8e573`，manifest SHA`aa979998df77370f5bd4bcbabe24bacc20a4b4c31a382d6d74d4b0d8381b5380`。
- 包在本地repo/local_runs，回执`takeover_local/icb32_export_lock_package_current.json`，板端`/home/root/icb32_export_lock_0935/<同名zip>`已SHA核对，GUI对应`/home/board/icb32_export_lock_0935/`。**未上传服务器、未解包、未启动包装器或大报告。**
- 09:37正常FileZilla站点登录收到421 There are too many connected users，自动一次重试仍421，09:38已Ctrl+Q关闭。当前不再占FTP连接，不开旁路；稍后用同一现有站点重试，不需要再次打包或改ZIP。上一次cedb报告包和4638精确SDC均已先前正常成功，只有新锁包装器包暂缓。未重复询问用户、无自动审批拒绝。
- FileZilla覆盖VNC时一次截图0939为黑遮挡，关闭FileZilla后0939_clear已真实读到L06；不能依据遮挡截图推测任务状态。当前最后VNC仍finish_live，窗口20971587；无本地长任务，原代理/relay保持。
- 新包装器launch.json已固定：调用自身icb32_export_locked.py，--package指cedb报告包、--manifest-sha256=4436e191...，--session=icb32_r4_export01，cwd=964。未来终态后再后台启动，control state在964/runs/icb32_r4_export01/state.json、report.log；正式输出仍964/runs/icb32_r4_final_report01。上传后先4文件哈希及2项服务器工具测试，不能提前启动正式报告。
- `takeover_local/progress_0940.py`执行后勿重复。接下来继续原队列，稍后重试锁包装器FTP；保持当前报告与SDC事实，不把工具准备当最终验收完成。
