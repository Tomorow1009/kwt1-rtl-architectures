# N1约5000吞吐版本收尾 — 2026-11-17

## 当前要求与选择

用户要求“找到之前5000吞吐左右的那一版，把它跑完”，随后明确选择 **N1：5048.64 task/s**，不是B0的4917.66，也不是桌面T80或G32。本次补齐N1原冻结版本的结果核验、持久归档和交付；只有发现原证据缺失/失败才补跑。当前不开发N2、D1、D2，不重复启动已通过的1200任务。

新独立工作树`E:/fpga_race-two/kwt1-legacy5000-20261117`，分支`codex/light-light126/legacy5000-closeout-20261117`，起点`764006f`。旧G32工作树保留，未跟踪的`S0_SYNTH05_FINISH_LAUNCH_20261115.py`未加入本工作。每次压缩前更新本文件和根CONTEXT_HANDOFF，恢复后重读AGENTS、此检查点、N1_FINAL_REVIEW、N1_STAGE_REVIEW及新执行进度。

## 已核实的本地历史证据

- 生产硬件`9305c6948c764fed01fe86b20bb3db94170299ab`；受测运行工具`0f62e41207909904efd544992013c1244b0fd63b`。
- 80PE，X14/F10、W12/F12、acc/b32、total33、SHIFT10。原32位容器、三半字偏置，原缓存和编码。
- 已有1200真实ASIC/E203任务、30,412,800个total/result/saturated零差异；ASIC14、恢复、竞争、同网表门级14（无SDF），完整12层SAIF/PT及100条浮点精度完成。
- 固定12平均29711周期、5048.635185621487 task/s；项目面积保守上界0.9511486879005002mm²；setup +0.0000510216ns，hold +0.00153732ns；SS/0.99V/125°C、6.666666ns声明任务模式。
- 时间加权整机61.7773489406039289609334365mW、12.2364442055173459727µJ/task；最大逐层NRMSE0.1933721614699203%。功耗是已审核的布局前统计模型估算，非物理签核/官方600。
- 历史最终审阅文件`workspaces/arch03/N1_FINAL_REVIEW_20261113.md`及`handoff/team/evidence/N1_STAGE_REVIEW_20261113.json`明确阶段已通过；部分早期交接页正文仍保留“待审”历史段落，不能据此误判全部未完成。
- 原最终report SHA `8f778dd1f201855ae6b0fad815e3e3b0e258a64a694fab4cc538569ee522c2e1`；模型关联snapshot SHA `b9b2af6c888a0d37144e8eb91ee98f625b3c390701116619096b558f833853ce`。23:52本次实时远端哈希核查均通过。

**历史路径限制保持披露：**N1是共享写ACK后转发，后来的T80/G32才改为原System Bus写入后真实读回。N1的5048不能作为后来四段原总线路径的性能，也不因历史数值/PPA通过自动证明最新框架合规。用户已获说明并确认选择N1；本次不擅自改硬件或计时口径来追求新成绩。

## 服务器身份及未完成工作

N1私有根`/tmp/s4_21usr_n1_20261113_0210`；OPS02=`ROOT/light-light126-n1-precisionops02-20261113_090845`。最终结果在`OPS02/final_report01/report.json`及`OPS02/model_review_1330/snapshot.json`。

三个原冻结包必须独立保留：

| 包 | manifest SHA256 |
|---|---|
| light-light126-n1-v4-20261113_045945-0f62e4120790 | 1c55d5515de4258c77537e52387809ea04a33a334a4fefee8e2600ec2b7209e0 |
| light-light126-n1-v4-20261113_013211-9305c6948c76 | 73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d |
| light-light126-n1-v4-20261113_022722-41b0846ce719 | 0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e |

11月13日archive01/02失败保留；archive03当时仅本地准备，未部署/启动。待本次实时核查后使用新目录，不重放旧launch。最终需要完整三包归档、明确名单的辅助证据归档（含OPS02最终报告/审阅/浮点来源）和恢复索引；只归档三包不能称整个N1根已保存。只复制归档，不删除N1源。实际空间和锁必须先读取，不照搬历史空闲值。

## 当前连接与工具会话

