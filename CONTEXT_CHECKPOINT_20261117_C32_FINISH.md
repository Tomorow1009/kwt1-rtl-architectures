# C32-A后半程：finish03已运行

最后观察：2026-11-17 02:03:28（北京时间）。压缩恢复后先读AGENTS、有效计划、根交接、本检查点及STATUS。不要把旧失败队列或历史PID当作当前作业。

压缩前核对：原finish03仍running/power_layer_07，前6层功耗已完成；最近/tmp69.66GiB。全SAIF12和timing/DRC查询均已完成，无新失败、无重启。首层PT的189个无时钟引脚已按既有解析器核对为静态JTAG DTM186＋reset_sync3；禁用弧c=6098、p=37440、C=69820、d=250，不关闭检查，不将本层替代全12最终审阅。当前映射area_inventory经哈希核验，仅匹配15个CLKLANAQV4_12TR40，均归platform_other，加速器匹配0；只是名称清单，不宣称门控覆盖度或节能。

上述事实补入C32_POWER_L01及C32_STRUCTURE_REVIEW证据。最近已push52e921b，本次记录随后同步。GUI终端空闲，无活跃输入，export_review03未运行；仍须等待原finish03全部完成退出并读取实际终态SHA，才能运行导出/连接/模型事实工具。原T80、旧八路、P80/C80冻结证据与所有备份保持。后续C32-B/G32仍未开始。

## 最新：SAIF12和诊断已完成，PT第3层运行

finish03父308692仍running，stage为power_layer_03，已完成structure/gate/saif/timing_audit/drc_audit及power_layer_01/02。没有重新综合、重跑240或另起正式EDA。导出export_review03仍未执行，C32-A未冻结。

- SAIF12全部通过304128输出、761444514B；SHA `7a9cdba2de2efcbe131b08071076202eaf27e86731a468e0e3c8661466e6353f`，01:48:48机器断言摘要及全部12周期匹配本版门级。见C32_SAIF12_20261117.json。
- 结构摘要SHA `e7c2a91b88ce496776f59a110f91b60bec08d1969f5dc0aefb4d18d08ccfb7eb`；声明端口6486、空载驱动133匹配；32PE/32转换器。其他警告实际为LINT1=4、LINT32=6256、LINT33=702，完整4个空载单元为原debug CSR两项、AON POR和PLIC IRQ寄存器；不豁免驱动功耗或面积。见C32_STRUCTURE_REVIEW_20261117.json。
- timing摘要SHA `968a02165572b84192c141dfd492062b7e975062150c7da216341fa3b4390543`，DRC摘要SHA `e345c6a1326fc33e3a00f313efdd32d06a82af602e4740ee8877d03897e44034`。0约束违反，驱动查询完整；3条高扇出为core_csr_clk、hfclk及AON crossing_clock，仍限定布局前模型。三个诊断哈希01:52:43机器核验。初次人工抄录timing哈希错误被断言拒绝，重新按十进制字节恢复后通过；未改变报告或网表。
- PT L01摘要SHA `f0454c777ad2c45b74c437f11dc636072b391f20329f6f6ee24049ce79ad9f0b`，01:54:22机器核验。74750周期，整机0.0487147979W、0.0000242762051925459046500J；活动直接映射237428、孤立默认1274、未注释0、总238702，220宏齐全，实际hf/lf为6.666666/66ns。单层值不当成12层平均；未知影响及模型仍待完整审阅。见C32_POWER_L01_20261117.json。

最新GUI输入已结束、终端空闲。一次截图请求早于本地会话38353结束而找不到文件，等待完成后成功读取，未重发服务器命令。最近已push4361d4a，本次活动/诊断/功耗证据随后同步。原导出工具、受保护路径、旧失败及清理限制按下文保持。下方较早状态均为历史。

## 最新：SAIF前八层通过，正在L09

01:27:50完成回执已包含L01–L08，活动合计507634642B。01:30:00原finish03父308692仍running/saif，子10278运行L09，/tmp70.33GiB；共享盘最新只读可用1048576B，当前队列未受影响，不进行额外清理。后继timing/DRC/PT12仍未开始。新增C32_EVIDENCE_INDEX_20261117.md列出有效受测包、运行目录和本地证据，原LOCAL_BRINGUP已标历史入口，避免误启动旧包。

