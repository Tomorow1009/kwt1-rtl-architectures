# C80已冻结，进入C32-A

## 21:47 空间恢复完成，C32-A真实ASIC队列已启动

恢复22/PID202397已退出：49200个已归档生成输入副本2639224198B全部清理；源码、结果CSV、日志、JSON及R4原摘要不改。私有/tmp归档保留，新持久备份 PROJECT/backups/r4-generated-inputs-20261116_2135 已复制并逐文件SHA/大小核验；不是删除唯一副本。回执详见 C32_SHARED_SPACE_RECOVERY22_20261116.json。不得再次执行22，19/20和原始失败initial01也不重跑。

唯一 C32 initial02 队列于2026-11-16 21:44:35.190599启动，PID205526。包 ROOT/light-light126-c32-61246bb，ROOT=/tmp/s4_21usr_c32_20261116_2010。21:46:38观察 status=running、stage=soc、error=null、completed=[]，编译已结束并派发extremes例。真实ASIC14尚未整体完成，不能当作PASS。

启动回执 ROOT/c32_initial02_launch.json SHA 22d2e7a2e15a88ce0675777a257951ab3561af09a7f3dc9f475d0c40842aa8cd；请求 SHA 361fbe5b3a50ae930d2840ba6872d099ccde9e84b17ff41edebb5dd93abd4c4c。队列 runs/c32_initial02/state.json 动态变化，不以旧状态SHA校验当前进度。原协作锁由本队列管理，不能清除、接管或另派EDA。受测源码61246bb和1081成员manifest保持，桌面T80/旧八路/P80/C80完全不动。

21:45:30共享可用1401946112B；启动时私有/tmp78390505472B，共享1527775232B。后续全部C32硬件结果写私有/tmp，服务器共享空间仍紧张。下一步沿原队列CPU14→恢复→竞争→综合→240→精度；成功退出后才用已部署 ops-recovery02/C32_FINISH_FROM_INITIAL02_20261116.py 启动自己的门级/SAIF/PT队列。此工具须绑定实际终态SHA。C32-B/G32仍未开始。

无GUI输入传输在运行，第一终端workspace3空闲，窗口18874435。最近Git已push4a609e7，本段及22证据待同步。压缩后先读本段、计划、AGENTS、STATUS；不要据下方旧“共享盘满/尚未启动”状态重复操作。


## 21:38 归档21全量通过，精确恢复22已启动

只读归档完成并退出：49200文件2639224198B，gzip508256874B，完整回读及源再核对通过；回执 ROOT/r4_generated_archive21/receipt.json SHA 1b8ae10a78a0fb8f094ff34d55fc0e245bb4ed4b7c3fd17418cbb813b3e5e6ef。本地证据 C32_R4_ARCHIVE21_20261116.json。原R4摘要/结果/日志/源码/活动均未改。

恢复22于21:38通过可见终端显式启动，PID202397，ROOT/r4_recovery22.py SHA fa9290736120c2a9473badeaeff208835bf199d5fa7a90dc4b99afec0c61620c；日志与启动回执为 r4_recovery22.log、r4_recovery22_launch.json。它再次核验归档、元数据与选中文件后，仅删除归档中的生成输入副本；保持/tmp归档，成功后写新持久备份 PROJECT/backups/r4-generated-inputs-20261116_2135 并核验，再调用既有initial02。此刻尚未观察删除完成或C32启动。

下一步先读 r4_generated_recovery22/state.json、persistent_copy.json、followup.json 和 c32_initial02_launch.json；不可重跑22，不重复旧initial01/19/20。GUI传输53526/81314/17056均已退出，第一终端空闲。最新已push4b02978；本段和新归档证据待同步。所有T80/旧八路/P80/C80及已有备份保持保护。

本地两次通过PowerShell管道插入中文记录遇到stdin编码错误，未写文件；改用UTF-8文件读取插入，硬件与远端运行不受影响。


## 21:34 R4归档身份修正；回读运行中

archive21初次PID197816已退出，在身份检查阶段失败，未创建OUT、未归档、未删除。历史`ICB32_FINAL1200_20261111.json`中的batch_identity哈希第8/9字符抄反；实际为`27060dfcec0e8fcfadd925d2899ecabcad3c05d05d9048e631616811b540adc9`，机器确认与原未改summary内部`batch_identity_sha256`完全一致，summary SHA保持`3bb0290586f7b92e5a392cb8f7e735ec483b8b302cc285a39fff2e63ebc01bc2`。原错误记录保留，不将差异视为硬件变更。

