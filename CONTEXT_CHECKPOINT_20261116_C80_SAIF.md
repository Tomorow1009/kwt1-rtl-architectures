# C80活动完成与功耗分析：18:05恢复检查点

**18:05恢复核对：SAIF12完成；18:03:01原队列running/power_layer_05，PT完成4/12，原58047/59705继续。新根交接已整理，旧原文保留CONTEXT_HISTORY_20261116_C80_1805.md。以下带时间条目为历史观察，最新优先；没有新归档、删除或C32硬件。**

**17:56最新：自己的SAIF12全部完成，304128输出、847238周期、1170767047B，summary SHA29fbb12f…70bbcdd已机器核对。时序/DRC只读诊断完成，约束报告clear、接口核对通过；完整独立结论仍待模型汇总。PT L01已完成，首层55.1722385mW、26.9189002872µJ，非12层均值；17:54原队列运行power_layer_02。原58047/59705不变；第一标签空闲，第二94139至18:03:29。没有归档、新删除或C32任务。**

**17:43:29观察更新：SAIF11/12，PT尚未开始；原58047/59705继续，最新push9a045f2。第二94139只读观察器仍到18:03:29。没有活动传输，没有归档或新清理任务。**

**17:33更新：活动9/12，原58047/59705继续；旧观察器82248正常结束。新第二标签只读观察器94139于17:33:29开始、预计18:03:29结束，禁止向其前台输入。最新已push c8c730d，copy03全部预部署核验、cleanup16已提交但未部署/执行；没有归档或新清理任务。**

**17:42最新：活动已10/12，17:39:42累计975,565,187B，仍原队列。cleanup16已仅预部署到`ops-b0-cleanup16-c8c730d`，未执行、输出目录不存在；入口SHA `0e98728332e0ba048142231f414322dc3aaf21e287b3bde0bc4121124c976441`，导入回执 `eda250cdc43986be6636510fc8f5ee6ebd700df01151134d51f0047976e7f204` 已17:41:31机器assert。两次只读SHA断言因人工抄写失败，已按8位分组纠正；原文件无变。全部传输3622等已完成；第一标签空闲，第二94139观察器仍到18:03:29。最新push c8c730d，之后本页和新部署证据待同步。**

更新：2026-11-16，北京时间。恢复先读AGENTS、有效计划、根交接、本页及STATUS；以下远端状态是最后观察，必须重新核对。

## 有效任务与保护

有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，与用户下载原文同SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。S0/P80已冻结，当前C80；自己的功能、PPA、报告和归档冻结完成后才进入C32-A/可选B，再G32。最终32PE、150MHz/6.666666ns、SS/.99V/125°C、保守面积≤1.00mm²；原32位ICB及真实共享写ACK后原总线读回保持，X14/W12/acc32/total33/SHIFT10保持。

**桌面T80_Delivery_20261113、全部旧八路、P80冻结包和备份绝不改/移/删。** C80运行包不改，不清团队锁，不重复原队列。没有开始C32硬件或G32。C32只读分析见`C32_PREPARATION_READONLY_20261116.md`，不构成新硬件PASS。

本地`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`；最新已push **4065fc2**。之后待提交的是本页/交接/STATUS、新copy03部署证据和仅本地的cleanup16。唯一历史未跟踪`S0_SYNTH05_FINISH_LAUNCH_20261115.py`不添加、不运行。

## 原队列继续，不重复派发

私有根`/tmp/s4_21usr_c80_20261116_1245`，包`light-light126-c80-74f3ae7`；受测提交`74f3ae7bb479d5fdd7917702c4a2c0671eacb61b`，1008文件manifest `d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59`。

