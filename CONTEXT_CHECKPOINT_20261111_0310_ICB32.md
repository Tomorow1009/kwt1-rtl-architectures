# 2026-11-11 03:10 持续执行检查点

**继续执行，不要结束等用户再催。** 压缩后先读AGENTS、`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点和STATUS的icb32_c64_execution。旧计划/失败路径/三包身份见02:32、01:41、01:12检查点。

## 新增实际完成

1. **e65新综合已完成**，原唯一队列75421正常结束，02:55确认锁正常释放。`runs/icb32_r4_first01/icb32_synth/summary.json` SHA `fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`，随后独立断言通过。SS/.99V/125°C、6.666666ns，setup +0.0000715256ns、hold +0.000253469ns，128大+96小宏、0锁存器、最终无组合时序环、constraints无违例。新增面积保守上界**0.926561671200504mm²**（全部SoC标准单元+加速器内部宏），已知新增0.7658783064005987mm²，整机4.448778171173114mm²。详见`handoff/team/evidence/ICB32_SYNTH_20261111.json`。
2. **497真实CPU竞争两例通过**，L01/extremes共50688输出；CPU等待期间最大DMA接受次数均1，限制8。各56/65轮scratch核对，真实并发请求被观察。摘要`dd4ad0628963c932665a4f1cd11b25d3df4d5cec693da080916b02e8d8c250b4`，02:59:38结束。
3. **497真实E203无复位10阶段通过**，5种配置拒绝带真实store-access-fault、初载取消、4096cycle驱动超时排空、A/B/A，76032输出。实际阶段周期0/0/0/0/0/171/3939/34639/33914/34639，仿真8.7492s。摘要**`edc75947ecbf0bddedc0b96b87fde040599abeab68213295f272cef5833399dd`**（首字符e，尾组f272cef5 833399dd，勿抄成cdc或ce358）。03:01:43结束。两个CPU摘要03:06独立断言，证据`ICB32_CPU_DIAGNOSTICS_20261111.json`。polling诊断不作为生产IRQ性能/功耗，未改RTL和生产固件。
4. **497只读时序/实际门级端口probe通过**，`runs/icb32_r4_timing01/icb32_timing_audit`，03:06:41结束，SHA `49565632fa09318cd025866883df7dbed1dcfb3e5631ed4030e79011b9647ae1`。3个TIM-134网为`u_e203_subsys_top/core_csr_clk`、`u_e203_subsys_top/hfclk`、`u_e203_subsys_top/u_sirv_aon_top/crossing_clock`，六模块边界核查通过，未改网表。证据`ICB32_TIMING_PROBE_20261111.json`。

以上是新增报告/功能证据，**不是完整PPA验收**。还需全时序范围/未知活动/缺模型审阅及同网表gate/PPA。check_design汇总包括未用输入706、未连端口10432、无负载cell4、常量连接9935、同cell多pin连接1000、无负载net706；保留原始报告，不仅凭警告名称全部豁免。PT的完整no_clock/disabled-arcs等在后续功耗报告中读取。

## 唯一当前任务：新网表gate14＋12活动

- 03:08:13从497包启动**PID209764**：`runs/icb32_r4_gate01/icb32_gate`。最后实际**03:09:28.275099 running**，尚无完成用例，mapped_probe.log child209836。不要重复启动。父日志`icb32_gate01_launcher.log`。没有其他新EDA并发。
- 该任务引用**e65**的实际synth目录及上面明确SHA，14默认用例、12层`--activity-cases`；预期无SDF功能门级，不能宣称延迟签核。CPU诊断串行launcher188709已结束，不再当前。
- 当前包根父目录仍`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。e65=`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`；497=`light-light126-icb32-r4-20261111_011258-49759e108719`；R1=`light-light126-icb32-r1-20261111_012941-f95e940862ca`，R1服务器尚未执行。

## 桌面、同步、已尝试路径

- 板端VNC window20971587，第三终端交互cwd**仍为f95 R1包根**（Popen的cwd不会改变交互终端）。FileZilla关闭，原代理保持，无本地仿真/构建。
- 当前终端最后命令是只读gate状态查询，可Up Return重复；查询文本`E:/fpga_race-two/takeover_local/icb32_gate_status.txt`，截图`icb32_gate_status.png`。它先clear，再输出状态/已完成例/launcher尾部，截图前等1s避免VNC画面尚未刷完。其他查询后需重新type对应文件，不盲目Up。
- 服务器操作只通过板端VNC；FTP只有Linux FileZilla。`F:/linux_fpga_try/ac820.ps1`支持type/key/screenshot。单次type最多1000字符；第一次长诊断命令在本地被拒绝、随后含嵌套转义双引号的tcsh命令被解析拒绝，**均未启动任务**。已换成787字符Popen调用`/bin/bash -c`固定两条命令，实际串行成功。不要再执行旧`icb32_start_diagnostics.txt`；v2也已成功，禁止重复。截图路径有一次try_try拼写错误，仅截图失败已补读，无服务器影响。
- 本地最后独立核云端为**31a732e4649315af31cd7eb28cd30631edea64a4**（02:32检查点）。本轮三份新证据/当前记录待提交。无RTL、固件修改。一般push先受网络sandbox拒绝，按已授权目的地require_escalated成功；无auto-review拒绝。