本地提交9167b46仅纠正归档器常量。新源SHA `2a28e61f85792f4f0d2fc2655950feaeb34a3a9e728ca108042f982dace233c4`，服务器新`ROOT/r4_archive21_fixed.py`及`r4_archive21_fixed.log`，PID199005，21:32仍在扫描输入，日志尚未报SELECTED，原源未改。输出待`ROOT/r4_generated_archive21/receipt.json`；完整回读通过前不能删除。

严格后继恢复工具`C32_R4_GENERATED_RECOVERY22_20261116.py`已本地Python3.6及11范围检查，提交7829d9c，SHA `fa9290736120c2a9473badeaeff208835bf199d5fa7a90dc4b99afec0c61620c`。当前GUI传输会话53526输入recovery22.b64，未退出前不可另发键盘。**尚未执行22。** 它须显式绑定21完成回执，重核全归档和选中文件，只删已归档每例输入副本，保留/tmp压缩及证据，随后核验持久副本`PROJECT/backups/r4-generated-inputs-20261116_2135`，再调用现有initial02。若任何步骤失败先读状态，不重跑删除。

21:28实际df：共享NFS8.8TB满，statvfs块大小1MiB、available1块，inode尚有60887；/tmp约74GiB。不是本地仿真失败。C32仍无CPU/综合任务；保护桌面T80、旧八路、全部结果及冻结备份。

## 21:27 恢复核对；仅准备 R4 输入归档21

重读有效计划、AGENTS、根交接、STATUS和本检查点，确认S0/P80/C80已冻结；C32-A本地完成，服务器尚未启动硬件。最新源码提交e23bed5只增加只读归档工具，不改变61246bb受测硬件。`C32_R4_GENERATED_ARCHIVE21_20261116.py` SHA `6f98219c19bb640cee5f15ca6ae884daaecc64b62328a0f1b3da9ae48b8a1ed6`，本地Python3.6语法和11范围检查通过。

候选严格限旧R4 96443包的`icb32_r4_finish01_final1200/icb32_batch/cases`每任务.hex/.bin/.verilog生成输入；已只读确认1200例/30412800输出完成。summary SHA `3bb0290586f7b92e5a392cb8f7e735ec483b8b302cc285a39fff2e63ebc01bc2`，identity SHA `27060dfcce0e8fcfadd925d2899ecabcad3c05d05d9048e631616811b540adc9`。归档21只复制至私有/tmp并全量回读、源再核对；不删除源，不动结果CSV/日志/JSON/源码/网表/SAIF。后续删除尚未准备或授权执行到具体工具。

当前GUI会话72180仅传archive21.b64到`/tmp/s4_21usr_c32_20261116_2010`，未退出前不能并发键盘输入。第一终端workspace3，窗口18874435经新windows/screenshot核对。无新EDA、无initial02。原19/20删除已完成，不能重复；旧R4唯一gzip、桌面T80、旧八路、P80/C80及完整备份不动。

更新时间：2026-11-16 20:13（北京时间）。压缩后先读AGENTS、有效计划、根交接、本文及STATUS，核对完成与未完成项，不从旧待办重启队列。

## 21:12 清理20完成但空间再耗尽；C32硬件尚未启动

21:14更新：只读du已结束，第一终端回到Bash提示符，两标签可用，无GUI传输。`takeover_local/c32_space_inventory_latest.png`列出其它较大旧包：N1-v4-20261113_013211-9305c6948c76约7.131GB（主要为必须保留的R4 gzip，不动其唯一归档）、`light-light126-icb32-r4-20261111_043048-96443c284a1c`约3.744GB、`light-light126-batch-identity-dma16-20261110_045000-66838470bb12`约1.565GB。其它T80包排除。下一步仅核查旧R4/DMA16的生成数据/缓存及备份，不能直接删除整包。尚未准备cleanup21；当前无服务器EDA，无initial02。

