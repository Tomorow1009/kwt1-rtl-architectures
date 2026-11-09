# 功耗数值导出准备

2026-11-10 01:18：新增`dma16_power_numbers.py`及6项拒绝／精度测试，与既有功耗测试共18项通过。**尚未在实际DMA16功耗报告运行；完整JSON/CSV/中文最终报告生成器仍未完成。**

解析格式依据为服务器实际T-2022.03-SP5-1的历史`d3_power07_h0/asic_power`报告，只用于查看格式，不把旧8路功耗移给新配置。实际字段为`Dynamic_power_unit : 1 Watt`和`Leakage_power_unit : 1 Watt`；`report_power`为Averaged Power、e203_soc_top、9有效数字。表有clock_network、register、combinational、sequential、memory、io_pad、black_box七类，以及Net Switching、Cell Internal、Cell Leakage和Total四个总项。

新工具核对明确1W单位、有限非负9位科学记数、完整唯一分类与总项，并按照显示末位的舍入误差核对行与列合计；缺项不能按零补齐，单位变更需先审核。它读取实际已通过报告收集阶段的summary SHA及每个artifact SHA，拒绝工具错误及文件变化，保留各文件警告出现次数、活动未知值和原始审核清单。

```text
python3 workspaces/arch03/scripts/dma16_power_numbers.py --run <已完成dma16_power目录> --summary-sha256 <核对过的摘要> --output <新JSON文件>
```

输出`reported_power_w`和`raw_reported_energy_j`是未经最终审核的原始数值换算；`system_power_verified=false`、`approved_average_power_w=null`、`approved_energy_j=null`不会因为有数值自动改变。七类PT分类并非架构模块分解，不能把重叠层级相加；最终CPU／TCM／DMA／共享SRAM等模块功耗仍需hierarchy和SRAM报告核对。

后续：gate03全14和12活动完成后先跑实际DMA16首层PT，核查单位、时钟、禁用弧、模型、X及活动映射；用新工具验真实报告格式，再处理12层，补最终冻结配置关联、模块分解、JSON/CSV和中文汇总。当前不改gate03运行包或源文件。
