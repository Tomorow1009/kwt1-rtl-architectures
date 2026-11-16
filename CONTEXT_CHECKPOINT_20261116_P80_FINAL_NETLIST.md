# P80最终网表验收继续入口

更新：2026-11-16 11:38（北京时间）。恢复时先读AGENTS.md、当前计划、本文件及根交接；下列远端状态仅对应观察时间。

## 11:38最新：报告、12层清单完成，原连接核对中

11:37:13.879623原watcher显示export96154进入`querying_own_mapped_connections`、无错误。原18阶段仍为`reports_ready_review_required`，父95253已经退出，不重启。原报告子205116已结束；后续清单子225367在11:29:03实读第8层、99.7%CPU，随后完整清单完成，原流程自然启动同网表连接查询。后续别名、模型快照及独立结论/归档待完成，P80未冻结。

报告`1023646/runs/p80_report05/p80_report/report.json` SHA **a5821699ef4551bfdfb485c7c3b9bae3e07f0fb0b27ca984ed58f3d0a6ace5ce**；固件SHA **29441cd52dacccde21f84a6cb165f52233eb51ed9e1a49f89508a50458a31069**。11:32:23服务器断言与本地转录相同。固定12新浮点最大NRMSE0.1425636423408142%；12层活动源表完全一致，374206直接映射/1273独立孤立默认/375479总计/0未注释；SRAM合同为60X＋32W＋128复用。PT averaged、X系数0.5、排除初始X，单位ns/V/pF；详见P80_REPORT_MODEL_OBSERVATION_20261116.json。这些事实尚不替代独立连接及功耗结论。

**当前第一标签watcher178083前台，第二Bash空闲，全部输入会话结束。**watcher约11:43自然退出，只是观察器；不要由此重启EDA或export。VNC18874435/workspace3；FileZilla未打开。最后确认push293d4a9，后续文件待同步。只复制归档启动器与transfer文本仍未部署或运行，等原export完成退出后先刷新空间。无新增服务器删除，cleanup13仍不需要；T80桌面、旧八路及源包未改。

C80仍仅软件准备：新增`c80_data.py`、`test_c80_data.py`及`C80_CODEC_FORMAT_20261116.md`；压缩/raw、数值参考、来源及新旧格式拒绝三组测试通过，Python3.6语法通过。本地14例源为旧N1包0f62e412的validated_data，manifest SHA 1c55d5515de4258c77537e52387809ea04a33a334a4fefee8e2600ec2b7209e0；自己重新计算total/result/saturated并编码到`local_runs/c80_fixed14_software_20261116_1135`，354816参考输出零差异，41.859秒，33556已结束。新manifest SHA **7ca8bc59ac04fa41fef61576da430c6a2150cabca54250fb7fa812719044cf07**。固定12编码平均25790B，不混用first20的25075.65B。

11:36:23.197221原服务器P80包142fae2的70个实际源文件逐项匹配manifest，路径＋SHA链**75b233b5fefce53feeac39fb2f61af70bbacfe96c05641df63e1b9af859790bd**与本地适配输入相同。原软件生成manifest中的join=false为较早快照，另存C80_FIXED14_SOFTWARE_PREPARATION_20261116.json记录成功连接，不改旧回执。没有C80 RTL、固件、服务器硬件验证或阶段PASS。

本次恢复只读STATUS时PowerShell默认ConvertFrom-Json因C/c键大小写冲突拒绝，已用-AsHashtable/原Python读取；Windows rg通配路径及一个不存在p80_data.py读取失败均仅本地只读，不影响文件或运行。所有修改通过独立新增工具/文档完成，旧运行包未动。

## 11:09最新：P80功耗12全部生成，原导出运行

11:00原18阶段队列自然到达`reports_ready_review_required`；11:04:54.732922确认父95253已退出，原export96154为`exporting`、子205116运行。队列最终state SHA `7302a8de8565e23f62eeec8a68015e92577bf50e36c634aae4bc2ff354b0c8ea`。不要重启旧队列或后继；仍需完整导出、未知/模型事实、独立结论及持久复制归档，P80尚未冻结。

