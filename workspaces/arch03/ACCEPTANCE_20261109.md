# 本科组实施与验收清单（D1—D2，2026-11-09 北京时间）

依据项目修订实施计划开始执行。开发基线 `aa3f90724720020fe3b4468181eed16646c55f0f`，个人分支 `codex/light-light126/undergrad-d1-numerics`。历史架构快照、旧 100 样本暂停运行和已通过的 37 组 CPU 记录保持原状。

本轮先完成数值与本地总线验证，后续服务器整机工作沿用独立包和统一运行锁。最终结果与原始文件索引见 [D1 证据](../../handoff/team/evidence/UNDERGRAD_D1_20261109.json)。

已生成并在干净目录解包核验的标准包：`local_runs/light-light126-d1-baseline-arch03-20261109_004719-d00633b3331e.zip`，约 10.68 MB，受测包提交 `d00633b3331edf9cdd897c4935e958642a54ddab`。341 个文件哈希、14 组独立标准库整数复算及 14 份固件镜像的输入段/shift 逐字节核对通过。[运行包回执](../../handoff/team/evidence/UNDERGRAD_D1_PACKAGE_20261109.json)记录 SHA256 和本地目录；尚未上传或执行服务器测试。

标准包恰好包含现有审计器要求的 12 层、extremes、rounding。另一个 21 用例扩展包只作为压力测试准备件，现有 `audit.py` 不接受该扩展目录集合，不能直接沿用标准审计流程给它盖通过结论。

D2 本地准备源码已冻结为 `860a6b3f820df2e3933d1989cf8453f59ce87665`，详见 [D2 证据](../../handoff/team/evidence/UNDERGRAD_D2_20261109.json)。已通过的本地测试输入字节与该提交一致；该提交尚未上传或服务器执行。服务器已恢复既有 Linux VNC，只读确认原平台、TCM、ROM、时钟和目标库。自动审批拒绝了私有运行包的外传，明确上传授权仍待答复；本地开发和服务器只读核查继续进行。

D2 标准包 `light-light126-d2-prep-arch03-20261109_020924-71902ce3b9d7.zip` 已在干净目录核验：355 个输入文件、14 组独立整数复算及 14 份固件完整字节布局均通过。包为 10,706,838 字节，SHA256 `594e17548064aba1656795faaed5c1f02290981081ed3a2c1f83708825e5d155`，包提交 `71902ce3b9d76a0aa5669914fbe23dd56362d185`；[回执](../../handoff/team/evidence/UNDERGRAD_D2_PACKAGE_20261109.json)明确记录尚未上传。

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
| 正式平台/库与工具 | 已恢复只读访问并核对实际接口/库 | 平台 163 文件指纹；SS 0.99 V 125°C；开新任务前仍须检查桌面、进程与锁 |
| 严格 150 MHz 约束 | 脚本已修订，未综合 | 6.666666666 ns；读取实际时钟 period，拒绝 6.667 ns 旧结果 |
| ITCM/DTCM/ROM/时钟复位工艺实现 | 本地 TCM 通过，工艺绑定已准备；整机未验收 | 两种模型各 98,682 字读取检查；11 种目标单元映射；实际 DC/厂商宏仍待测 |
| 整机综合、setup/hold、约束覆盖 | 未完成 | 当前只有历史两个块；必须新运行和新报告 |
| 整系统/计分面积两份明细 | 未完成 | 512 KiB 是否属于规定复用存储仍需核对平台依据；不自行豁免 |
| 综合后 12 层功能及必要时序验证 | 未完成 | 不能用 DDC 重载代替功能一致性 |
| 正式全流程计时与同窗口功耗 | 监视器、14 份新固件和 VCD 入口已准备，未测真实 CPU/功耗 | 以加载前标记成功应答开始、最后输出写成功应答结束；E203/互连/宏均需覆盖 |
| PR #6 与 32 位复制性能对照 | 尚未开始 | 必做验收通过后再测，不宣称静态修改已有收益 |
| 来源、复现与配置绑定 | 本轮已记录 | 数值文档、代码提交、样本清单、输入/输出 SHA256；最终统一冻结配置仍待整机结果 |
| 提交期限、模板、字段与视频 | 尚未确认精确要求 | 公开通知只说明 11 月中旬；不得借用 FPGA/芯片应用赛道时间 |

