# 2026-11-11 04:30 持续执行检查点

用户要求能继续就持续做，不逐步等待确认；压缩前保存Markdown，压缩后重读计划与检查点。当前有效计划仍`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`：原32位ICB、无损输入落库成功ACK后解码、16×4 MAC，11/11 18:00冻结、11/12 17:16交付准备、11/13晚上截止。没有增加架构、改数值或提频。无主动子代理。

## 已完成

- 新R4真实ASIC/E20314例354816输出、IRQ/WFI通过，12层平均34616周期，150MHz折算4333.256 task/s、7028.611 MMAC/s，5000未达到。比原225770周期整体约6.522128倍，不能全部归因于MAC。
- e65新综合完成，SS/.99V/125°C/6.666666ns，setup +0.0000715256ns、hold +0.000253469ns、224宏、0锁存器、无组合环、无约束违例。保守新增面积上界0.926561671200504mm²，整机4.448778171173114mm²。摘要`fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`。完整时序范围/功耗仍待审核。
- 497包真实CPU竞争2例50688输出、无复位恢复10阶段76032输出通过；5次真实store trap、取消、4096周期超时排空、A/B/A，CPU竞争最大等待1个DMA接受机会（限制8）。详细摘要和独立SHA见`ICB32_CPU_DIAGNOSTICS_20261111.json`。
- 网表只读probe通过。04:11进一步查明4条LINT-1“Cells do not drive”为原平台debug/reset/PLIC的无输出连接实例，网表和结构报告哈希与固定综合摘要一致；补入`ICB32_SYNTH_20261111.json`。其他结构警告和PT时钟/禁用弧范围未审定，没有运行旧DMA16专用audit或额外大扫描。
- 原ecf串行队列已自然完成，旧8门级14/活动12及MAC有效样本扫描收回；旧8功耗对照仍缺。原fcd自己的1200通过、664.393 task/s和29.6273mW布局前估算保留，不能借给新RTL；旧系统功耗仍false。
- 本地同通路R1/R4输出一致，局部3.35914倍；固定R4 raw/压缩12层304128输出一致，平均38052→34616周期（减少9.0297%）、事务减少13.6905%。均无CPU/PPA。
- 重新阅读赛题原图第12/14、13/14页，交付索引补全各材料位置和缺口；官方新增面积2.25mm²，本项目仍2.00mm²。原图不要求物理布局布线验收；无SDF功能门级和布局前功耗如实标注。

## 当前唯一服务器重任务

**497包`runs/icb32_r4_gate01/icb32_gate`，driver209764。最后实看04:27:44.690936：L03活动scanner254612运行17:28，CPU99.7%，读9,486,685,144/12,584,787,471B约75.4%。** 原gate从03:08:13开始，未重启，未清锁，无并发EDA。

已完整完成2/14门级及2/12活动：
- L01：25344输出，34639周期；VCD 12,595,749,229B，SHA`79d9318980a13bd5afbb2b67cbfe9ae3f0375df35f41cc98e7bf06c118c5705f`；未知值记录996956。
- L02：25344输出，34607周期；VCD 12,567,832,939B，SHA`a9c2e2755850991776db9845105859dc41f88c1ddb577e346b9f2ecd3ab8244d`；未知值记录1011115。规范化回执SHA`178d24292c3b30da9e8cb6da7ee93bb0de6400b366a4456c6375c0f665c67146`，04:07两SHA转录已在服务器断言。

两层真实IRQ/WFI均通过。部分证据`ICB32_GATE_PROGRESS_20261111.json`，不是最终summary；未知记录不是覆盖率/翻转次数，也没有批准功耗。每层含完整大VCD扫描约半小时，剩余按实际宿主进度留20%余量。