11:06:44.535472完整12层独立只读汇总：平均功耗 **0.05377585129193407297236885091 W**、单任务 **0.00002780043931140106863325 J**；时间加权动态0.04660252608160091301432280472W、泄漏0.007173325295331354562492477519W，保留PT分量打印精度。总时间0.006203626046304秒、总能量0.0003336052717368128235990J。每层摘要SHA、同综合/SAIF来源及J=P×t均核对；本地转录12行规范JSON哈希`a14a376ecf00c813a91810c486119af3ce19978a26a84b73a2158db9d8df4141`由服务器断言匹配。原始摘录见`P80_POWER12_OBSERVATION_20261116.json`。数字不是独立模型验收，官方600/物理签核不声称。

**当前第二标签Bash空闲，第一标签watcher178083保持（约11:43上限）；全部输入会话已结束，最近55193。** 一次长查询在键入前被工具“最多1000字符”拒绝，未发送Enter，随后按900字符分段输入成功。注意上限是每次type总字符，不只是每行；后续copy transfer同样必须分段。`local_runs/p80_read_finish05_numbers.py`只读脚本及截图保留。

只复制归档启动器`P80_COPY_ONLY_LAUNCH_20261116.py`和`local_runs/p80_copy_only_transfer_20261116.txt`已准备但**未部署/执行**，启动器SHA `8fea98f6fc94beba0541039659bb6fadb72517cab505876389339a5bd63f403f`。必须等原export事实完成且退出后再运行；它在源外建请求/log、新目标backups/p80-runtime时间目录，调用原包已有工具，保留源和全部历史。共享空间最近55GB，启动前刷新，不执行cleanup13。

C80仅软件：新增`c80_codec.py`，暂定MAGIC KWC5/版本00050000/布局00100006，拒绝旧P80和实验C80P头；最终RTL/格式尚未冻结。240份独立新头文件`local_runs/c80_host_format_first20_20261116_1102`只改32B头，载荷及总长与筛选完全一致，内部恢复规范流SHA逐项相同。manifest SHA `06bad2009ccca242f037f7548909e0ac4e606254ccbeee2a0e4e49d43bc8289e`；2组新头/互拒绝/偏置/raw测试和Python3.6语法通过，28222已结束。准备脚本`local_runs/c80_reheader_first20_20261116.py`、回执及说明保留；不是C80硬件PASS，没有上传或EDA。

最后确认push e014eef；本节、功耗摘录及主机格式待随后同步。桌面T80、旧八路和原受测包均未改；服务器本轮未新增删除。

## 10:42最新：PT6/12完成，原队列第7层

10:40:40.456276第一标签watcher178083显示running/power_layer_07、error=None，PT6层完成，export96154仍waiting_original_finish。原95253及锁不变。**第一标签watcher前台，第二标签Bash空闲，所有输入和本地57622模型运行均已结束。**剩余PT6层、导出/未知模型事实、独立结论及持久归档冻结；没有新增EDA、服务器删除或修改T80/旧八路。

10:28:48自身最终DDC查询：约束明确无违反、完整解析、无未解析驱动；1000阈值高扇出为core_csr_clk、hfclk及crossing_clock三个时钟网。数字/摘要SHA见`P80_TIMING_DRC_OBSERVATION_20261116.json`。10:33:13读取L01功耗为0.0536131226W、0.0000287620077154296075036J，窗口536473.279686ns；完整十二层汇总仍待，不能用首层替代。L01活动直接374206、孤立默认1273、未注释0，SRAM220（加速器92/ITCM32/DTCM32/共享64），后续全层/未知影响审核保持。

