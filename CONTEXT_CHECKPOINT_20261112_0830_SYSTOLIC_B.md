# 2026-11-12 08:30 起：授权清理并恢复 B 验证

## 当前目标和授权

继续有效直接5×16脉动B计划，A取消，R4冻结交付退路。用户明确授权自行删除已验证、很大概率近期不再用的大文件，并要求清理后继续。这取代旧计划“不删历史证据”的绝对限制。只清理本项目已确认旧波形；保留输出/日志/摘要/哈希/重建输入及R4、当前B。

压缩后重读本文件、AGENTS、有效计划、STATUS和03:15检查点。08:00收敛已过，不再加结构优化；生产RTL仍63da6ba，09:30:41硬冻结和11/13 17:00收尾安排保持。新的PPA未通过前不能称B合格。

## 已完成与上轮缺口

B/v3 ASIC/E20314例354816输出/IRQ-WFI通过，30502.3333周期、4917.6566task/s；自己的1200、映射gate14、SAIF/R4交叉核对、12层功耗、严格时序面积仍待。旧synth01因ENOSPC退出，无mapped.v等最终工件；旧validation01也退出，state是过期状态。不能重启旧session。

08:31:59重新观察：可用61.619140625GiB，同账号无EDA进程；空间恢复原因未确定。本轮未删除任何文件时就已出现该余量，不能归功于本轮。递归全目录查锁/波形耗时，已Ctrl+C停止自己的只读扫描，改为明确旧目录。

旧ecf3包`runs/mmio8_source_gate_full01/mmio8_gate`12个VCD共335.7351337GiB；历史summary SHA06e388e1b744494fc00f224a43caf8de2ebf7e764eb1b655541ce7288a408533。拟选择L09–L12共约112GiB清理，保留L01/L02已用功耗波形和其余旧波形。尚未执行删除；需核验终态、摘要和占用后写清单再unlink。R4的49759e gate/activity、96443c power/batch及固定hex不动。

## 工具包与现场

本地8d8f262包705输入、ZIP SHA b2d31c9906a3d7f3640581d19fac568682f61e7fa3655fb59df692ed66c7d837、manifest ac83363a9b3ea5cd88976b13f66a12a6543e68607def89b7ce40496eb359f177；生产固件manifest维持11d860ca。最新云端51631f4。新包已开发板暂存`/home/root/systolic_b_final_8d8f262/`且SHA核验。第一次上传因尚未创建暂存目录失败，随后mkdir和重新上传成功，不是包损坏。

FileZilla20972102已登录既有站点，正在上传新包；截图b_final_uploaded.png显示100%但队列仍有1项，尚待最终成功观察。VNC18874435 workspace3，cwd仍caad包。VNC核验输出被FileZilla遮挡，后续关闭FZ后重读b_cleanup_review_short命令。不在workspace4操作。

已准备但未执行：b_final_unpack.txt、b_final_preflight.txt。删除命令尚未写；新综合尚未启动。所有本地tools在E:/fpga_race-two/takeover_local。当前无本地长期验证。

## 08:49：清理完成，新的唯一综合与后继队列已经启动

- 08:42:42.206619仅删除旧ecf3门级L09/L10/L11/L12四个VCD，共120705994578B（112.41621764GiB；09:03独立重读修正先前合计转录）；路径解析/非链接/大小/summary SHA/fuser无人占用通过，执行前保存清单。输出/日志/活动扫描/摘要/网表/输入全部保留。此四层后续原始活动复查或功耗需要重生波形，不能称原VCD仍可用。证据`handoff/team/evidence/SERVER_WAVE_CLEANUP_20261112.json`。
- 远端清单`ecf3.../runs/mmio8_source_gate_full01/authorized_cleanup_20261112.json` SHA **8939b88472f6a8ae1ae5312d4eb47e3c06da6faafa078ec651c194cd3519d80c**。已确认四路径不存在。清理后截图实际可用**172.50390625GiB**；前一评论误读175.30已更正。08:46时171.9609375GiB，属共享盘动态值。
- 新8d8f262 ZIP已FileZilla成功上传，队列空/成功1项，22秒；已断开并关闭FZ。新独立包安全解包通过，705输入和三固件检查通过，manifest **ac83363a9b3ea5cd88976b13f66a12a6543e68607def89b7ce40496eb359f177**。不得重传或重复解包。
- 新包cwd`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_032054-8d8f26247b7a`。
- 新综合`runs/systolic_b_v3_synth02/systolic_b_synth`，driver **183038**，开始 **2026-11-12T08:45:21.455160**；08:46:07状态running，协作锁存在。launch已执行，不可重启。尚无新的PPA。
- 新唯一后继队列 **184658**，开始08:47:09.711761，`runs/systolic_b_v3_validation02_queue`；准确绑定183038和上述开始时间/manifest，等待综合完成后sequence/contention/tinySAIF/timing/gate14串行。没有最终1200自动启动。launch已执行，不可重复。
- 旧synth01、validation01失败现场均原样保留。R4波形/功耗/1200、固定hex均未动。
- 现场VNC18874435/workspace3、新8d包空闲shell，FZ已关闭。b_cleanup_receipt_query已Return并读取截图，没有待输入命令。本地无长期进程。下一步检查新进程/锁归属、保存同步并在等待综合期间准备交付说明；不得重复旧EDA。

## 08:58：同步与实现候选冻结

