# S0完整功耗已获得，正在汇总 — 2026-11-16

**01:59:38最新实查：全12未知清单、连接、别名和模型快照已完成，export193002/检查218088及子进程均退出，团队锁释放，VNC终端空闲。S0声明任务模式/布局前估算的技术结论通过，待copy-only归档回读后冻结，S1尚未改硬件。先读`workspaces/arch03/S0_STAGE_REPORT_20261116.md`及`handoff/team/evidence/S0_STAGE_CONCLUSION_20261116.json`。**

- 模型快照SHA `351bc89a8707b409897887290a9201e79ba54b427aec9e74dd284f15331ee32d`，全部2444未直接解析名称均分类，未知显式控制引脚0；12层活动注释完整，220宏覆盖。
- **哈希转录纠正：** 正确report SHA为`65c471298fe5109ed4f246df573422cbd9434e15c5f9f4d42ef4b5b9caa3f48c`。旧本地索引首部多写c、末尾漏c；一次只读查询因此AssertionError，已纠正本地记录，原服务器报告从未更改。
- 全12禁用弧实际均为C72218/c12145/d201/p59255，总143819。旧首层148318及其分项为本地屏幕转录错误，由完整表核对更正，原服务器表不动。
- 新copy-only启动器`handoff/team/evidence/S0_COPY_ARCHIVE_20261116.py`已本地Python3.6语法核对，尚未部署或执行；沿用已部署e516e4c归档工具，外部cwd和日志，完整回读，源不删。
- 最新空间/tmp 92,301,160,448 B、storage2 12,073,304,064 B；归档工具须再次按真实压缩量检查20%余量及2GiB保留，不清旧证据。
- 最新输入83216/90179/50559/12160均已结束；前台旧watcher241373自然退出，当前Bash空闲。VNC18874435/workspace3、FileZilla关闭；桌面T80及旧八路不动。

**01:39:39最新实查：S0报告已完整导出；export转为unknown_inventory子239612运行，L01/02未知清单已完成（40699/40689项）。当前前台只读watcher241373；export193002与检查等待218088保持。46642/56100及此前输入全部结束，S0未冻结、S1未开发，保护目录不动。**

报告目录：`66b9496/runs/s0_report01/t80_s0_report`，JSON7,231,534B、tasks.csv4035B、summary.csv366B、report_zh.md4103B、receipt.json414B。新的小型转录索引为`handoff/team/evidence/S0_REPORT_EXPORT_SNAPSHOT_20261116.json`。

- report SHA：`65c471298fe5109ed4f246df573422cbd9434e15c5f9f4d42ef4b5b9caa3f48c`。
- receipt SHA：`603fc47473341acebd2b1bc59a528a3526fd8a5d9647f221d29f8d6eacd1d667`。
- S0新最终网表 SHA：`8ec59cc89847f18713e7504dc4d7e35eeb491432490209102764165d4409ff12`。
- 报告确认112569周期/1332.5160568184847task/s，功耗/能耗与上次12层直接汇总一致；ASIC14、gate14、final240、activity12、power12及两组内部精度字段为真。
- 前20条最大逐层汇总NRMSE0.20198143836753799%，最大单任务0.20953408931848963%；固定12任务最大0.1425636423408142%。两组样本不混用；官方600条仍不宣称通过。
- 报告仍是数值导出，独立阶段通过由后续模型/连接事实和人工结论另记；不原地改该报告或回执。当前不启动第二个导出、未知清单或连接任务。

**01:28:59最新实查：export子231552仍正常运行11:40、CPU99.2%；新前台只读watcher236422。旧233182只退出用于查询项目文件，01:26:24观察report正读取本次SAIF layer_07.saif，证明在复核活动而非停滞。后台export193002、检查等待218088保持；16713及全部输入结束。f090f49已push。原17阶段全部通过收集，S0尚未冻结，S1未开发，保护目录不动。**

## 当前有效要求

