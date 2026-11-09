# 旧 8 路 MMIO 同口径源加载固件交接

更新：2026-11-09。本文件由 `/root/contest_requirements` 维护，供上下文压缩后恢复。当前主计划是 `IMPLEMENTATION_PLAN_DMA16_20261109.md`；这是旧 8 路对照，不是 8 路 DMA 新候选。

## 11月10日00:10主代理接续（优先于下方历史）

**00:56更新**：c5包`mmio8_source02`真实ASIC/E203完整14例通过354816输出，started00:28:41.945678、finished00:48:11.467276；摘要`fb712c89750950ffbfb8357222affea0ac0540788e744bbb1b14d38ecf3fc5f5`已于00:49:36.693275在服务器逐字节assert。所有任务3843121周期，12层饱和0、extremes6336/rounding4554；原1ns首请求相位现在独立校验通过。新原8路综合及功耗仍未运行；旧synth07/旧BEGIN窗口不作为本次PPA。下面00:10未上传/未服务器执行的状态均为历史。

原包fcd445f的`mmio8_source01`已真实执行E203/ASIC：模拟器25344输出全部匹配，CPU完成，但阶段因Python计时断言失败，不计正式通过。原始首VALID为19070.998093ns，最后输出ACK为25639874.102679ns，周期差3843121；精确事件时间比整周期时长少1ns。保留原运行及错误，不能修改其摘要补PASS。

观察器现在同时记录首VALID的实际时间、其前一个时钟沿时间和沿内相位；解析器要求相位在[0,6.666666)ns、首事件=首沿+相位、末ACK−首沿=周期数×周期。没有放宽时钟周期误差，也没有把首请求等待挪到计时外。周期数为精确事件时长向上取整的保守值，额外量小于一周期；输出同时保留精确elapsed_ns和counted_duration_ns。硬件、原固件和源服务未变。旧日志缺少独立首沿/相位凭据，新入口拒绝，须新包重跑。

28项相关工具测试通过。过程总线夹具phase1的layer_01/extremes/rounding通过76032输出，目录`local_runs/mmio8_source_fixture_20261110_000632_386056`，summary SHA `1a5d7a33044d5988ff57bdf0033485b7c478328437fb3bda0b7e9864d572c722`；phase0的layer_01通过25344输出，目录`local_runs/mmio8_source_fixture_20261110_000754_276790`，SHA `103bd169fdef5e4e9b840ffc09a7596231e4914f5b26f0d263e510d33b47b28a`。两运行各6项拒绝测试通过。此夹具无E203，不是服务器重验；新相位修复尚未提交/上传。

同源MMIO8独立综合入口已在51bc8d1包加入并上传，尚未执行；见`MMIO8_SYNTH_HANDOFF.md`。当前优先运行DMA16 gate02，不能并行争用服务器锁；待允许调度后再做修复后的MMIO8完整14例及新综合。

## 已完成与实际证据边界

只新增以下生产文件，不修改已冻结 DMA16 或旧驱动：

- `sw/main_mmio8_source.c`：在首个源读取前调用原 `kwt_abort()`，有界轮询 STATUS 低 5 位全部清零；读取原设备 ID，检查 shift。源地址 `0xb0000000`，用 11744 次 volatile uint32 拷贝到 `0xa0000000`，再调用原 `kwt_run_layer()`，输出 `0xa000c000`。
- `scripts/build_mmio8_source.py`：Zig RV32IMAC/ILP32，复用现有 `kwt.c`、`kwt.h`、`start.S`、`link.ld`，复用 `build_dma16_firmware.py` 的纯 ELF/元数据校验 helper；所有这些依赖均纳入新 manifest 的 `source_sha256`。ITCM 262144 B，0xfff0 只存 shift，0x10000 之后全零，不接受任务输入参数。
- `scripts/mmio8_source_layout.py`：保留 legacy tile8 原流，不重排到 tile16；仅把两半字低半字先行打包成小端 32 位源。原 load.hex、expected.npz、result.hex、saturated.hex、total.hex 均逐字节保留。原期望结果只供 observer，不是硬件输入。
- `scripts/test_mmio8_source.py`：8 项软件契约测试，含误用 tile16、半字翻转、字节序错误、bias40 高 padding、短文件负例，及已验证 ELF/ITCM 边界 helper 的 8 项检查。

实际执行结果：

- Zig 构建 `local_runs/mmio8_source_firmware_20261109_v1` 成功，代码 load segment 共 1374 B，shift11/12 各一份 program-only 镜像。
- 8 项单测全部通过。Python 3.6 语法检查通过；没有运行 ASIC、CPU、IRQ、综合、时序或功耗。
- `local_runs/mmio8_source_layout14_20261109_v1` 的 14 例共 328832 半字逐一独立解码核对通过，bias 高字节 padding 全部检查；原 14 例文件未改写。
- 原数据来源：`local_runs/light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386/validated_data`。不重跑 TF，不构造新 expected，不覆盖原向量。
- 对当前 HEAD 逐字节比较 `kwt.c`、`kwt.h`、`start.S`、`link.ld` 全部相同。`kwt.c` 保留原除法/坐标校验与 MMIO 轮询，未引入取消的 PR #6 独立优化轮。

首次构建尝试在创建输出目录前因 helper Path 未 resolve 导致 relative_to 报错。已仅修复新 builder 的路径解析并成功重跑；不是编译器或 RTL 失败。

## 计时与事务观察契约

完整计时仍应由总线 observer 给出：首个 B0000000 源读请求 VALID 发出（包含首拍 ready 等待）到最终输出写响应成功，并确认相关事务排空。`mail[8]` 的 BEGIN 只用于 arm，不是计时起点。