最近已push7012008；本次结果索引与状态随后同步。export_review03仍已部署未执行。当前GUI输入结束、终端空闲，空间恢复19/20/22/23/24/25均不重复；桌面T80、旧八路、S0/P80/C80及备份保持。C32-A未冻结，C32-B/G32未开始。

## 当前：SAIF前五层通过，原队列继续

01:13:20已读取完成回执L01–L05，周期分别74750、73187、72186、72264、70798，合计活动317357854B。父308692仍running/saif；01:11子326234已退出L05模拟，/tmp70.51GiB。后续子进程用status_v4实时查询，不能沿用历史PID。导出/模型审阅/冻结未执行，C32-B/G32未开始。

本轮只读汇总本版area_inventory.json，哈希与冻结综合摘要匹配，145386个加速器叶实例分类总和与物理块一致。结果见C32_AREA_BREAKDOWN_20261117.json及C32_PROGRESS：阵列0.1122147600、X/W缓存含适配0.2476915783、转换0.0436027200、DMA0.0401173752、解码0.0216369720、MMIO0.0079566984、其余核心0.0859193832mm²。保守项目上界仍0.722402955mm²，不更换面积口径。README及验收表已移除过期的当前入口；历史失败仍保留。

一次临时只读查询误用complete_cycles字段报KeyError，核对p80_window.py后改用cycles并成功读取；未写远端文件或影响队列。最新GUI输入已结束、终端空闲。最近已push44098fd，本次进度与面积随后同步。下方条目按历史观察保留。

压缩前核对：父308692仍running/saif，最新子321863运行L03，日志00:57:44更新，/tmp70.68GiB。L01首例回执已核验，L02后队列进入L03；后继timing/DRC/PT12尚未开始。C32_PROGRESS新增S0/P80/C80/C32-A固定12同口径表，C32功耗保持待本版结果，未借旧值。最近已pushc4752e0；本次checkpoint随后同步。VNC空闲、无活动输入；空间恢复19/20/22/23/24/25全部完成，不重复。当前仍只跟进finish03，旧finish01/02不重启，export_review03未执行。

## 最新：SAIF L01已核验，正在L02

00:53:03父308692 running/saif，子319666运行L02，/tmp70.74GiB。00:54:05读取case_progress确认L01已完成并核验：25344输出、74750周期、SAIF63448403B、duration498333.283500ns、timescale0.000001ns；VCS CPU time298.780s。实际起止为93149.990685ns至591483.274185ns，包含完整装载至最终ACK/排空窗口，功能和坐标回执与门级一致。native SAIF仍采用X/Z合并驻留模型，不能提前宣布功耗审核完成。

当前子PID后续会变化，继续用status_v4读台账。无额外空间清理或新任务。export_review03仍未执行，C32-A未冻结，C32-B/G32未开始。门级里程碑已push85213ee；本次状态随后同步。最后GUI会话9445完成、终端空闲；每次恢复重查窗口。

## 最新：门级14通过，进入完整SAIF12

gate14自身summary已passed，14例354816输出（row/col/result/saturated）逐项核对通过，无SDF、内部total不可见；total由自己的ASIC240证明，不伪称门级total已观察。SHA **fde3abb19c8de0f4de3329141109783ad02135408c91b226382e89100cefdb7f**，00:48机器核验，并断言全部14例完整周期与本版ASIC RTL完全相同。详见C32_GATE14_20261117.json。

finish03父308692目前running/saif，completed为structure、gate，最新子317438正在`c32_finish03_saif/c32_saif/layer_01.log`。/tmp70.80GiB。当前不重复门级，继续本队列SAIF12→timing/DRC→PT12。全部成功退出后才运行已部署export_review03；当前未执行。GUI会话93752已结束，无活跃输入，终端空闲。最近已pushc9730e6，本次门级里程碑随后同步。

