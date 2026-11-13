# 最新答疑与已验证版本的总线通路核查

日期：2026-11-13。当前任务是回答已有逻辑验证版本中哪些符合最新答疑，尤其是结果写回必须经过原平台总线。此次只读核查代码、Git 历史和本地保存的服务器证据；未运行新仿真、EDA、远端操作或改动 RTL。

## 结论

- 有一个已通过逻辑验证、数据加载和结果写回都经过原 System Bus 的回退版本：**旧 8 路 MMIO 同源加载版** `original_repaired_mmio8_source_reference`。正式 ASIC14 受测包提交为 `c5e0bbfbb79d1ea0def138395e8e7838f5e3bd4c`，不是最早把任务数据随 ITCM 镜像预填的旧版本。
- 它满足本轮重点核查的原总线通路、32 位接口、实际加载、完整矩阵写回和包含加载/写回的计时要求。这是工程核查结论，不是组委会整体认证；不能据此宣布所有参赛指标均已验收。
- DMA16、ICB32 R1/R4、B0、N1，以及当前 N2 继承的接线，把 DMA 接在原 System Bus 分路器 O4 输出之后的新增仲裁器上。其结果虽然通过 32 位 ICB 事务写入共享 SRAM，却不经过原总线分路器。按新答疑第 16 问的严格口径，不能把这些现有 DMA 配置列为总线通路合规版本，需调整接入位置并重新验证。
- 不应错误描述这些高速版本为“直接写 SRAM 独立物理端口”：当前共享 SRAM 控制器仅有一套 cmd/rsp 接口。其问题是上游接入位置，主要依据第 16 问；第 18 问进一步确认仅保留 CPU/MMIO 经过原总线不够。
- 这些高速版本历史的算术/ASIC/门级 PASS 仍然有效，但它们不证明符合刚提供的新接线要求，过去文档中的“原 ICB 写回”不足以证明原 System Bus 路径完整。

## 最新答疑来源与检查项

文件：`E:/UserData/LENOVO/Downloads/赛题问题答复.pdf`，4 页；SHA256 `706a5d60765f577a5c56c3cbd389da652badbe7bde8ffa574309aef7b6516e30`。

已提取阅读四页全文，渲染并视觉核查第 4 页；中间渲染保存在工作区外层 `tmp/pdfs/qa_20261113/`。

| 条目 | 本次采用的要求 |
|---|---|
| 2、9 | 实际加载输入/参数；不能预置共享 SRAM 权重；从开始加载到结果写回完成计时 |
| 5、7 | 离线权重量化/重排/打包可复现；数值模型与 RTL 位一致；提供编码解码及验证入口 |
| 10 | 正式精度、吞吐、功耗、面积必须对应同一冻结配置 |
| 11 | SRAM 保存本设计数值格式的完整 99×256 输出矩阵，不另外压缩结果 |
| 12、14 | 平台及 SRAM 接口保持 32 位，不能增加绕过规定接口的并行通路 |
| 13 | 不得用直接 ITCM/DTCM 访问替代共享 SRAM 规定通路 |
| 15、16 | DMA 必须经过原 System Bus；不能在 SRAM 前另增绕过总线的多主互连或 TB 装载接口 |
| 17 | 不允许另拉绕过规定通路的 SRAM→加速器流式总线 |
| 18 | 结果写回也必须经过规定通路；绕过 SysBus 的独立 SRAM 写端口不符合 |

第 6 问本身写“参见第六问答复”，存在自引用；不能据此推导 GPTQ 的许可与否。本次无需依赖该条。

## 旧 8 路同源加载版证据

### 实际路径

加载源由 CPU 通过原总线读取，CPU 再通过原总线写共享 SRAM；CPU 从共享 SRAM 读输入，经原总线 MMIO 喂给计算核。

结果路径：加速器 OUTPUT 寄存器 → E203 通过原总线读取 → E203 执行半字存储 → 原 System Bus 分路器 O4 → 单活跃 CPU 路径的 arb/router → 共享 SRAM。

- `workspaces/arch03/sw/main_mmio8_source.c:65` 的循环执行 `shared32[copied] = source[copied]`；源地址 B0000000，非 ITCM 任务数据。
- `workspaces/arch03/sw/kwt.c:42` 执行 `output[row*256u+col]=(int16_t)(word&65535u)`，输出地址从 A000C000 开始。
- `workspaces/arch03/scripts/install_mmio8_source.py` 使用 `mmio8_reference` 分支；`install_dma16.py:84-86` 只实例化 MMIO 核，DMA 主设备输出全部绑零。该版虽保留公共仲裁模块，但没有活跃的绕行 DMA 主机。
- `workspaces/arch03/tb/arch03_mmio8_source_monitor.svh:112-138` 在 CPU 侧真实响应上逐个核验写回地址、字节掩码、数据和坐标；25344 个输出写 ACK 齐全才结束窗口。
- 每任务源读取 11744 次、初始共享写入 11744 次、共享输入读取 23488 次、结果半字写回 25344 次；每个结果为 signed16，总输出 50688 字节。

