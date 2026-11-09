# 整机任务模式时序复核

## DMA16当前综合的独立复查（2026-11-10）

06:18审定：全部结构告警已完成分类与用途复核，结合下述时钟、约束、禁用弧、数值及同网表功能证据，接受**声明范围内的稳定任务模式综合时序**。正式依据见[FROZEN_REVIEW](FROZEN_REVIEW_20261110.md)。本节以下“等待审核/false”为当时历史状态，原始工件仍保持原标记；最终报告须另外绑定审定记录，不原地修改旧摘要。

06:11更新：b60包实际结构审计于06:03:57.998090完成，完整解析1334模块（替代初步文本统计1315）。全部4852条LINT-8/28均无声明之外的逻辑引用，方向为4684输入、168输出；没有未解析对象或表达式待判对象。原网表/报告SHA保持不变，完整清单位于b60 `runs/dma16_struct_review01/mapped_port_diagnostic.json`，SHA=`999df6259a5a0a93f7c958ecefdeefa2114275d9354ad4236e4b02367c576c60`，独立断言已通过。这解释了端口类告警，其他LINT类别和正式接受记录仍须完成；不改变物理签核范围。

05:58本地新增`dma16_structural_audit.py`：绑定当前综合摘要及mapped.v/check_design_mapped.rpt的实际SHA，逐模块读取端口方向/范围，并检查全部LINT-8/LINT-28对象在去掉头部与声明后的实际逻辑引用。仅声明、表达式仍存在、缺失/未解析对象分别处理；输出完整对象表及其余LINT计数，不自动批准时序。8个定向测试通过，尚未上传或在实际1315模块网表运行。入口为`python3 workspaces/arch03/scripts/dma16_structural_audit.py --synth-run <fcd综合目录> --summary-sha256 1ee58262e81ba39b92959df1e0b38da99ac7981a25b0bfc2943e469c7042d339 --output <新的JSON>`，只读原工件，不需要启动EDA。

05:52补充：重新核对当前`check_design_mapped.rpt`与综合摘要中的SHA，实际15159行；仅统计Warning行得到LINT-1=4、LINT-2=178、LINT-8=178、LINT-28=4674、LINT-32=4549、LINT-33=502。四个无负载cell来自debug的ndreset/fullreset、AON POR和PLIC flop。178个无负载输入主要出现在综合算术子模块，实际例子有dot64的A[39]/B[39]及DMA地址加法器A[0]；未连接端口涉及238个design，含原平台接口和算术单元未用位。已取得完整报告及模块计数，但查看代表对象不是全部对象审定，不能仅凭告警分类或功能通过自动升级strict_timing_verified。当前只读统计不运行DC、不修改原网表。原始截图`takeover_local/d2_20261109/dma16_lint_inventory.png`、`dma16_lint_examples.png`、`lint_module_inventory.png`留本机。

04:57实际诊断完成：8c包`dma16_timing_audit01`于04:32:14.234559通过，SHA=`2b60daffaf19c85512b95c13024eabe4abe856e9a30764fadcff3fa102f309fa`。原DDC查询的3条网络为`u_e203_subsys_top/core_csr_clk`、`u_e203_subsys_top/hfclk`、`u_e203_subsys_top/u_sirv_aon_top/crossing_clock`。同次冻结平台源码分别追到`clk_core_exu`、HF选择器、`aon_io_lfclk`，均为时钟网络，不是漏计的数据高扇出。PT189个no_clock对象也已精确归入被固定TCK关闭的JTAG DTM和复位同步器；actual mapped.sdc的TCK/TMS/TDI均case=0。禁用弧C46683/p12863/c1992/d202，共61740条，没有l/L/u/U/f标记，原综合无TIM-209/约束违规。仍保持稳定任务模式、理想时钟和布局前库/负载假设；setup裕量非常小，不能宣称物理时钟树、寄生或启动/JTAG工作模式签核。

