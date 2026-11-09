# 本科组实施与验收清单（2026-11-09 北京时间）

交付位置及同配置复现顺序见 [交付索引](DELIVERY_INDEX_20261109.md)，已有实测窗口换算见 [性能基线](BASELINE_PERFORMANCE_20261109.md)。

| 验收项 | 当前状态 | 证据或下一步 |
|---|---|---|
| 基线、候选与范围冻结 | 完成 | 旧配置与新修正包分别绑定；PR #6 895ffc10 仍为待测草稿，不混入本轮实现 |
| 任意 X/W/b 编码、解码、格式 | 完成并本地测试 | [NUMERIC_FORMAT.md](NUMERIC_FORMAT.md)、numeric.py |
| 固定 600 条开发样本、完整 12 层提取 | 完成 | 7,200 任务；182,476,800 输出；逐样本/代码/环境哈希 |
| 软件精度及原整数模型交叉验证 | 完成 | 最差层 0.14941871%；最差任务 0.22915377%；零截限、零输出饱和 |
| 评估器异常与单任务门槛 | 完成 | 缺失、重复、非有限值、错误尺度、汇总掩盖失败等测试 |
| 12 层、最差及最大幅值 RTL 对照 | 19 组、481,536 输出通过 | 新样本 12 层 + 3 组筛选任务 + 4 组边界；XSim、pin_mock，不等同厂商宏/CPU |
| 连续换层、中止恢复、缓存旧值隔离 | 本地及真实 E203 各 6 任务通过 | `d3_sequence01` 两组 A/B/A、152,064 输出、poison17/中止、实际驱动超时恢复；功能 TCM 范围 |
| 固件与真实 ASIC 分支 CPU | 旧标准 14 用例通过，新配置运行中 | `46cb3de/d3_full01`：354,816 输出；`371316a/d3_full02` 正验证 UART 修正与完整任务启动模式 |
| 正式平台/库与工具 | 固定平台、真实厂商模型和 DC 链接已通过 | 163 文件平台指纹；SS 0.99 V 125°C；共享服务器运行前检查桌面、进程与锁 |
| 严格 150 MHz 约束 | 实际周期通过，setup 未通过 | `371316a/d3_synth04`：6.666666000000 ns；setup −0.740983 ns、hold +0.00623399 ns；剩余 3 条 LF 输出时钟预算需修正重验 |
| ITCM/DTCM/ROM/时钟复位工艺实现 | 厂商组件和 ASIC RTL 全量通过 | 真实 TCM 98,682 检查、262,144 字节启动映射、11 类标准单元；PLL 原平台为透传实现 |
| 整机综合、setup/hold、约束覆盖 | 新综合报告完成，时序仍待修正 | `d3_synth04` 锁存器 0、四个精确 CDC 首级绑定、未列出未约束端点；三条高扇出警告及 I/O 假设仍需审核；见 [时序复核](TIMING_REVIEW_20261109.md) |
| 整系统/计分面积两份明细 | 整系统汇总与面积单位已核对，计分归属未定 | 138 个宏、1,276 种标准单元的 Liberty/LEF 面积依据；整机约 3.812814 mm²，保守计分情景及条件见 [面积复核](AREA_REVIEW_20261109.md) |
| 综合后 12 层功能及必要时序验证 | 第 1 层真实门级通过，全量待验 | `d3_gate01`：25,344 输出、3,890,080 周期；无 SDF；新配置仍需完整 14 用例 |
| 正式全流程计时与同窗口功耗 | 旧完整活动通过；功耗首轮有错误，未验收 | `d3_power01` 因 PT-063 被拒绝；`55698a6` 环境修正包已上传且服务器 399 文件核验通过，实际运行及活动/模型审核待完成 |
| PR #6 与 32 位复制性能对照 | 尚未开始 | 必做验收通过后再测，不宣称静态修改已有收益 |
| 来源、复现与配置绑定 | 本轮已记录 | 数值文档、代码提交、样本清单、输入/输出 SHA256；最终统一冻结配置仍待整机结果 |
| 提交期限、模板、字段与视频 | 尚未确认精确要求 | 公开通知只说明 11 月中旬；不得借用 FPGA/芯片应用赛道时间 |

以下保留历次过程记录；其中“尚未运行/待授权”等旧叙述以表内当前状态及执行检查点为准。