- **58047**：`私有根/c80_followup02.json`，源`ops-followup02-3502772/C80_FINAL_FOLLOWUP02_20261116.py`，SHA `d5f012fefa01db49de5cb093774d7afee2547692a3f4611c7a2e25e73221cdc5`。自己的precision04通过，当前`包/runs/c80_finish02/state.json`为running/saif，已完成structure/gate。
- **17:26:43已完成SAIF 8/12，累计780,452,359B，无error**。目录`包/runs/c80_finish02_saif/c80_saif`，逐例回执`case_progress.json`。首层SHA `5de0976bb232db38ad2f69b444b61cc49b34afd6fe7625de35637fdb89eb9d6b`、97,575,322B，73186周期，窗口93149.990685—581056.608561ns已机器核对。每层独立核对结果、坐标、IRQ/WFI、最终ACK/排空和SAIF完整窗口。尚无C80功耗数字。
- 原finish继续SAIF12→timing_audit→drc_audit→PT12，正式EDA串行且仍持原团队锁。不能修改正在执行的采集器或重跑门级。
- **59705**：`私有根/c80_export_review02/state.json`，源`ops-export02-00e0810/C80_EXPORT_REVIEW02_20261116.py`，SHA `4c001bb4603a52b3c6f24d95566442bc59c48ee9709e37cbd224b0982331048a`；17:20仍waiting_original_finish。它将在58047自然完成退出后导出`包/runs/c80_report02/c80_report`、unknown_inventory02、unknown_connections02及`私有根/c80_export_review02/model_review_snapshot.json`，不会自动验收或进入C32。

## 本版已完成成果

1. 本地48解码、完整14、十阶段恢复、latency2/预取ABA六任务、raw完整任务、10000随机＋32定向块通过；未重跑。
2. 真实ASIC/E20314、恢复、竞争通过；ASIC summary `4c3668ebe351804b43edd8cf1ec4a56ab4004ed2c8724cc73a8afcc4929b7cb1`。固定12总847238周期、均70603.1666667、150MHz折算2124.5505985 task/s，较P80吞吐+9.8326562%。编码平均25790B，四段实际384174事务；不是芯片实测。
3. 新综合`runs/c80_initial02_synth/c80_synth`完成。summary `0d1b11b013e4c4ee1698417e20124c4cb5601b49aae3d8b4b15cd0f2f0b46fc5`；mapped.v `6a62a3aa792865390549dd11a841d0888501902c449c61c74aa82eecd2523b00`。保守项目0.9611361367002672mm²，整机4.483352635935mm²；setup+0.000216007ns、hold+0.00623399ns、220宏/0锁存器。数值条件通过，完整独立时序/模型结论仍待后续。
4. 自己的240任务、6,082,560输出及total零失败，compile_count1。summary `8dca0f4f57548b2b0f58af3326b909a5a0034b7fa3adad4ccf3030a7b8793312`，批量均69352.7125周期，不能替换固定12均值。
5. 同批FLOAT precision04通过，summary `d7e0dbb52d17659e78af3357688367d4624773221c7693ed3c543f2de2d84acb`；20条合并逐层最大NRMSE0.20198143836753799%，最大单任务0.20953408931848963%，裁剪/饱和0，非官方600。
6. 自己的无SDF gate14通过354816输出，固定12总847238；summary `4c57b9d0df63dc3bcc081a095eb1eabbf0c383069d4b666582702fd6ab34f8cd`。门级不观察内部total，不能填参考total冒充。

仍缺：剩余SAIF、PT12、完整独立审核、持久归档和冻结。完整旧失败/身份见`CONTEXT_CHECKPOINT_20261116_C80_GATE.md`及更早FINAL_NETLIST页。

## 空间与已完成清理

17:26共享`Desktop/IC`仍仅1,048,576B；17:01私有/tmp约81.55GB，足够本轮活动（当时余量预算约3.09GB）。共享空间不是静态保证，归档/新锁前重新检查。

先前cleanup14已经删除旧B0的49,200份已完整备份生成输入副本2,616,732,144B，完整备份和全部结果保留；T80、旧八路、P80未动。其state SHA `39edc92bf5c29dbdaff714aef264c786246e9e20bbf305fa6f5ec1f0859130b0`；不要重跑。

