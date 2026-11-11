# 2026-11-11 14:35：R4交付已完成，R1综合通过初筛，原8路功耗继续

压缩后先读AGENTS、`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点、STATUS/EXECUTION_CHECKPOINT的`icb32_c64_execution`。用户要求能继续就继续，不逐步等确认。历史细节在[13:25检查点及所有增量](CONTEXT_CHECKPOINT_20261111_1325_ICB32.md)。本轮不再开发新RTL；已有作业不重复。

## 一、R4主候选已经完成的工作

- 真ASIC RTL/E203 1200任务、30412800输出、零失败；整批平均34618.743333周期。ASIC14、真实CPU竞争/恢复、同网表gate14/12完整活动、干净ASIC14及计数全部通过。
- 最终锁内报告13:19:23.854688完成，全部1200回执/原输出独立重审通过。四个输出文件与receipt哈希核验，原wrapper121468/child121471结束并正常释放自锁。**不再运行R4报告、1200、上传或三条prepare/history/launch。**
- 同配置12层平均34616周期、150MHz折算4333.2562977task/s；整机加权71.8126319mW、平均16.5724388µJ/task。项目面积保守上界0.9265616712mm²，声明稳定任务模式综合时序及面积上界独立接受。功耗仍为布局前估算且system_power_verified=false；官方600和物理签核未验。没有达到5000目标。
- 最终报告：964包`runs/icb32_r4_final_report01`。report SHA `e4a2514b7f47440a7ed0049aa685bdc36fc17180d4b9e3e256d5cd8998fa6958`；receipt SHA `2e54dc4378b1d59ee13ba236eb4b3093daa44d2a8a769830201fa295d94d004d`。证据`ICB32_FINAL_EXPORT_20261111.json`含CSV/中文报告哈希及全部身份，不必重新转录。
- 团队交付准备包已经实际生成并读回核验：`local_runs/icb32-r4-delivery-preparation-20261111_132750-928559fea8ab.zip`，11519662B、117文件，SHA `dcbd8ef42ff293d44f92654772f7b394fcbce52528b51002eef72ee813abd289`。原964源码ZIP的636输入重新核验；不重编译硬件。此包含最新说明/小证据及原源码包，服务器大产物为位置/哈希引用，**不是已向赛事提交的完整附件**。证据`ICB32_DELIVERY_PACKAGE_20261111.json`。清晰入口`workspaces/arch03/ICB32_DELIVERY_20261111.md`。

## 二、R1相同搬运对照的新实际结果

R1包：`light-light126-icb32-r1-20261111_012941-f95e940862ca`。13:19再次核验607文件，manifest SHA `109e3314f54d0baed2584c15cb3449957057ac99c6b526d673bd39d9b62a013f`。正式IRQ固件SHA `e29565e6c823d5115388c556159c6ff65d3ffe24b946198cf1068e13751e2bc9`，rows1/prefetch1。全部RTL与R4相同，仅行并行参数/固件不同。

- 独立session `icb32_r1_compare01`，ASIC PID187418已13:33:02.951083正常完成。14例354816输出、ASIC/E203、IRQ/WFI通过；12层均值116280周期，全部14周期与本地一致。摘要SHA `1980d8eb8ead959d0a3ec099f0fb3d4461924210abf6a785b60a85fac67286f6`，已与stage核对。
- R1综合PID203950、DC child212679已**14:15:03.555558完成**，协作锁已释放。14:17:23.681320最终摘要与stage核对。SHA `8622be54321234d81764149989fc42e68ab6ca5b81be18c32abbb5f81e723d0a`。
- 最终综合实际：6.666666ns/LF66ns，setup+0.0000495911ns、hold+0.000432789ns；128大宏+96小宏=224，0锁存器、无组合环。known_added0.4580073527998128mm²，保守预算0.6186546479997178mm²，整机叶面积4140871.147976652µm²。属于数值初筛，R1自己的完整时序审阅/门级/功耗尚未完成，不继承R4审定。证据`ICB32_R1_SERVER_20261111.json`。
- 创新说明已补实际CPU链225770→116280→34616周期；数据通路综合变化1.941606倍，同通路行并行3.359140倍，总体6.522128倍。R1功耗不从周期比例推算。

## 三、R1门级尚未启动：真实磁盘约束

13:37可用135.405GiB，R4现有12VCD共139.178GiB、最大12.333GiB，因此决定先测R1一层。14:20尝试`takeover_local/icb32_r1_gatepilot_launch.txt`，**启动前assert拦下，未创建session、log或进程**。14:22:00.671183确认共享锁不存在，session/log不存在，free仅37.0048GiB，低于50GiB预留条件。不是R1门级功能失败，不能写成“gate已运行”。

14:27:47.270745 free36.7197GiB；检查R1综合最大的普通文件仅约76.8MB（mapped_probe_inventory）、57.1MB（area_inventory）、31.1MB（leaf_area），未把磁盘下降原因归给未观察的其他作业。14:32可用32.3037GiB。**不降低门槛盲启新波形，不删除/移动历史证据。** 如果空间恢复或用户提供其他存储，先重新评估预算、确认共享锁空闲，再决定R1单层试测；当前先继续利用已有波形做原8路功耗。

## 四、当前唯一实际作业：原8路L01完整窗口功耗

运行包ecf3：`light-light126-mmio-timing-dma16-20261110_111311-ecf3cd4afb3c`。14:27重新核验**683文件**，manifest SHA `1ad974f4f5b13aad37bc2e145d792aa2554d5ae65c73b3b7386626a2aaca01fe`，源提交`ecf3cd4afb3c96b9580687b5ab42db60e0372292`。

已有gate无需重跑：`runs/mmio8_source_gate_full01/mmio8_gate`，摘要SHA `06e388e1b744494fc00f224a43caf8de2ebf7e764eb1b655541ce7288a408533`；14例354816输出/12活动均通过，每任务3843121周期、无SDF。新功耗工具直接读取这些波形，不另生VCD。不要把旧单层gate的19.939132mW直接拼入这个全14gate报告。

**`mmio8_fullpower_l01_launch.txt`已经执行成功，不可再启动。** 新session `mmio8_fullpower_l01_v1`，stage `mmio8_power`。14:32:29.085086实际state/lock PID **293690**，started **14:30:05.733222**，running/errorNone、power.log13352B、free32.3037109375GiB；目录在ecf3包下`runs/mmio8_fullpower_l01_v1/mmio8_power`。以state/lock读取PID为准。启动前20GiB空间检查通过，目标目录独立，无覆盖。

后续：继续观察这一原作业；完成后读取实际summary与stage SHA，使用该包`mmio8_power_numbers.py`的真实接口提取数值、确认单位/138宏/完整窗口，再按磁盘与协作锁条件串行L02–L12。当前只启动L01，**没有后继自动队列，也没有L02任务**。不套用R4的224宏/IRQ或ICB32功耗解析器。先读工具接口再调用，不凭旧首层值填新结果。所有12层齐全前不输出完整均值。

## 五、桌面、恢复、云端及等待信息

服务器包前缀：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。共享锁：Desktop/IC/.arch02_team_lock。VNC第三终端shell，cwd仍964包（`light-light126-icb32-r4-20261111_043048-96443c284a1c`），不是ecf3；各查询/启动明确指定包路径。窗口20971587/800×450；最后命令`takeover_local/mmio8_fullpower_status.txt`已执行并返回shell，截图`mmio8_fullpower_l01_live.png`。FileZilla关闭，无本机exec遗留，无CUA会话。

板端helper `F:/linux_fpga_try/ac820.ps1`；恢复先windows确认。type每次≤1000字符、成功后Return，再等5秒截图。若截图仍是命令在执行，等刷新，**不能重复Return**。14:27只读683文件核验曾多等约10秒，最后正常通过。不要使用Up历史重放或开启隐藏回传渠道。

最新独立确认云端为`693341c949f25dd39c7c96b8be7bb6ec9f232cf6`。之后的检查点、R1最终综合/磁盘及原8路启动记录、创新对照文档需提交同步。既有同范围私仓同步授权有效，分支仍`codex/light-light126/undergrad-d1-numerics`；源码/小证据，不包含库、凭据、聊天原文或大产物。

两个异步信息问题待用户回复：①正式提交入口、附件大小/格式、队名/署名；②是否有团队附加存储或空间协调方式。都不是暂停/权限确认，不阻塞已有波形功耗工作，不重复询问。用户截止11月13日晚上、内部交付准备11月12日17:16不变。当前R4已经有交付退路；保持真实未验项，继续能推进的工作。