04:27：新增`dma16_timing_audit`只读阶段，使用原mapped.ddc及同库查询实际高扇出网络，完整保留原文件SHA并复核生产身份；相关63tests通过，尚未上传/执行。不能把查询入口已完成当成高扇出已审核。实际首层PT已无工具错误；其189个no_clock对象为JTAG DTM 186和JTAG复位同步3，禁用弧61740行仍在核查。后续须记录完整原因与实际SDC约束，不能移用历史结论。

本节绑定fcd445f的`dma16_fix_synth01/dma16_synth`，summary SHA256为`1ee58262e81ba39b92959df1e0b38da99ac7981a25b0bfc2943e469c7042d339`。新网表的周期为6.666666000000ns、LF66ns；最差setup **+0.0000290871ns**、hold **+0.00136402ns**，各有2个路径组，锁存器为0。数值非负，但setup裕量很小，不称宽裕。

02:37只读复查原始`check_timing.rpt`、`constraints.rpt`和综合日志：约束报告明确无违规，最终检查包含generated_clocks、loops、no_input_delay、unconstrained_endpoints、pulse_clock_cell_type、no_driving_cell、partial_input_delay；没有TIM-209或自动组合回路切断。**仍有3条高扇出网络，TIM-134说明按1000扇出参与延迟计算**（综合日志两次出现同类告警，不是6个独立网络）。mapped设计还保留LINT无负载及未连接端口等诊断，不能用“没有约束违规”替代全部结构解释。

约束继续为固定任务模式：PLL/分频旁路、启动去抖已稳定、JTAG静态、复位不处于切换；仅四个精确LF计时器同步器首级D例外，无整域屏蔽，无SysMem例外。SysMem全部106位仍有HF输入/输出1ns最大、0ns最小预算、输入转换0.1ns和输出负载0.01。三项LF外部控制输出继续采用其源域1ns/0ns预算，尚不是外部接收器规格验证。

后续实际DMA16 PrimeTime报告将输出`check_timing -verbose`与`report_disable_timing -nosplit`。必须按具体对象解释no_clock、禁用弧及高扇出影响；旧8路189个no_clock对象尚不能直接归因为JTAG，更不能直接复用于新网表。当前保留strict_timing_verified=false，等待这些审核；稳定任务模式报告不包含上电全过程、复位释放或物理签核。赛题按逻辑综合验收面积，不要求物理边长或布局布线，不能把物理签核误列为官方新增前置条件。

## 历史8路时序记录

本记录对应 `c323781` 的 `d3_synth03` 原始映射，以及 `4c8803e` 的 `d3_reports01` 独立报告复核。后者未重新映射，也未修改原运行。摘要 SHA256 为 `41d1a1681b324f84e83a66a48a7701e945bf188d30898ee2ac5f8dfd9c6e784d`。

实际 HF 周期为 6.666666000000 ns，LF 为 66 ns。最差 setup 为 −1.77329254 ns，最差 hold 为 −0.09681505 ns。138 个 SRAM 宏及逐叶面积与总报告核对一致；计分面积、时序和功耗均未通过最终验收。

## 实际路径和拟修正依据

