# 2026-11-12 01:04：B恢复，原综合完成，新v3包上传

## 恢复要求

用户已再次明确继续，并确认开发板上电/网线接好。持续实施直接5×16脉动B，不因普通进度汇报停止；A取消、R4保底，原收敛08:00/冻结09:30:41/11月13日17:00交付不变。先读AGENTS、CONTEXT_HANDOFF、本文件、21:23暂停检查点、20:55检查点、有效B计划和STATUS。不重复R4或旧B作业，不删证据。

## 桌面与连接

00:48初始直连以太网Disconnected/网络不可达；用户接好后00:53恢复，开发板刚重启。电脑端隐藏连接辅助：FTP PID14084，VNC PID31004，既有`takeover_local/contest_links_dns.py`固定目标，日志`b_resume_20261112_{ftp,vnc}.log`。板端helper仍F:/linux_fpga_try/ac820.ps1，调用需escalated。

新VNC窗口 **18874435**，class Vncviewer，800×450。初连落在队友workspace4，仅切换到**workspace3**，没有操作workspace4的终端。workspace3仍旧e11包空闲shell。FileZilla当前已正常断开退出，传输队列空。没有CUA会话。

## 原B/v2综合已自然完成，不重跑

原e11包`systolic_b_v2_synth01/systolic_b_synth` **22:14:48.271183**完成；11月12日00:56/00:58实际读取state为passed，summary为reports_ready_review_required。PID99451/108110不再运行，锁不存在，EDA进程列表空。

- 92小宏+128大宏=220，零锁存器，最终组合环检查无环。
- 整机面积4608011.089621µm²；计入预算保守上界 **1.0857945895010312mm²**。
- DC周期6.666666ns、setup/hold初步非负；具体数值与摘要SHA在`takeover_local/b_synth_values.png`，需后续独立精确核对。
- 仍timing_verified=false、scoring_area_verified=false，没有门级/功耗。该网表只属旧B/v2，不能证明新版63da6ba。
- **00:58 free14.411GiB**，无额外存储，不开普通大VCD，不删旧文件。后续批量/SAIF先做空间预算。

## 新v3包已上传，下一步服务器解包

源码提交仍 **63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86**，已云同步，RTL/生产固件本轮未改。

包`light-light126-systolic-b-v3-20261111_211137-63da6ba0d6d9.zip`，11197550B/663输入，SHA **3433af44f5f80ec6c3b2d78a2a90accbf16d67dcd1312af981ef4045f391d0f2**。重启后板端`/home/root/systolic_b_v3_63da6ba/`SHA再次核对。

01:03通过Linux FileZilla上传至既有`/IC/light-light126-undergrad-d2-20261109/`成功，显示11.2MB/22秒、成功1、空队列，截图`b_fz_complete.png`。已Ctrl+D/Ctrl+Q断开退出，勿重复上传。

**当前已向VNC输入`takeover_local/b_v3_unpack.txt`，等待该type调用结束后才按Return。** 它验证既有unpack.py哈希、新ZIP SHA并安全展开到bundles新目录。接着执行`b_v3_preflight.txt`核663输入、IRQ固件、锁/进程，再使用准备好的`b_v3_asic14_launch.txt`。这三条截至本检查点均未执行，不能称新v3 ASIC启动。预期新session=`systolic_b_v3_first01`。

服务器父目录`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`，新目录同ZIP去后缀。旧e11完整目录见暂停检查点。

## 本轮本地新验证工具（未提交，未服务器运行）

新增`systolic_b_batch.py`：基于固定100样本清单，一次编译1200真实ASIC/E203冷任务，绑定B contract/layout/五行/IRQ，独立逐例输出及回执；旧37或R4 PASS不可导入。尚未实际1200。

新增`build_systolic_b_contention.py`、`systolic_b_contention.py`、`main_systolic_b_contention.c`：同原共享仲裁器scratch读写、明确v2/v3布局和B ID，独立polling非性能固件。固件编译与verify通过：`local_runs/systolic_b_contention_firmware_20261112_0054`。尚未真实CPU执行。

新增B sequence构建/服务器runner/本地runner/C main/monitor/fixture。固定明确v3布局，80PE双结果逐项坐标、数值、饱和核对；按原坐标独立映射v3加载顺序。早启动允许超时前部分正确输出，仍核成功写ACK和排空。保留5个真实CPU guarded-store异常的服务器验收要求，NO_CPU夹具不能冒充。

本地`local_runs/systolic_b_sequence_fixture_20261112_005323_689646`通过：3项故意坏观察回执拒绝，10阶段（5坏配置、cancel、timeout、A/B/A），3完整任务 **76032输出**。session46954已结束。实际C固件`local_runs/systolic_b_sequence_firmware_20261112_0100`编译、ELF故障指令/段、无任务预填核验通过。新版Python parser独立核10阶段回执通过，NO_CPU整段被实际CPU入口拒绝。所有B Python按3.6语法通过。证据`handoff/team/evidence/SYSTOLIC_B_DIAGNOSTICS_LOCAL_20261112.json`。

