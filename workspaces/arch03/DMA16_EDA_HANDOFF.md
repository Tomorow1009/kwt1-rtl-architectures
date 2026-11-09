# DMA16 EDA 入口交接

更新时间：2026-11-09 18:48:09+08:00。子代理evidence_audit。有效计划IMPLEMENTATION_PLAN_DMA16_20261109.md；H0=17:16:08+08:00。

## 当前完成与交付（优先于下方历史设计记录）

- 已新增 scripts/dma16_synth.py，接口 `synth(cfg, run, platform_source, call)`；root已在server_run接入此stage。SHA256 `94f7c46bf01dbd1b7b14e1ec81b4dcd6e6de649b710fc4af8bbaaef4aa5dc582`。
- 已新增 scripts/test_dma16_synth.py，SHA256 `3218d44ec373c88df9cbbe59fb394d4328feb0071a712cd03d9eb620685df4ab`。新14项＋复用原soc_synth的9项，共23项离线测试通过，2026-11-09 18:48:09前完成，exec退出0。命令：在scripts目录执行 `python -m unittest test_dma16_synth test_soc_synth -v`。Python3.6语法检查通过。测试生成的负slack/面积为夹具，不是EDA报告。
- 独立install_dma16＋dma16_soc.source_list＋TCM RTL；新的链接DDC，拒绝已有platform/libs/linked.ddc/mapped.v/summary的旧目录。源/库/准备脚本/全部头文件hash绑定；库工具错误、空DB、DC错误、标记缺失、输入变化均拒绝。
- 源顶层ANSI与映射后non-ANSI均独立核查原SysMem 10组方向/宽度/位编号。Tcl在链接、SDC、映射后验证全部106bit（35输入、71输出）且归入all_inputs/all_outputs。与HF同预算max1ns/min0ns/transition0.1/load0.01；原三个LF输出例外保持；不加falsepath，仅原4个timer首级D例外。
- 宏逐owner核对：ITCM32大/DTCM32大/shared64大/accel2大32小；合计162宏、1048KiB。功能RAM分支拒绝；只对真实宏dont_touch。area_inventory逐叶去重求和并与工具总计核对，实际宏area与固定Liberty对比，缺arb/router/shared接口标准单元均拒绝。
- 面积输出两值：known_added含accelerator（含DMA/FIFO/core/内部SRAM）、arb、router、shared接口stdcells；conservative_budget再加所有其余整机stdcells，含无法直接归属的新IRQ OR/glue，保守上界不漏算新增逻辑。TCM64和shared64宏单列复用面积，不混入新增预算。官方scoring_area仍null/false，需审核确切归属。
- 复用1276标准单元＋两SRAM的LEF单位交叉校核，要求当前Liberty SHA与原证据一致，并重新核对两宏宽×高。仅复用几何单位证明，绝不复制旧8小宏数或旧面积。运行包必须包含 `handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json`；root已知要加入白名单。
- 映射后输出 `mapped_probe_inventory.tsv`，列DMA/core模块端口、core_done_q/fifo_count_q/half_q/load_word_q/error_q别名实际存在数量与路径。无大面积donttouch保别名；gate monitor须以本次映射实际模块端口/信号调整。
- 返回固定 `reports_ready_review_required`；timing_verified/scoring_area_verified/gate_simulation_verified/system_power_verified/physical_signoff均false。即使slack非负也只给informational布尔。新14测试明确负setup不会升级为验收成功。

## 未完成、风险和下一步

1. 本子代理没有运行服务器DC/LC，尚无DMA16真实时序/面积/映射网表；本机没有完整固定平台拷贝，ANSI解析已用实际installer.patch_soc输出夹具验证，真实安装仍由root服务器流程核对。
2. Synopsys端口集合审计按总线逐bit对象进行；若实际工具API格式不同会安全停止，需读取实际端口对象而非放松106bit/方向/全时序覆盖要求。
3. 普通compile可能移除内部别名。新观测报告仅供定位，不保证现有RTL层次monitor可直接用于gate；勿为了测试大量dont_touch。
4. 工艺角/时序预算是假设，全部结构、未约束路径、门控、启动/复位和CDC仍需审核；布局前功耗不完整时仍不能写低功耗或能耗成绩。
5. root负责不可变打包、服务器stage、核验。不要拿旧synth07网表验证新硬件。旧soc_synth.py、asic_link.py未修改，生产DMA16引擎仍冻结。
6. 当前无本代理运行中任务、未操作服务器、未Git提交。压缩后先读AGENTS/CONTEXT_HANDOFF/当前计划/本交接，再核对root最新消息。

## 实施时识别并纠正的路径

- 最初parser草案只适配non-ANSI；读取install_dma16实际patch后，在运行前改为ANSI和non-ANSI双解析，并增加真实patch产物测试。
- 同一DC proc内source约束与映射后审计共享Tcl数组，草案array set空列表不会清旧键；运行前加unset，测试同一解释器二次guard通过。
- 用已有成熟soc_synth报告模板做exact-once替换来复用精确CDC/报告逻辑；模板内容变化立即失败，避免静默沿用138旧宏。它读的是本stage新linked.ddc，没有旧DDC恢复入口。

## 历史任务与设计记录

主代理最新任务：新增独立scripts/dma16_synth.py，不改旧soc_synth/asic_link；复用库、约束、fail-fast，install_dma16安装新SoC；主代理将提供dma16_soc.source_list()无参Path列表。接口synth(cfg,run,platform_source,call)。统计130大+32小=162宏、1048KiB；DMA/arb/router/加速器全部新增面积，TCM/共享等单列；原SysMem新增顶层10组端口同HF预算，独立数量/方向/位宽核查，不新加falsepath。只reports_ready_review_required，不自动timing_verified。不得服务器运行或git提交。

已读取：soc_synth.py全文件、asic_link.py、install_dma16.py、test_soc_synth.py、memory_technology.py。dma16_soc.py尚未创建，需在synth执行时lazy import，离线测试不依赖其存在。尚未写dma16_synth.py或测试。

设计决定：复用asic_link.libraries的固定标准库/实际SRAM Liberty校验与DB编译；独立新链接Tcl，fail-fast+162宏逐owner核对+拒绝功能存储分支；复用soc_synth.constraints/mapped_exceptions和报告模板但针对162宏修改并添加实际SysMem端口清单报告。源哈希绑定新安装器/入口/数值/RTL/工艺/时序文件。只对真实宏dont_touch，普通DC compile保留层级但内部别名可能优化，需报告实际可观察性风险，不为TB保留大量donttouch。

引擎生产RTL已冻结，全部局部验证通过，见DMA16_ENGINE_HANDOFF.md；不要因EDA入口开发改它。最终engine SHA=4270345c39477220831ef4fda8227dc4f3c8d6df71f66234bfc0ec63b2df9f53。无本代理未结束的仿真或服务器任务。

接下来：实现严格面积归属和SysMem约束生成；新增离线测试实际执行Tcl集合预算、缺端口/错方向/错误库拒绝、负setup结果保持未验收、162宏面积计数/漏计arbiter拒绝；检查Python3.6语法，执行本地unittest。更新本交接后给root代码与测试回执。
