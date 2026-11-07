# 架构二 SRAM 接口适配验收报告

日期：2026-11-07。本机实际执行，最终结论：**宏接口适配及替代模型验证通过，原行为后端兼容回归通过**。

本次仅有厂商封装截图，没有真实底层功能模型。以下 pin_mock 结果不能称为真实 SRAM 验证通过，也不代表 SoC、150 MHz 时序、面积或功耗签核。

## 变更与数据范围

新增 128/4096 单端口宏适配器，16 位写掩码、显式极性/辅助引脚配置、复位访问门控和 1/2 拍返回对齐。新增引脚替代模型、单测和三后端入口，保持 18 KiB 单缓冲、8 路 MAC、加载及写回协议。

原 dot64、requantize、arch02_linear 与 20261106_223645_c6de2c8e 基线哈希完全相同；详见 acceptance.json。未修改原 NPZ、历史报告和架构一，未上传 GitHub。

数据为 real_sample_001 的12层完整NPZ，每层独立输入 X[99,64]、W[64,256]、b[256]，每层25344输出。每个后端、每个仿真器均验证同一组304128个独立输出，不能将重复验证次数相加称为更多模型覆盖。软件参考全部304128输出精确一致，浮点误差不作为官方模型准确率验收。

## 本机运行证据

- pin_mock：[`20261107_002446_22036186`](sim/20261107_002446_22036186/summary.json)
- behavioral：[`20261107_002928_c5a28cf3`](sim/20261107_002928_c5a28cf3/summary.json)
- [本阶段综合验收](sim/20261107_002446_22036186/acceptance.json)
- [软件报告与NPZ身份](sim/20261107_002446_22036186/software.json)
- [后端配置与非法参数拒绝测试](sim/20261107_002446_22036186/backend_guards/results.json)

每轮保存输入/源码哈希、逐层日志、实际输出CSV及重建NPZ。源码在运行结束及最终归档时再次核验，没有运行中修改。生成配置头文件在各仿真器工作目录下，pin_mock 使用显式假设配置。

## 逐层结果

| 层 | pin_mock Icarus | pin_mock XSim | behavioral Icarus | behavioral XSim |
|---|---|---|---|---|
| 1 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 2 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 3 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 4 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 5 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 6 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 7 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 8 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 9 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 10 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 11 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 12 | 25344 / PASS | 25344 / PASS | 25344 / PASS | 25344 / PASS |
| 合计 | 304128 / PASS | 304128 / PASS | 304128 / PASS | 304128 / PASS |

以上每项都比较41位total、16位result及saturated，并重建99×256输出矩阵，检查坐标不遗漏、不重复、每路每点积接收64对输入，以及输入地址4095→4096跨bank。

## 定向与异常检查

两个后端的两套仿真器均通过：

- 128/4096容量×1/2拍延迟，共4组适配器读写单测：首尾地址、连续读、读写切换、空拍、复位取消返回。
- 3次额外完整定向矩阵，共76032输出；含8路不同权重/偏置、极值、舍入、饱和、随机加载空拍和输出反压。
- 2拍读延迟下连续两任务不复位切换输入/参数及shift，9个复位探针全部通过。
- 原1103组数值向量在8路上验证，共8824次lane检查。
- 6类负向用例按预期失败：偏置填充错误、缺文件、截断、加载超时、错误参考、未初始化读。

pin_mock两套工具另通过逐位写掩码、写入Q保持、未选中Q保持与禁止写入测试。配置/后端8项拒绝测试通过：缺选项、缺源文件、混入mock、未确认配置、EMA越界、不支持原生延迟、非法AW、非法READ_LATENCY。前6项检查Python入口，后2项在Icarus检查RTL报错；这些负向测试使用临时文件，不修改输入资料。

## 周期与波形

两种后端、两套工具、全部真实层的1拍无暂停作业均为：加载23488周期，计算/控制215424周期，写回25344周期，总计 **264256周期/层**；其中有效8路MAC更新202752周期。与原行为模型相同，不包含真实总线/E203条件，不能作为正式比赛性能或150 MHz达标证据。

完整真实矩阵默认不录制全量信号。代表波形：

- [Icarus 2拍矩阵/复位波形](sim/20261107_002446_22036186/iverilog/rounding_l2.vcd)
- [XSim 2拍矩阵波形](sim/20261107_002446_22036186/xsim/rounding_l2.wdb)
- [XSim 宏引脚及返回流水线波形](sim/20261107_002446_22036186/xsim/adapter_pins.wdb)

```tcl
open_wave_database D:/IC_compeyition/Fast_coding/arch02/sim/20261107_002446_22036186/xsim/adapter_pins.wdb
open_wave_config D:/IC_compeyition/Fast_coding/arch02/sim/20261107_002446_22036186/xsim/adapter_pins.wcfg
```

宏引脚波形由额外重跑4组单测录制，不重复计入独立覆盖。a/b分别为128容量的1/2拍单测，c/d为4096容量；记录了全部子层次。关注cs/we、cen/gwen/wen、macro_q、valid_q、latency2.data_q/valid_d与rvalid。矩阵波形使用rounding_l2.wcfg打开，检查x_v/w_v/feed对齐及反压期间输出稳定。

## 复现与后续

```powershell
Set-Location D:/IC_compeyition/Fast_coding/arch02
./scripts/run_arch02.ps1 -Backend pin_mock -Mode all -Simulator both
./scripts/run_arch02.ps1 -Backend behavioral -Mode all -Simulator both
```

[适配与真实模型配置说明](SRAM_ADAPTER.md)记录全部已确认端口及未确认项。真实宏必须单独提供底层模型和已确认配置，再使用vendor后端；不会自动回退到替代模型。本次EMA/EMAW/RET1N等假设不应直接用于流片。
