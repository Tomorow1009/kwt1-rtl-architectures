# DMA16 独立核心交接

更新：2026-11-09，新任务DMA计时窗口开始；子代理 dma_feasibility。H0=2026-11-09T17:16:08+08:00。

有效计划：IMPLEMENTATION_PLAN_DMA16_20261109.md。主代理授权本代理只新增16路核心及其定向测试，不改架构二、安装器或公共交接，不连接服务器、不提交Git。压缩后先重读 AGENTS.md、CONTEXT_HANDOFF.md、新计划及本文件。

## 已完成

- 新增 `rtl/arch03_linear16.sv`：16个原dot64、2个4096×16 X宏、32个独立128×16权重宏。load/compute独立控制，两bank有效位，完整W+b才有效；固定有序tile流以load_tile/compute_tile追踪bank归属。prefetch_enable启动锁存，关闭时禁止提前装下一tile。
- 端口沿用arch02_linear：start_valid/start_ready、shift、load_valid/load_ready/load_data、out_valid/out_ready/out_row/out_column/result/saturated、busy/done/error；新增cancel/prefetch_enable。done是最后输出握手后的1周期脉冲。非法bias高8位置sticky error，不接受start；cancel同步清任务并以flush_q清MAC/SRAM返回流水，调用者须等start_ready。SRAM物理内容不清零。
- 新增 `tb/tb_arch03_linear16.sv`：逐41bit累加和/结果/饱和、完整25344坐标与精确顺序；随机输入空拍、随机和连续输出反压；宏同bank读写冲突/返回一致性断言；MAC接受64项断言；X地址4095/4096与16tile覆盖。
- 新增 `scripts/local_verify_linear16.py`：旧已校验tile8向量独立置换为tile16，逐矩阵坐标/偏置片段核对；运行XSim并独立读取CSV比较NPZ；检查运行前后源码哈希。明确cpu_executed=false、dma_executed=false。
- 首轮 pin_mock 12个完整任务304128输出通过：layer01/extremes/rounding × 预取开关 × 连续2次；5阶段cancel与非法bias恢复。`local_runs/arch03_linear16_20261109_172259_700961_pin_mock/summary.json`。这是旧版TB同输入重复，RTL与当前相同。
- 首轮随机反压核心周期：关闭约188k，开启约169k；开启观察约10k周期load/compute并行。仅核心结果，不能当完整DMA性能。

## 后续回归已完成

- 强化pin_mock全量旧12层+extremes/rounding，两种预取、不同A/B连续运行56任务、1419264输出通过。`local_runs/arch03_linear16_20261109_172620_010181_pin_mock/summary.json`。session1321已退出0。
- behavioral无停顿A/B/A：12任务304128输出通过。`local_runs/arch03_linear16_20261109_172758_564578_behavioral/summary.json`。session46933已退出0。prefetch关闭156560周期；开启140480周期、12450周期计算/装载重叠。仅核心性能。
- 正式d3冻结14case pin_mock预取A/B/A：42任务1064448输出通过。`local_runs/arch03_linear16_20261109_173050_650156_pin_mock/summary.json`。session86916已退出0。输入来自`local_runs/light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386/validated_data`。
- 双bank同时有效时cancel、输出暂停硬复位、启动参数锁存、5阶段cancel、非法bias恢复均在强化TB中真实执行通过。
- 正式导出器与本测试独立转换对d3全部14case、328832半字逐项一致。回执`local_runs/dma16_core_layout_crosscheck_20261109_h0/crosscheck.json`。
- 核心RTL始终未修改，SHA256 `6bb63bf42437617a5b73b71c22c0874528868f5ef9b4f01be5d9687dde433322`。未连接服务器或提交Git。

## 新任务／未完成

主代理追加：只读审阅其新增`rtl/arch03_icb_arb2.sv`和`rtl/arch03_icb_memory_router.sv`，新增独立TB/runner实测CPU/DMA公平、stalled grant稳定、response归属、非法地址/source写拒绝、source边界及反压。只改新增测试，不自行改其RTL。主代理已真实核对O4 base80000000、regionLSB31，source B0000000合法，原sysmem零应答stub会经同一原有接口供TB响应。

