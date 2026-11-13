# T80技术文档交接

本文件用于队友撰写技术说明、实现报告和答辩材料，不是重新启动验证任务的指令。资料快照截至服务器观察时间2026-11-13 22:34:19；主工作流仍在完成报告、时序与未知活动审核、持久归档。后续结果以同配置的新报告为准。

## 仓库与身份

- 私人仓库：`Tomorow1009/kwt1-rtl-architectures`。
- 当前个人分支：`codex/light-light126/n1-t80-t64-g64-20261113`。不能只读取main。
- 本文件所在提交是本次文档资料快照；**生产硬件提交始终是`876b883d95199f2d1889019cbfec4c93c42d1be5`**。
- 受测活动输入包使用`cef81d4`工具修复，后续报告工具`b80b171`、归档工具`66186a6`单独追踪。工具修复不等于重新综合硬件。
- 有效计划是[T80优先收尾计划](workspaces/arch03/T80_PRIORITY_COMPLETION_PLAN_20261113.md)。G64已取消，T64暂停；旧路线文档仅用于历史对照。
- 先读[AGENTS](AGENTS.md)、[团队同步](handoff/team/SYNC.md)、[当前交接](CONTEXT_HANDOFF.md)与[状态](handoff/team/STATUS.json)。旧文档可能保留当时的“综合中”“数据未上传”等表述，应按观察时间判断。

## T80实际实现

T80是在N1缩位数值核心基础上，改为原系统总线真实共享SRAM读回的80 PE版本。不是T64，不是新增ICG门控版。

```text
E203 MMIO配置、IRQ/WFI、状态与异常处理
                ↓
原32位ICB：源读取 → 写512 KiB共享SRAM → 对应写成功后原总线读回
                ↓
读响应FIFO → 无损解码 → 五行X缓存／16列权重物理双缓冲
                ↓
5×16输出驻留脉动阵列（80 PE）
                ↓
偏置／舍入／饱和 → 两组结果暂存 → 两个16位结果打包
                ↓
32字输出FIFO → 原ICB写回 → 最后成功写ACK并证明事务排空
```

四类DMA事务均经过上游CPU/DMA公平仲裁、原mem_fab、原O4与地址路由；不允许写数据或写ACK直接转发给解码器。保留32位接口、源信用3、源FIFO16、读响应FIFO16、描述符队列8和输出FIFO32。源窗口、地址映射和具体寄存器以[ABI](workspaces/arch03/T80_ABI.md)及安装器为准。

数值为X signed14/F10、W signed12/F12、乘积signed26/F22、累加器及偏置signed32/F22、total signed33/F22、输出signed16/F12；SHIFT=10，半值远离零、signed16饱和。外部容器与物理SRAM字仍为16位，偏置仍用三个半字传送。layout为`0x00100004`，numeric为`0x000e0c20`。

X采用60个128×16宏，W采用32个128×16宏；内部共23 KiB。加上复用存储，全SoC映射220个宏。五行分组共20组，最后一组仅四行有效。没有新增正式ICG，不能把寄存器更新使能写成已完成时钟门控。

## 阅读源码的入口

| 文档主题 | 文件入口 |
|---|---|
| T80 MMIO、任务控制、IRQ与完成语义 | [arch03_t80_accel.sv](workspaces/arch03/rtl/arch03_t80_accel.sv)、[T80_ABI.md](workspaces/arch03/T80_ABI.md) |
| 四段搬运、提交顺序、反压和取消排空 | [arch03_t80_transport.sv](workspaces/arch03/rtl/arch03_t80_transport.sv)、[install_t80.py](workspaces/arch03/scripts/install_t80.py) |
| 五行缓存、权重双缓冲和结果调度 | [arch03_n1_linear16x5.sv](workspaces/arch03/rtl/arch03_n1_linear16x5.sv) |
| 80 PE脉动数值与舍入 | [arch03_n1_systolic5x16.sv](workspaces/arch03/rtl/arch03_n1_systolic5x16.sv)、[arch03_n1_requantize.sv](workspaces/arch03/rtl/arch03_n1_requantize.sv) |
| 无损编码及解码 | [n1_codec.py](workspaces/arch03/scripts/n1_codec.py)、[arch03_n1_decoder.sv](workspaces/arch03/rtl/arch03_n1_decoder.sv) |
| CPU驱动 | [kwt_t80.c](workspaces/arch03/sw/kwt_t80.c)、[kwt_t80.h](workspaces/arch03/sw/kwt_t80.h)、[main_t80.c](workspaces/arch03/sw/main_t80.c) |
| 固件构建及打包 | [build_t80_firmware.py](workspaces/arch03/scripts/build_t80_firmware.py)、[package_t80.py](workspaces/arch03/scripts/package_t80.py) |
| 原始量化、数据来源 | [DATA100说明](docs/data/x14-w12-b32/DATA100_X14_W12_B32.md)、[转换器](tools/kwt-x14-w12-b32/convert_kwt1_x14_w12_b32.py) |
| ASIC、批量及功能门级验证 | `workspaces/arch03/scripts/t80_soc.py`、`t80_batch.py`、`t80_gate.py` |
| 完整计时、实际总线路由 | [arch03_task_window_t80.sv](workspaces/arch03/tb/arch03_task_window_t80.sv)、`arch03_t80_route_audit.svh`、`t80_window.py` |
| 综合、活动、功耗 | `workspaces/arch03/scripts/t80_synth.py`、`t80_saif.py`、`t80_power.py` |
| 接续、结果导出、归档 | `workspaces/arch03/scripts/t80_resume_evidence.py`、`transport_report_stage.py`、`t80_report.py`、`t80_archive_runtime.py` |

