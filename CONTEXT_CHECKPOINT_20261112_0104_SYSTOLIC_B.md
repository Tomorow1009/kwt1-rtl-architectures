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
