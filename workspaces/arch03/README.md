**02:55更正：当前C32-A约束未通过。原始报告有326条max_transition违反、旧解析器未识别，之前“0约束违反”记录有误。完整功能与数值仍保留，但不能冻结，需新映射修复及同网表重新验证。详见[当前修复检查点](../../CONTEXT_CHECKPOINT_20261117_C32_DRC_REPAIR.md)。下文较早数值为未合格网表结果，不能作为最终阶段结论。**

**当前入口（2026-11-17 02:20）：** S0/P80/C80已冻结。C32-A自己的ASIC14/恢复/竞争/240/精度、新综合、门级14、SAIF12、时序/约束查询和PT12全部完成；finish03已自然退出，export_review03正在汇总与独立模型审阅。固定12为2078.1572task/s、保守0.722402955mm²，初步整机48.9738373mW、23.5659905µJ/task；布局前估算，最终阶段尚未冻结。见[当前检查点](../../CONTEXT_CHECKPOINT_20261117_C32_REVIEW.md)、[结果索引](C32_EVIDENCE_INDEX_20261117.md)、[阶段对照](C32_PROGRESS_20261117.md)和[有效计划](IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md)。桌面T80及旧八路全部保护，不重启历史队列。下方较早状态仅供历史追溯。

**最新入口（2026-11-16 13:37）：** P80已完整冻结，C80自身ASIC14、恢复及CPU竞争通过，固定12平均70603.1667周期/2124.5506task/s；原队列正执行新综合。见[C80进度](C80_STAGE_PROGRESS_20261116.md)、[C80服务器检查点](../../CONTEXT_CHECKPOINT_20261116_C80_SERVER.md)与[有效计划](IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md)。C80自己的PPA/240/门级与功耗仍待完成，C32/G32未开始。桌面T80、旧八路及P80全部证据保持。下方为历史快照。

**当前入口（2026-11-16）：** 执行[T80→P80→C80→C32→G32](IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md)，最终32PE、项目面积≤1.00mm²，正式批量只用前20条。S0已验收、冻结及归档；P80三深度各14例已通过，固定12层均为77,545.333周期，先选最小深度2。自己的恢复/竞争/240已通过，6082560输出及total零差异。新1023646综合工具修复已在真实DC完成共享块映射，当前加速器块运行；整机PPA尚未验收。见[阶段进度与搬运统计](P80_STAGE_PROGRESS_20261116.md)、[本轮验收表](ACCEPTANCE_T80_P80_C32_G32_20261115.md)、[最新检查点](../../CONTEXT_CHECKPOINT_20261116_P80_LIBRARY_FIX.md)及[根交接](../../CONTEXT_HANDOFF.md)。服务器桌面T80及全部旧八路文件保持原样；旧T64/G64后续不再派发。以下均为历史入口，不据旧PID恢复任务。

**历史入口（2026-11-13 18:39）：** [T80→T64→G64](N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md)。T80真实ASIC14/前20条240任务及恢复/竞争通过，现有队列正在综合；T64本地验证通过，独立包传输中，尚无服务器验收。旧8路全部数据禁止删除/覆盖。见[当时检查点](../../CONTEXT_CHECKPOINT_20261113_T80_T64_1839.md)。

**当前入口（2026-11-13）：** 执行[T80→T64→G64](N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md)。T80真实共享读回ASIC14已通过，前20条240任务回归进行中；新PPA未验。旧N1/N2条目仅为历史，见[当前检查点](../../CONTEXT_CHECKPOINT_20261113_T80_EXTENDED.md)。

**2026-11-13 15:05 progress:** [N1 accepted results and N2 work remaining](PROGRESS_N1_N2_20261113_1505.md). N1: 5048.635 task/s, 0.951149 mm2, 61.77735 mW / 12.23644 uJ in declared pre-layout model scope. N2 local array/datapath14 passed; actual ASIC/PPA pending. Older entries below are historical.

