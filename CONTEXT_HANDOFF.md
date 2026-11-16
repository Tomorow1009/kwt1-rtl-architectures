# 当前交接：T80 → P80 → C80 → C32 → G32

更新：2026-11-16 15:13，北京时间。以下远端状态附观察时间，不代替恢复时现场核对。

## 必须先读

- `AGENTS.md`、`handoff/team/README.md`、`handoff/team/SYNC.md`。
- 有效计划：`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`。
- 当前详细检查点：`CONTEXT_CHECKPOINT_20261116_C80_FINAL_NETLIST.md`。
- `handoff/team/STATUS.json`中`c32_g32_20261115.c80_development`及`workspaces/arch03/C80_STAGE_PROGRESS_20261116.md`。
- 本页整理前的完整交接原文保存在`CONTEXT_HISTORY_20261116_C80_1458.md`，未删除旧进展或失败路径。

## 用户约束与当前阶段

持续执行新计划。最终32PE、150MHz/6.666666ns、SS/.99V/125°C、项目保守面积≤1.00mm²。每版正式批量仅前20条×12层；完整100条另行授权。原32位ICB、平台缓冲参数、源读→共享写成功ACK→原总线实际读回→计算→最终输出ACK/排空不变。X14/W12/acc32/total33/SHIFT10不变。

**桌面`T80_Delivery_20261113`及任何旧八路数据不得修改、移动、删除。P80冻结包和备份保持。** 不恢复旧T64/G64/A/宽ICB/省略共享写路线。

S0、P80已验收归档冻结。当前C80；C80完整完成后才进入C32-A/可选B，再G32。C32只有只读设计核对，没有硬件开发或服务器任务。

## 本地身份

工作区`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。最新已push **19ce48f**，其后是进度文档变更。

C80受测包提交仍是 **74f3ae7bb479d5fdd7917702c4a2c0671eacb61b**，后续工具不改受测RTL/固件。历史未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不添加、不运行。

## 远端活跃作业：不要重复启动

私有根`/tmp/s4_21usr_c80_20261116_1245`，包`light-light126-c80-74f3ae7`。1008文件清单SHA `d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59`。

1. 原初始队列父 **279630**，`包/runs/c80_initial02/state.json`，13:21:31启动。15:06:04已完成最终综合并进入batch20；15:09:43为13/240、零失败。所有原DC子进程自然完成，不能重启。
2. 后续父 **314678**，`私有根/c80_followup01.json`，14:49:07为waiting_original_initial02。原队列结束后按严格条件独立恢复缺NumPy精度，再顺序gate14、SAIF12、时序/DRC及PT12。新目录`runs/c80_precision03`（如需）及`runs/c80_finish01`。已安排，不手动重复派发。
3. 汇总父 **4047**，`私有根/c80_export_review01/state.json`，14:49:07为waiting_original_finish。源码`ops-export-fd51996/C80_EXPORT_REVIEW01_20261116.py`；等314678退出后导出同一版报告及未知活动/连接快照。连接查询持原团队锁，不并发EDA、不自动认可/归档/进入C32。

锁仍为原共享`.arch02_team_lock`，不清锁、不杀父子、不改活跃包。新工具导入回执SHA已机器断言：`3af466b9209b221402ea7a466569a47c591e0c8184ad00ee776a5c381a04450c`。完整身份和失败传输在详细检查点。

## 已完成与尚缺

- C80自身ASIC/E203十四例354816输出、total/result/saturated及坐标、真实IRQ/WFI通过；恢复/ABA和CPU竞争通过。
- 固定12总847238、平均70603.1666667周期、150MHz折算2124.5505985task/s；相对P80吞吐+9.8326562%。非实物测量。
- 固定12编码平均29756→25790B；实际四段响应共384174笔，源读/共享写/共享读各77370，输出写152064。
- 之前本地48解码、完整14、raw、两拍SRAM/预取ABA、10000随机＋32定向块全部通过，详见C80_LOCAL检查点。不重复已完成项。
- 最终新综合完成，保守面积0.9611361367002672mm²，setup+0.000216007ns/hold+0.00623399ns，220宏/0锁存器；15:11服务器assert身份及关键数字。完整SHA和首次转录更正见新检查点。
- 仍缺C80自己的240/FLOAT、gate14、SAIF12/PT12、独立审核、持久归档和冻结。尚无C80功耗结果。不得转移P80证据为C80 PASS。

P80冻结`arch03-p80-depth2-20261116-1211`：1934.3524task/s、保守0.9529288663mm²、53.7758513mW、27.8004393µJ/task，布局前声明范围；备份copy03已完整回读。引用`P80_FREEZE_20261116.json`，不重跑。

## GUI与下一步

先读computer-use技能及`F:/linux_fpga_try/AGENTS.md`，使用现有板端`ac820.ps1`可见VNC。恢复重新windows确认；本轮18874435、workspace3，workspace4不操作，FileZilla未用。14:56两个终端标签空闲；最近输入25231/16671/69193/74090/83364/63186均已结束。未运行后台只读观察器。

先读取原279630/314678/4047及锁/空间，不据旧状态重启。最终综合已通过数值闸门，当前继续自己的240；当前阶段失败则保存原记录另行诊断。完整审核和复制归档冻结之后，才实现C32；接口准备在`workspaces/arch03/C32_PREPARATION_READONLY_20261116.md`。

每次压缩前更新本页与详细检查点，记录新进程、证据、未完成项和失败入口。完整历史记录不删除。
