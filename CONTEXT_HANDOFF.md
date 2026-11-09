# 当前工作与上下文交接

更新时间：2026-11-09，北京时间。每次准备压缩上下文前更新本文件；压缩后先重读本文件、AGENTS.md、当前计划和执行检查点。

## 当前要求与停点

用户已明确 PLEASE IMPLEMENT 新版三天计划，撤销此前暂停，开始直接16路MAC＋ICB DMA＋双缓冲；不做8路DMA。H0=2026-11-09T17:16:08+08:00，H28硬冻结=2026-11-10T21:16:08+08:00，内部H72=2026-11-12T17:16:08+08:00，官方精确截止尚未核实。

当前有效计划为 [DMA16三天计划](workspaces/arch03/IMPLEMENTATION_PLAN_DMA16_20261109.md)，老师答复记录在 [答疑依据](workspaces/arch03/QA_DMA_LOADING_20261109.md)。旧七天计划和历史证据保留。DMA16核心、搬运、仲裁、布局和正式监视器已通过本地测试；真实E203/厂商宏、新STA、门级及功耗尚待新运行。

本地分工：dma_feasibility负责新增linear16核心和核心测试；evidence_audit负责DMA16引擎/MMIO及协议测试；contest_requirements负责tile16布局和独立数值验证；主代理负责平台源接口核查、仲裁/安装、CPU固件、集成及服务器调度。各代理只改自己新增文件，不提交git；主代理统一集成。

已核对原sysmem_icb_*接线/译码，source=0xb0000000位于原O4覆盖范围；恢复原加载源响应路径，禁止新增SRAM私口。DMA源读→共享写ACK→共享读到缓存→结果写ACK全部计时。新版数据46976B，输出50688B，四段191616B；同任务预取允许，跨任务预装禁止。

## 最新实施检查点（2026-11-09约18:49）

- 以下内容覆盖下方旧暂停/17:50记录的实时状态。旧synth07已读完成，不重跑；远端EDA/锁最后实际观察仍是17:24无任务/无锁，下一次启动前重新查。
- DMA最终RTL SHA4270345c39477220831ef4fda8227dc4f3c8d6df71f66234bfc0ec63b2df9f53；ABI6b1c53a46e8f490208adbd1d4734d2aead2bbe1ebf0df93cf0e294c7eba87c90。15协议、28真实core/arb/router/shared任务709632输出通过；包括首源请求前X/W失效、无复位新任务、held请求取消排空。最终协议和datapath目录在DMA16_ENGINE_HANDOFF及主JSON。
- fabric386事务公平性/owner/反压通过；source统一为N接受、N+1最早ACK，11752请求测试通过。此前多余pending拍已删除，旧模型从未进ASIC。window3完整任务及12失败/取消、完成后非法事务拒绝通过。
- 正式source/window/monitor同名层次夹具6任务152064输出通过：pf0=274010、pf1=225770周期。夹具只用过程MMIO，没有E203，不能当ASIC吞吐。单任务VCD边界轻审计已过，起163.333317ns/止1505296.516137ns与window逐fs一致、225770周期。XSim动态路径落为dcv，且其0宽parameter不被既有严格ASIC活动审计器接受；保留两次失败，不放宽服务器审计。
- PLIC全部16原源已分配：DMA与GPIOB原线OR，共claim ID16；priority0x0c000040/enable0x0c002000 mask0x10000/threshold0x0c200000/claim0x0c200004。CLINT实际generated RTL已核对mtime0x0200bff8、mtimecmp0x02004000；irq_mapping.json记录源链和截图哈希。MEMS使用hfclk，实际WFI期间DMA仍需CPU验证。
- 新固件显式等待STATUS bit14 ready：poll目录local_runs/dma16_firmware_poll_20261109_startready_v2；IRQ目录local_runs/dma16_firmware_irq_20261109_mapping_v1。只含程序/SHIFT，0x10000后全零；IRQ真trap/WFI/PLIC和timer probe已编译未运行。1024timer ticks、1M probe cycles是初版参数待测。
- root新增install_dma16.py、dma16_soc.py、package_dma16.py及server_run dma16_soc/build/synth阶段；6集成契约测试通过，实际固定平台新安装/编译仍未执行。旧8路参考安装显式拒绝，不能误用DMA监视器；旧对照完整新加载口径尚未实现。
- batch支持冻结boot_by_shift；19单测和14case夹具通过，不属于ASIC。独立批量在build释放sharedlock后自行持同一锁，旧37不续。新1200、真实CPU连续A/B/A和错误恢复、14门级、12功耗、150MHz和新增面积均未完成。
- 新dma16_synth已完成，23项新旧离线测试通过；不改旧综合脚本。需包入UNDERGRAD_D3_SERVER_20261109.json用于同Liberty面积单位依据。仲裁/router/内联IRQ/glue不能漏计。
- 新文件准备首个实施提交/上传；代理review的IRQ映射/固件源码冻结缺口和包名变量覆盖均已修，实际打包后再核验ZIP根目录与全部哈希；固定源码与固件哈希→提交私人分支→package_dma16.py→开发板暂存→Linux FileZilla→服务器安全解包→先dma16_smoke01/layer01，再IRQ和14。独立运行说明DMA16_EXECUTION.md。
- 最近VNC窗口18874436，relay session22118；辅助工具key必须--keys Return；服务器Python必须python3，系统python是2且无pathlib。UI若命令已输入只补Return，勿重复输入。最近18:41只读平台检查；当前没有新EDA任务。工具截图在takeover_local/d2_20261109/dma16_*。
- 正式监视器在最终mailbox检查finished&&!failed及全部ACK；VCD在最终output ACK停止，不等稍晚drain证明。IRQ模式要求mail中的external/timer/WFI>0、done event且无未处理中断；程序source和irq_mapping均进入batch contract哈希。