### 已完成验证

1. `workspaces/arch03/EXECUTION_CHECKPOINT.json` 的 `dma16_execution.mmio8_source02`：
   - 包 `light-light126-mmio-phase-dma16-20261110_001443-c5e0bbfbb79d`；2026-11-10 00:48:11 完成。
   - 真实 ASIC RTL/E203：12 个层任务加 extremes/rounding，共 14 例、354816 输出通过。
   - 摘要 SHA256 `fb712c89750950ffbfb8357222affea0ac0540788e744bbb1b14d38ecf3fc5f5`，历史记录已独立核对。
   - 每任务 3843121 周期；150 MHz 折算 39.030777329 task/s，约 25.62 ms/task。不是硅片实测。
2. `handoff/team/evidence/OLD_QUEUE_RECOVERED_20261111.json`：
   - `ecf3cd4afb3c` 工具包，`runs/mmio8_source_gate_full01/mmio8_gate`。
   - 同网表全 SoC 功能门级 14 例、354816 输出通过；无 SDF。
   - 摘要 SHA256 `06e388e1b744494fc00f224a43caf8de2ebf7e764eb1b655541ce7288a408533`。
3. 已用 `git diff <受测提交> HEAD -- <相关文件>` 对照 MMIO8 的安装器、公共安装器、驱动、主程序、核、SRAM、仲裁、路由及监视器，共 10 个文件，全部无差异。核查 HEAD：`5b0d137b71ffe2e1653ec4c6763d045856caa503`。

### 仍未完成/限制

- 该同源版本没有证据证明完成自己的 1200 任务批量；不得借用 DMA16/R4/B/N1 的批量 PASS。
- `MMIO8_TIMING_REVIEW_20261110.md` 留有时序正式审定未完成项；已存在非负 setup/hold 数字，不等同整体审定。
- `MMIO8_FULLPOWER_20261111.json` 的完整 12 层功耗/审核未闭环；其中运行状态仅是 11 月 11 日历史快照，本次没有远端实查。
- 官方随机 600 条精度仍未验证。原项目内部 600 条软件数值评估不能替代官方评测。
- `SERVER_WAVE_CLEANUP_THIRD_20261112.json` 记录原 MMIO8 的 12 个大 VCD 已授权清理，历史小日志/数值/来源保留；后续新功耗/原始波形检查需再生成波形。

## 后续问答补充：旧 8 路吞吐、综合、功耗

2026-11-13继续核对本地保存的服务器摘要，没有新启动服务器仿真或EDA。

| 项目 | 数值与范围 |
|---|---|
| 完整任务周期 | 3843121，首SysMem源请求VALID到最终结果写ACK，包含加载、搬运、等待、计算、写回 |
| 150MHz折算吞吐 | 39.030777329 task/s；每任务为99×64乘64×256并写回完整99×256结果，不是每秒音频数或完整编码器次数 |
| 单任务时延 | 标称150MHz换算25.620806667ms；实际仿真窗口25.620804104586ms，含首请求相位与周期精度差异 |
| 等效MAC吞吐 | 63.308545320 MMAC/s |
| 综合面积保守项目预算 | 0.2921861914119108mm²；计所有SoC标准单元和加速器SRAM，仅排除复用的64共享SRAM宏和64个TCM宏，不是完整芯片含所有存储的面积 |
| 综合条件 | SS，0.99V，125°C；HF周期6.666666ns |
| setup / hold | +0.00000905991ns / +0.00131008ns；setup余量极小，正式约束/例外审核未闭环 |
| SRAM / latch | 总138个宏，130个4096×16与8个128×16；其中加速器2大+8小；0 latch |
| 第一层整机功耗 | 19.9391320mW；internal12.1767968mW，switching1.48551364mW，leakage6.27682032mW；布局前估算，非芯片实测 |
| 第一层整机能耗 | 510.856594987µJ/task；对应完整25.620804ms窗口，不是12层平均 |

