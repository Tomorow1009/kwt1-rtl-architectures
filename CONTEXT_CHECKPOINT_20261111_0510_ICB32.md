# 2026-11-11 05:10 持续执行检查点

用户要求能继续就持续做，不逐项停下；压缩前写Markdown，压缩后重读计划和检查点。当前有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`：原32位ICB、无损输入真实落库成功ACK后解码、16×4 MAC；11/11 18:00冻结，11/12 17:16交付准备，用户截止11/13晚上。不要因后台EDA运行中就结束本轮。无主动子代理、无新goal。

## 已完成及实际结果

- 新R4真实ASIC/E20314例354816输出、IRQ/WFI通过；12层平均34616周期、150MHz折算4333.2562977 task/s，未达5000。e65的ASIC摘要`e5d009732e822cb5cf730e85b652a160f5022ba0197a9e6ff60960d76121d604`。本地两组贡献对照也完成：同通路R1/R4局部3.35914倍；固定R4 raw/压缩平均38052→34616、周期减少9.0297%，均不能当R1服务器PPA。
- e65新综合完成，SS/.99V/125°C/6.666666ns，setup +0.0000715256ns、hold +0.000253469ns、224宏、0锁存器、无组合环/约束违例。保守新增面积上界0.926561671200504mm²，整机4.448778171173114mm²。摘要`fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`；完整时序范围/功耗待审。4条LINT-1已查明是原平台无输出连接实例，其他警告不自动豁免，详情综合证据。
- 497真实CPU竞争2例50688输出、10阶段无复位恢复76032输出通过；5次真实store trap、取消、4096周期超时排空、A/B/A，CPU最大等待1个DMA机会（限8）。两个摘要在`ICB32_CPU_DIAGNOSTICS_20261111.json`。
- 原ecf旧队列已自然完成，旧8路门级14/活动12和原DMA16 MAC有效扫描已收回。旧8功耗仍缺；原fcd自己的1200、664.393 task/s与29.6273mW/44.5931µJ布局前估算保留，系统功耗false，不能转移给新RTL。
- 被动计数工具只改TB/报告，DUT和生产固件未变。本地L01/extremes共50688输出/17工具检查通过；X读101376/写6336、W读409600/写16384、MAC1622016，首层利用率73.166%。真实ASIC计数仍待964运行，R1计数未实测。
- 新`ICB32_DESIGN_REPORT_20261111.md`准备稿已完成，包含实际架构/ABI/格式、面积和贡献对照、来源及未验项；14个本地引用有效，交付索引已链接。尚未将功耗、1200或官方精度标成通过。

## 当前唯一重作业：497原gate，不重启

**05:05:51.747321实看：driver209764正在L05完整活动扫描，child291732。** 原gate启动03:08:13.465421，运行`runs/icb32_r4_gate01/icb32_gate`，原锁由其持有；没有清锁或并发EDA。

已完成4/14门级、4/12完整活动，每层25344输出、真实IRQ/WFI均通过，周期L01=34639、L02=34607、L03=34603、L04=34595，与ASIC一致。各原始VCD和规范化回执哈希见`handoff/team/evidence/ICB32_GATE_PROGRESS_20261111.json`。最终summary尚未产生。

L04新增：VCD12564314076B，SHA`dbff10b7edea7cdb0120b50944f67d1522b2a92dec7a63e81153dee51e5cf92c`；规范化回执SHA`6d83bbbf63bf592af20869366eb69acebc39e58ffa2d0684fd5d50fd67ca5cf9`，05:05:29.576624独立断言通过。窗口92949.990705..323583.300975ns，未知值记录958805，仍需解释；不是翻转次数/覆盖率。初次抄错回执首组末字符f为1导致只读断言失败，分行重读纠正后成功，原数据未改。

每层含完整大VCD扫描约28分钟。按实际宿主进度估剩余时间加20%，不能把芯片加速当仿真加速；scanner结束后还会hash，case_progress未发布前不能算完整通过。

## 后继已经启动：285397，禁止手工重复启动其计划阶段

新`icb32_finalize_queue.py`已从提交`e09331dac7f285521acd7bf98522d3c730ec1798`导出独立ops包。正常板端Linux FileZilla上传、安全新解包、4输入及4保护测试通过。过程不改任何已上传运行包。失败保护测试覆盖原gate未完成/失败、身份或摘要变化、活动缺失及严格串行范围。

- 小包`light-light126-icb32-ops-20261111_045128-e09331dac7f2.zip`，6330B，ZIP SHA`cb5129b433e8e00462de450ee9c0a9550609799642573a210edd4a06a67cca53`。
- manifest SHA`b5ff86370dabada2f02f3da376ad1e892daf75536e86606aa4ba7ee6c9ae1568`。
- 进程285397于04:56:04.647646启动，核验964全部输入和固定100数据后于04:56:43.020316建立state。**04:58:45.702948实看waiting_gate、completed=[]，唯一重作业和锁仍为209764。** 启动后首次状态查询过早而无文件，随后确认正常，无重复启动。
- 后继明确绑定原gate PID/启动时间和e65综合SHA。原14门级/12活动全部通过且锁释放后，依次运行`icb32_r4_finish01_power_l01..12`（每项后实际数值提取）、`icb32_r4_finish01_metrics14`、`icb32_r4_finish01_final1200`。失败停止，不重试/清锁。
- 状态在**964包**`runs/icb32_r4_finish01_queue/state.json`；launcher在**ops包**`launcher.log`。后续每层原始数字在队列`layer_XX_numbers.json`，完成后准备`report_request.json`，没有自动批准功耗/时序或自动导出最终报告。
- 因此不要另行启动同范围power/metrics/batch。观察原gate和后继，读取实际功耗后审阅；队列失败则保存真实原因，修复工具要新包/新session，不能原地重启。

## 运行包与身份

共同服务器父目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

1. 主ASIC/综合e65：`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`，`runs/icb32_r4_first01/icb32_soc`和`icb32_synth`。75421旧后继已结束，不能重启。
2. 诊断/gate497：`light-light126-icb32-r4-20261111_011258-49759e108719`，630输入/三固件已核验。ZIP SHA`ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4`。
3. R1对照：`light-light126-icb32-r1-20261111_012941-f95e940862ca`，607输入预检通过，服务器ASIC/PPA未跑。
4. **当前交互cwd/后继运行根964：**`light-light126-icb32-r4-20261111_043048-96443c284a1c`。ZIP11139802B/636输入，SHA`18cf4c4def9fcab43174de974c6ca45851af35b6ac1ea701915bd8c57b41b161`。04:42:01.946139预检三固件和生产身份通过，manifest SHA`3afd9a35da42cc9c237314bd18a2d186ecea693e6bb2e82c716d8b8548f938e5`。

964的34项RTL/生产固件/运行映像与497相同。生产FW manifest=`fde6cbea29cda15a066a9f3710d8684ae0ba14f73dfd497a80e0a68b3952849b`、ELF=`8cf32dcdfd842936127292652b21b4f7c2bd0529da73620f1c0949fe213ec233`。序列诊断ELF只有非装载debug/symbol节变化，sequence.bin/verilog相同；不能说所有ELF相同。详细`ICB32_METRICS_PACKAGE_20261111.json`。新被动观察器不要求重复现有同网表gate/综合。

## 未完成与接续顺序

1. 原gate剩余10例/8活动；收回最终summary SHA并确认后继自动接手。保持队列285397，不能重复启动。
2. 12层实际功耗/能耗、单位/224宏/活动/未知值和任务模式时序说明。保持system_power_verified=false直至有足够依据；无需扩展无关大扫描或物理签核。
3. 后继964普通ASIC14真实被动计数/干净目录复现；自己的最终100×12/30412800输出。固定数据`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。看batch_progress宿主ETA并加20%。
4. 队列完成后审阅自动生成request，填保存的失败/未验history，再运行`icb32_report.py --request ... --output <新目录>`。该报告会独立重审新1200回执以及完整网表活动，串行执行。
5. 最终同配置JSON/CSV/中文报告，更新设计报告、材料和提交包；R1实际PPA及旧8功耗对照后排，主候选合格交付优先。官方600样本精度、物理签核未验证，内部回归不得冒充官方成绩。

