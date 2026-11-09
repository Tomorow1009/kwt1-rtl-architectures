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