开发板已重新上电。首次启动VNC转发PID42556因缺少已有paramiko依赖路径退出；没有创建新网络通道。修正为ac820.ps1原PYTHONPATH后，现有固定目标隐藏转发助手PID31812运行，日志`takeover_local/vnc_relay_20261117_2350.log/.err`。新VNC窗口 **18874436**，workspace3第一终端；workspace4不操作，FileZilla未打开。旧18874435失效。

只读会话2161已结束并已查看截图。23:52实际核对N1原report及snapshot两个固定SHA均通过；原archive03未创建。共享盘仅1,048,576B、/tmp仅120,221,696B，原团队锁不存在。G32原队列已终态`full100_and_precision_passed_archive_pending`且PID98932退出；两个等待器当时均T状态。没有新N1仿真/EDA/归档启动。

## 其他队列与保护范围

G32 full100队列PID98932在18:05暂停时继续运行，最后本地记822/1200（以实际暂停JSON和最新终态为准）；现在可能已完成，需读取原终态，不能重复跑。G32报告等待器146858和R4 L05迁移等待器130462当时SIGSTOP，回执`/tmp/s4_21usr_g32_full100_pause_20261117_1804.json`保存PID/start_ticks。此次优先N1，不自动恢复G32报告归档。若N1归档确实需要L05已核验的无损迁移释放空间，先核对原PID身份、源/副本及锁后再处理，不能清锁或重复启动迁移。

永远不修改、移动、删除桌面`T80_Delivery_20261113`或旧八路数据。保留N1/B0/R4/G32全部冻结源码、历史失败回执与备份。已做的清理32～41、R4 L03/L04归档不重复。用户原HEX上传取消状态保留。新结果与小型交接记录可按既有授权同步团队私人GitHub；不提交厂商库、凭据或大型运行产物。

## 23:55–23:59实时进度及当前阻塞

用户已明确答复选择N1，不再等待版本确认。为N1持久归档空间，已按暂停回执逐项核对UID、脚本路径、start_ticks、T状态和脚本SHA，并且确认锁不存在后，仅SIGCONT恢复R4 L05迁移PID130462。G32报告等待器146858继续T暂停。新控制目录`/tmp/s4_21usr_n1_closeout_20261117_2355`保存`l05_resume.json`。会话68309已结束，截图`n1_l05_resume.png`确认恢复。

L05目前**仍未删除原gzip**。23:58:56检查migration.log持续`WAIT_SHARED_LOCK_STORAGE`，原锁不存在；共享盘仅1MiB导致连锁元数据都无法分配。它会每5秒重试取原锁，不得另启迁移或绕过原锁。需要先从已有持久B0完整归档中核验极少量生成重复件，释放数MiB以建立锁；不得重复清理已经不存在的32～41范围，不删除N1、桌面T80、旧八路或唯一资料。尚未选定/删除任何新文件。

23:57有界目录清点完成，回执`/tmp/s4_21usr_n1_closeout_20261117_2355/initial_inventory.json`。原`n1_runtime_archive02_1410_control/request.json`实际只登记0f62和9305两个包，不含41b：0f62共64,316文件/6,135,393,145B，9305共1,554文件/754,370,888B。原根24直接子项含41b，需另外核对其归档方案，不能把旧请求误称覆盖三包。根目录还含两个旧archive控制、failed_partial_disposal.json以及工具/精度/浮点/NumPy等辅助项，必须明确保存范围。会话33997已结束，`n1_closeout_inventory_done.png`已读；目前workspace3第一终端为空闲shell，最新VNC仍18874436，无待输入会话。

现本地`n1_archive_runtime.py`精确SHA仍8a1162f15b3e7c561c11ecc403e5a0bca806078fb47ee080374ff678f7cfb5db，`n1_paths.py`为fe301e1e5f87852103c537b8191c7064f1b8c44a8979f1977901bf26ed16e39d；auxiliary当前LF字节与旧CRLF部署SHA不同，不能直接冒用旧SHA。后续在新外部工具目录部署，禁止改三个冻结包。原归档工具保留20%压缩体积余量+2GiB，先算实际体积再决定是否需要沿用已验证的512MiB仅复制策略；未做修改、未盲启大归档。

## 11月18日00:02–00:16续作

