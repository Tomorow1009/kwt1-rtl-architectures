# G32最终网表验证恢复点（2026-11-17 13:12）

## 13:12补充：40b已启动，保留前检拒绝

39真实终态SHA已逐8字符读取并在服务器断言：`40c51722a13dba88fc0f0d2745436b13805488ca3e3a6405578026f1deff128b`。此前人工转录漏字符并把首段51写成15，40原脚本父33184在校验旧回执阶段退出、未创建输出目录，零新删除；40b第一次部署也在写文件前被SHA断言拒绝。原记录均保留，没有放松校验。

只修正正确旧回执SHA后，**40b父34816自13:11:45.383108运行**，源码SHA `7b116d68da0206df20b9028d796081eac7f7bd83505998d0c4ecc5903e4e367d`；实际服务器路径`ROOT/b0_recovery40b.py`，输出控制仍为新`ROOT/b0_archived_expected40`。39资料已写`G32_STORAGE_RECOVERY39_20261117.json`。迁移父32512最后13:10为`waiting_for_team_lock`，尚无删除。当前正在输入只读状态查询（exec64753），结束后看`takeover_local/g32_state1312.png`。不再发送任何40/40b或迁移启动命令。

## 13:08补充：39已结束，提前无损迁移解决持续满盘

39首次父29276在任何清理目录创建之前因38终态预期错误退出，零删除；实际38为`verified_duplicates_removed_archive_retained`。保留失败脚本/日志，新39b仅修正这个预期，SHA `5aa1074b1bd976018d994b7798846216d296ca294d7f1f701d58c5b3a34b92fc`，父30458自13:02:03启动，已移除32份4864624B完整归档重复参考。回执SHA `40c51722a13dba88fc0f0d2745436b13805488ca3e3a6405578026f1deff128b`，剩余88份13391630B。13:05共享空间再次1048576B，查询22550仍等待，不能重跑39。

因此调整后续顺序：**先提前执行已经核验暂存的R4 L04无损迁移，原G32查询仍不重启，共用原锁串行**。迁移唯一父32512于13:06:28.734541启动，工具/暂存身份不变；控制`/tmp/s4_21usr_r4_l04_xzmigrate01_20261117`，日志`/tmp/s4_21usr_g32_reviewops_20261117_0948/l04_migration01.log`。尚未读取其状态，不宣称已删源或腾出空间。原已准备`g32_start_l04_migration01_gui.txt`禁止再发送，实际已用`g32_start_l04_before_query_gui.txt`。

新有界恢复40只允许剩余88份已完整归档expected.npz，SHA `aa8ef67710a4c725c62113787c0f1dafad8bab27969bec271dcc3fb93bb1419e`，同样取得原锁即停止，不碰T80/旧八路/唯一结果。本地适配累计数和精确传输字节已核对，正在可见Linux VNC输入启动命令，exec会话90724；退出后先看`takeover_local/g32_rec40_launch.png`，不能重复发送。原export4543、query22550尚未重启；最终报告草稿`G32_STAGE_REPORT_20261117.md`已生成。下一步核对迁移/40/查询，仅当实际完成才安排最终归档和冻结。

## 13:02补充：导出连接查询在等待锁存储，准备有界恢复39

已重读计划与检查点。12:52:59和12:57:22的开发板Linux VNC截图显示：export父4543仍在、connections子22550仍在，日志反复`WAIT_INITIAL_SHARED_LOCK_STORAGE`；原锁不存在，shared仅1048576B，尚无`runs/g32_unknown_connections01`。这不是DC运行变慢，亦不能据导出状态误称已经开始连接查询。用户确认没有团队共享盘写入，不再重复询问。原队列、RTL、网表和报告均不重启或修改。

已准备独立`G32_B0_ARCHIVED_EXPECTED_RECOVERY39_20261117.py`，SHA `89ebc868d0faec06a2707f2993e37ccc98e70ca3b5a02f9f76dc268377a8bb47`。从完整持久B0备份清单扣除32～38全部已校验日志，只允许剩余120份18256254B中的最多32份生成expected.npz重复件；再次核验归档、文件SHA/大小、原等待请求/进程/日志及原锁，取得锁即停止，不改源码、结果摘要、日志、网表、活动、桌面T80或旧八路。适配逻辑与累计数量本地检查通过。新入口已通过可见Linux VNC逐段输入中（本机exec会话82130），尚未读取启动回执，不可重复发送。部署命令为`takeover_local/g32_start_recovery39_gui.txt`，不是重跑38。