## 当前客户端与避坑

- 板端Linux VNC重新盘点20971587，FileZilla已断开退出。原FTP代理21036/VNC relay23793继续，不重复启动。服务器命令只经板端VNC、文件只经Linux FileZilla；本地到板端暂存允许现有helper。
- 当前最后VNC命令**`takeover_local/icb32_gate_status.txt`**，cwd964包根。通用`icb32_gate_live.txt`动态读取209764的child/VCD偏移；`icb32_ops_status.txt`读285397后继状态及锁。不要用旧固定scanner PID；最后命令若变成哈希断言就不能误Up当进度。
- `F:/linux_fpga_try/ac820.ps1`沿用已授权提升和prefix，不读/打印凭据。当前无CUA会话或completion_summary欠项。type一次≤1000字符；远端tcsh避免嵌套转义双引号与美元符号。exec返回session先poll结束再读新截图，避免旧图。
- Python为`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`；Zig在父目录takeover_local/tools。不重跑旧adapt_icb32_sequence.py覆盖4096修复。不rerun一次性progress_04xx/05xx脚本使状态倒退或重复记录。
- 本地4队列检查首次只因Windows路径测试期望写死失败，修测试后通过；Set-Content一次位置参数写文件失败，改明确-LiteralPath/-Value后成功，无服务器修改。新计数第一次本地变量声明顺序编译失败已修并保留目录。详见04:30检查点增量，不算DUT失败。
- 云端最后已独立核`e09331dac7f285521acd7bf98522d3c730ec1798`；05:00/05:10进度、L04和设计报告待本次提交同步。个人分支持续同范围同步已授权。无自动审批拒绝，无本地长任务。

