# 架构二：8 路并行线性加速器与分块 SRAM

2026-11-08 服务器更新：实际厂商 SRAM 的 `ARM_UD_MODEL` 功能分支已在 VCS 完成 12 层 304128 个输出验证；默认时序分支的 hold 报错保留；DC 在单一 RVT SS 0.99V/125°C 角、6.667ns 和暂定 IO 预算下，经增量 hold 修复后 setup/hold 违例均为零，包含 SRAM 的综合面积约 0.127957 mm²。尚非布局布线或全角签核。服务器路径、修复记录和运行方法见 [SERVER_HANDOFF.md](SERVER_HANDOFF.md)。下文原本机验证说明及历史报告应按其运行日期理解。

本目录实现一个语音样本的一层 `Y[99,256] = X[99,64] × W[64,256] + b[256]`。同一硬件依次加载 12 层各自捕获的输入及参数。8 路 MAC 同时计算相邻 8 列，输入 X 广播，权重从 8 个独立 bank 读取。

架构一位于上一级目录，未覆盖。这里直接编译 `../rtl/dot64.sv`、`../rtl/requantize.sv`，复用已经验证的数值和握手逻辑。已增加截图端口对应的宏适配器和 behavioral/pin_mock/vendor 后端；本机可验证行为模型及引脚替代模型，真实宏仍待提供，不代表 E203 SoC 或真实 SRAM 签核。

## 赛题约束与本阶段边界

依据用户提供的指南截图第 3、10～12 页：系统共享 SRAM 为 **512 KB**；内部 SRAM 容量由参赛队根据面积和效率决定，使用指定 16×128、16×1024、16×4096 单/双端口宏组合。目录截图中的 2048×16 未在该指南列表内，本设计不采用。

新增加速器、接口及内部 SRAM 的面积合计上限为 **2.25 mm²**。复用的 E203、共享 SRAM、固定总线/外设不计入该面积预算，但功耗统计需按规则涵盖相应系统部分。统一目标为 **150 MHz**，不新增 DDR 或其他外部存储控制器。

正式性能计时包括输入/参数装载、等待、E203 调度、计算及写回；任务开始前清除缓存有效状态。后续官方答疑要求参赛队自建加载环境，取代指南中“组委会提供环境”的旧表述。

本科数值门槛是在全部官方评测样本上逐层汇总 NRMSE，再取 12 层最大值，要求不超过 3%。本机单样本完整矩阵结果不替代这一验收，不使用测试集调整尺度。

本阶段没有共享 SRAM 总线事务、E203 调度、真实宏时序/面积/功耗模型；独立加载端口的吞吐量不代表赛方 System Bus 或 NICE 带宽。每层使用独立捕获输入，不是端到端量化传播或分类精度验证。

## SRAM、数值与循环组织

| 内容 | 使用量 | 宏组织 | 配置容量 |
|---|---:|---|---:|
| 输入 X | 6336×16 位，12672 B | 2×4096×16 单端口 | 16 KiB |
| 当前 8 列权重 | 512×16 位，1024 B | 8×128×16 单端口，各使用地址 0～63 | 2 KiB |
| 8 个偏置 | 320 位 | 寄存器 | 不计入 SRAM 容量 |
| 8 个结果及饱和标志 | 136 位 | 输出保持寄存器 | 不计入 SRAM 容量 |

SRAM 共 **18 KiB**，另有累加器、控制等寄存器。容量不等于面积，尚不能据此宣称满足 2.25 mm²。

- 输入地址：`row*64+k`。地址小于 4096 访问 X bank 0，否则访问 bank 1 的 `address-4096`。读取返回用有效标记选择对应 bank，支持跨越 4095→4096。
- 权重：`bank=lane`、`address=k`，存放 `W[k,group*8+lane]`；每组复用 99 行后重新装载下一组。
- 循环：group=0…31 → row=0…98 → k=0…63。每次启动 8 个 dot64，连续送入 64 对数，排空读流水线，捕获 8 个输出，再逐项写回。
- 写回顺序：group→row→lane。矩阵位置为 `row*256+group*8+lane`，不能把流中的第 n 个结果直接当作行优先位置 n。
- X/W 为 signed16、小数 12 位；偏置 signed40、小数 24 位；乘积累加 signed40，加偏置总和 signed41；shift=12 时输出小数 12 位。支持每任务 shift=0…31，就近舍入、半值远离零，最后饱和到 signed16。

