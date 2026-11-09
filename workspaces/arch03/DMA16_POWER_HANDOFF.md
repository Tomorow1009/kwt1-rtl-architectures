# DMA16 完整任务功耗入口交接

更新时间：2026-11-09 19:17:02+08:00。子代理evidence_audit。当前有效计划IMPLEMENTATION_PLAN_DMA16_20261109.md，H0=17:16:08+08:00。主代理要求独立适配，不改已冻结DMA16 RTL/synth、旧soc_power/activity，不操作服务器、不提交Git。

## 已完成

- 只读审查旧soc_power.py、activity.py/activity_fast.py/activity_scan.cpp、旧gate_soc以及POWER_REVIEW_20261109.md。旧power绑定138宏、asic_synth/gate_soc阶段及旧scope，不能直接套新版。
- 新增scripts/dma16_activity.py：SHA256 `8308f970598a9101437546f3001c00639543d46119c2e7d3c580f432538ad5b6`。
- 新增scripts/dma16_power.py：SHA256 `0ad39aaff3e6e4198c9e7ef3018deb0aeb65ac5a989227b0fd49d550ce2e9c90`。
- 新增scripts/test_dma16_power.py：SHA256 `8b67df00825e130dfa51899f72c42a3def644a83aff157ba9da6136e191c14cd`。
- 新10项＋旧power4项＋旧activity2项，共16项测试通过；最后命令在scripts目录：`python -m unittest test_dma16_power test_soc_power test_activity -v`。exec退出0；Python3.6语法通过。新测试用本机g++实际编译原C++扫描器并完整扫描小VCD，验证未知值保留、边界及截断拒绝。这些是夹具/工具契约验证，绝非功耗测量。
- dma16_activity接口与旧一致：`audit_activity(path, window, run, call)`；仍由原native扫描每条记录、完整SHA256，不抽样、不改旧扫描器。独立头部核对SoC顶层SysMem10组106bit、accel/arb/router/shared各唯一层次与声明。保留unknown_value_records，明确不是翻转数、覆盖百分比或可忽略值。
- dma16_power接口：`estimate(cfg, run, gate, expected_sha, case, call)`。旧proc模板exact-once替换为162宏，逐owner守卫、全部SysMem位/方向检查，新增`sh_continue_on_error=false`。LC启动环境沿用已修PT-063方案，仍须真实运行确认。
- 总power/hierarchy/SRAM/verbose/with_boundary_nets、单位、时钟/约束、标注前后/unannotated/来源、实际X配置报告均必需。新增七个不重叠叶分类计数：accel、arb、router、shared、ITCM、DTCM、其余platform；只计覆盖，不把层级相互重叠的功耗简单相加。
- 窗口强制boundary=`first_source_valid_to_final_write_response_ack_with_drain_proof`、四段191616B、period6.666666ns；cycle与real时间一致，finished证明允许晚于最终ACK。末ACK以后CPU读完成状态不延长功耗窗口。
- 独立`summarize_twelve(reports)`需要layer_01—12各一次、同一gate summary/synth summary/firmware SHA；所有layout和activity绑定。当前数值power_w/energy_j/null，汇总不伪造零功耗。审核后正确聚合是sum(E_i)/sum(duration_i)，不是不同长度任务的功耗算术平均。

## 与root/gate的接口约定（待root最终入口实现）

- stage=`dma16_gate`；scope=`dma16_whole_soc_mapped_functional_without_SDF`。
- `dma16_gate.verify_synthesis(synthesis, expected_sha, cfg)`由root实现；本power lazy import此守卫，绝不fallback旧138宏验证器。
- gate summary须有：`cpu_executed=true`、`gate_simulation_verified=true`、`synthesis_run`、`synthesis_summary_sha256`、`firmware_sha256`（firmware manifest）、`source_inputs_sha256`（gate/source_inputs.json）。
- 每case须有：`case`、`outputs=25344`、`layout_sha256`、原dma16_soc.read_window格式`task_window`、新dma16_activity返回`activity`。
- gate source_inputs字典所有实际输入逐hash复验；功耗前后完整VCD hash和header证明复验；真实综合网表/SDC/3个数据库保持原sha。
- gate代码代理dma_feasibility已告知：其新被动MMIO gate proof测试使finished=end+15周期，但窗口end仍末ACK；已有生成器和真实RTL小试，不代表映射门级通过。root负责最终stage/schema及映射probe。
- 根代理已收到上述接口通知；当前未接服务器stage。首个冻结包2bd6b0f不包含这些后续新适配，须另包绑定。

## 必须真实核验的阻断点

1. `PT-063`修复只完成子进程环境准备；原d3_power01有报告但失败。root当前新旧基线gate/power进展须读其实时回执，不从本文件推断完成。启动错误、许可证、read_sdc、宏引用、工具error必须无未处理失败。
2. 源加载顶层I/O已恢复；新网表必须162宏，并由相同门级路径、真实原SysMem source、固件only ITCM boot产生活动。不得用旧07网表证明新DMA16。
3. 标准库泄漏单位1µW、SRAM为1mW。两SRAM各80内部功耗组、4非零条件泄漏组及VDDPE/VDDCE rails；cell_leakage_power=0不能当宏无泄漏。实际PrimeTime单位换算/宏模型/RET1N条件和分量求和必须逐报告审核。
4. 原活动覆盖33.99%是toggle超过门槛的比例，不是只有33.99%网络映射。应单独核对activity_sources中的精确、默认、传播、未标注来源；完整VCD和六大层次事件本身不证明PX注释正确。
5. unknown_value_records按原文件保留；相同ID可出现在多个角色，角色有重叠不能简单求和；它不是翻转计数。PX实际power_x_transition_derate_factor与power_include_initial_x_transitions需留存解释，不能人为替换X或把缺失活动按零功耗。
6. 默认report_power排除外部输入驱动的boundary nets，新入口保存两种总数，不混算。外部PC/源模型不在SoC实例范围内；SoC加载接口自身、E203、TCM、加速器、DMA/仲裁/router、共享SRAM和其他平台均在范围内。
7. 无提取寄生/物理时钟树；原库无wire-load模型，输出负载和source接口预算是明确假设。当前只能布局前估计，不能物理签核；缺导线或其他模型贡献不能写成0。
8. 全12任务各自功耗仍待实跑；首层或旧模型功耗不能替代，也不能把不同版本最佳吞吐、面积和功耗拼一起。数值解析/单位换算应等root传实际新report格式后实现并测试，当前不猜格式自动声称W/J。

## 当前待办与恢复

- root完成dma16_gate入口/实际mapped probe、冻结一致包和真实14case gate，其中12层全窗口VCD；使用新的dma16_activity。
- root报告原基线本次PX工具/单位/设置结果后，按真实报告补数字解析与审核回执；再集成新power stage、逐12层运行。
- 需要可选地增补实际未知节点/宏输出定位；当前仅全局未知记录数量，头部覆盖不能替代位置/模型解释。
- Synopsys总线bit集合和VCS VCD向量范围按当前常规格式严格检查；若真实格式不同会安全失败，先读真实产物再兼容，不能放宽范围完整性。
- 本代理当前无运行任务，没有服务器操作或Git提交，未修改旧power/activity/冻结RTL/synth。压缩后重读AGENTS、CONTEXT_HANDOFF、当前计划、本文件及DMA16_EDA_HANDOFF，并核对root实时进展。