已重读AGENTS、交接、N1最终审阅和归档范围计划。00:02只读清点原B0完整归档中仍存在的批量文件7378份、23,786,434B；没有选择删除生成模型`standard_cells.v`或任何源码。随后限定为已持久完整归档的1200份逐任务`task.log`，共2,759,700B，保留compile.log、summary、源、网表及全部完整备份。原完整B0备份SHA仍按已保存常量核对。

新脚本`handoff/team/evidence/N1_ARCHIVE_BOOTSTRAP_20261118.py`，SHA `815a035a4d8f99d61f2a69cde86544d66712dbc6370d0b47c894de7e05ad908f`，语法检查通过，00:12经VNC启动PID **80971**，服务器路径`/tmp/s4_21usr_n1_closeout_20261117_2355/bootstrap42.py`，日志同名`.log`，启动回执`.launch.json`。先重新核对完整归档哈希、逐个成员解压内容和当前原件，再检查无EDA/占用/锁；仅在确认R4 L05仍等待锁时短暂停止同一PID、删除上述归档重复日志，记录逐文件journal，最后恢复同一迁移。没有删备份、N1、T80、旧八路。00:13日志尚无输出，仍在核验，L05仍waiting_for_team_lock、source_deleted=false；共享1MiB、tmp107405312B。**还没有观察到清理或迁移完成，不能提前记录成功。**

本地命令初次含CRLF被板端输入后端拒绝（未输入任何字符）；去掉CR后部署完成。今后VNC文本明确移除CR并保留末尾LF。

辅助归档白名单新增实际观察到的5项（两个旧归档控制目录、a02/fe65旧工具、failed_partial_disposal.json），共21项覆盖根24子项除3包以外全部已知内容。原辅助归档17项测试通过；工具新SHA `38841293029d4b59354ef596465ce0bd32f9022bde54cd848e2ab1e8d1271845`。原runtime/path工具不变。部署脚本`takeover_local/n1_tools_0015_deploy.py/.txt`把已核验旧工具增量重建到控制目录下`tools-20261118_0015`，仅创建新文件；新请求加入41b包、两个实际inventory SHA、保留原队列request绑定。目标新持久目录分别为`backups/n1-runtime-20261118_0015`和`operations/n1-aux-archive-20261118_0015`。

**最后操作：**VNC输入会话57095仍在逐段输入部署命令，必须用write_stdin收完并截图确认后才再输入。部署仅核对终态/名单并生成请求，没有启动归档。新工具/请求是否完全创建以最后输出为准。所有N1源保持原样；G32 finisher146858继续暂停，不自动恢复。

## 00:16–00:22已观察到的完成与新启动

57095和后续71712均已结束并截图。工具部署实际通过：三包49条原终态记录、根24子项完整匹配（三包加21辅助项）。原runtime请求SHA `6aa79be2948fa3a5468b7078eff6013ae7b8b47328cce6ddbbeac2b363b760da`；aux请求SHA `de9e314894e9d6c9eb7990240b2453ed77e3a24a4e9f127ff463147e2fd2be45`。

bootstrap42已完成：1200份B0已备份逐任务日志重复件、2,759,700B删除；完整归档、summary、compile.log、源、网表保留。回执`bootstrap42/state.json`SHA `62c6fd59a0e9ec7cfaef1393ac4511dbf951da61d391787c93dc4ccff5764693`，删除后共享空闲4194304B，已恢复原L05进程。PID80971退出。它没有修改N1、T80、旧八路。

00:19:45原R4 L05无损迁移已完成：`durable_xz_verified_original_gzip_copy_retained`，完整解压回读true。新持久XZ 2,709,005,716B；回执`PROJECT/backups/r4-l05-xz-20261117/receipt.json`SHA `5a661ac0fce451fa51c2c2f50ad6e7f6ca2ca2f117038c5ad2b8218e91b46491`。原共享gzip重复件已删除，精确gzip和XZ暂存副本仍保留；旧JSON不动。实时空闲约4.39GB，锁已释放。

第一次N1归档驱动`archive_driver.py`SHA `1f0d0fe439a3d45a1dddb3c09fcee2081872e68187b81386e0f88e572b667f81`、PID83982在**写入任何归档之前**因截图aux请求SHA转录错误触发assert并退出；日志保留，无`archive_state.json`。重新单独显示完整SHA后已修正本地`N1_CLOSEOUT_ARCHIVE_20261118.py`，SHA `914c74d55f87b3284661d37beed9cf01758485484e8788cd0d98af27d724607e`。第二次只新建`archive_driver02.py/.log/.launch.json`，不覆盖失败文件，先21项辅助plan→identities→归档，后完整三包归档；仍保留20%+2GiB，源不删除。