首版单缓冲，加载与计算不重叠。每个权重 bank 每拍提供 16 位，共 128 位；X 缓存另外提供 16 位，不能把这种内部并行带宽等同于外部加载接口带宽。

## 顶层接口及装载格式

`arch02_linear` 参数 `READ_LATENCY` 默认 1，也验证 2。时钟单域，`rst_n` 低有效异步复位；集成时同步释放，TB 在下降沿释放。

| 接口 | 约定 |
|---|---|
| start_valid/start_ready + shift[4:0] | 上升沿握手开始一层，锁存 shift；一次一个在途任务 |
| load_valid/load_ready + load_data[15:0] | 固定顺序的 16 位装载流；等待时发送方保持 valid/data |
| out_valid/out_ready | 上升沿握手代表接收端完成该项写回；反压时 row/column/result/saturated 均保持 |
| out_row[6:0], out_column[7:0] | 输出的真实矩阵坐标 |
| result signed[15:0], saturated | 饱和后的结果和标志 |
| busy, done, error | busy 覆盖加载至最后写回；done 为最后写回接受后的一个周期脉冲；error 为偏置高位非法的锁存故障，需复位恢复 |

装载流严格依次包含：

1. 6336 个 X 字，行优先。
2. 对每个 group，512 个 W 字，k 外层、lane 内层。
3. 紧接该组 24 个偏置字，lane 外层，每个偏置低位优先拆成 3×16 位。

偏置按 40 位补码编码，第 3 字的高 8 位必须为零（负数也不能把该字高 8 位填成 FF）。一个 group 共 536 字，一层共 **23488 字**。偏置字节传输包含填充，因此输入接口总传输 46976 B；输出 result 数据为 50688 B，不含接口地址/控制开销。

`load.hex` 每行 4 个十六进制字符，23488 行。`total.hex`/`result.hex`/`saturated.hex` 各 25344 行，按矩阵行优先存放，分别为 11/4/1 个字符；total 仅低 41 位有效。`layout.json` 记录 shift、计数及文件哈希。原 NPZ 不转置、不修改；导出程序对 bank 布局和偏置拆装再做独立回读检查。

复位取消进行中的任务，清空状态和流水线有效位，不要求物理 SRAM 的内容复位。下一任务必须重新加载全部输入及每组权重/偏置；行为模型额外清空“已写”检查标记以捕获未初始化读取。复位前已经写回的部分结果属于被取消任务，系统级调用方应丢弃。

缺失加载数据时硬件等待，不自行产生旧结果；TB 的无进展 watchdog 报错。发送方必须提供规定字数。SRAM 原始接口没有独立的 ready，适配器需保证声明的固定读延迟。

## 源码和运行

| 位置 | 用途 |
|---|---|
| rtl/arch02_linear.sv | 分块调度、10 个存储端口、8 路 MAC、结果保持与写回 |
| rtl/sram_port.sv | 中性同步存储接口，选择行为模型或宏适配器 |
| rtl/sram_macro_adapter.sv | 128/4096 宏命名端口连接、配置极性及读返回对齐 |
| tb/pin_mock.sv、tb/pin_mock_config.json | 自编引脚替代模型和显式测试假设，不是厂商模型 |
| tb/tb_sram_adapter.sv | 容量/读延迟组合及掩码、保持单测 |
| tb/sram_model.sv | 行为 SRAM，读延迟及未初始化读取检查，不是工艺宏模型 |
| tb/tb_arch02.sv | 完整矩阵、显式写回存储、反压、复位、连续任务和周期统计 |
| tb/tb_lanes.sv | 原 1103 组数值向量在每个 lane 上验证 |
| scripts/data.py、scripts/run.py | NPZ 验证、导出、双仿真器调度、矩阵重建、故障测试 |

需要 Python/NumPy、Icarus、Vivado XSim；默认从 PATH 查找工具。工程原 `vectors` 由 `../scripts/gen_vectors.py` 生成，使用现有 1103 组基线。运行不需要 TensorFlow 或重新提取模型。