cleanup20/PID187957已退出，21:06:50.235783实测1852文件98453710B精确清理完成，完整归档保留。回执`ROOT/b0_archived_generated_duplicates20/state.json` SHA `36d6c8b449345b998669572fb520ac05ea16f1d2ea9a1f1df5329c84de2d24b4`；后继initial02又在共享>=64MiB检查拒绝，未创建其队列或任务；共享再次1048576B。**19/20均完成，不得重跑删除。** 20的followup.json及log记录后继失败，清理本身状态仍完成；见C32_SHARED_SPACE_RECOVERY20_20261116.json。

当前没有GUI输入传输会话。第一终端在只读`du -B1 --max-depth=1 PROJECT/bundles`及Python排序中，21:11截图仍未返回提示符；不要在它完成前追加输入。输出会列18个最大历史包，下一步检查哪些非T80/非旧八路的生成缓存可完整归档。只读查询不意味着允许删除候选；必须核验备份、身份、进程和范围。

已确认旧R4 12.595GB原始VCD早在11月13日完成gzip核验并删除原始副本，不能重复归档/删除；唯一7GB压缩件与回执仍保留。旧B0当前>40MB只剩R4方法关联SAIF，未选入删除范围。不得为解决空间触碰桌面T80、旧八路、P80/C80冻结包或完整备份。

新C32包和全部已传工具完整，受测61246bb、manifest `0b12bff8f9d989e83eb48d4bd5e62185852edf592e442d3bccbdb1070fc849cc`。原initial01零工作ENOSPC失败保留；现有ops-recovery02可在空间恢复后直接调用，不重建/重传。真实CPU14/综合/240/PPA仍未运行。最新恢复源码提交b33e7a8，本段及证据待同步。

## 20:58 清理19已完成；共享盘再次满，initial02尚未派发

21:04补充：只读统计已返回，五个旧B0 run的生成/编译副本共1852文件98453710B（3个gate14各574/30590599B，contention82/4417569B，sequence48/2264344B）。新`C32_B0_GENERATED_DUPLICATES20_20261116.py`提交b33e7a8，SHA `8a3cbb86f6edccbb1a76acc12fa3415873373ef629055fd933a1fe408ebac277`，Python3.6语法和17项范围守卫通过。只允许这五目录、7种生成文件类型，逐项核验完整归档/源SHA，保留全部源码/网表/摘要/日志；全程无锁/无EDA/无占用检查，删除日志持久化。成功后立即调用已部署initial02；不会重复initial01或改变RTL。**当前本地会话17378仅传cleanup20.b64，尚未执行；未退出前不发VNC输入。** 新工具输出`ROOT/b0_archived_generated_duplicates20`，会在清理完成后单独记录followup；若失败必须先读状态，绝不能重跑删除。

- cleanup19/PID180471已退出；20:49:33.824636回执`verified_duplicates_removed_backup_retained`，精确移除三份旧B0 drc06重复统计481632614B，源备份保留。回执SHA `b08a1d1b1dc488f498bd81fa687df873c9bb3a39799ef4b2777b400e3c752b51`，当时共享可用341835776B。见`C32_SHARED_SPACE_RECOVERY19_20261116.json`。**不得再执行19。**
- 新启动器及其后继工具已部署到`ROOT/ops-recovery02/`，两文件packet SHA `191eb8ab7fd048fc9aef27305d8850c292dad5b8da312fbba3523fbbdb1e9473`；本地提交79e7334已push。
- `C32_QUALIFICATION02_LAUNCH_20261116.py` SHA `5a74620bc3a76bf3285f49274a224af0f3767f0287be0d5a9871af29413c917d`。它绑定initial01失败与cleanup19，参数`--manifest-sha256`及`--cleanup-receipt-sha256`。20:55在共享空间>=64MiB前置检查被拒绝，**尚未创建initial02请求、日志、队列或进程**。20:57共享又仅1048576B。不要误报已运行CPU。
- `C32_FINISH_FROM_INITIAL02_20261116.py` SHA `c87a1324fdc89a850697c6efe634393167b015fdf28aa229e8fb1bc338612329`已部署，但只能在initial02完成并退出后用，finish01尚未创建。旧绑定initial01的finish启动器不可用。
- 人工manifest转录第50/51字符曾交换，已用服务器逐字符差异纠正（未派发作业）。**准确manifest：`0b12bff8f9d989e83eb48d4bd5e62185852edf592e442d3bccbdb1070fc849cc`**。之后通过prepared回执读取准确参数，并复核实际manifest，不再重抄。不要重跑会mkdir ops的bootstrap，因为ops-recovery02已存在。
- 20:57只读筛选旧B0仍存在的>40MB归档成员，只剩旧R4 `systolic_b_r4_saif_replay01/native_saif_r4_replay/layer_01.saif` 94632798B。它未进入清理范围，不动方法资格数据。
- 当前只读GUI查询会话40570正在统计同一旧B0归档内各旧run的生成输入/编译副本（.hex/.bin/.verilog/.o/.so/.a/simv），排除名称含r4的run。截图`takeover_local/c32_b0_small_duplicate_groups.png`；先poll并读结果。尚未选定或编写cleanup20，未执行任何额外删除。若有适合的已归档副本，必须重验归档/源哈希/占用；恢复空间后尽快直接调用已部署initial02，避免再次被占满。