**最后输入会话67651仍需收尾并截图确认PID及启动结果。** 当前尚未观察到N1任何归档verified。新状态在控制根`archive_state.json`，日志`archive_driver02.log`。本地新中文收尾说明`workspaces/arch03/N1_CLOSEOUT_20261118.md`明确把归档目标标为计划路径，不能在完成前宣称已备份。

## 00:22–00:31：辅助归档完成、完整包容量重试

67651已完成；第二次驱动PID85162实际启动。**辅助归档已verified**：21项、1069成员（170目录/899普通文件/0链接）、源901,602,670B；持久压缩包709,504,053B。目录`PROJECT/operations/n1-aux-archive-20261118_0015`，archive SHA `387cfa890876ebed24754aed1692d6cfeb099402d11f485f5160ae554c9139ca`，receipt SHA `33993d020103fc642b9d07168bea4d5e3359fcf2ae7b5487e7180e71faa23042`。完整成员回读、源前后核对已通过。最终报告/精度来源/审阅资料已有持久副本；不要重跑辅助归档。

完整三包清点74,538成员、7,137,788,745B。精确gzip计数接近1.4GB；00:25第二次驱动在**创建归档目标之前**因`1.2×压缩体积+2GiB`空间前置条件失败，完整包尚未写入，原`backups/n1-runtime-20261118_0015`不存在。保留`archive_driver02.log`及`archive_state.json`，该状态中的auxiliary仍是verified。共享空间当时3,704,673,280B，不能把这次失败写为N1硬件失败。

已在独立工具副本采用显式**1.5GiB储备+20%压缩体积余量**；仅改变RESERVE常量和错误提示，完整SHA、前后树核对、解压回读以及保留原件均不变，不扩大清理。新helper派生SHA `710b186dde6c9a048a7064e88482eac8e4de3b3f8c0ff5943d72709c6da1c05b`，目录控制根`tools-20261118_0030-reserve1536`，记录`capacity_profile.json`。

第三次运行脚本`N1_CLOSEOUT_ARCHIVE_RETRY03_20261118.py`SHA `ab5d885b220aefb4b2316a4e3ce3aaae198b06d933681307abf8f527dd6ad340`，服务端`archive_driver03.py`，PID **89126**（00:30:37截图确认）。仅重试三包，使用新`runtime_request03.json`和`archive_state03.json`，原失败状态不覆盖。新完整包目标为`PROJECT/backups/n1-runtime-20261118_0030`。尚未观察到最终verified。

已同步私人GitHub个人分支提交 **ac1343c**，包含N1已有结论、小型交接和归档工具，不含厂商库/大型数据。后续变化待下一次同步。

交付索引工具本地`handoff/team/evidence/N1_CLOSEOUT_PUBLISH_20261118.py`SHA `a55e71eb657ddfc33b9bcfece3d1e75cf42b5aad75ea544ccd06f30396313ce1`；要求`archive_state03.json`中两档均verified才可执行。它拟在`PROJECT/operations/n1-closeout-20261118_0030`新建可读目录，原JSON/CSV、审核附录、原综合网表/报告、五个关键RTL及两档恢复索引，不改T80。原审阅文件payload SHA `fab93fd3b85370b23fa629635ff4701ba5fc067ff9cebf92fd94afc7f2b1a35d`。

**最后操作：VNC输入会话89104仍在部署publish.py和review_payload.json，约12KB命令；必须先收尾并截图。只部署，不会自行运行publish。** 当前窗口18874436/workspace3第一终端，禁止并行输入；归档89126后台继续。下一步查看archive_driver03.log/state03，等待实际verified后运行publish.py，核对receipt/文件集合，更新中文说明和STATUS并同步GitHub。G32 finisher146858仍暂停；N1/T80/旧八路源没有改动。

## 00:34–00:44：共享空间持续减少；当前恢复入口