首源读取前的 `kwt_abort`、STATUS 清零检查和 fence 是冷缓存前置条件。进入原 `kwt_run_layer` 后，原驱动仍会再次 abort；这次在源加载之后，属于完整测量窗口的一部分。没有改写原驱动来省掉这次操作。

下列是 C 源级访问次数，不是已经量出的 ICB ACK 统计：

- 新初始搬运：11744 次 uint32 source 读取与 11744 次 uint32 shared 写入，分别 46976 B。
- 原驱动的 LOAD：23488 次 volatile uint16 shared 读取，再各一次 MMIO LOAD 写。实际外部 ICB 可能按 32 位字服务，必须观察，不能当成 DMA 的 11744 次共享读。
- 原驱动写回：25344 次 int16 store，逻辑输出 50688 B。需要观察 SH 对应的地址、有效字节 mask 和实际完成响应，不能直接当成 DMA 的 12672 次写响应。
- STATUS、ID、SHIFT、CONTROL、LOAD、OUTPUT、计数器、邮箱和指令/数据活动须按实际总线区分；不能把与任务无关的后续邮箱访问延长最终输出边界。
- `mail[4..5]` 是 CPU 诊断跨度，含 BEGIN 及读取计数开销；`mail[14..15]` 为搬运 CPU 跨度，`mail[16..17]` 为原 driver.stats.cycles。跨度不能相加作为总任务时间。
- 原 `start.S` 禁用中断，当前参考为原轮询行为，不宣称 IRQ/WFI 或 CPU 省电。

## 邮箱与新固件格式

原设备 ID `0x4b575403`、原 MMIO ABI 不变。新布局标签 `0x00080001` 仅用于 manifest/邮箱识别，不增加硬件寄存器。

| 索引 | 含义 |
|---|---|
| 0 | 原成功魔数 0x4b575450；普通失败 0xbad00002，原 trap 使用 0xbad00001 |
| 1 | 原 kwt_result 返回值 |
| 2、3 | 原 driver 输入半字数、输出半字数 |
| 4、5 | 包含加载的 CPU 诊断周期低/高字 |
| 6 | 饱和数 |
| 7 | 0x4b575403 |
| 8 | 清零后，首源访问前写 0x4b575442 作为 arm |
| 9 | 软件已复制 uint32 数；不是 measured ACK |
| 10 | 0x00080001 布局标签 |
| 11 | 0xb0000000 源地址 |
| 12、13 | 46976 输入逻辑字节，50688 输出逻辑字节 |
| 14、15 | CPU source-copy 周期低/高字 |
| 16、17 | 原 driver.stats.cycles 低/高字 |
| 18 | 首次源加载前成功观察的 STATUS（低 5 位为 0） |
| 19 | shift |
| 20 | 0x4d385331，即 M8S1 |

其余邮箱字未定义；不要套用 DMA16 mail[21..31] 的 IRQ 验证逻辑。

新 firmware `run_mode=single_cpu_mmio8_source_v1`，新布局 `schema=kwt1-arch03-mmio8-source-q12-v1`。不能直接调用只接受 DMA16 mode 的 `dma16_soc.verify_firmware`。应对照新 manifest 的完整 source_sha、ELF、segments、每 shift image hash，重新用 ELF+metadata helper 生成 expected 镜像核对；物理 boot 可复用已验证 asic_boot 转换器。

## 当前哈希

| 对象 | SHA256 |
|---|---|
| 固件 manifest.json | `0e5ddd6be7a632cab585f1cce119395520e6be23e186172ca62802c956dcc49e` |
| driver.elf | `f0a9b13f9150ec8fc308add6ec44717274f0b722b2b94514efa68a398c6631f4` |
| shift_11.verilog | `1a960337726cff0b757314da71caa8ff8cde5a2045022845b514054db9042612` |
| shift_12.verilog | `cd94f1d7fdb17c55b85b41b0f457a379e23a945e7b00f1d64aaeaf72de20c16c` |
| layout14 manifest.json | `e5080ad79c097a4f71c7078d0696b44be8bd849be1240214d7ca596951d1667e` |
| main_mmio8_source.c | `1c0617bccbd76f2cdb137093fd2d4e618d376439ad27c39e5dc1226cf59cec78` |
| build_mmio8_source.py | `193b6ed5390cfac57f00cc5e1486464e48ed722a82988f5821a0afd6156eaa9e` |
| mmio8_source_layout.py | `c65f72af3652c7286199205f2da9892573fe80428f324e9d63f975296157f770` |
| test_mmio8_source.py | `f4b20df581abf65307399cd7f37daf75534f42f7a33ed03c991d524e6913df7f` |
| 原 kwt.c | `8b99b3b311aa2393114ef854696f8c0f05f81bc14dbc4dca816509a2136abf13` |

## 尚未完成、下一步与禁止混用

由主代理独立接旧 8 路 reference installer/monitor：原 SysMem ICB 源、原硬件/宏、相同源服务与工艺、program-only 物理 boot；核验初始 memcpy、LOAD、OUTPUT、写响应、冷启动、错误/超时及最终排空。先完整 14 例实际 E203/ASIC 验证，才能形成新的同口径吞吐对照。

当前全部结果仅为编译/布局/软件契约验证。旧 3890080 周期从旧 BEGIN 响应开始，不能用作本次新口径性能值；新 CPU 周期也不能替代总线计时。没有启动任何服务器任务，没有 git commit 或 push。

前一 DMA16 集成只读审查已发现并由主代理修复：IRQ mapping 绑定、完整固件源哈希冻结、ZIP 根目录变量覆盖。本子代理最后验证 poll/IRQ 当前源码和程序镜像通过；实际首包归档和上传由主代理处理，详见主记录。本文件不宣称 DMA16 CPU 验证完成。
