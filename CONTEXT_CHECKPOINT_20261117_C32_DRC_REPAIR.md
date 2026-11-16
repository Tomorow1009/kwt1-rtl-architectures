# C32-A修复验收检查点：11月17日06:09

## 有效计划与保护范围

恢复先读AGENTS、handoff/team/README.md、SYNC.md、STATUS.json、本文件及 `workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`。计划SHA：1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。

路线S0→P80→C80→C32-A→可选C32-B→G32。前三阶段已冻结；当前仅完成C32-A本阶段，不提前开始后继硬件。最终32PE、150MHz/6.666666ns、SS/.99V/125°C、保守面积≤1.00mm²，<.50为努力目标。原32位ICB、原平台缓冲；源读→共享写成功ACK→原总线真实读回→解码→计算→输出ACK排空。X14/W12/acc32/b32/total33、SHIFT10；正式20条×12层，100条未自动授权。

**旧八路全部数据、Desktop/T80_Delivery_20261113、冻结S0/P80/C80运行及备份不改不移不删。** 用户已确认没有团队持续共享盘写入，不能归咎队友。清理32/33/34已终态，禁止重复。所有新验证产物仍/tmp。

## 唯一正式队列及当前完成项

ROOT=/tmp/s4_21usr_c32_20261116_2010

- 当前包：ROOT/light-light126-c32-repair-5828804；manifest321c38f06fe155e491bcb580703eb5fdc96755f4bf4876d7c5545c6ae3b0dd07。
- 原功能包：ROOT/light-light126-c32-91135f6；manifestd877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7。
- 生产RTL仍61246bb2a21c56a9bfd871fd68de93028d79f5fd，固件/原受测工具91135f61c97c980039793c6637d0a06888638df0。修复03只换6个同库等价驱动单元，全部其他Verilog token和leaf一致，无RTL/拓扑/约束改变。
- 唯一父**101802**，ROOT/c32_finish04_driver.py，04:44:20.534853启动；队列当前包/runs/c32_finish_repair04。driver SHA69d8a2cfa69b692953ce1dbddea77f491f85d288cd5a077ccaa5e4d0bc3ceeac。原共享锁始终由它持有，不重启、不清锁。
- **06:08:37.239001**：running/power_layer_01；已完成structure、gate、saif、timing_audit、drc_audit。最后已记录子140573（drc_audit）退出，开始时间06:07:26.133996；PT子尚未在该截图中显示。共享盘1048576B、/tmp61340139520B。
- 精简只读入口ROOT/c32_repair04_status.py（SHA6bf482079317c2363ecbd77e89ff976d56a28dc2e652aa6725d5c5c732388992）。不要打印大state或重复WAIT日志。

### 修复03映射与新门级/活动

映射当前包/runs/c32_repair03/c32_synth，summary SHA78268481a2fc203ae27102239ac9cdfcf83fdac3fef40dd08c8e1e2e2ef878e5，mapped.v SHA4f6e416402f2a178ec0ae0494fab1cddc53d7cf9113ac19990e108580b47c1dc（已机器断言）。constraints.rpt明确无违反。保守项目面积0.7224077334997787mm²，setup +0.0000524521ns、hold +0.0010598ns，92小宏+128大宏=220，非预期锁存器0。映射身份显式说明DDC复用及等价修复，不能伪称新三块综合。

新门级14：当前包/runs/c32_finish_repair04_gate/c32_gate，summary SHA8eaea9b1318f8f8031c3d4f160283140842896b68cb73bbfd93f719b81ed09a9。354816输出通过，全部14周期与同RTL ASIC14机器比较一致；无SDF，内部total不可观测。

**新活动12已全部通过**：当前包/runs/c32_finish_repair04_saif/c32_saif，summary SHA5a8e6da88e10481f172b9e64b0c458bd8773a06ea6072bd49315ce956f5e07ba。12层、304128输出、761444514B活动；每层完整窗口与自己的新门级一致。06:07:13.537961已机器断言summary及其修复03综合/新gate14身份。固定12周期：[74750,73187,72186,72264,70798,69193,68427,68604,68610,70970,75393,81770]。新证据C32_SAIF12_REPAIR03_20261117.json。

