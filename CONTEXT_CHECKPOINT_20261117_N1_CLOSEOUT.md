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
