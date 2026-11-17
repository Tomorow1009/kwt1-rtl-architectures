# G32最终归档与冻结恢复点（2026-11-17 13:30）

## 当前目标

工程`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。

S0、P80、C80、C32-A已冻结；C32-B本地吞吐下降0.0603109733%，未晋级。**G32全部硬件验证、完整功耗及声明条件的模型审阅均完成，正在完整持久归档，下一步冻结、生成五版对照及同步。** 不重跑任何已完成硬件阶段，不创建goal或新代理，不以部分完成结束工作。

固定32PE、150MHz/6.666666ns、SS/0.99V/125°C、保守项目面积≤1.00mm²；0.50mm²仅努力目标。原32位ICB及平台缓冲参数不变；源读→真实共享写ACK→原总线实际读回→解码→计算→最后输出ACK排空。X14/W12/product26/acc32/b32/total33/result16，SHIFT10。正式批量为原前20条×12＝240任务。

**桌面T80_Delivery_20261113、全部旧八路以及冻结S0/P80/C80/C32源码/运行/备份不得修改、移动或删除。** 用户已说明没有团队持续写共享盘，不再重复询问或归咎队友。新验证全部在/tmp；数据清理仅限明确、完整持久备份核验的重复件。旧计划T64/G64、A广播版、宽ICB或旁路均不恢复。

13:30已按计划向用户异步询问是否追加完整100条（估计4–5小时），**尚未得到批准，不能自动运行**；继续当前20条范围的冻结和交付不需等待。

## 唯一活动作业：完整归档

ROOT=`/tmp/s4_21usr_g32_20261117_0810`；BUNDLE=`ROOT/light-light126-g32-0e16994`。

**归档期间禁止再从ROOT运行status03或打开源树文件**，避免影响源树使用检查。只能读取下面源树外控制目录及目标状态。

- 外层启动目录`/tmp/s4_21usr_g32_archive_dispatch01_20261117`，`launch.json`/`launch.log`。
- 启动父41479，13:26:58.467497；实际worker **41491**。
- 控制目录`/tmp/s4_21usr_g32_runtime_20261117_1326_final01`，`launch.json`/`request.json`/`archive.log`。
- 持久目标：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups/g32-runtime-20261117_1326-final01`。
- **13:28:36.674506最后观察：worker活着，目标state=copying，已写11,000成员/约474MB，shared剩2487222272B。** 没有失败；原文件保留，必须等全部成员回读及worker退出再冻结。不能重复启动。
- 本次实际GUI入口`takeover_local/g32_start_archive_reviewed_gui.txt`。最初两处人工哈希多字符被前置断言拒绝、未创建归档目录；分段读取纠正后13:26:58全部模型/迁移事实断言通过，再首次启动。原回执未修改。
- 外部归档工具`/tmp/s4_21usr_g32_archiveops_20261117_1006/G32_ARCHIVE_RECOVERED01_20261117.py`，manifest `b38f1276e0920eb35906d19714f0dc0744effb416c82c149fcf156f49d106e26`。copy_only_512MiB+20%余量，精确外部操作源码快照并入ROOT，逐成员回读，源保留。没有任意目录重定位验收声明。

## G32结果和身份

- 生产提交`0e16994675bb15e53642017a88f6307da9af4a01`；manifest `3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a`，1059文件；payload `3c0a0f9156b6e40093bc5f9f5d91ae6cb5f95c207ba54e51bb2136a5bc44ab57`。
- 最终网表`f02759430cff876497e7158a5b570a7543553f066a58197a5eeca0546c6e02bb`。
- 报告`BUNDLE/runs/g32_report01/g32_report/report.json`，SHA `f95e15e701e08bf8cd0bb091307b93c3c71af71705a5a998f4a84bb2e8af0183`。
- 固定12：总866152周期，均72179.33333333333，2078.1571825730357task/s；均编码25790B，总384174事务，窗口5774346.089232ns。与C32-A逐层周期相同。
- 整机加权功耗W `0.04278824864980673138202070768`，动态 `0.03588379622301803840434473395`、泄漏 `0.006904452681160974055362107344`；J/task `0.0000205895130213414919707`。相对C32-A功耗/能耗下降12.63036288109743%。报告分量存在末位四舍五入差，不强行改写。
- 保守项目面积0.727972347099813mm²，已知新增0.5672276958999081，整机4.250188847065895；0.50目标未达到。92内部小宏+128复用大宏=220；非预期锁存器0、约束违反0。
- 普通setup +0.000433922ns、hold +0.00289777ns；383实际ICG覆盖10306寄存器时钟端点，逐个766检查最差+0.070571/+0.18723ns，TE静态0。保持控制/valid/信用/IRQ/响应运行。
- 本地10000随机+32定向，317824输出，seed0x7834a9f1；C32/G32门控/静态旁路逐周期一致。自身ASIC14、恢复、竞争通过。自身240任务6082560输出和total零失败；同网表gate14 354816输出无SDF、SAIF12/PT12通过。
- 20条NRMSE逐层最大0.20198143836753799%，逐任务最大0.20953408931848963%；固定12最大0.1425636423408142%，裁剪/饱和0。官方600、SDF及物理签核不声明。
- 被动计数：有效MAC利用率70.2251%、0.443541事务/拍，元信息峰值2；源/共享写/共享读/输出各平均响应3.017/3.682/4.300/3.043拍。均供数空拍18654.25，首项等待2288.0833，普通块间隔81.2849，换tile间隔404.1944，尾部16+22拍。结果槽及结果反压0；等待重叠不能相加。

