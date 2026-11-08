# 架构三：E203 System Bus 集成

状态：本地 ICB/SRAM/矩阵回归与固件构建已完成；服务器上传受 FTP 421 连接限制阻塞。
**当前没有 E203 执行通过、服务器 VCS/DC、综合后功能或官方 600 样本验收记录。**
这是开发中的架构三，不替换架构二或历史快照。

## 基线与设计

- 团队基线：main `8aa230695668458673b370bf85f8a397fc507a34`。
- 计算核心直接引用 `../arch02`：8 路 MAC、16 位输入/权重、40 位偏置、41 位求和、移位舍入及饱和。
- 官方服务器平台：`/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master`。
- 163 个 RTL/header、原测试台及文件列表的规范化 SHA256：`ee8bfec8d1e192a974be81479ef8a01793de3e59c2e2f8769886e8e86143e56e`。
- 已只读核对：32 位 ICB 地址/数据，4 位写掩码；存储子系统 O5 示例窗口从 `0x40000000` 开始；O4 SysMem 原为空应答；ITCM/DTCM 基地址分别为 `0x80000000`/`0x90000000`，各 256 KiB。
- 集成脚本在新目录复制并修改固定平台。原目录、历史运行及其中的临时编辑文件不修改。脚本尚未在服务器执行，补丁上下文仍须实际验证。

新增独立共享 SRAM 地址为 `0xA0000000–0xA007FFFF`，512 KiB，由 32 组双 `4096×16` 宏组成。
这属于团队补齐的**新平台映射**，不是声称组委会原有实现。保留原两块 TCM；赛事对额外共享存储的兼容性尚未确认。
加速器内部仍为原架构二 8 个 `128×16`、2 个 `4096×16` 宏。

## MMIO 接口

基地址 `0x40000000`，前 4 KiB 有效。单笔在途，命令握手时发生副作用，应答在反压期间保持。
控制写入只支持对齐 32 位、全部四字节有效；不支持的访问返回 ICB error 并锁存错误。

| 偏移 | 寄存器 | 语义 |
|---|---|---|
| 0x00 | ID | 只读 `0x4B575403` |
| 0x04 | CONTROL | 写 1 启动；写 2 中止/复位任务与计数、清除错误；不清除 SRAM 物理单元 |
| 0x08 | STATUS | bit0 busy、bit1 load_ready、bit2 output_valid、bit3 done、bit4 error |
| 0x0C | SHIFT | 空闲时配置 0–31，启动时锁定 |
| 0x10 | LOAD | 写入低 16 位流数据，高 16 位必须为零；未就绪写入报错 |
| 0x14 | OUTPUT | 原子读取并消费一个输出：bit15:0 结果、22:16 行、30:23 列、31 饱和 |
| 0x18 | LOAD_COUNT | 本任务已接受输入数，完整任务为 23,488 |
| 0x1C | OUTPUT_COUNT | 本任务已消费输出数，完整任务为 25,344 |
| 0x20 | ERROR | 0 无错、1 MMIO 访问错误、2 核心偏置格式错误 |

空输出读取、错误地址、未对齐访问、忙时重复启动均报错。错误恢复通过 CONTROL=2；新任务重新装载全部输入和参数。
设备 done 表示最后输出已被 MMIO 读取；**软件任务完成**还必须等待 CPU 写回最后结果并执行 fence。

共享 SRAM 支持 ICB 字节掩码；读返回地址所在 32 位字，由 E203 LSU 提取字节/半字。越出 512 KiB 返回错误，禁止地址回绕。

## 固件与测试

`sw/kwt.c` 提供 `kwt_run_layer`：检查共享缓冲区范围/重叠，交替装载与收取输出，校验输出顺序及计数，含周期超时和错误恢复。
`sw/main.c` 经真实 E203 总线把 ITCM 中的层输入复制到共享 SRAM，然后执行驱动；TB 不代算乘加，也不直接代替 CPU 搬运。
固件使用 RV32 IMAC / ILP32，当前本机工具为官方 Zig 0.13.0 内置 C 交叉编译器；软件版本、工具和源码哈希记录在固件 manifest。
未重新训练、微调或重新提取模型。