这项已完成：新增`tb/tb_arch03_icb_fabric.sv`和`scripts/local_verify_fabric.py`，真实XSim通过386事务（CPU193/DMA193），128次双主机公平竞争、101周期请求阻塞、629周期响应反压、193共享访问、65源访问、128非法访问拒绝、44下游原生error传播；最终pending排空。回执`local_runs/arch03_fabric_20261109_175055_289123/summary.json`。没有改主代理RTL，没有发现其功能缺陷。受测arb SHA256 `115c4ec34a4d60229f8f87e3eb8416cf1ae9ea52fdf82c6fdb31137c3b5b8a43`，router `c855578f080c555c695b5b5dff2200a7bdc2460ed1579029010bf4825add2b83`。这里是协议目标替身，不是真实CPU或SRAM/DMA集成验收。

保留两次测试失败：`arch03_fabric_20261109_174714_028840`全部258事务走完但只有1次竞争，测试覆盖闸门拒绝；增加双主机持续请求阶段。`arch03_fabric_20261109_175020_216169`因新增always引用reg早于声明被Xvlog拒绝；调整测试声明顺序后成功。均为测试问题，无生产RTL修复。

此前运行记录（现均已完成，保留过程）：

1. 加强TB后全量pin_mock回归正在运行：12层+extremes/rounding、两种预取、每组不同A/B输入连续运行，共56任务。新增双bank都有效时cancel、输出暂停时硬复位、启动后改变shift/prefetch输入以检查锁存。运行目录 `local_runs/arch03_linear16_20261109_172620_010181_pin_mock`；exec session **1321**。最近观察前三组（layer01 pf0/pf1、layer02 pf0）通过；不能将整批提前标PASS。
2. behavioral无停顿A/B/A补充正在运行：extremes、rounding，两种预取、repeats=3，共12任务。运行目录 `local_runs/arch03_linear16_20261109_172758_564578_behavioral`；exec session **46933**。尚未读最终结果。
3. 两个运行都锁定当前RTL/TB/runner源码哈希，结束前不要修改这些文件。用write_stdin读上述session结果；失去session时读目录最终summary与日志，不能重启已有运行。
4. 尚未服务器厂商宏、ASIC CPU/DMA集成、综合、时序、面积、功耗验收。主代理和evidence_audit负责集成，已通知准确端口。核心接收逐16bit输出，32bit打包/FIFO归DMA模块。

## 尝试路径和限制

- 第一次XSim编译/展开和首轮仿真即通过，尚无RTL失败修复。首轮exec只输出stdout导致session号未保存，已以日志/最终summary核实完成，没有重复启动。
- 新测试在已通过基础上增强A/B不同数据、预取取消和硬复位；这使首轮summary只能证明旧TB范围，当前增强范围待运行完成。
- 本地Vivado：`D:/Xilinx/Vivado/2018.3/bin`；Python：`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`。
- 运行命令见各目录options；完整入口例如 `python workspaces/arch03/scripts/local_verify_linear16.py --vivado-bin D:/Xilinx/Vivado/2018.3/bin --backend pin_mock --prepared local_runs/arch03_linear16_20261109_172259_700961_pin_mock/tile8`。
- 不修改其他代理新建的DMA/layout文件；Git未提交改动属于协作正常状态，不能reset/clean。

## 下一步

核心回归、正式layout交叉比较及arb2/router协议测试全部完成并已回报，不重复启动已完成作业。后续真实CPU/DMA/服务器/PPA整合由主代理推进。核心有序控制以tile计数器和bank有效位追踪归属，当前没有独立bank_tile寄存器；若需要加入显式tag，应另做变更并重验，不能复用当前源码哈希的PASS。

主代理新增任务：只新增独立`arch03_task_window16`监视器、TB和runner，不改现有window或installer。监视器仅通过接口观察，不绑RTL层级；首source读valid真正发出时起计（不是接受拍），全部12672结果32bit写成功ACK且global_pending/fifo/本地pending排空才结束，检查3×11744+12672事务、每段完整地址覆盖及单outstanding。取消/error允许failed结束但不能PASS。

已获主代理接受的接口：输入clk/rst_n、task_arm（成功MMIO START）、task_cancel（CANCEL/引擎error）、cmd_valid/ready/addr/read/wmask、rsp_valid/ready/err、global_pending、fifo_empty、core_done；输出active/finished/failed、failure_code[31:0]、start_cycle/end_cycle/window_cycles[63:0]、source_read_acks/input_write_acks/input_read_acks/output_write_acks[31:0]、command_wait_cycles/response_wait_cycles[63:0]。可额外realtime start_time/end_time。window_cycles=end-start，batch period_fs=6666666。

