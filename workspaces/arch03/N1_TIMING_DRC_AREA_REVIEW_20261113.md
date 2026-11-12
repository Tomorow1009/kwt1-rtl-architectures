# N1 原综合时序、DRC与面积有限审阅

观察截止 **2026-11-13 06:16:45（北京时间）**，尚未授予时序或 N1 阶段验收。受查生产仍为9305c6948c764fed01fe86b20bb3db94170299ab，原综合摘要cc7f26115f3158fb69f4575f28b5dfde4dd8e5b3aeefda2a927928ad8418db31，mapped SHA59c75a4930d82a417e8ac77386751f9cb53c7813964e329729ed9f2a3bfdc82e。

小型证据见 [N1_TIMING_DRC_AREA_REVIEW_20261113.json](../../handoff/team/evidence/N1_TIMING_DRC_AREA_REVIEW_20261113.json)，包含实际查询/截图哈希、全部七类面积数值与被审源码身份。本次只读原报告和源码，没有新综合、改变原文件或放宽约束。

## 已读取的实际结果

| 项目 | 本轮事实 |
|---|---|
| check_timing | 06:07:28，原文件509B，SHA `f3b968241c0211cd20c32496ea3366222309b49ae3ccf572b2150a2e46d7d56c`。全文含generated_clocks、loops、no_input_delay、unconstrained_endpoints、pulse_clock_cell_type、no_driving_cell、partial_input_delay检查；只有一条TIM-134，无其他warning/error |
| 高扇出 | 实际为 **4条**，工具使用1000扇出数估计其延迟。当前名字尚未读取，不能套用B0的3条平台时钟解释 |
| mapped.sdc | 06:08:25，SHA `773e089a556e68a74ac7ad46cf02e9c62a709fdd8974a6e40cd31bd48137af1b`。2个create_clock、12个case-analysis、1条false-path；实际例外仅lfextclk到tim0…3首级同步器D |
| 面积 | 06:09:37，348866个leaf、220宏；全部SoC标准单元加92个内部宏的项目保守上界 **0.9511486879005002 mm²**，限值1.20。库几何依据状态为`identical_library_geometry_proof_reused`；官方最终面积归属未确认 |
| 全部约束违例 | 06:15:40，完整报告253B。实际SHA先与上述固定summary的`artifacts[constraints.rpt]`断言相等；clean声明1个、VIOLATED=0、errors=0，完整正文明确无违反 |
| 实际模式与SysMem预算 | 06:16:45，12个case值均与声明一致；HF输入max1/min0各35位、transition max/min0.1各35位；输出load0.01及HF max1/min0各71位。共106个方向位、353条对应约束行 |

原DC观察setup=+0.0000510216 ns、hold=+0.00153732 ns，max/min各2个路径组、0锁存、无组合环、约束报告明确无违例。它们是当前声明条件的数值证据；极小正裕量不等于完成时序范围审核或物理裕量充足。

面积叶求和为4473365.18786784 µm²，DC报告值为4473365.187497 µm²，差0.00037084 µm²，在原工具规定的求和容差内。两种来源分别保留，不改原数。七组打印列仅为标准单元与SRAM，不含逻辑常量的数量，不能将其数量小计直接当全部leaf数。

## 约束范围与精确周期

N1调用与B0/R4相同的[soc_synth.py](scripts/soc_synth.py)约束生成器；原始task_mode.sdc由[n1_gate.verify_synthesis](scripts/n1_gate.py)逐字核验。允许的声明仍限于SS、0.99 V、125°C稳定任务模式：HF=6.666666 ns、LF=66 ns、两者uncertainty=0.1 ns，固定boot/PLL旁路、静态JTAG、稳定复位和启动选择。

精确例外只有`lfextclk`到原`u_perips_apb_pwm/u_tim0..3/u_in_stage/r_ls_clk_sync_reg[0]/D`四个首级D；下游stage1/2仍计时。本次原SDC选择性扫描未见multicycle、clock groups、user disable-timing、clock-gating放宽、ideal-network或propagated-clock命令。12个case实际为JTAG TCK/TMS/TDI=0、外部复位和低有效唤醒输入=1、三个dbgmode_n=1、bootrom_n=0、bootrom_deglitch/io_q=1、pllbypass=1、plloutdivby1=1。106个SysMem位的实际预算也已核对，详见上表。源码保持三个AON输出按LF计时，其他输出按HF；未在本次SysMem查询中额外审三个LF输出的序列化行。不扩大为活动JTAG、PLL切换、启动/复位释放全过程或布局后签核。

原DC实际metrics是6.666666 ns；`write_sdc`把HF周期/下降沿写为6.66667/3.33333 ns，分别相差+4 fs/−3 fs。无需因此重综合。[n1_power.py](scripts/n1_power.py)已有精确副本流程：先核原SDC和summary身份，用[restore_clock](scripts/icb32_delivery_sdc.py)只恢复该HF行到6.666666/3.333333，其余字节保持，另存`mapped.precise.sdc`与`power_clock_input.json`。PT导入后实际读回HF/LF，Tcl以1e−12容差检查，Python再按Decimal严格检查`power_clock.txt`。本次只确认实现存在；实际PT回执尚未生成，不把计划值当实测值。

## 批次结束后的最小必要工作

1. 原批次结束且原共享锁实际释放后，运行一次 **当前N1的timing_audit**，查清四条高扇出网。该工具只读原DDC、列threshold1000对象和模块接口，不重编译、不授予STA通过。第四条若属于新增数据/使能或未解释的时钟，按实际对象诊断，不能自动豁免。
2. 原constraints完整SHA、clean声明和无违反已核对，**不运行零目标drc_audit**。该工具即使query_targets为空也会启动DC，无法补充新的DRC事实。只有后续出现真实违例、未识别报告或必要驱动疑问时才运行；不沿用B0旧U号。
3. 完成当前同网表gate14并保存任务模式观察。正常N1 L01功耗已会生成`check_timing -verbose`、`report_disable_timing -nosplit`和时钟报告，可顺带核全部no_clock对象、禁弧原因及精确周期。复用这些必要作业，不另开PT重复获取。旧B0/R4的no_clock或禁弧数量不转移给N1。

面积解析对每个唯一leaf、物理库正面积、220宏归属和整机求和已有检查。保守预算计入所有SoC标准单元与92个新增小宏，仅排除ITCM32、DTCM32、共享64个复用大宏；因此DMA、router、仲裁、FIFO、IRQ等逻辑不会因层级归属漏计。核对本轮清单和原库几何身份后，可使用这个小于1.20 mm²的上界，无需为了细分出更小数字重综合。

本轮有限静态报告查询结束，不再扩展逐门或重复清单。原批次和共享锁释放后顺序为一次当前四网timing_audit，再同网表gate14，随后正常活动/功耗作业。`n1_timing_audit`、`n1_drc_audit`和最终报告收集器均明确保留`strict_timing_verified=false`；runner PASS只代表该工具完成。最终独立审阅还须绑定实际四条高扇出范围、同网表功能以及完整时序/禁弧范围，方可接受与B0相同的声明条件。此文不批准进入N2。