本地准备`P80_COPY_ONLY_LAUNCH_20261116.py`，要求原queue/export自然完成退出且哈希一致，才在源目录外启动已有严格复制归档器；不清锁、不删除源、目标为既有backups下新的p80-runtime目录。Python3.6语法、完整终态前置接受以及运行中export/变更report拒绝检查通过。**尚未部署或执行**，恢复空间后不需要cleanup13。

C80仅软件：新增`c80_codec_profile.py`，对原240份候选文件做单元素/128bit reservoir供数预算。完整bit及每任务23488内部半字计数一致；无限输出接收下，1拍/7拍输入周期对应平均23740.2833/43879.6375模型周期，后者输入反压0。这不是RTL或整机周期，不能成为验收；源文件不变、C80硬件未开始。完整本地输出`local_runs/c80_scalar_budget_20261116_1040.json` SHA `bf48db2906794f9b9a16c56feac0a28132f4840c5aa65bf0ad5a338662390a04`，小型摘要及实现说明已写。

最近本地41f93c9，最后确认push558b606，本节后继续同步。之前一次多文件补丁匹配失败为原子拒绝，未改文件，已按完整行重试成功；没有运行包影响。

## 10:26最新：完整活动12层通过，原队列进入PT第2层

10:20:59.304502原队列running/power_layer_01、error=None；自身SAIF12摘要SHA `83af4dca794d3884e76455bbda53bc86462a7d11e9ea0e49def03d3cacf4f8c4`。实读总计12任务、304128输出、930544周期、1171998648字节活动、6203626.046304ns；全部scope/duration/residence通过，原网表未改，没有新VCD。完整摘录见`P80_SAIF12_COMPLETION_20261116.json`。timing_audit及drc_audit已产出诊断，尚不等于独立时序结论。

10:25:09.603132第一标签原watcher178083显示running/power_layer_02、error=None，第一层功耗分析已完成；export96154仍waiting_original_finish。父95253、原锁及运行包保持，没有新增EDA。**当前第一标签watcher178083前台，第二标签Bash空闲；此前10:21查询已完成且提示符确认，全部输入结束。**最后确认push8bc21f4。

共享盘最新实读仍09:57约55GB，没有新清理，cleanup13仍未执行且当前不需要。剩余PT11层、导出/模型事实、独立审核和持久归档冻结。C80只有离线软件准备，未进入C80硬件；T80桌面及旧八路保持原样。

## 10:13最新：活动11/12，新只读watcher178083

10:13:08.858196：原95253队列running/saif、error=None，SAIF11，precision/structure/gate完成；原export96154状态waiting_original_finish。原watcher151016已按时退出，Bash提示符确认后新进程先断言`/proc/151016`不存在，再启动只读watcher**178083**（10:13:08.856093）。它每30秒读取原队列和export状态，最长90分钟，导出完成/失败时退出；不派发任何EDA。

**前台第一标签watcher178083，第二标签Bash空闲，输入全部结束（最近83118）**。不要依据下方旧watcher151016记录键入；恢复先新截图。原正式队列没有中断、重启或改文件，桌面T80及旧八路不动。本地最新af77e94（10层检查点）尚未push，最后确认push6e5fa30；本节后统一同步。

剩余最后一层活动、详细STA/DRC、PT12、export/模型审核与持久归档。共享盘最近09:57约55GB可用，不执行不必要清理。C80仅离线软件准备已完成并同源核对，C80 RTL/C32/G32均未开始；P80仍未冻结。

## 10:10当前：活动10/12，原观察器即将自然到时

10:09:24原watcher显示running/saif、error=None、SAIF10，已完成precision/structure/gate；当前具体子PID未重查，不继续把旧layer09的169613当作实时子进程。**前台第一标签watcher151016，第二标签Bash空闲，所有输入结束**。观察器按原约定约10:11:54自然到时，退出不代表原EDA父95253或export96154结束；确认提示符再建立只读观察，不向尚运行的watcher键入。

