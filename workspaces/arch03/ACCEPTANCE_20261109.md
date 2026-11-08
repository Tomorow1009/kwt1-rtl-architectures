# 本科组实施与验收清单（D1，2026-11-09 北京时间）

依据项目修订实施计划开始执行。开发基线 `aa3f90724720020fe3b4468181eed16646c55f0f`，个人分支 `codex/light-light126/undergrad-d1-numerics`。历史架构快照、旧 100 样本暂停运行和已通过的 37 组 CPU 记录保持原状。

本轮先完成数值与本地总线验证，后续服务器整机工作沿用独立包和统一运行锁。最终结果与原始文件索引见 [D1 证据](../../handoff/team/evidence/UNDERGRAD_D1_20261109.json)。

已生成并在干净目录解包核验的标准包：`local_runs/light-light126-d1-baseline-arch03-20261109_004719-d00633b3331e.zip`，约 10.68 MB，受测包提交 `d00633b3331edf9cdd897c4935e958642a54ddab`。341 个文件哈希、14 组独立标准库整数复算及 14 份固件镜像的输入段/shift 逐字节核对通过。[运行包回执](../../handoff/team/evidence/UNDERGRAD_D1_PACKAGE_20261109.json)记录 SHA256 和本地目录；尚未上传或执行服务器测试。

标准包恰好包含现有审计器要求的 12 层、extremes、rounding。另一个 21 用例扩展包只作为压力测试准备件，现有 `audit.py` 不接受该扩展目录集合，不能直接沿用标准审计流程给它盖通过结论。

| 验收项 | 当前状态 | 证据或下一步 |
|---|---|---|
| 基线、候选与范围冻结 | 完成 | 基线如上；PR #6 895ffc10 仍为待测草稿，不混入本轮实现 |
| 任意 X/W/b 编码、解码、格式 | 完成并本地测试 | [NUMERIC_FORMAT.md](NUMERIC_FORMAT.md)、numeric.py |
| 固定 600 条开发样本、完整 12 层提取 | 完成 | 7,200 任务；182,476,800 输出；逐样本/代码/环境哈希 |
| 软件精度及原整数模型交叉验证 | 完成 | 最差层 0.14941871%；最差任务 0.22915377%；零截限、零输出饱和 |
| 评估器异常与单任务门槛 | 完成 | 缺失、重复、非有限值、错误尺度、汇总掩盖失败等测试 |
| 12 层、最差及最大幅值 RTL 对照 | 19 组、481,536 输出通过 | 新样本 12 层 + 3 组筛选任务 + 4 组边界；XSim、pin_mock，不等同厂商宏/CPU |
| 连续换层、中止恢复、缓存旧值隔离 | 6 任务、152,064 输出通过 | 同仿真换层→部分装载毒化→中止→恢复；真实 CPU 连续任务仍待测 |
| 固件构建 | 21 份镜像完成，未执行新 CPU 测试 | Zig 0.13.0、RV32 IMAC/ILP32；manifest 锁定 ELF 和镜像 |
| 正式平台/库与工具 | 历史来源已锁定，实时可用性未复验 | 平台 163 文件指纹；SS 0.99 V 125°C；共享服务器需重新检查 |
| 严格 150 MHz 约束 | 脚本已修订，未综合 | 6.666666666 ns；读取实际时钟 period，拒绝 6.667 ns 旧结果 |
| ITCM/DTCM/ROM/时钟复位工艺实现 | 未完成 | 不能以全局 FPGA 功能分支替代 ASIC 实现 |
| 整机综合、setup/hold、约束覆盖 | 未完成 | 当前只有历史两个块；必须新运行和新报告 |
| 整系统/计分面积两份明细 | 未完成 | 512 KiB 是否属于规定复用存储仍需核对平台依据；不自行豁免 |
| 综合后 12 层功能及必要时序验证 | 未完成 | 不能用 DDC 重载代替功能一致性 |
| 正式全流程计时与同窗口功耗 | 未完成 | 源准备/失效/装载/末次写响应/fence 边界；E203/互连/宏功耗均需覆盖 |
| PR #6 与 32 位复制性能对照 | 尚未开始 | 必做验收通过后再测，不宣称静态修改已有收益 |
| 来源、复现与配置绑定 | 本轮已记录 | 数值文档、代码提交、样本清单、输入/输出 SHA256；最终统一冻结配置仍待整机结果 |
| 提交期限、模板、字段与视频 | 尚未确认精确要求 | 公开通知只说明 11 月中旬；不得借用 FPGA/芯片应用赛道时间 |

