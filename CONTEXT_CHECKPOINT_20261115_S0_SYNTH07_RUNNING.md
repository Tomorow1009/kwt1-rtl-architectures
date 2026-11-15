# S0 synth07正在运行 — 2026-11-15 22:00

**22:14:21最近观察：父139859仍running、CPU/SoC子143046 CPU99.7%、elapsed9:14，日志在优化ITCM WEN相关路径，无错误；未看到最终网表/面积/时序。前台现为新只读live watcher（PID未从截屏读出），其本地命令`local_runs/s0_live_watch_command.txt`会自动转看finish01并在终态退出；不是shell。63916及此前全部输入均结束。自动接续143305不重复启动。**

**报告准备：** 已只读核验原T80请求`/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4/runs/t80_final_report01/request.json`，SHA **ec74187f550a70e5bbe0662862b8db5c142448baa223855099b5e391612d9e43**。本地新`handoff/team/evidence/S0_BUILD_REPORT_REQUEST_20261115.py`仅准备请求（没有运行/部署）：finish01全部17步顺序完整并终态后，复用旧请求的同源ASIC/240/FLOAT三项，综合/gate/SAIF/PT全部使用新S0引用；拒绝不完整队列的本地夹具及Python3.6语法通过。随后调用包内原`s0_report.py`导出，不能把准备请求当正式报告。旧FLOAT位于另一个/tmp根，仅按固定旧请求与manifest身份读取，不注入新runtime_roots或扩宽路径权限。

**22:06:56最新实际状态：加速器增量已完成，父139859仍running/error=None；DC子143046正在CPU/SoC块。自动接续等待器143305已实际启动，源码cc21f8d，`ops-9ffb2a9/s0_followup_cc21f8d.log`显示等待synth07 running；finish01尚未启动。85724/75913输入均结束；当前VNC前台Bash空闲（无watcher）。需要继续时先只读现有state/进程，绝不再启动synth或等待器。**

**22:04更新：共享块已完成，22:03:36实际观察父139859、DC141571正在accelerator增量映射，CPU99.2%、elapsed1:48，无错误。只读watcher140380已由Ctrl+C正常退出，后台综合不动。当前唯一输入exec85724正在传输18行`local_runs/s0_followup_cc21f8d/transfer.ps1`，不要并发输入或重复执行。接续脚本SHA841ced330ffedd9e37b1640615609bfa939894fb5926789da168bc478167c0dc；部署后会启动仅等待synth07终态的后台观察器，全部门槛通过才一次启动finish01，任何失败即保留并停止，不自动重试。尚未观察实际部署/等待器PID。cc21f8d已push。**