| 项目 | 原平台事实 | 修正范围与验证要求 |
|---|---|---|
| 启动选择跨 LF/HF 路径 | `sirv_aon_wrapper` 将固定低电平 bootrom_n 取反后送入 `sirv_DeglitchShiftRegister`；`T_8 → T_9 → sync → last` 在 LF 上升沿更新，输出 `sync & last`；复位输入在原平台绑 1，寄存器无复位。最差 setup 从 `last_reg` 到 ITCM。 | 任务模式在四个 LF 边沿后要求 `bootrom_deglitch/io_q=1`。增加仅针对此引脚的 case analysis，以及完整任务期间拒绝 0/X 的实际 RTL/门级监视。启动过渡及改变启动引脚不在此稳定任务模式内；尚须新服务器运行确认。 |
| 计时器 LF 同步输入 | 四个 `u_perips_apb_pwm/u_tim0..3/u_in_stage` 含 `r_ls_clk_sync[2:0]`。每个 HF 边沿执行 `{r_ls_clk_sync[1:0], ls_clk_i}`；边沿检测使用级 1 和级 2，级 0 只送级 1。最差 hold 来自 LF 输入到级 0。 | 映射后必须精确找到四个 `r_ls_clk_sync_reg[0]/D`，仅对 `lfextclk → 这些 D` 设置例外。级 0→1、级 1→2 和其他 LF/HF 路径继续检查。数量或名称不符必须失败，不设置整组异步时钟例外。物理亚稳态可靠性及布局不由此证明。 |
| UART 无效发送数据锁存器 | 三个 UART 的组合块默认 `fifo_tx_valid=0`，仅合法 THR 写入赋值 `fifo_tx_data=PWDATA[7:0]`，无效分支缺省值造成 24 个锁存器。`check_timing` 将这 24 个 D 列为未约束端点。`io_generic_fifo` 仅在 `valid_i && !full` 时接收数据。 | 在新 ASIC 平台副本中增加无效 payload 默认值 0，保留所有有效数据与 valid/复位/清空逻辑。原平台不变。新增原模块与修正模块同时接收 APB/串口激励的服务器对照入口；实际通过前不得声称等价或锁存器已消除。 |

## 验证状态

本地 65 项 Python 测试通过，包含四个同步器首级端点的 Tcl 执行检查、拒绝缺少端点、UART 补丁形状约束及已有输入完整性检查。新增启动模式监视器通过 XSim 正例和六类反例；UART 对照 TB 通过语法编译，尚未和服务器真实模块共同执行。

实际服务器 `371316a/d3_uart01` 已于 09:00 通过原 UART/修正版对照：31,464 周期、213 次 APB 写、246 次读、195 个有效发送输入周期、31,269 次空闲 payload 检查、600 个 TX 边沿。原摘要中的 `tx_accepts` 实为 valid 周期计数，不当作成功入队数。摘要 SHA256 `20319adb2a35a5a24f73f96cc8bfadc6ab1ae7574dcc8b7d7c99a499f82c6544`。这不是 CPU 或时序验收。

新 `371316a/d3_synth04` 已于 09:18:43 完成。摘要 SHA256 `504842eb0a8822d9f2915eee5f58bc37fddb2e96411fd2e6ffed8bc8b50eff4`。锁存器为 0，四个精确 timer 同步器首级 D 成功绑定；`check_timing` 不再列出未约束端点。最差 hold 为 +0.00623399 ns，但 setup 仍为 −0.740983 ns，因此严格时序未验收。新配置 ASIC 14 用例 `d3_full02` 于 09:24 启动，UART 实现变化后的完整整机功能仍在重验。

## LF 外部控制输出预算修正

200 条所报最大延迟路径中仅 3 条 setup 违规，端点为 `io_pads_aon_pmu_padrst_o_oval`、`io_pads_aon_pmu_vddpaden_o_oval` 和 `lfxoscen`。前两者余量 −0.74098206 ns，第三者 −0.62426758 ns。实际发射寄存器均由 LF 驱动；原约束却把所有输出都统一赋给 HF，形成 LF 66 ns 发射到 HF 66.66665649 ns 接收的接口预算。

已核对官方平台连线：PMU 控制经 `sirv_aon_wrapper` 直接连到两个 AON pad 输出；`lfxoscen` 来自 `sirv_aon_lclkgen_regs/lfxoscen_dfflrs`，用于晶振使能。新约束将这三个明确命名的输出预算参考改为 LF，仍保留 1 ns 最大、0 ns 最小延迟及原负载；其余输出继续按 HF。每个名字和总数都强制核对，不增加 false path、多周期或整域屏蔽。**这是显式的源时钟域接口预算假设，并非已取得外部接收器时序规格；上电控制过程仍不属于稳定任务模式。** 新约束必须通过新的独立综合验证，不能改写 `d3_synth04` 为通过。