```powershell
Set-Location D:\IC_compeyition\Fast_coding\arch02
# 默认软件全量 + 双仿真器 12 层 + 定向/故障/数值回归
.\scripts\run_arch02.ps1
# 新增引脚替代模型：完整矩阵和协议回归
.\scripts\run_arch02.ps1 -Backend pin_mock -Mode all -Simulator both
# 双工具首层及完整定向回归；不能声称12层RTL通过
.\scripts\run_arch02.ps1 -Mode smoke
# 仅完整软件校验与导出
.\scripts\run_arch02.ps1 -Mode software
# 可显式指定工具/数据
.\scripts\run_arch02.ps1 -Simulator both -VivadoBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'
# 数据缺省为上一级 KWT1/model_data/outputs/real_sample_001
# 可用 -DataRoot 指定其他满足固定格式的完整 NPZ 根目录
```

每次创建 `sim/<运行编号>`，原资料和历史运行不覆盖。每个仿真器对每个测试顶层/延迟配置构建一次，逐层复用快照；XSim 使用 options 文件传参。Icarus 和 XSim 独立并行运行。日志必须有预期 PASS，并拒绝 Fatal/Error；特别处理 XSim 2018.3 在 `$fatal` 后仍可能返回退出码 0 的行为。

`software.json` 保存原 NPZ 身份和逐层误差，`summary.json` 保存源码/向量哈希、作业结果与周期；CSV 按握手记录 `matrix_index,total,result,saturated`，NPZ 重建为 99×256。TB 每次握手也写入显式结果存储数组，并在 done 后核对全部单元。输出流与文件均不回馈 DUT 运算。

## 验证覆盖与周期解释

默认读延迟 1 拍：两套分别验证 12 层各 25344 输出，总计 304128 个真实输出。定向矩阵验证不同 lane 权重/偏置、极值、饱和与舍入；2 拍配置结合随机空拍/反压，运行两个不同矩阵，不复位地从 shift=11 切换至 12。

复位探针覆盖：空闲、输入装载中、权重装载中、偏置拆装中、MAC 启动前、MAC 中途、转换阶段、输出反压、到达输入 bank 1 后的输出反压。每次确认任务取消、接口复位禁止握手，再重新启动。完整任务必须命中 X 地址 4095/4096、每路 64 次接收、全部矩阵坐标且无重复。

故障测试使用运行目录中的临时副本，覆盖非法偏置高位、缺文件、HEX 截断、加载中断超时、错误参考和未初始化 SRAM 读取。后两者用于测试 scoreboard 和模型保护，不是硬件运行输入。

周期分项：load 包含加载空拍；compute 包含启动、SRAM 延迟、MAC 及转换/捕获；write 包含反压。`load_wait` 和 `write_wait` 是前述分项的子集，不应再次加入 total；`mac_updates` 是 8 路并行更新拍数，不是乘加总次数。

无空拍/反压且读延迟 1 拍时，一层参考周期为加载 23488、计算/控制 215424、写回 25344，合计 264256；有效 MAC 更新 202752 拍。以目标 150 MHz 换算约 1.7617 ms，**只是模型条件下换算，不是已验证工作频率或正式比赛吞吐量**。尚未包含共享 SRAM 入库、E203 调度、总线仲裁和真实写响应等成本。

## 波形与宏接入

主要波形保存在 `rounding_l2.vcd` 或 `rounding_l2.wdb/.wcfg`，包含复位、连续任务和 2 拍延迟。全量真实矩阵默认不记录信号波形。

```tcl
open_wave_database D:/IC_compeyition/Fast_coding/arch02/sim/<运行编号>/xsim/rounding_l2.wdb
open_wave_config D:/IC_compeyition/Fast_coding/arch02/sim/<运行编号>/xsim/rounding_l2.wcfg
```

观察 state、group_index、row_index、issued、x_addr、x_v、w_v、feed、load_ready 和 out_valid/out_ready；result 与偏置等数据按 Signed Decimal 显示。WRITE 阶段反压时结果和坐标不变；RUN 仅在同步 SRAM 返回有效时给 MAC 送数。phase 数值：IDLE=0、LOAD_X=1、LOAD_W=2、LOAD_B=3、LAUNCH=4、RUN=5、WRITE=6、FAULT=7。

真实宏资料清单和接入流程见 [SRAM_ADAPTER.md](SRAM_ADAPTER.md)。本阶段不自动上传 GitHub；实际验收结果见 [VERIFICATION.md](VERIFICATION.md)。

本次宏适配和引脚替代模型验收见 [SRAM_VERIFICATION.md](SRAM_VERIFICATION.md)；原 VERIFICATION.md 保留为历史行为模型报告。
