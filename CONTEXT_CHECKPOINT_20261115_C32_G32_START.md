# 新路线启动：T80→P80→C80→C32→G32

用户于2026-11-15提供新计划并授权开始，继续要求服务器桌面T80完全不动。新有效原文已逐字保存为workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md，SHA256为1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。

## 新旧差异及保护

- 最终配置固定16列×2行/32PE，S0分块综合→S1请求流水→S2完整编码→S3两行及缓存→S4ICG。取代T64→G64后续路线，不继续旧队列的门级/功耗，不开发G64。
- 硬面积≤1.00mm²，<0.50mm²为C32努力目标；32PE分块算术上限约2930task/s，3000仅逼近方向。
- 保留原32位ICB及平台缓冲/在途参数、共享写ACK后原总线读回、X14/W12/b32/SHIFT10、IRQ/WFI和完整输出。
- 每个硬件冻结版自己的原14例、10000随机及协议/恢复、前20条240任务、门级14、完整活动/功耗12。S0可引用相同RTL的既有T80功能证据，新分块网表须独立验证，不能继承旧网表PASS。
- 桌面/storage2/2026contest/server4/s4_21usr/Desktop/T80_Delivery_20261113及全部旧八路不写、不移、不删。所有旧计划/证据保留。

## 工作树及基线

新工作树E:/fpga_race-two/kwt1-c32-g32-20261115；新分支codex/light-light126/t80-pipeline-c32-g32-20261115，从6465f251a0a3aadf74498a59bac4a55e71c8a796派生。旧T64/T80工作树不切换或覆盖。

17:35 fetch后确认原T80分支仍575b3cbdf9f2cef92f7cf90acd3b2168ba21fdd4，计划引用在该分支正确；T64接续分支为6465f25。main有独立数据文档更新96701e7，未整分支合入。

当前T80 accel/transport、N1 linear/systolic/decoder及install_t80与受测876b883一致（git diff为空）。S0必须继续核对完整source_list、平台指纹、固件及原T80报告。

## 旧T64实际作业：先安全收尾，不恢复派发

原ROOT=/tmp/s4_21usr_t64_20261115_1510，active=ROOT/light-light126-t64-resume-3552163，manifest81f861731d29df3252c775e8bc1dcab8628b2f2f79c71fa504827c9e7d2ed763。

17:25:56暂停回执ops-3552163/user_pause_20261115_1724.json记录原暂停身份。17:38:43已重新核对/proc的PID、start_ticks、UID、完整命令、父子关系、SIGINT处理和锁owner哈希，全部与回执一致。共享盘仅1048576字节可用，/tmp约99GB可用，不能把共享盘当有空间。

17:41:17.046108已执行安全交接：只向原暂停父325056发送SIGINT后SIGCONT；子15147没有收到信号。原ProcessLedger.drain捕获中断后等待当前综合完成才抛出并释放锁，后续阶段不会派发。操作前重跑两个中断排空测试通过。服务器回执ops-3552163/new_plan_stop_after_child_20261115.json。17:49:08.289587实际只读观察父S、子R、原锁存在，综合仍在处理requantize模块；queue JSON的running只是尚未收尾的记录，不能恢复旧队列。综合完成可能将队列记为中断失败，属于用户换路线，不是硬件失败。不得清锁或重启。

T64已过ASIC14/240/竞争/恢复，数值结果保留；综合最终结果待收取。新S0不把T64结果当T80证据。

## 当前S0工作与待办

已读新原文、AGENTS、团队同步和暂停检查点，创建独立分支、保存原文；尚未新增RTL或启动新EDA。S0_T80_SOURCE_IDENTITY_20261115.json记录完整选定源码/安装器/固件来源共24文件与876b883逐字相同；这是Git源文件身份，不替代服务器平台、库和固件二进制身份。

新增partition_synth_contract.py及5项本地测试，17:52再次全部通过：分开物理分块/计费归属，未知CPU胶合仍保守计入；缓存指纹锁定源码、参数、库、约束、工具、依赖DDC，拒绝缺失/损坏/变化缓存；生成由同一T80顶层DDC提取边界环境的characterize脚本。该工具尚未服务器实测，不能称S0综合通过。详细设计见workspaces/arch03/S0_PARTITION_IMPLEMENTATION_NOTES.md。

566816a已经推送新分支。18:04已实现三块映射和顶层链接脚本、独立单锁S0入口及白名单工具覆盖式输入包克隆工具；前10项本地检查通过，包克隆检查正在补齐。未在服务器执行，新Tcl仍待实际DC兼容检查。最后17:58:25旧T64父S/子R，日志继续处理DW加法模块，/tmp约99GB、共享仅1MiB；不启动第二个EDA。

原T80综合来源与summary已定位：/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-t80-v4-9196556-delta03/runs/t80_finish02_synth/t80_synth，summary c485b3f77cd7c4f9d7911c5e2052babbc2d8c83811b94ec72c608ffed027f341，mapped.v 6a9ab02be889d4aecb55576a71c51ce68f324fc8a0897430e0dbe40a1373eff2。服务器安装DC路径/eda/synopsys/dc/dc_2022.03-SP5-5/bin/dc_shell，下一步先help能力检查再正式映射。

新包拟从/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4的833个输入复制到新私有root，manifest181bb96b719363be5350e9e968ac2b2ad29555e2f4606e362721be3c42629b9b；本地对应备份ZIP已核对身份。只追加S0新工具/文档及当前n1_process，不复制runs、不改原件。接下来完成工具测试、提交同步、准备并传输overlay；旧T64自然退出释放锁前不启动新EDA。S1/S2/S3/S4尚未开始。

VNC18874435/workspace3当前shell，FileZilla未开；板端转发91027持续。所有旧输入已结束。恢复时先读取本计划/检查点，再观察实时锁/进程/空间。尚无新阶段PASS，不能自动进入S1。
