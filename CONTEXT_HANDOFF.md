# 当前工作与上下文交接

更新时间：2026-11-09，北京时间。每次准备压缩上下文前更新本文件；压缩后先重读本文件、AGENTS.md、当前计划和执行检查点。

## 当前要求与停点

**最新：用户已明确要求“同步到云端一下，然后继续”，并确认开发板重新上电。当前暂停已解除。** 先保存并推送暂停期间的小型证据与交接记录，再恢复现有连接工具，重查两项验证原始摘要和协作锁后继续新综合。暂停前两个远端任务均已自然完成，但22:36:25的FREE记录不是当前状态；恢复时必须重新核对。暂停经过保留在下方历史检查点。

用户已明确 PLEASE IMPLEMENT 新版三天计划，撤销此前暂停，开始直接16路MAC＋ICB DMA＋双缓冲；不做8路DMA。H0=2026-11-09T17:16:08+08:00，H28硬冻结=2026-11-10T21:16:08+08:00，内部H72=2026-11-12T17:16:08+08:00，官方精确截止尚未核实。

最新用户补充：提交截止为**2026-11-13晚上**，具体时刻/入口未确认，来源是用户直接答复。内部冻结和72小时交付节点保持不变，不能因截止晚一天就推迟1200回归。

**FileZilla已获用户明确恢复（2026-11-09约21:18）：用户说“你可以用filezilla了”。** 此前为队友上传而暂停的限制解除。5bdf88b后续包已板端SHA核验但未上传；21:39发现取消组合反馈与gate探测问题，保留该包并由修正版新包替代。仍用开发板Linux FileZilla到已授权独立服务器目录；首包已完整上传，不重传。首包综合已结束但有TIM-209，不能据此验收时序。

当前有效计划为 [DMA16三天计划](workspaces/arch03/IMPLEMENTATION_PLAN_DMA16_20261109.md)，老师答复记录在 [答疑依据](workspaces/arch03/QA_DMA_LOADING_20261109.md)。旧七天计划和历史证据保留。DMA16核心、搬运、仲裁、布局和正式监视器已通过本地测试；真实E203/厂商宏、新STA、门级及功耗尚待新运行。

本地分工：dma_feasibility负责新增linear16核心和核心测试；evidence_audit负责DMA16引擎/MMIO及协议测试；contest_requirements负责tile16布局和独立数值验证；主代理负责平台源接口核查、仲裁/安装、CPU固件、集成及服务器调度。各代理只改自己新增文件，不提交git；主代理统一集成。

已核对原sysmem_icb_*接线/译码，source=0xb0000000位于原O4覆盖范围；恢复原加载源响应路径，禁止新增SRAM私口。DMA源读→共享写ACK→共享读到缓存→结果写ACK全部计时。新版数据46976B，输出50688B，四段191616B；同任务预取允许，跨任务预装禁止。

## 最新实施检查点（2026-11-09约18:49）

### 用户恢复与云端同步（本节优先于下方暂停记录）

- 已重新读取有效三天计划、AGENTS、交接及JSON检查点。用户明确恢复开发板和工程操作，并先要求云端同步；既有上传范围与FileZilla单连接方案继续有效。
- 本次待同步仅7份证据/Markdown文档，不含凭据、厂商库或大型运行产物；受测生产RTL仍是fcd445f，不为文档提交重跑已完成14例。两摘要SHA转录尚需服务器assert，保留未复核标记。
- 云端同步后重建本机VNC中继与板端查看器；不复用旧窗口ID或已停止PID，不清协作锁，不重跑旧1200的37组。新综合仍待实际状态检查后启动。

### 22:40用户暂停交接（最高优先级）