89104已结束，publish.py及review_payload.json哈希均在屏幕核对成功，**未执行publish**。随后归档第三次89126又因1.5GiB+20%空间前置失败，仍发生在创建目标之前；`archive_state03.json`为failed_preserved。共享空闲从3.70GB降至1.72GB（00:34），再到1.42GB（00:36）、915406848B（00:40）。我方除709MB辅助归档外没有这些新增共享写入，不能臆测具体占用者。不能继续降低储备并盲重跑。

00:36只读检查完整B0归档对应的其余现存文件：1646项/395,915,288B，不足恢复空间；**未删除这些综合中间产物**。没有删除standard_cells.v、mapped.v、DDC或这些综合报告。现改为已有授权范围内的无损R4压缩迁移，先清理真正已持久保存的/tmp压缩重复件，保留原gzip及持久XZ。

已实际读取：R4 L04持久XZ 2,782,976,660B，receipt SHA `c6962b18892f8bd0b3561224c2e8219ebbd2e791305e90a797a502fb7593d053`；L05持久XZ 2,709,005,716B，receipt SHA仍`5a661ac0fce451fa51c2c2f50ad6e7f6ca2ca2f117038c5ad2b8218e91b46491`。两者均full_durable_readback_verified=true，分别/tmp暂存根的layer_04.vcd.xz、layer_05.vcd.xz仍存在；拟仅在压缩字节SHA/长度及无人使用检查后删除这两份临时重复件，共5,491,982,376B，不删除精确原gzip暂存副本或任何共享备份。

R4 L06既有共享source在`PROJECT/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02/layer_06.vcd.gz`，gzip7,430,640,268B、原VCD12,210,217,662B；原receipt SHA `2e2e38a866a0b90978b1379018e2bd762a0673b7c7b4beb2c353d9d0f38383579`，原状态lossless_archived_raw_removed。**L06共享原件目前没有删除或修改。**

新准备脚本`handoff/team/evidence/N1_R4_L06_STORAGE_STAGE_20261118.py` SHA `273cd25e0684afc6afeeecc017522fec85f3468724238f60d7e8022f3e111e20`，只删除上述两份已验证/tmp重复XZ，再把L06原gzip无损转为新/tmp XZ，preset0、单CPU低优先级、512MiB储备、4GiB输出上限；全量gzip压缩字节核对、raw SHA/字节核对及独立XZ解压回读，原shared gzip保留。工具持原团队锁，不清旧锁。此阶段**不做L06共享迁移**；须观察完整staging终态后再实施迁移。

服务端部署到控制根`l06_stage.py/.log/.launch.json`；状态根`/tmp/s4_21usr_n1_r4_l06_stage_20261118/state.json`。**最后输入会话86682仍在部署约5KB命令，须先write_stdin结束并截图确认PID，不并行发GUI输入。** 新脚本先核对大文件，未观察到任何新增清理或L06压缩完成，不能提前写成功。

下一步：1）核实L06暂存进程/进度，保持G32 finisher146858暂停；2）完整暂存通过后，在新持久目录完成R4 L06无损迁移并保留所有回执，确保原raw VCD可完整恢复；3）有足够共享空间后，以新尝试目录重启**仅N1完整三包**归档，勿重跑已verified辅助档；4）当前publish.py仍硬绑failed的archive_state03.json，最终新尝试通过后需新建publish02.py明确绑定新状态，不能直接运行旧publish.py；5）发布独立N1结果目录，更新计划/检查点/STATUS并同步。尚无N1完整三包持久归档，辅助归档与已完成硬件结果均有效。

## 00:47–01:07：当前实际是L06 preset3新暂存

第一份l06_stage.py（PID95939）在任何删除/创建OUT前因**L06回执SHA转录多出一位**失败，日志保留。已用8位分组逐字符核对：正确SHA为`2e2e38a866a0b90978b1379018e2bd762a0673b7c7b4beb2c353d9d0f3838359`（64位）；上文以`...83579`结尾的65位是历史错误，不再使用。L04/L05固定回执SHA核对无差异。

第二份`l06_stage02.py`SHA `df134866251d2d8747dd5faf3844beba379fa20d2bf39f2f8999c2c6249eb5fe`，PID99444，00:52截图确认启动。因共享盘再次只有1MiB，改为**共享盘只读暂存流程**，不创建/绕过共享锁；清理/tmp重复件前仍确认无原锁、无EDA及无占用。这与历史只读XZ staging做法一致，正式迁移与N1归档仍必须持原共享锁。