完成输入后先等待会话退出、读取`takeover_local/g32_recovery39_launch.png`，再核对恢复39状态与原export进展。后续仍为：model snapshot事实审核→L04无损持久迁移→G32完整归档→冻结及五阶段对照。L04迁移和G32归档尚未启动；最终100条未授权。12:45数字保持有效。

## 12:45补充：完整功耗数字已核对，活动清单继续

G32报告已生成：`BUNDLE/runs/g32_report01/g32_report/report.json`，SHA **f95e15e701e08bf8cd0bb091307b93c3c71af71705a5a998f4a84bb2e8af0183**。12:41:51服务器断言了完整SHA、12层周期/长度/功耗、动态/泄漏加权值、能耗及finish终态。**finish正确SHA为24a7828e38fa4d387ffb0d2ed18e78495d57bed8e78e64c5a80dc436f1e5b414（64字符）**；先前本地漏一个f造成63字符转录，已纠正。导出启动器始终取实际服务器SHA，原终态不变。

- 全12均72179.33333333333周期，2078.1571825730357task/s，3370.804200648385MMAC/s。
- 加权功耗W **0.04278824864980673138202070768**；动态 **0.03588379622301803840434473395**，泄漏 **0.006904452681160974055362107344**；J/task **0.0000205895130213414919707**。与冻结C32-A相比功耗/能耗均−12.63036288109743%，完整周期不变。属于布局前数值，模型审阅尚未结束，不标阶段最终验收。
- 12层编码总309480B、均25790B，总384174事务；L12为31276B（不是人工初抄的31272）。总窗口5774346.089232ns。各层实际值与本地计算已断言，见`G32_POWER12_20261117.json`及`workspaces/arch03/reports/g32_20261117/fixed12_power.csv`。
- 自己的240均70929.40833333334周期，min64833/max81861，宿主2737.018175350968秒；固定12最差NRMSE0.1425636423408142%，与20条统计分开。

12:44:55.763750，export父4543为`collecting_existing_activity`，export子4745已退出，inventory子17744存活，未知清单目录已有10个gz文件但summary尚未生成（文件数不当通过层数）。不重启。后续连接查询/别名/snapshot由原export顺序执行。

当前本地正规`g32_icg_timing.py`已同步三处PT2022修复，字节SHA与实际恢复工具相同：`33c20a4c5a9d081a9d60e9ed9d57bda80da44081306630a9659499ed9bf1e57d`。服务器只读断言及5项既有工具测试通过；**服务器生产包、RTL和网表未修改**。提交1e0ef75已推。原失败及旧脚本仍在不可变运行包内，复现文档`G32_REPRODUCTION_20261117.md`说明差别。

没有活动GUI输入会话。准备的`takeover_local/g32_read_model_review_gui.txt`须snapshot实际存在后才发送；其余L04迁移和G32归档均未启动。报告page1/2已经读取，无需重复。下一步等待独立模型事实齐备，审核后迁移L04释放持久归档空间，再完成G32归档/冻结与全路线对照。当前数字不需要重跑PT。

## 12:21补充：原队列正常完成，报告导出已启动

finish01于12:19:05.607454完成全部17阶段，父277152和最后子3355均已退出、原锁释放。终态`reports_ready_review_required`，SHA `24a7828e38fa4d387ffb0d2ed18e78495d57bed8e78e64c5a80dc436f1e5b414`。自己的gate14/SAIF12/PT12全部完成，不能再启动finish。详见`G32_FINISH12_20261117.json`。

已发送原准备入口，**export_review01父4543自12:20:33.450364运行**。12:21:35.585434状态`exporting`，export子4745存活，尚无report.json，未知清单尚未开始。不要重启export。只读状态入口为本地`takeover_local/g32_review_status_gui.txt`，通过当前开发板Linux VNC输入；没有后台GUI输入会话。其余已准备的报告读取/L04迁移命令仍未发送。

最新已推72625ba，当前新增finish回执及README/checkpoint待本次进度提交。完成导出后先读取本版完整功耗/模型事实，独立审阅后才启动L04迁移及G32归档。原失败与历史运行保持不动。

## 12:16补充：功耗10层完成，面积分解已取回