实现完成：新增`tb/arch03_task_window16.sv`、`tb/tb_arch03_task_window16.sv`、`scripts/local_verify_window16.py`。非综合monitor在cmd_valid/addr/read变化时捕获首源请求，映射最近发送时钟沿的cycle编号，防止NBA生成valid后次拍观察漏1拍；posedge做实际握手/ACK计数；异步观察global_pending/FIFO等排空证明。**主代理后续澄清：end_cycle/end_ns固定为最后相关ACK，finished可以更晚；观察/证明的延迟不得增加计时。**正常core_done允许早于末写ACK（计算先完成FIFO再排空），不能把core_done直接当结束。它若早于全部输入读ACK则失败。

最终XSim回归通过：`local_runs/arch03_window16_20261109_181620_539354/summary.json`。3个完整四段任务，每个191616B；12种负向/取消检测全部failed结束，额外post-DONE写也锁存failed。首请求ready额外7周期+末ACK反压31周期，窗口相对基准精确+38；另一例global_pending延迟4、FIFO延迟6周期，仅finished延后6周期、end_cycle不变。独立realtime与周期×6.666666ns相符。

正式top须在固件完成邮箱时再次检查finished&&!failed，不能仅依较早window failed=0打印验收；后续非法额外命令/孤立响应会锁存failed。功耗按start_ns/end_ns裁窗，不能直接把晚到finished/dumpoff当作真实功耗终点。观察器SHA256 `f293be21d3526cc1fd946a276a7d175908c1d668af74b33494dc56a8a43a7aff`。当前本代理无运行中测试。

其他只读审查：已核对kwt_dma16.c CANCEL/PENDING掩码、完成ACK计数和tile16坐标与RTL一致；MODE0 CPU源复制在MMIO START之前，因此仅debug，不能直接套DMA观察器作同口径对照。已向引擎代理指出orphan检测条件`dma_rsp_valid && !pending_q && !dma_cmd_valid`会漏掉cmd_valid=1/cmd_ready=0时提前出现response；建议改为`!pending_q && !dma_fire`并负测，未代改其RTL。引擎代理已知旧datapath起点可能漏首拍，旧291154/347392只保留原边界，不当正式吞吐。

## 加载源／生产monitor审查（2026-11-09 18:40附近）

主代理追加只读review `scripts/install_dma16.py`、`tb/arch03_dma16_source.sv`、`tb/arch03_dma16_monitor.svh`，新增独立夹具测试，不操作服务器或Git。发现source初版多了一拍pending：N接受、N+1置valid、N+2最早ACK；datapath jitter=0是N接受寄存valid、N+1最早ACK。已回报后获得明确授权修改生产source，统一为后者，删除多余pending拍。其余生产monitor/installer仍只读。

- 新增source单测及runner：`tb/tb_arch03_dma16_source.sv`、`scripts/local_verify_source16.py`。全11744源字、5种非法/边界请求、20周期响应反压、reset取消与文件数据保留，共11752完成请求通过；确证ACK最早N+1。证据`local_runs/arch03_source16_20261109_183204_772860/summary.json`。source当前SHA256 `b3cc324c016c49cca71e5a0c53fcf116253d9e4dba79f45c52be2acd28976c7a`。
- 新增完整同名层次夹具`tb/tb_arch03_dma16_monitor_fixture.sv`及`scripts/local_verify_dma16_monitor.py`：真实DMA/core/arb/router/shared pin_mock+原production source+原production monitor，由procedural MMIO/mailbox initiator驱动，没有E203。原monitor硬编码cpu_executed=true日志在夹具内无效，runner/summary必须明确cpu_executed=false，不能拿该标记冒充CPU验证。
- 首轮夹具6任务（layer01/extremes/rounding × pf0/pf1）所有输出与monitor检查均走通，pf0=274010、pf1=225770，与datapath jitter=0完全一致。但**最终源码哈希审计拒绝**：production monitor在运行期间被主代理修改。原运行`local_runs/dma16_monitor_fixture_20261109_183440_172869`没有最终PASS summary，不得算冻结验收。session34840已退出1。已通知主代理等待其monitor修改告段落后用当前文件重跑。
- installer确定性缺口已报告：mmio8_reference分支仍使用DMA16 monitor（字段不匹配且a3_dma绑0），将展开失败或窗口不开始；应拒绝该变体或另配监视器。DMA16正向接口已由夹具展开/运行验证过。gate monitor仍绑定内部核心/FIFO层次，扁平映射后须单独适配，不能靠SysMem顶层端口推断门级兼容。

下一步：等主代理告知monitor稳定，重跑现有6任务夹具并保存最终summary；不要修改生产monitor/installer。当前无本代理运行中的作业。已有全核心/窗口/fabric/source单测不重复跑。

## 冻结monitor重跑完成（2026-11-09约18:42）