**当前入口（2026-11-13 02:45）：** 正执行[N1→N2→D1→D2计划](IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md)。N1真实ASIC14、恢复、CPU竞争通过；固定12平均29711周期/5048.635task/s（150MHz折算）。新综合运行中，自己的1200/门级/功耗/完整浮点精度未验，未进入N2。B0及历史备份保留，状态以[根交接](../../CONTEXT_HANDOFF.md)和[N1清单](N1_ACCEPTANCE_20261113.md)为准。下方停止/等待和旧待办是历史记录。

**当前入口（11月12日19:22）：** 直接5×16脉动B已完成自己的真实ASIC/E2031200任务、30,412,800输出，零失败；ASIC14、CPU恢复/竞争、DRC06同网表功能门级14和声明任务模式时序/面积审核已通过。SAIF/VCD方法对照已通过，B自己的活动与功耗仍待完成。12层完整平均30502.3333周期、150MHz折算4917.6566task/s，面积保守上界1.0990947mm²。见[B交付索引](SYSTOLIC_B_DELIVERY_20261112.md)、[实施计划](IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md)、[复现手册](SYSTOLIC_B_RUNBOOK.md)和[最新检查点](../../CONTEXT_CHECKPOINT_20261112_1922_SYSTOLIC_B.md)。R4及其全部交付证据保留；更早37组停止记录不是当前批量状态。

[11月12日22:15收尾交接：实现、结果、探索路径、远端作业与VNC释放](SYSTOLIC_B_STAGE_HANDOFF_20261112.md)。本次交接取代下方旧进度；等待用户新计划，不启动新工作。

以下按日期保留历史，不覆盖上述进度或实际运行终态；不得据旧PID重启队列。

**11月12日12:48：B ASIC14/门级14均已通过；综合4项max_transition违规尚待修复，时序未批准。** [历史检查点](../../CONTEXT_CHECKPOINT_20261112_1140_SYSTOLIC_B.md)记录原队列终态、279.51GiB授权清理及新修复工具。当时自己的1200/功耗待验，R4保留。

**Active: direct 5x16 systolic B/v3, credits3; ASIC/E20314 passed (30502.33 cycles / 4917.66 task/s at150MHz).** Read [B plan](IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md), [B acceptance](ACCEPTANCE_SYSTOLIC_B_20261111.md), [B reproduction runbook](SYSTOLIC_B_RUNBOOK.md), and [latest checkpoint](../../CONTEXT_CHECKPOINT_20261112_0830_SYSTOLIC_B.md). Authorized obsolete MMIO8 wave cleanup released112.42GiB; R4/B evidence retained. Fresh synth02 PID183038 and validation02 queue184658 are running as last observed08:52 on Nov12; inspect live state before actions, never duplicate launches. Source candidate frozen; own1200, mapped gate, timing/area and SAIF/power still require their own evidence. R4 remains delivery fallback.

# 架构三：E203 System Bus 集成

**11月11日本轮收尾：** 先读[实现与探索总结](ICB32_STAGE_REPORT_20261111.md)、[交付入口](ICB32_DELIVERY_20261111.md)和[收尾检查点](../../CONTEXT_CHECKPOINT_20261111_WRAPUP_ICB32.md)。R4自己的1200/30412800、门级14/活动12、干净复现、最终报告及交付准备包已完成；4333.256task/s、71.8126mW、16.5724µJ。系统功耗未知影响仍未审定。按用户要求保存同步并等新计划，现有原8路L02功耗保留，后继队列不启动。下方时间标记为历史。

**11月11日13:00当前状态：** 新ICB32 / R4自己的真实ASIC/E203 1200任务、30412800输出全部通过，零失败、一次编译。同网表gate14/activity12、干净ASIC14复现、十二层功耗及稳定任务模式时序/面积上界审阅均已完成。最终锁内报告已完成全部回执重审，系统功耗未知活动影响仍未批准；[验收表](ACCEPTANCE_ICB32_20261111.md)与[当前检查点](../../CONTEXT_CHECKPOINT_20261111_1240_ICB32.md)为接续依据。

**11月11日03:10当前入口：** 新R4真实ASIC/E20314例、354816输出和IRQ/WFI通过，12层平均34616周期/4333.256 task/s（150MHz折算）。新综合已完成，setup/hold为正、224宏/0锁存器/无组合环，新增面积保守上界0.926562mm²；完整时序和功耗审核尚未闭环。497包真实CPU竞争2例/无复位恢复10阶段均通过，当前同网表门级14/活动12已运行PID209764；新最终1200和干净复现仍待办。以[新版验收表](ACCEPTANCE_ICB32_20261111.md)、[运行手册](ICB32_RUNBOOK.md)及根交接为准；下方较早状态为历史。