12:15:58.549942，唯一父277152仍为running/power_layer_11，已完成structure/gate/saif/timing_audit/drc_audit及power_layer_01至10。当前子2275自12:15:45.942631运行，锁277152；共享盘1048576B，/tmp41976614912B。所有旧失败/恢复队列不重启。

`G32_AREA_BREAKDOWN_20261117.json`保存同网表叶实例分解：内部X/W宏0.2462886943mm²、阵列0.1108144296、核心响应/偏置/结果/控制0.1354008096、DMA及缓冲0.0404627496、编码器0.0218661576、实际383ICG0.0017115504；其余控制/仲裁及保守平台归属均计入，总0.7279723471。来源摘要及无重叠求和服务器断言通过。未达到0.50努力目标，满足1.00限制。

最新已推a5dc0ff。新增最终表生成器`handoff/team/evidence/BUILD_STAGE_COMPARISON_20261117.py`只读取已验收且归档的结论/冻结记录；前四阶段哈希连接已检查。G32尚缺最终结论/冻结，**现在不运行正式五版导出**。

已准备但未发送的可见Linux终端命令位于`E:/fpga_race-two/takeover_local/`：`g32_start_export01_gui.txt`（finish终态后），`g32_read_report_page1_gui.txt`/`page2`（导出完成后）、`g32_start_l04_migration01_gui.txt`（export和独立审阅完成后）。后者核对finish/export退出、原锁不存在、ops及暂存SHA，启动唯一L04无损迁移；目前未删L04源gzip。不存在活动GUI输入会话。不要提前启动归档或重做门级/活动。

## 11:58补充：SAIF全部完成，继续同一队列

`G32_GATE_SAIF12_20261117.json`记录自己的gate14/SAIF12服务器断言。SAIF摘要`19500ec93b08c9844f29552be3b000c0fe551337266514203a5e8c42902a6420`，12层304128输出、781461667B，全部实际窗口与自身门级完全一致。此前末段SHA人工转录错误导致只读断言拒绝，已纠正，服务器结果不变。

11:57:15原父277152为running/power_layer_03，completed含structure/gate/saif/timing_audit/drc_audit及power_layer_01/02。最后ledger子320075已退出0；当前队列未终态，不启动export。锁277152，shared1048576B、tmp42153918464B。两层功耗只是初值，不宣布节能。无活动GUI输入会话。

后续继续status03核查，finish完全结束后执行已准备export；其余恢复/归档入口见下文。下文11:35观察保留为历史，不当实时。

压缩恢复后先读AGENTS、团队README/SYNC、有效计划、本文件及STATUS的`c32_g32_20261115`。此前完整过程保留在`CONTEXT_CHECKPOINT_20261117_G32_RECOVERY.md`和`CONTEXT_HISTORY_20261117_G32_PRE0936.md`。不要依历史PID重启作业。

## 当前任务与不可改变范围

工程`E:/fpga_race-two/kwt1-c32-g32-20261115`；分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。

有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。路线S0→P80→C80→C32-A→可选C32-B→G32；前四阶段已冻结，C32-B本地吞吐下降0.0603109733%，未晋级。当前只完成G32，不恢复旧A、T64/G64、宽ICB等路线。

- 最终32PE，150MHz/6.666666ns，SS/0.99V/125°C，保守面积≤1.00mm²；0.50mm²是努力目标。
- 原32位ICB及平台缓冲参数不变；源读→真实共享写ACK→原总线实际读回→解码→计算→最后输出ACK排空。不得旁路或预加载下一任务。
- X14/W12/product26/acc32/b32/total33/result16，SHIFT10。正式只有前20条×12＝240任务、6082560输出及total；**新100条未授权**。
- **Desktop/T80_Delivery_20261113、全部旧八路、冻结S0/P80/C80/C32源码/运行/备份不改不移不删。** 用户已明确没有团队持续写共享盘；共享盘变化原因未知，不再询问或归咎队友。
- 同范围GitHub同步已授权；不强推、不提交凭据/厂商库/大产物。不要创建goal或新代理。不要以部分完成结束工作。

## 唯一运行中的队列

ROOT=`/tmp/s4_21usr_g32_20261117_0810`。
BUNDLE=`ROOT/light-light126-g32-0e16994`。
生产提交`0e16994675bb15e53642017a88f6307da9af4a01`。
manifest `3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a`（1059文件）。
payload `3c0a0f9156b6e40093bc5f9f5d91ae6cb5f95c207ba54e51bb2136a5bc44ab57`。