本地与服务器受测RTL始终61246bb；1081成员新包仍完整。T80/旧八路/P80/C80/完整备份保护不变。C32自身CPU/PPA仍未运行；当前阶段仍C32-A，不进入C32-B/G32。新19及换行问题的本地记录、初始失败保留，不恢复任何旧EDA队列。

## 20:47 新包已核验，initial01零子任务因共享盘满失败

**C32服务器硬件仍未运行。** 主包重建和1081输入准备已完成。包路径`/tmp/s4_21usr_c32_20261116_2010/light-light126-c32-61246bb`，manifest准确SHA `0b12bff8f9d989e83eb48d4bd5e62185852edf592e442d3bccbdb1070fc849cc`；受测提交仍61246bb。此前人工抄录65字符哈希触发前置拒绝，无任务；之后用prepared回执机器取值启动。

- 差分首次重建被25处基准哈希差异拦住；只读核对25处全是CRLF/LF，无内容变化。新重建器`C32_RECONSTRUCT_LF_61246BB_20261116.py`提交e9c52fe，SHA `d21c6326c6241b13d04dcbd5c90ac0a827972ce84ab185a48cb7bc1dcfc01d65`，先核验原冻结字节，再仅内存换行归一化并检查差分基准SHA，最后完整payload仍精确为`40fed77e347aad1347f1998f19801652770b176c5f5e0e03f405d68d0a11c602`。原工具和失败保留。新根`reconstruction_lf_receipt.json`记录25处，原源未改。
- `c32_initial01`于20:40:42.554042启动PID177134，随后在`.arch02_team_lock`的mkdir即ENOSPC失败。20:41:53状态failed，completed=[]、无stage；20:45机器确认PID不存在、整个队列无child回执。原state SHA `42ffa16c397ab474753eb1cc9ef5617c2bf226bbee1c318f8e752fd5416aa674`；request SHA `49a8fa04de09a5e269c89cc21c99be1fffa5d7018467c469c350ad2ad977cd7a`。**不得重跑/覆写initial01。** 启动时/tmp可用79114158080B，共享盘仅1048576B，仍无法创建锁。
- 已只读找到旧B0 `systolic_b_v3_drc06/systolic_b_synth`三份已归档重复统计：mapped_probe_inventory.tsv 268868363B、area_inventory.json 137502877B、leaf_area.tsv 75261374B，合计481632614B。不是T80/旧八路，也不是源、网表或摘要。完整B0归档及63653成员回读证明不动。
- 新范围限定工具`C32_B0_DUPLICATE_REPORTS19_20261116.py`提交b026f9b，SHA `d87d789ad28b0e2ab2c4d290f52b3997f9d525a755eb7942ceba46af4d06e071`，本地Python3.6语法和6项终态守卫通过。它重新hash完整归档、清单、三源文件，检查无锁/无EDA/无占用，写intent及journal后才删三个重复文件；原B0完整备份留存。**当前本地会话12125仅通过GUI传cleanup19.b64，尚未执行删除。未退出前不发其它VNC输入。**
- 清理成功后应从同一612冻结包新建`c32_initial02`，显式绑定initial01零工作终态和cleanup19回执；原初始启动器写死initial01不可再次调用。本地`C32_FINISH01_LAUNCH_20261116.py`也写死initial01，后续须新增绑定initial02的启动器，不能原地改受测包或冒用旧成功。

