# 用户暂停，等待新计划 — 2026-11-15 17:26

**最新用户要求暂停并改走即将提供的新计划。本轮停止推进，不自动恢复原队列或进入G64。** 桌面T80和全部旧八路继续保护。

## 已确认的暂停方式

17:25:56.177774服务器确认：调度Python **PID325056状态T（SIGSTOP）**；当前综合子进程 **PID15147状态R，未发送任何停止/终止信号**。父子身份、UID、父进程关系、完整命令、原锁owner及综合stdout直接写icb32_synth.log均已核对后，只暂停调度父进程。现有综合继续生成结果，后续门级/SAIF/PT等不会派发。

原队列JSON可能仍显示running/t64_synth，这是暂停前文件，**进程状态和专用暂停回执才是当前状态**。原协作锁保留，不能当陈旧锁清除。综合结束后，子进程可能等待父进程恢复以回收；不能因此重启综合或旧队列。

暂停回执：

`/tmp/s4_21usr_t64_20261115_1510/ops-3552163/user_pause_20261115_1724.json`

含driver/child精确start_ticks、命令、queue、锁owner SHA、子进程状态、未给子进程发信号的记录。恢复必须等用户新指示，先核对回执与/proc身份、原锁和已有综合结果；若仍需原队列，才对核验后的原父进程SIGCONT。若新计划改变后继，先制定安全交接，不直接恢复让旧队列自动派发。

## 已完成

- T64生产e2e83ce：本地10000随机＋32定向、14完整例、1/2拍SRAM、反压及恢复通过。
- 真ASIC/E203十四例354816个输出、total及饱和检查通过：b9155b4/runs/t64_soc03/t64_soc，SHA8eb6e9822817c2bcdba325b977f7d27e381b8f2b0b2eb6f0331049a7474f7e2e。
- 原前20条240任务6082560个输出、total及饱和通过：9934df8/runs/t64_serial02_batch20/t64_batch20，SHA50c42478461985dfd33f0324aa464dc3d775388d6e54e3de4f06c8d46f190d16。不扩大100条，不重跑这两项。
- 3552163竞争固件修复后实际通过：225轮scratch、29946竞争拍。CPU无复位恢复序列也通过。
- 固定12性能均值112568周期，150MHz折算1332.5278942505863task/s；240任务均值112567.75另列。
- 工艺库编译、SoC链接已通过；映射综合正在执行。当前还没有最终T64面积、时序、门级、功耗或全项验收结论。G64未开始。

## 活跃包与目录

ROOT=`/tmp/s4_21usr_t64_20261115_1510`

active=`ROOT/light-light126-t64-resume-3552163`

manifest=`81f861731d29df3252c775e8bc1dcab8628b2f2f79c71fa504827c9e7d2ed763`，881文件及三固件通过。

queue=`active/runs/t64_serial03/state.json`

综合=`active/runs/t64_serial03_synth/t64_synth`，日志icb32_synth.log，ledger child_000007.json。

原request=`ROOT/ops-3552163/singlelock_request05.json`，主log=t64_serial03.log。

仅诊断竞争C/镜像及工具变化；生产RTL、性能/恢复固件、数据和验证器未变。修复boot仅offset1864的一个字节21→17；9项工具/契约测试及错误ROWS5编译拒绝通过。

## 尝试路径与保留

- 原serial02在五行检查残留返回BAD_ARGUMENT，失败保留；355修复仅诊断固件并复用已过ASIC14/240。
- 共享盘曾多次满；只对旧未运行T64 delta01/fix02相同输入保留全部路径/字节做硬链接去重，最近41文件、回执存ops-3552163/contention_repair_dedup02_*.json。T80/旧8路/历史结果未删改。
- 首次暂停输入超过helper1000字符限制，未键入命令、无信号；随后分900+658字符输入成功。截图takeover_local/t64_pause_result02.png。
- 本地低效差分helper已结束；正式包、所有传输输入均完成。暂停exec52641已结束。

## UI、Git与待办

只读watcher3636已退出，当前VNC18874435/workspace3为shell提示符，无半截输入，不再监控。板端转发session91027保持；FileZilla未开。不能自动重新启动watcher或EDA。

独立工作树E:/fpga_race-two/kwt1-t64-g64-20261115，私人分支codex/light-light126/t64-g64-resume-20261115。上次push4b229aa；本次暂停记录待提交同步。/tmp仍不是持久备份，归档工具未执行。

等待新计划；收到后比较与当前冻结硬件、已完成证据及在跑综合的关系，再更新有效计划和后继队列。压缩后先读本文件和根交接，不能按旧“持续推进”恢复。