| 范围 | 地址/布局 |
|---|---|
| 固件入口 | ITCM `0x80000000` |
| 层 shift | ITCM `0x8000FFF0` |
| 原始打包输入 | ITCM `0x80010000`，23,488 个 little-endian uint16 |
| 共享输入 | `0xA0000000`，46,976 字节 |
| 共享输出 | `0xA000C000`，50,688 字节，99×256 行主序 |
| 软件结果邮箱 | `0xA001F000`，状态、计数、周期数、饱和数 |
| 栈 | DTCM 顶部，`0x9003FFF0` |

SoC 监视器只检查真实 ICB 写入，覆盖全部输入复制与输出坐标，收到软件完成邮箱后才打印 `ARCH03_SOC_PASS`。
SoC TB 复用原 ITCM 装载流程，移除旧教学测试固定 PC 的退出条件，时钟设为 6.667 ns。

本地命令（仓库根；工具路径由个人配置提供）：

```text
python workspaces/arch03/scripts/local_verify.py --vivado-bin <Vivado/bin> --backend pin_mock --cases layer_01 layer_02 layer_03 layer_04 layer_05 layer_06 layer_07 layer_08 layer_09 layer_10 layer_11 layer_12 extremes rounding
python workspaces/arch03/scripts/test_evaluate.py
python workspaces/arch03/scripts/build_firmware.py --zig <zig.exe> --data <准备好的data目录> --output <新的固件目录>
```

`evaluate.py` 从实际 CSV 重建完整矩阵，先验证整数逐位一致，再累计每层 SSE/参考能量计算 NRMSE；不平均单样本误差比例。
输入 manifest 必须记录每个文件的 SHA256、样本标识、层号及尺度。development 数据不能报告 official PASS；official 标识仅在核对组委会来源后使用，且必须覆盖 600 个不同样本的全部 12 层。
目前没有官方样本，现有全量 Y[0,0] 档案不能替代完整矩阵评测。

## 上传及服务器阶段

先提交，再运行 `scripts/package.py --data <目录> --firmware <目录> --member <个人标识>`。
它拒绝脏工作区，核对固件源码、ELF、输入及 shift，生成带哈希的 ZIP 和回执。
平台源码不从服务器回传；包内保存本地已提交补丁，依赖上述固定平台指纹。厂商库保留服务器原位置。
通过 **AC820 Linux FileZilla** 上传到 `/IC` 下个人新目录；不要使用 Windows VNC/FileZilla。

```text
python3 unpack.py <包.zip> --destination <个人独立目录> --sha256 <回执哈希>
cd <新解包目录>
python3 workspaces/arch03/scripts/server_run.py status --session acceptance01
python3 workspaces/arch03/scripts/server_run.py icb --session acceptance01
python3 workspaces/arch03/scripts/server_run.py soc --session acceptance01
python3 workspaces/arch03/scripts/server_run.py dc_accel --session acceptance01
python3 workspaces/arch03/scripts/server_run.py dc_shared --session acceptance01
```

运行前仍须核对共享桌面、已有 EDA 进程和临时修改；入口复用 `.arch02_team_lock` 目录锁。
每个阶段只运行一次；失败保留，修复后提交新包/新会话。中断时若子进程仍运行，锁保留，禁止直接重启。
以上 DC 阶段**仅覆盖加速器接口块和共享 SRAM**，检查真实宏数量、150 MHz setup/hold 和约束报告，不能冒充整机综合。

尚待完成：服务器实际平台补丁/启动验证、14 组 SoC VCS、分模块 DC 实跑、平台 TCM/时钟/复位的工艺适配与整机 DC、综合后功能验证、最终证据审计及官方精度验收。
这些条件通过前 PR 保持草稿，不能合并并宣布完成。
