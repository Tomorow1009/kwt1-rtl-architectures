# S0后继工具传输检查点

**20:46:54最新观察：** 原synth03父75787/DC76822仍running/error=None，accelerator首轮优化已完成并进入`Beginning Pass 1 Mapping (Incremental)`（hold修复），DC已运行1:09:18/CPU1:09:05。中间面积约0.79mm²不能当最终面积，CPU及顶层尚未完成；TIM-134提示两条高扇出网，须用最终时序审核核对。前台仍watcher91575，没有未完输入或传输。新S0功耗审核profile本地补齐：未知活动清单/四段窗口/新分块网表身份，26项相关检查通过，尚未部署；运行05c和后继774包不改。617启动脚本仍未传输或运行。S1–S4未开始。

**20:34:49当前恢复状态：** synth03原父75787/DC76822继续running，accelerator已输出`Beginning Mapping Optimizations (High effort)`；57:13 elapsed/57:04 CPU、99.7%，error=None。shared_sram已完成，CPU/SoC与最终链接尚未开始。当前前台只读watcher91575；本轮只读截图cell g2:525已结束，无未完输入/传输。后继774包的845文件/manifest/import均已完成，S0_FINISH_LAUNCH_20261115.py仅本地已提交617cf17，未部署或执行。**不要重复启动任何综合或收尾队列；先截图读取原作业终态。**

**20:26:46最新观察：** 原synth03父75787/DC76822仍running/accelerator、99.7%CPU、49:10 elapsed/49:02 CPU，日志Processing DW01_add_width4，error=None。只读watcher91575保持。新工具已部署，launcher仅本地准备未执行。最新Git **617cf17已push**，工作树当时干净。只读三次截图的functions cell g2:520已结束，无未完输入/exec；板端转发91027保持。下一步仍读取原综合终态，不重启、不修改05c受测包；S1–S4未开始。

**20:17:12最后观察：** 原综合仍running/accelerator、DC76822 CPU99.7%，39:36 elapsed/39:30 CPU；日志推进到Allocating blocks/DW算术单元处理，error=None。新工具774已部署且import通过，当前只有原综合在跑。已在本地准备handoff/team/evidence/S0_FINISH_LAUNCH_20261115.py（Python3.6语法通过），尚未传输/执行；它要求原synth03 passed、原父75787退出、summary身份正确、面积≤1.00、setup/hold非负及原锁不存在，才创建全新的s0_finish01并调用774包统一锁队列。无清理、无修改旧包、无自动重试。当前前台只读watcher91575保持。

**20:11更新，覆盖下方传输状态：** exec39807已61/61结束，服务器S0_INPUTS_PREPARED确认845文件及ce81bdd6…清单匹配，S0_NEXT_TOOLS_READY确认没有启动新EDA。20:09:39实际import s0_finish/s0_report通过，模块齐全。20:11:09原synth03仍running/accelerator，DC76822 CPU99.7%、33:33 elapsed/33:28 CPU，日志已从Processing推进到OPT-1206常量寄存器处理，无错误。shared_sram仍是唯一已生成独立DDC的块。

**当前VNC前台为新只读观察器PID91575，不是shell。** 每30秒显示原75787/DC76822状态与CPU时间，终态自动退出。所有输入exec39807/69865/31346已结束。要输入命令前先看截图，必要时Ctrl+C只退出此观察器，后台综合保持。截图takeover_local/s0_watcher2011.png。不要重跑传输、原观察器78421、任何旧launcher或综合。

2026-11-15 20:02，北京时间。恢复先读AGENTS.md、CONTEXT_HANDOFF.md、本文件、有效计划workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md及STATUS.c32_g32_20261115。

## 当前动作，先收完

**唯一VNC输入exec39807仍在进行**：local_runs/s0_finish_7743127/transfer.ps1，共61行，20:01:27已18行。状态同目录transfer_state.json。不要并发向VNC输入、不要重跑脚本或再次Return；当前是新Bash中的完整here-doc。最后会自动仅复制新工具包，校验全部manifest，输出S0_NEXT_TOOLS_READY only_cloned_inputs_no_EDA_started=true，不启动任何EDA。

当前VNC18874435/workspace3，旧只读观察器78421已19:55用Ctrl+C退出，截图s0_watcher_exit1955.png证实回到Bash；此后只读资源查询完成，输入传输开始。旧tcsh残缺here-doc仍保留不碰，workspace4不碰。板端转发91027保留。工具F:/linux_fpga_try/ac820.ps1；Windows输入工具仅用于既有Linux板端VNC控制。