现有`systolic_b_soc.py`增加contention诊断插桩、独立脚本身份；`server_run.py`增加B batch/contention/sequence及firmware选择，沿用原共享锁；`install_systolic_b.py`纠正文档manifest为v2_v3/cap000405ff（旧值0003053f过时），**不改变RTL接线**。旧63da6ba上传包保持不变，后续新工具需独立提交包，不原地修改旧包。没有活动本地仿真会话。

尝试中一次生成脚本因匹配不到不需要的import而停止，本地runner未写；随后只补缺的runner并实际运行通过，硬件未改。没有新的RTL数值失败。

## 未完成

新v3实际ASIC14/真实CPU恢复竞争、新综合/严格审阅、自己的1200、同网表gate14、SAIF及12层功耗、报告/干净复现均未完成。v3 READ_LATENCY2重叠单测也仍缺（v2已有）。SAIF只读定位结果仍沿20:55检查点，未采集；优先小夹具/R4 L01同窗口≤1%核对后用，空间14GiB必须控制。

下一步先执行新包服务器核验/ASIC14，不重复上传；同时保存提交新增验证工具并准备独立后续工具包。保持R4交付资格，全部性能/面积/功耗必须同冻结配置。


## 01:06 increment

New v3 UNPACK_HASH_PASS observed on server; no repeat unpack/upload. b_v3_preflight.txt is being typed; wait exec session30736 completion before Return. Original B synth values read and no EDA/lock at00:58. All 11 codec/synth unit tests and B Python3.6 syntax pass. No new ASIC job yet.


## 01:08 increment

New v3 unpack and663 inputs/IRQ firmware passed. First preflight process-list comprehension raised IndexError because ps emitted rows with only PIDs; file/firmware checks already succeeded. Independent pgrep -l -u s4_21usr dc_shell|pt_shell|simv|vcs returned1 with empty stderr/stdout at01:07:59; lock absent. b_v3_asic14_launch.txt has now been typed AND Return executed; inspect b_v3_started.png next for PID. Do not launch it again. FileZilla closed. No local long-running sessions.


## 01:10 increment

B/v3 ASIC14 launched once: session systolic_b_v3_first01, driverPID67766, source63da6ba. Last read-only live query executed; screenshot b_v3_live_0110.png needs viewing. No local jobs running. package_systolic_b.py now has optional --diagnostics to compile/export distinct contention and v3 sequence firmware; not yet packaged/tested in clean export. All new tools still uncommitted.


## 01:14 increment

New63da6ba B/v3 actual ASIC14 PASSED at2026-11-12T01:11:55.771680:354816 outputs, IRQ/WFI all,12-layer mean30502.333333 cycles /4917.656573task/s, host case total48.04762985697016sec. Final summary/state hash independently matched by server query; screenshot b_v3_asic14_final.png. Original67766 completed, no repeat. b_v3_synth_launch.txt (new session systolic_b_v3_synth01, lock+pgrep guards) was typed AND Return executed; inspect b_v3_synth_started.png for PID, do not relaunch.

New tools committed/pushed c4d8cf0f338fa3ba7f2aa5e3d4e1a3eeb2bfaf7f, ls-remote matched. Diagnostic package generated/verified: light-light126-systolic-b-v3-20261112_011055-c4d8cf0f338f.zip,11357606B,698 inputs,SHA8693e18fdc255676ec049728845d3068b5baf282cb9b12e24f5df229f6ab17e1. Three exported firmwares verified;35 runtime RTL/numeric/production firmware files match63da6ba exactly. Evidence SYSTOLIC_B_DIAGNOSTIC_PACKAGE_20261112.json. New package still LOCAL ONLY, not board/FTP. session27919 completed. No local active simulations.


New v3 synth launch observed PID75738, session systolic_b_v3_synth01. Last query b_saif_report_help.txt typed but not Return yet. It reads installed VCS Tcl report-help only. Keep original synth running.


## 01:17 recovery detail

SAIF report-help read produced clipped output; compact b_saif_syntax.txt now typed and Return executed. Next view b_saif_syntax.png. It extracts report/region/examples from vendor saif.tcl; no extra EDA run. VNC workspace3 current cwd is63da6ba package. FileZilla closed. Sole new synthesis75738 must continue. No pending tool sessions. Diagnostic c4d package still local only. Remaining priority: upload new tools while synth runs, verify storage budget for1200, adapt B gate observer to paired output and selected v3 decoder, native SAIF tiny test after lock releases.


## 01:21 increment: gate observer preparation

New local systolic_b_gate_monitor.py reuses original port/MMIO drain proof generator with B paired-result/v3 observer and explicit decoder_v3 binding. local_verify_systolic_b_monitor.py --layout3 --gate-monitor now enabled; ordinary activity remains blocked. Run local_runs/systolic_b_monitor_fixture_20261112_011740_058277 PASSED6 tasks152064 outputs (L01/extremes/rounding x pf0/1), no CPU/mapped netlist. Local exec session ID was not printed by wrapper, but terminal summary file exists and all six logs complete; no running simulator remains.