- 生产受测提交仍为`fcd445fb212a81469c900c6aa1cbb544daad08a5`，源码已push。其修复包已三端核验/安全解包/624输入检查，不重传。后续本地只有证据和交接文档修改，尚未再次提交/push；未开始报告生成器开发，不要误记为已实现。
- `dma16_fix_full01`真实ASIC/E203 IRQ **14例通过，354816输出**。driver119217，started22:24:11.597528，finished22:27:06.519870；各任务225770周期，12层饱和0、extremes6336、rounding4554。新bus_metrics已随实际任务解析通过，阶段延迟/竞争具体数值尚未人工收回。summary完整SHA以服务器原文件为准，截图转录候选`1b7e03944fcab5f17eefdd71bb5a6a739180e2718e8a77ddf9a0148704ec8514`尚未做远端assert复核。
- 暂停请求到来前已启动`dma16_fix_sequence01`，stage dma16_sequence，cases layer_01/rounding。最后检查实际 **passed**，driver141621，started22:32:12.284209，finished22:34:32.292395；10阶段真实CPU拒绝/取消/原驱动timeout/无复位A/B/A由runner验收。完整summary逐阶段数据与hash尚待恢复后细读。截图转录候选SHA`44e8fb569104d9aed867e110e434929b04e9508439518e84d6cbc8108dd61ab1`尚未远端assert复核。原始证据图`takeover_local/d2_20261109/dma16_pause3_remote_status.png`（位于工作区根目录E:/fpga_race-two下）。
- 最后远端观察22:36:25.050096：上述两任务自然结束，共享锁FREE；未停止、清锁或重跑任何远端作业。新综合 **未启动**，没有自动后续队列。新RTL严格STA/面积、14门级、12功耗、最终1200真实ASIC/30412800输出、同加载源8路对照及最终报告仍未验收。
- 板端两个客户端已正常Alt+F4关闭，随后窗口清单无Vncviewer/Filezilla。FileZilla上传成功33秒，之前已Ctrl+D断开，活动队列为空，历史失败与成功队列保留。单连接站点`IC-single-connection`/AskPassword/max_connections=1是有效恢复路径，避免QuickConnect额外传输连接触发421。
- 本机已核验并停止：36448=`ftp_proxy.py`、32568=`board_link.py relay`。没有本地XSim/编译回归运行，没有活动子代理。旧vnc-relay.pid文件23160已过期，不可凭此PID杀进程；恢复时重新发现/核验身份。没有关闭远端Linux桌面。
- 恢复顺序：重新接板并启动现有连接工具 → 只读确认两PASS及SHA/metrics/seq详情 → 检查真实共享锁 → 新session综合fcd445f，先检查TIM-209是否消失及所有约束/禁用弧 → 同网表gate14与12活动功耗 → 冻结真实ASIC1200。不得沿用有loop的synth01网表，旧37批量不续跑，旧5bdf候选包不上传。
- H0/H28/H64/H72和11月13日晚截止原记录保留，暂停没有擅自改排期；恢复时按实际剩余时间复核。用户未要求本次暂停时新云端推送，当前证据已保存本地Markdown/JSON。

### 22:24上传完成及新ASIC启动（最新）

- 22:25已读实际launcher：`dma16_fix_full01` driver **119217**，launcher22:24:11.127045。FileZilla显示上传成功，传输33秒、成功队列1、历史失败1、活动队列空；已正常Ctrl+D断开并最小化，释放FTP名额。服务器回归状态正在读取，不重启。
- 修复包fcd445f已完整上传到比赛服务器。22:18:55.519353服务器实测16429946字节、SHA`c58499378295ba493ce7bdaff18dcd62b49fe9537252eb351376ef4b358fd7d0`；既有unpack.py全部路径/hash检查后安全解包。22:22:14.983538再次`inputs()`核对624文件、完整提交号正确、真实共享锁False、本账号EDA列表空。
- FTP故障路径已厘清：普通QuickConnect能列目录，但传输尝试额外连接时421，新包22:09仍不存在。用户明确队友已断开。新建Linux FileZilla站点`IC-single-connection`，沿用原host/port/account，登录模式“询问密码”、传输设置限制并发连接=1，选择断开旧连接并在当前标签连接。随后单连接上传成功，未绕过限制、未开并行账号、未保存新密码。旧失败队列保留；当前须读完成队列后正常断开FTP释放名额。
- 已向新包请求启动`dma16_fix_full01`，stage dma16_soc、firmware_irq、默认完整14例。launcher已发出，PID/状态正在读取；禁止重复启动。目录为新包/runs/dma16_fix_full01/dma16_soc，driver日志同runs/dma16_fix_full01.driver.log。完成后先读summary/全部输出/metrics，再串行CPU sequence和新综合。
- 最终数据入口清单服务器22:05:03.485514实测100样本/1200层，固定SHA匹配；仅manifest预检，逐层文件由新batch再次核验。旧37组没有启动。新版真实CPU错误恢复、新综合严格STA/面积、14门级、12功耗、最终1200仍未验收。

