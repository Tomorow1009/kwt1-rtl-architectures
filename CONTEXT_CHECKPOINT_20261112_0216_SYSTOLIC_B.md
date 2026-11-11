# 2026-11-12 02:16：B/v3验证继续

## 当前任务与约束

用户已继续并确认板端接网。直接5×16脉动B，A取消、R4保底；有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`。H0=11/11 19:30:41，功能收敛11/12 08:00，冻结09:30:41，交付11/13 17:00。压缩后读AGENTS、根交接、本文件、01:04检查点全部增量、有效计划及STATUS。保留失败和历史证据，不删文件、不续旧8/R1、不重跑R4的1200。

生产硬件受测63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86；最新工具35d8ae1b20a1a8ba417e9971c631d50e00173a4e已云同步。本轮未改生产RTL。

## 已完成与实测

- B/v3实际ASIC/E20314例354816输出、IRQ/WFI全通过，finished01:11:55.771680，summary SHA614d9f605996c9dfb302add53254461c62d7ec3c295fdc003c7964b6233a5d5d。原67766已结束。
- 02:00独立读逐例：12层平均30502.333333周期、31338.666667编码字节、28341.333333事务；150MHz折算4917.656573task/s，较R4提升13.4864%。该流量即使一拍一事务也最多5292.623259task/s，不能宣称7000。详见`handoff/team/evidence/SYSTOLIC_B_ASIC14_METRICS_20261112.json`。
- READ_LATENCY2/v3本地18任务456192输出通过，run013329_596203_pin_mock，summary SHA0c02c8776c3df7dd276665cc0780a7fb4c617453ea141776f9b6f6f6ab5f6cf6。前两夹具失败已保留：v2取消等待不适合早启动；坏bias检查未等暂存消费。只修TB，无新RTL数值失败。
- 本地gate观察夹具6任务152064输出通过，无CPU/映射网表。gate92小宏计数已修正。全部本地仿真结束。
- 35d包11377937B/705输入/三固件，本地及服务器核验通过，FileZilla成功后关闭。ZIP SHAeff31c13bd682c03db525187db54cbac964eb134e753df216c7ca3dee6f650d9，manifest SHAb2efb14665212853e63da2a040b3c1bff862e076cb50fb174de021d17c3c9840。c4d包只在本地，已由35d替代上传；两者均保留。

## 当前作业（每项附最后观察）

服务器bundles父目录`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`。

1. 唯一综合位于63da包`light-light126-systolic-b-v3-20261111_211137-63da6ba0d6d9/runs/systolic_b_v3_synth01/systolic_b_synth`。driver75738/child79637，started2026-11-12T01:14:15.533251。02:04:28 common_shell_ex仍99.7%CPU、elapsed44:25、RSS25922708KiB、日志67426B，算术映射中。旧v2综合约114分钟，不能因等待久就重启。
2. 唯一验证队列PID103191，01:51:02.310665启动，位于新35d包`light-light126-systolic-b-v3-20261112_014002-35d8ae1b20a1/runs/systolic_b_v3_validation01_queue`。**02:16:09.649334实际观察waiting_synthesis，completed/optional_failures空，无error；锁仍75738/79637/systolic_b_v3_synth01。** 后续串行sequence、contention两例、SAIF小试、timing诊断、gate14；SAIF失败保留但不阻塞gate，不自动1200、不自动批准PPA。不要重复任何启动。
3. 最近空间01:36:40为27.75GiB，本轮未删除；单例无波形证据约2.57–2.73MB。1200工具已有20%余量+2GiB保留和逐例检查，开始前仍核空间。

## 新本地草稿（未提交/部署，无实际SAIF结果）

- `native_saif_activity.py`流式核完整SAIF时长/层级/106个SysMem接口位/T0,T1,TX,TZ和翻转；声明数不是物理网数，未知影响待审。
- `native_saif_replay.py`只允许冻结R4 L01、需tiny实际PASS；同网表仅增debug visibility，原完整窗口采SAIF不生成VCD，独立复核25344输出、IRQ/WFI、窗口和哈希。
- `native_saif_crosscheck.py`相同R4库/网表/设置，read_saif替换read_vcd，核相同覆盖和整机/主要模块功耗差≤1%；通过仅批准活动方法，不批准系统功耗。尚未接server_run。
- 上述与tiny本地4项合成测试、Python3.6语法通过；真实格式/边界仍等服务器小试。
- `systolic_b_precision.py`准备在B自己的1200后重核30412800输出，再利用固定清单逐例SSE/参考能量汇总浮点误差；显式标注本次未重算浮点参考，只在实际逐位等价证明下复用数学误差，不继承旧硬件PASS。
- 服务器固定100数据`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507，schema kwt1-full-arch02-q12-v1。1200项有SSE/refenergy，最差层0.149414275410407%。本地105829条dot(0,0)清单不是全矩阵，已排除；内部600最差0.14941871%范围不同，均非官方。
- 阶段报告`workspaces/arch03/SYSTOLIC_B_PROGRESS_20261112.md`及两个新JSON证据待提交。