主代理确认monitor冻结后已完成重跑：`local_runs/dma16_monitor_fixture_20261109_183941_919463/summary.json`，session6115退出0。layer01/extremes/rounding两种预取共6任务、152064输出逐项通过，所有运行时源码前后哈希一致。关闭预取274010周期，开启225770周期，与datapath jitter=0一致。原monitor变更期间的首轮失败仍保留，未计为冻结PASS。

本夹具是procedural MMIO/mailbox发起，真实core/DMA/arb/router/shared pin_mock及生产source/window/monitor运行；没有E203。summary明确`cpu_executed=false`，原monitor日志硬编码CPU标志在夹具中不能当证据。本次没有启用VCD，不将功能PASS宣称为活动裁窗验证；真实ASIC CPU、IRQ/WFI、厂商宏、门级层级适配、PPA仍待主代理执行。

只读复核：`install_dma16.install()`现已明确拒绝非dma16变体，先前mmio8_reference误用监视器风险已封住。门级monitor仍引用内部core/FIFO信号，必须经门级别名适配和真实编译再验，不因RTL夹具通过而宣称扁平网表兼容。生产source保持最早N+1 ACK定义和SHA256 `b3cc324c016c49cca71e5a0c53fcf116253d9e4dba79f45c52be2acd28976c7a`，本代理不再修改已冻结core/source/window。

当前本代理无运行中作业，无服务器操作或Git提交；已将最终证据路径与边界回报主代理。后续按集成发现的问题再定向补测，不重复已完成的全回归。

## 单任务完整VCD边界验证（2026-11-09约18:49）

主代理追加要求：同一生产source/window/monitor，仅layer01/prefetch1启用ACTIVITY，实际VCD dumpon/dumpoff必须匹配window，不改生产文件。已增强本地runner `--activity`（强制单case和单pf），并新增独立`local_audit_dma16_activity.py`轻审计。

- 实际运行：`local_runs/dma16_monitor_fixture_20261109_184337_045342`，session92371已退出。25344结果和生产monitor检查通过、周期225770，但runner按请求文件名检查时失败：XSim2018.3将动态packed-reg `$dumpfile`路径写成工作目录`dcv`。保留此失败，未给该运行伪造功能summary。
- 原始VCD `dcv`为749218404字节，SHA256 `daae0b9d5018187bc77ca7e8ff1ef16c5d817a1f863e4eb365a9b6f73e138d54`。严格production activity.py初次拒绝其136个`$var parameter 0`零宽参数；没有修改或放宽正式ASIC审计器。
- 独立边界审计实际通过：`activity_boundary_audit.json`。完整文件扫描确认dumpvars/dumpoff在0，唯一dumpon在163.333317ns，最终dumpoff在1505296.516137ns，与window start_ns/end_ns逐fs相等，文件最后timestamp即终点。225771条时钟上升值记录，除起始快照外所有间隔均6666666fs，实际周期6.666666ns。
- 这是边界及实际时钟证明，`full_activity_value_audit=false`、`cpu_executed=false`、`asic_power_evidence=false`，不声称未知值覆盖、门级映射或功耗通过。production source/monitor/window/fixture哈希仍与上一6/6冻结结果相同。
- 本地runner随后增加明确记录的`dcv`兼容文件名发现，只查本轮新建目录；尚未为这项文件名选择再次重跑仿真，已有原始文件已独立审核。不重复生成750MB波形，下一次必要仿真时再验证该分支。边界审计命令为`python workspaces/arch03/scripts/local_audit_dma16_activity.py --vcd <run>/dcv --log <run>/layer_01_pf1.log --output <run>/activity_boundary_audit.json`。

所有结果与工具兼容限制已回报主代理。当前本代理无运行中作业，生产文件冻结不动；无服务器操作或Git提交。

## 门级monitor离线准备（2026-11-09约19:17）

主代理首包固定2bd6b0f后追加任务：只新增门级monitor适配生成器及离线测试，不能改冻结RTL/source/window/monitor/综合，不操作服务器、不提交。先提出接口方案后实施，真实mapped probe由主代理完成。

新增文件：`scripts/dma16_gate_monitor.py`、`tb/arch03_dma16_gate_proof.sv`、`tb/tb_arch03_dma16_gate_proof.sv`、`scripts/local_verify_dma16_gate_monitor.py`。