- dfb1bcdfd0d0f85b6643d434788026934b378770已push且ls-remote一致，包含清理/恢复记录。当前新源码候选记录尚待下一次提交。
- 08:52:57综合日志正在处理脉动delay/5×16/core模块；实际owner.json锁PID183038、session synth02和新8d包匹配，队列184658仍waiting_synthesis、无completed/失败；可用170.0869140625GiB。查询b_synth02_brief已完整执行，shell空闲。
- 已检查报告器、后继队列、SAIF捕获/解析及B gate字段的衔接；无代码变动，无新增硬件测试结论。报告器始终把工程审阅单列，不能把数值导出当自动验收。
- `handoff/team/evidence/SYSTOLIC_B_SOURCE_FREEZE_20261112.json`固定实现候选：8d包25个RTL源文件逐字节等于当前Git和生产63da Git blob，7个生产固件来源与manifest相符。初次用Windows工作树字节比较因CRLF与Git导出LF不同停止，确认差异仅换行；最终依据实际ZIP与Git blob逐字节比较，未放宽服务器输入哈希。没有修改任何RTL或生产固件。
- 候选记录schema是`source-candidate-freeze`，**不是**最终队列所需的`freeze-review`；eligible_for_final1200、时序/面积/系统功耗仍false。硬冻结前已固定结构，后继只待当前候选实际证据。R4仍是当前交付退路，不把未完成PPA写成通过。
- 当前仍有新综合183038与后继184658，不能再次launch；旧synth01/validation01保留过期state，不是活跃进程。没有新的最终1200/gate/SAIF结果。下一步继续观察原综合，审阅新网表并完成队列后再决定自己的1200；待结果期间整理最终材料即可，不追加结构优化。

## 09:10：只读监视器运行，复现与创新材料已备

- 46e44a37a4788206f2495c4377389f5bb8320a3a已push且远端一致，包含源码候选固定记录。未修改生产硬件，未启动额外EDA。
- 09:05:16实际owner锁为driver183038、child **192693**（common_shell_ex，状态R），累计用户CPU83605 ticks、系统810 ticks，SC_CLK_TCK=100；验证队列184658为sleep等待。实际进程仍推进，不是旧state假运行。
- 第一版`b_synth02_monitor.txt`因远端shell嵌套引号报`Unmatched '.`，未启动监视器，不影响原作业。第二版`b_synth02_monitor_v2.txt`为单行生成器，已成功运行，每30秒显示原综合/队列/空间，结束或失败自行退出。
- **当前VNC18874435/workspace3是前台只读监视器，不是空闲shell。不要直接向其中type新命令。** 只截图观察；如必须输入只读查询，先Ctrl+C结束本监视器，不能向183038/192693/184658发信号。FZ已关闭，无本地exec会话或仿真任务。
- 09:08:08.780993最新：synth183038 running，queue184658 waiting_synthesis，completed=[]、optional_failures=[]、error=None；可用**167.701171875GiB**。目前无新门级/功耗/1200结果。
- 新增`workspaces/arch03/SYSTOLIC_B_RUNBOOK.md`，绑定8d包、三固件、独立ASIC/综合/gate、最终1200/SAIF方法与回执要求；新增`SYSTOLIC_B_INNOVATION_20261112.md`，整理R4/B整体差异、实际带宽下界和答辩范围。README入口更新；本地Markdown链接/差异检查通过，尚未新打包，不需要中断当前不可变包。
- 清理合计本地转录曾把120705994578误写120709954758；09:03:52按原清单逐项重印并核算，实际**120,705,994,578B=112.41621764190495GiB**，约112.42GiB。原服务器清单/哈希和四个文件大小未变，本地JSON及上文已修正；不是追加删除。
- 下一步继续等当前综合/队列实际结束，不能为了等待重复测试或启另一份综合。预计原同配置6193秒量级，08:45开始约10:30附近才收回；这是估计，不是完成承诺。到硬冻结09:30仍保留已固定的63da实现和R4交付资格；B的PPA及最终批量必须待实际证明。

## 09:24：比赛材料核对，当前作业无新增错误

- 536d012920c85d54862d1d2c00a50644c1e243aa已同步并ls-remote一致，工作区当时干净。之后新增比赛原图核对回执、运行手册附件对应表和创新说明中的能耗比较门槛，待下一次提交。
- 重新读取本地赛题图片11–14（印刷10–13/14页）：功能/数值40、SoC/综合/复现20、创新20；效率与创新须先全部硬门槛通过。官方面积2.25mm²，团队继续2.00；官方冻结后统一12性能任务及600精度样本与内部数据不同；未标注活动/未建模宏不按零。四原图SHA保存在`SYSTOLIC_B_REQUIREMENTS_RECHECK_20261112.json`。没有再次询问用户暂缓提供的提交入口。
- 按当前B完整平均周期及R4实际能耗，低于R4的16.5724388µJ/task需要B时间加权功耗低于约81.4976mW；只是比较门槛，不是B功耗预测。写入创新说明，实际B功耗仍未取得。
- 准备了**未执行**的后继只读命令：`b_synth02_result_ready.txt`读取完成后的摘要；`b_synth02_structure_ready.txt`绑定实际摘要/网表生成新结构警告清单。必须等综合真实passed、前台监视器结束或仅停止监视器后才能输入，不自动启动新EDA，不重复已存在的结构输出。
- 09:23:39.807516监视器显示synth183038 running、queue184658 waiting_synthesis、完成=[]、可选失败=[]、error=None。可用空间升至**257.7529296875GiB**；额外回升原因未核查，不能计入本轮清理成果。本轮仍只删除上述四VCD。最近截图`b_monitor_0924.png`已读取。
- **现场仍为VNC18874435/workspace3前台只读monitor_v2，不能直接输入shell命令。** FZ关闭，无本地长任务，无待Return输入；原综合/队列不得重复。继续等实际结果，不改变已固定硬件或验收口径。
