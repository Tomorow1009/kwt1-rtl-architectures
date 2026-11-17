# G32最终网表验证恢复点（2026-11-17 11:58）

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
