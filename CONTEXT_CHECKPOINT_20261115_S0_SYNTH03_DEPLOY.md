# S0第三次部署检查点

**19:55本地后继准备：** 新增s0_report.py及t80_report.py显式S0分支、新增s0_finish.py统一原锁串行收尾；s0_prepare_bundle overlay增加这些工具，下一包不得覆盖05c运行包。12项相关本地检查通过（报告4、来源2、队列2、复制2、真实子进程2）；首次从错误cwd运行导致import失败，正确scripts目录重跑已过。工具待提交/部署；报告未生成，收尾队列未启动。最后19:51:44当前综合仍在accelerator，无错误。前台watcher78421仍在，所有输入结束。

**19:41当前真实运行：** 26行输入exec32639已结束，05c包841文件及manifest4473686e…实际匹配。R4 sequence普通缓存35文件6,699,345B归档回读并复制返回共享盘，SHA200e23d33de51ab78a1b42b425676859c9d288d2fcedd4507f1a68e7adf16f8f，原结果不变。synth03实际父PID**75787**，19:38:00状态running/error=None，边界提取及clock_serialization.json完成，**shared_sram独立mapped.ddc已完成，加速器块正在综合**。19:41:13再次观察仍running/accelerator，尚未最终网表/面积/时序。

**VNC当前前台不再是shell，而是只读观察器PID78421**：每30秒显示原synth03状态/最新块日志，不写文件、不启动EDA；任务终态会自行退出。截图takeover_local/s0_synth03_watcher.png。后续要输入命令时，先确认当前仍为此观察器，再Ctrl+C只结束前台观察器，不能中断后台75787或DC子进程。不得把shell命令直接键入观察器。板端转发91027保持，当前没有未结束输入。

2026-11-15 19:34，北京时间。压缩后先读AGENTS.md、本文件、CONTEXT_HANDOFF.md、有效计划workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md和handoff/team/STATUS.json。按用户要求持续推进，无需逐步确认。

## 目标及保护边界

路线S0分块综合→S1 P80搬运流水→S2 C80无损编码→S3 C32-A及可选紧凑缓存B→S4 G32实际ICG。最终固定16×2/32PE、项目面积≤1.00mm²、150MHz/6.666666ns、SS/0.99V/125°C。原32位ICB及平台并发参数不改；源读→共享写成功ACK→原总线读回→解码→全部结果写ACK/排空，不能旁路共享存储。数值X14/F10、W12/F12、累加/偏置32、total33、结果16/F12、SHIFT10不变。正式批量仅前20条/240任务，不能自动扩展100条。

服务器桌面/storage2/2026contest/server4/s4_21usr/Desktop/T80_Delivery_20261113与全部旧八路文件不写、不移、不删。T80生产硬件876b883保持，旧T64/G64后继已停止；旧T64综合自然完成，所有结果保留，不恢复旧队列。

## 工作树与同步

E:/fpga_race-two/kwt1-c32-g32-20261115；分支codex/light-light126/t80-pipeline-c32-g32-20261115。Git命令带-c safe.directory=该绝对路径。

最新工具提交**05c923fe178230f0550d79dfd4b4ae3fcfc0c79f**已经push。此前0bf4af3修版本/文本精度，2e85053为恢复记录，d497c19为空间处理及预检记录。当前尚未提交新S0_R4_SEQUENCE_CACHE_SYNTH03_20261115.py和本检查点/进度更新。不要修改正在上传或已冻结的输入。

## 已完成及失败原因

- 保存新计划、独立分支、验收表；原文SHA1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。
- S0分块工具实现：从原实测T80 mapped环境characterize边界，使用同源未映射linked.ddc分别映射共享/加速器/CPU，顶层只链接不compile；缓存指纹、子网表前后不变、逐叶面积归属以及新网表gate/SAIF/PT入口。
- 原833输入包复制成c6及0bf两个841文件新包，全部清单核验通过；原源码/固件不变。新硬件阶段S1–S4未开始。
- cap01、02、03均因共享盘满无法mkdir原协作锁而失败，DC没有启动；不得重跑这些session。cap04/PID62910实际DC执行5秒完成，通过终态/summary已由后续launcher核验。
- synth01/c6/PID64154：19:09:16–19:09:20失败在`dc_shell -version`；此安装器打印正确版本但退出1。新工具改为正常退出Tcl会话的banner读取完整T-2022.03-SP5-5，不放宽ProcessLedger失败规则。
- synth02/0bf/PID71485：19:26:01–19:27:02已进入characterize并导出加速器边界，在waveform属性嵌套列表处失败；锁自然释放，无当前EDA。get_attribute官方手册说明每对象返回一个属性值，waveform又是列表。05c修复只展开该外层列表，不改变数值。
- 安装DC自带手册位于/eda/synopsys/dc/dc_2022.03-SP5-5/doc/syn/man/cat2。已核对characterize的准确选项-constraints、write_script -format dctcl -nosplit -output；write_sdc无-significant_digits，不能猜测添加。
- 原mapped.sdc及characterized.tcl会把周期6.666666舍入成6.66667。现同时导出原生period/waveform高精度TSV，保存raw脚本，仅恢复create_clock数字字段；端口延迟等不动，未知/缺失/重复时钟或超出舍入误差均拒绝，实际重载周期守卫保留。
- 本轮相关13项本地检查全部通过，包含实际Tcl解释器的嵌套/平铺waveform及失败输入；其余S0来源/复制测试和8项原T80兼容检查前次已通过，不无故重跑。当前尚无S0映射、门级或PPA PASS。