先重读`AGENTS.md`、`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`、本检查点和STATUS。用户原计划与保存副本SHA均为`1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。

路线S0→P80→C80→C32→G32；正式最终32PE、原32位ICB、原平台缓冲参数、真实共享写ACK后原总线读回、150MHz/6.666666ns、SS/.99V/125°C、项目面积≤1.00mm²。数值X14/W12/acc32/total33/SHIFT10不变。每阶段完整报告后冻结再推进；正式批量仅前20条240任务，不开100条。

**服务器`Desktop/T80_Delivery_20261113`及全部旧八路文件禁止写、移、删；不重启旧T64/G64。** 原T80硬件876b883保持。当前个人分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。本地工作树`E:/fpga_race-two/kwt1-c32-g32-20261115`。

## 已完成及真实结果

- 原S0 `s0_finish03`于01:16:37观察终态`reports_ready_review_required`，17阶段全部完成，无错误。父172535退出；原只读watcher224035自然退出。不重启该队列。
- 新综合为a5f138e/s0_synth08，保守项目面积0.9535222591004618mm²，整机约4.475738758645mm²，220宏，latches0；setup+0.000386715ns、hold+0.0055688ns。三块同源身份及边界预算证据保留。
- 综合耗时结论必须包含恢复路径：synth07的shared约40.45s、accelerator约197.28s、CPU约770.62s是该次映射记录，其中加速器用了经指纹核验的先前恢复种子；synth08只重链接。**不能把三项相加当冷启动完整综合耗时，也不能据此预先宣称分块综合的加速倍数。** 原失败作业和种子构建成本均保留，最终报告注明此边界。
- 新网表门级14例354,816输出通过；无SDF、门级result/saturated/坐标/共享写回核对，不宣称门级internal total33可见。S0同源ASIC14/240沿用原受测RTL证据，不重跑。
- 新网表SAIF12及PT12全部完成。01:17:51逐个核对12份summary哈希、层序和共同综合/活动身份后读取：
  - 时间加权平均功耗`0.05024037337247095855282833936 W`。
  - 平均能耗`0.0000377033868307654954451 J/task`。
  - 加权动态`0.04306381651949904799130607302 W`，泄漏`0.007176556796782684398013662731 W`；分量与total保留PT原精度，不强行归一化。
  - 12层总窗口`9005519.099448 ns`，按6.666666ns计算平均112569周期。P=总能量/总时间的本地转录交叉计算误差0。
- 小型证据`handoff/team/evidence/S0_POWER12_SNAPSHOT_20261116.json`；截图`s0_power12_values_0118.png`。完整功耗约50.2404mW、37.7034µJ，相对原T8050.231619870716627mW约+0.017426%。均布局前估算，独立活动/模型事实汇总还在进行，S0尚未冻结。
- **转录更正**：首层实际`0.0501344018 W`。早先本地/口头`0.051344018 W`是屏幕数值转录错误，已向用户更正并修STATUS；服务器原报告从未改动。首层不是12层均值。
- 时序/结构独立读取见`S0_SYNTH_REVIEW_SNAPSHOT_20261116.json`及`S0_STRUCTURE_REVIEW_SNAPSHOT_20261116.json`。DDC高扇出清单3个时钟网络，与初始TIM-134的4个计数差异保留；不能伪称已消除该警告。未细分面积0.1609004207998941mm²仍全部计入保守上界。
- 首层PT完整表189无时钟引脚均静态JTAG；完整12层禁用弧均143819，仅c/C/d/p（更正早期转录，见顶部）。已完成前6层stdout日志哈希和错误前缀检查，全部12层原工具的错误拒绝及redirect报告核对已完成。

## 当前实际进程与下一步

**01:20:54实查：前台只读watcher233182；export子231552运行3:35、CPU97.9%，正在导出报告，没有失败。全部53391/46008及此前输入已结束。**

运行根：`/tmp/s4_21usr_t80_20261115_1830`。

1. 综合包`light-light126-t80-s0-a5f138e`，manifest `c4774571c8aebe323657a5aaebc017f24324396b28ea6b2852e32e40a213b924`。`runs/s0_synth08/t80_s0_synth/summary.json` SHA `e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916`。
2. 验证包`light-light126-t80-s0-66b9496`，manifest `2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4`。`runs/s0_finish03/state.json`终态SHA `dc900c9d685a0c0d968b40581af040350818e632886b5ace2a60e5ed89a12ce0`。
3. **export父193002**：`ops-66b9496/S0_EXPORT_AFTER_FINISH_20261115.py`（源8da012f）已等待原队列正常结束。当前子231552运行`s0_report.py`，输出预定`66包/runs/s0_report01/t80_s0_report`。随后已有入口生成`runs/s0_unknown_inventory01`，全12未知活动清单。状态看`ops-66b9496/s0_export01_control/{report.log,report_exit.json,unknown_inventory.log,result.json}`。不要重复启动。
4. **检查等待父218088**：`ops-66b9496/S0_COMPLETE_REVIEW_20261116.py`，源dfa13b0，SHA `8f3299cc60796e8f679d3b05d83507afec726e7d439939730e9cb8272a375878`。等export result通过后才生成新请求、用原团队锁执行一次DC连接查询、再作只读别名与模型事实汇总。控制`ops-66b9496/s0_review01_control`、driver同ops下`s0_review01_driver.log`。不自动验收或归档，不开始S1。
5. 请求builder `S0_BUILD_CONNECTION_REQUEST_20261116.py`已部署，SHA `04665592cd0edcf63b828722e4f4d815b2dedef7cb1498eab514b94d7a8ad6c0`。连接session为`66包/runs/s0_unknown_connections01`，结果子目录`s0_unknown_s0`。不要手工再启动相同session。
6. 当前只读watcher233182命令保存在`local_runs/s0_followup_watch_command.txt`，源码`local_runs/s0_followup_watch.py`。观察export/review两组child进程及日志，review终态或失败时自然退出。向终端输入新shell前只退出这个前台watcher，不能中断后台父子或删锁。

后续依次：核对完整报告及连接/模型事实→写独立S0阶段结论→copy-only持久归档→开始P80。未知活动仍按实际PT策略报告，不给缺模型或未知值填零，不把布局前结果写成物理签核。

## 已部署工具、归档边界

`ops-review-e516e4c`的6个工具已核验导入，未执行归档：s0_model_review_snapshot、s0_archive_contract/runtime、n1_archive_runtime、t80_archive_runtime、transport_report_stage。调用时导入路径先ops再66包scripts；不要写入冻结bundle。模型工具只联结事实，不自动授予验收。

归档需等待所有上述父子结束，核进程/锁/空间；从**源runtime外的cwd**执行，日志也放源runtime外。新目标为既有团队backups下新`s0-runtime-YYYYMMDD_HHMM`目录，完整tar回读、前后哈希核对，**保留所有源文件**。不动桌面T80，不删旧八路。最近空间实读是23:52:16的/tmp约95GB、storage2约29.3GB，归档前须重查。

## 本地准备、历史失败与恢复提醒

- S1未改RTL/TB，`S1_PREPARATION_20261116.md`只记录已有8项描述符与新增2/4/8元信息队列的区别、原总线/信用/取消/观察器要求。xvlog仅检查版本，实际Vivado Simulator2018.3，未运行P80。
- 旧synth03/05/06/07及finish01/02失败全部保留，原因见`CONTEXT_CHECKPOINT_20261115_S0_FINAL_READY.md`历史；不能重启、删记录或借其PASS。
- `handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`是旧未跟踪启动器，不加入提交、不执行。
- 两个早先只读警告查询因Bash引号和过度转义无效；仅query03字符串前缀查询作为证据。原EDA作业/文件均未受影响。
- GUI：先`ac820.ps1 windows`确认新窗口，当前VNC18874435/workspace3；FileZilla关闭，workspace4不碰。板端relay91027保持。既有helper前缀授权持续；无隐藏服务器SSH/下载。
- 本地Python `E:/fpga_race-two/.venv-kwt/Scripts/python.exe -B`，Vivado `D:/Xilinx/Vivado/2018.3/bin`。不要把非ASCII Python经PowerShell stdin写入，中文文档用apply_patch。Git仅个人分支正常push，不强推。
