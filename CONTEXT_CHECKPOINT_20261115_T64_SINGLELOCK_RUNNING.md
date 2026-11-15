# T64单锁队列实际运行 — 2026-11-15 16:13

## 16:20补充

16:19:49.501150观察同一队列running、error=None，批量55/240、failed=0、checked_outputs=1393920；当前simv297516为sample005/layer08，ledger child000056。含20%余量剩余1676.438秒；不能保证最终结束时刻。原lock/queue未重启。最后截图t64_batch_progress_1622.png（文件名近似，实际观察时间以画面为准）。watch文本已改为batch_progress.json简要字段，避免打印全部逐例列表。

另准备t64_archive_runtime.py，复制归档并逐成员读回，保留原件/外部symlink文本；2项本地测试通过，未部署/执行。归档须等全部作业结束和持久空间足够；当前不改活跃包，不增加EDA。4f597f7已push，归档工具与本补充待同步。所有转录传输、输入exec已结束，转发91027保持。

恢复读AGENTS、有效T64/G64恢复计划、根交接及本文件。桌面T80保持原样，旧八路全部保留。只前20条240任务；G64必须等T64完整验收。

## 已完成与当前实际作业

ASIC14已通过，354816输出，固定12均值112568周期、1332.5278942505863task/s。原run仍b9155b4/runs/t64_soc03/t64_soc，不重跑。**真实summary SHA为8eb6e9822817c2bcdba325b977f7d27e381b8f2b0b2eb6f0331049a7474f7e2e**；早前抄写错误由新队列引用检查阻止，服务器state与实际hash一致，已经修正交接文档。原结束时间15:37:02.589594。

工具9934df8已push。单锁队列保持原共享锁，所有子进程经同一ProcessLedger等待回收，独立stage目录/回执。43项相关工具测试通过；没有修改T64 RTL或固件。

- ROOT=/tmp/s4_21usr_t64_20261115_1510
- BUNDLE=ROOT/light-light126-t64-resume-9934df8
- manifest SHA=32f48cc22391667881476ba6bf6ad7e26b69c6693e19182fb8688a69ac596c68，881文件和三类固件已服务器预检通过。
- OPS=ROOT/ops-9934df8
- 主队列BUNDLE/runs/t64_serial02/state.json，主日志OPS/t64_serial02.log。
- 当前stage BUNDLE/runs/t64_serial02_batch20/t64_batch20。
- **16:12:44.478320实读**：主PID289025，running/t64_batch20，error=None；编译子PID289973，中央ledger child_000001，tmp剩100243980288B。
- launcher03 SHA2367969121af07fb6717b73ba4c4d54dcb25dabfa04260f4a1251d00160a4bf3，源码保存handoff/team/evidence/T64_SINGLELOCK_LAUNCH03_20261115.py。唯一新request为OPS/singlelock_request03.json，不改请求或活跃包。

队列自动顺序：batch20→contention→sequence→synth→gate14→saif12→timing/drc/structure→power12→precision20。只串行，不再阶段间释放/重建锁。任何失败保留并停止派发，不能重复启动旧队列。综合完成可先读取初步面积/时序，完整结果仍须后续闭合。

## 已尝试及失败，全部保留

1. 旧soc01/soc02在锁mkdir处ENOSPC；soc03实际通过。
2. 旧包装器268175在soc03后启动batch20_01，再次锁mkdir ENOSPC，未编译；旧包装器已退出。
3. launcher01深目录临时硬链接创建ENOSPC，未启动队列。
4. launcher02改在旧T64包根创建短临时硬链接，对16个相同输入去重，全部原路径/字节保留，shared free4194304B；新serial01因旧ASIC摘要引用抄写错而在预检停止，无stage目录/EDA。
5. launcher03修正引用并用新serial02，实际取得锁且进入批量编译。本次没有额外去重。
6. 本地生成launcher03曾因CRLF/LF源字节校验失败，未发往服务器；已明确按服务器LF源生成并校验。

旧T64 delta01/fix02部分输入共享inode，禁止原地编辑二者。原42份数据、6份固件和本轮16份其他输入均有独立去重回执。T80与旧八路完全未动，不删除波形。

## 待完成与接续

240任务及全部T64 PPA/精度仍待运行；G64未开始。通过当前阶段不等于完整验收。后续导出报告要显式绑定旧b915 bundle作为ASIC14证据，report入口已支持runtime-evidence；最终需要持久归档，/tmp不是备份。

当前工作树E:/fpga_race-two/kwt1-t64-g64-20261115，分支codex/light-light126/t64-g64-resume-20261115。launcher源码及最新状态待提交push。旧工作树T80未提交资料保持不动。

VNC18874435/workspace3，FileZilla未开，板端转发91027保持。所有传输和输入会话均结束，无半截heredoc；最近53253已结束。明确键入takeover_local/t64_singlelock_watch.txt读取serial02，不用Up以免重复启动命令。当前截图t64_singlelock_serial02_state.png。压缩后先读本文件再观察实际作业，不将16:12状态当实时。