截至本段尚无任何新清理完成、无C32 CPU/PPA结果、无C32-B/G32。桌面T80、旧八路、P80/C80冻结与备份全部未动。原删除14/17/18不可重复；16从未执行且已过期。接续先读本段和实际会话，不按下方早期“正在ASIC”文字推断状态。

## 20:31 主传输完成，部署工具传输中

- 旧GUI会话13372已正常退出，97332字符和结束行全部发出，20:30截图确认第一终端回到Bash提示符。**不要重复传delta03**。服务器尚未重建或启动EDA。
- 新GUI会话70703正在输入`deployment_tools02.b64`（6588字符），结束后自动写`C32TOOLSEND`并截图。未退出前不要另发VNC输入。该工具payload SHA `34829ef86778d18293f812fe00c21b4a42297068c2811812d41ce8e2a0b3c39a`，3文件。
- 本地`local_runs/c32_overlay_20261116_2002/prepare_remote01.py`已准备1477字符ASCII，先语法检查。待工具传输结束后，通过可见终端运行此代码：核验工具payload、独占创建`ops-deploy01`，执行重建器核验完整612 payload，再提取其prepare工具创建新C32包。若失败保留现场，不跳过哈希。
- 当前已push `643398e`：新增本地带范围的报告`C32_LOCAL_BRINGUP_20261116.md`及终态后显式启动门级/功耗的`C32_FINISH01_LAUNCH_20261116.py`，SHA `6a7ab5a948c33cdecd96642f03b9ad484c8e1dc0f556a069ed52c8b5b051196f`。此工具只准备，不能在initial01完成退出前运行；本地Python3.6语法与CLI检查通过。硬件受测提交仍61246bb。
- 本次没有新增硬件改动、重跑测试或清理服务器文件。T80/旧八路/P80/C80保护不变。新包完成校验后继续原计划自己的ASIC14/恢复/竞争/综合/240/精度。

## 20:13 受测提交已同步，GUI传输正在运行

**C32-A受测源码及工具已提交并push：`61246bb2a21c56a9bfd871fd68de93028d79f5fd`。** 三套固件绑定当前源码检查通过。C32自己的真实CPU/PPA仍未运行，所有本地结果范围不变。

- 完整传输资料：`local_runs/c32_overlay_20261116_2002/payload.json`，114文件，5485929B，SHA `40fed77e347aad1347f1998f19801652770b176c5f5e0e03f405d68d0a11c602`。普通zlib445715B未传。
- 精确差分传输：同目录`delta03.zlib`，72999B，SHA `64d6f32d905cd59decb73a08a7120d31634d95dc4503b3717feccf1ea22525b5`；base64文件`delta03.b64`共97332字符。基于冻结C80成员做只读重建，最终完整payload SHA必须相同。早先delta01/02/XZ只是本地压缩尝试，没有上传。
- **本地exec会话13372正在连续GUI输入，不能另发VNC键盘输入、切换标签或重复启动传输。** 它每段900字符，进度`local_runs/c32_overlay_20261116_2002/gui_transfer_chunks.txt`；最后观察20:11已9900字符。循环将自动发送全部内容及`C32PAYLOADEND`结束行，并保存`takeover_local/c32_transfer_payload_done.png`。恢复先poll该会话/读本地进度和截图；未见退出不要发送下一命令。可继续纯本地工作。
- 新私有根已于20:07建立：`/tmp/s4_21usr_c32_20261116_2010`，0700。第一终端当前在`cat > .../delta03.b64 <<'C32PAYLOADEND'`中，窗口18874435/workspace3。最后截图`takeover_local/c32_transfer_start.png`。没有FileZilla；原FTP DNS约束仍保持，未尝试绕过。
- 下一步上传本地重建器`handoff/team/evidence/C32_RECONSTRUCT_61246BB_20261116.py`（SHA `5092484b3a34ab1d3d32549c67784217f1d7e96419237d5c450794bc7fcf09d2`），本地完整重建/损坏拒绝通过。服务器先验证C80 manifest及每个引用成员，再独占创建`payload_61246bb.json`。若基准成员不存在/哈希不符，保留失败并修复传输资料，不能跳过检查。
- 从核验payload取出`c32_prepare_bundle.py`到新根bootstrap，运行`--payload ... --root ... --bundle light-light126-c32-61246bb`。新包只读复制C80原包1008文件并写新C32覆盖；源不会修改。核对prepared回执/新manifest全部文件。
- 新启动器已本地准备`handoff/team/evidence/C32_QUALIFICATION01_LAUNCH_20261116.py`，**尚未上传或执行**。需要显式`--manifest-sha256`，绑定payload612、prepared回执、冻结C80报告SHA、S0预算、DATA100和FLOAT、私有NumPy、进程/锁/空间。将启动唯一`c32_initial01`，顺序CPU14→恢复→竞争→综合→240→精度；C32-B/G32不会自动启动。
- 当前qualification源码SHA `147af697f797cfcd84796a66fa7daecd24910f1527f8d08422fb9c216ae63afb`。冻结C80对照报告`/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7/runs/c80_report02/c80_report/report.json` SHA `46d13e9cbfac0730bec8eb7ea0b7927a9612462cf4b5cd056402c06155711cf4`。新队列要求同源、同编码SHA；不要求C32-A必须超过C80才测自己的PPA。