**g32_finish01父277152**，10:28:48.918079启动。外部request/launch/log位于ROOT同名前缀，状态`BUNDLE/runs/g32_finish01/state.json`。取得原协作锁后始终串行，生产包未修改。

**11:35:43.053960最后观察：running/saif，completed=[structure,gate]，error=None；门级14全过，SAIF L01–L09完整输出/窗口核验已过。L10子310691自11:34:40.739312运行。** 原锁277152，shared1048576B、/tmp42750861312B。不要重启队列；新的验证写/tmp，当前不依赖共享盘空闲。

只读入口：

```text
python3 -B /tmp/s4_21usr_g32_20261117_0810/status03.py
```

status03源码`handoff/team/evidence/G32_STATUS_FINAL_CURRENT_20261117.py`，SHA `8059697d01f58f8d75c485b9ab9d983d13eddb175d092693db1a0c3b906ce25e`，已核验部署。它显示finish/逐层gate及SAIF/PT数/空间。旧status02可用但冗长，status01仍指已失败旧队列，不使用。

当前队列顺序：structure→gate14→SAIF12→timing_audit→drc_audit→power_layer_01…12。门级每层约1分钟，SAIF本轮前几层约4分钟仿真+约1分钟活动核验；不能把仿真退出当窗口通过。PT和最终审阅仍未开始。无本地仿真运行，无GUI后台输入会话。

## 已完成G32证据

- 本地10000随机+32定向、317824输出，seed0x7834a9f1；C32/G32门控/G32静态旁路逐周期相同；本地14例、一/两拍SRAM、ABA/取消/恢复及27协议场景通过。见G32_LOCAL_VALIDATION_20261117.json，不重复。
- 自己的ASIC/E20314例354816输出及total、IRQ/WFI，CPU恢复/竞争通过。固定12周期 `[74750,73187,72186,72264,70798,69193,68427,68604,68610,70970,75393,81770]`，总866152，均72179.3333333333，名义150MHz **2078.157182573task/s**，每层与同数据C32-A相同。
- 新三块综合`runs/g32_initial01_synth/g32_synth`：summary `5f270c7366d5914b4fbe219862987e19314e7f6c24f90b00b8f963890a9c8a92`，netlist `f02759430cff876497e7158a5b570a7543553f066a58197a5eeca0546c6e02bb`。保守面积 **0.727972347099813mm²**，setup **+0.000433922ns**，hold **+0.00289777ns**；92小+128大=220宏、0非预期锁存器，约束明确无违反。实际383加速器ICG、10306寄存器时钟端点，array249/core70/transport64。
- 自己的ICG查询`runs/g32_recovery01_icg/g32_icg`，summary **2657d4a98c669d56ef62e2c5bb499d943dc15d3c0fe886ad1190251a476de0dd**。383个TE静态0，逐个setup/hold共766路径，最差+0.070571/+0.18723ns。原生无负裕量报告默认slack_lesser_than0，短报告并非无检查；完整383定义与766路径已独立核对。ROOT/g32_icg_native_review01.json SHA **add21a6f755ae86cc1496886ff16aa8c03ddbef2d521db02ee09c4dc3cc979c1**。全局禁用弧/模型仍随最终功耗审阅，不以局部检查代替系统结论。
- 自己的前20条240任务、**6082560输出及total零失败**，新FLOAT逐层最大NRMSE **0.20198143836753799%**、逐任务最大**0.20953408931848963%**，裁剪及饱和0。10:36对SHA/数值进行服务器机器断言。batch summary **0f8a57042e702dcc8b3c5db0ed322892863bad52c700a0937c41dc714dc83f59**，precision summary **ac2062b23d4f7656211122cc35336a86ceff5f3d0eb3eab369ef76326b69ab4a**。见G32_FIRST20_PRECISION_20261117.json。
- 自己的最终网表gate14全过，354816输出。summary `runs/g32_finish01_gate/g32_gate/summary.json` SHA **b76eaea9f59f8a7f23ce7132c85579844d8dc1773cc07c84051dc961ac77a793**。固定12周期同上，extremes57532、rounding56822；无SDF，门级total不可观测，total是ASIC证据。
- G32功耗目前尚无数值，不能套用C32或以ICG数量宣布节能。

## 原失败与恢复，不可重跑