生成器读取冻结production monitor，只生成独立SVH：DMA与MMIO使用u_arch03_accel真实边界端口；核心使用实际实例u_arch03_accel.core的out_valid/out_ready/out_row/out_column/result/saturated；共享使用u_arch03_shared端口。arb/router以各自cmd/rsp边界被动跟踪单在途及held valid，避开无功能fanout可能被综合删除的transaction_pending和a3_alias。所有DUT内部*_q及A3MEM/A3DMA别名依赖均删除并检查。真实门级五组实例路径必须另行probe；不接受任意Verilog表达式或常真替代。

完成证明来自真实MMIO命令/响应配对：START前PENDING有效mask0x1f1f为0，加idle/start-ready STATUS；CLEAR后重新观察start-ready，不凭空置FIFO空。START后失效旧证明。所有12672输出ACK后新发出的STATUS、COMPLETION、PENDING、ERROR读取分别证明DONE/idle、低6位31、有效pending全0、ERROR0；仅响应延后而命令在末ACK前发出的旧快照不能当新证明。FIFO空没有绑常真。窗口finished因此延后，但end仍原lastDMAACK；后续CPU邮箱流量不会抹掉已成立的MMIO证明，fabric pending另行跟踪。error/取消/未知读数据/协议违例只能拒绝PASS。此正向单任务门级observer不是多任务取消恢复验收器，异常可保持failed而不发布成功窗口。

XSim实际通过：`local_runs/dma16_gate_monitor_offline_20261109_191506_399311/summary.json`，session91976退出0。14项定向覆盖缺少初始PENDING、CLEAR后新STATUS、陈旧PENDING响应、非空FIFO、aborted/core_busy状态、错误响应/非零ERROR/unknown、额外DMA、CANCEL、arb孤立响应、router多在途及CPU mailbox pending。另真实RTL+pin_mock完整layer01/pf1：25344输出逐项一致，cycles225770；start_cycle26/end225796/finished225811，完成证明比末ACK晚15拍而计时不变。源码/布局前后哈希通过。

CLI已生成同目录`port_only_candidate.svh`及JSON manifest，状态明确offline_candidate、gate_simulation_verified=false。调用示例：`python workspaces/arch03/scripts/dma16_gate_monitor.py --bindings <probed-five-instance-paths.json> --output <new-dir>/arch03_dma16_gate_monitor.svh`。门级编译还须加入新增arch03_dma16_gate_proof.sv。当前只支持简单层次标识符；若flatten导致模块/core边界不存在，不得臆测网名，需由主代理依据真实网表决定绑定/保留边界路径。

结果已回报主代理与功耗适配代理。当前无运行中本地作业，生产RTL/source/window/monitor全未修改，无服务器操作/Git提交；真实映射、厂商宏、E203、SDF、门级14case及功耗仍未由本工作证明。

## 同口径原MMIO8源加载本地夹具（2026-11-09约19:22）

主代理追加同加载源8路参考验证，指定新增独立TB/runner，不改冻结DMA16文件或主代理8monitor。新增`tb/tb_arch03_mmio8_source_fixture.sv`和`scripts/local_verify_mmio8_source.py`，保持同名平台层次，使用原arch03_icb_accel/arch02_linear、真实arb/router/shared pin_mock，DMA主设备端绑0，加载源复用已冻结production N+1 ACK模型。

procedural CPU依main_mmio8_source.c与原kwt.c的总线语义执行：CTRL2成功后读ID和STATUS低5位0，mail8 BEGIN；11744次源32读及shared32写；再执行原驱动CTRL2/ID/SHIFT/START和轮询；每个LOAD先实际读取shared半字地址一次，共23488次32位返回；每个OUTPUT读取得坐标/饱和后以SH字节掩码写回，共25344次。VALID在posedge后NBA发出，窗口cycle与实际ns差值一致。没有E203，没有模拟CPU指令周期；原monitor日志硬编码cpu_executed=true不能当CPU证明，runner强制独立NO_CPU标志和summary false。

真实XSim三case（layer01/extremes/rounding）通过，76032输出逐项核对NPZ：`local_runs/mmio8_source_fixture_20261109_191951_524017/summary.json`。session58631退出0，全部case均733131夹具周期；实际周期6.666666ns。每例成功ACK分别source11744、inputwrite11744、inputread23488、outputwrite25344；运行前后生产source、8monitor、RTL和数据哈希一致。数据目录`local_runs/mmio8_source_layout14_20261109_v1`。额外独立NPZ比对这三case的result/saturated/total与正式DMA16数据完全一致。

已向主代理报告8monitor只读严谨性缺口：当前m8_cleared由任意低5位0的STATUS响应置1，没有独立“确实观察到本任务CTRL2成功响应”门槛；本夹具实际做了两次CTRL2，所以正向证据有效。主代理可补seen_clear状态和负测，若改monitor应另跑对应新哈希验证，不能借本次PASS。此问题未由本代理代改。

