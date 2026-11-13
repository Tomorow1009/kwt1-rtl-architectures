# T80 L03通过与输入备份 — 2026-11-13 21:00

压缩恢复先读本文件、20:57检查点和T80_PRIORITY_COMPLETION_PLAN_20261113.md。G64取消、T64暂停；旧8路不删除，当前只完成T80。

20:59:28.315609实读：t80_finish03仍running/t80_saif，父183563、子183576、error=None；L01/L02/L03三层已通过，cycles116752/113732/112106，SAIF字节97722100/97710598/97711398。/tmp剩157567946752B。后面9层活动、12层功耗、20条精度关联仍自动继续。当前不启动其他EDA、不修改在跑包。L01用了405.330秒CPU，后续每层约数分钟，不能按普通门级50秒估算。

本地新增输入备份local_runs/t80_input_backup_cef81d4/t80-hardware876b883-activitycef81d4-inputs.zip，8989696B，SHA 1f6742d40f171ccb06f979f6a31ad39fec18b31c4a20dd53101cd3ec263298ed；833项逐文件回读均匹配manifest181bb96b...。只备份已冻结输入，不代表正在生成的输出已经备份，更不代表T80已整体验收。回执已入handoff/team/evidence/T80_INPUT_BACKUP_20261113.json。

已读取N1_FINAL_REVIEW_20261113.md：其最终审核接受的是稳定任务模式和可复现布局前模型，非物理初态最坏值。T80必须用自己的12层PT重新核no_clock/禁弧/未知和模型，不能借N1 PASS。原T80 TIM-134=4与DDC查询3平台时钟的统计差异保留，不额外重新综合。四个LINT1对象已实读为原debug两reset输出、AON POR、PLIC prio；常量/重复输入LINT32/33与实际原文一致。未完成审核保持false。

检查过n1_archive_runtime.py：它硬编码N1的stage/queue schema，不可直接套用于T80；尚未新建T80输出归档器。最终应在原队列、报告和审阅均结束后，用明确T80路径及哈希的无损归档保留源码、活动、报告，绝不删旧8路或输入。所有/tmp产物持久化仍待办。

8文件最终report ops已经部署并预检通过（/tmp/s4_21usr_t80_20261113_2012/ops-review-cfbca86；manifest f35927b878b4fe32caf77fb63d252939fb8aa9d4eb523eff367f2461af8e3c81）。后续用其transport_report_stage.py带明确runtime-root及181bb96b...manifest；当前原采集/功耗队列用ops-cef81d4，实际request SHA e0009ed15805d221489ac441b2019669d79e506ef7ad0bf54274de1d9b35c888。

**没有待续传输、没有半截VNC命令、没有本地活跃验证进程。** 所有既往exec传输已完成。当前状态命令takeover_local/t80_finish03_compact_cmd.txt；下次按需截图。VNC18874436/workspace3，FZ20972102断开，恢复先windows核实。主终端仍在共享盘旧T80 delta01。

最新已push eb6215d；d6e3c45及本次更新待同步。工作树kwt1-t80-t64-g64，个人分支codex/light-light126/n1-t80-t64-g64-20261113。禁止重启旧队列、重复ASIC240或门级14、恢复G64/T64。
