# 32位ICB与16×4执行检查点

H0=2026-11-10T22:04:16+08:00。用户已明确“没问题，按计划开始吧”，此前暂停解除。新有效计划workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md；11/11 18:00冻结，11/12 17:16交付准备。

## 当前状态

### 22:46增量（最新）

- 独立R1/R4核心、压缩transport/MMIO wrapper已实现：arch03_linear16x4.sv、arch03_icb32_transport.sv、arch03_icb32_accel.sv。transport源16/提交16/命令8/输出32，成功ACK发布，命令寄存器与旧pending owner分开，保持取消时held请求。MMIO新layout00100002及cap字段、动态长度；旧DMA layout仅原模块支持，debug支持旧scalar。
- R4核心本地pin_mock18任务（L01/extremes/rounding × pf0/1 × A/B/A，B=L12）全部通过，精确41bit总和/结果/sat、五阶段cancel、badbias、复位、末3行屏蔽和输入向量1..4检查；目录arch03_linear16x4_20261110_223725_260527_pin_mock，摘要ICB32_R4_CORE_20261110.json。首次223649_885305因Windows.bat拆generic参数=而xelab失败，改options文件后通过，原失败保留。
- 完整本地压缩datapath首L01 R4 pf1/jitter0通过：37428B、34639周期、25344输出，确认每个提交字在成功共享写ACK之后、每个解码半字等于原流、全部最终写响应、无复位held首请求取消；目录icb32_datapath_20261110_224350_084107，摘要ICB32_R4_FIRST_20261110.json。约4330.379task/s只按150MHz本地折算，无E203/时序/面积/功耗，不是最终成绩。shared_turnover首次已接真实pin_mock SRAM通过该完整任务。
- 正在跑：会话66399=R4全14例pf1/jitter1；6284=R1三例L01/extremes/rounding×pf0/1名义。工具local_icb32_datapath_verify.py。勿在运行中改这些受测文件。旧核心18任务会话10246及首datapath51571已结束。VNC隧道76458保留。
- 未完成：错误响应/取消各阶段集成定向、CPU竞争、R4名义12层及raw对照、新固件/平台安装/动态source/观察器/PPA宏清单、新ASIC14/1200/门级/功耗/干净复现；代码全部未提交。下一步先收局部结果并做协议测试，同时准备独立服务器运行入口；不能复用旧fcd PASS给新代码。
- 原服务器队列最后22:10仍8路L08扫描；未查新状态，不能重复或清锁。

### 22:34增量（最新）

- B1完整14例pf1/jitter1全部通过，354816输出；原目录222327_360464。名义条件另6例（L01/extremes/rounding × pf0/1）通过：pf0=227003、pf1=162713周期，原目录222810_184211。本地pin_mock真实DMA/core/shared，无CPU，不是服务器成绩。会话29674/83350均结束。摘要分别ICB32_B1_14_20261110.json、ICB32_B1_NOMINAL_20261110.json。
- turnover arb/router独立协议目标386事务通过，CPU/DMA各193、同拍退旧接新306次，错误/仲裁/反压通过；原目录arch03_turnover_fabric_20261110_222758_918604，摘要ICB32_TURNOVER_20261110.json。首次222736_316471编译失败仅TB误放counter声明域，保留失败；修复后pass。shared_sram_turnover尚未实际集成验证。
- 已写独立arch03_linear16x4.sv，R1/R4向量输入、64小宏X/32小宏W、双结果bank、末3行屏蔽；尚未编译/测试，不能声称核心通过。下一步核心测试，再新压缩DMA、ABI/固件/ASIC/PPA。全部未提交，原生产未改。
- 服务器最后仍22:10旧队列状态，未新查，不重启/清锁；VNC长会话76458保留。

### 22:27接续（优先）