**完整活动复核通过（08:38）：** `371316a/d3_activity02` 对保留的旧门级仿真产物完成原始包、源码、启动镜像、全部 25,344 个输出和完整 VCD 的独立复核；没有重跑或改写原仿真。扫描 5,495,122,711 条活动记录，六类部件均有活动，起止与完整任务窗口一致。摘要 SHA256 `cc75446e2f0c01ca4e57bd13af697be0f8a82f6b9d94566a40111f2e19f2d72f`；未知值记录仍需功耗解释，活动映射与系统功耗尚未验收。`4c8803e/d3_power01` 已于 08:40 启动。新 UART/启动模式/CDC 修正并未因此通过。

**真实门级首层通过（07:29）：** `4c8803e` 新包在 `d3_reports01` 完成原综合产物的独立复核，138 个宏和逐实例面积汇总一致；原 `d3_synth03` 保留。`d3_gate01` 使用该摘要绑定的综合网表及真实厂商功能模型，第 1 层全部 25,344 个输出通过，完整窗口 3,890,080 周期，与 ASIC RTL 相同。范围是无 SDF 的门级功能，setup/hold 仍为负值、完整 14 用例门级及功耗未验收。新 `d3_activity01` 正采集第 1 层完整任务活动。

**综合报告状态（07:12）：** `c323781` 的 `d3_synth03` 已生成完整映射网表和报告，实际 HF 周期为 6.666666000000 ns、138 个 SRAM 宏数量正确；setup −1.77329254 ns、hold −0.09681505 ns，严格时序尚未通过。Python 把 Tcl 过程定义中的标记回显也计为完成标记，导致报告收集失败。现已加入仅匹配独立输出行的修正和新目录报告复核入口；63 项测试通过，原失败运行保留，尚未服务器复核。最差路径涉及启动选择去抖寄存器及低频时钟同步器，仍须核对实际工作模式。

**最新 ASIC 全量验收（06:43）：** `46cb3de` 的 `d3_full01` 已于 06:39 完成真实 ASIC 分支 14 用例，12 层加 extremes/rounding 共 354,816 个实际 CPU 写回逐项通过；各完整任务窗口均为 3,890,080 周期、6.666666 ns。12 层无饱和，两个合成边界用例饱和数 6,336/4,554 与参考一致。摘要 SHA256 `d799ba311f50b1b8ff78b8a60a86a76ca3dc2d9c67238e7a7a25c994ddbfe310`。此为 ASIC RTL 功能证据，不等同门级/时序/功耗。修正综合包 `c323781` 的 `d3_synth03` 已在前一运行释放锁后启动。

**门级入口准备（06:37）：** 新 `gate_soc` 入口要求已完成的整机综合摘要 SHA256，复核网表/约束/原始输入及当前 RTL、固件源码一致性。按实际映射 SRAM 路径生成 ITCM 装载器，其 32 个宏、16,384 个物理行已在 XSim 存储替身中全部核对；59 项 Python 测试通过。此项仅为本地入口准备，实际综合网表、SDF 与功耗仍未验收。

**最新综合排查（06:24）：** `d3_synth02` 整机链接通过并生成映射产物，但 SDC 首个复位端口拼写错误导致约束中途退出；后续 DC 仍执行了映射，因此其时序不可验收。另发现工具把 6.666666666 ns 存为 6.666667000000 ns、多时钟组路径误判及虚拟常量面积分类问题。已准备明确端口/更短周期/多组最差裕量/失败即停修正，不放宽频率检查；仍须新包重跑。`46cb3de` 的独立 `d3_full01` ASIC 全量 14 用例已于 06:19 启动，原运行保留。

**最新 ASIC 验收（06:02）：** `e60a3cc` 标准包的 `d3_smoke04` 已完成 ASIC 分支真实 E203 第 1 层：25,344 个输出逐项匹配，未定义全局 FPGA，真实 SRAM/标准单元功能模型运行；任务时钟模式 test_mode=0、pllbypass=1、divider_bypass=1。完整窗口为 3,890,080 周期，输入/输出半字计数 23,488/25,344，饱和为 0。这是单任务 ASIC RTL 功能通过，完整 14 组、门级及物理时序/功耗仍待完成。整机综合首轮在 SRAM 哈希守卫处发现历史抄写的相邻字符交换；已与原始截图及最新服务器 SHA256 对照更正，库未变。`46cb3de` 修正版已安全上传/解包，`d3_synth02` 正在运行。

