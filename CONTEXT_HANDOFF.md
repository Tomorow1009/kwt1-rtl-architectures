# G32恢复检查点：2026-11-17 09:36

压缩恢复后先读AGENTS、团队README/SYNC、有效计划、本文件及STATUS的`c32_g32_20261115.g32_development`。旧交接完整保留`CONTEXT_HISTORY_20261117_G32_PRE0936.md`；不要按旧“运行中”状态重启任务。

## 目标、已完成及保护范围

- 计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA 1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。
- S0/P80/C80/C32-A已冻结，C32-B因完整吞吐下降0.06031%未晋级。当前只完成G32；32PE、150MHz/6.666666ns、SS/.99V/125°C、保守面积≤1.00mm²。
- 原32位ICB及平台缓冲不变；源读→真实共享写ACK→原总线读回→解码→计算→完整输出ACK排空。X14/W12/acc32/b32/total33、SHIFT10。
- 正式20×12＝240任务、6082560输出及total。100条未授权。
- **Desktop/T80_Delivery_20261113、旧八路全部数据、冻结S0/P80/C80/C32和备份不改不移不删。** 用户确认团队没有共享盘持续写入，原因未知，不归咎队友。
- 不建goal、不派新子代理。VNC只用第三工作区，原锁不清、旧队列不重启。GitHub同范围同步已授权。

G32生产源码0e16994675bb15e53642017a88f6307da9af4a01；ROOT=`/tmp/s4_21usr_g32_20261117_0810`，BUNDLE=`ROOT/light-light126-g32-0e16994`；manifest 3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a。生产包未改。

本地10000随机＋32定向317824输出，C32/G32门控/G32旁路逐周期相同；14例、1/2拍、取消/恢复/ABA及27协议场景通过。服务器自己的ASIC14、真实CPU恢复及竞争、新三块综合通过。固定12总866152周期、平均72179.3333333，2078.157182573 task/s，每层与同数据C32-A相同。

新综合保守面积0.727972347099813mm²，setup +0.000433922ns、hold +0.00289777ns；92小宏＋128大宏、0锁存器，DRC明确无违反。实际383个加速器ICG、10306寄存器时钟端点。普通时序结果不能替代实际门控时序或功耗。

综合`BUNDLE/runs/g32_initial01_synth/g32_synth`，summary 5f270c7366d5914b4fbe219862987e19314e7f6c24f90b00b8f963890a9c8a92，netlist f02759430cff876497e7158a5b570a7543553f066a58197a5eeca0546c6e02bb。

## 失败路径与当前唯一队列

原initial01父202586已退出，完成soc/sequence/contention/synth后在ICG检查失败：PT2022 pin不支持`name`属性。失败state SHA de797dab25bccd50134556e363bb074ebe94a22650965495f4e9820cda9d4df5。不能改成passed，不能重跑原队列。ROOT/status01.py仍指向原队列，不反映新恢复。

修复只改3处pin查询为`full_name =~ */E`或`*/TE`；网表、约束和原生检查不变。第一版启动器因两份请求JSON序列化不同而拒绝，未创建队列；09:29逐字段比较完全相同。新启动器分别核验原外部hash与内部语义，旧操作目录保留。

**当前g32_recovery01父245913**，09:31:49.991797启动。新ops=`/tmp/s4_21usr_g32_recoveryops_20261117_0933`，manifest cfc31793de02b5795d272f84e3f7cb537a02ad10749d9628fb92a3d368ba02bd。ROOT/g32_recovery01_request.json、_launch.json、.log；状态BUNDLE/runs/g32_recovery01/state.json。

**09:36:01.531127最后观察：running/icg，子247663，completed=[]、error=None。** 原锁已取得；先门控检查与批量准入，再自动自己的batch20和precision。原ASIC/恢复/竞争/综合不重复。PT日志BUNDLE/runs/g32_recovery01_icg/g32_icg/clock_gating.log。

原四阶段＋新三阶段显式连接已实现，19项工具测试通过。`g32_recovery_contract.py`核验回执、进程、来源、网表及全部哈希，保留原失败，不借旧PASS。

## 唯一GUI输入会话，先等待结束

**统一exec会话27381正在运行**，将7个后续工具部署到`/tmp/s4_21usr_g32_ops_20261117_0938`，只部署不启动队列。先write_stdin等结束，再截图确认G32_COMPLETION_OPS_PREPARED；禁止同时输入其他VNC命令。

