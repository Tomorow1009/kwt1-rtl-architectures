# T80继续综合、审查工具接收完成 — 2026-11-13 19:27

先重读有效计划`workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md`及补充`T80_RESULT_PRIORITY_20261113.md`。每版前20条、240任务；未授权100条。服务器旧八路全部文件禁止删除、覆盖或归档后删原件。

## 已完成和当前作业

- T80生产RTL仍876b883；ASIC14、240任务6082560输出/total/sat、真实CPU竞争及恢复通过。固定12平均112569周期、150MHz折算1332.5160568 task/s；PPA与新20条浮点关联尚未齐全。
- 唯一正式队列`t80_finish02`，PID14008，当前child23158，实际DC此前PID29185。**19:26:07.864091再次实读running/t80_synth、completed=2、无错误，可用磁盘22661824512B。** 不重启、不修改其脚本或输入。
- T64生产RTL e2e83ce，本地随机10000、14例、延迟/ABA、恢复及三套固件通过；已部署`light-light126-t64-v4-65d2507-fix02`，875文件，manifest6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1。19:07预检通过。真实CPU/EDA未运行；旧delta01缺ABI的失败目录保留。
- 审查工具VNC传输31899已经结束，**19:20:11观察到TRANSPORT_REVIEW_OPS_READY 8**，manifest669837cebad4edd91988a0247b4b5c87950560756cb49243221b2ba422e1dac3。目录`PROJECT/operations/light-light126-transport-reviewops-d611597`。仍需导入/身份预检，尚未开始审查任务。
- 本地没有活动的VNC传输或验证进程。VNC窗口18874436、FileZilla20972102于本次重新核对；恢复后再查windows。工作区3，终端cwd仍T80原delta01；勿碰workspace4。FileZilla未连接，最后19:09仍421。
- Git已推送847ce94，62ff08e复现入口及本检查点待推送。生产硬件未再改动。

## 新的执行优先级

用户建议综合一完就先报告最终网表对应面积/时序/宏与结构初值，不等12层功耗。已接受，保持最终验收严格区分。现有队列不可原地换序；可选VCS/PT流水需新调度与独立回执验证，不为其拖延当前队列。19:23资源：96CPU、约665GiB可用内存、约21.45GiB磁盘；许可未确认。既有功耗入口要求完整12层SAIF冻结摘要，不能直接偷跑单层PT。

## 接续

1. 用`takeover_local/t80_finish02_compact_cmd.txt`读取原队列；综合完成立即读取同网表summary、metrics和结构报告，给初步结论。不要只等最终队列。
2. 队列继续timing/drc/structure、gate14、SAIF12、power12及precision。失败保留；不原地重复。
3. 审查ops预检后，用完整队列及自己的ASIC/batch导出报告。precision需引用join内部的float20报告，不混同两个目录。
4. 收齐T80必要证据后启动T64自己的正式队列；G64必须等待T64完整验收。
5. 未知活动、严格时序及面积归属不得借用历史N1/B0。T80与T64本地pin_mock对比不是实际SoC吞吐。

PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109。原协作锁在上级IC/.arch02_team_lock，绝不自动清锁。所有历史失败与旧8路资料保留。
