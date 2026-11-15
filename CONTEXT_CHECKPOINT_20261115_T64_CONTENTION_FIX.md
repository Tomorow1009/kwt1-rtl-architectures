# T64批量通过与竞争固件修复 — 2026-11-15 16:58

## 17:14竞争通过

17:15:24.549548实读queue325056 running/t64_sequence/error=None、completed1。新只读watcher **3636** 在前台，39078输入完成；旧325493已结束。自动每30秒更新。恢复必须按当前3636观察器判断，不能把旧PID当实时。

17:14:35截图已显示T64_SINGLELOCK_STAGE_PASS contention；真实CPU225轮scratch，competing29946、cpu_grants14603、dma_grants36243、scratch_writes/reads各7189，fair_max0。完整layer01的诊断窗口167650周期，**不是性能固件周期**。sim宿主9.116230098996311秒，原输出文件保留，最终摘要hash以queue引用为准。接续sequence，无重启。截图t64_watch_interrupt_readonly.png。

仅以Control_L c退出前台只读watcher325493，后台325056不动；正在重新打开缩短日志显示的观察器，输入exec尚需收尾。当前T64竞争修复已实际通过，不再重跑该项。

## 17:12实际启动

17:12:52.029129首次实读：queue实际Python PID **325056**，status=running/stage=t64_contention/error=None，ASIC14+240_REUSED=True。launcher返回的325042是启动进程，不代替state的实际PID。**前台只读watcher PID325493**，每30秒显示；需要输命令前先截图并Control_L c仅退出观察器，不终止后台队列。89627输入已结束。截图t64_serial03_first_watch.png。

新队列PID325042，3552163/runs/t64_serial03；request为ops-3552163/singlelock_request05.json，log同ops/t64_serial03.log。launcher02源码SHA1d2fe4cfca174897b6581ec0babc296feb46935de4ec677c9f592f2f46a163d2，保存handoff/team/evidence/T64_CONTENTION_REPAIR_LAUNCH02_20261115.py。

初次launcher01因共享盘重新满在free检查拒绝，无队列/请求/EDA。第二次只对旧T64 delta01/fix02输入41个完全相同文件去重，原路径/字节全部保留，free4194304B。prepared/complete回执ops-3552163/contention_repair_dedup02_*.json。没有删除T80、旧八路或历史结果。截图t64_rowfix_launch02_result.png。

全部包/launcher传输完成50436/56052/48883。正在启动只读观察器local_runs/t64_remainder_watch.py，新前台状态须截图确认；后台queue不能中断。原14/240明确跳过。源码/生产固件不变；只修诊断行数。Git已push a8e3fa4，最新运行记录待提交。

## 17:08部署补充

修复提交35521631b9fdedff03ec6e7c50f1558e38b2aafd；正式包local_runs/t64_resume_3552163/reconstructed，881文件，manifest81f861731d29df3252c775e8bc1dcab8628b2f2f79c71fa504827c9e7d2ed763。三固件本地校验通过，生产/性能/恢复输入相同；竞争boot只改offset1864的一个字节21→17。ROWS5负编译已指定cache重试并正确拒绝。

**VNC包传输exec50436正在进行，32行，状态local_runs/t64_resume_3552163/transfer_state.json。不能同时输入新命令。** 原本地打包脚本因SequenceMatcher对重复verilog文本低效，改为压缩完整镜像后约9秒完成；旧本地进程19276/5916已结束，exec4438 exit1。PowerShell Stop-Process报错，最终仅对精确匹配的本地helper用taskkill终止，没有动服务器进程。

17:01:02.068506服务器只读：LOCK ABSENT、EDA[]、tmp99410456576B、shared401604608B。新启动器准备为handoff/team/evidence/T64_CONTENTION_REPAIR_LAUNCH_20261115.py，SHA cf806b467b0e125f0134b42c2cc49dc61e620aad275b3b9e420918f509543b0b；传输入口local_runs/transfer_rowfix_launch.ps1，共7行，尚未执行。它会新建ops-3552163/request04、t64_serial03，引用原ASIC14与240，跳过成功阶段，只从contention接续。无需存储去重，任何原任务/锁存在则拒绝。