## 未完成和后续

新v3综合终态/严格时序与面积、真实CPU恢复竞争、自己的1200、同网表gate14、实际tinySAIF/R4 L01≤1%核对、B活动12/整机功耗、冻结报告及干净复现均未完成。旧v2的1.085795mm²和R4功耗不能代替B证据。

先收原综合/队列，继续准备SAIF接口；tiny成功才做R4交叉核对。符合硬约束后冻结B并跑自己的1200。禁止改计时或增加架构追7000。

## 现场恢复

板端helper F:/linux_fpga_try/ac820.ps1；隐藏FTP/VNC relay14084/31004。02:15已新列窗口/截图：VNC18874435/class Vncviewer，workspace3，新35d包shell；FileZilla关闭，workspace4不操作。无CUA会话，无本地仿真。

上次只读`b_validation_live.txt`已输入但未Return；02:16本轮已确认屏幕、Return并读取`takeover_local/b_queue_0216.png`，无待输入命令。所有launch文件早已执行，不能再执行。

## 02:25增量：SAIF工具接入、原始误差统计核对

02:19:35实际综合健康查询：原75738/79637，CPU99.4%、elapsed59:31、RSS25923916KiB、日志215322B，继续算术映射。没有新EDA。02:25固定100清单只读计算通过全部1200项SSE/能量与原12层汇总一致，shift集合[12]，max0.1494142754104067%，float manifest SHA504155c6b44afea2cd199e48b83f1eb51b7d87a7678c13e667f602cef56f5c3f。该读数不证明B自己的1200已跑。

本地新增`systolic_b_saif.py`和`systolic_b_power.py`，server_run已接R4 replay/crosscheck、B saif/power四阶段与显式来源哈希。B活动入口要求实际R4≤1%核对通过及B自己的gate14；按原完整窗口重放，每层核真实输出/IRQ/周期，存储按R4首例2倍估计并逐例重估，另20%+2GiB保留。功耗使用B220宏守卫，系统包括CPU/互连/SRAM；未知影响仍false。ICB32数值解析器新增明确systolic_b=92宏profile，旧默认96不变，不能互相接受。

9项本地SAIF/新旧功耗入口测试通过；8个脚本Python3.6语法、4种缺少来源参数在读取配置/拿锁前拒绝均通过。一次新测试期望字符串拼写不符实际Tcl守卫，改为实际路径后通过；另两次本地替换脚本因PowerShell转义/相对cwd错误失败，未产生修改，之后已正确更新。没有实际SAIF/功耗PASS。这些新工具尚未打包部署，原35d队列保持不可变。

下一步先提交/云同步工具及证据；等原综合和tiny真实结论，必要时修兼容性再导出新不可变工具包。当前VNC最后命令是已完成的`b_reference_sse.txt`，shell就绪；FileZilla关闭，无本地长期任务。

## 02:33增量：云同步、调度统计通过，原综合进入高强度优化

37fc276a8699001f87ebd9f1a2e4df18d6721f9b已push并ls-remote一致；它包含SAIF/精度/报告工具及此前证据，生产硬件不变。随后新增被动调度计数和结构警告解析，尚待本轮提交/新包。

本地`local_runs/systolic_b_monitor_fixture_20261112_023105_608860`两例50688输出通过，session89826已结束，L01/extremes保持31339/38337周期。L01：320块/20480次feed/25344结果，supply_empty9793，X等6420/W等5083（重叠，不相加），slot/credit等0，304个tile内间隔平均81.7961、最小64/最大352；15次换tile平均356.2；首feed距首源1011周期，最后feed至结果被观察19周期，最终写ACK再37周期。详见SYSTOLIC_B_SCHEDULE_LOCAL_20261112.json。19拍包含结果观察寄存器，不能直接称末四行阵列内部传播跨度。

第一次023014 run硬件L01已过，但本地wrapper仅传cycle/count而新解析器需要完整window，KeyError start_ns，保留失败目录；改为读取原完整计时回执后两例通过。8种故意破坏实际调度计数均被拒绝。只改TB/parser/local wrapper，生产RTL未改。后续clean ASIC14需采新统计，旧14仍有效但没有这些新字段。旧基础metrics解析保持兼容。

新增`systolic_b_structure.py`复用已验证mapped端口解析器，绑定B自己的综合摘要；逐个解析LINT-2驱动层级并比对声明未使用的输入。合成层级正常/错配小检查通过，实际B网表尚未就绪，不宣称结构警告已审完。

