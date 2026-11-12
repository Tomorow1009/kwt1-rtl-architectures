# N1阵列压力与CPU诊断工具交接（2026-11-13）

有效计划为`IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`。本记录仅覆盖本地阵列压力、固件编译及诊断观察器检查；不代表E203、厂商SRAM、ASIC时序、面积或系统功耗验收。B0文件未修改，没有启动N2。

## 已完成

- 独立Python整数模型与`tb_arch03_n1_systolic5x16.sv`完成固定种子`0x7834a9f1`的10000随机块和32定向块，逐项核对794560个有效输出的sum、total33、result16、saturated和每输出64次MAC。末四行、II64连续块、全阵列暂停、标签回绕、11次部分块取消及11次部分块复位均覆盖。
- 新增N1专用竞争固件`main_n1_contention.c`、构建器和`n1_contention.py`。固件使用真实CPU对共享SRAM暂存区进行写/读/比较，后续服务器观察器要求CPU和DMA实际竞争及公平服务，保留total33审核。该固件不是IRQ性能固件。
- 新增N1专用十阶段恢复固件`main_n1_sequence.c`、构建器、`n1_sequence_soc.py`和`arch03_n1_sequence_monitor.svh`。阶段为五种配置拒绝、装载中取消、轮询超时排空、无复位A/B/A。保留原真实异常入口汇编，但使用新N1诊断标识与schema；A/B均强制SHIFT10。
- CPU固件检查ID=`4b575306`、capability=`000505bf`、numeric=`000e0c20`和layout=`00100004`。sequence观察器独立检查实际MMIO身份读响应、成功共享写ACK后解码、实际total33及坐标唯一性，输出五列`row,col,result,saturated,total`。参考数据不会进入ELF或ITCM任务区。
- 本地十阶段fixture使用真实N1 DMA、核心、仲裁、路由及pin mock SRAM，无E203。A/B/A三任务76032个输出的result、sat、实际total33全部通过；提前切换源、错异常EPC回执、缺回执字段三个反例均被拒绝。
- 14项软件自检核对两固件身份/程序区边界、两个任务SHIFT12拒绝、源描述符错误、源文件互换、旧四列capture、旧41位total、33位保留位等。复用正式服务器逐阶段解析逻辑检查实际fixture回执，并确认NO_CPU日志不能被作为E203通过证据。

## 运行证据

| 范围 | 目录或文件 | SHA-256（摘要/清单） |
|---|---|---|
| 阵列完整压力 | `local_runs/n1_systolic_array_20261113_010306_915102/summary.json` | `1c90ab97c0b0b61b2a3c52714b7bce5c6c166c67f3dad516c49227e6440780e5` |
| 竞争固件编译 | `local_runs/n1_contention_firmware_20261113_03/manifest.json` | `f643a42b8d4f5fe5d725b75759486fe073a4326075fdc9ce933b2a8e2c2ffaca` |
| 恢复固件编译 | `local_runs/n1_sequence_firmware_20261113_03/manifest.json` | `6af492af709fd011744bfd5aded41e80d56658f7c4cd2b584de12d5fa78ee9f0` |
| 本地十阶段fixture | `local_runs/n1_sequence_fixture_20261113_011315_300384/summary.json` | `c10990c6412587e2e4dab7e9c8b94463d7e8cbaf107678ba82d87ae12168adfa` |
| 诊断工具自检 | `local_runs/n1_diagnostics_selftest_20261113_01/summary.json` | `6dd694b624896ea7d1c71ae7b4174ce2ddf87480ea2e1b6d9af49536c806e387` |

运行目录均相对仓库根目录，生成的大文件未入Git。数据使用`workspaces/arch03/local_runs/n1_data14_20261113_02/source`，A=`layer_01`、B=`rounding`，编码长度31428B和4204B。fixture完整窗口周期30547、22337、30547，仅属本地诊断数据，不作为真实ASIC/E203吞吐结论。

## 已尝试与失败路径

- 首轮`*_firmware_20261113_02`编译因复制诊断C代码时遗留旧`KWT_SYSTOLIC_LAYOUT_V3`宏名失败；新N1布局宏与身份检查修正后，独立03目录编译及校验通过。02目录与日志保留。
- 一次本地文件生成尝试使用当前Python不支持的`Path.write_text(newline=...)`参数，在创建首个文件前停止；改为UTF-8字节写入。该失败未修改B0或已有文件。
- 不将NO_CPU回执伪装成真实CPU日志；自检要求正式解析器明确拒绝。

## 尚未完成及恢复入口

- 由主代理将`n1_contention.monitor()`接入`n1_soc.compile_design`的专用`diagnostic='contention'`分支，并用`n1_contention.verify_firmware`审核对应固件。
- `n1_sequence_soc.verify(cfg,run,platform_source,cases,call,firmware)`为独立真实ASIC/E203入口，使用服务器`validated_data`中相同N1 A/B源及对应固件目录。编译后方可证明CPU实际执行、异常陷阱、驱动超时、SRAM厂商模型和无复位A/B/A。
- 上述真实CPU竞争/恢复、1200批量、PPA及完整精度尚不能由本记录宣称通过；以主计划和最终服务器回执为准。
- 本子任务没有连接远端、接触协作锁或启动服务器作业。最后本地fixture进程已正常退出，无待续本地会话。
- 文件源码与固件哈希绑定；任何受测源码改动后需重新构建相应固件。不要覆盖03和已完成fixture目录。