最新已push `6e5fa30`。共享空间最近09:57实读约55GB，cleanup13不需要且仍未部署/执行；任何归档前再刷新空间。本轮没有服务器删除、修改桌面T80或旧八路。剩余活动2、详细STA/DRC、PT12/模型审核、独立结论及持久归档；P80未冻结。C80只有已同步的离线软件及同批240源哈希连接，RTL/C32/G32均未开始。

## 09:58最新：活动8/12，共享空间恢复约55GB

09:57:53.931341只读核对：原95253队列running/saif；L01～L08已完成。L08为74101周期/25344输出，活动SHA `fd246ded9406b9e04679d8ef796f768d2e1f7bc02cd916d65ef6d26d330fd14a`。**第9层子169613**于09:54:17.182830启动。原export96154继续等待，没有新增EDA作业。

当前tmp可用87053959168B，共享盘可用**55034511360B**；剩余4层活动预算2617662920B。共享空间已由外部变化恢复，**本轮未删除任何服务器文件**。cleanup13仍未部署/执行，目前不需要使用；后续持久归档先刷新空间，不因旧记录“只有1MiB”而执行不必要清理。B0备份、桌面T80及旧八路保持原样。

**前台第二标签Bash空闲，第一标签只读watcher151016保持**（约10:11:50上限）；全部输入结束（最近32383）。最新push `0f5c731`，本节及小型观察JSON待同步。剩余SAIF4、详细STA/DRC、PT12、export/独立结论及持久归档；P80未冻结。C80仅本地离线软件准备通过，正式RTL/格式/PPA未开始或冻结，详见09:46记录与C80准备说明。

## 09:50当前恢复点

09:48:53原watcher显示running/saif、error=None、SAIF7，仍是precision/structure/gate完成。第一标签watcher151016前台，第二标签Bash空闲；全部输入结束。原父95253/export96154不变，没有新服务器作业、文件写入、上传或删除。剩余活动5、STA/DRC、PT12、最终模型审核与持久归档；P80未冻结。

`ffc8067`已push，含C80纯软件筛选和240源哈希连接。C80候选完整流均值25075.65B，软件往返/同源连接通过，不代表RTL、解码周期或PPA。新偏置规范外部23232半字与核心内部23488半字必须分开计数；计划在解码器内部恢复第三偏置半字，预测状态独立于计算SRAM。本地没有活动测试会话，C80 RTL/C32/G32均未开始。旧T80桌面和全部旧八路数据不动。

本地检查点更新的一次中文stdin因编码错误未执行，后续通过直接UTF-8文件补丁完成；`0925cf5`只含解码集成文档，不含该失败更新。服务器不受影响，原队列未重启。

## 09:46最新：P80活动6/12，离线C80准备已通过

09:45:22原watcher显示running/saif、error=None、SAIF6，已完成precision/structure/gate。原95253/export96154不变；**第一标签watcher151016前台，第二标签Bash空闲，全部输入已结束**。尚待活动6层/STA/DRC/PT12/审核/归档；没有新增服务器文件、上传、删除或EDA作业。

并行仅软件准备：`ffbfa54`新增C80离线候选/筛选，`da38819`显式选择字节相同PR转换器；6组codec测试、Python3.6语法通过。首次screen因CRLF哈希不同在创建输出前被拒绝；本地Git原字节SHA c993…匹配，原工作树未改。运行`local_runs/c80_offline_screen_20261116_0940_02`完成240任务，两个候选11028480整数逐坐标一致。输入流均值29755.9B→29243.9B（仅偏置）→25075.65B（完整候选），未开发C80 RTL、未冻结格式、未得解码周期/PPA，不能称阶段通过。

09:41:58.786567只读源连接通过：服务器原DATA100前20条240个实际load.hex逐项符合固定inventory，其路径+哈希链`af44510d1fdf61059af8eef82ecdbf2810da6be004f364ad95ed2fcff242d987`与本地同源重数量化一致。第一次GUI输入因CR回车在键入前拒绝，LF重试通过，所有会话已结束（最近51765）。原数据没有改动。摘要及说明见`C80_OFFLINE_PREPARATION_20261116.md`与`C80_FIRST20_SOURCE_JOIN_20261116.json`。