00:54实测：两份/tmp L04/L05 XZ重复件**已核验并删除**，合计5,491,982,376B；其共享持久XZ、原gzip暂存及全部回执均保留。状态在`/tmp/s4_21usr_n1_r4_l06_stage_20261118/state.json`，`duplicate_removal.jsonl`保留清理记录。原L06共享gzip仍完整不动。

preset0实测压缩率偏低：01:00 raw5,368,709,120B→XZ2,115,837,438B，用时461.10s，预计完整输出会超4GiB上限。相比历史preset3，L04压缩2014.50s、L05压缩2066.79s，输出约2.7GB。已核对99444的UID、命令、脚本SHA后仅SIGINT此进程，保存`控制根/l06_stage02_stop.json`（含start_ticks、停止前状态及原因）；01:05截图确认发出中断。没有停止其他任务、没有删除L06共享原件。

新方案用已实际验证的**preset3**，估计压缩约35分钟，再加独立回读。新脚本`N1_R4_L06_RESTAGE_20261118.py` SHA `5cc9d3d7d3992e00768071d490de3e65e681fa6deaf08df8f8afcc37f90ae772`。先确认旧阶段failed且99444退出，再完整重核原gzip、记录未验收preset0临时输出的SHA/大小，**仅删除该本次失败派生文件**，保留旧state/日志/停止回执；随后写新`/tmp/s4_21usr_n1_r4_l06_stage03_20261118`，不重复删除L04/L05副本。仍512MiB储备、4GiB输出上限、源只读、full raw SHA和独立XZ回读。服务端新文件`控制根/l06_restage03.py/.log/.launch.json`。本地语法及新脚本全部长SHA长度检查通过。

**最后输入会话36831仍在部署并启动preset3；必须write_stdin结束、截图确认PID和启动结果后才输入。** 尚未观察新preset3的压缩进度或最终verified。上一个VNC会话17402已结束，旧后续工具部署成功但未执行。

后续迁移工具已准备：本地`N1_R4_L06_STORAGE_MIGRATE_20261118.py`和`N1_L06_LOCK_SPACE_20261118.py`。旧服务端`l06_migrate.py`SHA baf2ff710439219a29df878a60c75be6e23d8bc160caac2e3a2f33271e1eccd0、`l06_lock_space.py`SHA4061db531be01f941abb3751c652b9e8f6ff12208ad7b3c1cf556424aef9a3f5绑定旧stage，**不要执行**。本地已改为新stage03路径和新source_script SHA，需部署新`l06_migrate02.py`、`l06_lock_space02.py`并记录新SHA。

迁移前需完整preset3终态、固定SHA及原PID退出；迁移会先取原锁再做大文件核验，避免核验期间空间被占。若锁元数据仍无法写入，条件bootstrap只考虑**一个**已在不变B0完整归档内的`.../systolic_b_v3_drc06/systolic_b_synth/hierarchy.rpt`重复报告（约7.85MB），共享空闲≥16MiB则不清理；必须重新核完整备份SHA和原完整回读证明、当前文件SHA及无人使用，再删该重复件并立即调用迁移。**这个hierarchy.rpt目前未删除，bootstrap尚未执行。** 原库/RTL/网表/T80/旧八路/N1不在范围。

L06迁移保留完整暂存XZ、原JSON与全raw VCD内容；此次没有额外精确gzip容器副本，旧gzip容器字节不会保留，恢复的是原始VCD逐字节内容。迁移新目标仍`PROJECT/backups/r4-l06-xz-20261118`，不得改旧回执。完成空间恢复后再用新attempt04归档N1三个包，建议显式512MiB储备+20%余量（既有复制归档原则，完整回读不减），记录配置；不要重复已verified的709MB辅助档。尚未编写/启动attempt04。

私人GitHub已推送 **cca5844**。01:05后的最新stage修复、restage及迁移准备尚待下一次提交同步。本地归档结果说明仍如实标明完整三包未持久化，N1数值/精度/PPA已完成。

## 01:14最新恢复锚点（覆盖上文旧“正在输入”状态）

