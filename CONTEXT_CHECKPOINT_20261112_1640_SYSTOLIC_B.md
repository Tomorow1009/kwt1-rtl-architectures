# B 检查点：2026-11-12 16:40

任务 ACTIVE。直接5×16脉动B，A取消，生产RTL/固件63da6ba/v3/credits3冻结，R4保底。用户授权持续实施与同范围GitHub/服务器同步；无需逐步确认。11/13 17:00前收尾。压缩后读AGENTS、本检查点、有效B计划和STATUS，再核对真实作业。不要重跑旧批次或再次清理。

## 新完成：DRC06自己的门级14全部通过

ced包`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`下：

- `runs/systolic_b_v3_drc06_gate02/systolic_b_gate`，driver79264，**16:36:07.471433 passed**，不是原gate01。
- summary SHA **7c1a3ade96aa9a6bcb307d291b216667a7c6ff9595632e08bfb0f6d69289de99**。
- 14例×25344=**354816输出**、真实E203/IRQ/WFI；无SDF。12层周期[31339,30735,30423,30491,30079,29775,29423,29511,29419,30215,31383,33235]，extremes38337/rounding33707。
- 平均30502.333333周期，150MHz折算4917.656573task/s，与自己的ASIC14完整窗口一致；不是芯片实测。7000未达，5000还差502.333平均周期。
- 精确绑定DRC06综合b81780033ef65998c43a874b559e54da0d958524a040eff374b1e8f1a4824ced及固件11d860ca0269f962a71250e72925c730def0da79d931a79e3102c82ddaa16b91。
- 新门级工具d48来源检查验证全部相同SRAM配置副本，原gate01在仿真前失败的目录保留；不借用旧synth02门级PASS。
- 新证据`handoff/team/evidence/SYSTOLIC_B_DRC06_GATE14_20261112.json`，当前本地待提交。

## 当前唯一作业：R4 SAIF/PT交叉核对

16:37:28实际LOCK False、EDA []，确认gate02结束。随后**16:38:50唯一启动crosscheck01，PID118517**：

`runs/systolic_b_r4_crosscheck01/native_saif_r4_crosscheck`

使用c307 ops，manifest **d855f9f4b4b5108625fa00327c41f4fd300acee2d91545e113eb822245729691**；请求`operations/r4_saif_crosscheck01_request.json` SHA **bcc2cc0fe8b62f0e960cf651405fd8d6b1551040f12fd184e436db8462928346**已部署。**不要重复安装请求或执行b_c307_crosscheck_launch.txt**。未读取终态，不能称方法合格或B功耗通过。

它绑定已完成R4 replay01 summary **f7d542dd8e741c008c37c8f50385de451742a4e9125da685228056698e23d21a**，以及R4 L01原功耗summary **18190f6d4021de0ba55ae2b2be00a456f89217a6efbd0c0e3412831617f2d00c**。同窗口25344输出/34639周期、SAIF94632798B已通过。交叉核对保持原R4原SDC/设置，要求整机及主要模块差≤1%。不改变原R4结果。

下一步读state、launcher和power.log；若失败先核原因，保留目录，新会话重试，不能清锁或直接借tiny试验批准方法。只有当前作业释放真实锁后才能下一EDA。

## 已完成的当前网表评审依据

DRC06综合15:02:00.609042完成；0约束违规，setup+0.00010252ns、hold+0.00249085ns，92小宏/128复用大宏，0锁存器、无组合环。面积保守上界1.099094695900963mm²，整机4621311.195906µm²。只等价升驱动7单元，原RTL/任务约束不改。

timing02 PID62215于15:54:23.668453完成，summary **bfd0007c4846649c7f3ea018a5dbad480e10f8c406f309c3089b016d0c7da3b6**。三个TIM134网络为core_csr_clk、hfclk、AON crossing_clock，均平台时钟，声明综合扇出模型1000；check_timing无其他警告。timing01相对DDC路径错误保留，绝对路径02完成，本地入口Path.resolve修复已同步，不为一行修复重跑。

结构清单`runs/systolic_b_drc06_structure01.json` SHA **12f843804ca02d61ae5f260e30c556c1fe0cf89c2d98586ae6acbdb219ec73fd**：2222模块，13040警告端口全仅声明，244无负载驱动全部对应未用端口，无遗漏。4个LINT1均原平台debug/AON/PLIC irq0。LINT32=12048常量连接、LINT33=1186共用输入网络，保留原报告；新同网表门级14已通过。

