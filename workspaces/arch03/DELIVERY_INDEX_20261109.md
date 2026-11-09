# 本科任务交付索引与复现顺序

本索引对应 2026-11-09 的实施工作，尚不是最终提交包。实时通过、失败和待验状态以 [验收表](ACCEPTANCE_20261109.md)、[服务器证据](../../handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json) 为准。正式赛题正文第 13—14 页要求提交工程、报告、数值材料及来源说明；最终评测使用同一冻结版本。

## 工程与来源

| 交付内容 | 工程位置 | 边界 |
|---|---|---|
| 数值接口、矩阵布局、误差定义和复现命令 | [NUMERIC_FORMAT.md](NUMERIC_FORMAT.md)、`scripts/numeric.py` | 任意合法 X/W/b 输入；600 条数据是内部开发集 |
| FC1 算术和 SRAM 缓冲 | `../arch02/rtl/` | 团队既有 8 路 MAC 基线；不是本轮新发明 |
| System Bus/ICB 接口和共享存储 | `rtl/`、[README.md](README.md) | 团队架构三集成；共享 SRAM 是团队补齐的平台映射 |
| 实际 E203 固件和驱动 | `sw/kwt.c`、`sw/main.c`、`sw/main_sequence.c` | CPU 执行实际装载、启动、收取及写回 |
| 固件构建与输入验证 | `scripts/build_firmware.py`、`scripts/build_sequence_firmware.py` | 源输入和 shift 与固件内容逐字节核对 |
| 官方平台适配 | `scripts/install_platform.py`、`scripts/technology_binding.py`、`scripts/memory_technology.py` | 原平台/工艺库保留在服务器；新独立副本有明确补丁和指纹 |
| 功能验证及反例 | `tb/`、`scripts/test_*.py`、`scripts/local_*verify.py` | 替身、真实厂商模型、CPU 和门级证据分别标识 |
| 服务器复现入口与打包 | `scripts/server_run.py`、`scripts/package.py` | 每个配置先提交、打包、核验，再用独立 session 执行 |
| 整机综合、活动及功耗 | `scripts/soc_synth.py`、`scripts/gate_soc.py`、`scripts/activity_fast.py`、`scripts/soc_power.py` | 报告生成不自动等于时序或功耗验收 |
| 活动映射、功耗模型和失败运行复核 | [POWER_REVIEW_20261109.md](POWER_REVIEW_20261109.md) | 明确区分翻转覆盖、精确映射、未知值及布局前估算边界 |

上游模型为 ARM-software/keyword-transformer 指定提交 `237e4097afd4f6851e0b82f0a8d65c2dfe8eae30`，KWT-1 `best_weights`；数据来源为 Google Speech Commands V2。未训练、微调或蒸馏模型。E203、标准单元、SRAM 宏和工具仍归其原始来源；厂商库、工具和个人凭据不进入源码包。本轮自主工作是接口/固件和工艺适配的修订、通用数值评估、任务监视器、连续恢复验证及可核验的自动运行流程。团队既有算术核心和共享存储集成单独标识，不混为本轮贡献。

测试参考文件只供独立检查器比较。上电时允许装入的 ITCM 镜像包含程序及 X/W/b 源数据，任务阶段由 CPU 通过真实平台搬运并驱动硬件计算。参考结果不作为计算输入，监视器的参考数组也不进入 SoC 活动范围。

## 已有证据及配置隔离