原initial01父202586完成soc/sequence/contention/synth后，PT2022不支持pin的name属性而失败，原state SHA **de797dab25bccd50134556e363bb074ebe94a22650965495f4e9820cda9d4df5**。只在外部工具修正三处pin查询为full_name模式，网表/约束不变。原失败证据保持失败，不改成PASS。

新recovery01父245913自09:31:49运行icg/batch20/precision，**10:27:22.313638全部完成并退出**。终态SHA **59bfae25095530f60bd551f92e0bc97d5ebbe32b8224f2be14c79e125399d870**。明确连接原四阶段与恢复三阶段，19项工具合同测试通过。外部ops0922首次因JSON序列化误拒绝，未创建队列；修复只改身份核对方式，0933成功。不要调用旧成功initial入口或重复任何已经通过的硬件阶段。

## 后续工具已部署，等finish终态后继续

完成工具OPS=`/tmp/s4_21usr_g32_ops_20261117_0938`，manifest **f614bef8b387b3943914cd7cd7407934bac2ba47396be15f95e789d1b07d21d4**。

1. finish01完全终态`reports_ready_review_required`，父/全部子进程退出后，使用本地准备的`E:/fpga_race-two/takeover_local/g32_start_export01_gui.txt`。**尚未发送。** 它自动绑定实际finish终态SHA并核验已知recovery终态及ops清单，再后台启动`G32_EXPORT_RECOVERED_REVIEW01_20261117.py`。不使用旧ops0845启动器。
2. 导出控制ROOT/g32_export_review01，日志ROOT/g32_export_review01.log、进程ROOT/g32_export_review01_launch.json。顺序：report→完整SAIF未知活动12→本版映射连接DC查询（原锁）→alias→model_review_snapshot。状态`facts_joined_manual_conclusion_required`后独立审核全局无时钟、禁用弧、关键端点、宏模型、单位/活动；不修改原始自动false标志，不拿它代替独立结论。
3. 与冻结C32-A同12输入/编码/完整时窗比较，整机µJ/task必须降低、完整周期不能增加，面积≤1.00。若无收益按计划保留C32，不预判G32优胜。
4. 完整证据审核后安排下述L04持久迁移释放归档空间，之后迅速做G32完整持久归档，不清理旧8/T80。
5. 归档启动器已部署`/tmp/s4_21usr_g32_archiveops_20261117_1006/G32_ARCHIVE_RECOVERED01_20261117.py`；manifest **b38f1276e0920eb35906d19714f0dc0744effb416c82c149fcf156f49d106e26**，launcher SHA **784d130a8ff9bb0ef9b790088a703ba998c972b197bce8c4104bed5aae471542**。**尚未启动**。要求recovery/finish/report/export终态实际SHA及`--name g32-runtime-YYYYMMDD_HHMM-<suffix>`；采用copy_only_512MiB+20%余量，全成员回读、源保留。将5个外部操作目录及自身精确源码复制到ROOT/completed_operations_snapshot01并一并归档。运行日志/控制写ROOT之外/tmp目录，避免归档包含活动日志。归档进行时不要运行ROOT/status03制造打开文件观察冲突，改查独立归档控制目录。

## 空间处理与明确禁止重复动作

- 清理32～38全部结束，不重复。最近38父278712于10:32:23移除32份已由完整持久备份核验的B0生成expected.npz，共4866429B；state SHA **4337023c8976f16d9a83d09fa701a2bf507005b8ff882dd88ad15879c1fb24e3**已机器断言。还有120份18256254B未清。源码/网表/日志/活动/完整备份不改，不能借此删除其他路径。
- 当前原锁已取得，不需要为finish再清理。将来新的锁若因ENOSPC阻塞，先核实具体队列/锁/进程，只使用新的明确清单，不重跑38。
- R4 L03已完成持久XZ迁移，不再做。R4L01唯一gzip及其SAIF方法依赖保护。
- **R4 L04只完成/tmp暂存与只读完整前检，尚未迁移或删除源gzip。** 暂存`/tmp/s4_21usr_r4_l04_xzstage_20261117`，stage02父232887已退出，stage SHA **a0bcf091dd3899031dd350d4fe47e01a4a96d4b392945ac11285601b06ecd7af**。原gzip7649800109B完整精确副本保留；XZ2782976660B，已完整解压核验12564314076B原VCD的SHA。净可省4866823449B。
- 项目PROJECT=`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`。L04原路径`PROJECT/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02/layer_04.vcd.gz`，JSON保留。迁移目标`PROJECT/backups/r4-l04-xz-20261117`；控制`/tmp/s4_21usr_r4_l04_xzmigrate01_20261117`。
- 工具已部署`/tmp/s4_21usr_g32_reviewops_20261117_0948/G32_R4_L04_XZ_MIGRATE_20261117.py`，源SHA **3125e9b076130f0b0bdaa376abd7c80f8c27af85e48084b41c81cf7c0406331d**，ops manifest **df1007b0ad6852b1d9f47bc5d3599715f739fe816271cc07136fa64444f9917c**。默认只读，09:49只读完整前检已过；实际必须显式`--migrate --stage-sha256 <上面精确值>`，取得原锁，再核验原gzip和两个暂存完整副本、源戳和进程后仅删除这个重复gzip，复制XZ并再次完整解压回读，保留原gzip/tmp副本及RESTORE。没有实际迁移就不能声称共享空间已释放。
- 三个原桌面helper PID10519/79103/202972的FD不可见，身份已固定分类；限制明确保留，不宣称完整FD可见。5项进程/锁守卫测试已过。若出现未知受保护进程或已使用源文件，工具拒绝，不能绕过。