来源为 `BASELINE_PERFORMANCE_20261109.md`、`MMIO8_SYNTH_HANDOFF.md`、`MMIO8_TIMING_REVIEW_20261110.md`、`handoff/team/evidence/MMIO8_FULLPOWER_20261111.json`，及 `EXECUTION_CHECKPOINT.json` 中的mmio8_source02/mmio8_source_synth01。

**第二层状态更正：** `MMIO8_FULLPOWER_20261111.json` 的15:04 running是历史快照。更晚的 `CONTEXT_CHECKPOINT_20261111_2000_SYSTOLIC_B.md:35` 记录20:00服务器实查：`mmio8_fullpower_l02_v2` 已于11月11日15:17:11.637795 passed，摘要SHA `736f0b5a7f6864410fc92d147a44d5549cde516c22bac1626376b98b6dd752ed`。本地未找到其经过独立提取/核验的功耗数值，不能猜值或沿用L01。L03–L12未见完成证据，完整12层平均和系统功耗正式审核仍未闭环。

## 高速 DMA 版本的问题定位

`workspaces/arch03/scripts/install_dma16.py:61-82`：

```text
原 System Bus / sirv_icb1to8_bus 的 O4 → a3_cpu_* ─┐
                                                  ├→ 新增 u_arch03_arb → u_arch03_router → SRAM
加速器 DMA → a3_dma_* ─────────────────────────────┘
```

DMA 源读、入库写和结果写共享上述新增支路；它们并不先进入原总线分路器。`install_icb32.py` 仅替换为 turnover 仲裁/路由/SRAM；`install_systolic_b.py`、`install_n1.py`、`install_n2.py` 再替换加速器，继承相同接入位置。

N1 `arch03_n1_accel.sv:105-112` 把结果接给 transport；`arch03_systolic_b_transport.sv:116-118,153-168` 将结果作为 K_OUTPUT 送同一个 DMA 口，并等待全部 12672 次 32 位成功写 ACK。两项 signed16 结果打包进 32 位总线字不构成第 11 问禁止的额外输出压缩。

因此：这些版本的完整结果确实写入 SRAM，也有正确握手，但“真实 ICB 写回”和“经过原平台 System Bus”是两个不同检查点。

- R4 已有自己的 ASIC/E203 1200 任务、30412800 输出零失败记录，见 `ICB32_FINAL1200_20261111.json`。
- B0 已有同规模记录，见 `SYSTOLIC_B_ASIC1200_20261112.json`。
- N1 已有同规模记录及声明模型范围的阶段验收，见 `N1_FINAL_REVIEW_20261113.md`；该验收不能扩大解释为新答疑下的总线合规认证。
- N2 只有本地验证，见 `N2_LOCAL_PROGRESS_20261113_1435.json`，还不能视为已完成真实 E203/ASIC 验收。
- 对照 R4 的 e65e8dc 和 N1 的 9305c69 受测提交，所查接线/transport 文件与本次 HEAD 无变化。B0 的 63da6ba 对照发现 `install_systolic_b.py` 只有 variant/capability/layout 元数据更新，已检查完整差异，没有接线改动；其余所查接线/transport 文件无变化。

ACK 后转发给内部解码 FIFO 是这些高速版本的另一个既有工程解释。新接线方案还应结合第 17 问重新审视其数据取得方式；本次不把它单独宣布为已获官方认可，也不把内部 FIFO 误称为另拉 SRAM 物理流式端口。

## 已尝试路径与恢复说明

- 优先检查最新 N1/R4 验收；沿 accelerator → transport → installer → arb/router → SRAM 追踪，发现原来的“原 ICB”文字描述不足以证明原 System Bus 路径。
- 回溯 MMIO8 的源加载修正版及实际 CPU 存储、被动写回监视器，找到了符合本次通路要求且已验证的回退版本。
- 最早 `main.c` 从 80010000 的任务数据源启动，不能与此次推荐的 `main_mmio8_source.c` 混淆。
- Python 最初中文输出编码不正确，设置 `PYTHONIOENCODING=utf-8` 后全文读取成功。已读 PDF，不需要再次猜测内容或联网查答疑。
- 无子代理、无新服务器作业、无远端锁/进程检查。旧检查点的 PID/锁/空间不可视为实时信息。
- 本地已有未跟踪的 `scripts/local_verify_n2_load_guards.py` 与 `tb/tb_arch03_n2_load_guards.sv`，此次没有改动。
- 此次请求的核查已完成；未实施总线重接。后续若继续优化，应先修订总线拓扑，再对新冻结配置做加载/读/写协议、CPU竞争/恢复、完整数值回归及PPA；旧高速PPA不能自动沿用。不要因阅读本记录重启任何旧任务。
