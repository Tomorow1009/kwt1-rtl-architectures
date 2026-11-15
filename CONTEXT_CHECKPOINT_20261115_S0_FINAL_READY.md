# S0最终链接完成，验证入口修复 — 2026-11-15 22:58

**11月16日00:14当前唯一VNC输入exec18946：45行`local_runs/s0_review_ops_e516e4c_02/transfer.ps1`，只部署6个审核/归档工具到新`ops-review-e516e4c`，不启EDA或归档。先收完该输入再截图，禁止并发键入或重跑。前台199060已仅退出观察器；后台172535验证、193002汇总等待不动。最后00:13:26 SAIF L01–L07通过，L08子200584仿真已退出、核对中。T80桌面/旧八路不动。**

- 审核工具部署来源e516e4c，6文件、139模块静态闭包及Python3.6通过；本地payload SHA `fd028bc649412db0a3c761691dd9c68cdcc8bfaaaf2f1c0529d24caa4c43a423`。首个本地目录`local_runs/s0_review_ops_e516e4c`因编码名称utf8-sig拼写错误停止、未传服务器；实际使用后缀`_02`目录，生成器`local_runs/build_s0_review_ops.py`。
- 本次部署仅写新ops目录，导入时显式将66b9496脚本路径放入sys.path并核server_run.ROOT；旧bundle源码/manifest不改。完成标记应为`S0_REVIEW_TOOLS_READY 6 NO_EDA_NO_ARCHIVE`，尚未观察，不提前称部署完成。
- 完成输入后可恢复`local_runs/s0_finish03_case_watch_command.txt`只读观察；新watcher PID须实际记录。e516e4c已经push，git仅有旧未跟踪S0_SYNTH05启动器（勿加入）。

**11月16日00:04:53实查：finish03父172535仍运行，SAIF L01–L06已通过，L07子197943运行，无错误；只读汇总等待器193002保持。前台watcher已换成199060（193691仅Ctrl+C退出用于只读报告核查），所有85268/18334/23998/40106输入完成。S0未冻结，S1未开始，T80桌面/旧八路不动。13fdc27已push。**

- 00:01–00:03只读完整constraints/check_timing和partition_area，并先核对summary中的文件哈希：constraints明确无违例；check_timing全部非空行只有TIM-134，4条高扇出网络按1000估计，实际网络名仍待队列timing_audit。106个SysMem位、max1/min0、transition0.1/load0.01已覆盖。
- 新小型证据`handoff/team/evidence/S0_SYNTH_REVIEW_SNAPSHOT_20261116.json`保存上述观察及截图哈希。面积继续用原T80同口径保守上界0.9535222591004618mm²；73,334个归属未细分leaf的0.1609004207998941mm²仍全部计费，不用较小的“明确新增”数替代门槛。物理三块和整机叶求和单独记录。
- 实际DC metrics的latches是字符串`"0"`；已将本地尚未部署的`s0_model_review_snapshot.py`按整数值核验，测试改用真实字符串形态，3项重新通过。原综合文件未改。
- 后续归档还须从源runtime之外的cwd运行，并把归档进程日志也放源runtime之外；`no_open_users`检查本账号cwd/fd/maps，归档自己的日志若留在源root会被正确拒绝。完整保留源，不删除任何历史证据。

**23:57:58实查：原finish03父172535继续，SAIF L01–L05已通过，L06子195282运行，error=None。前台只读watcher193691；旧177140仅退出观察器。汇总等待器193002已部署并等待原17步队列退出，之后只导出报告和未知活动清单，不启动EDA或S1。所有3447/34023/77571输入结束，无半截命令；8da012f已push。T80桌面和旧八路不动。**

最新恢复补充：

- 已部署汇总工具8da012f：`ops-66b9496/S0_EXPORT_AFTER_FINISH_20261115.py`，SHA06bfe60625dfea206ace3cff788679afee24d30e5b4583f4b7918d8196635715；builder REQUEST04的Git原始字节SHA9ca45ab038c916ce00b64c63a7c49fdd7948b365392e5fdacfb12c19597bba0c，不能用本地CRLF文件的753d...替代。控制`ops-66b9496/s0_export01_control`；driver同ops下`s0_export01_driver.log`。
- 原17阶段全部完成且父退出后，才建立`runs/s0_report01/t80_s0_report`，随后`runs/s0_unknown_inventory01`；失败保留、不自动重试。尚未导出报告或授予验收。不要重启等待器193002。
- 23:52:16实读可用：/tmp 94,974,496,768B，/storage2 29,304,553,472B。本次未清理任何文件；正式归档前仍重新核查。
- `s0_model_review_snapshot.py`及其测试已提交5430dc5：3项真实小文件测试（另含8种拒绝情形）、Python3.6通过，尚未部署/运行。绑定S0自己的最终网表、12PT、连接及别名证据，复用已有全行时序表解析器，仅聚合事实，不自动通过。未知连接/别名查询尚未运行，等完整导出/清单后再按原团队锁进行；不借N1旧数量。
- copy-only归档工具9422302已push但未部署；还需n1_archive_runtime/t80_archive_runtime/transport_report_stage等依赖，66包不含这些模块。保留源且完整回读；旧T80归档入口不直接适用S0。
- 一次本地中文stdin进度更新因编码报错，未写文件；随后改为apply_patch记录。5430dc5只含审核工具，不能误称该提交已记录上述进度。