本地证据：`G32_POWER12_20261117.json`、`G32_AREA_BREAKDOWN_20261117.json`、`G32_PASSIVE_METRICS12_20261117.json`、`G32_FIRST20_PRECISION_20261117.json`、`G32_GATE_SAIF12_20261117.json`、`G32_ICG_RECOVERY01_20261117.json`。报告草稿`workspaces/arch03/G32_STAGE_REPORT_20261117.md`，复现说明`G32_REPRODUCTION_20261117.md`。

## 模型审阅已经完成

原export父4543于13:17:27.240974完成`facts_joined_manual_conclusion_required`，全部子进程退出。只读事实审核通过，原自动false标志保留，最终独立结论另存。

- 快照SHA `22a09d087d2528b5df267dadf1c660ddd24e7835158b71ee0e2f91cfcc1d9cec`。
- export终态SHA `cce0dca85a27d407dca9789eeb61d5969414183f5b6ee72f87136ef0a841c2ef`。
- inventory SHA `6917669ec3d9863c5046f767374c8a0b4d93447f02d1bc3f2c5f80762e858be3`。
- connections SHA `90fb11107c78f1afcfb93e2b648f1a5dd82462fdc2902880c1d5e4739c947d3f`。
- 41175目标，38512解析、2663未映射名称全部分类：2199 absent、313 dummy、151 wirealias；62326叶端点，未知显式clock/reset/ICG/SRAM控制端点0。
- 12层时序表相同，无时钟仅static JTAG DTM186+reset sync3；禁用弧C67628/c6098/d250/p35139，无用户/环/false类别。PT时钟6.666666/66ns，JTAG TCK/TMS/TDI静态0。
- 未豁免全部未知状态或驱动内部功耗；保留averaged PT、X-transition derate0.5、initial-X除外及X/Z驻留信息。仅为稳定任务模式、布局前模型估算，不是物理误差保证。
- 全部上述身份/数值及L04迁移哈希在13:26:58.382457服务器断言通过。本地`G32_MODEL_REVIEW_20261117.json`已经记录。

## 存储恢复已完成，不重复

旧共享盘满使query22550等锁存储；39b删除32份4864624B、40b删除剩88份13391630B，全部是已完整持久备份B0 generated expected.npz重复件。**清理32～40均结束，不重复。** 完整B0备份、源码、摘要、日志、活动、T80、旧8及冻结阶段未改。失败前检均零删除；见RECOVERY39/40记录。

40回执SHA `4a551cc20f663b20fae846ba4407804c019c3e95cb50f8f7f30a7201d3bcbe8f`已在服务器断言；该旧重复件集合剩余0。39回执正确SHA `40c51722a13dba88fc0f0d2745436b13805488ca3e3a6405578026f1deff128b`；不要抄旧错误的40c15722或63字符版本。

R4 L04提前持久迁移父32512于13:15:59.474301完成，精确gzip副本仍在`/tmp/s4_21usr_r4_l04_xzstage_20261117/original_layer_04.vcd.gz`。持久目录`PROJECT/backups/r4-l04-xz-20261117`，XZ2782976660B，完整解压12564314076B通过，净省4866823449B；原JSON不改，仅核验后的重复gzip删除。