自己的PT12、模型/未知活动最终审核及持久归档仍待完成，C32-A尚未冻结。旧坏网表48.9738373mW/23.5659905µJ不能继承；STATUS原数值已移入unqualified_original_netlist_evidence，新功耗字段null。

### 可复用的同RTL功能/精度证据

本地10000随机+32定向、14例、1/2拍、ABA/取消；真实ASIC14、恢复、CPU竞争、20×12共6082560输出及total零差异均已完成，均不重复。原initial03 state SHA37e1279f0c165b6fb50493c4d87edb2a994e159a90e22e48b92c41ef8ab500c0。最大逐层NRMSE .20198143836753799%，固定12最大 .1425636423408142%，官方600未验。

固定12平均72179.3333333周期、2078.1571825730357task/s；240批量均值70929.4083另列。固定12完整编码均值25790B、四段事务均值32014.5。C80冻结对照为70603.1667周期、2124.5505985task/s、保守.9611361367mm²、55.3675891mW、26.0608448µJ。详见对应JSON/阶段报告，不拼接不同版本最好值。

## 自动报告等待器

父**110729**，ROOT/c32_finish04_export_wait.py，05:02:53.930401启动；06:08:37检查/proc命令身份仍匹配。它只等待101802自然成功退出，随后调用ROOT/c32_repaired04_export_review.py一次；失败不重试，不晋级硬件。

waiter SHA6afee3001cde7f6e4ffe71ff01737173f014e6fd9c44a39bf4d3f78dcf65e777；exporter SHAa2aaef702e6c241f1bc12da41905c0e4434d5a8c803c6299958f5fd6b28bcebc。控制ROOT/c32_repaired_export_review03，报告当前包/runs/c32_report_repair03/c32_report，未知清单runs/c32_unknown_inventory_repair03，连接runs/c32_connections_repair03/c32_unknown_c32。新连接查询自带原锁ENOSPC等待，不启动旧export03。

## 存储：正在制作完整只读副本，尚未释放空间

共享盘持续约1MiB；HOME和共享盘同设备45，/tmp设备2051。B0包约85.29GB主要是旧R4已压缩波形，不能作为编译缓存删除。旧N1 >1MB csrc候选0。旧B0原大文件/最终网表/R4交叉核对依赖保留。

当前只读对象：PROJECT/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02/layer_03.vcd.gz，PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109。gzip7662823694B，对应原VCD12584787471B，11月12日原VCD已完整归档移除；原JSON保留。

1. 三段64MiB样本XZ3/gzip6往返全部一致；仅可行性，不是删除证明。probe结果/tmp/s4_21usr_c32_storageprobe_20261117/result.json，SHA1177460e4694be4852dd7c13d48c41a1ad0c8445a019bf178d095d2eee596c1已由stager机器验证。
2. **父128419**正在只读staging：/tmp/s4_21usr_r4_l03_xzstage_20261117.py，SHA1ab445bf8f621c84f40adb0db4e4fa43fbb5f18e660e13cd720a820b0c286f04；日志同前缀.log、启动回执同前缀_launch.json，控制及文件目录/tmp/s4_21usr_r4_l03_xzstage_20261117。nice+15单核，保留12GiB/tmp余量。
3. 原gzip完整临时副本original_layer_03.vcd.gz已复制并独立全SHA回读通过。06:08:37状态compressing_xz，已处理8858370048B/1582.8366秒，未出现错误。**尚需完成XZ并独立全量解压核对原VCD哈希/字节数；共享原gzip尚未改动或删除。**
4. 仅本地准备的新迁移入口handoff/team/evidence/C32_R4_L03_XZ_MIGRATE_20261117.py（SHAdea8d1031dd70d71bd9e630722c3948ed49422780dd34a834c17a7f0f7a991e1）未部署/未执行。默认仅只读前检；--migrate为单独操作。要求完整stager终态及进程退出、旧gzip+临时gzip+XZ全哈希、至少2GiB净收益、原协作锁；唯一删除目标是上述R4 L03旧gzip，原回执和临时gzip保留，持久XZ必须再完整回读。共享盘不足时必须先删已完全备份的gzip才能放入XZ；失败会保留临时两份数据和partial，不广泛清理。不能将它当已完成或盲目启动。
5. 严格全进程检查遇到/proc权限限制。06:01:02只读确认的不可见进程是UID14021的桌面系统辅助进程：10519 gnome-keyring-d / argv0 gnome-keyring-daemon / start_ticks15432；79103 gnome-pty-helpe / gnome-pty-helper /139476165；202972同helper /197856763。可观测50个进程未见该源占用；3个描述符不可读。新本地入口只分类这三个固定身份，未知PID、启动计数/名称变化或可见占用全部拒绝，**不声称完整idle证明，保留不可见范围**。3项测试通过；它不能仅凭这一观察授权删除，完整备份及明确迁移操作仍为独立前提。没有绕过OS描述符权限，没有自动审批拒绝需要追问用户的事件。