**23:44:14实查：原队列172535仍在SAIF阶段；L01/L02完整活动已通过，L03 simv187750已退出，正进行输出与窗口核对，尚不计为通过。gate14/354,816输出及synth08已完成，不重跑。前台只读watcher177140，所有输入结束；服务器桌面T80和旧八路不动。**

**23:27:38最新实查：gate14全部完成，354,816输出逐坐标/result/saturated及写回核对通过，queue completed=2、stage=saif。父172535，SAIF VCS子180054运行54秒（1471 modules done），error=None；前台只读watcher177140。gate路径为66b9496/runs/s0_finish03_gate/t80_s0_gate，SAIF路径为同包runs/s0_finish03_saif/t80_s0_saif。全部输入结束，无半截命令；不重跑gate或综合。严格无SDF，internal total在门级不可观测的边界仍明确保留。**

**23:24:37最新实查：gate已逐例通过12/14（extremes、rounding、L01–L10），当前L11 simv178996；父172535，completed stage仍1，error=None。前台watcher已替换为177140（旧173225仅Ctrl+C退出），命令`local_runs/s0_finish03_case_watch_command.txt`现在显示case_progress回执及当前日志；98978输入已结束。尚未获得完整gate summary，不重跑。已有1bbd126已push。**

**后续归档注意（只读检查所得，未执行）：**现有`t80_archive_runtime.py`固定旧T80队列schema及`session/t80_kind`目录，不直接接受S0的`t80_s0_kind`。最终持久归档需按S0实际终态适配，保留已核验tar写入/完整回读原语；现/tmp包含多份历史失败包，不能盲套旧入口。归档前重新查空间与终态，不动桌面T80或旧八路。当前未新增清理、压缩或备份操作。

归档实施还须注意：`n1_archive_runtime.no_open_users`检查cwd，归档进程本身须从源runtime之外运行；原通用入口会扫描整个runtime，不能把只检查一个bundle终态误称所有历史子目录已验收。源文件不得删除，完整解压回读和前后哈希一致后才记录备份完成。S0 report入口只写报告文件、不自动创建旧归档器期待的session state，需明确适配而非伪造旧T80队列状态。

S1准备仅做了只读源码核对（未开发）：团队仲裁器和memory_router均为单pending、允许retire同拍接新请求。保持原平台buffer参数，必须先测原通路接受/响应间隔，不能把仲裁器队列深度直接当下游吞吐。router是否限制服务率以测量判断；当前RTL完全未改，S1尚未开始。

**23:14:55最新实查：SRAM双清单核对已通过，当前gate已进入VCS编译子174044（已运行10秒），父172535、watcher173225继续，无错误。端口DC173089已完成26秒。全部输入结束，不重启；6683ce5已push。下一步等真实gate14结果，随后原队列SAIF12/timing/DRC/PT12。**

**23:12:55实查：66b9496/s0_finish03父172535运行，structure已完成、completed=1，当前gate端口DC子173089，无错误。开始23:11:48.772018。前台只读watcher173225；全部96034/10794/4606输入已结束，无半截输入。下一次命令前只退出该watcher，不碰后台队列或锁。综合仍是a5f138e/synth08，不重跑；T80桌面及旧八路不动。**

**23:10当前唯一输入exec10794：13行`local_runs/s0_finish04_launch_1881cd3/transfer.ps1`，启动器SHA3b20c94cc969816b8f171808b2c53a62fb9db9a6e2ae2e905fae6b362732a649。66b9496包853文件和manifest2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4已服务器核验，96034输入结束。新目标66b9496/runs/s0_finish03，仍引用a5f138e/synth08已完成网表；尚未观察新PID。1881cd3已push。先收完输入，禁止并发VNC/重跑；下一个只读watch命令在local_runs/s0_finish03_watch_command.txt。最新report请求为S0_BUILD_REPORT_REQUEST04_20261115.py，未部署执行。**

**23:07新失败：finish02父168421在gate的SRAM配置来源核对停止，VCS尚未启动。门级DC端口探针子168925已正常完成27秒；不是数值失败。重链接当前header已被不可变`synthesis_inputs.json`记录，但旧gate仅查`source_inputs.json`。本地仅对明确S0 profile同时核对两份清单哈希、全部历史header、当前header和实际模型；冲突/缺失/任一字节变化仍拒绝，不修改完成综合的任何文件。3项新测试（含6种损坏情形）及2项来源路由测试通过。当前watcher169108已自然结束，Bash空闲、无EDA；全部旧失败保留。下一新工具包/finish03，不重跑synth08。**