## 实际综合状态

新S0综合仍是**05c923f包的s0_synth03**，父PID75787，子DC实际PID76822（ps comm common_shell_ex）。19:55:42实际观察running/error=None，子CPU99.7%、已运行18:06、CPU时间18:03，说明仍在计算；shared_sram块已mapped.ddc，accelerator映射中。边界characterize和clock_serialization.json已经完成。尚无最终CPU/DDC/跨块时序/面积/功耗，不重启、不修改运行输入。

路径：/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-05c923f/runs/s0_synth03；stage=t80_s0_synth。原manifest4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2。

19:55:42 /tmp空余98,500,583,424B，shared只有1,048,576B；不能当实时。下阶段必须重新读原锁/资源。没有启动后继队列。

## 新工具身份

分支codex/light-light126/t80-pipeline-c32-g32-20261115，工作树E:/fpga_race-two/kwt1-c32-g32-20261115。**774312747e7024b7c0b25db68a646fe4880a1cc3已push**；69bfa64是本轮主要报告/队列提交，7743127补齐精度join依赖。

新目标包：/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-7743127，ops=ops-7743127。

- 新输入845文件，manifest预期ce81bdd649b4168326bc910229fc6685f4f6e8e7d0bae44443bb449278205870。
- payload SHA e5481b8f5085530074c302d73a264e6a3ec59bb59eb7b77b30f4b8315c525f6c。
- delta SHA 6acf502ffa0472cca1b0a029278976ef26a25cfd54c63589da1ca5b458711cd6。
- 来自原833输入clone，仅固定工具overlay；原运行及服务器桌面T80/全部旧8路不动。
- 本地实际执行了delta内存重建并逐字核对完整payload；Python3.6语法通过。报告/队列静态导入闭包153项核对，所有项目模块均包含且与本地受测字节相同。
- local_runs/s0_finish_69bfa64仅为未传输的候选，依赖检查发现缺t80_precision_join，已废止为本地准备产物；**从未部署**，不能使用其manifest。

## 本轮完成

1. s0_report.py独立schema及运行包验证；t80_report显式S0分支，保留旧入口行为。先验证三DDC及原平台/库，再关联新网表自己的gate14/SAIF12/PT12；只允许同源ASIC14/240引用。项目门槛1.00mm²，归属未审清按同口径保守上界，完整窗口时间加权功耗，缺层不填零。结果仍须独立审核，不能自动冻结或进入S1。
2. s0_finish.py统一持原共享锁串行运行structure→gate14→SAIF12→timing/DRC→PT12。一个ProcessLedger追踪全部子进程，阶段失败停止后继，不重综合、不重启旧队列。降低阶段间shared满盘导致重新建锁失败的影响。
3. 报告4、来源2、队列2、复制2、实际子进程同锁2共12项检查通过。首次从错误cwd运行3项import失败，改在scripts目录执行通过，不是服务器或RTL失败。
4. 相关源码和运行进度已push；当前硬件与固件没有变化。

## 收完后下一步

- 先等待exec39807结束并查看takeover_local/s0_finish_7743127.png，确认S0_INPUTS_PREPARED及S0_NEXT_TOOLS_READY、实际845及manifest吻合。没有这些证据不能记服务器部署通过。
- 可见VNC只读复查原synth03，不发第二个综合，不改05c包；必要时重新启只读观察器。
- synth03真正完成后读取同最终网表的面积/setup/hold/宏/约束/结构及child_identity，不继承旧网表PASS。
- 后继统一锁入口需生成新的request，引用原05c S0实际summary SHA、新774操作包manifest及显式runtime-evidence对05c包注册。初始共享锁仍要有少量空间；不换锁、不自动删锁，旧8路与T80桌面完全保护。新queue未启动。
- 已知SAIF方法资格只读路径：/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck，SHA a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26。
- 全部S0完成报告及冻结后才进入S1，S1–S4未开始。原T64/G64取消后继，不能恢复。

更早失败、R4可恢复编译缓存归档、来源及完整恢复规则见CONTEXT_CHECKPOINT_20261115_S0_SYNTH03_DEPLOY.md及S0_SERVER_PREFLIGHT.md。已归档操作不要重复。
