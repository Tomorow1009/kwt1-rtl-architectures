# 架构二 SRAM 宏接口适配

2026-11-07：依据例化截图补齐适配器，保持 **2×4096×16 + 8×128×16 = 18 KiB** 单缓冲，计算和加载接口不变。

## 截图确认的端口

截图中的 `*_rtl_top → *_fr_top → 底层宏` 为两级直接转接。设计直接例化底层宏；仅有转接封装不能完成真实仿真。

| 类型 | 宏 | 地址宽度 | 其他端口 |
|---|---|---|---|
| 单端口，本次使用 | RAMSP128X16 / RAMSP4096X16 | 7 / 12 | Q/D[15:0]、CLK、CEN、WEN[15:0]、GWEN、EMA[2:0]、EMAW[1:0]、RET1N |
| 单端口，仅记录 | RAMSP1024X16 / RAMSP2048X16 | 10 / 11 | 同上 |
| 双端口，仅记录 | RAMTP128X16 / RAMTP1024X16 | 7 / 10 | QA[15:0]、CLKA/CENA/AA、CLKB/CENB/WENB[15:0]/AB/DB[15:0]、EMAA/EMAB[2:0]、RET1N、COLLDISN |

双端口为 A 读、B 写的 1R1W，不是两个对称读写口。本次不使用1024、2048或双端口；2048未在此前指南的允许规格列表中。

## 适配行为

`rtl/sram_port.sv` 保留 cs/we 高有效逻辑接口，we=1整字写。非行为后端进入 `rtl/sram_macro_adapter.sv`，AW=7/12选择宏；不支持的AW或READ_LATENCY明确失败。WEN是16位写掩码，与GWEN分别进行极性转换；复位期间片选、写使能均无效。

底层读约定为上升沿采样请求，同一沿后更新Q，接口延迟1拍。READ_LATENCY=1直接返回Q及对应valid；=2同时增加一级数据和valid寄存器。各X bank独立返回valid，原控制器据此选择数据，避免跨bank错位。

复位只取消返回并禁止访问，不清空宏阵列，不把RET1N当复位。仿真written标记随复位清空，检查新任务装载完整性；SYNTHESIS时移除此标记。

## 后端与测试假设

| 后端 | 内容 | 结论范围 |
|---|---|---|
| behavioral（默认） | 原逻辑接口行为模型 | 行为模型回归 |
| pin_mock | 新适配器+自编同名引脚模型 | 端口映射与假设条件下功能 |
| vendor | 新适配器+外部厂商源文件和配置 | 指定模型功能仿真，不等于PPA签核 |

`tb/pin_mock.sv` 是独立编写的测试替代品，不是厂商模型。测试约定：CEN/GWEN/WEN低有效，上升沿同步读写，写入/未选中时Q保持；EMA=0、EMAW=0、RET1N=1。配置来自 `tb/pin_mock_config.json`。**这些常量不是厂商推荐值；截图没有确认极性、读时序或辅助引脚合法配置。**

```powershell
Set-Location D:/IC_compeyition/Fast_coding/arch02
./scripts/run_arch02.ps1 -Backend pin_mock -Mode all -Simulator both
./scripts/run_arch02.ps1 -Backend behavioral -Mode all -Simulator both
# 首层和全部定向/协议测试
./scripts/run_arch02.ps1 -Backend pin_mock -Mode smoke
```

每轮保存独立源码/配置哈希、生成的arch02_sram_config.vh、逐作业日志、CSV/NPZ、周期、软件报告和summary.json。pin_mock额外执行四组容量/延迟组合测试及逐位掩码测试。

## 后续真实宏运行

取得底层模型和时序/配置说明后，分别核实两种容量的控制极性、辅助引脚、读延迟、触发沿及Q行为。当前适配器只支持原生单拍上升沿宏，其他时序需要修改适配器，脚本会拒绝强行套用。

外部vendor.f每行一个Verilog/SystemVerilog源路径，支持绝对路径或相对filelist目录路径，忽略空行及#注释。它不是任意编译器命令文件。include目录通过-VendorInclude数组提供，列入模型所需全部依赖，避免重复定义模块。

外部JSON沿用 `tb/pin_mock_config.json` 的macros字段，按真实资料逐项填写。kind必须为vendor_confirmed，另加非空evidence字段记录文档/模型版本及确认来源。此字段是使用者确认记录，不能代替核实；不能仅改kind就把mock常量当成真实配置。

每种容量必填：cen_low/gwen_low/wen_low为0或1，ema为0…7，emaw为0…3，ret1n为0或1，read_latency=1，clock_edge=posedge。RTL没有隐式厂商默认常量，脚本显式生成配置头文件。

```powershell
./scripts/run_arch02.ps1 -Backend vendor -Mode all -Simulator both `
  -VendorFilelist 'D:/your_sram_library/vendor.f' `
  -SramConfig 'D:/your_sram_library/confirmed_config.json' `
  -VendorInclude 'D:/your_sram_library/include'
```

缺文件/配置立即失败，显式拒绝本项目mock进入vendor源列表，不回退到替代模型。厂商模型若需要额外primitive或特殊编译选项且工具不支持，应保留失败记录。

后续先通过两种容量宏单测，再重跑双工具完整矩阵与协议验证。真实宏功能、SoC绑定、150 MHz、2.25 mm²及功耗验收仍需后续完成。本次不上传GitHub。