### 22:03修正版打包停点（最新）

- 修复提交`fcd445fb212a81469c900c6aa1cbb544daad08a5`已push私人分支。生产RTL唯一行为变更是取消译码去掉多余access_error条件；本地15协议/28数据通路/monitor+metrics/A/B/A复验通过，见下节回执。综合及gate入口均拒绝原始TIM-209；gate probe严格核对直接模块边界、保留DC wildcard内部引脚计数；power新增已安装PT手册确认的verbose时钟/disabled-arc报告。
- 新包`light-light126-dma16-loopfix-dma16-20261109_215719-fcd445fb212a.zip`，16429946字节、624文件，SHA`c58499378295ba493ce7bdaff18dcd62b49fe9537252eb351376ef4b358fd7d0`。干净路径CRC/所有路径/逐文件hash/四固件/109tests通过；audit=`local_runs/dma16_loopfix_clean_audit_20261109_2200/receipt.json`，SHA`236d079907a542defb2658e5ccaed7e2b8883b2e21661124f1b29f4c709785e3`。新包尚未执行ASIC。
- 已板端暂存并自动SHA核验：`/home/root/undergrad-dma16-loopfix-20261109/<同名ZIP>`；GUI为`/home/board/undergrad-dma16-loopfix-20261109/`。旧5bdf后续包保留但不上传。当前FileZilla窗口20972102，已选新目录，队列空，22:01重连仍421用户过多；不绕行或开并发连接。VNC18874436当前被FTP遮挡，需要FTP Alt_L F9后查看，操作前重新发现窗口。
- 新包上传成功后：服务器校验ZIP摘要、安全解包、624输入 → 新session实际ASIC14/IRQ/metrics → 真实CPU10阶段恢复 → 新综合。不要重启原synth01，也不能复用其网表验收fcd445f。原服务器锁最后21:46观察False，下一次启动必须刷新。
- 最终100样本数据已查交接：服务器`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。新batch会逐项核验并重排；旧37组不续跑。最终1200、新14门级、12功耗、严格时序和系统功耗均仍待完成。
- 本轮辅助错误保留说明：记录脚本一次因Python3.8 Path.write_text不支持newline参数而未写文件，已改open(newline)成功保存；第一次109tests中的负裕量合成夹具缺少新loop-check头，补齐夹具后通过，未放宽生产检查。WindowsCIM只读进程查询被系统拒绝，改用Get-Process/包回执确认打包完成，未中断进程。

### 21:39压缩恢复与综合审查（优先于下方历史）

- 21:52修复后本地复验：15协议通过`dma16_protocol_20261109_214621_159607`；14×pf0/pf1共28真实数据通路任务709632输出通过`dma16_datapath_20261109_214621_861576`；正式monitor+metrics两任务50688输出通过`dma16_monitor_fixture_20261109_214720_530015`，完整周期pf0=274010/pf1=225770；10阶段A/B/A及3负测通过`dma16_sequence_fixture_20261109_214721_177343`（NO_CPU）。109工具测试通过，补gate拒绝旧回路报告后36相关测试再通过。新真实ASIC/综合/门级仍未运行。
- synth01 summary SHA已于21:50:57.351498通过服务器assert精确核验：`d60e386e8d6498576da5e21c369425513d420e4b1b19a393bc41d85c6e72be20`。旧网表已知新增面积0.273783044812mm²，保守预算0.434674847212mm²；这些只是旧网表归属核算，不能免除新RTL重综合。21:46实际锁False。
- 已重读有效计划、AGENTS、STATUS和执行检查点。用户21:18明确允许FileZilla；21:24/21:30同客户端重连仍421连接人数过多，无新传输。5bdf88b后续包已板端SHA核验，但尚未上传；发现以下问题后改为保留并由修正版新包替代，不能继续上传此候选。
- `dma16_synth01`已于21:18:35.199596结束，driver7612。报告收集成功，但check_timing发现组合回路自动切断时序弧，严格STA仍不合格。原始setup +0.0000104904ns、hold +0.00150293ns、整机面积3956891.346900um²、130大宏/32小宏、latches0；这些不能作为严格时序通过。summary SHA待精确核验，不凭截图猜写。
- RTL已定位`access_error → cancel_request → blocked → access_error`结构反馈：CTRL=2取消本来无条件合法，取消译码却重复依赖包含debug LOAD/OUTPUT检查的access_error。准备仅去掉cancel_request的该依赖，保留地址/对齐/full-write/data检查及排空语义。此刻尚未修改RTL；修改后必须重跑本地协议/数据通路、真实ASIC14及新综合，原首包14例仅为历史数值证据。
- 门级探测适配发现实际DC通配`*/u_arch03_accel/dma_*`返回386项、`core/*`返回211316项，包含子层级内部cell pin；现有gate parser误要求整个DMA集合等于106个模块边界pin。修正为按直接父层级精确核对边界pin，并保留内部条目数量及原始哈希；五模块全部端口/方向/位宽验证仍必须严格，不放宽缺失端口。
- 旧power告警数已定位：power.log773个PSW-208、activity_coverage_before.rpt773个PSW-208、timing_check.rpt1个PTE-003，共1547。189个无时钟pin尚缺对象清单，不能假设全部无关；旧0.0200384986W仍非正式系统功耗结论。
- 当前VNC只读命令已发出，待截图读取具体loop警告、面积归属；不得盲目重复。新EDA未启动，操作前重新检查真实共享锁。禁止用false path隐藏组合反馈、用旧网表验证新RTL或覆盖原运行。

### 21:09实施检查点（优先于下方历史记录）

- 首包同IRQ固件 `dma16_full01` **完整14例通过**，354816输出。12层零饱和，extremes6336、rounding4554；全部完整首源至末ACK为225770周期。started20:51:18.258165，finished20:54:07.550197，driver316389。summary SHA `899da0be2f54ef99d5b93c641d932f0a16a5f6b36770bc91fb2fea32d082c3a5`；IRQ首层SHA `9ab83f86e125841b47f35ea64a6fbda2569a3d22f841e56c256bec6a4a072936`。两个转录摘要已21:05:32.213658通过服务器assert与原state交叉验证。
- 14例实际仿真宿主耗时min2.668223730896938s、mean3.097152099462359s、max3.3244687309488654s、sum43.36012939247303s；compile_receipt55.1665074571035802s。按平均仿真×1200×1.2约1.24h只含仿真，不能当整个最终批量；新batch含准备/重核实际计时，最终仍按首批实际总耗时更新。旧28.8h估算不再适用。
- 真实IRQ首层及14例证明当前实际PLIC/WFI/定时唤醒可执行，但仍不能声明节能；需要新门级功耗。累计额外poll1+IRQ1+14为16次实际ASIC任务，最终100样本1200另跑，不拿这些替代。
- 新 `dma16_synth01` 已启动，driver **7612**（不要误抄7012）、started **20:59:17.415251**，child11305实际dma16_synth.log。21:05:32最后观察仍running，library/link已进展到综合。首包路径/runs/dma16_synth01/dma16_synth；禁止重启或清锁，等待现有任务结果。新严格STA、计分面积、门级、功耗尚未完成。
- 旧power07 SHA `2368034a7fa03fb3124403758a86ecbd1b65d1448cc9d593fe36fd96e5959187` 已按4×16组抄回。verbose动态/泄漏为W，实际总原始值0.0200384986W；只适用旧BEGIN窗口，不能乘新225770周期。实际X设置0.5/false，112361nets精确映射。power.log可见773个PSW-208，工具总1547warnings差异需检查重定向报告。POWER_REVIEW已记录，正式system_power_verified仍false。
- 新证据/交接/POWER_REVIEW修改待小型记录提交；后续工具包5bdf88b已完整本地核验并云端保存，尚未板端或服务器上传。**FileZilla保持用户暂停，必须等明确恢复。** 后续sequence/MMIO8/metrics/gate/power服务器入口须新包，不能手工把新脚本粘入旧服务器包绕过上传暂停。

### 20:54实施补充（历史）

- 真实IRQ首层dma16_irq01已通过：driver305472，started20:44:53.351114，finished20:46:53.150876。25344输出、零饱和；首源cycle11413/末ACK237183/225770周期，CPU236980；external=1、timer=23、WFI=23、events=1、unhandled=0。host仿真3.0708447720389813秒。原始图dma16_irq01_progress1.png、dma16_full01_started.png；summary SHA需精确分组读取，不猜抄。
- 首包同IRQ固件完整14例已新启动dma16_full01，driver316389，launcher20:51:17.712172；最后观察20:52:18已启动，结果未读。不要重启；完成后检查全部354816输出/饱和/IRQ及周期，再串行启动首包dma16_synth01。
- 旧power verbose已实际明确Dynamic Power Units=1 W、Leakage Power Units=1 W。尚未完成告警、未知值、各宏及活动覆盖审核，system_power_verified仍false。当前只读诊断命令在取精简warnings/settings/source映射头与分组SHA。新14仿真可同时只读旧报告，但不能同时启动另一EDA。

### 20:45实施检查点（历史）

- 后续源码/小型证据已提交并push私人分支：`5bdf88bf7d71439f585c68eaf6d9c6ce18bb7264`；生产RTL、原source/window/monitor、installer和synth保持首包字节。新增被动metrics只在仿真接入。现有新证据JSON修改尚未再次提交。
- 后续完整包已在本地生成：`light-light126-dma16-followon-dma16-20261109_203856-5bdf88bf7d71.zip`，16426075字节、624项manifest输入，SHA `ec1308c0ae5bd2cc4e1ab3d7c628ee5ed0fa11c05a25625815eb7f76ae51ce95`。未传开发板/服务器。独立干净解包CRC/唯一根/全部路径与624hash、4套FW、93tests通过；audit在local_runs/dma16_followon_clean_audit_20261109_2040/receipt.json，SHA7df385e57e7a8e1b700e6af9ef2a4b0a109eb988beea41756c2f5e7a97cca4a1。FileZilla仍用户暂停，禁止自动恢复。
- 第一次后续打包被严格FW源码hash拒绝：新start_dma16_sequence.S工作区CRLF而Git为LF。失败目录保留，未弱化哈希检查。仅规范该文件到Git原始LF字节，代码无diff；刷新其索引后重建sequence **v6**，manifest `fd58521b9763f6d332929a8cd44cb0196d15988c649f0b65905cd77045865cef`，ELF/boot与v5完全相同。后续包包含v6，v4/v5不可用于当前包的源码身份。
- 旧d3_power07_h0阶段最终passed，结束20:39:00.549312，20:42:34.154052观察锁FREE。PT实际链接/读完整VCD/update_power/全部报告完成，没有Error行，原PT-063未出现。工具报告1547warnings，逐类核对未完成；第一次正则汇总转义错误返回空，不能当无警告。实际units为时间1e-9s/电压1V/电流0.001A/电容1e-12F；功耗报告数值和W单位仍要由verbose核对。system_power_verified仍false，不能把reports ready当正式功耗验收。
- 已请求在首包独立session `dma16_irq01` 执行dma16_soc layer_01、firmware_irq；紧接上一步实际FREE检查，启动脚本也检查lock及session不存在。正在读取实际PID/状态；不得重复启动。接下来IRQ通过后同FW跑14，再启动首包dma16_synth；后续新门级/sequence/MMIO8/metrics服务器运行等待FTP恢复后上传已核验新包。

### 20:34实施检查点（历史）

- dma16_smoke01实际通过：layer_01、25344输出、零饱和、首源cycle993/末ACK226763/225770周期、CPU226351；仿真宿主9.16798612099734秒。结束20:11:24.332854，最后读20:21:54.780747。summary SHA4b32b136f7a5f368d2a2f3f29714e2bc2cd8b05d0c7eea420dea49ab8c9a207c。首包2bd6b0f polling范围；IRQ/14/新PPA未过，不能声明最终500task/s或全新版已验收。
- 原锁自然释放后启动旧修复8路功耗d3_power07_h0，driver **266936**（先前误抄206936已改JSON），实际started20:23:42.769200，PT child267785。20:31日志实际LC/PT链接成功并在读完整31.25GB VCD，暂未出现早期PT-063；最终结果未读。run为portcheck包/runs/d3_power07_h0/asic_power。不得重启/清锁；它完成后按原首包串行IRQ首层、14例，再新DMA综合。
- 被动metrics已接dma16_soc/dma16_gate；在TB生成include，绑定实际accel/arb端口，修改后平台TB hash入manifest；门级必须实际probe。生产RTL/installer/source_list不改，metrics不综合。逐例摘要解析完整47904事务/191616B，原window逐周期交叉核对；batch_contract要求完整metrics块，batch每次核对/恢复都重新解析，不只看END标记。ASIC活动改用dma16_activity严格SysMem/新模块审计。
- 本地真实数据通路+原正式monitor+metrics，pf0/pf1两任务50688输出通过：local_runs/dma16_monitor_fixture_20261109_202649_158872，summary SHA8ac129560fe5c1fb86250318921677e2dc143228040c4919ad364f34251c5b65。最终脚本变更后pf1复核local_runs/dma16_monitor_fixture_20261109_203109_390417，SHAf20c1e8cef4e1ca839ae8c5903f908e672fdc03c805cb2c2e29c89ddffc48b22。两者都是NO_CPU；protocol独立oracle7模式仍保留。相关工具93tests PASS，git diff --check通过。
- batch解析增加完整metrics后，sequence依赖身份重建到 **v5**，manifest933ba35729318c892ebc5e230c1ff1647c51d913649515fde0f1745dfb86b680；与v4 ELF/boot逐字节相同，ELF5f751362ad33a01f0b4237c84ef36b809708e23f6913741451c19eb0a80b9acd。四套FW再验证通过。后续包选择v5，不能误用v4旧依赖manifest。
- 实施报告/清单已补真实ASIC首层与剩余缺口。后续约57项新工具/文档/测试尚未提交；准备独立commit和本地包，**FileZilla继续暂停，不能上传或重连，等待用户明确可以传**。上次窗口核对20:18没有FileZilla。

### 20:19压缩恢复补充（历史）

- 已重新读取AGENTS、有效DMA16三天计划、STATUS、执行检查点及各工作线交接。FileZilla继续用户暂停；20:18通过开发板窗口清单重新核对，只有VNC等桌面窗口、没有FileZilla。未重新连接、未上传。等待用户明确允许恢复；本地开发与已有服务器任务继续。
- 旧修复8路 `d3_gate07_h0` 已完成，最后观察20:07:32.641508为passed、锁释放，结束19:55:48.511351；summary SHA256 `4e735f46f27f643c820f59b386e1e4e04eca5f02b0719a50330a2a40a6e82f8e`。首层25344输出通过，旧BEGIN窗口3890080周期；完整VCD31246581717字节原生扫描通过scope/window，unknown记录34900278、active记录5759095124。完整VCD SHA尚未精确抄回，不猜测；该结果不能证明DMA16或新加载口径。
- 首包的真实ASIC `dma16_smoke01` 已在20:09:16.557734启动，driver244469，stage dma16_soc，layer_01，默认polling固件。最后观察20:11:09为running、未读最终结果。运行目录为首包/runs/dma16_smoke01/dma16_soc，日志首包/runs/dma16_smoke01.driver.log。不能重启或清其锁；下一步只读检查状态。前次只读helper会话56013已消失，需观察屏幕，不盲目重输旧命令。
- 新sequence完整10阶段/3任务76032输出及3负测本地通过：local_runs/dma16_sequence_fixture_20261109_200001_072693。它是过程MMIO、NO_CPU；真实E203 trap/mret/timeout仍未验证。runner12项测试及未修改夹具日志交叉核验通过，整体ASIC parser明确拒绝NO_CPU。交叉回执local_runs/dma16_sequence_parser_crosscheck_20261109_v1/receipt.json。v4固件manifest 2d921e2563d7dd70b51d7d29f36b802e208a18445b3c05df2c6a086f6203ff1b。生成TB已补ASIC clock guard需要的四个a3别名。
- 新被动总线统计模块/解析器已完成，7 RTL模式及5解析测试通过：local_runs/dma16_bus_metrics_20261109_200900_766574/summary.json，SHA daff51a565bf6663f1f1348344e926355cbf84bcd034fdc1be3026d9d1482812。独立事件oracle检查47904事务/191616B、直方图和竞争区间；仅协议夹具，无CPU/MAC。下一步将其加入ASIC/gate仿真observer，使用实际端口binding及原window交叉检查；不得加入综合生产RTL。
- 新server_run已接mmio8_soc/dma16_gate/dma16_power/dma16_sequence；package支持MMIO8和sequence独立固件；poll、IRQ、MMIO8、sequence四套源码/ELF/镜像均验证。dma16_batch已记录真实宿主时间及剩余量1.2余量估算（不拿芯片周期推算仿真速度），20测试通过；sequence因依赖batch哈希重建到v4，旧版本保留。
- 中文实施报告、验收清单、交付索引已更新，但新门级、功耗、序列、MMIO8、metrics及batch改动尚未另提交/打包。首包2bd6b0f不可变；FTP暂停期间先本地准备后续包。仍缺新ASIC14、IRQ/WFI、CPU恢复、150MHz新网表/面积、14门级、12全活动功耗及最终1200 ASIC任务。旧PT-063修复实跑待新smoke自然释放锁后串行安排。

### 19:45实施补充（历史，优先于19:20）

- 首包2bd6b0f已经经开发板Linux FileZilla上传。FTP最终断开并记入失败队列，但服务器2026-11-09T19:32:35.329713实测16217831字节与SHA6bd72b192968bfd5783248e5978a2223f476e7b43717183df43583337d0e4a17完全一致；既有unpack.py安全解包成功，随后inputs()核验573文件。不要重传/覆盖此完整包，不把FTP失败UI当作文件损坏。
- 新bundle绝对路径：/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-dma16-smoke-dma16-20261109_185450-2bd6b0f0075d。真实平台安装预检runs/dma16_install_preflight01/platform已通过：原baseline ee8bfecd81e192a974be81479ef8a01793de3e59c2e2f8769886e8e86143e56e、9个modified files；这是安装接线生成，未运行VCS/CPU。
- 旧门级d3_gate07_h0已经完成VCS、进入全文件native扫描；19:41:15活动子PID151649仍运行，读到VCD位置12030109043字节/总31246581717约38.5%。该扫描实际CPU持续推进，不能停止或跳过。真实锁是/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock，由driver128986持有。此前一次诊断用b.parents[1]查错层级显示LOCK False，已纠正，不能据此启动并行EDA。
- synth07约束报告显示无违反项，check_timing/结构警告仍继续逐项读；DMA16硬件尚未STA。新smoke应等现有锁自然释放。旧power修复实跑和新smoke随后统一串行，不同时占用。
- 后续新MMIO8 monitor已修clear凭据：必须成功CTRL2后新idle STATUS，START/新clear/复位失效。local_runs/mmio8_source_fixture_20261109_193147_494985/summary.json 6负测+3任务76032输出通过，733131过程总线cycles，NO E203。mmio8_soc新增12契约测试+layout8合计20通过。root已接server_run mmio8_soc、package --mmio8-firmware，实际ASIC未跑。
- 新dma16_gate.py/root stage、dma16_power/root stage已接好；gate只读同SHA DDC实际probe五模块及clock/boot端口，严格拒绝缺失，后续仅新增测试固件允许复用同一实际生产RTL网表。source identity不得把无关sw新增误当硬件变更。新gate10tests通过、实际mapped binding未做。所有这些均不在第一包中，需要独立后续提交/运行包。
- 三工作线继续：contest新增独立DMA16真实CPUsequence固件（5非法START真实trap、装载取消、短timeout恢复、A/B/A）；core与其对齐新source/monitor及NO_CPU夹具；evidence新增被动DMA分阶段总线统计。第一包生产RTL/固件/source/window/monitor保持冻结。新1200、14门级、12活动功耗、IRQ/WFI及CPU错误恢复仍未验收。

### 19:20压缩恢复补充（优先）

- 第一实施提交已完成并push私人分支：2bd6b0f0075d7e0a61809cd7f70fc990e7364e85。首包light-light126-dma16-smoke-dma16-20261109_185450-2bd6b0f0075d.zip，16217831字节、573输入文件，SHA6bd72b192968bfd5783248e5978a2223f476e7b43717183df43583337d0e4a17；独立ZIP唯一根/全部entry hash/CRC、干净包6测试通过。板端/home/root/undergrad-dma16-smoke-20261109同名ZIP已SHA核验。GUI路径为/home/board/undergrad-dma16-smoke-20261109。
- 尚未传到比赛服务器：Linux FileZilla登录收到421用户过多，已约隔数分钟在同一会话正常重试，没有绕行或开启并发连接。FileZilla当前窗口20972102，class Filezilla；已正常启动受限FTP代理。旧VNC仍18874436、relay session22118。目标仍icdesigns0.nicu.cn:18888、/IC/light-light126-undergrad-d2-20261109，密码只经helper --text-file stdin输入，禁止输出内容。
- FileZilla位于chroot GUI内，host无filezilla可执行文件。启动使用helper exec `busybox chroot /opt/ac820-gui-root /usr/local/bin/ac820-desktop-run filezilla >/tmp/kwt_dma16_filezilla.log 2>&1 </dev/null &`。代理入口F:/linux_fpga_try/tools/start_ftp_link.ps1。不能在截图被FileZilla遮挡时读VNC黑块；helper只设置focus、不raise。最有效切换：FileZilla用Alt_L F9最小化→VNC可见；恢复FileZilla点击主机Xfce4-panel窗口10485764的(216,15)。不要把远端Mate桌面顶栏当本机面板。xdotool不存在，XRaiseWindow尝试未前置，勿再重复。
- 18:59:47新预检：共享锁空、本比赛账号无EDA；全服务器其他账号有任务，不动。19:04:06.789751启动旧8路synth07的独立gate/activity首层，用原已上传portcheck包，session d3_gate07_h0、driver128986，编译子130399、仿真子153110；19:13:00最后读仍running且ASIC_BOOT/MODE/BOOT_MODE全部日志已出现。这是保底旧边界证据，不是新版加载对照。不得重启或清其锁，完成后读summary并继续旧PT修复实跑。
- 原门级run：.../bundles/light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386/runs/d3_gate07_h0/gate_soc；driver日志同bundle/runs/d3_gate07_h0.driver.log。synth07 summary SHA仍3a167b8a0c3f77d5837a91c9aa43264f4c4e2fbec44313e075f84a4ed92e3ed6。
- 首包已不可变，后续工作在当前worktree新文件中，不能替换首包内容。contest代理新增MMIO8_SOURCE_HANDOFF、原驱动SysMem源加载固件/布局/8单测（无CPU验证），正在新增mmio8_soc；root新增install_mmio8_source和arch03_mmio8_source_monitor，core代理正在做真实8core/arb/router/source的过程MMIO夹具（无E203）。该对照不是8路DMA。
- core代理新增port-only gate monitor生成器dma16_gate_monitor.py和arch03_dma16_gate_proof.sv，14定向+1真实RTL任务25344输出通过；cycles225770，finished晚15拍但end不变。实际门级需以新mapped_probe绑定5个模块路径，尚未写/执行dma16_gate stage。proof从末ACK之后的新MMIO PENDING/COMPLETION/ERROR/STATUS响应证明排空，不绑fifo_empty常真。
- evidence代理新增dma16_activity.py/dma16_power.py及10离线测试，实际native完整扫描/unknown保留，未运行PT。约定新gate scope=dma16_whole_soc_mapped_functional_without_SDF、stage=dma16_gate；summary需firmware_sha256/source_inputs_sha256，case需outputs/layout_sha256/task_window/activity；power依赖后续dma16_gate.verify_synthesis。12任务同gate/synth/firmware汇总，缺功耗/覆盖时值null不当0。
- 下一步：查看gate活动进展，等该锁正常释放后安排旧power；FTP继续适度重试，成功后把已板端核验首包经Linux FileZilla传到授权目录，按ZIP SHA及safe-unpack验573文件，运行dma16_smoke01单层→IRQ→14。新8对照、门级/功耗适配完成后另提交/打新包。后续1200、真实CPU无复位A/B/A/错误恢复、150MHz新STA/面积和12功耗仍缺。

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