02:32:53.010370最新实际服务器观察：原锁systolic_b_v3_synth01，child79637 CPU99.5%、elapsed1:12:48、RSS25925576KiB、日志215971B，Beginning Mapping Optimizations (High effort)。不要重启。VNC仍workspace3、新35d包shell，FileZilla关闭，无本地仿真。下一步提交本轮工具、导出新不可变包（实际tiny未出，部署不等于PASS），原35d队列不修改。

## 02:44增量：新SAIF/调度包已就绪，原队列仍等待

最新工具提交**caad8de19f7c25f2fb5043f52c0cc165ae778c6c**，push及ls-remote一致。新包`light-light126-systolic-b-v3-20261112_023413-caad8de19f7c.zip`，11408516B/716输入，SHA**c9954967656ee51489780766da05df2b5427cf5b10e0dbbd84274a81d08af62c**，manifest SHA**55c408734dc559eb84fb3a797ce196ec6c2350d288677eb49684361313234009**。本地/板端/服务器全部输入和三固件核验通过；本轮明确比较的arch03 RTL+生产firmware共26文件，与63da包相同（未计arch02等，不能混作早前30项）。

已FileZilla上传成功11.5MB界面显示/22秒（精确字节见上），空队列后Ctrl+D/Ctrl+Q退出。板端源`/home/root/systolic_b_saif_caad8de/`，GUI对应`/home/board/systolic_b_saif_caad8de/`。服务器解包UNPACK_HASH_PASS，02:42:57确认NEW_B_716_SAIF_TOOLS_FIRMWARE_PASS716及manifest相符。证据`handoff/team/evidence/SYSTOLIC_B_SAIF_PACKAGE_20261112.json`。**勿重复上传、解包，尚未启动任何新SAIF/功耗作业。**

当前VNC18874435/workspace3的cwd已经切至新caad8de包。新只读`takeover_local/b_validation_from_caad.txt`已输入并Return执行；02:43:44.934642观察原35d队列103191仍waiting_synthesis，completed/optional_failures空，无error，锁75738/79637/systolic_b_v3_synth01。原队列仍在35d包，不在新caad包；今后查它用from_caad文件，原b_validation_live相对目录已不适用。`b_synth_health_new.txt`根据锁绝对路径，可在新包使用。

本次FileZilla首次用ctrl+s字符串被板端拒绝，未发送按键；实际helper需`--keys Control_L s`（组合按住），后正常。密码只用既有text-file输入，没有读取/输出凭据。新FZ曾复用窗口ID20972102，但现已关闭，不能继续用该ID。所有type会话已结束、无未完成输入或Return、无本地仿真/打包任务。

后续：继续原综合与35d队列。实际tiny通过后，从caad包按server_run native_saif_r4_replay → native_saif_r4_crosscheck → systolic_b_saif → systolic_b_power使用新独立session/明确来源摘要；全部同原共享锁，不能与原队列争抢或重启。当前tiny/R4核对/B活动功耗均未通过。还需新B结构警告/时序审阅、最终1200、clean ASIC14收集新增调度统计、最终报告/干净复现。没有改变冻结时间或生产硬件。

## 02:55增量：恢复核对与B报告导出工具

重读AGENTS、有效B计划、本检查点、根交接及STATUS，重新列举板端窗口并观察第三工作区，连接正常、空闲shell、FileZilla关闭。02:50:45.443738原综合锁仍systolic_b_v3_synth01、child79637，99.5%CPU、elapsed1:30:40、RSS25928096KiB、日志239855B，正在映射/时序优化。02:53:24.804011原103191队列仍waiting_synthesis，completed/optional_failures空，error为null。没有重启或新增EDA。

新增`scripts/systolic_b_report.py`准备同配置JSON、逐层与汇总CSV、中文Markdown和哈希回执。重新验证ASIC/gate14输出、真实IRQ/WFI、boot无预加载、完整窗口、源码/平台/固件/库/网表身份；可接自己的1200和合格SAIF/12层功耗，缺项为空。最终1200另逐例核对实际日志/boot/IRQ和原始矩阵误差，未知活动影响、官方600、物理签核不自动批准。功耗区分时间加权平均与层算术平均，避免把不等时长直接平均。

新增2项针对不等时长功耗、缺层不计零和工件改写拒绝的本地检查通过，Python3.6语法通过。该导出工具尚未服务器部署、未生成B最终报告；当前仍缺新综合终态、CPU恢复竞争、gate14、自己的1200和实际SAIF/PPA。生产RTL/固件未改，原716输入caad包及35d队列保持不可变。一次查找误用了不存在的tests目录，仅只读报路径不存在，实际测试位于scripts并已执行。