等32行包传输完成，截图确认T64_ROW_FIX_READY，再执行7行launcher并观察新queue。只读自动观察器已准备local_runs/t64_remainder_watch.py及takeover_local/t64_remainder_watch_command.txt，尚未启动。Git最新a8e3fa4已push，含ASIC240观察JSON与新版验收表。桌面T80与旧8路仍未动，G64未开始。

恢复先读AGENTS、T64_G64_RESUME_PLAN_20261115.md、原N1_T80_T64_G64计划及本记录。桌面T80和旧8路完全保护；仅前20条240任务，G64须等T64完整验收。

## 已完成

- 生产RTL e2e83ce不变。ASIC14在b9155b4/runs/t64_soc03/t64_soc通过，354816输出，摘要SHA `8eb6e9822817c2bcdba325b977f7d27e381b8f2b0b2eb6f0331049a7474f7e2e`。
- 真实ASIC/E203批量在9934df8/runs/t64_serial02_batch20/t64_batch20通过，240任务、6082560输出与total及饱和核对，failed0。摘要SHA `50c42478461985dfd33f0324aa464dc3d775388d6e54e3de4f06c8d46f190d16`，16:47:13实读；实际宿主1908.727736334秒，批量均值112567.75周期。
- 固定12性能任务均值112568周期、1332.5278942505863 task/s，不能将批量均值替换它。
- 截图takeover_local/t64_batch_final_identity.png保留。原始服务器报告不修改。

## 新失败及修复范围

原主队列serial02/PID289025在竞争测试失败后自然退出，观察器300088也自行退出。竞争stage16:44:39开始，编译成功，仿真在启动DMA前报bad00002/fffffffe，即BAD_ARGUMENT。源码main_t64_contention.c错误检查metadata[3]!=5u；修为KWT_ICB32_ROWS，并加编译时必须四行检查。其他5u值（如恢复测试期望五次trap）不改。共有头文件默认值不改，正式三个构建入口均显式传ROWS4。

已增加队列prior_batch显式复用：核验原passed状态、摘要SHA和240数量，只允许调度工具与独立竞争固件改变，生产RTL、性能/恢复固件、数据、验证器必须相同。队列6项及契约3项测试通过。

本地试构建local_runs/t64_contention_rowfix01成功；错误行数负编译第一次因Zig默认cache权限AccessDenied未验证，须指定项目cache后重做。正式包必须从Git LF源码构建，不能用CRLF工作树源码哈希冒充冻结包。

## 待做

提交修复、新包仅重建竞争固件，校验三套固件和全部文件；新会话引用旧ASIC14与240，从竞争/恢复继续综合、门级14、SAIF12、时序/结构审核、功耗12、精度20。不重启serial02、不重跑成功任务。综合未开始，功耗与G64未开始。

根目录/tmp/s4_21usr_t64_20261115_1510；旧包light-light126-t64-resume-9934df8，manifest32f48cc22391667881476ba6bf6ad7e26b69c6693e19182fb8688a69ac596c68。b915包manifestc80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804。原共享盘基本满，/tmp约93GiB；下次启动前重查进程/原锁/空间，不清锁。以前对两份未运行T64输入做保留路径和字节的硬链接去重，不能原地修改这些包。无T80/旧8路删除。

VNC18874435，workspace3，FileZilla没开，转发session91027保持。当前shell空闲，无半截heredoc；Ctrl+C的正确helper键名是Control_L c，ctrl+c无效。先观察实际窗口再操作。Git上次push3c0f1aa，当前修复未提交。/tmp不是持久备份，归档工具已准备但未执行。