## 05:22增量：持续运行与云端同步

- 05:10检查点、L04、后继入口和设计报告已提交并独立核对云端`502915f49a1a20231a9895613959c40159f8b341`。新报告补充当前12层的理想事务上界4804.099 task/s、实际占比90.199%，由原始计数推导；不称功耗效率，不改目标窗口或增加结构优化。
- **05:21:43.802109实际：原gate209764仍运行，L05活动291732，CPU99.7%；后继285397仍waiting_gate，completed=[]且进程存在。** 05:21:04.049494读取VCD偏移8553754615/12447866354B，约68.7%。仍只有一个重作业，没有失败/重启。
- 新通用`takeover_local/icb32_all_live.txt`已实测可用，合并显示原gate完成层、后继状态/最近结果和实际进程。它是**当前最后VNC命令**，cwd仍964包根；Up Return可重复此状态查询。需要VCD偏移时使用gate_live。FileZilla关闭，未重复上传。
- 本地一次性progress_0510.py直接执行遇到Python3.8源文件编码报错；文件严格UTF-8读取正常，加入编码声明并用显式UTF-8读取compile/exec后成功保存。该脚本已执行，不要重跑其追加L04操作；项目JSON/Markdown均已复读正常。没有改服务器数据或RTL。
- 持续等待原gate和后继，后继自动完成power12→metrics14→final1200。用户尚未暂停；不要发“稍后继续”的终止回复，不重复启动后继已有计划阶段。重要进展和下次压缩前继续保存根交接与检查点。

## 05:32增量：第5层完整通过

- **05:31:03.136673实看：原gate209764已完成L01–L05，当前L06映射仿真306705；后继285397仍waiting_gate、completed=[]，两个进程均存在，只有一个重作业。**
- L05实际25344输出/34587周期，真实IRQ/WFI与完整活动通过。VCD12447866354B，窗口92949.990705..323529.967647ns，未知记录1043091。规范化回执SHA`8e8f859fd7e020609675b1d692c6c3ece9f789555512fd475b30e402bd8362b7`、VCD SHA`06ba83d24e903e963f0ac4bca60983622a4bf13d562a09468ad3f8aeb42a4262`，05:30:31.439827独立断言通过。现5/14门级、5/12活动，不是整批完成。
- 当前最后VNC仍`icb32_all_live.txt`，cwd964，Up Return可用。新增`icb32_gate_receipt_compact.txt`把最新完整层的两个SHA分行显示，减少f/1转录混淆；固定L05断言文件不要当进度查询。FileZilla关闭。
- 云端已独立核`0437edb436a73136a2892d0d74d0c9b3d158a87b`。硬件/固件没有新增改动，新PPA/metrics14/最终1200仍由后继接续，不手工重复启动。继续等待、读实际报告；当前无失败或审批阻塞。

## 05:35增量：第6层活动扫描

- L05证据与05:32检查点已经提交并独立核云端`3df333cbcb9599ea54629b972c91e000bf80ec8b`。
- **05:34:57.836913实看：gate209764当前L06活动扫描309313，CPU99.7%，原L06 sim306705已结束；5层完整回执不变。后继285397仍waiting_gate、completed=[]，进程存在。** 最后VNC仍all_live查询，cwd964，FileZilla关闭，无新本地任务。
- 最终汇总时注意`icb32_report.py`当前默认把任务时序、面积、系统功耗保留false，并在unverified中固定列出协议/恢复/竞争/干净复现。实际CPU竞争/恢复已有独立通过证据，964 metrics14完成后也有干净复现；最终应将同身份的审阅和这些摘要明确关联，或在配套审阅报告解释导出器覆盖范围，不照抄固定待办而误称已完成项目未做。不要为此重跑已有诊断，不在实际PT结果到来前扩大审核或先批准功耗。