**11月11日01:24执行入口：** 当前有效要求已改为[32位 ICB 搬运优化与16×4 MAC计划](IMPLEMENTATION_PLAN_ICB32_C64_20261110.md)，当前运行入口见[ICB32运行手册](ICB32_RUNBOOK.md)。新R4本地14例、反压/恢复及无复位序列通过，尚不代表真实E203验收。49759e1诊断包已由板端FileZilla上传，服务器630输入及IRQ/竞争/序列三套固件哈希通过；e65的唯一ASIC14→综合后继仍在等待旧队列。生产fcd的1200通过及664.393 task/s保底不变。下方旧计划、旧37组和早期“未完成”均属历史，不覆盖根交接最新状态。

**11月10日10:40当前入口：** 生产fcd配置已完成ASIC14、恢复/竞争、门级14/12活动，668最终1200通过30412800输出，a2完整报告再次独立重审通过；任务模式时序及0.434796781612mm²面积上界已审定。12层PT数值及活动来源/设置核验完成，系统功耗仍待未知活动影响与建模审核。原8路同源首层门级/PT完成，完整对照待办。最新工具b85通过215干净tests及679服务器输入，生产保持冻结。以下旧进展均保留为历史，实时作业以根交接为准。

**11月10日04:43更新：** ASIC14、门级14/12活动、CPU竞争2例均通过；首层PT已无工具错误并成功提取原始数值，实际JSON/CSV/中文初步报告已导出。时钟/禁用弧/高扇出对象已查明，保持任务模式和布局前范围。最终1200首轮在第一例回执重读因tuple/list表示差异停止，输出检查通过但整批failed；仅解析器修正及61项相关检查已通过，尚待新包和全新批次重跑。系统功耗模型/未知活动、其余11层、原8路新PPA及最终交付仍缺。以根交接最新条目为准。

**11月10日03:50更新：** 生产fcd的真实ASIC14例及恢复序列已通过；a53的gate03已完整通过14例354816输出、12份全窗口活动，每任务225770周期。414包首层功耗正在运行。严格时序、系统功耗、CPU竞争、最终1200、新MMIO8 PPA和交付仍待验，详见根交接最上方记录；下文早期进度保留为历史。

**当前已按用户明确实施指示恢复，直接推进16路DMA。** 有效路线为[三天DMA16计划](IMPLEMENTATION_PLAN_DMA16_20261109.md)，H0为11月9日17:16:08，H28冻结为11月10日21:16:08。先读根目录[交接](../../CONTEXT_HANDOFF.md)和[检查点](EXECUTION_CHECKPOINT.json)的dma16_execution。旧synth07于11:33:34完成报告收集，setup/hold为正，仍待约束、门级与功耗闭环；不得重启原运行或用其网表证明新DMA通路。

新增独立[DMA16 ABI](DMA16_ABI.md)、linear16、DMA/公平仲裁/原SysMem加载源、固件及ASIC入口。fcd445f真实ASIC/E203 IRQ14例354816输出及CPU十阶段恢复通过，每任务225770周期；新综合setup/hold非负、无组合回路，严格PPA审核尚未闭环。11月10日02:10，gate03已完成前五层完整门级与活动，余下继续。原8路同源ASIC14例通过、每任务3843121周期。最终1200、12功耗与复现仍待完成，详细证据见[实施记录](../../handoff/team/evidence/DMA16_IMPLEMENTATION_20261109.json)。以下旧8路接口和D2/D3记录保留为历史，不代表当前DMA16验收。

2026-11-09 正执行本科组修订计划：600 条开发样本数值评估、真实 CPU 连续恢复、修正配置 ASIC 分支 14 用例（`d3_full02`，354,816 输出）均已通过。旧配置门级首层和完整任务活动审计通过；功耗首轮因 PT-063 被拒绝，环境与详细报告修正包已上传。`d3_synth04` 锁存器为 0、hold 转正；随后 `d3_synth05` 因 LF 输出端口的小写 o 误写成 0 而不可验收。精确名称及 DC 约束出错立即停止修正已本地测试，待新独立综合；严格时序和完整门级/功耗仍未完成。