当前本代理无运行中测试，结果已回报主代理。733131不是E203软件性能，不能与DMA225770直接宣称官方速度提升；下一步真实ASIC CPU、同条件综合/PPA、门级及实际冻结条件由主代理集成。

## MMIO8清状态证据修复与负测（2026-11-09约19:34）

主代理明确授权修改本次新`tb/arch03_mmio8_source_monitor.svh`，修复上节seen_clear缺口，只允许改该monitor及本代理新fixture/runner/交接，不动首包DMA文件。已完成：新增m8_clear_command_seen，仅实际成功CTRL2响应置1；CTRL2/START一旦接受立即撤销旧clear/idle凭据；必须随后真实读取低5位已知零STATUS，才允许BEGIN。error响应比较改用case inequality，未知error不能当成功清除。复位撤销旧凭据；已armed/active/结束待提交的任务复位明确失败，不将取消任务变成成功任务。

最终证据：`local_runs/mmio8_source_fixture_20261109_193147_494985/summary.json`，session55118退出0。6项独立真实RTL负测全部按预期fatal且无成功标记：1未clear仅STATUS0；2clear成功但未重新读STATUS；3旧凭据后再次CTRL2已接受但ACK被反压；4复位后重读STATUS0仍不可复用旧clear；5已armed任务复位；6START已消耗idle凭据。负测专门断言并记录实际STATUS=00000000，case4复位前后均为0，避免依赖默认值推断覆盖。

同一最终编译/哈希下三正向layer01/extremes/rounding全部通过，76032输出，所有ACK计数完整，733131cycle不变，实际时钟6.666666ns。首轮修复（尚未加强STATUS=0日志断言）也已通过，记录保留在`mmio8_source_fixture_20261109_192904_405454`，session36395退出0；以193147最终记录作为完整证据。

最终SHA256：
- 8monitor `84f4174e81aa8f2759b4f2e5fab2048b7996a5e811f896557cec3756e876c43f`
- 8fixture `88d7a9b6d2eef9deb9ffd80685605970b5d726e0365cd9be171162b7428a12b4`
- 8runner `175bd2a88c6fcf14fc500b226d7d1f58e90349e05ac5db00d91bf56fa2ef13d9`

取消/复位范围审核：真实CONTROL2驱动原arch03_icb_accel.abort_q，使core的rst_n失效，之后STATUS证明可观测空闲；本观察器保证成功clear响应和新idle状态都发生在BEGIN之前，替代clear未ACK不算，复位后必须重新获取凭据。原驱动在源复制后另做一次CTRL2仍合法；本监视器是单任务正向验收，不声称任意中途取消、未知注入或连续多任务恢复全覆盖。真实E203、厂商宏、门级、PPA仍未由这些夹具验证。

最后比对首包linear16、DMA16engine、source、window、production DMA16monitor五文件，均与此前冻结哈希完全一致。当前无运行中本地测试，无服务器操作或Git提交；已向主代理回报全部路径、哈希及范围。

## 新任务：DMA16真实CPU sequence配套（准备中）

主代理追加sequence source/monitor和本地真实DMA/core/fabric夹具，只新增sequence TB/runner/交接，不修改首包单任务文件。contest_requirements正在写main_dma16_sequence.c/start_dma16_sequence.S/build_dma16_sequence.py。已只读旧8路ITCM sequence，明确不能复用其数据预填/任务计时/首任务退出逻辑。当前尚未创建sequence代码，无运行中作业。

已与固件代理确认契约v1：polling，无IRQ；metadata ITCM fff0四词为magic53313631、A descriptor=(source_id<<16)|shift、B descriptor、short_timeout默认8192。默认A=source0/layer01/shift12，B=source1/rounding/shift11。固定源地址B0000000，source预读文件plusargs FIRST_LOAD32/SECOND_LOAD32；monitor用DATA_DIR/SECOND_DIR/CAPTURE_PREFIX。CPU先CANCEL/CLEAR等ready，mail[33]成功写ACK才选descriptor，要求无残留DMA/源事务及core.start_ready；mail[32]=phaseid开始阶段。选择源不向硬件预填数据。

