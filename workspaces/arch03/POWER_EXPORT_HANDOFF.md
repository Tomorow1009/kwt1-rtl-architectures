# 功耗数值导出准备

2026-11-10 01:44：数值提取、模块分解和JSON/CSV/中文证据导出工具已实现，**30项相关测试通过，尚未在实际DMA16功耗报告执行**。生产RTL/固件、当前gate03运行包均未改变。此前01:18的18测试及b2afb88仅包含原始分类功耗提取；本次新增实际层级格式处理与汇总器。

解析格式依据为服务器实际T-2022.03-SP5-1的历史`d3_power07_h0/asic_power`报告，只用于查看格式，不把旧8路功耗移给新配置。实际字段为`Dynamic_power_unit : 1 Watt`和`Leakage_power_unit : 1 Watt`；`report_power`为Averaged Power、e203_soc_top、9有效数字。表有clock_network、register、combinational、sequential、memory、io_pad、black_box七类，以及Net Switching、Cell Internal、Cell Leakage和Total四个总项。

新工具核对明确1W单位、有限非负9位科学记数、完整唯一分类与总项，并按照显示末位的舍入误差核对行与列合计；缺项不能按零补齐，单位变更需先审核。它读取实际已通过报告收集阶段的summary SHA及每个artifact SHA，拒绝工具错误及文件变化，保留各文件警告出现次数、活动未知值和原始审核清单。

```text
python3 workspaces/arch03/scripts/dma16_power_numbers.py --run <已完成dma16_power目录> --summary-sha256 <核对过的摘要> --output <新JSON文件>
```

输出`reported_power_w`和`raw_reported_energy_j`是未经最终审核的原始数值换算；`system_power_verified=false`、`approved_average_power_w=null`、`approved_energy_j=null`不会因为有数值自动改变。七类PT分类并非架构模块分解。

已只读核对实际旧PT层级格式：`power_hierarchy.rpt`即使请求8位小数仍显示3位有效数字，零值显示`0.000`。新解析器保留显示舍入误差，不冒称高精度。CPU顶层包含ITCM/DTCM，分解时减去完整TCM包装子树；加速器、共享SRAM、DMA仲裁、DMA路由互斥，其余平台由总值减去这些互斥范围。缺失、重名、错误嵌套及负残差均拒绝。SRAM独立逐单元检查162宏（ITCM32、DTCM32、shared64、accelerator34），拒绝黑盒属性；SRAM已经包含在模块功耗内，不重复加总。模型与活动审核仍未完成。

新增`dma16_report.py`读取显式运行索引，核对阶段状态、摘要和文件哈希、ASIC/综合RTL与平台逐文件一致、同固件/布局/门级/波形绑定；导出`report.json`、`tasks.csv`、`modules.csv`、`summary.csv`、`report_zh.md`及哈希回执。12层能耗逐窗口累加，总平均功耗按总能量除总时长计算。缺一层时总功耗与总能耗保持null；未审核字段不会自动变成通过。

入口：`python3 workspaces/arch03/scripts/dma16_report.py --request <新运行索引JSON> --output <不存在的报告目录>`。索引schema为`dma16-report-request-v1`，必需`asic`/`synthesis`/`gate`各含`run`及已核对的`sha256`；可选`power`为同结构数组、`batch`为目录及state.json的SHA、`history`为`status`（failed/stopped/unverified）、`description`、`run`数组。batch缺省明确记未运行；提供时必须完整1200真实ASIC任务，并逐例重新核对全部捕获输出与冻结契约，不能用旧37组或只统计回执数量。

后续：提交并独立打包新工具；gate03全14和12活动完成后先跑实际DMA16首层PT，核查单位、时钟、禁用弧、模型、X及活动映射；用新工具验真实格式，再处理12层、最终1200与完整报告。当前只完成工具及合成测试，不是实际PPA/最终交付完成。