当前状态见 [验收清单](ACCEPTANCE_20261109.md)，交付和同配置复现顺序见 [交付索引](DELIVERY_INDEX_20261109.md)，接口见 [数值格式](NUMERIC_FORMAT.md)。以下 D2 及更早服务器记录是历史过程，不代表当前修正包已经验收；其中“尚未运行”等描述以当前验收表为准。

D2 本地准备见 [验收清单](ACCEPTANCE_20261109.md) 和 [证据](../../handoff/team/evidence/UNDERGRAD_D2_20261109.json)：完整容量 TCM 宏适配通过两种替身模型，旧工艺单元已按目标 Liberty 元数据显式绑定，新增实际写应答计时观察器及可选同窗口 VCD。源码提交 `860a6b3`，37 项 Python 单测通过；新固件、厂商宏、整机 ASIC 链接和功耗均未服务器验收。

后续提交 `cc5e193` 增加标准单元厂商测试入口、A/B/A 连续固件、超时/中止被动观察器及重复窗口检查。40 项 Python 测试通过；合成观察器测试明确 `cpu_executed=false`，实际 CPU 连续执行仍待服务器验证。见 [后续证据](../../handoff/team/evidence/UNDERGRAD_D2_FOLLOW_ON_20261109.json)。

状态：Linux FileZilla 上传、293 个受测输入核对、厂商模型 ICB 与真实 E203 C 驱动各 14 组（354,816 输出）、两块 DC 及独立审计通过。受测源码 `f00e7acf7b40`，审计工具 `8fc4756a715c`；见 [正式范围与哈希](../../handoff/team/evidence/ARCH03_ACCEPTANCE_20261108.json) 和 [保留的失败尝试](../../handoff/team/evidence/ARCH03_SERVER_20261108.json)。
**两块 DC 不是整机 DC；综合后功能与端到端分类仍未验证。100 样本批量于 2026-11-08 按用户要求停止以优化吞吐：软件 1,200 组通过，CPU 37/1,200 组通过，第 38 组中断。整批尚未验收。**
这是开发中的架构三，不替换架构二或历史快照。

## 基线与设计