压缩前最新核对：finish03父308692仍running/gate，最新子313308运行L06，/tmp71.06GiB。没有失败或重启；structure已完成。读取映射结构证明确有32个PE、1阵列、32个requantize，sum32/total33；declaration_only6486且unloaded driver匹配，其他LINT-1/32保持待结合最终报告审核，未擅自豁免。完整gate14/SAIF12/PT12、导出/独立结论/归档/冻结未完成。后继export_review03已部署未执行；C32-B/G32未开始。最近已push2416ee2，当前更新随后同步。

最新进展：门级编译已完成，finish03父308692仍running/gate，最新子311236正在`c32_finish03_gate/c32_gate/layer_01.log`。日志实际ASIC启动、源读取与严格时序标记已出现，L01尚未结束。不依据文件名推断完整门级PASS；等待本阶段summary。VNC最后v4状态查询已结束，终端空闲，无活动GUI输入。

## 当前作业与恢复命令

- ROOT=`/tmp/s4_21usr_c32_20261116_2010`；BUNDLE=`ROOT/light-light126-c32-91135f6`。
- 当前队列`BUNDLE/runs/c32_finish03`，父PID **308692**，启动 **00:31:05.429536**。00:32:31状态running/gate，structure已完成；mapped_probe子309141已退出，接下来由同一队列编译和运行门级。
- 日志`ROOT/c32_finish03.log`；启动回执`ROOT/c32_finish03_launch.json`。原协作锁`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`由该队列持有，不能清锁、重启或另起正式EDA。
- 推荐只读命令：`python3 -B /tmp/s4_21usr_c32_20261116_2010/c32_status_readonly_v4.py`，SHA `1468f671fd258cdfe04857a4518e2d03024a65d96fa11bc1cad1ce2c336e3784`。V4优先读取finish03；旧v1/v2/v3保留但不能误以旧失败队列为当前状态。
- 当前VNC窗口18874435、workspace3第一终端空闲。GUI输入会话26709/82850/75895/53809/82984均已完成；无活动输入。恢复必须重新查窗口，不能使用workspace4。

## 已完成且不重跑

- S0/P80/C80已冻结，保留全部证据。C32-A的10000随机＋32定向、本地14、两拍SRAM、恢复、真实ASIC14、CPU恢复和竞争、新综合、自身240、FLOAT20连接已完成。
- 受测包91135f61c97c980039793c6637d0a06888638df0；生产RTL来自61246bb2a21c56a9bfd871fd68de93028d79f5fd。修复仅为竞争固件旧五行检查，RTL与IRQ/恢复固件不变。
- 包manifest `d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7`，1081输入；payload_91135f6.json SHA `bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc`。运行中不能修改这些输入。
- initial03父238916已退出，六阶段soc/sequence/contention/synth/batch20/precision齐全。成功终态SHA **37e1279f0c165b6fb50493c4d87edb2a994e159a90e22e48b92c41ef8ab500c0**。
- 自身240任务、6082560输出及total，零差异；均70929.40833333334周期、最小64833、最大81861。批量摘要SHA **2b51abd8844c73e342487e0be3e69c3cccfa4528296ef01ba15f1dca22621e81**。
- 同批浮点精度连接通过，最大逐层NRMSE0.20198143836753799%，最大任务0.20953408931848963%，裁剪/饱和0。精度摘要SHA **ca5a8e3afdac539bcad08367611cf38c5c602754c5eddf152e307be13e4775ca**。三份哈希00:05:47机器验证通过。不是官方600条。
- 固定12仍单独报告：866152总周期、均72179.33333333333、2078.1571825730357task/s（150MHz折算），比C80低2.183681386%。编码文件与C80一致，平均25790B、32014.5笔四段DMA事务。不可混用240的平均周期。
- 自己的新综合保守项目面积0.722402954997787mm²，明确新增0.5618935446998727，整机4.244619443828；setup+0.0000524521ns/hold+0.0010598ns，220宏/0锁存器。摘要SHA **ee08629b7cc9181d6e6db4ae21205ae931c6b1fe28f5c4420afd83097e8cef87**。SS/.99V/125°C、6.666666ns；独立最终审核与功耗仍待完成。