**最新连续任务验收（05:47）：** `b400db0` 连续包的 `d3_sequence01` 已在真实 E203 上完成两组 A/B/A，共 6 个任务、152,064 个输出逐项核对通过；两组都通过部分 17 次 LOAD 后中止和实际驱动在 1 次 LOAD 后超时，再恢复完成 A。任务间没有复位，6 个完整装载至最终写回窗口均为 3,890,077 周期、周期 6.666666 ns。此入口明确使用平台功能 TCM；不冒充 ASIC 或门级验收。ASIC `d3_smoke02` 编译暴露默认 timescale 缺失，修正包 `cd524e2` 已核验上传，`d3_smoke03` 正在执行。

**最新服务器进度（05:33）：** 用户已明确授权指定范围的上传及服务器验证，旧“等待上传授权”描述为历史状态。D3 标准、连续及采样修正包均通过 Linux FileZilla 上传，并完成服务器 ZIP/解包哈希校验。实际标准单元测试通过 11 种单元和 12 项门控检查；`d3_vendor02` 的 TCM 98,682 次完整地址/掩码/保持检查和启动映射 262,144 字节、32 个真实宏读回通过。首轮 TCM 的 10 ps 采样失败已保留；同周期 3 ns 采样修正后通过，生产 RTL 未变。ASIC CPU 首轮因原平台六条旧外部库路径被严格解析器拒绝，尚未编译；只对固定文件清单允许排除这些替代/未使用库条目的修正通过 53 项本地测试，待新包验证。[服务器证据](../../handoff/team/evidence/UNDERGRAD_D3_SERVER_20261109.json)随实际结果更新。整机 CPU、综合、门级、严格时序和功耗仍未通过。

依据项目修订实施计划开始执行。开发基线 `aa3f90724720020fe3b4468181eed16646c55f0f`，个人分支 `codex/light-light126/undergrad-d1-numerics`。历史架构快照、旧 100 样本暂停运行和已通过的 37 组 CPU 记录保持原状。

本轮先完成数值与本地总线验证，后续服务器整机工作沿用独立包和统一运行锁。最终结果与原始文件索引见 [D1 证据](../../handoff/team/evidence/UNDERGRAD_D1_20261109.json)。

已生成并在干净目录解包核验的标准包：`local_runs/light-light126-d1-baseline-arch03-20261109_004719-d00633b3331e.zip`，约 10.68 MB，受测包提交 `d00633b3331edf9cdd897c4935e958642a54ddab`。341 个文件哈希、14 组独立标准库整数复算及 14 份固件镜像的输入段/shift 逐字节核对通过。[运行包回执](../../handoff/team/evidence/UNDERGRAD_D1_PACKAGE_20261109.json)记录 SHA256 和本地目录；尚未上传或执行服务器测试。

标准包恰好包含现有审计器要求的 12 层、extremes、rounding。另一个 21 用例扩展包只作为压力测试准备件，现有 `audit.py` 不接受该扩展目录集合，不能直接沿用标准审计流程给它盖通过结论。

D2 本地准备源码已冻结为 `860a6b3f820df2e3933d1989cf8453f59ce87665`，详见 [D2 证据](../../handoff/team/evidence/UNDERGRAD_D2_20261109.json)。已通过的本地测试输入字节与该提交一致；该提交尚未上传或服务器执行。服务器已恢复既有 Linux VNC，只读确认原平台、TCM、ROM、时钟和目标库。自动审批拒绝了私有运行包的外传，明确上传授权仍待答复；本地开发和服务器只读核查继续进行。

D2 标准包 `light-light126-d2-prep-arch03-20261109_020924-71902ce3b9d7.zip` 已在干净目录核验：355 个输入文件、14 组独立整数复算及 14 份固件完整字节布局均通过。包为 10,706,838 字节，SHA256 `594e17548064aba1656795faaed5c1f02290981081ed3a2c1f83708825e5d155`，包提交 `71902ce3b9d76a0aa5669914fbe23dd56362d185`；[回执](../../handoff/team/evidence/UNDERGRAD_D2_PACKAGE_20261109.json)明确记录尚未上传。

D2 后续源码 `cc5e193da0c7657b2b0f4e0599bdd7bf2aa40e4f` 又补齐标准单元厂商测试入口、A/B/A 连续任务固件与观察器，见 [后续证据](../../handoff/team/evidence/UNDERGRAD_D2_FOLLOW_ON_20261109.json)。40 项 Python 测试、重复计时窗口、两种监视器展开、标准单元本地替身测试均通过；三任务观察器使用**合成流量**核对 76,032 条结果并拒绝四类反例，明确没有 CPU 或算术硬件。两份连续固件只完成构建与字节布局核验，不能写成真实 CPU 连续任务通过。

