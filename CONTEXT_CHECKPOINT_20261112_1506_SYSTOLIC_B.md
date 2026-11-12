# B 检查点：2026-11-12 15:06

## 16:12增量：原门级继续，功耗工具精确周期修复

16:11:48 gate02/PID79264前两层PASS、L03进行中，无错误。编译和SRAM来源链检查已通过；当前子进程88593。不重启该批次。R4 PT请求已部署，但尚未启动。

新网表mapped.sdc实际只保留四个LF timer第一同步级D例外（tim0..3/r_ls_clk_sync_reg[0]/D），没有多周期、clock_groups或disable_timing命令；DC实际周期6.666666ns，而write_sdc序列化为6.66667ns。B功耗工具新增独立mapped.precise.sdc，复用严格restore_clock仅恢复HF周期/下降沿，保留原文件；PT实际读入周期另存power_clock.txt并断言HF6.666666/LF66ns。报告明确区分新B精确SDC与历史R4原舍入SDC，不冒充旧R4已经重测。5项功耗/报告工具检查通过；硬件/网表/原约束未改变。这些修复尚未部署，需新ops目录。

本地timing_audit相对路径修复已语法检查；timing02实际用绝对路径完成，不需要为这一行修复重跑。STATUS已校正当前新网表门级/1200/功耗均未完成，旧synth02门级PASS仅作历史。下一步同步工具并部署新独立副本，等待原gate02，再R4 PT交叉核对。

## 16:03增量：DRC06时序诊断完成，新门级已启动

16:05核实：**gate02 PID79264，启动16:02:46**，16:04仍running/mapped_probe子进程79454，尚无仿真PASS。新结构清单SHA **12f843804ca02d61ae5f260e30c556c1fe0cf89c2d98586ae6acbdb219ec73fd**，2222模块；LINT-1=4、2=244、8=244、28=12796、32=12048、33=1186；全部13040端口提示仅声明，244无负载网与相应未用端口一一匹配，无extra/missing。4个LINT1为原平台ndreset/fullreset/porrst/PLIC irq0实例，不是新B漏接。

R4交叉核对请求已部署并验证SHA bcc2cc0f...，**launch仍未执行**，须等gate02结束和真实锁释放。不要重复安装请求。

timing01 PID47376于15:47:38.474456失败：工具把相对mapped.ddc路径放入新运行目录解释；不是网表问题。失败目录保留，本地timing_audit入口补Path.resolve，尚未提交/部署。

timing02 PID62215使用绝对综合路径，于15:54:23.668453 passed；summary SHA **bfd0007c4846649c7f3ea018a5dbad480e10f8c406f309c3089b016d0c7da3b6**。三个高扇出网络为u_e203_subsys_top/core_csr_clk、u_e203_subsys_top/hfclk、u_e203_subsys_top/u_sirv_aon_top/crossing_clock，均为平台时钟网络；不声明物理签核。

16:00执行静态结构清单b_drc06_structure_run，输出runs/systolic_b_drc06_structure01.json，待读结果。16:01:25实际LOCK False、EDA []。随后b_d48_gate02_launch已执行，**不得重复启动**，PID从b_gate02_launch.png读取。使用d48新gate工具和DRC06 b817...网表；旧gate01的配置来源错误已修复，但不能继承旧网表PASS。

R4 replay01已正式通过，仍待PT交叉核对；请求和launch只在本地准备，尚未部署/启动。final1200尚未批准。当前VNC工作区3/ced shell，FZ关闭。不要操作workspace4，不再清理历史文件。

## 15:48增量

15:45实际R4回执outputs25344/window34639，SAIF SHA **378a012cba19532df1a3cf57892f2959df6dee5c38501b1ecefda722a6d01cfb**；scope tb_top.u_e203_soc_top、106源端口bits，全部输出/时窗审计通过；真实锁False/EDA[]。

随后**DRC06 timing01 PID47376于15:47:24唯一启动**，ced runs/systolic_b_v3_drc06_timing01/systolic_b_timing_audit。只读，不修改网表。当前正在收终态及high_fanout.tsv，截图b_drc06_timing_result.png待读；gate02依旧未启动。

R4 PT crosscheck请求已本地生成，但**未部署/未启动**：b_r4_crosscheck_request_install.txt，目标operations/r4_saif_crosscheck01_request.json，SHA **bcc2cc0fe8b62f0e960cf651405fd8d6b1551040f12fd184e436db8462928346**；launch b_c307_crosscheck_launch.txt使用c307十工具，引用replayf7d542...与原power18190...。完成当前只读EDA、启动gate02后可准备请求文件，但绝不并行启动PT。

