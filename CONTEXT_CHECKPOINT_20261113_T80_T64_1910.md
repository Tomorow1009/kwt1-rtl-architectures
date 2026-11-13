# T64接收预检通过、T80综合仍运行 — 2026-11-13 19:10

**用户最新约束：服务器旧8路全部数据及产物禁止删除、覆盖或归档后删原件。本轮没有执行服务器删除。** 有效计划仍为`workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md`，每版前20条240任务；全100条未授权；G64等T64全项验收。

## 运行与接收

- T80原队列`t80_finish02`，驱动PID14008，开始18:22:51，仍是唯一正式EDA队列。19:03:01实读running/t80_synth、child23158。19:08:08.734274只读进程核查：实际DC PID29185、父23158，R态，99.7% CPU，累计CPU00:37:16，RSS25468948KB；没有失败终态。19:04:10可用空间27936161792B。不要因日志长时间停留在Processing而重启，实际CPU仍在推进。
- T80此前ASIC14、240任务6082560输出/total/sat、CPU竞争及恢复均通过。固定12平均112569周期，150MHz折算1332.5160568 task/s；面积、时序、门级、功耗与20条新浮点关联仍待收齐。旧finish01失败保留，生产RTL876b883不变。
- T64第一次874文件重建成功，但服务器固件预检发现遗漏`T64_ABI.md`。这是运行子集生成遗漏，不是RTL输出失败；没有启动任何T64 ASIC/EDA。旧`light-light126-t64-v4-65d2507-delta01`原样保留。
- 已在全新`light-light126-t64-v4-65d2507-fix02`补齐固件全部来源引用，875文件，manifest SHA **6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1**。**服务器19:07:08.365340预检通过全部875文件和IRQ/竞争/恢复三套固件，row_lanes=4、source65d25073a1afcf4fc37da29c2d40ffc56f7e122a。** 实际RTL仍e2e83ce，T64真实CPU/PPA仍未验。
- T64完整ZIP仍`local_runs/light-light126-t64-v4-20261113_183328-65d25073a1af.zip`，981文件、9597032B、SHA bbc52d95968ec51324b7af7e30600361cb5c2f4461c9f735a401ac7278320709。本地`local_runs/t64_fix02/reconstructed`与该完整包875项完全一致，已实际执行三套固件验证。首次缺ABI的子集生成路径要记为失败，不能只做import检查代替固件引用检查。
- 前两次VNC传输exec60646（141行）、3519（21行）均已结束。T64预检和只读短命令也均结束。

## 当前正在进行的本地任务

**exec会话31899正在通过VNC工作区3发送审查工具，64行。完成前禁止额外VNC键盘操作。** 实时进度`local_runs/transport_reviewops_d611597/transfer_state.json`；执行脚本`local_runs/transfer_transport_review.ps1`。只是在新operations目录写入工具，不启动EDA。

- 目标：`PROJECT/operations/light-light126-transport-reviewops-d611597`；8文件，manifest **669837cebad4edd91988a0247b4b5c87950560756cb49243221b2ba422e1dac3**。读取已经存在的旧T64 delta01作为部分相同代码来源，SHA逐项核验，不修改它。
- 本地源`local_runs/transport_reviewops_d611597`；工具从已提交d611597导出，T80旧bundle+该ops的8模块本地导入通过。包括报告导出、未知活动清单/连接/别名/静态概率审查及新阶段身份绑定；不自动授予PPA验收。
- 小ZIP37239B，SHA **9d030d10116995b3ffed1cdd8ecd6d1188e194d47260842d97fbe4d32812cba2**，已暂存板端实际路径`/opt/ac820-gui-root/home/board/t80_review_ops_1857/`，桌面FileZilla看到`/home/board/t80_review_ops_1857/`。第一次误用桌面路径作板端根路径失败，未创建文件；修正后upload SHA通过。
- 19:09再次FTP连接仍421；没有服务器FTP上传。不要不停重试。FileZilla未连接、队列空。

## 接续操作

1. 重读计划、本检查点及`T80_T64_G64_EXECUTION.json`。先poll31899，结束后截图看`TRANSPORT_REVIEW_OPS_READY`8文件及manifest回执，核验后才能使用。
2. 终端cwd仍原T80 delta01：`PROJECT/bundles/light-light126-t80-v4-20261113_165244-876b883d9519-delta01`。VNC18874436、FileZilla20972102本轮已实读，恢复后重新windows确认；勿碰workspace4。
3. 原队列状态命令已备好`E:/fpga_race-two/takeover_local/t80_finish02_compact_cmd.txt`；进程命令`t80_process_cmd.txt`；日志尾部`t80_synth_status_cmd.txt`。不要在31899输入中并发执行。
4. T80综合后队列自行继续timing/drc/structure、门级14、SAIF12、power12及precision。读取实际终态；错误保留后定位，不原地重跑。T64正式作业等T80结束及必要审核，后续只用fix02。
5. T80报告导出工具`transport_report_stage.py`需要完整21个阶段及自己的ASIC引用。precision参数必须取join报告内部reference指向的float20，不直接指向join目录。导出之后仍需审核时序、面积和未知活动；不把`reports_ready`直接标为验收。
6. 本地新增`test_transport_report.py`的2个加权/缺项/窗口测试通过，提交5a3a633；最近已推送26f4541，5a3a633及本检查点待同步。T64代码/固件没有改动。

PROJECT=`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`。现有team lock仍在上级IC/.arch02_team_lock，绝不自动清锁。历史旧8路及其他失败证据均保留。