- 所有VNC输入会话36831、42077、57747已结束并截图；现在workspace3第一终端空闲，无待输入PTY。窗口仍18874436。
- **实际后台任务只有L06 preset3暂存 PID107226**（本任务范围；G32 finisher146858仍T暂停）。脚本`控制根/l06_restage03.py` SHA `5cc9d3d7d3992e00768071d490de3e65e681fa6deaf08df8f8afcc37f90ae772`；状态`/tmp/s4_21usr_n1_r4_l06_stage03_20261118/state.json`。01:14:46读取：`compressing_l06_xz`，raw2,147,483,648B、XZ451,314,814B、elapsed323.10s，未见错误。预计整段约30–35分钟，之后独立回读；不能提前写staging verified。
- 旧preset0 PID99444已退出、state为failed_preserved；新restage已记录并清理它从未验收的临时XZ派生文件（原shared gzip完整重核，旧日志/state/stop回执保留），开始新文件。没有删除L06共享gzip。
- 新后续工具已部署且逐个SHA与本地一致，**尚未执行**：
  - `l06_migrate02.py`：`ec229f8eeefd470f79aa70f3b20b7584449b8cd4d8e71ae1cd4cdafca7f17637`
  - `l06_lock_space02.py`：`50e13e5a500b664399f1423f31158d3892f279fc6e7165468976fd069beb6396`
  - `archive_driver04.py`：`573111a43084771dfaddb52f23735be0801c02786fb98a641d5479a38ec771d3`
  - `publish02.py`：`667a87b440ffd6bab771903c548cca3899939f0d9aec0bc268ecea0d190aedb2`
- 待preset3真正完成且PID退出，计算其state SHA并以CLI传给`l06_lock_space02.py --stage-sha256 <实际SHA> --migration-sha256 ec229...`。该入口必要时仅清理一个已完整备份的B0 hierarchy.rpt重复件，立即调用已核验迁移（先取锁再读大文件）；空间足则不清。输出控制`控制根/lock_space43`与`控制根/l06_migrate01`。不要用旧无02后缀迁移工具。
- L06共享迁移完整回读通过、进程退出、原锁释放后，才启动`archive_driver04.py`，新状态`控制根/archive_state04.json`，新完整三包持久目标`PROJECT/backups/n1-runtime-20261118_0110`。显式512MiB储备+20%余量，打印精确预算，原来源和所有回读检查保留；只归档三包，不重做已verified辅助档。
- 两档均verified后运行`publish02.py 控制根/review_payload.json fab93fd3b85370b23fa629635ff4701ba5fc067ff9cebf92fd94afc7f2b1a35d`。新可读结果目标`PROJECT/operations/n1-closeout-20261118_0110`。旧publish.py绑定失败state03，不能使用。
- 交付只读预检已确认：原综合实际在`N1ROOT/light-light126-n1-v4-20261113_013211-9305c6948c76/runs/n1_synth01/n1_synth`；待复制网表/报告14份49,265,092B，符合64MiB限额。mapped.v 31,806,243B，原文件不修改；完整源/固件/活动仍以三包归档为准。
- 所有新增本地脚本已做语法和64位SHA字面值长度检查；辅助归档17测试此前已通过。没有新硬件、综合或功耗作业。桌面T80、旧八路、N1冻结源不动。需要继续跟踪当前压缩，而不是重复启动任何旧作业。

## 01:34恢复记录

07d961f已推送私人GitHub个人分支。01:33:41再次只读观察L06 preset3 PID107226仍运行，raw 10,200,547,328/12,210,217,662B，XZ 2,196,067,903B，elapsed 1554.24s，未见错误。原L06 shared gzip仍保留。锁空间入口/migration02、runtime04和publish02均未启动；本地三个专用launch文本语法检查通过，仅待实际前置终态。辅助归档不重做，G32 finisher不恢复。当前workspace3终端空闲，没有待收尾输入会话。

## 01:45：L06暂存全部通过，迁移已启动

01:43:47实际读取stage03终态为fully_verified_staging_original_retained，full_xz_readback_verified=true，PID107226已退出。XZ 2,631,843,264B，压缩1866.9129s，原raw 12,210,217,662B完整SHA与长度一致。stage state SHA `6fe2a6daf8eff0c99a386677111ab3227e9784986ad1ec507e55ddf89b824702`。

