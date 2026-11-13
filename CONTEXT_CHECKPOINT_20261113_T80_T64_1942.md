# T80开始映射优化、T64顺序调整已部署 — 2026-11-13 19:42

继续执行`workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md`及`T80_RESULT_PRIORITY_20261113.md`。前20条240任务，不启动100条；T64完整验收前不进入G64。**旧八路服务器全部文件绝不删除、覆盖或归档后删原件。**

## 最新实读状态

- T80唯一正式队列`t80_finish02`，driver14008，child23158，实际DC最后确认29185。19:40:35.304067仍running/t80_synth，log已出现`Beginning Mapping Optimizations (High effort)`。这不是最终setup/hold或面积；不引用中间迭代数字作结果。
- 19:39:35共享free19545456640B，/tmp free246422388736B；当前综合目录`du -sk`为261464 KiB。共享空间下降主要不来自本次综合目录增长，后续需持续看空间预检；没有删任何服务器文件。若新阶段因空间停下，可评估已存在的显式私有/tmp运行支持，不能移动正在执行的综合。
- 先前T80 ASIC14、前20条240任务6082560输出/total/sat、CPU竞争和恢复仍通过，生产RTL876b883不变。PPA、同网表门级与新20条浮点关联待齐全。
- 19:38/19:39只读聚合固定12实测：112569周期，0.3108226954事务/周期，80PE利用率18.011353%。源读/共享写/共享读/输出写响应延迟3/3/4/3拍；同tile块间隔198.1543拍，首供数等待4446.3333拍，最终写回尾部255.5拍。等待重叠，不能相加作为总周期。详新证据`T80_ASIC12_COUNTERS_20261113.json`及`T80_MEASURED_TRANSPORT_20261113.md`。

## 接收和工具

- 审查ops `light-light126-transport-reviewops-d611597`，8文件，manifest669837cebad4edd91988a0247b4b5c87950560756cb49243221b2ba422e1dac3。**19:29:49服务器预检8文件/导入通过。** 不再有待完成传输31899。
- T64新队列顺序提交**fbfdc2e8838c68a941eeb6f1e7b44655abe4651c**：只将timing/drc/structure补充诊断后移到gate14和SAIF12之后，仍在最终报告之前。gate入口原有必需端口检查完整保留。无VCS/PT并行，没有改变T80当前队列或任何生产RTL。Python3.6语法与2项完整队列报告校验通过。
- T64新ops已在`PROJECT/operations/light-light126-t64-finishops-fbfdc2e`接收并于19:36:44预检通过。3文件，manifest **6917b611b2145d665bd6b1abd98ef65014a67b77431cec7c65e0ff3736d9ff9b**。旧65d2507 ops仍保留；后续正式T64请求应选新ops。T64基础运行包仍fix02的875文件/6632a4...，生产RTL仍e2e83ce。**没有启动T64正式任务。**
- 本地exec36906传输26行已完成；18099/79286指标查询也完成。没有本地后台任务，没有VNC待输入。
- VNC18874436、FileZilla20972102，当前终端cwd原T80 delta01，workspace3。恢复先windows核对。FZ未连、最后421，不持续重试，不碰workspace4。

## 恢复步骤

1. 读取原`t80_finish02`，综合成功后立即运行`takeover_local/t80_preliminary_cmd.txt`只读抽取最终摘要，先报告面积、setup/hold、宏数、latch/loop与未验项目，不等功耗12。它会要求对应synth stage已passed且summary SHA匹配。
2. 可用查询文件：`t80_finish02_compact_cmd.txt`、`t80_synth_status_cmd.txt`、`t80_process_cmd.txt`、`t80_space_scope_cmd.txt`。当前所有命令已完成。必要时截图读取输出，不因窗口截图较早而重复启动任务。
3. 原T80队列自动继续诊断、门级、SAIF、power12及precision，不原地编辑、不重启。失败保留并查实际原因。尚无最终PPA数字。
4. 完整报告入口`transport_report_stage.py`仍要21阶段完成；从precision join取内部float20引用；再做未知活动/时序审查，不把reports_ready当验收。
5. 所有新工作先在独立目录；T64后续使用已通过预检的fix02与新fbfdc2e ops。G64不得提前。

当前工作树`E:/fpga_race-two/kwt1-t80-t64-g64`，个人分支codex/light-light126/n1-t80-t64-g64-20261113。最近已推送4ab1517，fbfdc2e及本检查点/指标报告待同步。PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109。共享锁仍在上级IC/.arch02_team_lock。

## 19:47增量：未来队列满盘收尾修复

- 新提交4bbd0afa078c48c07e7c774fae9bdfbdaae75c7b修复未来T80/T64队列在Popen之后、状态写入ENOSPC时仍必须等待已接受子进程的问题。3个场景分别测试两种队列通过。只改本地/新operations，不替换当前正在执行的T80队列。
- 新T64 operations准备为`light-light126-t64-finishops-4bbd0af`，3文件，manifest c8d77f164f4f1c798f85741ae1dd6ffe3be5c8691193e5a6071cb131f0e45028。本地身份预检通过。
- **exec61820正在VNC工作区3传输26行，尚无服务器完成回执。此时不可并发向VNC打字。** `local_runs/t64_priority_ops_4bbd0af/transfer_state.json`记录进度，`local_runs/transfer_t64_safe.ps1`为执行脚本。先poll61820并观察完成，再验证新ops；旧fbfdc2e ops不动。
- 19:46:46最新截图仍为DC映射优化的中间迭代，不能把其面积/负裕量当最终结果；原T80继续。
- d7969bd已推送；4bbd0af及本增量尚待推送。旧8路文件仍无任何删除。