- receipt/state SHA `c6962b18892f8bd0b3561224c2e8219ebbd2e791305e90a797a502fb7593d053`。
- XZ SHA `1ee91497eba8d78848e6a8dc9a21acca3d83ca688d6ea6df71f15fdb89489674`。
- 原VCD SHA `dbff10b7edea7cdb0120b50944f67d1522b2a92dec7a63e81153dee51e5cf92c`。
- `G32_R4_L04_DURABLE_XZ_20261117.json`。不要重跑迁移，R4 L03也已持久归档，不重做；R4L01唯一gzip不得删。

## 待完成动作

1. 只从归档外控制/目标查原worker41491，等`verified_copy`及退出。读取receipt、manifest、全成员数量、总字节、SHA及源保持/全部回读。保留失败并排查，不重启同名归档。
2. 保存`G32_ARCHIVE_20261117.json`、独立`G32_STAGE_CONCLUSION_20261117.json`与`G32_FREEZE_20261117.json`。参照C32记录结构，使用本版所有证据；G32布局0x00100006、numeric0x000e0c20、ID0x4b57530f、capability0x000d02bf。最终tag可用`arch03-g32-final-20261117`，未创建。
3. `handoff/team/evidence/BUILD_STAGE_COMPARISON_20261117.py --output <新目录>`只在五版conclusion/freeze哈希均完整且归档回读通过后运行。生成JSON/CSV及中文对照、更新G32报告/ABI/README/验收表/STATUS/根交接，检查后提交推送及tag。
4. 所有比较用S0统一完整四段计时，不用桌面旧T80不同边界。G32相对S0吞吐+55.95738%、面积−23.65439%、功耗−14.83294%、能耗−45.39081%。整体路线收益，不全部归因门控。
5. 不自动运行100条；等待当前异步问题答复。若未答，完成授权的20条冻结与交付即可。

## 已尝试路径与不可重启队列

原initial01完成soc/sequence/contention/synth后，在PT2022 pin name查询失败，原state `de797dab25bccd50134556e363bb074ebe94a22650965495f4e9820cda9d4df5`保留。外部三处改为full_name后recovery01完成icg/batch20/precision，终态 `59bfae25095530f60bd551f92e0bc97d5ebbe32b8224f2be14c79e125399d870`。finish01于12:19:05完成17阶段，终态 **`24a7828e38fa4d387ffb0d2ed18e78495d57bed8e78e64c5a80dc436f1e5b414`**。全部已退出，绝不能重跑。

Git正规`g32_icg_timing.py`提交1e0ef75已与实际成功外部工具字节相同，SHA `33c20a4c5a9d081a9d60e9ed9d57bda80da44081306630a9659499ed9bf1e57d`，5项既有测试通过；服务器生产包没改。局部脚本查询修复不是RTL变更，不用重跑硬件。

更早历史与全部失败分支见`CONTEXT_CHECKPOINT_20261117_G32_FINAL.md`、`CONTEXT_CHECKPOINT_20261117_G32_RECOVERY.md`。C32只使用repair03最终记录，旧326 transition违反及旧功耗保持失败；C32最后只做6个同库等价驱动修复，不宣称冷启动重新综合。

## 操作与同步

只使用`F:/linux_fpga_try/ac820.ps1`已有开发板Linux X11 VNC；当前18874435，workspace3第一MateTerminal，**不碰workspace4**。先windows/截图确认；单个GUI输入会话，ASCII≤800字符分段，去CR保留结尾换行。截图有时早于终端结果，看到提示符才输入下一条。不要直接SSH服务器或绕过FileZilla公共地址守卫。

当前无待完成GUI输入会话。最新截图`takeover_local/g32_archive_state1329.png`（实际13:28:36）。归档时只监控外控制，别运行ROOT/status03。

本地Python`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`3.8，服务器3.6。中文通过apply_patch，不能PS管道编码写中文。当前最新已推`9d32b19`，其后新增模型、迁移、被动统计、恢复40回执及报告更新待本次同步。未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不是本轮，**不执行/不暂存**。

同范围私人GitHub同步已授权。推送用命令级`git -c safe.directory=E:/fpga_race-two/kwt1-c32-g32-20261115 push origin codex/light-light126/t80-pipeline-c32-g32-20261115`，不改全局safe.directory、不强推，不提交凭据/库/大产物。压缩前更新本文件及CONTEXT_HANDOFF；恢复重读计划、AGENTS和此检查点，按当前状态完成收尾。