最后确认push251fbbe，代码及本节待同步。C80/C32/G32硬件仍待P80冻结；只利用当前等待时间做离线准备。T80桌面、旧八路及B0备份不动。

## 09:29最新：活动3/12，交接入口已整理

09:28:21原watcher显示running/saif、error=None，precision/structure/gate完成。09:26:43逐项读取L01～03活动均通过；详见`P80_ACTIVITY_PROGRESS_20261116.json`。所有输入结束，**第一标签watcher151016前台，第二标签Bash空闲**。原95253/export96154保持，无新作业/删除。0363c46已push，本节及进度整理待同步。

根交接已缩为当前入口，旧392347字节逐字节存入`handoff/history/CONTEXT_HANDOFF_THROUGH_20261116_0928.md`，SHA `9abec37f5caf83650da4324b4e0ec2bc99c4a1072719c5dc56b55860cad74224`；历史没有删除。剩余SAIF9、详细STA/DRC、PT12/模型审核与归档，P80未冻结、C80未开始。

## 09:19最新：L01完整SAIF通过，L02原子进程运行

当前前台**第二标签Bash空闲**，第一标签watcher151016继续（上限约10:11:50）。所有输入结束，最近6969；VNC18874435/workspace3。原父95253、export05父96154不变，不清锁、不重启。

L01活动文件**97679538B**，SHA **`369a96911074d6d2b9a642c07d195290b27e339e33a0f2b813509a7d2171d89e`**；完整窗口93149.990685→629623.270371ns、536473.279686ns、80471周期，25344输出，回放输出/IRQ/WFI/窗口与同网表门级一致。原子149666于09:08:48.778415启动、09:13:15.782032自然结束；CPU266.020秒、实际wall267.003617秒；首份有效活动回执09:14:31.020395，总342.241980秒，其中解析/核对约75.238363秒。

**L02子152202**于09:14:31.035304启动，09:18:42原账本仍running。首例后存储预算free87824801792B、required3441161304B、remaining11、maximum98005883B，含1.2倍与2GiB余量。按首层估计从09:19起剩余活动约60～75分钟，后续STA/DRC/PT/审核/归档另计，不能作为完工承诺；详见`P80_SAIF_L01_OBSERVATION_20261116.json`。没有以旧波形代替本轮活动。

既有S0的已冻结原报告只读查到首层SAIF CPU290.340秒；仅作宿主开销参照，不复跑、不混入P80功耗。原source报告SHA65c471…已核验。2212dca是最近本地检查点提交，最后确认push3285a1d；本节/首层摘录待下一次同步。

本轮未新增任何服务器删除；B0重复输入cleanup13仅本地准备，六份DRC统计报告未准备清理工具。门级14/精度/最终综合已完成，剩余SAIF11、详细STA/DRC、PT12、export05、独立结论及持久归档冻结；C80/C32/G32均未开始。

## 09:13当前终端与活动采集

**前台第二标签Bash空闲；第一标签是只读watcher151016**（09:11:50开始，30秒间隔，最多120次，队列离开running即退出）。第二标签旧watcher135257已确认在08:49:50阶段变更时结束。所有输入已结束，最近7053；不要向第一标签watcher键入命令。VNC18874435，workspace3。

09:13:07：原95253仍为唯一队列父；**SAIF首层simv子149666**已经运行4:19/CPU99.5%/RSS542260KiB，尚无.saif完成文件。native编译42.264秒、elab13.147秒、link1.193秒已完成。原功耗前置仍在完整活动采集，不能因暂无文件便重启；SAIF是在窗口关闭后输出。tmp实际可用**87922278400B**；共享空间要在最终归档前重新读。原export05依然等待，无新EDA队列。