- 团队基线：main `8aa230695668458673b370bf85f8a397fc507a34`。
- 计算核心直接引用 `../arch02`：8 路 MAC、16 位输入/权重、40 位偏置、41 位求和、移位舍入及饱和。
- 官方服务器平台：`/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master`。
- 163 个 RTL/header、原测试台及文件列表的规范化 SHA256：`ee8bfecd81e192a974be81479ef8a01793de3e59c2e2f8769886e8e86143e56e`。已修正初始记录中 `8d`/`d8` 相邻字符抄录错误；错误值导致首包 SoC 阶段在复制平台前退出，失败记录保留。
- 已只读核对：32 位 ICB 地址/数据，4 位写掩码；存储子系统 O5 示例窗口从 `0x40000000` 开始；O4 SysMem 原为空应答；ITCM/DTCM 基地址分别为 `0x80000000`/`0x90000000`，各 256 KiB。
- 集成脚本已在新目录成功复制并修改固定平台；原目录、历史运行及其中的临时编辑文件未修改。首次编译发现 TB 局部 `FPGA` 宏晚于 RTL，现改为 SoC 编译命令全局定义，使用平台原有功能 TCM/ROM/时钟分支。加速器与新增共享 SRAM 仍使用真实厂商宏；功能 TCM 分支不能作为整机 ASIC 存储工艺验收。

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
功能 SoC TB 复用原 ITCM 装载流程，移除旧教学测试固定 PC 的退出条件。本轮时钟为显式 1 fs 精度、6.666666 ns 周期，旧 6.667 ns 配置只属于历史运行。新增 ASIC 入口在复位期间按厂商物理行列布局预装 ITCM 源镜像，运行时仍由 CPU 完整搬运、计算和写回；目前只通过本地独立物理布局替身验证，实际 ASIC CPU 尚未执行。

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
python3 workspaces/arch03/scripts/server_run.py tcm --session asic01
python3 workspaces/arch03/scripts/server_run.py asic_link --session asic01
python3 workspaces/arch03/scripts/server_run.py stdcell --session asic01
python3 workspaces/arch03/scripts/server_run.py asic_boot --session asic01
python3 workspaces/arch03/scripts/server_run.py asic_soc --session asic01 --cases layer_01 --activity-cases layer_01
python3 workspaces/arch03/scripts/server_run.py asic_synth --session synth01
python3 workspaces/arch03/scripts/server_run.py gate_soc --session gate01 --synth-run <completed-asic_synth-directory> --synth-summary-sha256 <verified-summary-sha256> --cases layer_01
```

`tcm` 检查实际 SRAM 功能模型；`asic_link` 检查完整 SoC 的工艺链接与宏数量，两者已有实际服务器通过记录。`soc --activity-cases layer_01` 可生成该用例全系统同窗口 VCD；固件、监视器和测试输入须与受测包一致。VCD 存在不代表功耗已估算或活动已正确映射。

运行前仍须核对共享桌面、已有 EDA 进程和临时修改；入口复用 `.arch02_team_lock` 目录锁。
每个阶段只运行一次；失败保留，修复后提交新包/新会话。中断时若子进程仍运行，锁保留，禁止直接重启。
`dc_accel`、`dc_shared` **仅覆盖加速器接口块和共享 SRAM**。`asic_synth` 才生成整机映射网表、SDC、setup/hold 与约束报告，以及逐叶实例面积表；其完成状态为 `reports_ready_review_required`，不是整机时序验收通过。必须审查所有时钟传播、未约束路径、LF/HF 交叉、结构警告、复位/工作模式和 I/O 假设。仅凭阶段完成标记不能宣布验收。

整机首轮实际 DC 暴露了端口拼写、工具周期舍入、多路径组和虚拟常量分类问题，失败报告均保留。当前综合请求周期为 `6.666666 ns`，仍严格检查工具实际读取值不得大于 `20/3 ns`；不接受将 `6.666667 ns` 视为舍入容差。约束错误会立即退出。DC 的两个逻辑常量源单列零综合面积，不表示物理 tie cell 已插入或免费。

`gate_soc` 要求完整综合阶段及明确摘要哈希，复核网表、SDC、输入、当前 RTL/固件以及平台安装器和工艺绑定的一致性。它采用映射后 ITCM 实例路径预装启动镜像、复用实际 CPU 总线写回检查，并支持 `--activity-cases layer_01`。历史网表首层已实际通过，当前修正配置仍需完整 14 用例；门级功能通过不会自动认可负裕量、未约束路径或功耗。该入口没有 SDF，不能当作带延迟时序仿真。

完整门级套件省略 `--cases` 时默认运行 12 层、extremes、rounding。为首层同时采集全窗口活动的命令形式为：

```text
python3 workspaces/arch03/scripts/server_run.py gate_soc --session <新的唯一会话名> --synth-run <该配置已完成的asic_synth目录> --synth-summary-sha256 <已核对摘要SHA256> --activity-cases layer_01
```

必须先取得对应综合结果并核对共享锁，不能把示例占位符直接执行，也不能重用已有会话。完整活动扫描会读取整个波形，期间仍由驱动持有同一协作锁。

系统功耗入口 `asic_power --session <new> --gate-run <passed-gate-directory> --gate-summary-sha256 <digest> --cases layer_01` 只接受通过功能检查且带完整窗口 VCD 的门级用例。它校验所有来源，按监视器的纳秒起止时间调用 PrimeTime PX，保留整机/层级/SRAM 功耗和活动未标注清单。状态仍为 `reports_ready_review_required`。旧配置已实际取得 PrimePower 许可证并产生报告，但 PT-063 启动错误使该运行不可验收；LC 子进程环境和详细单位/未知跃迁/边界网络报告修正仍待新运行。提取寄生参数、时钟网络/线负载假设、未知活动、宏模型及 µW/mW 单位差异须另行审查，不按零处理缺项。

`asic_soc` 不定义全局 FPGA，使用真实 TCM/共享/加速器 SRAM 功能模型和指定标准单元功能模型。时钟模式观察器在完整任务期间核对 test_mode=0、pllbypass=1、plloutdivby1=1 和启动选择，与稳定任务综合模式一致；修正配置 14 用例已通过，这不代替门级、时序或功耗验证。`memory_technology.json` 固定两份 SRAM Liberty 指纹和功耗组数量：`cell_leakage_power=0` 并不表示零漏电，库中有非零条件漏电项。物理面积单位已经 LEF 交叉核对，共享 SRAM 官方计分归属仍未确定。

启用活动记录时，审计器要求 VCD 包含 CPU、互连、加速器、共享 SRAM、ITCM/DTCM，且只能有一段与实际任务起止时间一致的 `$dumpon`/`$dumpoff` 区间。截断、错窗口、缺部件或未声明信号会失败；未知值记录单独计数。门级入口使用 `activity_fast.py` 和原生完整流扫描器，同时计算完整文件 SHA256；历史 29.86 GB 真实 VCS 波形已通过该审计。它只核验波形范围、窗口和完整性，不代表新网表活动映射或系统功耗通过。

完成同一受测包的 `icb`、`soc`、`dc_accel`、`dc_shared` 后，从包含已提交审计工具的新完整包执行：

```text
python3 workspaces/arch03/scripts/audit.py <受测完整包绝对路径> --session acceptance01 --output runs/audit01
```

审计工具先核对自身包与受测包全部硬件、驱动、数据、配置和执行脚本字节一致；新增审计工具/文档可来自后续提交。
它独立重算 14 组整数参考，重新检查 ICB/真实 CPU 的全部输出与饱和计数、源码/捕获/综合产物哈希，并以匹配的库重新加载两个块的 DDC 核对链接、锁存器和宏数量。
输出目录必须不存在；运行使用同一团队锁。`ARCH03_AUDIT_PASS` 仍明确表示 `whole_soc_dc=false physical_signoff=false`，不扩大通过范围。

尚待完成：新配置严格 150 MHz 及约束覆盖审核、完整 14 用例门级功能、同窗口系统功耗和最终计分面积归属。工艺组件、修正配置 ASIC CPU 14 用例、连续恢复和 600 样本开发精度已有各自范围的通过记录。官方评测数据在评测后公布，通用输入工具不以其发布为前提。旧 100 样本的 1,200 组 E203 批量验证保留为增强项，仍暂停。
这些条件通过前 PR 保持草稿，不能合并并宣布完成。

## 服务器 100 样本批量验证

用户指定 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，固定 manifest SHA256 为 `0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。它包含 100 个不同样本、每个 12 层 Q12 完整矩阵；目录原有 PASS 仅为软件记录。

