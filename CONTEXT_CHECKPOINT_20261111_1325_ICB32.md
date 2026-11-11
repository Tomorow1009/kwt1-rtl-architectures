# 2026-11-11 13:25：R4最终报告已通过独立重审

压缩后先读AGENTS、当前`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点和STATUS/EXECUTION_CHECKPOINT的`icb32_c64_execution`。用户要求继续推进，不逐步等待；本轮不改变R4硬件。全部历史见12:40检查点及13:00增量、11:20检查点。

## 已完成

- R4真实ASIC/E203最终1200任务、30412800输出、零失败，一次编译；12:51断言摘要同时匹配原stage/queue。整批均值34618.743333周期，min34555/max34883，150MHz折算4332.9129task/s。
- 最终锁内报告**13:19:23.854688正常完成**。13:20实际进程均退出、共享锁不存在；13:21核验全部四个工件哈希和wrapper的own_lock_released；13:23再次独立断言报告/回执转录哈希。完整1200回执/输出重审为passed_reaudited，不是新仿真。
- 报告输出：964包`runs/icb32_r4_final_report01`中的`report.json`、`tasks.csv`、`summary.csv`、`report_zh.md`、`receipt.json`。操作状态/日志仍为`runs/icb32_r4_export01`。wrapper121468/child121471已结束，不能重启。
- report SHA `e4a2514b7f47440a7ed0049aa685bdc36fc17180d4b9e3e256d5cd8998fa6958`；receipt SHA `2e54dc4378b1d59ee13ba236eb4b3093daa44d2a8a769830201fa295d94d004d`。
- 正式汇总采用964的干净ASIC14（摘要bb0ee4cf…），同e65综合/497门级身份绑定。12层及1200任务的被动计数全部收齐。报告均值34616周期/4333.2562977task/s，功耗0.07181263185379159926045759187W，能耗0.0000165724387710949571661J/task；十二层与1200统计不混用。
- 最终证据保存`handoff/team/evidence/ICB32_FINAL_EXPORT_20261111.json`。raw导出器的timing/area/power标志原样false；独立ICB32_SCOPED_REVIEW只接受稳定任务模式综合时序和项目保守面积。系统功耗未知影响、官方600、物理签核仍未验。
- 本地原964源码ZIP再次逐636输入核验，大小11139802，SHA18cf4c4def9fcab43174de974c6ca45851af35b6ac1ea701915bd8c57b41b161。新增清晰入口`workspaces/arch03/ICB32_DELIVERY_20261111.md`，72个当前文档链接已核；旧状态的第六层功耗转录已纠正为71.4346394mW，历史错值在功耗记录明确说明。
- 新`handoff/team/package_icb32_delivery.py`准备复用原样964ZIP和已提交说明/小型证据生成团队交付准备包。语法已检查；**尚未实际运行**，需先提交材料再运行，脚本拒绝脏工作树及缺最终回执。它不重新构建硬件、不包含服务器大产物、不代替正式赛事提交。

## 下一步，不重复已有作业

1. 检查本轮文档、最终证据，提交并同步已授权私人分支；运行新的delivery打包器，实际读回归档并记录SHA。服务器工件仍留原目录，不能开隐藏回传通道。
2. 按当前计划补R1同搬运对照。已告知用户在R4最终报告完成后串行推进，用于把本地3.359倍对照补成真实ASIC/PPA证据；不改变R4、不重复R4最终1200。
3. R1包`light-light126-icb32-r1-20261111_012941-f95e940862ca`已于**13:19:03.582673**重新核验607文件，manifest SHA `109e3314f54d0baed2584c15cb3449957057ac99c6b526d673bd39d9b62a013f`；IRQ firmware SHA `e29565e6c823d5115388c556159c6ff65d3ffe24b946198cf1068e13751e2bc9`，row_lanes=1，prefetch=1。全部RTL和964一致，差异为行数固件。实际runs=[]，新session可用。**还没有启动任何R1 EDA/仿真。**
4. 本机`takeover_local/icb32_r1_compare_launch.txt`已准备但未执行。它只在R4报告完成/自锁释放且实际teamlock不存在时，启动R1实际ASIC14，session`icb32_r1_compare01`，独立launch.log。启动后读取实际PID/state，等待ASIC14通过才运行综合；不要把launch本身当PASS。不要用R4 finalize队列给R1重复1200；R1是对照，当前先做ASIC14/综合再决定同网表活动功耗。

## 当前桌面及工具

开发板VNC窗口已重新inventory确认20971587，800×450，第三终端shell；cwd仍964包。FileZilla关闭，无传输，无CUA会话。只有板端Linux helper `F:/linux_fpga_try/ac820.ps1`；恢复先windows检查，不用旧坐标盲点，不通过SSH回传。type每条文本≤1000，成功后Return并等5秒截图。禁止Up+Return历史重放。

最后输入`icb32_export_hash_groups.txt`只读分组哈希。summary.csv第一次人工转录多了一个字符，本地长度断言在写文件前拦下；重新分组读取，正确64位为`f771c04c8cedfe4fb359fae8f3f979941aa2d57e3f81f43027c8712382d55e68`。服务器原报告未出错、未修改、未重跑。

服务器包目录前缀：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。964=`light-light126-icb32-r4-20261111_043048-96443c284a1c`，e65=`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`，497=`light-light126-icb32-r4-20261111_011258-49759e108719`。共享锁在Desktop/IC/.arch02_team_lock，绝不手工清锁。

云端上次独立确认d664d14b742c85dfac31c2e18529e9c33b336975。本轮最终导出证据、当前材料修订和交付打包器尚待提交/推送。源码/小摘要同范围同步授权持续有效，不上传库、凭据、聊天原文或大产物。

原fcd664task/s保底和完整回执保持；当前R4未达5000但功能、同网表门级、声明任务时序及面积上界已具证据。剩余系统功耗未知活动影响、R1/旧8完整PPA、正式赛事入口/文件限制/署名与提交收尾。冻结11/11 18:00、交付准备11/12 17:16、用户截止11/13晚上不变。继续能做的工作，不以进度报告结束本轮。

## 13:30增量：交付包已生成，R1已经启动

- 最终证据、交付说明和打包器已提交并独立确认云端`928559fea8ab8d01636ad1dbac2060f1f2be7025`。打包器已实际运行成功：`local_runs/icb32-r4-delivery-preparation-20261111_132750-928559fea8ab.zip`，11519662字节，117文件，SHA`dcbd8ef42ff293d44f92654772f7b394fcbce52528b51002eef72ee813abd289`。原636输入再核，归档逐文件读回通过；不需为了新运行记录重做此R4快照。小回执见`ICB32_DELIVERY_PACKAGE_20261111.json`。不是官方提交，服务器大产物未装入ZIP。
- **R1 launch已执行一次，成功PID187418。** 13:30:09.236138实际state为icb32_soc running、started13:29:07.205308、errorNone、捕获0（编译阶段），锁PID/session/bundle完全匹配。`icb32_r1_compare01`是独立R1 session；禁止重复launch。当前没有其他本项目服务器作业。
- 下一步用`takeover_local/icb32_r1_compare_status.txt`读取原状态，实际ASIC14通过后读摘要/逐例窗口/IRQ并绑定SHA，再启动同session尚未执行的icb32_synth。尚无R1综合或gate/power。R1是对照，不重复1200；不要调用包含final1200的R4 finalize队列。
- VNC仍20971587/第三终端shell/cwd964，最后命令是R1状态查询，FileZilla关闭。全部新R1进程/哈希与交付包回执已落本地记录，本增量待同步。

## 13:39增量：R1实际ASIC14通过，综合运行，先测活动体积

- R1 ASIC14已13:33:02.951083自然通过，354816输出、真实ASIC/E203、无全局FPGA、IRQ/WFI全部通过。13:35:23.168106摘要SHA与stage断言一致：`1980d8eb8ead959d0a3ec099f0fb3d4461924210abf6a785b60a85fac67286f6`。12层均值116280周期，与本地相同；同通路R4加速3.359140倍现有真实CPU证据。14周期已存ICB32_R1_SERVER_20261111.json。
- **synth_launch已执行一次成功。** R1同独立session icb32_r1_compare01，综合PID203950，started13:36:24.382957；13:39:18.034372实际synth running/errorNone，锁PID/session/bundle匹配。原ASIC187418已结束，禁止重复ASIC或synth。
- 13:37:28实际剩余磁盘135.405GiB；R4的12份VCD共139.178GiB、最大12.333GiB。完整门级总阶段5.36h不能简单按芯片周期推R1宿主耗时；R4单例仿真约202–299秒，其他时间含扫描/导出。**R1综合通过后先运行layer_01门级/活动试测，在容量/耗时明确后决定全12安排；不得盲启完整12活动，不删除/挪走历史证据。** 此探测只读stat/summary。R1门级尚未启动，也未准备launch文件。
- 已执行`icb32_r1_asic_verify.txt`、`icb32_r1_synth_launch.txt`。`icb32_r1_compare_status.txt`已改为读取实际case_progress；当前VNC最后为该status，仍shell/cwd964。
- 云端最新独立确认为`a0c241ba586333b7ebb0f274e0350fafe567ee34`（交付包与R1启动信息）；本增量、R1 ASIC PASS/综合/预算待同步。本机一次utf8-sig编码名拼写和一次PowerShell管道编码错误均在写文件前被拦下，改正/改用文件编辑继续；无服务器作业失败。