本地未提交为检查点/根交接/STATUS更新；所有源码已c307云同步。当前VNC workspace3/ced shell，FZ关闭，最后只读timing结果查询已执行，先收尾工具session再操作。

## 15:44增量：R4完整重放正式通过

replay01 PID314119已于 **15:41:08.962232 passed**，summary SHA **f7d542dd8e741c008c37c8f50385de451742a4e9125da685228056698e23d21a**。25344真实输出与原csv/窗口全部相同，SAIF94632798B。阶段只证明重放功能/窗口/活动审计，**尚未做PT≤1%功耗交叉核对，不是SAIF方法最终资格或B功耗通过**。原sim317388在15:39:50结束，CPU1489.810s。临时行计数误减1已说明，不影响正式check_capture。

下一步核真实锁后启动已准备DRC06 timing01（只读DC），接着新gate02；两者都尚未启动。然后R4交叉核对请求需要绑定本replay SHA和原R4 L01 power18190f6d4021de0ba55ae2b2be00a456f89217a6efbd0c0e3412831617f2d00c，使用610/d48/c307 ops的native_saif_r4_crosscheck，不能用ced旧SAIF模块。

最后回执/资源query b_r4_replay_receipt_resources已执行，图片同名.png需读；本地exec可能需收尾，之后无待Return。c307工具及云端已确认，最终队列仍未批准。当前只读静态报告显示DRC06无组合环，check_timing仅TIM134三个高扇出网络提示，实际归属待timing01读取。

## 15:42增量：完整R4 SAIF仿真已结束，审计回执待收

15:40:57实看R4 sim317388已结束，CPU1490秒约24.8分钟；日志15:39:50完成，完整34639周期、IRQ/WFI完成，window all_writes_responded=true/pending0。生成layer_01.saif **94632798B**。此时driver314119仍在Python后处理，尚未读取最终PASS/摘要；不得推断资格已过。临时进度脚本sum(lines)-1显示25343，文件可能无header，不能据此报缺一个输出；正式data.check_capture和哈希才裁决。

后续12层按每层约25分钟量级估算仿真，不用芯片速度比例；SAIF单层约90.25MiB，存储明显足够，实际B仍需首例重新预算。当前无B功耗数值。

最终流程工具c307c3d6dbdeaca94b2050fb1c41451d4a5926fa已push，第一次ls-remote TLS握手失败后重试成功确认。10文件ops已8条差分完成部署，目录operations/systolic_b_tools_c307c3d，manifest **d855f9f4b4b5108625fa00327c41f4fd300acee2d91545e113eb822245729691**。禁止重复append。新finalize可用已完成saif_qualification避免重放，活动通过ops/request，不能用ced旧finalize跑SAIF。直接从ops调用finalize时需要base scripts在PYTHONPATH（其导入ROOT来自base server_run）；正式请求与冻结review仍未准备/批准。

d48 gate02已准备未启动；新DRC06 timing01只读DC命令b_drc06_timing_launch.txt、structure01静态命令b_drc06_structure_run.txt也仅准备未执行。下一步收原R4终态/真实锁，随后先新时序诊断和gate02，再安排R4 PT交叉核对（或按资源串行顺序），绝不并发。

最后b_r4_replay_live查询已Return执行，截图b_r4_replay_finalcheck.png待读；可能有本地exec session需先收尾。VNC工作区3/ced shell，FZ关闭，无其他新作业。

## 15:32增量：R4重放继续，本地最终队列适配

15:24:40原R4重放314119/child317388继续，csv114688B；15:27:16已有11933/25344行，仍在完整230926.643574ns窗口的VCS run中，无SAIF文件或回执。debug+完整统计明显慢于普通功能仿真，按实测估预算，不以芯片加速比推算。一次ps参数显示不完整，不能据此推CPU数值；实际输出文件增长证明前进。

d48新9文件ops已部署验证，gate02命令已备但**未启动**。当前唯一EDA仍原R4 replay，不能并发。

本地systolic_b_finalize_queue已适配：活动步骤使用hash-bound ops/request而非ced旧SAIF模块；可提供已完成saif_qualification，避免重复R4重放；验证失败不掩盖已经完成的own1200，功耗保留未验。4项替身子进程流程检查通过（不是硬件PASS）。新finalize队列及测试尚未提交/部署，未来需要新工具副本，不能用旧base finalize启动带SAIF的正式队列。正式gate/冻结review仍未满足，最终队列不批准。

当前VNC工作区3/ced shell，FZ关闭；正在读取DRC06 check_timing/loop静态报告，不启动EDA。需收尾本地exec和读截图后继续。未修改RTL、网表、约束或当前运行目录输入。