- B1已创建独立arch03_dma16_forward_accel.sv（原DMA文件未改），以及tb_arch03_dma16_forward_datapath.sv/local_dma16_forward_datapath_verify.py；实现写成功ACK后load_word发布，无共享读回，core在首源读前已start但X/bank无效。TB每个load_fire验证原packet值及load_count<成功共享写ACK数×2；最终reads11744/writes24416，保留最后ACK及无复位取消held请求检查。
- B1 pin_mock真实datapath全14例pf1/jitter1运行会话29674，目录local_runs/dma16_forward_datapath_20261110_222327_360464；最后观察layer01–09全部通过，每例213836周期（带jitter，不能直接与旧225770名义窗口比）。原始14数据复用local_runs/light-light126-reportfix-dma16-20261110_020049-7dc2617176b6/validated_tile16且逐文件哈希验证。剩余通过和最终summary待读，不重启同批。
- 新增独立fabric版本arch03_icb_arb2_turnover.sv、arch03_icb_memory_router_turnover.sv、arch03_shared_sram_turnover.sv，原3文件保持不变。实现单在途rsp退旧/命令接新、老owner响应、同拍新pending优先、source窗口49152；shared保持读时序，写ready可在旧rsp消耗时接受。尚未compile/test/接入新DMA，不能声称通过。
- 下一步：收齐B1；另跑nominal jitter0与prefetch0必要对照；针对turnover写独立并发请求/响应scoreboard（旧fabric TB先记cmd后rsp不适用同拍，须响应先核销再新请求）；新R1/R4核心/压缩DMA集成仍未实现。
- STATUS.json与EXECUTION_CHECKPOINT.json新增顶层icb32_c64_execution字段，旧所有历史证据保留。新软件及decoder证据已入handoff/team/evidence；尚未git提交/推送/服务器上传。VNC隧道76458继续、第三远端终端空闲、旧重队列未动。

### 22:23完整接续入口（优先）

- 当前有效计划已保存，用户批准立即实施，不处于Plan Mode，不得以旧暂停停工。本轮不得无授权调用子代理（当前developer禁自动委派）。所有代码在既有个人分支，尚未提交/推送。
- codec软件8 tests通过；600/7200全任务编码/解码及独立坐标检查245秒通过，原始local_runs/icb32_codec600_20261110_2215，汇总已入handoff/team/evidence/ICB32_CODEC_600_20261110.json（SHA2ee5ab9786534c9d9ad099e604fc94d8039a1dce99309e8e8b2f211ca63b1dd6）。无截限、raw回退0、无任务理想总事务<=30000。平均37109.511111B，prefix13916.844444B；旧receipt把bias三半字计为coordinate_checks，入库摘要纠正为165427200原坐标，另列169113600回读半字。原回执不改，脚本仅未来输出字段修正，不重跑相同软件检查。
- 新RTL arch03_icb32_decoder.sv已实现，128bit有限reservoir，输入32bit、输出1..4×16内部向量，固定总头/块头/raw/bias检查、cancel与背压。TB tb_arch03_icb32_decoder.sv和runner local_verify_icb32_decoder.py在Vivado2018.3运行通过21项：16宽度、forced_raw、bad_magic/layout/width/count。每正常case含一次中途cancel和无复位连续两任务。独立decoder测试不是DMA/CPU/ASIC；原始local_runs/icb32_decoder_20261110_2219，摘要ICB32_DECODER_20261110.json SHA d1f4bc6fe7010fccc19ccbd721b710fa7c43c92ac2ae2d29b105dc3c8cf1498e。
- 两个本地运行会话87888/52519均已完成。VNC tunnel会话76458仍需保持；原服务器22:10状态未再查，parent232492/driver212822/scan127804在8路第8层，L02–L12全passed。不得重复启动队列/清锁。
- 下一步B1：复制现arch03_dma16_accel为独立arch03_dma16_forward_accel，保留原文件不变；PREPARE→CORE_START→COPY_READ；core在COPY_READ/COPY_WRITE/RUN均可load/out；源只有load_word空时请求，K_STAGE成功ACK后把copy_data送load_word，最后写后RUN；COPY_READ/RUN允许公平排输出，永不发K_LOAD共享读。错误/cancel停止发布，实际ACK计数仍保留。用现tb_arch03_dma16_datapath独立副本调整cold检查（core允许busy但x/bank valid必须0）、reads期望11744、sharedreads0、逐半字消费须落在ACK提交水位内。保留最终ACK/独立坐标/恢复断言。
- B1之后才改同拍周转的独立fabric、新参数化R1/R4核心与集成压缩。新固件/ABI/ASIC/服务器包/PPA尚未完成。不要把decoder单测当完成整计划。
- 工具：Python E:/fpga_race-two/.venv-kwt/Scripts/python.exe；Vivado D:/Xilinx/Vivado/2018.3/bin；命令参考local_verify_icb32_decoder.py与local_dma16_datapath_verify.py。现源码DMA/原datapath TB已读，见文件而非靠摘要猜细节。

