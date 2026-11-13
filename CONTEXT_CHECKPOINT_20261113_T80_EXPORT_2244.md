# T80全部21项完成，报告导出中 — 2026-11-13 22:44

继续有效计划T80_PRIORITY_COMPLETION_PLAN_20261113.md：只完成T80，G64取消、T64暂停、旧8路全部文件保留。原ASIC240、综合及gate14不能重跑。完整历史和路径见22:20、21:53检查点及STATUS。

主队列t80_finish03于22:33:18.385053自然完成，status=reports_ready_review_required、child_pid=None、21个阶段齐全。最终state SHA `a746925c3ef46405209d14494e0aaa88a30e98fdb6c06a942687ae64f61537c0`。原父183563已由导出启动器确认消失、协作锁已自然释放。

十二层SAIF通过，summary SHA `2fee667759ed46e95e672716ef4ccea60c1155fa63c0bc27323d72be5f49a35d`。十二层PT完成。原始功耗W依次为0.0501254834、0.0502292328、0.0502437986、0.0502531491、0.0503219143、0.0503468513、0.0503912009、0.0503552333、0.0503889248、0.0502546728、0.0501167029、0.0498352200。按实际周期手工转录复算：时间加权50.2316198707mW，37.6968176785µJ/task；尚待正式导出值交叉确认和未知影响审核，不能标系统功耗已验收。

前20条精度关联通过：240任务、6082560输出及total，最大逐层NRMSE 0.20198143836753799%，最大单任务0.20953408931848963%，X/W/b裁剪0、饱和0，fresh_float_reference_verified=true。精度summary SHA `b620e1201d725e9f48a63547d0c80cc2229a581bd750c36c9d54f2ff61e10151`，路径active/runs/t80_finish03_precision/t80_precision。非官方600条。

实际导出已启动：22:36:41开始，PID318967，session=t80_final_report01，使用ops-review-b80b171（manifest b4cef85bf45ad4bfc49bf328cc10e9ca75072615e5063696e8c03d275085f884），source SHA bb28cd7ce9157ec0e5e4e3560e70246abf61efd92d9a6b28277ef55bd73b717b。22:41:37实读status=exporting、无错误、log空；仍在核验原文件，不能重复启动。运行包active=/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4；导出状态active/runs/t80_final_report01/state.json；日志同root/ops-review-b80b171/t80_final_report01.log。导出包含unknown_inventory，结束后再做连接/别名/静态概率策略审核；这些额外审核尚未启动。

已集中读取12个PT timing_check/disabled_timing原报告，并先核验artifact SHA。画面可见L04–L12均189个no_clock且全在静态JTAG、HF6.666666ns/LF66ns。禁弧计数每层c12145、p60252、C72506、d201（case、常量及条件弧）。前三层滚出截图，最终需再以汇总集合确认全部12层；不要把截图未见的数据当作逐层已阅。查询文本takeover_local/t80_timing_read_cmd.txt，截图t80_timing_all12.png。无新DC/综合。

归档工具ops-archive-66186a6已部署并导入通过，未运行。等导出和审核全部关闭后，完整runtime根复制到durable backups新目录，保留原件，逐成员回读；不要删除任何历史资料。新归档日志和cwd必须在runtime根之外。

VNC18874436/workspace3，FZ20972102断开；当前没有未完成exec或半截输入。最后VNC命令读取导出state及log，不能误Up当成功耗查询。功耗通用命令takeover_local/t80_power_watch_cmd.txt；精度命令t80_precision_final_read.txt；导出启动器t80_export_launch.py和local_runs/t80_export_launch已执行完毕，不再执行。Git已push38057b4，本检查点待提交。压缩恢复重读AGENTS、计划、本检查点和STATUS，再查看当前导出状态。