## C32-A冻结对照

tag **arch03-c32a-repair03-20261117-0725**，结论`handoff/team/evidence/C32_STAGE_CONCLUSION_20261117.json`，冻结`C32_FREEZE_20261117.json`。
RTL61246bb2a21c56a9bfd871fd68de93028d79f5fd，功能/FW91135f61c97c980039793c6637d0a06888638df0，修复操作58288044bfbbe344fafc7550647bfc5c29eef0a7。

bundle `/tmp/s4_21usr_c32_20261116_2010/light-light126-c32-repair-5828804`，manifest321c38f06fe155e491bcb580703eb5fdc96755f4bf4876d7c5545c6ae3b0dd07。
报告`runs/c32_report_repair03/c32_report/report.json` SHA **ea4b916db90117e1082565bd9dd78947098200dddd39de5a6d2c42d950ad3565**；netlist4f6e416402f2a178ec0ae0494fab1cddc53d7cf9113ac19990e108580b47c1dc。

固定12同866152总周期/2078.157182573task/s，保守面积**0.7224077334997787mm²**。功耗W **0.04897381980833410302117873075**，动态0.04208028354075208508437318161，泄漏0.006893535898086675317958048934；J/task **0.0000235659820737505569651**。总窗口5774346.089232ns。G32当前面积较其增加0.7702871027%，并不代表能耗增加。

C32持久备份`PROJECT/backups/c32-runtime-20261117_0709-repair03-copy01`，1572653883B，tar SHA30f111ef8b51cb7ab223cc50a35e7812be4a8f08c53fc54df9b51aea8b56b80f，receipt f707f20af9a8f98a615298481a81daddc57e5ebb9fc98999b22097f185310db9；全成员回读，源保留。此阶段不重跑。其它S0/P80/C80结果、编码路径和冻结索引已在各自STAGE_REPORT/FREEZE文档，最终对照必须使用完整四段口径，不能混入桌面旧T80计时值。

## 操作、同步与恢复纪律

仅使用`F:/linux_fpga_try/ac820.ps1`的已有开发板Linux X11/VNC路径，窗口18874435最近核实；先windows/截图再输入，第三工作区第一MateTerminal，不碰workspace4。不直接SSH比赛服务器，不绕过FTP公共地址守卫，不另建网络通道。每次GUI输入只开一个exec会话，等退出再看截图/下条命令；ASCII每段≤800字符，删除CR并保留结尾换行。现无后台输入。

10:26自动审批曾将此动作误判Windows终端自动化；读取ac820和board_link代码证明输入发生于开发板Linux X11，不是Windows应用。根据skill的非Windows适用范围，提交同一动作复审后获准。不得借此绕过其他拒绝。

本地Python `E:/fpga_race-two/.venv-kwt/Scripts/python.exe`3.8；服务器3.6，使用`.open(newline=...)`而非Path.write_text(newline=)。`git push`升级账号时需只对该精确工作区用命令级`-c safe.directory=E:/fpga_race-two/kwt1-c32-g32-20261115`，不用全局设置。

最近已推 **dc386a1**；本11:35进度保存后再同步。历史未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不是本轮，**不提交/执行**。压缩前更新根CONTEXT_HANDOFF与STATUS；恢复后重读计划与最新检查点，继续原队列。