## 历史部署步骤：已完成，不重复执行

**主机exec32639已经结束**，local_runs/s0_fix_05c923f/transfer.ps1的26行全部完成，841文件及manifest已核验。完整引导已完成：重建payload、复制新包、归档并核验旧R4序列测试普通编译缓存、启动新s0_synth03。不得重新执行。

目标root=/tmp/s4_21usr_t80_20261115_1830；bundle=light-light126-t80-s0-05c923f；ops=ops-05c923f。

- 新manifest SHA4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2。
- 新payload SHAa28e0449a53d604444c0f97453ee9041125591915e37f33e625287c2397445b1。
- delta SHA f0b8f94f3476bb9c3c2d52eb22b773d9b40613dea769c4fab599a1b19a2ec0c7。
- 启动脚本handoff/team/evidence/S0_R4_SEQUENCE_CACHE_SYNTH03_20261115.py实际传输SHA4ddc137fd01b562d0396a9e5ff4dbfc4fdb55c62ae32a1730fc1e1855936e1fd。
- 上述差分引导已在本地实际执行只读重建，完整payload逐字一致；Python3.6语法通过。

完成先查看takeover_local/s0_fix_05c923f.png及新截图，看S0_INPUTS_PREPARED、归档回执、S0_SYNTH03_PID和Bash提示符。之后只读ops/s0_synth03_launcher.json、ops/s0_synth03.log、新bundle/runs/s0_synth03/state.json及t80_s0_synth/characterization/characterize.log。**脚本自动启动，不再手动运行旧synth_command.txt或任何旧launcher。** 如果失败保留所有目录，新工具和新包修复，不原地改输入。

## 空间与归档

共享盘空余反复从8–40MiB迅速降至1MiB；/tmp约98GB可用，MemAvailable约726GiB（18:45观察，正式启动仍要核对）。原共享锁必须保留原路径IC/.arch02_team_lock；不能换锁、删除他人锁或终止他人进程。

已对两个无runs的旧T64包相同输入合并存储，所有路径/字节/manifest保持，回执ops-c6aa1e2/s0_t64_dedup_*.json。随后按用户已有清理授权，对旧R4已完成运行的普通csrc编译缓存逐文件归档并完整SHA/大小回读后释放原重复缓存，归档均复制返回各原stage/csrc_regular_files_20261115.tar.gz；符号链接、目录、state/summary、结果、网表、数据和波形均不改。全部tar及逐文件回执还有独立/tmp副本；需要恢复csrc时按回执还原普通文件。

已完成R4 gate01（38文件48,122,849B）、metrics14（35文件9,970,277B）、final1200（35文件9,970,979B）、contention01（35文件9,639,341B）及sequence01（35文件6,699,345B）的缓存归档。具体SHA见本文件顶部、上一检查点及ops回执。原stage与summary身份、无人使用及逐成员回读已检查；不要重复归档。

## GUI及恢复纪律

板端工具F:/linux_fpga_try/ac820.ps1，VNC窗口18874435（仍需windows核对），workspace3的新独立Bash终端。旧tcsh终端保留未闭合失败输入，自动审批此前拒绝闭合它，绝不可再输入/执行。workspace4不碰。FileZilla已关闭，旧代理DNS公共地址检查失败，未绕过。板端VNC转发exec91027保留。

全部新脚本、失败与空间回执只在新ops/包，原T80桌面和旧8路从未操作。下一步先取得S0三个DDC、顶层跨块时序/面积/结构，然后新最终网表自己的门级14、SAIF12/PT12及报告，完成S0冻结才进入S1。