**ASIC 分支更正（02:45）：** 服务器精确文本核对确认 TCM/ROM 使用 `ifndef FPGA`，此前截图误读为 `ifdef`。早期 ASIC 安装器只修改了未被 ASIC 选中的分支，未替换实际 wrapper。此前所有 ASIC 入口均未执行，不能作为链接证据；`71902ce`、`49f0556` 的准备包不可用于 ASIC 链接。当前安装器已改为显式去除该条件，选取完整 TCM 端口后绑定真实宏，ROM 选用平台现有常量逻辑，并加入嵌套条件及 ROM 反例测试。旧包保留，须从修正提交重新打包后再执行服务器 ASIC 阶段。

修正已提交为 `bc6ebbe194210a50d1fe56b4022830672b2a049b`，41 项 Python 测试通过。该提交的标准/连续包分别含 367/422 个文件，均在全新目录通过完整哈希、14/21 组标准库整数复算和 14/2 份固件完整字节布局核验；详见 [更正与包回执](../../handoff/team/evidence/UNDERGRAD_D3_BRANCH_PACKAGE_20261109.json)。这两包均未上传；原平台实际补丁、ASIC 链接及 CPU 执行仍待服务器验证。

ASIC 启动准备新增 `asic_boot.py`、`asic_soc.py`：从已核验的固件字节镜像生成 32 份物理 SRAM 行文件，仅在复位保持期间初始化 ITCM 程序/源数据区。真实任务仍由 CPU 搬运、计算和写回。厂商模型实际布局为 `mem[0:511]`、每行 128 位，逻辑地址 `A` 对应行 `A>>3`、第 `b` 位对应物理位 `8*b+(A&7)`；不是普通 4096 项数组。独立物理布局替身已通过全部 32,768 字、262,144 字节读回，并拒绝缺失宏文件；45 项 Python 测试通过。`asic_boot` 厂商单测和 `asic_soc` 真实 ASIC 分支 RTL 入口均未在服务器运行，不能当作门级或时序通过。原官方 TB 的补丁锚点已只读核实，实际完整平台补丁仍需服务器执行检查。

后续入口：`server_run.py asic_boot --session <new>`，随后 `server_run.py asic_soc --session <new> --cases layer_01`，再扩至标准 14 用例。两者均须新包、上传授权及团队锁；不能使用不含这些入口的早期包。

D3 整机综合与功耗库准备：`asic_synth` 从新 ASIC 平台副本链接并生成整机网表、SDC、面积/时序/约束报告；严格要求 130 个大宏、8 个小宏，逐叶实例面积求和与总报告一致。报告状态仍为 `reports_ready_review_required`，不会自动声称 setup/hold、约束覆盖或计分面积通过。时钟采用精确 150 MHz HF 和原 TB 的 66 ns LF；复位外任务模式、JTAG 静止及 I/O 预算均显式记录，不屏蔽 LF/HF 交叉路径。新增时钟模式观察器本地正常模式及四类反例通过，实际 CPU 模式仍待测。

服务器只读确认两份 SRAM Liberty 各有 80 个内部功耗组、4 个非零漏电组，分别涉及 VDDPE/VDDCE；总漏电字段的 0 不能替代这些分组。指纹、面积及功耗元数据检查已接入 ASIC 链接。50 项 Python 测试、8 份服务器脚本 Python 3.6 语法、生成 Tcl 完整性检查通过；这些均不是 DC 或系统功耗运行结果。

VCD 校验又补充两项 Python 测试，总数为 52：要求整机六类层级齐全、一次完整记录区间与任务起止时间一致，拒绝截断/错窗口/缺部件/重复区间/时间倒退/未声明信号等情况，保留未知值统计。检查按流读取，避免一次载入整段大型波形。当前只有合成 VCD 解析测试；尚无新实际 CPU 同窗口 VCD、活动映射或功耗结果。

最新可用包来自 `de6e6e41ae5b89c000b48c4a49dd398db8028f95`（运行实现 `83126c3`）：标准包 10,769,549 字节/383 文件，连续包 14,388,276 字节/438 文件。两包已重新通过干净解包、完整哈希、14/21 组整数参考、14/2 份固件字节布局检查；标准包干净目录内 52 项测试通过，之后又复核两包共 821 个输入哈希。详见 [最新包回执](../../handoff/team/evidence/UNDERGRAD_D3_READY_PACKAGES_20261109.json)。两包均未上传，自动审批要求的明确上传授权仍待答复。下一步必须通过新的实际服务器运行获取证据，不能继续用本地准备结果代替验收。