## 15:24增量

云端d48c638a3bfba1292e6712506e2ff4e5b185b688已push及ls-remote核对。9文件新ops已7条差分命令全部部署，operations/systolic_b_tools_d48c638，manifest **2a681669db15eb66e609f64fba898ce53ee9743386551801d4d314f9b3417848**；不得重复append。新增gate模块从server_run导入原ROOT/A3，因此数据/固件仍绑定ced；source_inputs同时记录实际overlay模块hash与SRAM来源核对回执。8项gate/来源/ops测试通过。

**新gate02尚未启动**，准备命令takeover_local/b_d48_gate02_launch.txt，绑定DRC06 SHA b817...。等待当前R4 replay01 PID314119；15:18:25观察已编译完、child317388正在实际仿真，输出csv32768B，未有SAIF回执。不并发EDA。原gate01 failed前仿真记录保留，不重启。

当前只读b_r4_replay_live第二次查询已执行，截图b_r4_replay_live2.png待读；若exec返回session需先write_stdin收尾。VNC工作区3/ced shell，FZ关闭，后续不误发任何launch。

## 15:15增量：门级入口失败，R4 SAIF重放已启动

**DRC06 gate01 PID294410已于15:08:18.564130失败，仿真尚未开始。** 错误Missing/ambiguous traced synthesis SRAM configuration：修复链source_inputs保留原synth02、drc04/05/06四份同源arch02_sram_config.vh，旧检查器只允许一份。实际四文件存在、哈希逐项一致并与回执匹配，非数据或存储时序改变。失败目录保留，不能重跑01。

本地修复verify_gate_memory_config：允许多份但要求所有记录digest同一值、每一实际文件匹配、当前综合自己的include必须在追踪清单中、当前gate include也同SHA；保存memory_configuration_receipt，实际overlay gate模块hash写入source_inputs。ops新增gate14入口。6项针对同源副本、历史篡改、不同有效配置、缺当前配置及请求保护检查通过。尚未提交部署，新gate02不得使用旧610工具；新副本将含9文件（新增gate模块）。不修改DRC06网表或原约束。

15:11实际核真实锁已释放。**R4完整SAIF replay01 PID314119于15:13:24唯一启动**，ced runs/systolic_b_r4_saif_replay01/native_saif_r4_replay，610 ops及请求bded7b37...。当前唯一EDA，未读取实时回执；不重复launch，不与新gate02并发。下一步查原重放进展，同时本地提交部署gate工具修正，等锁释放后再新gate02。

云端390331c已push（记录DRC06清零和门级启动）；之后本次失败/新重放与工具修正仍本地未提交。当前VNC工作区3/ced shell，FZ关闭，无待Return/本地exec session；最后重放launch已完成。原“gate14正在运行”段落已由此增量取代。

任务 ACTIVE，不暂停。继续直接5×16脉动B计划，生产RTL/固件63da6ba/v3/credits3冻结；R4保底。不开发A或新编码。用户要求自主继续，压缩后重读AGENTS、有效B计划、本检查点、STATUS。11/13 17:00收尾。此前两次用户授权清理279.506GiB已完成，不重复；R4/B和小证据保护。

## 关键新结果：DRC06约束清零

ced包`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`下 `runs/systolic_b_v3_drc06/systolic_b_synth`。

- driver279581，14:55:42.201039→15:02:00.609042；报告已完成，不重启。
- summary SHA **b81780033ef65998c43a874b559e54da0d958524a040eff374b1e8f1a4824ced**。
- 实际完整report_constraint写明 **This design has no violated constraints**。
- 周期6.666666ns，LF66ns；setup **+0.00010252ns**，hold **+0.00249085ns**；两组路径、0锁存器、92小宏+128大宏。
- 整机面积4621311.195906µm²，项目计入面积保守上界 **1.099094695900963mm²**。布局前/任务模式，仍需同网表结构/时序审核与新gate，不称物理签核。
- 源RTL、固件、原task_mode约束未改。累计仅等价升驱动7个标准单元：3×BUFV2RD→BUFV4RD、AOI22V2→V4、3×NOR3CV2→V4。替换前核pin方向/函数，防增量优化降回。原库路径仍8d synth02/libs，避免DDC记忆身份冲突。
- 证据 `handoff/team/evidence/SYSTOLIC_B_DRC06_20261112.json` 已本地保存，尚未提交。

## 正在运行：新的14例门级

**PID294410，session systolic_b_v3_drc06_gate01，15:05:54唯一启动。** 路径ced `runs/systolic_b_v3_drc06_gate01/systolic_b_gate`，显式绑定上述新综合SHA，默认14例，无大波形、无SDF。使用ced原server_run入口，不是ops编译入口。尚未读取第一阶段实时state，不能推断已通过。