3285a1d已push，包含gate14与完整周期一致性及六份B0统计报告只读核对摘要；本节待同步。尚待SAIF12、详细STA/DRC、PT12、独立审核及持久归档，C80/C32/G32未开始。本次没有任何新的服务器删除，T80桌面、旧八路和B0备份不动。

## 09:09最新：同网表gate14全部通过，原队列进入SAIF

09:07:59实际队列running/saif、error=None，completed=[precision,structure,gate]。自身门级14全部通过，摘要SHA **`4688df6cc69d60c3705b603efbe65c3481e68f8742a1ff23a542945b48e29061`**；09:09进一步读取354816输出、全部14例完整周期与自己的ASIC RTL一致，固定12均值77545.33333333333。无SDF、门级不观察内部total，内部total已由自己的ASIC批量验证；不扩大此验证范围。详细摘录`P80_GATE14_OBSERVATION_20261116.json`。

前台第一标签Bash空闲，所有输入已结束（最近94093），第二旧watcher自然结束状态尚未截图；原父95253和export05不变。最新push02305a4；本节及gate14摘录待下一次提交。新活动12/STA/DRC/PT12、最终审核和持久归档仍待，未进入C80。

仅补充只读空间证据：B0完整原备份中的六个DRC04/05统计报告当前SHA全部匹配，961987609B，见`P80_B0_ARCHIVED_REPORTS_READONLY_20261116.json`。名称是**systolic_b_v3_drc04/05**，不是无v3的路径；此前严格名称查询返回0，未作文件操作。六文件为mapped_probe_inventory.tsv、area_inventory.json、leaf_area.tsv；没有移除原件，没有加入cleanup13，也没有准备/执行新的清理工具。原备份、最终DRC06、网表、T80桌面和旧八路不动。

## 有效目标与不可动对象

- 用户计划原件：`E:/UserData/LENOVO/Downloads/T80_搬运编码优化_32PE_时钟门控实施计划_20261115.md`。仓库副本`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。
- S0→P80→C80→C32-A/可选B→G32；最终16×2/32PE、150MHz、SS/.99V/125°C、6.666666ns，项目保守面积≤1.00mm²。每阶段自己的20条/240任务、门级14、活动12/功耗12及交接完成后进入下一阶段。
- 原32位ICB、原平台参数；源读→成功共享写ACK→原总线真实读回→解码→输出写ACK/排空。不能旁路、不跨任务预装载。X14/W12/acc32/total33/SHIFT10不变。
- **服务器Desktop/T80_Delivery_20261113和所有旧八路数据禁止修改、移动、删除。**本轮均未动。
- C80/C32/G32均未开始；原T64/G64旧队列不恢复。不使用旧网表PASS验收P80。

## 本地身份与操作入口

- 工作树`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。
- 最新已push **c8f6a24**；08:57新增精度/进度记录待随后提交。硬件142fae2，当前服务器操作包1023646；文档提交不改变受测硬件。
- Git使用`-c safe.directory=E:/fpga_race-two/kwt1-c32-g32-20261115`；Python用`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`。
- 未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不是本轮内容，不加、不运行。
- 已读computer-use技能及`F:/linux_fpga_try/AGENTS.md`。用`F:/linux_fpga_try/ac820.ps1`控制开发板上的可见VNC，不能绕到比赛服务器隐藏通道。
- VNC18874435、workspace3。**当前第一终端标签Bash空闲**；第二标签只读watcher135257应已在阶段离开synthesis时自然退出，需新截图核对。所有键盘会话已结束，最近68209。不能根据旧位置盲目输入。workspace4不动，FileZilla未使用。

## 当前唯一原队列：不要重启

服务器私有根`/tmp/s4_21usr_p80_20261116_0315`（下简称root）。