以上共享模块还依赖同仓库的arch02、平台安装、存储与标准单元适配工具，需克隆完整仓库，不能仅下载两个T80 RTL文件。

## 已有结果与限制

| 项目 | 目前可写入文档的结论 |
|---|---|
| 真实ASIC RTL/E203 | 14例、前20条×12层=240任务通过；批量6,082,560个输出的total/result/saturated逐项核对，CPU竞争与恢复通过 |
| 功能门级 | 同网表14例通过，无SDF；不能称布局后验证 |
| 完整吞吐 | 固定12任务平均112,569周期，150 MHz折算1,332.516 task/s；非芯片实测 |
| 初步面积 | 项目保守上界0.9521382079 mm²，满足1.20 mm²数值门槛；面积归属及完整审核状态需注明 |
| 初步时序 | SS/0.99 V/125°C、6.666666 ns，setup +0.000576019 ns、hold +0.00623399 ns；不冒充完整时序签核 |
| 活动 | 十二层完整窗口SAIF全部通过；窗口包含装载、搬运、等待、计算与最终写回 |
| 功耗 | 十二层功耗报告已生成；按22:34显示值和固定周期复算，时间加权约50.2315 mW、平均37.6967 µJ/task，属于布局前初步估算；未知活动和模型影响尚待最终审核 |
| 精度 | 前20条浮点/ASIC关联阶段已结束；具体NRMSE待读取最终明细，不以N1的100条数字冒充T80本轮结果 |
| 全量/官方状态 | 本轮不是100条1200任务；官方600条未验证 |

吞吐与瓶颈详见[实测搬运说明](workspaces/arch03/T80_MEASURED_TRANSPORT_20261113.md)及[12任务计数](handoff/team/evidence/T80_ASIC12_COUNTERS_20261113.json)。80 PE的完整窗口MAC利用率约18.01%，共享读响应平均4拍，其余三类响应平均3拍；等待区间互相重叠，不能相加成为总周期。单纯减少PE不保证增加吞吐。

面积和时序身份见[综合证据](handoff/team/evidence/T80_SYNTH_PRELIMINARY_20261113.json)。最新十二层功耗显示值、复算公式和截图SHA见[22:34功耗快照](handoff/team/evidence/T80_POWER12_SNAPSHOT_20261113_2234.json)，优先用后续完整报告的未舍入值替换。本快照不把`reports_ready_review_required`写成最终验收通过。

## 资料齐备范围

仓库已有RTL、TB、驱动源码、量化/编码、构建/打包、ASIC/门级/综合/SAIF/PT、报告/审核/归档工具及小型证据。本次额外同步[冻结输入包](deliverables/t80_876b883_cef81d4/README.md)：约9 MB，833个成员全部SHA-256核对，其中106个是此前未单独入库的生成固件与14例验证输入。

厂商库、工具许可证、官方平台外部依赖、完整100条数据、网表、SAIF和完整运行日志不冒充已入Git。平台和库在比赛授权环境；100条输入入口为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all`。旧DATA100文档的“尚未上传”是历史状态，不是当前入口状态。

原综合、ASIC与门级在`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`下各自的T80冻结目录；后续活动和功耗在`/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4/runs/`。具体run和哈希以状态及交接为准，`/tmp`不是持久备份，持久归档尚在收尾。写技术文档不需要启动这些目录中的任务。

## 历史路线应如何表述

- 原8路MMIO、16路DMA、R4、B0、N1保留为历史探索，各有独立硬件与计时口径。
- N1到T80的主要变化是成功共享写入后通过原总线真实读回，并将全部DMA接入原总线；不能把旧N1更高吞吐直接写成T80成绩。
- T64为4×16方案，仅有自己的局部/本地验证和接收预检；当前暂停，不借T80结论验收T64。G64已取消，无门控收益数据。
- T80早期SAIF接续因旧三段窗口验证器失败，后续只修复活动工具；失败路径保留，不能误写成RTL计算错误，也不能漏报工具修复。

## 给文档撰写者的任务

根据上述源码和证据撰写中文技术报告：任务及约束、框架与数据流、数值/编码、80 PE及缓存组织、DMA与CPU控制、验证方法、同配置结果、瓶颈、历史路线与取舍、复现依赖和未验证项。每个关键数字注明来源文件、配置和边界。

不重启服务器队列，不修改受测硬件，不删旧八路，不恢复T64/G64。示意图必须画出32位原总线及共享SRAM真实写入和读回；不得画成宽总线、写ACK旁路、已实现ICG或布局后签核。若主工作流发布更晚的最终报告，核对硬件、数据和库哈希后更新结果表。