每次压缩后仍按必读列表读取并核对，继续此实施链，不重做已完成本地测试，不将本地证据替代ASIC结果。

## DMA16实施进度（H0后，2026-11-09约17:50）

- 新计划和老师答复已落盘；用户已授权实施和恢复。所有新版功能/时序/功耗状态仍按实际分层，不沿用旧PASS。
- 原synth07已读：11:33:34.089843结束，stage passed仅表示reports ready；setup +0.0000376701ns，hold +0.00131178ns，latches0，仍待完整约束审核/新门级/功耗。17:24:18读到锁已释放、无EDA。原结果未修改、未重启。
- 固定平台O4 base=0x80000000/regionLSB31；0xb0000000源窗口合法。原e203_soc_top的sysmem为空零响应占位，恢复原已有ICB接口至仿真/门级边界，不加SRAM私口。PLIC base0x0c000000已核验，中断源号仍审查。
- tile16 14用例软件转换通过，354816输出与旧整数参考逐位一致；14布局单测通过。新目录local_runs/dma16_layout_14case_20261109_h0。
- linear16正式d3 14用例A/B/A pin_mock通过42任务/1064448输出，另旧源56任务与行为测试通过；核心无停顿pf0=156560、pf1=140480周期，仅核心性能。核心SHA6bb63bf42437617a5b73b71c22c0874528868f5ef9b4f01be5d9687dde433322。
- DMA/MMIO引擎9个协议测试通过（core stub），真实core集成正在测，不能当E203完成。DMA首版先完成整个源→shared装载，然后读缓存/计算/输出重叠；保留单笔在途。
- 原ASIC批量入口不复用旧功能TCM路径；新stdlib dma16_batch.py的15单测、14case重排和runner夹具通过，夹具复制参考不算RTL执行。
- 主代理新增arb2/router；258事务payload/owner/error等检查通过后公平性覆盖不足，核心代理正在补持续竞争激励，原失败日志保留，尚未标fabric全通过。
- 主代理下一步：完成IRQ映射、install_dma16与TB加载/计时/真实CPU固件，干净集成测试后打包上传。新代码尚未commit/上传/真实ASIC验证。
- 开发板VNC曾退出，已恢复；现窗口18874436，仅作为最近观察，操作前仍重新发现。relay exec session22118仍运行。已有助手读取保存key需reviewed escalation，不输出key。服务器操作经开发板Linux VNC，上传仍用Linux FileZilla。
- 分工独立交接见DMA16_CORE_HANDOFF.md、DMA16_ENGINE_HANDOFF.md、DMA16_LAYOUT_HANDOFF.md；主证据见handoff/team/evidence/DMA16_IMPLEMENTATION_20261109.json。