New systolic_b_gate.py copied/adapted from pinned old gate runner: B module refs,5-row/layout_v3/32-bit result/2-bit saturation port audit; v3 decoder direct ports crosschecked against frozen status_interface inventory (old decoder_interface points to inactive v2 decoder). No alias guesses. Same synthesis hashes/corner/area checks; functional only, SAIF activity blocked. Two tests against actual RTL ports and deliberately missing/wrong bindings pass. server_run adds systolic_b_gate, same synthesis digest/lock restrictions. These gate files are UNCOMMITTED and NOT PACKAGED.

Vendor VCS help actually read: saif -region <name> -depth <depth> <scopes> [-exclude <scopes>]; saif -start r1; saif -stop r1; saif -reset r1; saif -report <filename> -region <region> -tres <timeunit>. Example uses dut.bsaif /1ns, depth0 tb.dut. No native capture executed yet. Need establish whether output is readable SAIF, exact window/time resolution/T0/T1/TX/TZ and PT read_saif via tiny fixture under shared lock.

Last VNC command b_v3_synth_live.txt executed; view b_v3_synth_0121.png next. Terminal font reduced two steps only in workspace3,800x450 window unchanged. FileZilla closed. New c4d diagnostic package remains local only; may supersede with combined gate/SAIF tools after local preparation, preserve both. Original production B RTL unchanged.

## 01:37增量：验证工具继续，不改生产RTL

重新读计划/AGENTS/检查点/STATUS。01:31:34实际读取新v3综合仍running，driver75738、child79637、同session/锁，正在处理核心映射。不重跑。VNC18874435仍workspace3；FileZilla关闭。

门级工具修正从R4复制后残留的96小宏检查为B实际92，端口/错误绑定2项测试通过。新增systolic_b_timing_audit.py，仍为只读DDC诊断，不能自动批准时序。新增native_saif_probe.py及server_run阶段：计划用VCS原生UCLI采12..72ns小窗口，核T0/T1/TX/TZ、已知4次翻转和PT read_saif；解析器正常/8种破坏检查通过，**实际EDA尚未运行，R4 L01同窗口交叉核对仍缺**。已实际读取安装VCS saif.tcl和PT read_saif手册，不依赖猜测接口。

systolic_b_batch加入空间前置和逐例复核：初始按每例8MiB、余量20%加2GiB保留量；首例后按实测最大文件体积估剩余。没有删除任何文件。后续预算需读取b_storage_0137.png查询结果；该查询已Return执行。

新增v3 READ_LATENCY2本地核心检查：旧夹具按v2全X顺序等待MAC取消点，在早启动模式两个结果槽已满后等待卡住。run012715日志保留，主动停止仅该xsimk PID49924；首次Stop-Process报错，后核身份用taskkill成功，不影响远端。第二run013224发现夹具要求接收坏偏置后立即error，忽略了v3八元素暂存的消费延迟；夹具改为最多16拍等待，仍要求错误、busy/ready/输出全状态正确。还区分v3 X加载重叠和权重预取。以上均只改TB/本地runner，生产RTL未改。

第三run0133*本地session74989正在运行：layer01和extremes、pf0/1均通过三任务A/B/A，继续rounding；目标18任务456192输出。v3流独立按原矩阵坐标检查。后续先收回此run结论再提交/打包。首个c4d诊断包仍仅本地，可由包含本轮工具的新包替代上传，旧包保留。

未完成仍为：实际CPU恢复/竞争、新v3综合终态/严格审阅、B自己的1200、真实gate14、SAIF原生及R4交叉核对、B活动12/整机功耗、冻结报告与干净复现。当前性能只有已过ASIC14的4917.6566task/s折算值，不称7000、不称B功耗已验。

## 01:40增量：本地18任务完成，准备同步新工具包

本地session74989已正常结束，run `local_runs/arch03_systolic_b_20261112_013329_596203_pin_mock`通过18任务456192输出，summary SHA `0c02c8776c3df7dd276665cc0780a7fb4c617453ea141776f9b6f6f6ab5f6cf6`。独立记录`SYSTOLIC_B_V3_LATENCY2_20261112.json`，含前两次夹具失败/主动停止路径。没有本地仿真在跑。

01:36:40服务器实际ASIC14 summary SHA核对为`614d9f605996c9dfb302add53254461c62d7ec3c295fdc003c7964b6233a5d5d`，state一致。可用空间**27.75GiB**；L01/L12/extremes单例证据2677563/2729525/2570182B。空间回升原因未知，本轮没有删除任何文件。新综合仍running75738。

新增`systolic_b_validation_queue.py`只等待指定pid/started的当前B综合，通过后按同一共享锁串行运行新B真实CPU恢复、竞争、小SAIF、只读时序诊断、gate14。失败不覆盖旧run；SAIF小试失败保留独立失败记录但不阻塞功能gate；不会自动启动最终1200或批准PPA。该队列目前仅源码准备，**没有上传或启动**。

下一步提交本轮验证工具、同步云端、导出新不可变含三固件包，通过已授权FileZilla上传；核验后记录综合精确started，再唯一启动新B验证队列。保留c4d本地包，勿将它误记已上传。正式RTL仍63da6ba冻结候选。