### 22:15增量（优先于下方启动快照）

- 新计划、codec正式线格式ICB32_CODEC_V2.md、软件icb32_codec.py、8项定向test_icb32_codec.py已实现；8测试通过（16种位宽/尾块独立位解码、全流raw回退、非法头/截断/bias/导出）。未实现RTL decoder或新DMA/core，不能称硬件通过。
- 新icb32_compression_review.py开始对600捕获/7200任务逐任务真实编码、解码及独立原坐标检查，输出local_runs/icb32_codec600_20261110_2215，运行会话87888。首次输出12任务通过，完整结果尚待读取，不重启同目录。
- 现开发板在线，已恢复VNC既有认证（不输出凭据），FileZilla尚未打开。VNC tunnel本地长会话76458保持运行；当前viewer窗口18874435、远端第三终端页空闲csh。恢复先刷新窗口状态。
- 22:10服务器实际state确认L02–L12 MAC全部passed；原ecf唯一队列parent232492继续，mmio8_source_gate_full01的mmio8_gate于15:34:23.885524开始，driver212822，当前child127804扫描layer_08_activity_scan.log，CPU99.7%。ps已核实父子关系及活跃状态。共享锁存在，未清锁、未停止、未启动新重作业。截图takeover_local/icb32_queue_live.png和icb32_queue_detail.png。
- 状态查询第一次误取state根status得到None，已改读取stages实际字段核实；不是任务无状态或失败。开发板已有窗口与历史相同仅是本轮重新观测确认，不依赖旧ID。
- 下一步完成codec600回执并新增RTL解码/同拍周转与B1/参数化R4，更新运行工具的动态长度/宏清单。原生产fcd不改；目前修改仅本地未提交。

- 已保存新计划，现有源码HEAD57d62f6，生产fcd不变；19:46暂停文档未提交，保留。
- 新RTL/固件/codec尚未实现或验证。下一步先固定压缩格式与独立软件检查，再ACK转发/流水与参数化R1/R4核心，保持原模块作对照。
- 规划软件分析7200开发任务已完成但尚未固化脚本/摘要；64块+32B头平均37109.5111B，前缀13916.8444B，简单codec不足以证明5000。不要重复TensorFlow提取或改量化。
- 开发板19:46两个客户端正常退出，用户拟下电；本轮尚未检查是否重上电。远端最后观察12:12 L03，不是实时状态，不能重复原ecf串行队列/清锁。
- 保留1200/full02/12功耗已有结果，系统功耗false、原8完整PPA与干净复现等缺口不抹去。
- 代码/测试仍本地阶段，不称E203/厂商宏/新时序/PPA通过。

## 恢复入口

重读AGENTS、根交接、新计划、本检查点及三份状态。只在实际观测客户端/连接/队列后操作服务器；若开发板离线继续本地实现。当前个人分支保持，不能覆盖旧运行包。源输入压缩、成功落库后decode，输出不压缩；64bit仅内部buffer，公共ICB始终32bit。旧宽总线/128MAC方案取消。