阶段1..5为source错位B0000002、input越界A007F000、output=input重叠、input_bytes46972、output_bytes50684；非法START须实际ICB error及CPU store-access-fault cause7，FIRST_ERROR3/error_phase2/error_addr40000004，零DMA。阶段6有效START，source ACK>=32仍初始装载时CANCEL，实际排空/start_ready，保留partial ACK、无输出。阶段7原kwt_dma16_run timeout8192，必须实际source ACK>0且<11744、输出0、TIMEOUT及cancel_drained；若启动开销致source0必须失败不能伪装。阶段8/9/10正常A/B/A，无DUT复位，完整独立窗口和输出逐项核对。

每阶段receipt位于A0020000+(phase-1)*0x100，词0..32：phase,kind(1cfg/2cancel/3timeout/4success),rc,STATUS,COMPLETION,PENDING,FIRST_ERROR,error_addr,error_phase,source_ACK,stage_ACK,load_ACK,out_ACK,load_committed,out_committed,load_halves,out_halves,sat,cycles_lo,cycles_hi,cancel_drained,累计真实guarded_trap数,last_cause,last_epc,last_mtval,descriptor,modified_offset,modified_value,timeout_budget,pre_cancel_source_ACK,pre_cancel_stage_ACK,pre_cancel_STATUS,stats.primary_result。mail[34]=phase commit，需fence保证receipt先写完。最终mail[0]=53313650，失败bad00032，未预期trap bad00001；最终mail1rc/2完成阶段数/3当前phase/4trap数/5magic53313631/6IRQ0/7A_desc/8B_desc/9timeout。

实现建议已发主代理：每阶段MMIO命令/响应配对与寄存器snapshot校验，START尝试只允许本phase；5配置错误计数独立。source选择在CPU shared成功ACK后锁存，当前CPU mailbox自身事务的NBA排空不误当残留DMA。每个有效START后在首source VALID前观察core.cancel端口脉冲和随后start_ready，证明真实PREPARE冷清。复用冻结task_window16重复arm：错误/cancel允许failed完成，成功三次各独立25344结果和饱和核验，不在首任务退出。core负向恢复与trap/timeout的真正CPU执行最终由平台固件验，procedural夹具必须标NO_CPU。

下一步：等固件草稿完成做只读核对，然后新增独立arch03_dma16_sequence_source.sv、arch03_dma16_sequence_monitor.svh、tb_arch03_dma16_sequence_fixture.sv和local runner。禁止改已有single-task source/window/monitor或生产RTL，不操作服务器/提交。

### sequence首轮完成／最终回归待v4

已只读审核固件main/start/builder，未发现须改其代码的问题。v3固件manifest为`local_runs/dma16_sequence_firmware_20261109_v3/manifest.json`，SHA c04056ff804ae88660be2fcdc723aadbb0a53d92af7d2b49fc5220cb20e895cd；ELF5f751362ad33a01f0b4237c84ef36b809708e23f6913741451c19eb0a80b9acd；故障store80000100/resume80000104。实际bank文件CRLF与规范LF哈希区别由build_dma16_sequence.verify_runtime_sources核对token/payload并冻结实际文件SHA，不能把规范LF hash直接当文件hash。

本代理已新增4文件：`tb/arch03_dma16_sequence_source.sv`、`tb/arch03_dma16_sequence_monitor.svh`、`tb/tb_arch03_dma16_sequence_fixture.sv`、`scripts/local_verify_dma16_sequence.py`。真实模块/字节顺序保持首包，新增source两个PC预读bank，只有成功SELECT写响应后且DMA/source/core已排空可切换；每个有效START后首source VALID前必须观察core.cancel脉冲和core.start_ready，证明本次PREPARE。监视器将receipt字段3..17与真实MMIO读响应快照比对，再比独立DMA/core ACK/half/结果/sat计数；最后53313650才结束，不在首任务退出。

首轮实际XSim成功：`local_runs/dma16_sequence_fixture_20261109_195123_557884/summary.json`，session76690退出0，5个真实配置MMIO error零DMA；phase6独立ledger源35/初写34后取消排空；phase7局部tick超时源1348/初写1347排空；成功A/B/A各225770cycle、共76032输出，B rounding的sat4554、两次A的sat0。无DUT复位。窗口失败后字节计数停止，只显示失败前前缀（phase6窗口源34但ledger源35；phase7窗口源1347但ledger源1348），窗口end仍是最后相关ACK；失败阶段完整drain响应以独立ledger/receipt为准。只有成功8..10严格完整四段191616B。已通知root和固件代理，真实CPU runner允许该区别。