本批在 `sample_000004_layer_02` 运行时按用户要求停止。已通过 37 组、937,728 个输出，已完成产物哈希再次核对一致；父子进程退出，驱动自行释放团队锁。原运行器将 SIGTERM 导致的仿真退出码 255 记为 `failed`，原始记录不改写；独立停止回执明确原因是用户要求优化吞吐，不是已观察到算术错误。见 [停止记录](../../handoff/team/evidence/ARCH03_BATCH100_20261108.json)。暂停期间不自动续跑旧任务。

`scripts/batch_soc.py --help` 给出参数。使用已提交的新完整包，指定已通过的受测包、审计 JSON 及其 SHA256；输出必须是新包 `runs` 下的新目录。入口锁定原数据和独立输入快照，重算全部整数参考，再使用同一平台/RTL 编译 E203。它从已验证的 ELF 生成每层镜像，并先逐字节复现全部 14 份已通过镜像。每组必须由真实 CPU 搬运输入、执行驱动并写回全部 25,344 个结果。

状态与逐组回执保留在输出目录。`--resume` 只在确认没有仍运行的原作业、团队锁已由负责人正常处理后使用；工具不会清除已有锁。续跑核对同一工具、数据、编译输入/程序及已完成捕获，保留未完成尝试。最终只有 `ARCH03_BATCH_PASS samples=100 cases=1200 outputs=30412800 cpu_executed=true` 才表示本批完整矩阵通过，不表示语音分类验收。