### C32持久复制入口已部署，未启动

/tmp/s4_21usr_c32_archiveops01_20261117，54个冻结导入依赖已核验；tools.json SHAc53a4c486c5003341c7610f2e3706a9c99fe00b6ad6190829177eed8b2fb95ca，launcher.py SHA6ad68a9ee39c0ef6f4e29af23ef8a11ec3a39b3ce0abbed62252222d09d4f976。新等价修复合同+旧合同/容量合计12测试已过。只在101802、exporter、110729全部退出且新报告完整后显式调用launcher.py --tools-sha256上述值，要求20%+512MiB余量、全部回读，源不删。**当前无C32持久归档**。

## 已失败路径与不要重复的动作

- 原网表326条max_transition违反被旧解析器漏识别；旧PPA保留但不合格。解析器已修复，28项相关检查通过。
- repair01可选dont_touch空属性导致UID133失败；repair02仍有两条四舍五入0.00的max_capacitance违反；两者不合格、不能用其gate/PPA。repair03当前6单元修复通过。
- finish_repair03父99561在原锁创建ENOSPC，completed=[]、零子进程；当前finish04是新入口，未续跑失败队列。锁等待修复3测试通过。
- 旧export_review03因真实约束失败退出，旧unknown连接/原报告不当新网表结果。
- 清理32/33/34都终态；34后余已完全归档旧B0 generated NPZ536份/81364074B。不可重复删除；若以后要动须核验全链journal/当前存在/归档/无人使用。更早19–31同样不重复。

## 下一步与本地身份

继续同一101802的PT12，等110729一次性新报告/unknown/model snapshot；跟进128419完整只读XZ核验。随后准备具体且可审查的空间迁移，在原锁规则及副本核验全部满足后处理空间，不动保护目录。完成新网表审阅及持久归档后才冻结C32-A，再进入可选C32-B/G32。

本地E:/fpga_race-two/kwt1-c32-g32-20261115，分支codex/light-light126/t80-pipeline-c32-g32-20261115；最新1afc38c已推，本文及活动12证据待同步。仅历史S0_SYNTH05_FINISH_LAUNCH_20261115.py未跟踪，勿提交/执行。

VNC窗口18874435已重新确认、workspace3；不使用workspace4。当前无未结束GUI输入会话。不用子代理，不建goal。完整较早状态保留CONTEXT_HISTORY_20261117_C32_PRE0609.md以及0549/0523/0508/0455各历史，原计划不变。

## 06:31 增量记录（优先于上文旧观察）

