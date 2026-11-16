# C80 精度、自己的门级14通过，完整SAIF采集中

**16:54最新：原58047/finish02仍在saif，已有L01、L02共2层通过，SAIF合计195,142,377B。L01为97,575,322B，窗口93149.990685—581056.608561ns、73,186周期；SHA `5de0976bb232db38ad2f69b444b61cc49b34afd6fe7625de35637fdb89eb9d6b`已现场机器断言。逐例采集独立核对输出、IRQ/WFI、最终ACK与排空及整个活动窗口；未完成12层、未生成C80功耗，不能冻结。新小证据为`C80_SAIF_PROGRESS_20261116.json`。最新已push ff14464，之后是本次活动证据和文档变更。**

恢复操作：第一VNC标签空闲，最后输入65330已结束；第二标签只读观察器73000于16:45:52开始、预计16:57:52自然结束，不能向该前台输入。旧64504已经正常结束。16:53 /tmp可用81,649,795,072B；共享盘仍须归档前重新检查。本地STATUS原followup_started_at/payload以及远端反斜线路径是旧交接遗留，修正为新02身份时不改变服务器文件。恢复先现场读原58047和59705，不重启、不重复采集。

**16:39最新：原58047/finish02在16:36已完成gate并进入saif，59705继续等待。16:38:20直接读取gate最终summary：passed、14例354,816输出、fixed12总847238周期，与ASIC相同；无SDF，total不可观察。summary SHA `4c57b9d0df63dc3bcc081a095eb1eabbf0c383069d4b666582702fd6ab34f8cd`，现场机器已确认等于原队列gate引用。SAIF当时0层完成，处于该阶段前部；不能先报活动/功耗通过。第一标签空闲，62174输入已结束；第二64504仍到16:40:39结束。最新push5184258，之后门级证据/本页/STATUS及C32只读宏面积核对待提交。**

更新时间：2026-11-16 16:25，北京时间。恢复先读AGENTS、当前计划、根交接、本页和STATUS；旧现场时间不代表实时状态。

**16:29更新：7977d86已push。16:28:39实际gate case_progress已6/14（extremes、rounding、layer_01—04），仍原58047/finish02的gate；59705等待，无新失败。第二VNC标签只读观察器64504最多36×20秒，约16:40:39自然结束，禁止向该前台输入。最近输入34294已结束；已切回第一标签，使用前仍看截图。**

16:32补充：只读统计原B0持久备份manifest（已验证SHA443a49be…193aea9），排除/cases后的原始分类字节为.saif1,472,193,093、.tsv1,034,553,996、.json442,057,157、.rpt288,186,931、.ddc231,555,072等；这是旧备份内字节，不是当前可删除清单，未做新的源存在/占用/哈希核对，不能据此删除。六份早期B0 DRC报告仍是已知独立候选，当前C80持锁运行时不清理。16:31共享又仅1,048,576B，但当前gate输出在/tmp继续，不重启。后续持久复制必须按真实压缩体积和当时可用空间检查；不可借此删除SAIF方法资格引用、桌面T80、旧八路或P80。所有输入43950已结束，第一标签空闲，第二64504观察器保持。

## 有效计划和保护

- 下载原计划及副本`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`已核对同SHA：`1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。
- S0/P80已冻结，当前C80；完成自己的功能、PPA、审核和持久复制归档后才能进入C32-A/可选B，再G32。正式批量只前20×12，不擅自全100。
- 最终32PE、150MHz/6.666666ns、SS/.99V/125°C、保守项目面积≤1.00mm²。原32位ICB/平台缓冲、真实源读→共享写ACK→原总线读回→最终写ACK/排空保持，X14/W12/acc32/total33/SHIFT10保持。
- **桌面T80_Delivery_20261113、任何旧八路数据绝不改/移/删。P80冻结包和备份保留。** 不修改运行中的C80源码、固件和配置，不清原团队锁，不重复任务。

## 代码和同步

本地`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。最新已push **a8ef315**；之后仅本页及交接更新。

唯一历史未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不添加、不运行。C80生产受测包始终 **74f3ae7bb479d5fdd7917702c4a2c0671eacb61b**，后续只补工具和文档，RTL未变。自己的本地48解码、14/恢复/竞争/两拍SRAM/raw/10000随机+32定向块已通过，不重复。

## 远端身份和当前运行

私有根`/tmp/s4_21usr_c80_20261116_1245`，包`light-light126-c80-74f3ae7`，1008文件manifest SHA **d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59**。

1. **父58047**：`私有根/c80_followup02.json`，16:21 finishing_final_netlist；实际`包/runs/c80_finish02/state.json`为running/gate，completed=[structure]。16:24:28在运行rounding门级子62530；此前extremes日志已生成。个别日志存在或简单marker不是整个门级PASS。
2. followup源`ops-followup02-3502772/C80_FINAL_FOLLOWUP02_20261116.py`，SHA **d5f012fefa01db49de5cb093774d7afee2547692a3f4611c7a2e25e73221cdc5**，payload **c37fc7f142d064f0d490289a5413b8250a59295aa7b1b8ba8e4d01104b0805c7**。它使用老ops9eda的已核验NumPy恢复工具和原c80_finish，原团队锁/进程账本不变。
3. **汇总父59705**：`私有根/c80_export_review02/state.json`，16:21 waiting_original_finish。源`ops-export02-00e0810/C80_EXPORT_REVIEW02_20261116.py`，SHA **4c001bb4603a52b3c6f24d95566442bc59c48ee9709e37cbd224b0982331048a**。16:22:48机器assert新PID/源身份。等58047自然结束后导出`runs/c80_report02/c80_report`、unknown_inventory02/connections02和model_review_snapshot；不自动通过、不自动归档/进入C32。
4. 后续finish固定串行：structure→gate14→SAIF12→timing/DRC→PT12。当前没有新综合。不要重复启动任何finish/export。

