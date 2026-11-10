# 原8路同源加载综合入口

2026-11-10 08:38：1aa `runs/mmio8_source_synth01/mmio8_synth`于08:30:15.335643完成，summary SHA=`0e33c1d045d063829c34e97b7ba10109d446c381c95fa7003449d0bbc6159fc9`已08:37:10.857006独立断言确认。实际6.666666ns，setup=+0.00000905991ns、hold=+0.00131008ns，max/min各2组、0 latch，130大宏＋8小宏；全部SoC标准单元＋加速器SRAM的保守项目预算0.2921861914119108mm²。极小setup余量和正hold只是综合后当前约束结果，尚须约束/例外审核；没有门级、功耗或物理签核结论。最初手抄摘要SHA被严格断言拒绝，改为编号分组逐段读取后通过，原summary/state不变。当前共享服务器正在重审DMA16完整报告38915，原8路门级须继续排队，不能重跑综合或复用旧synth07。

2026-11-10 08:13：新综合已实际启动，1aa工具包`runs/mmio8_source_synth01/mmio8_synth`，driver17074，stage08:11:02.831326开始、08:12:18仍running；完成结果待收。开始前共享锁和EDA进程均为空，后续仍统一排队。这是已批准的原8路同源对照，保持MMIO/CPU搬运、DMA_present=false；不开发8路DMA，不复用旧synth07。以下“未启动”属于历史，不要重复运行。

2026-11-10 02:47：新增门级和功耗入口及本地验证已完成，详见[MMIO8_GATE_POWER_HANDOFF.md](MMIO8_GATE_POWER_HANDOFF.md)。仍未执行新MMIO8综合；共享服务器优先当前DMA16门级/功耗和冻结验证，不擅自并发。新工具本地通过不代表旧“mapped/PPA缺口”已闭环。

2026-11-10 00:58接续：入口已在51bc/a53/525独立包上传并核验；c5的`mmio8_source02`完整14例真实ASIC已通过。**mmio8_synth仍未执行**，当前共享服务器由gate03占用，完成后独立排队。下方“尚未提交打包”仅为最初准备时的历史状态。

2026-11-09：新增 `scripts/mmio8_synth.py` 与 `server_run.py mmio8_synth`。对照保留原8路MMIO计算驱动，由CPU经原SysMem响应源将输入实际搬入共享SRAM；不存在8路DMA。程序初始ITCM不含任务输入。

采用独立的新安装、源文件清单、linked.ddc及mapped.ddc，不复用旧synth07或DMA16网表。32+32个TCM宏、64共享宏及加速器2大/8小宏，总计138。源接口106位逐位核验；时钟6.666666ns、SS/0.99V/125°C、I/O预算及四条LF同步例外与DMA16一致。

面积保守值计入所有SoC标准单元和加速器宏，只单列已复用的共享/TCM宏，避免新增路由逻辑漏计。报告生成不自动授予时序、面积、门级或功耗验收。TIM-209、缺源端口、宏归属错误、输入变化及旧运行目录均拒绝。

本地34项相关工具测试通过（test_mmio8_synth、test_mmio8_soc、test_dma16_synth）；这是工具契约测试，不是服务器EDA结果。新入口尚未提交打包或服务器执行。已有fcd445f包包含mmio8_soc，可以先做真实ASIC同源吞吐对照；新的mmio8_synth必须经下一已核验独立包上传后运行。

恢复入口：先检查共享锁与现有DMA16作业；不能抢占或并发。后续先mmio8_soc完整14例，再mmio8_synth新session。MMIO8门级和新窗口功耗尚无完成证据，不能把旧BEGIN功耗拼接到新窗口。