恢复先读AGENTS、CONTEXT_HANDOFF、本文、STATUS.c32_g32_20261115，以及有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`（SHA1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39）。路线S0→P80→C80→C32→G32；S1–S4尚未开始。

## 当前实际作业：不要重启

- `/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-9ffb2a9/runs/s0_synth07/t80_s0_synth`。
- 工具提交 **9ffb2a987ae8261e1d27e80fefa89886b7d4d2c5**，852文件已服务器核验；manifest **d397b97768c6ce5089aeda32a5e2e22d50e30f0b5a34c6edfae12e71ea9988ba**。
- 父 **139859**；启动器来源437f156，服务器`ops-9ffb2a9/s0_synth07_launch_437f156.py`，SHA **5439847d78a2665ec7820f3d9c75d211cccb1b3307ca0f032e08aadb966a264d**。
- 控制记录`ops-9ffb2a9/s0_synth07_launch/{launch.json,driver.log,command.json,seed.json}`；子进程回执`runs/s0_synth07/process_ledger/child_*.json`。
- **22:00:10截图实际观察：短DDC链接探针已通过并完成两子块完整module token核对，进入characterization；子140561，CPU101%，12秒，无错误。** 探针子140080已退出；当前尚无新最终网表、面积或时序结论。
- 唯一原共享锁保持`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`；不改锁、不清锁、不并发EDA。

VNC **18874435**、workspace3前台为只读观察器 **140380**，每30秒读state/child/CPU/日志尾6行。不是shell；需要输入时先截图，仅退出此前台watcher，不能信号父或DC。观察器终态自行退出。42215、37121、25471输入全部完成，无半截传输。板端转发91027保持，FileZilla未连接，workspace4不碰，旧tcsh残留输入不碰。

本地观察命令`local_runs/s0_synth07_watch_command.txt`；截图`E:/fpga_race-two/takeover_local/s0_synth07_watch2200.png`。

## 新修复及已经核实的路径

1. synth05/a5包21:33失败：linked.ddc和mapped.ddc同时有同名设计，两条`arch03_t80_accel doesn't specify a unique design`。DC虽写文件仍拒绝；未进入CPU。旧目录保留。
2. synth06/5e包父135293：试用`read_file -single_file`仍未消除同名设计。短探针DC135510在67秒内发现两个块ambiguous，停止，**没有启动新块映射**。旧目录保留。
3. 当前9ff修复：`s0_read_replace`读取前保留设计对象集合，读后识别新对象，仅删除同名旧**内存**对象，再检查名字唯一。不会删除服务器文件。CPU和最终顶层共用这个入口；seed路径在原RTL缺失单元检查后`remove_design -designs`，保留库。
4. 新短探针实际通过：原unmapped顶层＋两个保留mapped seed可正确link，宏检查及两子块逐module token一致。只说明加载/链接方法正确，不是新硬件功能PASS。
5. 本地21项相关测试、852文件/136模块闭包、Python3.6语法与实际受测源码字节一致检查通过。
6. 三DDC完成后仍须CPU/顶层child identity、220宏、面积、setup/hold及结构/覆盖检查，不以中间块结果替代最终结果。
7. 新报告携带incremental_recovery与失败seed工具耗时；不能把恢复时间冒充从零完整综合耗时。

当前恢复seed仍只来自严格核验的旧synth03/05c包（原stateSHA83a9b896…、manifest4473686e…）。seed是未验收起点，当前仍重新incremental compile及生成完整报告。旧set_map_only错误来源、synth04锁ENOSPC、早期失败和可恢复编译缓存归档见S0_RECOVERY_RUNNING/S0_DDC_CONTAINER检查点。

## 收尾准备和待做

- 本地`handoff/team/evidence/S0_SYNTH07_FINISH_LAUNCH_20261115.py`已准备，Python3.6语法及隔离临时目录的完整启动路径夹具通过（Popen被替身替代，无EDA运行）。尚未部署/执行。
- 它要求synth07终态passed、真实launch PID已退出、同最终摘要setup/hold非负、保守面积≤1.00，再确认原锁和EDA空闲。收尾一次持原锁串行structure→gate14→SAIF12→timing/DRC→PT12，独立兄弟目录。
- **旧固定synth03/05的finish启动器均无效，不执行。** 未提交synth05文件只作旧准备物，不能误用。
- 新最终网表gate14、SAIF12、PT12、未知活动/模型审核及独立JSON/CSV/中文报告全部待做；同源旧ASIC14/240仅在身份一致时引用。S0正式报告/冻结后才进入S1。
- 新/tmp产物还需最终持久归档；目前不是最终交付。

## 始终保护

服务器桌面`T80_Delivery_20261113`与全部旧八路文件不写、不移、不删。当前T80硬件876b883及原测试证据保留。原32位ICB与四段实际传输、150MHz/6.666666ns、SS/.99V/125°C、SHIFT10不变；正式仅20条/240任务，完整100未授权。当前轮没有新的清理动作，已有N1编译缓存无损归档不重复。

Git分支`codex/light-light126/t80-pipeline-c32-g32-20261115`；当前工作树`E:/fpga_race-two/kwt1-c32-g32-20261115`。437f156已push；本文/验收表/收尾准备随后同步。每次压缩前更新根交接，压缩后核对真实当前PID、终态及输入，不能照旧记录重复启动。