共享盘最后仍仅1MiB，私有/tmp约79GB；未做任何新删除。桌面T80、旧八路、P80和C80冻结证据禁止动。压缩后先解决当前传输和新包校验，不回到旧综合或旧240。上面两个现场辅助脚本和本次进度待下一提交；不改变612受测硬件。

## 20:01 本地验证齐备，准备独立服务器包

- 完整本地14例通过354816输出及total，目录`local_runs/c32_datapath_20261116_194814_422485`。此替代总线jitter0周期约60k，不作为原平台性能。
- 两拍SRAM、预取0/1各A/B/A共6任务通过152064输出，目录`local_runs/c32_datapath_20261116_194815_001509`。
- 独立恢复fixture通过10阶段/3完整任务/76032输出及3项预期拒绝，目录`local_runs/c32_sequence_fixture_20261116_195223_950804`；不是CPU执行。
- 正向/竞争/恢复生产观察器编译完成；门级观察器本地端口编译和完成条件协议测试通过，目录分别`c32_monitor_elaborate_20261116_195109_914742`、`c32_gate_observer_20261116_195535_514696`。不等于真实网表门级。
- 独立固件三族`local_runs/c32_fw_{irq,sequence,contention}_20261116_1952`编译并绑定当前源码。新的安装器严格2行、32PE、220宏和布局6；保留原C80安装链5行检查，最终清除继承的80PE/旧布局字段。
- 新增C32自己的SoC/240/综合/门级/SAIF/PT/报告/归档入口；57个Python文件通过Python3.6语法及导入，54项工具测试通过。数值运行时前置检查既有私有NumPy，避免C80曾发生的长队列末尾缺包。
- `C32_LOCAL_QUALIFICATION_20261116.json`绑定上述摘要；服务器实测均未开始。生成过程中UTF8读取修复、测试模板缺依赖/旧ID已修正；没有硬件功能失败。删除了本轮误生成的、依赖尚不存在C32现场导出脚本的测试副本，原C80测试未动。

19:57:54只读VNC预检：本账号无DC/PT/simv/阶段队列，无协作锁；私有/tmp可用79155372032B，共享盘仅1048576B。未清理文件。窗口18874435、workspace3第一终端空闲，workspace4不操作。接下来提交本地受测源码、构建带哈希的新C32传输资料；从冻结C80源包只读复制新目录，不复制其PASS。部署前继续核对新包全量清单；原T80/旧八路/C80/P80保护不变。

新qualification对照冻结C80固定12同源、同编码SHA及长度，记录C32-A速度变化，不擅自要求它必须快于80PE后才测面积功耗。可选C32-B仍必须不慢于已验收C32-A。C32自己的真实CPU14/恢复/竞争/240、PPA、完整归档冻结仍待完成。

## 19:46 C32-A开发进度（优先于下方早期快照）

C80标签`arch03-c80-codec-20261116-1930`已在c7f3c00创建并推送。现已新增独立C32阵列、线性核、加速器、两套TB和两套本地运行器，共7文件；尚未提交。旧C80/P80/T80代码未改。硬件ID确定为`0x4b57530d`、能力`0x000b02bf`，两行结构；编码布局仍`0x00100006`，与C80字节相同。两32项结果区、32转换器、10位块号、800块/51200供数拍。C32-A仍60X＋32W小宏。