## 已完成

- 通用 X/W/b 编码、实际结果解码、数值格式及异常检查已完成。
- 600 条内部开发样本、7,200 个完整 FC1 任务、182,476,800 输出已评估。最差层 NRMSE 0.14941871%，最差任务 0.22915377%，模型样本无编码截限和输出饱和。不是官方评测集；未训练/微调模型。
- 本地 XSim pin_mock 共 25 任务、633,600 输出通过。
- 实际 E203 两组 A/B/A 共 6 任务、152,064 输出通过，包括部分装载中止、实际驱动超时及无复位恢复；此项属于平台功能 TCM 分支。
- 真实厂商 TCM 98,682 检查、262,144 字节启动映射和 11 类标准单元测试通过。
- 修正配置 `371316a/d3_full02` 的 ASIC CPU 完整 14 用例通过，354,816 输出逐项一致；14 个完整任务启动选择检查通过。当前 portcheck 的 RTL、固件、向量、测试台和平台准备与该配置逐字节一致。
- 原 UART/修正版对照通过：31,464 周期、213 次 APB 写、246 次读、600 个 TX 边沿。
- 实际完整任务窗口为 3,890,080 周期，周期 6.666666 ns；约 25.933864 ms/task、38.559622 task/s。这是功能仿真换算，尚未绑定最终时序通过结论。
- 1,276 种标准单元和两种 SRAM 的 Liberty/LEF 面积单位已交叉核对。整机 130 个大宏、8 个小宏，共 1,042 KiB。
- 设计报告草稿、数值格式、时序/面积/功耗复核及交付索引已保存。详细进度见[更新计划前检查点](workspaces/arch03/PROGRESS_BEFORE_PLAN_UPDATE_20261109.md)。

## 已尝试的路径和结果

| 路径或问题 | 结果与处理 |
|---|---|
| 早期平台功能 TCM/FPGA 分支 | 不能作为 ASIC 证据；已修正条件分支并用厂商宏、标准单元完成新的 ASIC CPU 全量测试 |
| TCM 首轮采样过早 | 旧失败保留；调整到同周期 3 ns 采样后真实组件测试通过，生产 RTL 不因该测试问题修改 |
| 工具周期舍入和报告完成标记 | 改用 6.666666 ns 严格周期；只匹配独立输出标记，避免把 Tcl 过程回显当成实际执行 |
| 启动选择路径、四个 timer CDC、UART 锁存器 | 增加完整任务模式守卫、精确首级 D 例外及无效 payload 默认值；UART 对照和新 ASIC 14 用例通过 |
| `d3_synth04` | 映射完成，锁存器 0，hold +0.00623399 ns，setup −0.740983 ns；剩余三个 LF 控制输出预算需重验，不能写成时序通过 |
| `d3_synth05` | 第一个 LF 端口的小写 o 被误写成 0；约束错误使结果不可用。DC 默认出错继续也已识别，新增显式失败即停 |
| `d3_synth06` | 第二个 LF 端口漏 `_o_`，工具退出码 1、映射前停止，验证了失败即停；旧目录保留 |
| 完整端口清单修正 | 独立提取实际网表全部 20 个顶层输出，清单哈希在本地和服务器一致；9 项定向测试通过。`d3_synth07` 已实际绑定正确三个 LF 输出 |
| 历史门级/活动 | 旧配置首层 25,344 输出通过；原 Python 活动扫描慢，保留原仿真后用完整原生扫描器独立复核 29.86 GB VCD。未抽样，仍有未知值记录需功耗解释 |
| `d3_power01` | 取得许可证并生成报告，但 PT-063 启动错误导致验收失败。LC 子进程环境、实际单位/未知跃迁/边界网络报告修正已打包，尚未实际功耗重验 |