实际mapped.sdc只有LF timer tim0..3第一级同步D的4个false-path端点，无multicycle/clock_groups/user disable_timing/SysMem假路径。106位SysMem接口全约束：max1ns/min0ns，transition0.1ns，load0.01库单位。输入接收外设规格为假设，不声称外部芯片签核。

面积当前416529叶实例清单逐项核归属；上界计入全部SoC标准单元和92加速器宏，仅排除128复用TCM/shared宏。库面积单位与几何按相同库hash复用证明，宏数按本版实际重数。新小证据`SYSTOLIC_B_DRC06_SCOPE_INVENTORY_20261112.json`本地待提交。小正裕量只适用声明SS/.99V/125°C稳定任务模式，不是物理裕量；PLL切换/JTAG活动/启动复位释放/提取寄生未签核。

## 已部署工具与云同步

- 最新云提交**219fed903ff471c29e23ee7a418725252c2ed216**（push/ls-remote一致），主要更新进度/创新/复现说明。
- 最新工具提交**52f37cc029c505102d99741c33a814f26373fb01**，独立13文件ops `operations/systolic_b_tools_52f37cc`，manifest **8fa64e620192e45ce99b4faef3bda698ae4d1405821992eae04093cc5c799435**。10条差分已全部部署核验，禁止再append。
- B新功耗将生成独立mapped.precise.sdc，保留原DC导出，实际PT断言/记录HF6.666666ns和LF66ns。报告保留历史R4原PT使用6.66667ns的序列化差异。5项工具检查通过；生产硬件未改。
- ced原709输入与manifest **39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d**未改。不能用ced旧SAIF解析器运行新功耗；ops覆盖相应工具。
- finalizer直接从ops执行时需`env PYTHONPATH=workspaces/arch03/scripts python3 ../../operations/systolic_b_tools_52f37cc/systolic_b_finalize_queue.py ...`。base模块ROOT仍指ced；cleanASIC14/own1200使用base；活动/功耗经hash请求调用52 ops。

## 最终队列尚未启动

本地`takeover_local/build_b_final_request.py`准备工具尚未调用，需传入**实际gate02 SHA**与成功crosscheck SHA后生成b_freeze_review01.json/b_finalize01_request.json。不能填假hash、不能凭已经准备文件声称冻结批准或1200通过。

当前gate与声明范围时序/面积依据已具备；完成交叉核对后重新核回执，将独立冻结评审绑定ASIC/DRC06/gate02/sequence/contention五个实际来源。最终队列前preflight再次校验源码/固件身份、全部摘要/输入/原队列终态与数据清单。

队列应执行：新干净ASIC14 → B自己的100×12/30412800 → 已合格方法下B activity12 → 每层PT power12 → 报告请求。使用saif_qualification跳过已完成R4重放。最后独立精度/报告复核和R4/B比较。自己的1200、B活动和系统功耗目前**全部未运行**。

完整SAIF重放R4单层实测VCS约25分钟，单层90.25MiB；新B仍以自己首层实测估宿主时间与20%余量，不能按芯片加速比估。门级本次约33分钟。共享盘最后15:04约376.27GiB，后续应重新检查，不把旧值当实时。

## 保留的历史与禁止重复事项

- B ASIC14/354816真实IRQ通过，恢复10阶段76032输出、两例竞争均通过；原validation03完整终态SHA d0a35dfd75df95199ec9a18a3cce323ea379f4620bfcbf9789a83f650c7c6b3。
- R4最终1200/30412800和原门级活动/功耗全部保留，不重跑1200。R4：4333.256task/s、71.8126mW、16.5724µJ，布局前、未知影响未完全审核，system_power_verified=false。
- 两次已授权清理共279.506GiB仅旧MMIO8 L03–L12原始VCD，回执与其它小证据保留。不得重删或删除R4/B。
- 原synth01磁盘满；DRC03库身份错误；04原transition/multiport；05上游transition/cap；06才清零。gate01来源副本工具误拒绝、timing01相对路径失败及SAIF早期单位/ANSI/属性失败均保留。不得原地重试。
- FTP421且用户确认无人使用，FZ关闭；不反复要求队友断线。已有授权VNC小工具部署在独立目录，不新增隐藏远程通道。

## 当前桌面

开发板VNC18874435，工作区3/ced包shell；**不操作工作区4**。FileZilla关闭。最新crosscheck启动Return已执行，截图确认PID118517，本地exec59144已收尾。无待Return、无待收本地session。恢复先观察/核窗口；下一动作只能查询原crosscheck，不再执行launch。