- 阵列压力通过：`local_runs/c32_systolic_array_20261116_193552_854669`，10000随机＋32定向，317824输出，sum/total/result/saturated及每输出64次MAC零差异；暂停201275拍，取消11、复位11，块号回绕及连续II64通过。种子0x7834a9f1。只证明独立阵列/转换，不含CPU、SRAM或PPA。
- 首层完整本地搬运通过：`local_runs/c32_datapath_20261116_194127_101770`，1拍SRAM、预取开、jitter=1，25344输出/total零差异，83308完整周期（带随机等待，不是正式性能）。实际源/共享写ACK/共享读回/结果ACK四段检查；独立按逻辑行算式检查每个物理X宏地址、跨五行组和尾行屏蔽。
- X到齐改为50个行对标志；读取流水保存实际RB/G，单端口冲突逐宏仲裁。尾row99禁止读取/写回。编码器、搬运及平台参数保持。
- 本地生成脚本曾遇文本模板断言；已另行生成正确文件并完成以上测试，原失败输出留local_runs。不要重跑一次性create_c32_array/datapath生成脚本覆盖实际源。

下一步完整14本地任务、两拍SRAM/预取开关/无复位A-B-A，再创建独立C32固件/安装/SoC观察器/统计/结构检查及服务器运行包。不放宽C80的5行/80PE检查。C32自己的真实CPU14/恢复/竞争/240、综合/门级/活动/功耗/归档均未做，不继承C80 PASS。服务器19:27终态仍是最后观察，本段未操作服务器。

代码摘要与原始summary身份保存于`handoff/team/evidence/C32_LOCAL_INITIAL_20261116.json`。历史未跟踪S0_SYNTH05_FINISH_LAUNCH_20261115.py继续不添加、不运行。桌面T80、旧八路及所有冻结备份保护不变。

## 当前目标与保护

有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。路线S0→P80→C80→C32-A/可选B→G32。最终32PE、150MHz/6.666666ns、SS/.99V/125°C、项目保守面积≤1.00mm²，<0.50mm²仅争取目标。

原32位ICB/平台缓冲、X14/W12/acc32/total33/SHIFT10不变，完整源读→共享写ACK→原总线读回→解码→计算→最终写ACK/排空。不能以ACK数据旁路提速。

**服务器桌面T80_Delivery_20261113、全部旧八路、P80及新冻结C80包/备份不修改、移动或删除。** 用户持续授权推进和私人GitHub同范围同步；不额外开启子代理，不因等待自动结束任务。

## 已完成与冻结

S0/P80此前已冻结。C80技术结论及全量持久归档已完成，冻结回执`handoff/team/evidence/C80_FREEZE_20261116.json`，标签预定`arch03-c80-codec-20261116-1930`（本页首次写入时待提交并打标签）。阶段报告`workspaces/arch03/C80_STAGE_REPORT_20261116.md`；早前完整经过见C80_POWER和C80_SAIF检查点，不重做。

C80受测提交74f3ae7bb479d5fdd7917702c4a2c0671eacb61b，RTL自2896d5deaed9e669ca23e12616e8d5091d72e034后不变。包1008文件manifest `d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59`，运行根`/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7`。

- 本地48解码、完整14、恢复/raw/1与2拍SRAM，10000随机＋32定向块；真实ASIC14、恢复及CPU竞争通过。
- 自身240任务6082560输出及total零差异；FLOAT20逐层最大NRMSE0.20198143836753799%，固定12最大0.1425636423408142%，裁剪/饱和0，非官方600。
- 固定12总847238、均70603.1666667周期，名义150MHz吞吐2124.5505985task/s，编码均25790B、四段384174事务。240均69352.7125，不能混用两组。
- 保守项目0.9611361367002672mm²，明确新增0.8005131007003622mm²，整机4.483352635935mm²；setup+0.000216007ns/hold+0.00623399ns，220宏/0锁存器。
- 同最终网表无SDF门级14、完整SAIF12及PT12通过；时间加权55.3675890516mW、26.0608448455µJ/task。比P80吞吐+9.8327%、功耗+2.9599%、能耗−6.2574%。
- 全12层374565直接映射＋1336孤立默认、未注释0；39930未知目标中37879直接解析、2051分类，关键显式控制未知0。保留原X活动政策与布局前限制，不宣称物理功耗误差上界。
- 模型快照SHA `81517233df218c5738a1e3950bef1dd1f5b8ca0de15a4948d1e6a85877f04071`，报告SHA `46d13e9cbfac0730bec8eb7ea0b7927a9612462cf4b5cd056402c06155711cf4`，网表SHA `6a62a3aa792865390549dd11a841d0888501902c449c61c74aa82eecd2523b00`。