## 后续服务器入口与边界

官方 E203 原目录、工艺库及厂商宏只在现有共享服务器。新增验证包可本地生成；运行前必须在既有允许路径中查看共享桌面、活动进程及 `.arch02_team_lock`。当前本地文件中没有完整官方平台源码，不能凭模块名猜测 ASIC 存储/时钟适配后宣称可链接。

下一阶段优先顺序：核对平台 ASIC 分支及 TCM 容量/读延迟/掩码 → 修复工艺绑定 → 整机链接/综合 → 精确时钟下的约束覆盖与 setup/hold → 网表功能 → 同窗口功耗。新脚本仅修复两块 DC 的时钟约束和审计门槛，不代表整机 DC 已实现。旧报告由原版本审计工具解释，不能用新版审计器补盖严格 150 MHz 通过。

本轮 Python 单测共 29 项通过，服务器侧改动通过 Python 3.6 语法检查；尚未在 DC 执行新的时钟报告命令。正式时序仍必须以真实新工具运行判断。

## D2 本地准备与实际接口核对

- ITCM `32768×64`、DTCM `65536×32`，各 256 KiB、各 32 个 `RAMSP4096X16`。新适配保留单周期有效读取、逐字节写掩码和 SRAM 复位保留；全地址写入/反向读回、所有 bank 边界及全部掩码在 behavioral、pin_mock 两种 XSim 模型中通过。两种模型合计 197,364 次完整字核对，不是厂商模型或 CPU 结果。
- ASIC 原 TCM 调用仿真 RAM；新安装模式只改新平台副本。原 ASIC ROM 已是常量组合逻辑，保持原实现。PLL 原模块直接透传参考时钟，不把它说成已实现模拟 PLL。
- 原 `GENERIC_RVT_SMIC.v` 的 23 个实例使用 11 种旧 8TR40 单元名，指定 SS 库均不含这些名字。已按实际 Liberty 引脚/函数映射为 12TR40 单元，保留全部连线；库 SHA256、引脚、函数和门控类型都须在运行时复核。名称映射不保证延迟或功耗相同。
- 新 `tcm` 阶段用于厂商 SRAM 功能验证；`asic_link` 用于完整 `e203_soc_top` 链接，要求 130 个大 SRAM、8 个小 SRAM，拒绝功能存储分支。二者均未执行；链接成功也不等于综合、时序或网表功能通过。
- 被动计时观察器从加载前 BEGIN 标记的成功总线应答计到最后输出写回的成功应答，包含真实装载、调度和等待；任务失效先完成，固件 `fence` 保证实际源读取在开始标记之后。CPU 自报时间另列，包含末次 fence/检查，不冒充相同窗口。
- 仿真 TB 显式采用 1 fs 精度及 `6.666666 ns` 可表示周期，DC 仍为 `6.666666666 ns`。报告须使用实际测得周期和起止时间；不再复用 `6.667 ns` 旧值。可选 VCD 仅记录 `u_e203_soc_top` 同窗口活动，不包含参考矩阵数组；尚未采到新 SoC 波形，亦未估算系统功耗。
- 计时测试覆盖延迟命令、应答反压、末次应答结束、混合掩码，以及过早装载/错误应答拒绝；实际监视器 include 在明确不含 CPU 的层级替身中完成展开。37 项 Python 单测通过。14 份新 RV32 固件只完成构建，没有新 CPU 执行证据。

本地复现新增入口：

```text
python workspaces/arch03/scripts/local_tcm_verify.py --vivado-bin <Vivado/bin> --backend pin_mock
python workspaces/arch03/scripts/local_tcm_verify.py --vivado-bin <Vivado/bin> --backend behavioral
python workspaces/arch03/scripts/local_window_verify.py --vivado-bin <Vivado/bin>
```

后续仍优先真实库 TCM/单元测试、ASIC 链接与 CPU 启动适配、整机综合/严格时序、网表功能、面积和功耗。CPU 连续任务与超时恢复尚未完成；新增函数或本地 PASS 不代替这些证据。每次上下文压缩后必须回读实施计划及 [执行检查点](EXECUTION_CHECKPOINT.json)，再核对已做、未做和待授权事项。

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