- 06:28:57.987328：唯一101802继续running/power_layer_08，自己的PT已完成7层；第8层子150238，06:28:55.963831启动。门级14、SAIF12、时序/DRC审核均完成。未重启作业。
- 自己的L01功耗summary已机器核验e0548230104f9525e684703259202f224a1ba6c4bb94678bc57c6f9cbf60ac69；48.7147681mW、24.276190342214µJ仅为第一层，不是12层平均。证据C32_POWER_L01_REPAIR03_20261117.json；旧L01指针移入原坏网表历史。
- R4 L03 XZ staging父128419已退出，06:21:36.057712全量解压回读完成，12584787471B原VCD哈希一致；XZ2780943668B，预计省4881880026B。state SHA632b0460df8d6a78e411aebae634ffe1ed7efd9cc1901b4fe165543b03d22e05；共享原gzip仍保留，无新删除。
- 首次只读迁移身份前检拒绝，未迁移/未删文件。原因已核对原06:01:02截图：202972的start_ticks实为130547063，我方误抄为197856763；原图和06:23/06:28重读一致。不是放宽检查或忽略身份变化。10519/79103原值正确。
- 本地迁移入口仅修正上述常量及新control02目录，3测试再通过；新脚本/tmp/s4_21usr_r4_l03_xzmigrate02_20261117.py SHA00a4db3982d05a786aacc80510804b2372082faff8b35b23b9364541dcb67d89，原脚本保留。06:30部署核验及只读可见进程检查通过（49可观测、3固定桌面辅助进程不可观测、可观测源占用0）；未声称全FD可见或完整idle。
- 新只读全哈希前检已发出，日志/tmp/s4_21usr_r4_l03_preflight02_20261117.log，启动回执同前缀.json；待读取PID与终态。没有传--migrate。不得重跑相同日志入口。
- 继续原PT12/110729报告等待器；全部结束后才持原锁进行具体无损归档迁移，收齐模型/活动审核和持久副本，再冻结C32-A。桌面T80、旧8、S0/P80/C80不动。

## 06:50 增量记录（最高优先恢复项）

1. **finish04父101802已自然退出**，终态reports_ready_review_required；finished06:41:14.588988，自己的门级14/活动12/时序/DRC/PT12全部结束。state SHA e39de67261e36f838cc93a2c39004b9373338dddea96675dc38ef5d461613183已由后续启动命令机器断言。不要重启。原锁已自然释放。
2. 110729等待器已自动派发新exporter **155861**，06:41:49.855622启动。06:47:50仍exporting、error=None。控制ROOT/c32_repaired_export_review03，仍需等report.json、unknown inventory、连接和model snapshot；不能启动旧export03或提前验收。自己的完整功耗数值待读取，仍不继承原坏网表数值。
3. R4 L03默认只读前检已通过，父151286退出，日志/tmp/s4_21usr_r4_l03_preflight02_20261117.log SHA c575195f3aaf1c9b43b93b1cb1d8bd40143d21494baa94ece7964ef58bc2576e。完整staging state SHA632b0460df8d6a78e411aebae634ffe1ed7efd9cc1901b4fe165543b03d22e05已机器核验。
4. **迁移02父156897失败且退出，删除0**。06:43:41.385391启动，在acquire_lock的mkdir遇到ENOSPC；control state仍preflight，source_deleted=false，原gzip仍存在。失败日志/tmp/s4_21usr_r4_l03_migrate02_20261117.log、control/tmp/s4_21usr_r4_l03_xzmigrate02_20261117保留，不原地重跑。
5. 新迁移03工具准备：/tmp/s4_21usr_r4_l03_xzmigrate03_20261117.py，SHA cdd422679ce3084b0397306bd1446b492dda11f231cd295c89927b2dda9b163d。新control同名去.py；完整原始内容/两份临时副本/原回执核验逻辑不变，新增等待原锁及ENOSPC5秒轮询，不清任何旧锁。5项身份和锁等待测试通过。**尚未启动迁移03。**
6. 新恢复35最多选择剩余536份中按名称排序前128份旧B0 generated expected.npz，全部已由完整持久archive核验。32/33/34 journals和并集、已删文件不得再现、剩余536份81364074B必须精确相符；仍使用原路径/字节/哈希/无人使用/无EDA检查，有锁立即停止。没有源码、网表、日志、波形、T80、旧8或冻结S0/P80/C80文件。代码handoff/team/evidence/C32_B0_ARCHIVED_EXPECTED_RECOVERY35_20261117.py SHA785667c891ca90644c2652c3b96c25c8c0fda36acc3cf7ec67164ef289366218，目标ROOT/c32_recovery35.py；静态逐项适配原32安全逻辑及语法已核对。**尚未执行35**，必须先有身份正确的迁移03 waiting_for_team_lock进程才允许运行。
7. **当前GUI传输统一exec会话76905尚在运行**：正在部署以上03/35两个新工具，无main执行；本地命令E:/fpga_race-two/takeover_local/c32_space03_deploy.txt，共8489字符。先write_stdin轮询直到退出，再截图确认两个DEPLOYED SHA。不得重复传输或在未结束前并发GUI输入。窗口18874435/workspace3；不用workspace4。
8. 下一步部署确认后，在新独立日志启动迁移03，核对waiting状态和原锁；再显式启动恢复35（--execute-verified-remaining-captures），持久归档/原锁均核验后只删已备份重复NPZ直到锁出现，供迁移03取得锁。之后跟踪R4持久XZ完整回读和C32新报告，完成C32持久copy后才冻结C32-A，再进入C32-B/G32。