输入`E:/fpga_race-two/takeover_local/g32_ops02_gui.txt`，5425字符；进度`g32_ops02_progress.txt`。manifest f614bef8b387b3943914cd7cd7407934bac2ba47396be15f95e789d1b07d21d4，payload e044c0f2ec274f641150884f915f9eb8529c3d8dbdf69599bee39eebc0cc0fc5。

新入口`G32_FINISH01_FROM_RECOVERY01_20261117.py`及`G32_EXPORT_RECOVERED_REVIEW01_20261117.py`需要原失败state、新恢复成功state等显式SHA。旧ops0845成功initial入口不适用，禁止调用。

## 空间状态

清理37父247294，09:34:53启动；128份已完整持久归档B0参考重复副本移除19454666B，余152份23122683B。state ROOT/b0_archived_expected37/state.json，显示SHA 850220e04bf6018a6011ba367ee40052bd64dc23f2d56b4b23efc4e3a58e7ead，待机器断言转录。已有归档、源、网表、日志、波形不改。09:36共享又仅1MiB，/tmp约48GB。**清理32～37均终态，禁止重复。**

R4 L04 stage02父232887，09:04:35启动；09:29:31仍compressing_xz，已处理8858370048B。目录`/tmp/s4_21usr_r4_l04_xzstage_20261117`；日志`/tmp/s4_21usr_g32_l04_storageops_20261117/stage02.log`。原gzip完整/tmp副本已核验；XZ独立完整解压回读仍待终态。没有共享源删除、没有持久迁移。样本probe不能替代全量核验。R4 L03持久迁移已完成，不重复。

## 下一步

1. GUI27381结束后读恢复队列和PT实际错误/结果，通过才继续240与FLOAT精度；失败保持原记录，在新目录处理具体问题。
2. 原恢复成功且所有子进程退出后，用新0938入口启动finish01：同网表门级14、SAIF12、时序/DRC、PT12，仍串行原锁。
3. 新导出、完整未知活动/连线/模型审阅、原生门控报告核对；与C32-A同周期比较整机能耗。未出结果不宣称节能。
4. 完整证据持久归档后冻结合格32PE。C32-A保底tag arch03-c32a-repair03-20261117-0725；面积.7224077334997787mm²、48.9738198083341mW、23.5659820737506µJ，持久备份已核验，不重跑。

本地最新86d4713；c4aa7b8已推。当前进度文档/STATUS/37回执/ops0938准备记录待同步。历史未跟踪S0_SYNTH05_FINISH_LAUNCH_20261115.py不提交不执行。VNC窗口18874435已本轮确认；F:/linux_fpga_try/ac820.ps1是已授权开发板Linux GUI入口，不绕过FTP代理或访问限制。

## 09:45增量（覆盖上文GUI及阶段状态）

- GUI27381及之后只读查询会话均已退出，无当前键盘输入。ops0938已核验部署，7文件、manifest f614bef8b387b3943914cd7cd7407934bac2ba47396be15f95e789d1b07d21d4；finish/export仍未运行。
- 新ICG检查通过批量准入，summary SHA **2657d4a98c669d56ef62e2c5bb499d943dc15d3c0fe886ad1190251a476de0dd** 已机器断言。383门控、TE静态0、setup +0.070571ns、hold +0.18723ns。原生定义报告65973B；setup/hold各327B明确`-slack_lesser_than 0`且`No paths with slack less than 0`，不是空检查。每个ICG两条实际路径完整TSV保留。PTE016仅时钟公共周期展开信息；PT003禁用弧仍留最终模型审阅。
- 09:44:54.858880，父245913 running/batch20，35任务887040输出、failed0。不要重复原ICG或重启批量。
- 新只读`g32_icg_native_review.py`及2测试本地通过，准备把定义行/逐路径/原生负裕量报告做最终机械连接，未传未执行。不跑额外PT、不改原报告。
- 清理37state SHA已于09:42机器断言，仍不重复。R4 L04暂存父232887已完成：09:41:50.676699，XZ2782976660B，预期省4866823449B；完整原始VCD解压回读通过，原共享gzip仍存在。显示state SHA 0cbf091dd3899031dd350d4fe47e01a4a96d4b392945ac11285601b06ecd7a7（该人工转录尚未断言，调用前重新计算/绑定，勿盲用）。
- 新L04迁移工具`handoff/team/evidence/G32_R4_L04_XZ_MIGRATE_20261117.py`本地准备，SHA3125e9b076130f0b0bdaa376abd7c80f8c27af85e48084b41c81cf7c0406331d，5项可见进程/原锁等待测试通过；仅由L03工具替换明确L04路径、大小、stager SHA，无删除范围扩大。默认只读完整前检，尚未传/运行，尚无L04持久迁移/删除。操作目标是原R4 L04gzip，绝不涉及T80/旧8或其他层。只有完整前检后才显式启动迁移，持原锁等当前队列自然结束。