服务器包共同父目录：
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`

- 主ASIC/综合：`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`，`runs/icb32_r4_first01/icb32_soc`和`icb32_synth`；已完成，不重启75421旧后继。
- 诊断/gate：`light-light126-icb32-r4-20261111_011258-49759e108719`，630输入/三固件核验通过；当前gate明确绑定e65综合SHA。ZIP SHA`ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4`。
- R1对照：`light-light126-icb32-r1-20261111_012941-f95e940862ca`，607输入预检通过，服务器ASIC/PPA未跑。VNC交互终端cwd**仍在此R1包根**，Popen只改变子进程cwd。

## 本地新增被动计数工具（尚未新包服务器验证）

查到计划要求的内部SRAM访问及MAC/总线服务计数尚未导出，因此本轮补齐**测试观察器和报告**，没有改DUT/生产固件。不要把这一必要补缺误写为新的硬件优化或新的功能失败。

- 新`tb/arch03_icb32_metrics.svh`、`scripts/icb32_bus_metrics.py`：在仿真外部观察96个SRAM逻辑端口和64个MAC握手，统计三段接受→应答延迟、ready等待、响应反压、在途等待、退旧接新和结果反压。先退旧owner再接新；不驱动DUT，不进入整机VCD功耗scope。
- `icb32_soc.compile_design`对普通ASIC运行生成独立metrics monitor包装，原生产monitor原文保持；contention诊断不插入。编译契约冻结生成文件和计数脚本；run_case解析计数入回执。
- `icb32_report.py`可核对日志计数、导出各层MAC利用率/事务率/内部SRAM次数；旧回执缺字段保留null。最终batch和重审补100样本编码字节min/mean/max。硬件身份比较只取平台RTL，不把测试台变化误判为新硬件。
- 现有本地monitor fixture的`--bus-metrics`接通。**`local_runs/icb32_monitor_fixture_20261111_042234_295948`两例L01/extremes通过50688输出，34639/38052周期均不变；session33908已结束。** 两例X读101376/写6336、W读409600/写16384、MAC1622016；首层利用率73.166%、0.90609事务/周期。明确无E203、无PPA，R1计数尚未实测。
- 第一轮`...042157_287911`在编译因计数任务引用变量早于声明失败；仅把插入点移至声明之后，第二轮通过。失败目录保留，不当硬件失败。
- 17项现有ICB32工具测试全部通过，Python编译和git diff --check通过；本地无运行任务。小证据`handoff/team/evidence/ICB32_PASSIVE_METRICS_LOCAL_20261111.json`，运行手册已补。
- 与497比较，`workspaces/arch03/rtl`、arch02算术/宏适配、正式`kwt_icb32`/main/start固件Git差异为空。新工具需提交、干净打包、正常FileZilla上传并核验；**当前服务器497完全没改**，不能声称服务器已具备计数。

## 未完成与下一步

1. 提交/云端同步上述工具与检查点，`package_icb32.py`从干净Git导出R4新测量包。正常FileZilla上传后仅做输入/生产固件与e65一致性预检，不并发EDA。
2. 继续原gate剩余12例/10活动。完成后读取最终immutable summary SHA、进程与锁，串行12层`icb32_power`，审核单位、224宏模型、活动/未知值与PT时钟/no_clock/disabled-arcs。
3. 新工具包的普通`icb32_soc`14例作真实计数及干净目录功能复现；保留与旧ASIC/Gate逐输出及周期对照。测试台新增计数不要求重做已有同网表gate，不新综合同一DUT。
4. 候选自己的最终`icb32_batch`1200真实ASIC/E203/30412800输出，固定`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。数据一次编译、每任务冷启动，按batch_progress估时加20%，不继承旧1200。
5. 最终同配置JSON/CSV/中文报告、功耗审阅/交付材料；R1实际ASIC/PPA和旧8功耗对照后排，主候选完整交付优先。若未达到5000如实报告，不改窗口。

## 客户端、云端和避坑

- 最新已独立核云端**49d0b4d52c99a4d101eb0b14577da2de311f49b3**，包含前两层和LINT-1审阅；新被动计数/本检查点待提交。私人仓库/个人分支持续同步授权有效，不重复询问。
- 板端Linux VNC window20971587已重新盘点；最后输入**`takeover_local/icb32_gate_live.txt`**（已实际成功），Up Return查询driver209764及即时child的CPU/打开VCD位置；驱动结束后用stage状态查询。`icb32_gate_status.txt`读状态及已完成层，`icb32_gate_latest_receipt.txt`读最近完整层。旧固定L01/L02 PID查询不可复用。
- FileZilla关闭；FTP代理21036/VNC relay23793继续。服务器命令只经板端VNC，文件只经板端Linux FileZilla；本地到板端暂存可用既有helper。新上传目标仍`icdesigns0.nicu.cn:18888`的`/IC/light-light126-undergrad-d2-20261109`。
- `F:/linux_fpga_try/ac820.ps1`需已有授权提升才能访问板端密钥；不读取/打印凭据。无CUA会话，无completion_summary欠项。单次type≤1000字符，远端交互tcsh：避免嵌套转义双引号和美元符号；之前仅只读查询的缩进正则失败已修复，无远端状态改变。
- 本地Python是`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`（在父目录）；不要误用repo相对venv。不要重跑旧`adapt_icb32_sequence.py`覆盖4096超时修复。用Python UTF-8编辑JSON，避免PowerShell大小写键丢失。
- 重要进展及下次压缩前继续更新本文件/新检查点和根交接；压缩后重读计划、AGENTS、STATUS、当前检查点再继续。仅用户明确暂停才关闭板端客户端，远端作业照常。

## 04:46增量：新包已云端/服务器同步，L03完整通过