- 父**95253**，`root/p80_final_combined05_controller.py`，SHA `46e2a8fb416db99febbc9c2bb6ea09b619b515bb185711c2a3a9782277d11651`。
- 队列`root/light-light126-p80-1023646/runs/p80_finish05/state.json`；根控制`root/p80_final_combined05.json`不包含实时stage，查询应读队列state。
- 原共享锁`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`，不清锁、不另启EDA。
- **08:56:45：running/gate，error=None，已完成extremes、rounding；layer_01的simv子143466运行8秒/CPU99.5%。**编译已成功，VCS编译35.891秒、elab7.095秒。不要重复编译或重跑已完成用例。
- 原队列先precision，再structure/gate14/SAIF12/timing_audit/drc_audit/PTL01～12，总18阶段。终态`reports_ready_review_required`后自然释放锁。
- 原export05父**96154**，`root/p80_export_review05_controller.py`，SHA `952242ef4a1ea2b9ee5bcde89ec0cd4b4c48f2bd504a55ae8a3f1031a31fee4b`；等待原队列，自然导出/未知活动清单/锁内一次连接查询/模型事实。不能重复启动。
- 导出目标：1023646包`runs/p80_report05/p80_report`、`runs/p80_unknown_inventory05`、`runs/p80_unknown_connections05/p80_unknown_p80`；最终事实`root/p80_export_review05/model_review_snapshot.json`。事实文件不自动授予阶段PASS，仍需独立结论。

## 已完成证据，不重跑

### S0

声明条件完整验收并持久归档/冻结，标签`arch03-s0-partitioned-20261116-0215`已push。平均112569周期、1332.5160568task/s；项目保守面积0.9535222591mm²；50.240373mW、37.703387µJ/task（布局前模型范围）。详见S0报告与FREEZE，不重跑S0。

### P80真实CPU与本地

- 硬件`142fae28545759e33fa38de514eabf752cb8c43a`。本地10000随机+32定向块、22矩阵、协议、取消、1/2拍SRAM已通过。
- 元信息深度2/4/8各自真实ASIC/E20314通过，354816输出/版；固定12周期一致，选最小深度2。
- 固定12：平均**77545.33333333333周期、1934.35237882357task/s**。相对S0吞吐+45.1654%；不是芯片实测。源码摘要`142fae2/runs/p80_fixed_d2_05/p80_soc` SHA `43e9ec58048d24ab8ab7d505723f7360b1e7e1e6eeaf5d76c81134cef34222c8`。
- 自己的深度2恢复十阶段、CPU竞争、前20条240任务全部通过，6082560输出及total零差异。`e139032/runs/p80_d2_batch20_02/p80_batch20` SHA `36953e487c757a9980c4ac33760b7a8f65c6f61209e6b2582a8342b582d7e687`。批量均值77545.1583333与固定12不可混用。
- 固定12平均编码29756B，平均34989个事务，符合3B/4+12672；详细搬运及调度读数已保存两个P80_FIXED12_*OBSERVATION JSON。供数空拍50301～62765，首供数等待2811～3707，最后写回尾部141；这些来自原摘要，没有新仿真，重叠等待不相加。

### P80最终综合

- 操作包`102364644dd181b23358dc2c7fe0d6e8279ae0d2`，manifest SHA `402c08165610ed18bdd772cddd3d527570fd62bdaa6ff820e0ad19b5d7082bcd`，947源文件。
- 运行`1023646/runs/p80_synth_d2_06/p80_synth`，摘要SHA **`75460463afddef3043613822bd58b8ee66e4869a826d49bf0899052d6e664c1e`**；网表SHA **`583e2e8f5ed6e61b357ddf477bab0e3e826e9f39f6ba490f16da275d40d0192c`**。
- 项目保守上界**0.9529288663004588mm²**，已知新增0.7924098895005534；整机4475145.365862um²。setup **+0.000055331ns**、hold **+0.00113887ns**，6.666666ns，92小宏+128大宏=220，锁存器0。
- 共享、加速器、CPU映射分别35.6743365、4470.2956079、748.8967320秒，最终链接133.8648641秒。原98857/132629/138231均已自然结束，没有重启或用失败映射替代。
- `P80_SYNTHESIS_NUMBERS_20261116.json`是初步数字；后续详细STA/DRC、门级、活动/功耗未齐，不提前冻结P80或称物理签核。
- 结构阶段已生成清单：11336项declaration_only，no_load匹配True；数值实例80PE/80转换/1阵列。实际剩余告警LINT32=10741、LINT33=1187、LINT1=4；四个LINT1为debug的ndreset/fullreset、AON porrst和PLIC优先级寄存器。无面积/内部功耗豁免，完整审核仍需后继证据。

