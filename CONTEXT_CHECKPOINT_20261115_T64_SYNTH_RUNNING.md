# T64正式综合进行中 — 2026-11-15 17:18

恢复必读：AGENTS、CONTEXT_HANDOFF、T64_G64_RESUME_PLAN_20261115、原N1_T80_T64_G64计划、本检查点。按用户要求保护服务器桌面T80及全部旧八路，恢复T64→G64；每版仅前20条240任务。G64须等T64规定验收完成，尚未开发。

## 已完成及身份

- 生产RTL e2e83ce121963d499ea67914b4c34a05a0c58f27，64PE/4行、原32位ICB与真实共享读回，SHIFT10，物理220宏不变。
- ASIC14真实CPU通过354816个total/result/saturated，b9155b4/runs/t64_soc03/t64_soc；summary SHA8eb6e9822817c2bcdba325b977f7d27e381b8f2b0b2eb6f0331049a7474f7e2e。
- ASIC240前20条通过6082560个total/result/saturated，9934df8/runs/t64_serial02_batch20/t64_batch20；SHA50c42478461985dfd33f0324aa464dc3d775388d6e54e3de4f06c8d46f190d16。不得重跑。
- 固定12均值112568周期、150MHz折算1332.5278942505863task/s；240均值112567.75另列。
- CPU竞争：3552163/runs/t64_serial03_contention/t64_contention通过。225轮scratch，29946竞争拍、cpu_grants14603、dma_grants36243、scratch读写各7189、fair_max0。167650周期是竞争固件诊断值，不替换性能值。
- CPU恢复：3552163/runs/t64_serial03_sequence/t64_sequence通过，队列17:16:24已completed2；恢复固件未修改，76032输出/total与10阶段由原verify入口强制核验。最终摘要哈希在queue完成引用中，尚未本地逐字符抄录。

## 当前唯一队列

ROOT=/tmp/s4_21usr_t64_20261115_1510，active=ROOT/light-light126-t64-resume-3552163，manifest81f861731d29df3252c775e8bc1dcab8628b2f2f79c71fa504827c9e7d2ed763，881文件及三固件服务器核验通过。

队列active/runs/t64_serial03/state.json，实际Python **PID325056**；launcher报325042仅为启动进程。ops-3552163/singlelock_request05.json、t64_serial03.log。原锁持续持有，阶段不另取锁。17:17:54.711807实读running/t64_synth，error=None，completed2、ASIC14+240_REUSED=True。当时最新ledger仍为已完成sequence.log/child11077；综合在库/平台准备阶段，未观察到DC映射启动，不猜测已完成。

后继仍自动串行：synth→gate14→saif12→timing/drc/structure→power12→precision20。随后报告导出与实际审核、持久归档，之后才开始G64。当前没有T64面积/功耗结论。

## 修复和失败路径

原serial02在竞争固件metadata行数写死5处返回BAD_ARGUMENT，尚未启动DMA。3552163仅修为KWT_ICB32_ROWS并加必须四行编译检查；生产RTL、性能/恢复固件、数据/验证器均未变。新的单锁工具显式引用旧ASIC14与240并核验身份，9测试通过。正式诊断固件从Git LF源码构建，boot仅offset1864字节21→17，三套固件均验证。

第一次修复launcher因共享盘又满在启动前拒绝。launcher02对两份旧未运行T64 delta01/fix02的41个相同输入做保留路径/字节的硬链接去重，free4194304B后立即启动；原件路径、哈希、结果全部保留，T80/旧8路未动。回执ops-3552163/contention_repair_dedup02_{prepared,complete}.json。禁止编辑这些硬链接冻结输入。

本地打包曾对巨大重复verilog做低效SequenceMatcher；改完整压缩载荷后9秒完成。仅终止本地helper19276/5916，服务器队列未动。旧失败记录和所有历史包保留。

## UI与恢复入口

VNC18874435/workspace3，**前台只读watcher PID3636**，每30秒刷新；不要向它输入shell。要查询新结果先截图，然后Control_L c仅结束watcher，再输命令；后台325056不动。watcher遇failed或reports_ready_review_required自行退出，届时应确认shell。输入exec39078已结束，所有包/launcher传输50436/56052/48883结束，无半截heredoc。唯一持续本地转发91027保留。FileZilla没开。

简洁观察器local_runs/t64_remainder_watch.py及takeover_local/t64_remainder_watch_command.txt。最近截图t64_synth_started.png。综合通过立即读同一summary/metrics/area/check_timing，不额外启动DC；异常先读取原日志。

## Git及归档

独立工作树E:/fpga_race-two/kwt1-t64-g64-20261115，分支codex/light-light126/t64-g64-resume-20261115。上次push e8d4482，本条及竞争/恢复验收更新待提交。

源码/小摘要已同步，无厂商库、大产物或凭据。/tmp是运行位置，不是持久备份；t64_archive_runtime.py已准备并通过两项本地复制读回/活动状态拒绝测试，尚未部署或执行。共享空间反复耗尽，只能完成所有任务后再根据真实空间安排持久归档；不得删除T80与旧八路。