16:24共享可用**1,334,837,248B**，在其他存储活动下下降；本轮运行结果均写私有/tmp（此前约82GB可用）。不据旧空间直接开始持久归档。

## 自己的已完成证据

- ASIC14：354,816输出及total/result/saturated/坐标，真实E203 IRQ/WFI；SHA `4c3668ebe351804b43edd8cf1ec4a56ab4004ed2c8724cc73a8afcc4929b7cb1`。恢复/ABA和CPU竞争通过，引用旧详细检查点。
- 固定12总847,238、均70,603.1666667周期，150MHz折算2,124.5505985 task/s，相对P80吞吐+9.8326562%；非芯片实测。实际四段384,174事务；平均编码25,790B。
- 新综合：`runs/c80_initial02_synth/c80_synth`，summary **0d1b11b013e4c4ee1698417e20124c4cb5601b49aae3d8b4b15cd0f2f0b46fc5**，netlist **6a62a3aa792865390549dd11a841d0888501902c449c61c74aa82eecd2523b00**。保守项目0.9611361367002672mm²；setup+0.000216007ns、hold+0.00623399ns、220宏/0锁存器；不是完整阶段验收。
- ASIC240：`runs/c80_initial02_batch20/c80_batch20`，summary **8dca0f4f57548b2b0f58af3326b909a5a0034b7fa3adad4ccf3030a7b8793312**。240任务/6,082,560输出及total、零失败、compile_count1。批量均69,352.7125周期，范围63,179—80,297，宿主2,274.8368秒；不能替换固定12平均。
- **新FLOAT精度04通过**：`runs/c80_precision04_precision/c80_precision`，summary **d7e0dbb52d17659e78af3357688367d4624773221c7693ed3c543f2de2d84acb**。同批浮点重新计算，20条合并逐层最大0.20198143836753799%，最大单任务0.20953408931848963%，X/W/b裁剪和输出饱和均0。内部20，不是官方600。16:22:48服务器assert本地哈希正确。
- 本地小证据`C80_ASIC240_20261116.json`、`C80_FIRST20_PRECISION_20261116.json`、`C80_SYNTHESIS_OBSERVATION_20261116.json`等已push。**仍无C80功耗数字，未冻结。**

## 保留的失败和空间处理

原279630 initial02完成五个硬件阶段，末precision仅缺NumPy失败。原后继314678在precision03取锁因共享盘ENOSPC失败，completed=[]、没有子工作；export4047随后failed_preserved，均已退出。finish01不存在，所有失败不改、不重启。第一次部署新followup02又在启动前空间检查拒绝，没有控制文件/任务；新工具原位保留后使用独立单次启动回执，没有重传覆盖。

15:56共享曾恢复4.13GB、16:03又满。已按用户授权清理**旧B0**（不是T80/旧八路）的49,200生成输入副本2,616,732,144B。完整原备份`systolic-b-20261112_2320`已全63,653成员/7,006,124,866B回读，备份SHA **dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50**保留，全部日志/输出/结果保留。

清理源d6eadfb/SHA **122dc4476cd2e1972c7187fdbab91c1be15770f53c4b72697b14309c535a1798**，`ops-b0-cleanup14-d6eadfb`父56033已完成退出。结果`私有根/b0_archived_batch_cleanup14/state.json` SHA **39edc92bf5c29dbdaff714aef264c786246e9e20bbf305fa6f5ec1f0859130b0**，16:22机器assert；journal保留。清理时无团队锁、无本账号EDA；实际可读47进程无候选使用，三个系统桌面服务fd受限已明确记载，不能声称全部fd可见。任何新锁/EDA或未知受限进程会停止。不是放宽EDA锁。

1860c87入口`ops-after-cleanup14-1860c87/C80_LAUNCH_AFTER_CLEANUP14_20261116.py`，父58039已经完成退出；确认清理终态后只启动一次58047。不要再运行清理或该入口。旧cleanup13只是准备、未部署；P80包未包含归档模块的早期只读import失败保持。六份B0中间DRC报表961,987,609B仍未删除。

## 归档、C32和下一步

新copy02源码 **00e0810** 的`handoff/team/evidence/C80_COPY_ONLY_LAUNCH02_20261116.py`只本地准备，绑定export02/followup02；未部署、未运行。旧copy01在`/tmp/s4_21usr_c80_archiveops_20261116_1526`仅预部署，不能用它处理新链。待58047/59705终态退出、报告及模型快照审核后，在源root外运行只复制归档。完整回读、源前后哈希一致、记录模型范围后才冻结C80。

C32只读准备文件`workspaces/arch03/C32_PREPARATION_READONLY_20261116.md`；已解析枚举6336有效X坐标/屏蔽64个row99位置，未写C32 RTL、未开发G32。不要提前进入硬件下一阶段。

VNC仍使用现有板端ac820.ps1，恢复重读computer-use和F:/linux_fpga_try/AGENTS.md并重新windows。当前18874435、workspace3；workspace4不操作、FileZilla未用。所有本地输入（最近31447/79157/80600/88189/8848）已结束，第一标签空闲；第二旧观察器按时结束，但使用前截图确认。没有正在传输的本地会话。

下一步现场读原finish02/ledger和export02，不重启；完整门级后读SAIF首例窗口/体积，继续原12层队列；功耗/模型完成后审核、复制归档、冻结，再C32。压缩前更新本页和根交接，恢复后重读计划并核对完成/未完成/失败路径。