正确 LF 端口为 `io_pads_aon_pmu_padrst_o_oval`、`io_pads_aon_pmu_vddpaden_o_oval`、`lfxoscen`。其 1 ns 最大/0 ns 最小预算参考 LF 源域，是明确接口假设；未新增整时钟域 false path，也没有外部接收器规格或物理签核结论。

## 当前冻结配置与远端状态

- 仓库：`E:/fpga_race-two/kwt1-rtl-architectures`。
- 分支：`codex/light-light126/undergrad-d1-numerics`，团队私人 GitHub 仓库。本地/此前缓存origin已核对的进度记录提交为 `fd47609107faece19235c0b04112e9c44fe6a72b`；文档提交不改变运行包源码。
- 受测源码：`5946c54263868bb701bebe515a285ffb9f238e47`。
- 包：`light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386.zip`；10,843,580 字节、402 文件；SHA256 `2d998f7dc8cadfaf230c90da499e1e7b3c110d1f86e2afeaca5723ecbb2ec4c5`。本地、开发板暂存、FileZilla 上传、服务器安全解包均已核验。
- 远端最后观察时间：**2026-11-09 11:30:53.840890**。`d3_synth07` 当时 running，驱动 139120、DC 子进程 141535，实际协作锁由该运行持有。开始时间 11:18:46.512651。
- 暂停时没有停止远端进程或关闭远端终端；它可能已经自行完成，最终结果尚未读取，不能沿用“running”作为实时判断。
- 开发板 VNC/FileZilla 已退出、上传队列为空；本机连接代理 10044、23248 已停止。窗口 ID/PID 只能作为历史信息，恢复时重新发现。

```text
运行目录：
/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386/runs/d3_synth07/asic_synth

实际协作锁：
/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock
```

远端保留的终端第 3 页为诊断页，cwd 为 SDC 包；第 4 页为运行页，cwd 为 reports 包。恢复时先观察界面，不盲用旧坐标。开发板连接辅助入口为 `F:/linux_fpga_try/ac820.ps1`；使用开发板 Linux VNC/FileZilla，不使用 Windows VNC/FileZilla，不新建未经授权的结果回传通道。

## 未完成与恢复顺序

1. 新计划已收到并获执行指示；先恢复连接，核对固定平台加载源/中断接口并读取synth07最终结果。
2. 先读取原 `d3_synth07` 状态及实际协作锁，审查最终 setup/hold、约束覆盖和结构警告，不重复启动。
3. 有效新网表需完整 14 用例门级验证，并采集同配置完整任务活动。
4. 实际运行并审核系统功耗：单位、SRAM、未知活动、映射及导线/时钟假设；通过后计算 J/task。
5. 用最终叶清单重算面积，确认官方计分归属，统一配置的精度、时序、面积、性能与功耗证据。
6. 完善最终报告和提交材料；精确截止、模板、字段及视频要求仍待确认。PR #6 与 32 位复制优化尚未测量，按新计划决定后续安排。

用户既有授权允许本计划当前及后续已核验源码/固件/测试包经开发板 Linux FileZilla 上传到 `icdesigns0.nicu.cn:18888` 的 `/IC/light-light126-undergrad-d2-20261109`，也已授权同步团队私人云端分支；用户本次IMPLEMENT指示已恢复执行。不要重新索取已授予的上传授权；只在已授权独立目录运行已核验包。

保留旧 1,200 组批量的 37 组通过和第 38 组中断，禁止自动恢复旧批次、修改原平台/历史快照、删除旧失败、自动清锁或停止其他人的作业。不同版本的最好结果不得拼成当前配置通过。

## 压缩后必读

依次核对 [AGENTS.md](AGENTS.md)、本文件、[当前DMA16计划](workspaces/arch03/IMPLEMENTATION_PLAN_DMA16_20261109.md)、[团队状态](handoff/team/STATUS.json)、[验收清单](workspaces/arch03/ACCEPTANCE_20261109.md)、[执行检查点](workspaces/arch03/EXECUTION_CHECKPOINT.json)及[服务器证据](handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json)。新计划到来后在此处更新有效计划指向，保留旧计划和历史证据。
