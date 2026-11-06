> 本文保留主工程历史背景；单样本数据及归档证据见 [v1.1.0](../v1.1.0/README.md)。本次结果见 [批量验收](BATCH_KWT1_VERIFICATION.md)，运行路径以 [版本入口](README.md) 为准。

# 验证记录

验证日期：2026-11-06。工程：`D:\IC_compeyition\Fast_coding`。

## 自动测试结果

Icarus Verilog 与 Vivado Simulator 2018.3 均实际编译并执行同一套 testbench，最终输出一致：

```text
PASS: vectors=1103 completed=1112 aborted=6 input_gaps=54018 output_stalls=12530 command_stalls=13
```

- 863 个定向向量、240 个固定种子随机向量。
- 随机向量中 144 个发生饱和，96 个未饱和。
- 所有 shift=0…31 均执行；舍入半值及两侧、正负饱和与精确边界覆盖在定向向量中。
- 6 个中途复位取消任务（MAC 四处、CONVERT、OUTPUT），每次取消后验证新任务。
- 1112 个成功输出包含向量测试和额外协议/复位恢复测试，无重复或遗留结果。
- 两个仿真器生成的 `events.csv` 逐字节相同，任务及复位的发生时间一致。
- 最终仿真时间为 1,424,490 ns；XSim 最终运行日志未出现 WARNING、ERROR 或 Fatal。
- GUI 工程创建脚本另经 Vivado batch 实际执行，创建/打开工程、编译、行为仿真和波形配置均完成，同样到达最终 PASS；工程位于 `sim/vivado_project/dot64_demo.xpr`，记录在 `sim/gui_project_check.log`。本次未通过鼠标操作 GUI。

证据位置：

| 仿真器 | 日志 | 波形 | 事件 |
|---|---|---|---|
| Icarus | `sim/iverilog/simulation.log` | `sim/iverilog/dot64.vcd` | `sim/iverilog/events.csv` |
| Vivado XSim | `sim/xsim/simulation.log` | `sim/xsim/dot64.wdb`、`dot64.wcfg` | `sim/xsim/events.csv` |

## 波形导航示例

以下均为 **ns**；CSV 原始值是 ps。以第一次运行该编号的区间为准，开始/完成时间均指握手上升沿。

| 场景 | case 编号 | 开始 | 完成 | 期望 |
|---|---:|---:|---:|---|
| 正数 | 3 | 4155 | 5825 | result=4096，未饱和 |
| 负数 | 4 | 5845 | 6565 | result=-4096，未饱和 |
| 大数抵消与偏置 | 10 | 13185 | 13905 | result=-1 |
| 正饱和 | 11 | 13925 | 15575 | result=32767，saturated=1 |
| 负饱和 | 12 | 15595 | 16295 | result=-32768，saturated=1 |
| shift=12，-1.5 舍入 | 378 | 486335 | 487085 | result=-2 |
| shift=12，+1.5 舍入 | 379 | 487105 | 488755 | result=2 |

复位发生时间：

| tag | 场景 | 时间 ns |
|---|---|---:|
| 0 | 初始空闲复位 | 10 |
| 10 | MAC，尚未接受输入 | 1415200 |
| 11 | MAC，接受 1 对后 | 1415990 |
| 12 | MAC，接受 32 对后 | 1417090 |
| 13 | MAC，接受 63 对后 | 1418500 |
| 20 | CONVERT，异步取消 | 1419911 |
| 21 | OUTPUT，结果被反压时取消 | 1421420 |

约 1422–1424 μs 可观察排队命令与提前提出的输入。其他区间通过 case_names.txt 和 events.csv 联合定位。

## 实现与验证边界

为兼容本机 Vivado 2018.3，Tcl 脚本路径使用正斜杠；`$readmemh` 文件名通过 `$sformat` 写入 packed 字符缓冲区后传递。数据加载后检查所有输入与答案不存在 X/Z，避免文件加载失败产生假通过。

完整 Vivado 启动时报告本机本地 Tcl Store 不可写，并回退到安装区；这没有阻止工程创建或仿真通过。独立 XSim 运行没有该警告。

本记录证明整数运算、复位和握手在所列测试下通过。尚未执行真实 KWT 精度标定、FPGA 综合/布局布线、频率与资源验收或 E203 集成；100 MHz 是测试激励时钟，不是已验证的硬件时序指标。