**23:03:35实际进展：新a7e7e49/s0_finish02父168421已运行，structure完成，completed=1；当前gate/DC端口探针子168925（common_shell_ex，96%CPU），error=None。队列开始23:02:32.412418；明确使用a5f138e/synth08 summary e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916。所有29202/56347/87739输入已结束。VNC当前为前台只读watcher169108，不能向它盲输shell；仅需命令时Ctrl+C退出watcher，不碰后台队列。转发91027保持，T80桌面/旧八路不动。**

**23:02部署接续：a7e7e49修复包853文件/manifest4d0699ff21c1708484f182e09a934ea918255ddfc116f1f2a179ec7b015e8766已服务器核验，29202输入结束。当前唯一输入exec56347，13行`local_runs/s0_finish03_launch_bc0a897/transfer.ps1`，启动器SHA5650846f3f3c16aba83a87cb839ff456f102adf8692666f350ddf30c3ed7a9d7。bc0a897已push。目标新包runs/s0_finish02，明确引用a5f138e/synth08，注册a5+9ff+05原证据。尚未观察新PID，不要重复执行；收完截图后查新driver/state。`S0_BUILD_REPORT_REQUEST03_20261115.py`已按新包/finish02准备，但未部署执行。**

恢复先读AGENTS、当前用户计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`、本文和STATUS。服务器桌面T80、旧八路不改；S1–S4未开始。

## 已完成

- a5f138e独立包853文件和manifest已服务器核验：`c4774571c8aebe323657a5aaebc017f24324396b28ea6b2852e32e40a213b924`。
- `/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-a5f138e/runs/s0_synth08/t80_s0_synth`最终链接已正常完成。父163793/DC164078结束，22:55:16接续守卫观察passed。只复用经完整核对的9ff三块，不重复映射。
- summary SHA `e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916`。
- 新最终报告：保守项目面积0.9535222591004618 mm²，明确新增部分0.7926218383005581 mm²，整机library area4475738.758645；setup +0.000386715 ns，hold +0.0055688 ns；92小宏+128大宏=220，latches0。声明时钟6.666666ns/低频66ns。独立时序审核、gate14、SAIF12/PT12仍待，不能把综合完成等同整阶段验收。
- 库冲突已修复：新报告用原DDC的canonical库路径，保留相同字节的新库副本。原三块及全部失败文件未改。
- 14e6b1b自动接续守卫165061成功等待并启动finish父165305；该父在取锁/建queue/启EDA前失败：`common.sha(__file__)`传入str，而函数要求Path。旧`ops-a5f138e/s0_finish01_launch`请求/日志保留，不能重复启动此控制目录。

## 当前修复与下一步

- 本地`s0_finish.py`仅改成`common.sha(Path(__file__))`。新增实际execute入口和17个阶段磁盘回执测试，包含错误工具哈希拒绝；共3项队列测试通过。外部EDA及锁mock，真实哈希和文件写入未mock。
- 新工具包需从a5f138e overlay生成，原综合无需重跑。新finish入口将**新工具bundle与a5综合bundle明确分别注册**，并注册9ff缓存及05seed；使用新独立session/控制目录。
- 最后22:56:55父165305已不存在；VNC18874435/workspace3为Bash空闲。只读watcher165525已Ctrl+C退出，所有输入49908/78220/51072/37467/79863/14118已结束，无半截输入。板端转发91027保持，FileZilla关闭。再次启动前核对真实进程/锁/空间。
- 依次完成新网表structure、gate14、SAIF12、timing/DRC、PT12，汇总及活动模型说明后冻结S0，再进入S1。原T80同源ASIC14/240和FLOAT可引用，旧网表gate/功耗不能替代新网表。
- `S0_BUILD_REPORT_REQUEST02_20261115.py`目前指向a5f138e/finish01，**必须改为实际新finish包与session后再部署**。新a5综合报告作为独立输入保存。

## 历史路径，禁止重启

详`CONTEXT_CHECKPOINT_20261115_S0_RELINK_READY.md`及其之前检查点：synth03无效set_map_only、synth05/06设计容器重复、synth07最终库路径重复。0e首次relink因手工抄错state SHA在EDA前停止；正确state为43294b528a89c8d0239ccd5e92ee597fc26531217fe3c5245052112030744405。

本次未清理任何服务器文件。既有可恢复编译缓存归档回执继续保留；全部桌面T80和旧八路数据保护不变。新/tmp产物最终仍需持久归档。

## 23:44本地准备

新增S0专用copy-only归档工具、终态合同及测试：严格绑定17阶段、报告和同网表；原tar完整回读原语复用，3项测试与Python3.6语法通过。尚未部署/运行，没有压缩、删除或修改任何服务器证据；持久盘空间须实际核查。旧归档入口目录契约不适用于S0，不能直接调用。新工具将全部源保留，归档成功不自动授予阶段验收。