| 证据 | 受测配置/运行 | 当前含义 |
|---|---|---|
| 600 样本、7,200 个完整任务 | [D1 数值证据](../../handoff/team/evidence/UNDERGRAD_D1_20261109.json) | 软件精度；不能替代未见官方样本或硬件全量测试 |
| 实际 CPU 连续任务/中止/超时恢复 | `b400db0` / `d3_sequence01/sequence` | 功能 TCM 分支的两组 A/B/A，共 6 任务 |
| 实际 ASIC 分支完整 14 用例 | `46cb3de` / `d3_full01/asic_soc` | 354,816 输出逐项通过；旧 UART 配置 |
| 整机网表、SDC、时序/面积明细 | `c323781` / `d3_synth03/asic_synth`，由 `4c8803e` / `d3_reports01/asic_synth` 独立复核 | 原始映射不变，setup/hold 为负，24 个 UART 锁存器 |
| 门级首层 | `4c8803e` / `d3_gate01/gate_soc` | 25,344 输出通过，无 SDF；不代表全部 14 用例 |
| 完整任务 VCD | `4c8803e` / `d3_activity01/gate_soc`，由 `371316a` / `d3_activity02/gate_soc` 复核 | 完整 29,860,998,380 字节、文件哈希和原始输入/输出复核通过；未知活动与功耗仍待审核 |
| 旧配置系统功耗 | `4c8803e` / `d3_power01/asic_power` | 工具运行 679 秒并生成报告；PT-063 启动错误导致验收失败，原报告保留 |
| UART、任务启动选择和 CDC 修正 | `371316a` 修正包 | UART 对照通过；`d3_synth04` 锁存器 0、hold 转正，3 条 LF 输出 setup 违规仍待修正；新 CPU `d3_full02` 运行中 |
| 功耗启动环境修正 | `55698a6` / toolenv 包 | 399 文件服务器解包核验通过；环境修复仍须实际工具运行验证 |
| LF 输出预算及门级平台来源绑定 | `f8fc1d8` / lfports 包 | 399 文件服务器解包核验通过；全量 CPU 结束后串行启动新综合 |

服务器包目录统一位于 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`。包全名、源码提交、ZIP SHA256、摘要 SHA256 和截图索引见服务器证据；不得只凭日期或运行名选取“最新”结果。

## 新冻结配置的必要复现顺序

1. 干净解包核对 manifest 所有文件；独立重算全部整数结果，并核对每份固件的源数据布局。保留工具、模型、数据及源码指纹。
2. 检查共享任务锁，再运行实际 UART 原版/修正版对照、ASIC 分支 14 用例。凡新增平台补丁都必须用新配置重验。
3. 新 `asic_synth` 产生映射网表、SDC、逐叶面积、完整约束和 setup/hold 报告。复核精确周期、所有例外依据、未约束路径及锁存器；不能以报告存在代替通过。
4. `gate_soc` 绑定这次综合摘要 SHA256，覆盖 12 层与必要边界。至少为所报告性能任务采集完整装载至最后写回窗口的 VCD；完整扫描、SHA256 和实际写回校验均须通过。
5. `asic_power` 绑定同一门级摘要及同一波形，检查活动覆盖、未知值、未标注对象、SRAM 及标准库功耗单位、导线/时钟假设和各部分求和，再计算该完整窗口的 J/task。
6. 汇总同一配置的数值、时序、面积、周期、吞吐和功耗。必做缺口仍存在时继续修复，暂不开展 PR #6/32 位复制等效率对照。

## 最终提交前仍须补齐

| 项目 | 完成标准 |
|---|---|
| 综合前后完整功能及严格时序 | 新配置 14 用例、完整约束依据、setup/hold 非负，按需要补 SDF/等价证据 |
| 计分面积 | 指定库单位已由全部标准单元和两种 SRAM 的 LEF 交叉确认；各项归属及豁免仍待确定，见 [面积复核](AREA_REVIEW_20261109.md) |
| 功耗与能耗 | 完整任务活动通过，全部部件覆盖和未建模项有解释，实际 W 与 J/task 计算可复核 |
| 最终源码/运行包 | 冻结提交、完整文件哈希、干净目录复现；原始网表/SDC/报告/活动文件有可取用位置 |
| 创新与答辩 | 有实测对照才记录收益；标明上游、团队既有和本轮修改的贡献 |
| 提交系统要求 | 核实芯片设计赛道实际截止、字段、模板和视频要求；公开“11 月中旬”不能替代精确通知 |

源码运行包、报告索引和待验清单可以继续完善；在上述证据齐全前，不将其命名或描述为“最终合格提交”。