## 后续服务器入口与边界

官方 E203 原目录、工艺库及厂商宏只在现有共享服务器。新增验证包可本地生成；运行前必须在既有允许路径中查看共享桌面、活动进程及 `.arch02_team_lock`。当前本地文件中没有完整官方平台源码，不能凭模块名猜测 ASIC 存储/时钟适配后宣称可链接。

下一阶段优先顺序：核对平台 ASIC 分支及 TCM 容量/读延迟/掩码 → 修复工艺绑定 → 整机链接/综合 → 精确时钟下的约束覆盖与 setup/hold → 网表功能 → 同窗口功耗。新脚本仅修复两块 DC 的时钟约束和审计门槛，不代表整机 DC 已实现。旧报告由原版本审计工具解释，不能用新版审计器补盖严格 150 MHz 通过。

本轮 Python 单测共 29 项通过，服务器侧改动通过 Python 3.6 语法检查；尚未在 DC 执行新的时钟报告命令。正式时序仍必须以真实新工具运行判断。

本地复现（完整提取/向量准备命令见数值文档）：

```text
python -m unittest discover -s workspaces/arch03/scripts -p test_*.py -v
python workspaces/arch03/scripts/local_verify.py --vivado-bin <Vivado/bin> --backend pin_mock --prepared <precision_cases> --cases layer_01 layer_02 layer_03 layer_04 layer_05 layer_06 layer_07 layer_08 layer_09 layer_10 layer_11 layer_12 worst_error largest_input largest_output zero shift00 shift31 cancellation
python workspaces/arch03/scripts/local_verify.py --vivado-bin <Vivado/bin> --backend pin_mock --prepared <precision_cases> --cases layer_01 shift00 --next-case layer_12
python workspaces/arch03/scripts/check_precision_captures.py --vectors <precision_cases> --run <single_task_RTL_run> --output <new_actual_precision_directory>
```

最后一条实测 15 个完整真实参数任务的浮点误差及逐位一致性；合成边界向量单独检查整数结果，不能当成目标模型的性能精度样本。两条 RTL 入口均显式记录 cpu_executed=false。

CPU 连续任务、超时恢复以及正式冷任务与性能窗口仍需新固件/监视器验证；本轮不把本地 ICB 连续仿真写成 CPU 已执行。旧 1,200 组回归保留暂停，不再列为本周必须完成的前置条件。

## 提交通知核查

2026-11-09 读取[西安邮电大学转发通知](https://www.xupt.edu.cn/info/2104/87092.htm)：芯片设计赛道作品提交为 11 月中旬，具体提交内容另行通知，提及报告和作品视频。公开官网此次返回的页面是芯片应用赛道，无法据此确定芯片设计赛道的精确截止时刻、上传字段或模板；本轮没有登录提交账号，也没有提交作品。

## 来源及自主贡献

上游模型/权重：ARM-software/keyword-transformer 指定提交和 best_weights，训练关闭；Speech Commands v0.02 及原 validation/testing 划分。官方 E203 与 SMIC40/RAMSP 工艺库保持其原有来源和授权位置，厂商库不入 Git。

团队既有贡献：arch02 8 路 MAC 与 SRAM 适配、arch03 System Bus/ICB 接口、共享 SRAM、驱动及先前测试平台。此次新增：通用编解码、完整矩阵开发评估、逐任务验收、严格时钟门槛、连续任务/中止恢复测试与证据绑定。提取逻辑复用并扩展团队已有 extract_kwt.py/batch_runtime.py 的权重检查和捕获方法，未宣称上游模型/CPU/存储宏为自主设计。