- 云端已独立核对`96443c284a1c865a8718ed7bb93a9e8ebfe48c09`。由干净提交导出测量包`light-light126-icb32-r4-20261111_043048-96443c284a1c.zip`，11139802B/636文件，SHA`18cf4c4def9fcab43174de974c6ca45851af35b6ac1ea701915bd8c57b41b161`。17工具检查再次通过。
- 正常板端Linux FileZilla成功上传；随后断开并关闭。服务器安全新解包通过，04:42:01.946139预检636输入、三套固件和生产manifest/ELF全部通过，没有启动新EDA。
- 34项RTL/生产固件/运行映像比较一致。序列诊断ELF只有非装载debug/symbol节不同，sequence.bin/verilog完全一致；manifest仅elf_sha256变化。不能宣称所有ELF二进制一致。详见`ICB32_METRICS_PACKAGE_20261111.json`。首次过宽身份断言失败已定位为调试元数据，不是DUT变化。
- L03门级25344输出/34603周期、真实IRQ/WFI及完整活动通过，VCD12584787471B；VCD与规范化回执SHA于04:39:48.090598独立断言，详见`ICB32_GATE_PROGRESS_20261111.json`。当前3/14门级、3/12活动完成。
- **04:45:34.900281实际：原driver209764仍运行，当前L04活动scanner273982。** 旧L03 scanner254612已结束。没有重启、清锁或并发EDA。
- VNC窗口重新盘点仍20971587，交互cwd已变为**964新包根**。最后命令是`icb32_gate_status.txt`，不再是R1路径或preflight。`../497...`查询仍适用。FileZilla已关闭，继承原FTP/VNC relay，不重复启动。
- 下一步保持原gate完成后串行12层功耗，再964普通ASIC14计数/干净功能复现及最终1200。新工具包预检通过不等于新计数已在真实ASIC运行。时序完整审阅、系统功耗、R1服务器PPA、最终交付仍待办。

## 05:00增量：串行后继已经实际启动，不能再手工启动相同阶段

- 源码/文档/小证据已同步并独立核云端`e09331dac7f285521acd7bf98522d3c730ec1798`。新`icb32_finalize_queue.py`只调度，不修改964或497快照；4项局部保护检查通过，服务器同4项也通过。首次本地测试只因Windows路径期望写死为POSIX而失败，改测试路径表达后通过，运行工具无需修正。
- 独立小工具包`light-light126-icb32-ops-20261111_045128-e09331dac7f2.zip`，6330B/4输入，ZIP SHA`cb5129b433e8e00462de450ee9c0a9550609799642573a210edd4a06a67cca53`、manifest SHA`b5ff86370dabada2f02f3da376ad1e892daf75536e86606aa4ba7ee6c9ae1568`。正常Linux FileZilla上传成功，服务器新目录安全解包，04:55:41.328366输入/4测试通过。FileZilla已断开退出。
- 后继进程**285397**于04:56:04.647646启动；它先核验964输入及固定100数据，状态于04:56:43.020316建立。启动后早查状态文件尚不存在，仅是预检阶段，随后实际确认正常等待，没有重启。
- **04:58:45.702948实看：`waiting_gate`，completed=[]；唯一锁仍是原gate209764/L04活动273982。** 后继不占EDA许可证，也不清锁。不能看到285397就误判成第二个EDA作业。
- 绑定原gate启动`2026-11-11T03:08:13.465421`、综合摘要`fd36940...`。原门级全部通过和锁释放后，自动依次执行12层`icb32_r4_finish01_power_l01..12`及数值提取、`icb32_r4_finish01_metrics14`、`icb32_r4_finish01_final1200`；任何失败即停，不重复子阶段。故**不要再手工启动这些阶段**。
- 后继状态在964包`runs/icb32_r4_finish01_queue/state.json`；launcher在ops包`launcher.log`。完成后生成`report_request.json`，功耗仍false/待审，不自动批准、导出或宣布最终合格。每层实际数值留队列`layer_XX_numbers.json`，可在后续串行作业中只读查看。
- `takeover_local/icb32_ops_status.txt`为当前最后VNC命令，cwd仍964包根；`icb32_gate_status.txt`看原gate已完成层，`icb32_gate_live.txt`看当前child读VCD进度。动态PID以实看为准，ops_boot里285397只用于本后继。脚本第一次写Set-Content未指明参数名失败，导致一次空Return；已改明确-LiteralPath/-Value并成功，没有重复解包。
- 下一步等原gate推进，收回完整summary后审核原队列/后继衔接；用新实际功耗报告完成单位/活动/模型及任务时序说明，最终报告重审1200及同配置材料。R1/旧8完整PPA仍后排，主候选完整交付优先。原fcd664退路不变。