该轮最小已通过 setup 路径只有 +0.00001001 ns，不能据此宣称较大时序裕量。同一次综合报告的总库面积为 3,817,053.008485 µm²；旧配置面积明细继续保留，最终计分明细应使用最终冻结网表重算。

本地新增 Tcl 执行测试核对所有输出恰好在一个域内分别具有最大/最小预算，缺失任一 LF 输出必须失败。门级/功耗入口又补齐平台安装器及工艺绑定的清单和实际文件哈希比较，防止 RTL 相同但平台补丁不同的旧网表被混用。71 项测试中通用运行通过 69 项，另 2 项 native scanner 测试显式指定扫描器后单独通过；4 个修改的 Python 文件通过 3.6 语法检查。上述准备不代表新服务器时序通过。

原报告的三条高扇出警告，以及理想时钟、I/O 预算和 wire/load 模型仍需复核。当前报告不是布局布线、完整启动过程或多角物理签核。不得把“报告收集完成”写成严格时序通过。

## 最新执行回执

`371316a/d3_full02` 于 09:44:45 通过全部 14 个 ASIC CPU 用例，354,816 个实际输出逐项一致，14 个完整任务启动选择检查均通过。每用例窗口 3,890,080 周期、CPU 自报 3,890,176 周期，12 层均零饱和，边界饱和计数分别为 6,336 和 4,554。数值摘要 SHA256 与旧 full01 相同，但这是不同执行：新 `source_inputs.json` SHA256 为 `dcb6ca8bcf70dd64323e3dd3e03a89e9aabd0555a0f496c06c4be6d71c8ce8e`，新日志具有完整任务 boot 模式标记，运行目录和受测提交分别绑定。

`f03d1c9/d3_synth05` 于 09:47:34 启动，实际采用上述 LF 输出约束修正。最新包与修正包的 8 个 RTL 文件、22 个固件/驱动文件、120 个向量文件、16 个测试台文件及 12 个平台准备文件均逐字节一致；约束和功耗收集器的变化单列。该次新综合结果尚待观察，不能从 full02 功能通过推断 setup/hold 通过。

## 端口精确拼写与工具错误策略更正

`d3_synth05` 实际报告约束错误：端口名的小写 `o` 被误写成数字 `0`，三个输出数量守卫失败。逐字符读取映射端口确认索引 23 为 ASCII 111。此轮映射即使完成也不可用于验收、门级或功耗；严格日志检查仍会拒绝错误。旧文件完整保留。

已安装 DC T-2022.03-SP5-5 的 `source(2)` 与 `sh_continue_on_error(3)` 说明默认允许脚本在错误后继续。新的脚本显式设置 `sh_continue_on_error=false`，再加载 SDC，确保名称/数量守卫失败立即返回外层错误处理。原纯 Tcl 测试没有模拟该默认行为，现已补齐；9 项综合相关测试通过，两个文件通过 Python 3.6 语法检查。下一次独立综合仍需实测确认。

## 全部顶层输出名称独立复核

`5754632/d3_synth06` 于 11:01:33 在第二个 LF 输出名称处失败：实际端口为 `io_pads_aon_pmu_vddpaden_o_oval`，前一版漏了 `_o_`。DC 实际以退出码 1 中止，未生成 `mapped.v`，验证了出错即停设置。原失败目录保留。

从 `d3_synth04` 实际综合网表独立提取全部 20 个顶层输出声明名称，本地清单与服务器排序 JSON 的 SHA256 均为 `ac56c79f557b44f5522cc85e22ed1debecc94894799b7f223fe3510e1fc7712d`。测试改用这份独立清单而非手工复写 SDC 名称，并分别验证任一 LF 输出缺失都被拒绝；9 项定向检查和 Python 3.6 语法通过。新修正不改变 RTL、固件或时钟预算，仍须独立服务器综合。