### P80新浮点精度连接

- `1023646/runs/p80_finish05_precision/p80_precision`已通过，摘要SHA **`d7fca6e57d2e879b42c89c4e4ab09e7d82aeda1ed8a293267e2a1bf840303f31`**。
- 同批20条240任务，6082560输出重新连接自身ASIC结果，最大逐层汇总NRMSE **0.20198143836753799%**，最大单任务 **0.20953408931848963%**，X/W/b裁剪均0、饱和0。详见P80_FIRST20_PRECISION_OBSERVATION。
- 实际FLOAT包`/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip`，SHA `5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2`。原始成员来源已核对，旧原ZIP容器edb…未获得，不混写。
- 固定12精度会由同队列最终导出再次计算/核对，官方600未验；不能把20条精度称官方结果。

## 空间、备份与准备工具

- 08:34共享盘仍只有1,048,576B；较早tmp可用约89GB，写新大包前刷新空间。
- 早先cache09/10/11已核验归档后清掉普通编译缓存，不能重跑。本次上下文**未删除任何服务器文件**。
- B0完整原备份`SERVER/IC/light-light126-undergrad-d2-20261109/backups/systolic-b-20261112_2320`只读保留：archive SHA `dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50`，1261445859B，63653成员/7006124866B已于08:23全量回读通过。
- 原只读预检12已结束，结果`root/b0_archived_batch_preflight12/verified_candidates.json` SHA `fbb98604283fcac8285dc817f554dd7bcccee37f85faba07d9fefe72906e9bd8`。仅B0完成批次cases里的49200个生成.hex/.verilog/.bin，共2616732144B，与备份一致；没有清理、未证明无占用，预检不重跑。
- 本地`P80_B0_ARCHIVED_BATCH_CLEANUP13_20261116.py`（156e828含保护测试）**未部署/未执行**。要求原P80队列和export05自然完成退出、获取原共享锁、备份和源SHA重新核对、严格无占用、逐文件日志及目录fsync；15个保护路径拒绝/6个状态拒绝场景通过。不可向仍运行队列并发清理；看不全自己的进程则失败，不据此豁免。
- P80最终持久复制归档尚未执行；使用已有`p80_archive_runtime.py`，要求1.2倍实测压缩大小+2GiB空间。不把临时根当最终交付，不自动覆盖原备份。

## 已失败路径与下一步

- 综合01旧驱动库限定符错误；综合02建锁ENOSPC；combined02 Path类型错误；combined03 ENOSPC；combined04重复旧set_local_link_library路径导致UID-15/993。全部保留，不重启。
- 1023646只在核对旧/新同字节DB后修正库引用，没有更改库/角/时钟/负载或RTL；当前真实四段综合已验证修复。
- 下一步继续原gate14→SAIF12→详细STA/DRC→PT12及export05；及时读取终态和失败，禁止重复派发。必须等本轮完整报告、独立结论和持久归档冻结后再实施C80。
- 当所有原队列结束后，按实际空间和严格占用检查决定是否执行已授权范围内的B0重复生成输入清理，保留完整备份与输出；旧八路/T80桌面始终排除。
- 压缩前更新根交接与本文件，记录前台标签、所有未结束输入/作业身份；压缩后先读计划与最新检查点，不能根据历史PID盲目恢复。