## 10:04 增量：批量143/240，原生门控独立核对完成

- 原父245913继续running/batch20，10:04:16.122185已143任务、3624192输出，failed0；当前子266177。估计剩余1260.44秒含20%余量。shared仍1MiB，/tmp46655098880B。不要重启批量。
- **新的只读状态入口ROOT/status02.py已部署**，SHA fdda247adabd1ad34a833cba84c9492a4fc8f92ab8eb5a59fb7b577d7fafb561。执行`python3 -B /tmp/s4_21usr_g32_20261117_0810/status02.py`即可读取新恢复/finish/批量/锁/空间。旧status01不再使用。所有GUI会话已结束，无后台输入。
- 原生检查已独立核对全部383个ICG定义、766条正裕量路径和无负裕量的原生报告。回执ROOT/g32_icg_native_review01.json，SHA **add21a6f755ae86cc1496886ff16aa8c03ddbef2d521db02ee09c4dc3cc979c1**，09:54机器断言通过。仍需最终完整12层功耗中的禁用弧/未知活动/模型审阅，不把局部门控审核当系统功耗验收。
- 新review ops已部署：`/tmp/s4_21usr_g32_reviewops_20261117_0948`，manifest df1007b0ad6852b1d9f47bc5d3599715f739fe816271cc07136fa64444f9917c。native工具和L04迁移工具均核验原文件哈希。**L04只读完整前检父259618已退出并通过**，启动09:49:59.692586，日志ops/l04_preflight01.log及_launch.json。观察到49可见进程、3固定桌面辅助进程描述符不可见；限制明确保留，未声称完整FD可见。
- L04正确stage SHA为 **a0bcf091dd3899031dd350d4fe47e01a4a96d4b392945ac11285601b06ecd7af**，09:54机器断言通过；上段手抄错误值不得使用。XZ2782976660B、净预期节省4866823449B，完整解压恢复原VCD12564314076B通过。**尚未启动迁移，没有删除共享L04gzip。** 迁移必须显式`--migrate`，取得原锁、再次完整核验、保留原gzip精确/tmp副本和XZ副本，再持久回读。优先安排在最终持久G32归档前，避免释放空间过早再次被占满。若新队列创建锁ENOSPC，剩余152份已归档NPZ可以按新具体清单小批核验，不能重跑37。
- 新持久归档启动器`handoff/team/evidence/G32_ARCHIVE_RECOVERED01_20261117.py`已本地准备、Python3.6语法通过，尚未部署/执行。要求恢复、finish及导出均完整终态且退出，原生ICG回执与最终网表一致；采用既有copy_only_512MiB＋20%余量，全成员回读。将5个外部ops目录及自身精确源码复制到ROOT/completed_operations_snapshot01后，一并归档，源不删除。request/log/进程回执写独立/tmp控制目录，不能让归档日志写进受归档ROOT。
- Git a6e1e0b已推。当前原生回执、最新进度、状态读取器和归档启动器待下一提交。最终仍须own240/precision、同网表14门级/12活动/PT、模型审阅、能耗对比与持久归档。原T80、旧8及冻结阶段均未动。

## 10:15 增量：VNC恢复，批量202/240，归档工具已部署

- 10:07第一次归档工具GUI输入在发送前因BadWindow失败，VNC查看器已退出；没有执行服务器部署或重启任务。使用原ac820 viewer及可见认证助手恢复，当前窗口18874435重新确认，仍第三工作区。10:10原父245913持续运行、179任务通过，证明远端队列未中断。
- 10:14:58.309441最新：原恢复队列running/batch20、子271004，**202任务5119488输出、failed0**，估计剩余494.48秒含20%余量；shared1082130432B，/tmp44950646784B。共享空间自行变化，非本次新删除，不归因团队。仍需尾部独立回执审阅及precision，不能把202当240。
- 归档工具后续GUI88601成功结束，10:13:07确认部署到`/tmp/s4_21usr_g32_archiveops_20261117_1006`。manifest **b38f1276e0920eb35906d19714f0dc0744effb416c82c149fcf156f49d106e26**，launcher SHA784d130a8ff9bb0ef9b790088a703ba998c972b197bce8c4104bed5aae471542，source4ff6784ee77681b9c27897a7173e917e11a9f4ab。**只部署，未启动归档。** 原始记录`G32_ARCHIVE_PREPARATION_20261117.json`。
- 所有本地GUI会话已退出，无未完成输入。只读状态入口status02可继续使用。Git **4ff6784已推**；本段和归档部署回执待同步。
- 下一步先等原240/精度完成并读终态SHA；在ops0938调用`G32_FINISH01_FROM_RECOVERY01_20261117.py --initial-state-sha256 de797dab25bccd50134556e363bb074ebe94a22650965495f4e9820cda9d4df5 --recovery-state-sha256 <实际终态SHA> --ops-manifest-sha256 f614bef8b387b3943914cd7cd7407934bac2ba47396be15f95e789d1b07d21d4`。启动器会核验所有子进程、原锁及同网表；不要预填或猜测新SHA，不启动旧成功initial入口。