最新本地提交e416b13（恢复工具和测试，未推）；此前9ff2cd2及82be84d已推。当前阶段报告已重写为新网表专用，原混合历史保留C32_STAGE_REPORT_PRE_REPAIR03_20261117.md，不再据旧表拿新功耗。仅S0_SYNTH05_FINISH_LAUNCH_20261115.py历史未跟踪勿提交。本段之后的实际观察继续追加；全部禁止保护范围与当前计划不变。

## 07:03 增量：新功耗数值及空间迁移完成

- 新修复03完整报告已生成，report SHA ea4b916db90117e1082565bd9dd78947098200dddd39de5a6d2c42d950ad3565。07:01:35.762375已机器断言该SHA、修复网表SHA、12层周期/时长/功耗/能耗关系。时间加权平均0.04897381980833410302117873075W，平均能耗0.0000235659820737505569651J。总时长5774346.089232ns、总能量0.0002827917848850066835812J。加权动态0.04208028354075208508437318161W、泄漏0.006893535898086675317958048934W。新证据C32_POWER12_REPAIR03_20261117.json，阶段报告已更新。
- 首次数字转录将power内部一位抄错，机器断言拒绝；分组重读后已更正并全断言通过。原report及实测数据未改，错误值未写入正式数值证据。
- 06:56:23 exporter155861为collecting_new_activity、error=None，export子155879已退出；新unknown inventory仍在处理。不要重复汇总或原EDA，之后还有连接及model snapshot。C32-A暂未冻结、未启动C32-B/G32。
- 迁移03父160753，06:52:30.217349启动；恢复35父161408，06:54:04.737909启动。35完成128份已归档expected.npz重复移除、19387868B，余408份61976206B。完整持久archive不变；不重复35。
- **R4 L03持久XZ已通过完整解压回读并完成**：06:58:31.604005，父160753已退出；status durable_xz_verified_original_gzip_copy_retained，2780943668B，完成时free4433379328B。目标PROJECT/backups/r4-l03-xz-20261117/layer_03.vcd.xz，receipt.json与RESTORE.txt保留。原共享gzip已删除，其精确副本仍在/tmp/s4_21usr_r4_l03_xzstage_20261117/original_layer_03.vcd.gz；原JSON未改。原始VCD全字节可恢复，不是丢弃波形。下一步读取/机器绑定持久receipt SHA及35journal状态，记录准确恢复索引。
- 所有GUI输入会话已结束；当前窗口18874435/workspace3。继续原export模型审核，等110729及export全部退出后，显式运行已部署C32复制launcher（tools SHA c53a4c486c5003341c7610f2e3706a9c99fe00b6ad6190829177eed8b2fb95ca），不得在其source仍写日志时归档。备份成功后才冻结C32-A。桌面T80/旧8/冻结S0/P80/C80不动。

## 07:11 增量：模型事实齐备，C32持久复制已发出