夹具没有E203，配置错误响应是真的硬件ICB error，但receipt中的guarded trap值是显式模拟，不能当真实CPU trap；phase7使用本地tick超时并真实cancel，只证明硬件恢复，不证明原C mcycle timeout执行。最终marker在ARCH03_SEQUENCE_NO_CPU下明确cpu_executed=false、actual_CPU_traps_verified=false、actual_driver_timeout_verified=false。

当前源码又增加了最终待验内容：每阶段commit通过后在PHASE_PASS之前输出`DMA16_SEQUENCE_RECEIPT phase=N words=<33个8位hex逗号分隔>`，供真实CPU runner保存与独立复核。三个新负测：partial期间提前切source、receipt错误fault EPC、缺失第32词，均要求明确fatal而不成功。尚未运行此增强版。原首轮summary仅对应加入这些修改之前的hash。

正式plusargs：FIRST_LOAD32/SECOND_LOAD32、DATA_DIR/SECOND_DIR、CAPTURE_PREFIX、FIRST_DESCRIPTOR/SECOND_DESCRIPTOR/EXPECTED_FAULT_EPC（%h）、SHORT_TIMEOUT（%d）。成功CSV `<prefix>__task1.csv`、task2、task3（row,col,result,sat）。日志顺序ARM→DMA16_TASK_WINDOW→DMA16_SEQUENCE_RECEIPT→DMA16_SEQUENCE_PHASE_PASS，最终DMA16_SEQUENCE_PASS。真实CPU runner由contest_requirements新增dma16_sequence_soc.py，不由本代理修改。

下一步等待固件代理v4 manifest（root正在修改dma16_batch计时元数据，v4需绑定新source hash），之后执行最终runner：`python workspaces/arch03/scripts/local_verify_dma16_sequence.py --vivado-bin D:/Xilinx/Vivado/2018.3/bin --data local_runs/dma16_layout_14case_20261109_h0 --firmware-manifest <v4>/manifest.json`。最终跑期间不要修改sequence四文件或builder依赖。当前无运行中本地测试；首包冻结文件未改，无server/git。

### sequence最终冻结验收完成（2026-11-09约20:02）

v4固件身份已固定：`local_runs/dma16_sequence_firmware_20261109_v4/manifest.json`，SHA256 `2d921e2563d7dd70b51d7d29f36b802e208a18445b3c05df2c6a086f6203ff1b`，builder `1929e60be8976c657521e324dee43ff2541e4b9ae236d40aa6516b3f362ce90a`；ELF、程序only boot、guarded EPC与v3逐字节相同，只更新验证工具身份。已绑定v4执行最终回归。

最终XSim全部通过：`local_runs/dma16_sequence_fixture_20261109_200001_072693/summary.json`，session58783退出0。三个独立负测：phase6仍活动时提前SELECT切源、phase1 receipt错误fault EPC、phase1缺少receipt[32]，均精确预期fatal且没有sequence成功标记。随后完整10phase、A/B/A 76032结果/饱和逐项通过，三个完整任务225770cycle；中间rounding/shift11 sat4554，layer01/shift12两次sat0。全部源、数据及v4 manifest前后哈希审计通过。

每phase现在额外输出完整33词receipt，日志顺序明确ARM→WINDOW→RECEIPT→PHASE_PASS。`summary.json.receipts`保存原词数组，PHASE_PASS保存独立总线计数。成功8..10全四段计数严格相同；失败1..7的window字节仅失败前前缀，phase ledger/receipt包含最后排空ACK（该差别已纳入真实CPU runner parser）。新的monitor还明确拒绝unknown MMIO error/read data和未知core idle/ready，不把X当可切源状态。

最终sequence文件SHA256：
- source `60c2832c66c80ed3c8b67cc7dac1aee6ca43e853fcbbda1f6a966bfe20fd9820`
- monitor `93259f9e028f092c7b612e5b87a3867fb9abf9314ee37f31d201cbc1ab5604f2`
- fixture `91ba2a28e04e6ce8dd1cee7f5017a2ae8f6dc64cf9ef9feaa97200218c1636ac`
- runner `57f88e5fc165756e6a0dbe6d50223e50836527d3bb7987e05dc65e5b39be4fee`

root与contest_requirements均已收到最终路径/hash/marker协议。contest负责`dma16_sequence_soc.py`实际ASIC CPU入口；它可逐阶段用本日志核验解析结构，但最终必须拒绝NO_CPU标记，不得改日志冒充CPU。当前结果仅真实硬件数据通路/错误响应/排空/冷清/A-B-A，无实际E203、guarded trap或原C driver timeout执行证据；无ASIC厂商宏/门级/PPA声明。当前无运行中本地作业，首包单任务文件未改，无服务器操作或Git提交。
