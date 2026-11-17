# G32完整100条追加验证：2026-11-17

**当前状态（17:30:03最新任务观察）：full100_02/PID98932正常运行，625/1200任务通过、15,840,000输出和total、0失败，余量20%的剩余估计7,474秒。独立L05迁移PID130462仍在waiting_for_team_lock，尚未迁移或删除共享gzip。收尾等待器PID146858存活且waiting_existing_queue，尚未生成报告或归档。GUI输入会话29076已结束；workspace3第一终端运行全流程前台只读监视器，每50秒刷新，无shell提示符。如需输入先Ctrl-C只停止显示并确认提示符，后台G32始终保留。当前没有新硬件任务。**

## 当前授权与目标

用户已经明确批准“追加完整100条回归”，取代上一冻结检查点中“等待批准”的待办。以冻结G32完成100条×12层=1200个真实ASIC/E203任务，逐项检查30,412,800个输出及signed33 total，并汇总同批完整浮点精度。预计约4–5小时，以实际宿主进度更新。

工程`E:/fpga_race-two/kwt1-c32-g32-20261115`；个人分支`codex/light-light126/t80-pipeline-c32-g32-20261115`；开始时HEAD `fa345a4dace48a6421cf9c98d80750a57d9d8278`。有效计划仍为`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，本次仅扩展最终G32数据规模，不再改变硬件或重跑PPA。

## 已完成、未完成与尝试路径

S0/P80/C80/C32-A/G32全部完成并冻结，详细证据见`CONTEXT_CHECKPOINT_20261117_G32_FROZEN.md`和`workspaces/arch03/FINAL_ROUTE_REPORT_20261117.md`。生产硬件为`0e16994675bb15e53642017a88f6307da9af4a01`，最终发布提交`ffa5dd1f7228a9b85a8d5a003d7b0ce64ab419dd`，tag `arch03-g32-final-20261117`不移动。

已有G32自身240任务/6,082,560输出和total零失败、ASIC14、CPU恢复竞争、最终门级14、SAIF12/PT12、面积时序和独立模型审核。固定12任务平均72179.33333333333周期、2078.1571825730357task/s、面积保守上界0.727972347099813mm²、布局前42.7882486498mW和20.5895130213µJ/task。这组PPA平均不得被100条回归均值替换。

本次开始时已读取计划、AGENTS、团队同步说明和冻结检查点。发现`g32_batch.py`明确限制240任务，随后新增独立100条入口；不能直接把旧PASS扩展为1200。历史原G32/恢复/finish/export/归档作业均已退出（13:33旧观察）。新的实时预检、失败启动及成功full100_02均记录在下文，不能把本段历史状态当作未启动。

## 数据与运行隔离

数据为服务器`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all`，100条/1200层/4800HEX，库存SHA `ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997`。浮点包`/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip`，SHA `5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2`。保留布局0x00100006、数值0x000e0c20、SHIFT10、32PE、实际共享写ACK再读回、最终写ACK及排空边界。

原G32根`/tmp/s4_21usr_g32_20261117_0810`及持久归档全部保留，不在该根新增运行。使用新/tmp独立根和新运行目录，一次编译，不采大波形；正式作业持有原`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`。先核实工具、数据、冻结源码身份、空间和锁，再开始。不同批次证据分别记录。

## 禁止与恢复入口

桌面`T80_Delivery_20261113`、旧八路及所有历史冻结证据禁止修改、移动或删除。清理32～40、R4 L03/L04归档已经完成，禁止重复执行。禁止恢复旧失败队列、删除协作锁、改写冻结包/tag；不提交大文件、厂商库或凭据。原未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不暂存、不运行。

15:19:28服务器实时预检：协作锁不存在，无我方EDA作业；/tmp可用40,738,131,968B，共享盘仅1,048,576B。VNC窗口18874435、workspace3第一终端。已新增独立`g32_full100_batch.py`、`g32_full100_float.py`、`g32_full100_precision_join.py`、`g32_full100_queue.py`，原工具不变。6项范围/拒绝测试及Python3.6语法检查通过；硬件/tb/sw无差异。新队列复制原manifest全部文件，要求所有原文件逐字节一致，仅允许追加4个100条工具；正式作业先建立固定NumPy运行时，再取原协作锁，一次编译1200任务后执行浮点复算与逐项连接。

## 部署及首次空间失败

工具提交`398a58b`已经推送。新运行根`/tmp/s4_21usr_g32_20261117_1530`，新包`light-light126-g32-full100-398a58b`；逐字节复制冻结包1059文件，仅新增4个100条工具。manifest `1577690aba585e473c7d0174ebca95618edc032e1184cf99a6d350bfa75d9052`；request `e260f5fc1b4f2a4b1c475f711f4d046a42b83e766040519892e3bfccab7bbfd1`。

15:27启动的full100_01/PID95634在创建原共享协作锁时返回ENOSPC，状态failed且已退出；未启动编译/仿真。失败目录和日志保留，不原地续跑。

15:31只读核查显示，旧B0完整1200批次还剩9份task.csv（2,898,594B），全部已收录在保留的完整持久备份；没有剩余编译.o/.so重复件。准备按此前清理授权逐项核验这些CSV及归档、确认无人使用，再删除重复原件并立即新建full100_02。脚本`handoff/team/evidence/G32_FULL100_LOCK_SPACE41_20261117.py`，SHA `8cf30d12c3c70a35761c5d6edcc17d114f00202e14424684778d2a1eb2083bfd`；不触及旧八路、桌面T80、任何日志/源码/网表/备份。当前脚本部署中，不能把准备状态标成清理已完成或回归已运行。

15:35:45已观察：space41完成，9份/2,898,594B已核验重复CSV删除、完整归档保留；state SHA `7f1b6d4bddcd3fcb7253bddf737d3934e1d322f312d09a704395cfbc2dbb7f45`。新full100_02驱动PID **98932**，开始时间15:35:05.461864，状态running、stage=batch100；尚未读取首任务回执。队列在新包`runs/full100_02`；批量在`runs/full100_02_batch100/g32_batch100`，后续精度在`runs/full100_02_precision100/g32_precision100`；驱动日志为新根`full100_02_driver.log`。只监控该队列，不重启full100_01，不重复清理41。共享盘仍约1MiB空余，/tmp约40GB；当前锁已成功建立，正式输出写/tmp。

下一步：持续检查1200进度及浮点汇总→准备完成后的持久归档空间→归档新证据、同步结果。未完成不得写PASS。共享盘归档空间需重新核实，不盲目向满盘写大文件。压缩前更新本文件及根CONTEXT_HANDOFF，恢复后重读有效计划、STATUS和检查点。

## 15:47进展与并行准备

full100_02自身55/1200任务、1,393,920输出和total通过，0失败；宿主已用599秒，余量20%的剩余估计14,959秒，预计约20:00完成批量（精度/归档随后）。不要重跑已有任务或重启队列。源码及运行入口至`f720769`已推送。

R4 L05只读无损副本准备已启动，PID106440；源为旧B0包`runs/r4_waves_lossless_archive02/layer_05.vcd.gz`，7,577,667,982B，对应原始VCD12,447,866,354B。新/tmp根`/tmp/s4_21usr_r4_l05_xzstage_20261117`，控制目录`/tmp/s4_21usr_g32_l05_storageops_20261117`。源码`handoff/team/evidence/G32_FULL100_R4_L05_XZ_STAGE_20261117.py`，SHA `13381ac32bb9bfe64fa9452154cb610f0028f394b140d3931bf17908c3bdc6e8`。15:47状态compressing_xz，gzip副本已完整核验，已处理1,342,177,280个原始字节、约217.6秒。低优先级nice+15，/tmp保留14GiB余量；共享源和收据未改，尚未启动持久迁移、未删除gzip。完成后须独立全解压回读；只有原G32验证释放锁后，才准备单独迁移，不能沿用L04脚本直接操作L05。

本地新增但尚未部署：`g32_full100_archive.py`、`g32_full100_archive_contract.py`，复用既有tar写入、完整回读和容量策略，新增完整1200/精度/1201子进程退出及原失败记录检查；4项范围拒绝测试和Python3.6语法通过。后续作为外部归档工具部署，**不能把它们追加到正在运行的冻结生产包**，也不能重跑最初glob打包脚本（该脚本原来只包含4个执行工具）。准备报告/归档仍是本轮待办，不把归档准备说成验收完成。

15:56本地又补充`g32_full100_report.py`，在完整验收后导出1200行CSV、逐层CSV、JSON和中文说明；固定12任务旧PPA明确单独引用，不与100条周期混算能耗。运行/归档/报告共13项范围与数值汇总测试通过，所有新增工具Python3.6语法通过。报告及L05迁移准备提交`9940681`已推送。L05迁移工具`G32_FULL100_R4_L05_XZ_MIGRATE_20261117.py`已在本地生成、SHA `3160a0a4a2e240d10f2f2884d4a3c37233244175ff6d50a6fe1f7080afa5d4e7`，尚未部署/执行；须先等无损副本完整回读通过，并等当前G32队列释放原协作锁，才可迁移。

收尾工具已部署并核验到`/tmp/s4_21usr_g32_full100_ops_20261117_1605`，包内只有`g32_full100_archive.py`、`g32_full100_archive_contract.py`、`g32_full100_report.py`和原G32结论的精确副本`G32_BASELINE_CONCLUSION.json`。操作包manifest实际SHA `331f238efe8150ca9a8ade11439f4185658c35d88f320192dddedc2264322941`。首次import发现旧生产包早于`g32_archive_capacity.py`，已在独立`/tmp/s4_21usr_g32_full100_deps_20261117_1610`补齐该已核验模块，模块SHA `2b591b8f32b583f03b11720d87b5029c64229bb56dc6fe4a86572512b504efcf`；16:09服务器实际import通过。**运行收尾工具时PYTHONPATH顺序：ops目录、deps目录、新生产包workspaces/arch03/scripts**，使用`python3 -B`避免改写源。记录见`G32_FULL100_POSTTOOLS_20261117.json`。

本地ASCII部署命令`E:/fpga_race-two/takeover_local/g32_full100_posttools_command.txt`及`g32_full100_dependencies_command.txt`均已执行，禁止重复创建。生产包未补文件、manifest未变。报告/归档请求需绑定最终full100_02 state SHA；等待全部1200、精度以及驱动/1201个子进程退出后再运行。报告需要baseline参数指向ops中的`G32_BASELINE_CONCLUSION.json`，output指向新运行根的一个新目录（例如`full100_export01`），不能写入旧冻结G32根。归档使用原共享锁、完整成员回读和1.2倍体积+512MiB容量策略；保留源，不改冻结tag。归档前还需将ops/deps及收尾请求/终态的精确副本保存到新运行根的独立snapshot目录，使它们进入完整持久备份；不要在归档开始后继续写该源根。

## 16:30归档空间准备

L05 staging完整回读通过且worker已退出，state SHA `988d3fee1d0a6064b10cc551c05d4b5cc2c302cfc45a060ffecaf2abd63657e4`。XZ为2,709,005,716B，相比原gzip预计净省4,868,662,266B；原gzip精确副本仍留在/tmp。独立迁移PID130462，控制入口`/tmp/s4_21usr_g32_l05_migrateops_20261117`，状态目录`/tmp/s4_21usr_r4_l05_xzmigrate01_20261117`。它等待G32释放原锁后再重新核验、迁移到`backups/r4-l05-xz-20261117`并全解压回读；当前尚未观察迁移完成，不重复启动、不清锁。记录见`handoff/team/evidence/G32_FULL100_L05_STORAGE_20261117.json`。

## 17:07收尾等待器已启动

新增串行收尾脚本`handoff/team/evidence/G32_FULL100_FINISH_20261117.py`已提交并推送`21da316`；SHA `b81754108f841acbd5848fac9806dc4119603d684b9dd6214be917a5e69ff6de`。它在`/tmp/s4_21usr_g32_full100_finishops_20261117_1705/finish.py --wait`运行，PID146858，launch.json和finish.log同目录。当前只等待精确full100_02/PID98932完成，不启动新硬件、不改生产包。

全部1200及浮点连接成功且驱动退出后，收尾脚本才创建`/tmp/s4_21usr_g32_full100_finish01_20261117/state.json`及request.json，绑定最终队列SHA。调用已验证外部报告器生成`/tmp/s4_21usr_g32_20261117_1530/full100_export01`；等L05持久迁移完成并退出后，将精确收尾工具、依赖、请求、L05回执保存到`closure_snapshot01`，然后通过既有归档器复制完整新运行根。归档目标为原backups下新的`g32-runtime-YYYYMMDD_HHMM-full10001`，实际值记录在收尾state中。完整成员回读通过后才写终态`full100_report_and_durable_archive_verified`。失败保留所有源和部分文件，不自动重试或清锁。**不要另行同时启动报告或归档。**

新的只读监视命令在本地`E:/fpga_race-two/takeover_local/g32_full100_monitor_all_command.txt`，显示批量、浮点、L05及收尾状态；Ctrl-C仍只停止前台显示。部署命令`g32_full100_finish_command.txt`已执行，不重放。初次本地命令生成的换行转义错误在发送前通过Python3.6语法检查发现并修复，服务器仅运行通过语法检查的版本。执行准备记录`G32_FULL100_FINISH_PREPARATION_20261117.json`。

17:30监视里程碑：自身完整回归已超过一半，625/1200、15,840,000输出和total、0失败；20%余量的批量剩余估计7,474秒，不包含后续精度连接/持久归档。此前完整20条与固定12任务PPA保持独立。下一步只跟踪当前三个已知进程，完成后读取收尾request/state/报告与持久回执，将实际新结果及哈希写回Git；不要另启动完整批次、综合或功耗。