01:44已执行已部署的l06_lock_space02.py，PID **127013**，原migration02身份及stage完整终态在启动时核对。日志`/tmp/s4_21usr_n1_closeout_20261117_2355/l06_lock_space02.log`，launch同名`.launch.json`。VNC会话63072已结束且截图确认PID。尚未观察迁移终态或原gzip删除，不能提前称空间恢复。下一步读取lock_space43/state.json、l06_migrate01/state.json及日志；进程正常则等待，不重启。migration verified、PID退出、锁释放后启动准备好的runtime04，之后publish02。

## 01:53：持久迁移通过，N1完整归档运行中

01:52:23已观察R4 L06迁移为durable_xz_verified_staged_xz_retained，full_durable_readback_verified=true，PID127013退出且原锁释放。共享XZ保留原12,210,217,662B原始VCD内容，暂存XZ仍保留；旧gzip容器已删，原JSON保留。持久receipt SHA `6843c87c3a810be7b9d7a36f66e9354ee5c20a0f9867179be301f5f05802c231`；迁移记录空闲4,371,513,344B，读屏时4,173,332,480B。lock_space43只删除1份已完整B0归档的hierarchy.rpt重复件，没有删源码、网表、N1、T80或旧八路。

01:53截图确认 **N1 runtime04 PID133407** 启动。日志`控制根/archive_driver04.log`、状态`控制根/archive_state04.json`，目标`PROJECT/backups/n1-runtime-20261118_0110`。新工具只改变容量储备并打印精确预算，保留完整成员回读和全部源；不重复辅助归档。VNC输入会话80241结束，终端空闲。下一步观察归档终态，不能重启/再次运行同一launch；通过后运行publish02并核对实际文件/receipt。


## 02:03最终锚点：本次N1收尾全部完成

- runtime04已成功：`both_archives_verified_original_sources_retained`，三包74,538成员（70,263普通文件、4,271目录、4链接文字），源7,137,788,745B，完整压缩包1,392,335,721B。逐成员解压回读与原件前后内容/元数据核对均通过，全部N1原件保留。
- 完整三包目录`PROJECT/backups/n1-runtime-20261118_0110`，archive SHA `a871a13520dcf48d697f9ebe190961c327c7ef1ba0dbd7e89cf0ed7b09a77351`，receipt SHA `1c5967498464e1cbe3f0beefa1b632fdcd03e176d86753ea15651a12e402e51d`。已verified辅助档保持原样，不重复跑。
- publish02实际PID133262已完成，发布到`PROJECT/operations/n1-closeout-20261118_0110`。27份文件包括五个关键RTL、原综合网表/报告、原JSON/CSV和最终审阅附录；README/closeout.json/receipt.json提供入口及全部恢复索引。
- 交付closeout SHA `403096198ca6f86edb4a516b7a0133a99af9ced2d993db963e8b9027a4467c68`；receipt SHA `b58dc446147231ae5e5104584c73cd6d94472d412db44e23efb46adbd62efed9`。
- 首次只读交付核对因本地读屏转录receipt SHA两处字符错误而assert；原服务器文件未变。随后按8字符分组重新读取并纠正本地索引，**02:02:46独立核对27份文件字节/内容、closeout/README和两份归档回执全部PASS**，runtime source identical=true。不得把转录错误写成硬件或归档失效。
- 同一观察确认107226/127013/133407/133262全部退出、原团队锁不存在；G32 finisher146858仍T暂停。所有VNC输入会话77132/65918已结束，当前workspace3第一终端空闲。不要再次启动任何closeout launch；没有本轮待跑硬件任务。
- 本轮硬件/精度/PPA沿用哈希一致的原完整N1验收，未重复1200、综合或活动。用户要求的N1（5048.64）备份及结果交付已完成；没有进入N2/D1/D2/G32。桌面T80、旧八路、N1冻结源均未修改。
- 最终中文说明`workspaces/arch03/N1_CLOSEOUT_20261118.md`，机器索引`handoff/team/evidence/N1_CLOSEOUT_RECEIPT_20261118.json`及STATUS已更新，下一步仅提交/推送这些小型完成记录，然后向用户交付实际地址。原N1_FINAL_REVIEW与N1_STAGE_REVIEW保留11月13日历史原文/哈希，其当时“备份待完成”由本次独立索引补充，不反向改写。
