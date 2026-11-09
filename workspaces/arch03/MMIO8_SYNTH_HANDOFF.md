# 原8路同源加载综合入口

2026-11-09：新增 `scripts/mmio8_synth.py` 与 `server_run.py mmio8_synth`。对照保留原8路MMIO计算驱动，由CPU经原SysMem响应源将输入实际搬入共享SRAM；不存在8路DMA。程序初始ITCM不含任务输入。

采用独立的新安装、源文件清单、linked.ddc及mapped.ddc，不复用旧synth07或DMA16网表。32+32个TCM宏、64共享宏及加速器2大/8小宏，总计138。源接口106位逐位核验；时钟6.666666ns、SS/0.99V/125°C、I/O预算及四条LF同步例外与DMA16一致。

面积保守值计入所有SoC标准单元和加速器宏，只单列已复用的共享/TCM宏，避免新增路由逻辑漏计。报告生成不自动授予时序、面积、门级或功耗验收。TIM-209、缺源端口、宏归属错误、输入变化及旧运行目录均拒绝。

本地34项相关工具测试通过（test_mmio8_synth、test_mmio8_soc、test_dma16_synth）；这是工具契约测试，不是服务器EDA结果。新入口尚未提交打包或服务器执行。已有fcd445f包包含mmio8_soc，可以先做真实ASIC同源吞吐对照；新的mmio8_synth必须经下一已核验独立包上传后运行。

恢复入口：先检查共享锁与现有DMA16作业；不能抢占或并发。后续先mmio8_soc完整14例，再mmio8_synth新session。MMIO8门级和新窗口功耗尚无完成证据，不能把旧BEGIN功耗拼接到新窗口。