## 后续服务器入口与边界

官方 E203 原目录、工艺库及厂商宏只在现有共享服务器。新增验证包可本地生成；运行前必须在既有允许路径中查看共享桌面、活动进程及 `.arch02_team_lock`。当前本地文件中没有完整官方平台源码，不能凭模块名猜测 ASIC 存储/时钟适配后宣称可链接。

下一阶段优先顺序：核对平台 ASIC 分支及 TCM 容量/读延迟/掩码 → 修复工艺绑定 → 整机链接/综合 → 精确时钟下的约束覆盖与 setup/hold → 网表功能 → 同窗口功耗。新脚本仅修复两块 DC 的时钟约束和审计门槛，不代表整机 DC 已实现。旧报告由原版本审计工具解释，不能用新版审计器补盖严格 150 MHz 通过。

本轮 Python 单测共 29 项通过，服务器侧改动通过 Python 3.6 语法检查；尚未在 DC 执行新的时钟报告命令。正式时序仍必须以真实新工具运行判断。

## D2 本地准备与实际接口核对

- ITCM `32768×64`、DTCM `65536×32`，各 256 KiB、各 32 个 `RAMSP4096X16`。新适配保留单周期有效读取、逐字节写掩码和 SRAM 复位保留；全地址写入/反向读回、所有 bank 边界及全部掩码在 behavioral、pin_mock 两种 XSim 模型中通过。两种模型合计 197,364 次完整字核对，不是厂商模型或 CPU 结果。
- 原非 FPGA TCM/ROM 路径选择独立 SRAM/ROM wrapper；另一分支提供完整 `sirv_gnrl_ram` 端口和常量 `sirv_mrom`。修正后的 ASIC 安装器在新副本中显式去除条件、把 TCM 完整接口绑定到真实宏，并采用已有常量 ROM，不定义全局 FPGA。PLL 原模块直接透传参考时钟，不把它说成已实现模拟 PLL。
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

## D2 后续连续任务与标准单元准备

标准单元模型已只读核对：同工艺 `scc40nll_vhsc40_rvt.v` 为 2,198,450 字节，包含全部 11 个目标模块，无额外 include，SHA256 锁定于 `technology_bindings.json`。`stdcell` 阶段使用实际模型的 `functional` 分支，只验逻辑与引脚；本地 `stdcell_pin_mock.sv` 是明确标注的独立替身，不能当作厂商通过。

连续固件把 A、B 两组独立输入放在启动前 ITCM 源区，由 CPU 完整搬运并计算 A→B→A。B 后执行 17 字部分装载、中止、周期超时及恢复；专用观察器核对实际 MMIO START/LOAD/ABORT 次数、三份完整写回和三段计时。普通 `soc` 拒绝连续固件，连续入口要求 `sequence_cpu_v1`，避免普通监视器在首任务后提前退出并误验收。

本地观察器测试保留了失败尝试：XSim Windows 参数分割、动态字符串 `$readmemh` 路径及填充空格文件名。实际 CSV 的 `x` 值曾被独立检查拒绝；修复后，所有参考数组在读取前置为未知，读取后逐项检查完整/已知。缺失参考、重复输出、缺少 ABORT、跳过超时均必须失败。后续测试产物与源码提交的字节一致性已核对。

准备入口：

```text
python workspaces/arch03/scripts/local_stdcell_verify.py --vivado-bin <Vivado/bin>
python workspaces/arch03/scripts/local_sequence_monitor_verify.py --vivado-bin <Vivado/bin> --data <14-case-data>
python workspaces/arch03/scripts/build_sequence_firmware.py --zig <zig> --data <21-case-data> --output <new-dir> --cases layer_01 worst_error --next-case layer_12
python3 workspaces/arch03/scripts/server_run.py stdcell --session <new-session>
python3 workspaces/arch03/scripts/server_run.py sequence --session <new-session> --cases layer_01 worst_error
```

最后两条尚未运行。连续包应单独使用对应固件和包含两个主任务及 layer_12 的数据；标准 14 用例审计不能给连续包盖通过结论。连续 CPU 入口仍沿用明确标识的功能 TCM 分支，ASIC CPU 启动、综合网表和功耗必须另行验证。

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
