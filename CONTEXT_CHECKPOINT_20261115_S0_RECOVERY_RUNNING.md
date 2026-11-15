# S0增量恢复运行检查点 — 2026-11-15 21:30

压缩后先读AGENTS、CONTEXT_HANDOFF、本文、有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`和STATUS.c32_g32_20261115。新路线S0→P80→C80→C32→G32；最终32PE/≤1.00mm²、原32位ICB四段真实传输、SHIFT10、SS/.99V/125°C、6.666666ns、只正式20条240任务。S1–S4未开始。

## 当前真实运行，不重复启动

- 运行根：`/tmp/s4_21usr_t80_20261115_1830`。
- 新冻结工具包：`light-light126-t80-s0-a5ce90a`，工具提交a5ce90ae4a967f0fddb12e3185fda5444ef9964f，852文件已服务器核验。
- manifest SHA **6d40f4d67fc94a3b10fe3e1ece27076cf7affc33297602078721397165ca8d78**。
- 当前session=`runs/s0_synth05`，阶段目录`t80_s0_synth`，父PID **126260**；开始**21:28:13.994272**。
- **21:29:58.219963实际观察：running/error=None，characterization完成，正在shared_sram块映射；DC子126956、CPU96.4%、elapsed23秒/CPU22秒。** 后续加速器增量恢复、CPU及最终链接尚待。
- 控制/主日志：`ops-a5ce90a/s0_synth05_launch/launch.json`、`driver.log`；子进程回执`runs/s0_synth05/process_ledger/child_*.json`。
- 仍使用原共享锁`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`；不换锁、不清锁、不并发EDA。

VNC18874435/workspace3当前前台为**只读watcher127118**，不是shell。每30秒读父状态/最新child/CPU及日志尾6行，终态自行退出。输入其他命令前先截图，必要时只Ctrl+C退出该watcher，不能信号父126260或DC。所有输入/exec33855、16016、1192、67984均已结束，无半截传输。旧tcsh残留输入不碰，workspace4不碰。板端转发91027仍保持；FileZilla关闭。截图`takeover_local/s0_synth05_watch2131.png`。

## 已保留的失败与恢复依据

1. synth03/05c包父75787/DC76822，**20:49:56.234720 failed**。共享块完成，加速器4438秒写出mapped.ddc/v/sdc，但characterize导出两条`set_map_only [get_cells U2055/U2048]`；原linked RTL无这些旧mapped单元，出现两条UID-95和CMD-036。运行器即使DC exit0也拒绝，正确保留失败；CPU未开始。原目录和日志不修改。
2. 原synth03 state SHA **83a9b896cb541a0631f7888ea796a10a5dcd7fe863b2fdeb91756a57e0e3783d**；原manifest **4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2**。
3. 新`s0_recovery.py`实际服务器预检已通过：固定失败包、状态、原源码/库/脚本/日志/输出；仅此两条错误可作未验收增量起点。新的块编译先在原linked RTL证明对象不存在，清理只涉及这两条优化指令，保留所有端口/负载/时钟/延迟预算，再加载seed重新incremental compile/hold/报告。不是复用失败PASS。
4. synth04父120765在共享锁mkdir处ENOSPC失败，**未启动DC**，目录保留。不要重启该session。
5. 空间启动器e2db114首次因运行目录应为`n1_contention_01`而非`n1_contention01`停止；02因手工转录字节数10,651,815与实际10,651,781不符停止。两次均发生于归档/删除前；原脚本保留。03使用分段实查的精确路径/大小，实际成功归档并启动synth05。
6. 当前03脚本来源 **b0a2548**，文件`handoff/team/evidence/S0_RECOVERY_SPACE_LAUNCH03_20261115.py`，服务器`ops-a5ce90a/s0_recovery_space_launch03.py`，SHA **2606f9eba050ebc7935442ee9cd9d1c0bc338714dd7988cbc1db434fa1d80315**。已执行，不再执行。

## 本次唯一实际归档

仅已通过的N1竞争测试普通编译缓存：
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-n1-v4-20261113_013211-9305c6948c76/runs/n1_contention_01/n1_contention/csrc`。

- 35文件、10,651,781B；tar.gz全部成员解压后的SHA和大小核对后才删除重复普通文件。
- 压缩包已核验返回原stage：`n1_contention/csrc_regular_files_20261115.tar.gz`。
- archive SHA **ad9cfaa5303e28f8dfed4a349c35297dc38c85d9c35c3af79a8154ff5ff95ec6**。
- 临时压缩包及逐文件回执在`ops-a5ce90a/n1_contention_csrc_regular_files_20261115.tar.gz`和`n1_contention_csrc_archive_receipt.json`。
- 原state、summary及结果/日志/源码均保持；目录和符号链接保持。完成时shared可用9,437,184B，随后已成功取原锁；非实时空间数。
- **服务器桌面T80_Delivery_20261113与全部旧8路均未操作。** 不重复此归档，不把归档缓存说成结果删除。恢复编译缓存时从保留tar解压。

## 本地及部署完成

- S0三DDC/边界/身份工具及新恢复工具20项相关检查通过；默认块脚本与05c旧版生成文本逐字一致。第一次本地漏加号的语法问题已修复并重跑。
- S0未知活动/可选审核独立profile26项检查通过，拒绝伪装旧T80网表；新包852文件及136模块静态闭包/Python3.6语法/源码字节一致检查通过。T80引擎state键不代表继承旧网表通过状态。
- 旧774包845文件仍在，但没有启动收尾queue。**617cf17固定synth03完成启动器已过时，不可运行**；新综合完成后按真实摘要/新PID另建收尾请求。
- 7156303/e55c1c8候选未部署。a5包852是当前唯一恢复运行包；源码不能在运行中修改。
- 最新已push **b0a2548**，个人分支`codex/light-light126/t80-pipeline-c32-g32-20261115`，工作树`E:/fpga_race-two/kwt1-c32-g32-20261115`。本检查点等进度文档随后同步；旧工作树不动。

## 下一步

1. 继续当前synth05，重点确认加速器增量日志没有旧map-only错误，再等CPU和最终顶层；不要重启以追求时间。
2. 完整同最终网表面积、setup/hold、220宏、0非预期锁存器/组合环、边界覆盖及child identity核对。中间area/slack不能当正式PASS。
3. 通过基本门槛后用同一原锁收尾工具串行structure→gate14→SAIF12→timing/DRC→PT12。使用a5或后续新操作包，显式注册当前综合包，固定真实summary SHA。不要用旧T80门级/功耗替代新网表。
4. S0报告JSON/CSV/中文、活动模型/未知影响说明及冻结后才进入S1；同源ASIC14/240可引用，不重跑旧T80。
5. 新/tmp产物仍需最终持久归档，当前不是最终交付。共享空间按实际核查；不清旧8路或T80桌面。

更早cap/synth工具失败、R4可恢复编译缓存归档、完整基线路径见S0_RECOVERY_TRANSFER、S0_NEXT_TOOLS_TRANSFER、S0_SYNTH03_DEPLOY检查点。已完成操作不重复。