- 07:09:17.128417观察：新export终态facts_joined_manual_conclusion_required，error=None，finished07:08:33.837854；unknown inventory12/12、连接子167226、aliases、model snapshot全链完成。尚需读取snapshot具体无时钟/禁用弧/未知端点分类，给出独立最终结论；不能仅凭工具完成自动宣称物理签核。
- **07:10已在可见终端发出C32 archiveops01/launcher.py --tools-sha256 c53a4c486c5003341c7610f2e3706a9c99fe00b6ad6190829177eed8b2fb95ca。当前截图终端尚未回到提示符，先截图核对返回/worker PID，不重复启动，也不在旧命令仍前台运行时继续输入。** 所有工具输入函数会话已结束；仅VNC终端前台命令可能忙。启动器只在所有父/子/waiter退出后放行，源ROOT全部保留。
- 07:09共享free2970615808B，本轮runtime约6.69GB未压缩；copy工具会先精确估计gzip大小，要求1.2倍+512MiB余量并逐成员回读。若空间门槛失败保留失败、原产物与已有XZ，不随意减少余量或删历史证据。
- R4持久receipt与control已于07:05:35.781918机器绑定，SHA7b8bb1dd0f59bee614b57c362786cfbf88491d802655880416cecf88bd74363f。XZ SHA44bdc9d4adae4e013931bcabd9fedd47f601aed08be6c67761b3d41d8b751ea4，2780943668B；完整原VCD12584787471B、SHA93f87e3fbac3dfab270f808e9c40c74835bce30336f4059b038a22614c4574bb。精确原gzip临时副本及原JSON继续保留。
- 恢复35终态SHA8778b950c3c8981257fa859e3d33d0c22276acecf993b81b7c80cb5472e3edeb也已机器绑定，父161408已退出；不重复35。新索引C32_R4_L03_DURABLE_XZ_20261117.json含完整恢复路径。
- 最新已推dce11da。自己的功耗数值和源哈希都已入Git。下一步先确认持久复制启动/运行状态，再读取新的model snapshot、完成范围明确的技术结论；归档完成及核验后冻结C32-A，再按有效计划评估可选C32-B/G32。不自动运行100条。所有旧8和桌面T80保护继续有效。

## 07:25 C32-A冻结：本阶段完整收口

- repair03本版门级14、SAIF12、PT12及完整模型事实已经收齐。07:15:51.319288机器绑定model snapshot、未知端点分类、12层时钟/禁用弧表；没有未知活动落到显式时钟、复位、ICG或SRAM控制引脚。记录原PT未知活动政策，不豁免驱动内部功耗。独立C32_STAGE_CONCLUSION_20261117.json给出稳定任务模式/布局前估算范围内的验收，原工具false标记不篡改。
- 归档worker168727已自然退出；07:16:55.275349完成copy，07:23:38.283548再次机器绑定关键值。目的PROJECT/backups/c32-runtime-20261117_0709-repair03-copy01；runtime-evidence.tar.gz 1572653883B，SHA30f111ef8b51cb7ab223cc50a35e7812be4a8f08c53fc54df9b51aea8b56b80f。25291常规文件、1706目录、11链接全部回读，源前后相同；源未改未删、迁址复现未宣称。receipt SHA f707f20af9a8f98a615298481a81daddc57e5ebb9fc98999b22097f185310db9，原协作锁已自然释放。
- 新冻结记录C32_FREEZE_20261117.json，计划tag arch03-c32a-repair03-20261117-0725。固定12：72179.3333333周期、2078.1571825730357task/s；保守0.7224077334997787mm²；48.9738198083341mW、23.5659820737506µJ/task。功能240/6082560输出及total零差异，未运行100条。C80对照：吞吐−2.18368%、面积−24.83815%、功耗−11.54786%、能耗−9.57322%。
- C32-B/G32硬件此前尚未开发；下一步先评估两4096×16行奇偶bank方案，吞吐下降则不选。不要重跑C32-A的240、综合或门级/PT。不再做旧8/T80清理、不重复35或R4迁移。

## 07:35 C32-B筛选完成，G32从冻结A派生

- C32-A冻结提交02fbd1a及tag arch03-c32a-repair03-20261117-0725已推GitHub。
- 新C32-B两4096×16实现本地14例354816输出及total通过，物理端口与末单行核对通过。run local_runs/c32b_datapath_20261117_072930_759016，父工具会话90958已退出。比较local_runs/c32_cache_compare_20261117_0734：同条件固定12总周期A725798/B726236、均值A60483.1666667/B60519.6666667，吞吐−0.0603109733%。18个共用文件及编码/参考哈希匹配。
- 不满足不降低吞吐筛选，候选不晋级；没有服务器PPA/ASIC、没有继承A的PASS。G32从冻结A直接派生，继续60小X+32小W缓存。源码和选择证据保留。首次runner误用codec32b.hex已修复，失败目录072828保留。
- 新G32契约G32_IMPLEMENTATION_CONTRACT_20261117.md：实际库ICG，数值数据门控，valid/归属/控制/IRQ/取消保持运行；同激励参考/门控/静态旁路逐周期对照，随后自己的20×12和完整新PPA。尚未启动服务器G32。