## 继续顺序和待办

1. 跟进当前gate，失败保留目录并定位实际工具/网表问题；不要提前把未完成14/12说成通过。
2. gate通过后，按实际summary SHA执行12层`icb32_power`，单队列串行；读新数值、单位/宏覆盖/未知活动、全时序报告。不能套旧29.6273mW。`icb32_report.py`已在497包，可生成JSON/CSV/中文报告。
3. 固定候选后执行自己的1200真实ASIC/E203/30412800输出，数据根`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest `0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。根据batch_progress端到端耗时留20%余量，不按芯片加速比例外推。
4. R1真实ASIC/PPA及旧8完整功耗对照、干净目录复现/交付仍未做。R4已测12层平均34616周期/4333.256task/s，5000未达；不改计时口径。原fcd 664.393/1200通过保底保留。
5. 11/11 18:00硬冻结、11/12 17:16交付准备、11/13晚上截止不变。保持当前架构；及时记录并同步，压缩后重读，继续实际工作。

## 03:12增量

最新实际03:12:04.597097，gate仍driver209764，probe和VCS编译已完成，正在layer_01.log/simv child212264，完成用例列表尚空。未观察到错误。当前所有新增文件都是证据和文档；真实受测RTL/固件不变。立即同步这些记录后继续gate，不重启。

## 03:18增量（后续压缩接续）

- 本轮证据/检查点/验收及README/运行手册已提交并云端独立核验`1477dd99aae44dd0d4527cba8f5c6e5cc6e9992a`，无RTL或生产固件改动。
- 首层门级仿真03:15:33结束，日志正常$finish，CPU time 250.000s，仿真时间328849967115fs；实际捕获25344行，VCD12012.24MiB（约11.73GiB）。全层阶段PASS要等活动核验，不能仅凭仿真退出转为完整通过。
- **最新实际03:17:42.863337 gate running driver209764，L01 activity_scan child214920**；完成用例列表仍空，原simv212264已结束。活动扫描器编译child214904已完成。不要重启任何已完成阶段。
- 当前最后终端命令再次是`icb32_gate_status.txt`，可Up Return；交互cwd仍R1。新增窗口进度只读脚本`icb32_gate_window_progress.txt`仅读取VCD末16KiB和小capture，不扫描全波形。其首次正则美元符号被tcsh解析拒绝，未执行；已去掉美元符号修正。不要将末尾16KiB没有时间戳推断成停滞，完整日志已证明正常结束。
- 后续继续当前12层活动及14门级，再12功耗和自己的最终1200等。若要启动12层功耗串行命令，可用可见终端Python构造固定`python3 ... && python3 ...`命令后Popen/bash，避免嵌套转义双引号、shell美元变量或超1000字符；实际启动前必须取得真实gate summary SHA、检查锁/新session，不提前运行。

## 03:22本地计划内对照接续

- 服务器03:21:17仍209764/214920在L01活动扫描，未有完整用例回执。03:19实测扫描CPU99.7%、elapsed3:32，已读2099811996/12595749229B（约16.7%）；首层扫描粗估约21分钟，不能按芯片周期当宿主速度。后续gate/活动预计数小时，原作业持续，不并发服务器任务。
- 利用等待时间，补计划内“同R4、压缩和raw输入”剩余11层本地贡献对照。**本地exec session50608正在跑**，新目录`local_runs/icb32_datapath_20261111_032040_657032`，现成入口`local_icb32_datapath_verify.py --rows 4 --raw --prefetch 1 --jitter 0 --cases layer_02 ... layer_12`，Vivado2018.3和项目venv；02/03两层已通过38052周期。不是新增RTL/验证框架，不占服务器。
- L01同配置raw已在`icb32_datapath_20261110_225510_415689`通过pf0/1（pf1=38052），不重复跑。新11层结束后，核旧L01和新11层的全部硬件/TB哈希、布局、配置一致，再与压缩R4 `icb32_datapath_20261110_225139_667062`按坐标比较12×25344输出；若哈希不同不得拼接。该对照明确本地pin_mock/无CPU/PPA，不转成正式服务器对照或最终1200。
- 当前最后终端命令为gate状态查询，可Up Return；本地新run受测文件不要改动。已有云端1477dd9，03:18/03:22增量尚未提交。

## 03:24本地对照完成

- 本地session50608已正常完成（11层全38052周期），目前无本地仿真。`takeover_local/compare_icb32_codec.py`已实际运行，通过三份报告的全部RTL/TB哈希、当前文件哈希、配置/布局校验，并对12层304128输出独立按坐标比较相同。已有L01可合法复用，不重复运行。
- 新证据`handoff/team/evidence/ICB32_LOCAL_CODEC_20261111.json`和中文`workspaces/arch03/ICB32_LOCAL_CODEC_COMPARISON_20261111.md`：raw平均38052周期/47008B/36176事务，压缩34616周期/37102.6667B/31223.3333事务；周期减少9.0297488%，吞吐提高9.9260458%，事务减少13.6904762%。明确本地pin_mock，无CPU/PPA；非新正式服务器配置。
- 最新服务器03:23:35.530592仍gate209764、L01 scan214920、completed=[]，无失败；该波形完整扫描尚未完。新证据/创新说明及检查点增量待同步，当前受测服务器包/RTL不变。