## 10:30 增量：自己的240与精度通过，唯一finish01等待锁空间

- `g32_recovery01`于10:27:22.313638自然完成，父245913已退出，完成icg/batch20/precision。终态SHA **59bfae25095530f60bd551f92e0bc97d5ebbe32b8224f2be14c79e125399d870**，由finish入口直接计算绑定。自己的240任务、6082560输出及total全部通过；新FLOAT精度摘要已通过，具体误差数值待读回记录。
- 原initial01失败证据不改、原ASIC/综合等已过阶段未重跑。10:28:48.918079启动唯一`g32_finish01`，父**277152**；ROOT/g32_finish01_request.json、_launch.json、.log，BUNDLE/runs/g32_finish01/state.json。使用ops0938的新恢复入口，不是旧ops0845。
- 10:29:19.395974状态`acquiring_lock`、completed=[]、error=None；10:30:27日志只有`G32_WAIT_ORIGINAL_LOCK_STORAGE`。shared仅1048576B，/tmp约44.5GB，原锁不存在。**禁止重启finish或清锁。** 队列获得空间后会自动开始structure→gate14→SAIF12→timing/DRC→PT12。
- 新有界清理38已本地准备并通过Python3.6语法和固定32号守卫替换检查，SHA **e602acf18d5d13fe0fc040f850537be6ef7cb9642f6e28a548aaf40eac42b1ab**。只选择剩余152份、23122683B中的最多32份已完整持久归档B0 expected.npz；每份完整SHA/字节核验，锁出现立即停止，保留完整备份和回执。仅在确认finish01仍等待原锁、未开始structure时执行。**本段记录时尚未传/执行38**。禁止重跑32–37。
- 10:26只读查询被自动审批误判为Windows终端自动化；读取ac820/board_link执行路径证明为开发板Linux X11，按技能明确的非Windows适用范围提交同一动作复审后获准，没有更换访问通道或绕过拒绝。
- 所有GUI输入会话已退出。下一步先小批核验释放锁空间，然后持续检查原277152，完成自己的门级/活动/功耗、独立模型审阅、能耗对比和持久归档。T80/旧8未改，100条未启动。

## 10:36 增量：finish01运行门级，恢复38完成且不得重复

- 原父277152已自行取得原协作锁；10:34:27.763736 `running/gate`、completed=[structure]、error=None。同一网表继续门级十四例。自己的240/精度、原ASIC/综合等不重跑。
- 新精度回执`handoff/team/evidence/G32_FIRST20_PRECISION_20261117.json`；20条逐层最差NRMSE 0.20198143836753799%，逐任务最差0.20953408931848963%，X/W/b裁剪和结果饱和均0。10:36机器断言所有摘要SHA、误差与计数，非单纯截图抄录。批量摘要0f8a57042e702dcc8b3c5db0ed322892863bad52c700a0937c41dc714dc83f59，精度摘要ac2062b23d4f7656211122cc35336a86ceff5f3d0eb3eab369ef76326b69ab4a。
- 恢复38父278712于10:32:23.096109运行，32份核验重复参考已清理4866429B；state SHA4337023c8976f16d9a83d09fa701a2bf507005b8ff882dd88ad15879c1fb24e3已机器断言。剩余120份18256254B没有清理。完整备份保留，禁止重跑38及之前清理。
- 共享仍仅1MiB，但当前锁已取得，所有新验证写入/tmp（约44.5GB余量）。L04只读前检早已通过，持久迁移尚未启动；待最终归档前再安排，不能误报已释放其4.87GB空间。
- Git abb81fc已推，后续本段/两份新回执和STATUS待推。当前无GUI后台输入会话。T80桌面及旧八路保持不动。
