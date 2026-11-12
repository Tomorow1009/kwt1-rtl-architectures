# N1进程记录修复包：部署与新批次启动记录

新OPS包已由根代理实际解包并通过Linux runtime身份核验；在截图桌面时钟
2026-11-13 05:36:50，唯一确认的新`n1_batch100_02`启动器返回PID 18736。
此处只记录部署和启动，不视为新的硬件PASS，也不以后台PID证明阶段已取得锁或编译成功。

新包为`light-light126-n1-v4-20261113_045945-0f62e4120790`，9,007,722字节；
ZIP SHA为`a9e14702e3092292826f1e37fc28fbc08064f2b0444ca744dd83217ba79920ce`，
manifest SHA为`1c55d5515de4258c77537e52387809ea04a33a334a4fefee8e2600ec2b7209e0`。
生产硬件仍使用原9305身份，不将工具提交误写为新硬件优化版本。

根代理执行的解包入口先核上传ZIP完整SHA和大小，再核808个普通文件均在唯一指定bundle下、
无父路径逃逸；检查私有根解析、UID与0700，独占创建新bundle后才解包。
实际`n1_server status`随后调用`n1_paths.configure`，检查全部807项manifest文件、所有者和私有根，
返回`SESSION_NOT_STARTED`。配置仍保留原共享盘的唯一协作锁，未改库、平台或数据地址。

05:34:19.775825只读检查显示共享盘可用9,077,522,432字节、私有盘746,456,555,520字节，
原锁不存在，同用户EDA进程列表为空。根代理记录此前一次准备回车被自动审批拒绝，随后清除
未提交输入，并于05:36:01再次核到`SESSION_NOT_STARTED`。之后仅执行一次已审查启动命令；
本记录没有把被拒绝的准备动作当作已启动或结束的任务。

新启动命令仅创建`runs`父目录，拒绝其符号链接；driver日志独占创建，session由N1入口新建。
使用固定`hex_short_all`、SHIFT10、layout4及主IRQ固件。必须完整重跑1,200任务；
旧ENOSPC失败批次已完成的65项仍是独立部分证据，不拼接或续接。

## 后续只读确认

`local_runs/n1_batch100_02_launch_20261113_0525/monitor.txt`（813字符）读取当前state、
progress摘要、最新child ledger和driver末8行，不重启任务。
`owner_identity.txt`（665字符）读取shared owner、private ledger identity和PID存在状态，
用于确认Linux实际启用一次共享owner与私有逐子进程记录。两者均通过Python3.6语法检查；
本资料代理未远端执行。监测发生在两个原子更新之间时，文件间可能短暂不同步，不能用单张
快照覆盖终态回执；若记录缺失或阶段失败，应先查原状态，不能自动另起新批次。

详细工具修复与32项本地测试见`N1_PROCESS_LEDGER_FIX_20261113.md`；
源码/固件/数据同一性见`handoff/team/evidence/N1_PROCESS_FIX_PACKAGE_IDENTITY_20261113_0505.json`。
本次逐项截图哈希、启动参数、审批重查范围及尚未核实项见
`handoff/team/evidence/N1_PROCESS_FIX_DEPLOYMENT_20261113_0537.json`。

该记录时刻尚待实际state/ledger检查、全1200终态及独立重审、严格时序、同网表门级与活动功耗。
完整100条浮点源也仍缺；不进入N2。私有`/tmp`证据最终必须持久化归档，不能作为长期交付位置。

## 05:39只读观察增量

已亲读`n1_batch02_owner_0539.png`与`n1_batch02_monitor_0539.png`。
前者实际桌面时钟05:38:46，显示`shared_owner_updates_after_acquisition=false`、
`DRIVER_PROC True`，当前owner SHA与ledger内记录一致：
`0c36f2761e4f7ad1244830533124fc3df104e551c17ed7ad2665cae8d5cd8694`。
后者05:39:30显示编译子进程20695，随后样本001的layer01与layer02分别出现
`N1_BATCH_CASE_PASS`，完整周期30,547与29,947；第三层子进程26685已记录。
这是至少两个任务的实际进度，仍不是完整1200验收。

长路径和JSON使此前state/progress及owner头部滚出截图，因此不据此补写未见字段。
新增`monitor_compact.txt`、`owner_compact.txt`、`log_compact.txt`分别最多7、4、3条短行，
三者合计最多14行；只输出关键计数、PID、布尔一致性、周期及宿主秒数，不输出长路径、
整命令或整JSON。尚缺数据以None/缺失标志展示，不填零。监测命令只读，不能启动或重启任务。

## 05:44紧凑观察增量

亲读`n1_monitor_short_0543.png`：05:43:19.839074，state为running，PID18736，
实际阶段started为05:36:45.043281；完成39任务、失败0，result与total各988,416项。
此快照的剩余时间估算含20%余量约8,889秒，属于运行时估算，不能作完成时刻承诺。
上一子进程31453已exited、wait_completed=true、returncode=0；子进程31504仍running，
wait与returncode为None。末项sample_004_layer_03为29,631周期、宿主3.42秒。

亲读`n1_owner_short_0544.png`：05:44:08，owner为18736/n1_batch100_02，
owner完整字典、原始SHA及冻结process工具SHA均匹配；共享owner后续更新关闭，driver仍存在。
因此N1新ProcessLedger已有实际Linux归属与收割子进程证据。未在服务器注入ENOSPC，
不能将本地故障测试误称服务器全故障覆盖。当前仍只确认39任务进度，完整1200与其他验收未完成。
