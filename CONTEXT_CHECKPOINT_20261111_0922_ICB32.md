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