## 已失败与空间恢复：不要重复执行

- finish01父297927于00:06:49创建共享锁ENOSPC，零子任务，已退出。终态SHA **0c853c6c0bf5585437d49823d58f8c2527d05b28eb9cf11e491696acec5c58a6**。
- 恢复24完成：旧B0 drc04/drc05两份已完整归档repair_seed.ddc，66052096B；归档和逐文件哈希、进程检查通过，最终网表/日志/源/备份不动。回执`ROOT/b0_archived_repair_seeds24/state.json` SHA **60cdf04891898ebc28cfbc8ff55ad2033d471de7b288bb04c01973538fa8599c**。worker303992已退出。
- 当时实际free从1048576升至66060288B，但约32秒后耗尽；finish02父304144于00:21:00同样在锁创建前失败，无子任务。终态SHA **c502d28a5d4aee1689abe597b40465f42a2d98c17fb9468b28b3ecd7423eccec**。不是硬件失败，不重启它。
- `df -i`观察有110656空闲inode；quota工具未安装。不能确认共享盘其他写入来源。用户已说明没有团队持续写入，不再重复询问。
- 恢复25完成：仅旧B0 `systolic_b_power_final01_power_l01`至l12中的`disabled_timing.rpt`，共12文件/165281376B，逐项匹配原完整回读归档，原件清理后归档仍保留。回执`ROOT/b0_archived_diagnostics25/state.json` SHA **4e15ede39287b131c7960341774d04d7067bcf2367ed4bce9cf0d3a5d107f080**；free_after131072000B。worker308400已退出，followup返回0，随后finish03已实际运行。两个清理回执哈希00:32:31机器核验通过。
- 保留归档：PROJECT/backups/systolic-b-20261112_2320/completed-evidence.tar.gz，SHA dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50。PROJECT为IC下light-light126-undergrad-d2-20261109。
- 空间恢复19/20/22/23/24/25均已完成，禁止重复。所有新大产物在/tmp，最后可用71.25GiB。桌面T80、旧八路、冻结P80/C80及其备份完全保护。
- 首次initial终态SHA截图转录错误被断言拒绝，随后以十进制字节读回修正并机器核验；未改证据。旧失败转录及本地脚本编码入口问题记录于前一检查点，不当作RTL失败。

## 后续工具与完成条件

1. 跟进当前finish03，顺序structure→gate14（无SDF）→SAIF12→timing_audit→drc_audit→PT12，不并行、不重复综合或240，不提前进入C32-B/G32。
2. 当前启动工具`ROOT/c32_finish03_from_initial03.py` SHA291bcfe3ea26d23fe58f8baea34511c67b2c353cb9807f8cd3135f30fac13e27，**已经执行，不再启动**。新队列引用同一冻结c32_finish.py及网表。
3. 全部报告完成、父子退出后，用`ROOT/c32_export_review03_tool.py`，SHA **86247880c807fe298943b8a4913fa80fa5fd3a83fe6b62c739665deaec7d7dfc**，传`--initial-state-sha256`上述initial03成功哈希及`--finish-state-sha256`实际finish03成功终态哈希。此工具**尚未执行**。它绑定finish03，生成本版JSON/CSV/中文报告与未知活动/连接/模型事实；旧export01/02不能使用。
4. 依据自己的全部证据做声明条件下的独立结论，保留布局前估算、无SDF、静态JTAG和未知活动模型边界。整理归档并完整回读；共享盘没有容量时不删除受保护数据以强行复制。不得假称已有持久副本。
5. C32-A真实完成报告/冻结后，再评估C32-B缓存和G32门控。正式批量只20条，不自动跑100条。

本地分支`codex/light-light126/t80-pipeline-c32-g32-20261115`，工程E:/fpga_race-two/kwt1-c32-g32-20261115。最近已push34b2de0；下一次同步包含当前检查点和恢复回执。历史未追踪S0_SYNTH05_FINISH_LAUNCH_20261115.py不提交不执行。前期失败、平台依赖、完整浮点源和旧冻结证据见CONTEXT_CHECKPOINT_20261116_C32_SERVER.md及此前历史交接。