新**只读preflight15**父84083已完成退出，未删除文件。仅18个精确候选：12份旧B0 final01_activity12 SAIF＋6份早期drc04/05大统计，2,339,541,372B；当前源SHA和大小与备份成员全部一致。源`ops-b0-preflight15-964373c/C80_B0_REPORTS_SAIF_PREFLIGHT15_20261116.py` SHA `66442ee9177fe61175dca7cad488c39d9a4d322c9acf1db5aceee21c3b476b61`；结果`私有根/b0_archived_reports_saif_preflight15/verified_candidates.json` SHA `3d9ffdba6e36bca8487da1355ccdb8b397439d9332c2e026bcb1a4399bd9097c`，17:14机器assert。

原完整备份`Desktop/IC/light-light126-undergrad-d2-20261109/backups/systolic-b-20261112_2320/completed-evidence.tar.gz`仍保留，1,261,445,859B，SHA `dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50`。preflight15重新完整哈希；原63,653成员/7,006,124,866B逐成员回读回执仍绑定。R4方法资格SAIF、summary、日志、源和网表不在18文件范围。

**cleanup16已预部署，未执行**：`handoff/team/evidence/C80_B0_DUPLICATES_CLEANUP16_20261116.py`。必须显式`--execute-verified-duplicates`，要求当前58047和59705终态退出、无原锁、无本账号EDA、再次核对18文件/完整备份/占用，并逐文件fsync日志。只有两个已识别桌面服务类别的受限fd沿用原维护例外，未知受限进程会阻止。3个终态允许/6个拒绝场景已本地检查。若export仅上层显示“connections failed”而深层因ENOSPC，这个入口将保守拒绝；必须先调查实际失败，不能绕过。不要在当前EDA仍运行时调用。

## 归档工具：都是预部署，没有归档任务

- copy01旧入口绑定失败01链，不能使用。
- copy02：`/tmp/s4_21usr_c80_archiveops02_20261116_1658`；绑定当前02链，50依赖；导入回执`45e6ce912a992f56c13053547f8dc66514c4eeff9952149771cef8b75a52d660`。标准20%＋2GiB固定预留。
- **copy03**：`/tmp/s4_21usr_c80_archiveops03_20261116_1720`，提交`4065fc211b8aba307a0dfce8a15a4b1283d89f32`，入口`C80_COPY_ONLY_LAUNCH03_20261116.py` SHA `e49e8af01880e56555267736170a294cc4340a3f6c6fb27ac3f46084e019675c`。
- copy03的51依赖导入已通过；receipt **`ffba1790ee1b64a0f8476bc55c9ed374d339e1d17c1df34e7893dacb72b32c54`**已17:26机器assert。payload `3bbcc8f8ffa81af605893a670da845568ee8a3c6a2dd90174e453235822fe2d5`。
- 新helper runtime SHA `f69d1ebd4114e94ae0ddfff8866728c2897c06f4ac7e10b9264cb96326dbff2f`，capacity SHA `a2904fed5a05c4ee38ab0e5cf959fad37013baf14a6609453b7b4ed0fcf87408`。采用**显式20%＋512MiB固定预留**，默认旧配置仍2GiB；精确压缩计数、写中空间检查、原团队锁、全成员解压回读和源前后哈希不变。10项本地测试通过。空间争用/短写保留源和partial，不自动当通过。
- source不删除；只有当前队列、汇总退出，报告/模型结论完成且实际空间足够时，才在源root外发起新`archive03`控制目录和`backups/c80-runtime-时间-copy03`。不提前执行，不修改活跃包。细节见`C80_ARCHIVE_STORAGE_POLICY_20261116.md`。

## GUI、进程和继续步骤

使用既有板端`F:/linux_fpga_try/ac820.ps1`，重读该目录AGENTS和computer-use技能；刷新windows身份。17:26窗口18874435、workspace3，第一标签空闲。第二标签只读观察器**82248**至约17:30:41自然结束，禁止向其前台输入。旧73000正常退出。

全部本地输入已结束，最近copy03传输session38996为15/15且完成；没有进行中的FileZilla传输。先检查截图再输入。

下一步跟随原58047/59705，读活动终态、自己的STA/DRC及12功耗；不要重跑已完成240、综合或gate。完成报告后独立检查功耗模型/未知活动和声明时序条件，处理实际归档容量，冻结C80再C32。压缩前更新本页和根交接；恢复重读计划及本页，保留所有失败和历史路径。