下一步先执行只读 `takeover_local/b_drc06_gate_live.txt` 查看state/回执；禁止再发b_drc06_gate_launch。原synth02 gate14通过不属于新网表，不能借用。

启动前15:04:58.338438实际检查无EDA、无锁，free376.26953125GiB。锁必须用server_config.server_root/.arch02_team_lock；以前临时脚本的../../.arch02_team_lock位置错误，仅这些临时False输出无效，ops实际锁一直正确。

## SAIF已完成与待办

正式tiny probe04通过，ced `runs/systolic_b_v3_saif_probe04/systolic_b_saif_probe`，PID251446，14:24:57.106218结束。
summary SHA **5b89541639df84d147f76b407bfd13c906b9fdf7bcbee912650cef716687a25b**。VCS 12..72ns完整60ns/1fs，PT从文件注释得到概率.333333、翻转率.0666667/ns，核对4次翻转。X/Z合并TX，分离测量false。证据SYSTOLIC_B_SAIF_PROBE_20261112.json已提交。

R4完整SAIF请求已部署并哈希核验：`operations/r4_saif_replay01_request.json`，SHA **bded7b37bb6755ae9c45f0a5ff7987bd8a2ae580b8e9692316adba9fe6384f5f**。指向冻结R4 gate95113a...及probe04。**尚未启动重放**。`b_610_r4_replay_launch.txt`仅准备，必须等当前gate释放锁再启动，不与其并发。完成重放后才能PT与原R4 L01 VCD≤1%交叉核对，继而B活动12/功耗12。

## 工具与同步

最新已云同步并ls-remote核对 **610e25f2c2444cf6d9cea53e02892e614bb6d168**。8工具已8条差分完整部署至 `operations/systolic_b_tools_610e25f`，manifest **f6e7739acb7a1ca1d7e71689791239e01fcd97d99ba373f161c9bf683b5da54c**。禁止重传/append。0d、60、ee及之前bf/e6目录全保留。

610 ops支持带hash请求的native_saif_r4_replay/crosscheck及B saif/power，复用同锁、新session、原bundle.inputs、全部ops源hash和请求/引用摘要检查。新入口10项相关本地工具保护测试通过。base ced仍是旧SAIF解析器，**不能直接用原base server_run去做SAIF；要用610 ops覆盖的新版模块**。Gate/CPU batch原base工具可继续。

FTP421，用户确认无队友使用；FZ关闭。不增加新传输通道，采用已授权VNC新个人小工具副本。完整2b/62 ZIP仍仅板端暂存且有旧工具问题，不执行。源包ced709输入/manifest39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d保持未改。

## 已通过和仍缺

B自己的ASIC14/354816输出/IRQ-WFI、无复位CPU恢复76032输出、两例CPU竞争通过；原synth02门级14通过；平均30502.3333周期/4917.6566 task/s（150MHz折算）。最终自己的1200/30412800尚未跑。新7000不可能由当前28341事务下界保证，不改计时。

仍缺：DRC06新gate14、最终结构/时序clock/例外审核、单独冻结review、干净ASIC14、自己的1200、R4完整SAIF交叉核对、B活动12/系统功耗12、最终R4/B报告。systolic_b_finalize_queue要求精确asic/synth/gate/sequence/contention及freeze-review，当前gate未完成不批准。报告中的功耗未知影响维持未验证，不当零。

R4自身1200/30412800、gate/activity/报告保留，不重跑1200；4333.256task/s、71.8126mW、16.5724µJ，system_power_verified=false。R4各大回执/波形及dataset SHA见1350/1438和更早检查点。

失败路径全部保留：DRC03重复库身份失败；04四transition/两multiport未修完；05多端口清除，但三上游transition/cap违规；72个VIOLATED字符串包含引脚重复，非72独立net。inspect02因可选型号无quiet UID109失败，但已生成可读driver表；新工具quiet修正。SAIF早期单位/注释/ANSI/属性错误逐一有保留目录，最终04才通过。

## 当前桌面和下一操作

VNC18874435工作区3，ced包shell，FZ关闭；不要工作区4。最后门级launch已执行并截图确认PID294410。无待Return/本地exec session。当前门级在后台，不能把shell输入当其stdin。

本地未提交：本检查点/根交接、DRC06证据与STATUS、B验收清单更新。先保存同步这些小记录，同时继续只读门级观察和最终结构报告准备。每次新EDA必须核真实锁与进程，不能清锁或重复旧队列。