备份`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups/c80-runtime-20261116_1923-copy03`，752263487B，SHA `81123521ea325f7f9b89f23e7c132ee8ed62f1ae5b702d2b69139d124b219d39`。19478文件/1293目录/6链接全部回读，源前后相同、源未删。回执SHA `f4531ad245395a3de7388dcad55c550d8b73b08600da195e493abf7ae77fbc8c`，清单SHA `5b87c5d35021e22f3d43e7b79f70464b2fdc1c8de8a3144b2e132f00e8e9acb0`；19:28:49机器断言。独立技术结论提交120b477，SHA `4c4d3a70fcdbee758817718a4b0d4088d1248951003e3579c5cf056ddb37e218`。

## 原队列/空间终态与禁止重复项

19:27观察：58047验证、59705汇总、134382连接查询、DC137120及归档143417均自然退出，无协作锁。汇总19:11:17结束，状态facts_joined_manual_conclusion_required，终态SHA `311c74f6b83c2020458f20b49d9ef8d60c16b466ec7d0af9a2ebf977b6ed97e3`。不要再启动综合、240、门级、活动、功耗或旧export。

共享盘满曾使连接查询等待原锁：single17(6dabb3f)核验完整归档与占用后，仅删除旧B0 drc05/mapped_probe_inventory.tsv，268811341B，原查询自行继续。之后remaining18(120b477)在所有队列退出/无锁/无EDA时清理其余17份旧B0重复SAIF/DRC明细2070730031B。完整B0备份`backups/systolic-b-20261112_2320/completed-evidence.tar.gz`及全部结果保留。两项回执在Git对应JSON。**cleanup14/17/18均完成，不重复；cleanup16从未执行且已不适用，禁止运行。** 没有删除T80、旧八路、P80、R4方法资格、当前C80或任何源文件/网表/日志。

共享盘19:27只剩463470592B（会变化），新服务器运行继续用独立私有/tmp及原团队锁。copy03已完成，不重复启动。未采用后续只读列出的B0 drc06候选，没有新增清理。此前失败initial缺NumPy、followup01空间失败、export01失败均完整保存入本次归档。

## C32-A接续准备与未完成项

先读`workspaces/arch03/C32_PREPARATION_READONLY_20261116.md`。以下为19:29时的准备清单；已有RTL和本地结果以顶部19:46更新为准。固件、运行包和服务器任务仍未开始：

1. 新独立2×16阵列和线性核，32PE/32转换器、两32项结果区、10位块标签、50行组/800块、最后仅row98。X/W token27/25位，波前跨度16/15，不重置普通连续块。
2. C32-A保留60个X小宏＋32个W小宏。逻辑pair与旧五行物理G区分；row4/5跨bank/G，迟到响应携带真实RB/G。按逻辑行/对发布到齐，最后禁止row99访问/输出；1/2拍和实际宏冲突需重新验证。
3. 复用C80编码字节、DMA/仲裁/原平台参数与参考，独立ID/能力和安装/测量/结构入口。当前4b57530d/e/f只检查过未占用，尚未正式分配。不要放宽旧C80的5行/80PE检查。
4. 本地完整数值协议与10000随机块，自己的ASIC14/恢复/竞争/240、综合时序面积、同网表gate14/SAIF12/PT12，独立报告后冻结。不要继承C80 PASS。
5. 之后才评估可选C32-B（两4096×16奇偶Xbank）及G32，原80PE不自动恢复。当前编码均25790B下搬运仍限制约2128task/s，不能用51200计算下界宣称C32接近3000。

本地`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。Python3.8为E:/fpga_race-two/.venv-kwt/Scripts/python.exe；Vivado2018.3、Zig已可用。历史未跟踪S0_SYNTH05_FINISH_LAUNCH_20261115.py不添加、不运行。120b477已push，本页及冻结回执待提交。GUI恢复先刷新windows/screenshot，既有ac820.ps1，当前18874435/workspace3，两终端空闲，workspace4不操作；FileZilla未用。
