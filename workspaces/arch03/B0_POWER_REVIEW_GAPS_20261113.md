# B0功耗只读审查：已知证据、剩余缺口和最小读取入口

记录时间：2026-11-13 01:57（Asia/Shanghai）。本次为N1阶段的B0对照证据整理；不实施N2，不重跑B0的1200、门级、SAIF或PT。最新状态以根检查点为准，本文件不宣称服务器实时状态。

## 已确认的基线与本次范围

已重读有效计划`IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`、根交接、01:20检查点及其01:50增量、团队STATUS/SYNC。生产B0仍为`63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86`，N1冻结实现`9305c6948c764fed01fe86b20bb3db94170299ab`未修改。

根代理在00:34、00:39已读取服务器最终报告。B0固定12层和自己的1200均已完成，正式报告在ced包的`runs/systolic_b_backup_report01/report.json`；不能再引用22:15交接中“尚无功耗”或23:56“报告仍运行”的历史状态。

| 项目 | 已读取的最终值及范围 |
|---|---|
| 时间加权整机平均功耗 | `0.06983707336109641885320248724 W`，布局前估算 |
| 平均单任务能耗 | `0.0000142012898511016506547 J` |
| 固定12层平均周期 | 30502.333333，按150MHz折算4917.656573task/s |
| 项目面积保守上界 | 1.0990946959mm²，独立面积审核记录另存 |
| 功耗影响审核 | `system_power_verified=false` |

`systolic_b_report.py`的导出器保守地固定上述verified字段为false；该字段本身不能定位缺失模型，也不意味着功耗数值没有生成。应查看实际未知活动、模型及工具证据后另作有范围的审查，不能直接改布尔值解决缺口。

精确数字更正：根代理后续实际inventory02及独立Decimal复算确认`ΣE=0.0001704154782132198078564 J`、`Σt=2440186.422648 ns`，故`ΣE/Σt=0.06983707336109641885320248724 W`。本文件最初的长小数为手抄错误，已按原始能量/时长更正；69.8371mW展示值和14.2013µJ/task不变。这不是新功耗运行，也未更改原报告。

## 已有证据能证明什么

1. R4 L01的SAIF/VCD方法对照已经通过：整机相差0.013849%，主要模块最大相差0.534759%，均≤1%。实际PT连接检查证明当次1060个默认声明都没有直接或叶节点负载。该证据批准SAIF传递方法；1060不是B0可直接沿用的默认网数量，也没有批准B0未知活动影响。
2. B0功耗入口要求完整任务窗口、精确6.666666ns的独立SDC、同一网表/固件/库身份；switch和static映射表都必须满足`default=已逐网证明的孤立数`、`exact+implied+isolated=total`。已映射信号仍可能含X/Z，映射完整不等于未知影响已消除。
3. 本地已有的B0详细活动观测只有L01：618149个声明，41406个有未知，18620个全窗口未知。CPU/TCM/加速器/共享存储均有未知声明。这些包括别名，模块统计交叠，不能相加，不能把比例称为功耗误差。
4. 原生SAIF记录VCS合并TX（X或Z），不能从中分别报告X与Z驻留时间。组件摘要只保留前12个未知名称示例，不是完整未知网清单。
5. 两种SRAM Liberty已经有指纹、单位、80个internal_power组及4个leakage组的检查机制。SRAM leakage单位为1mW，标准单元为1µW；SRAM两路电源为VDDPE/VDDCE。`cell_leakage_power=0`不能替代条件/电源组的实际泄漏值。旧R4实际泄漏解释可作为模型分析线索，但B0的92个内部小宏加128个复用大宏仍需绑定自己的原始报告。

具体来源：`handoff/team/evidence/SYSTOLIC_B_SAIF_METHOD_20261112.json`、`SYSTOLIC_B_ACTIVITY_PARTIAL_20261112.json`；`scripts/native_saif_activity.py`、`native_saif_isolated.py`、`systolic_b_power.py`、`systolic_b_report.py`；`memory_technology.json`和旧`ICB32_POWER_REVIEW_20261111.md`。旧文件的阶段状态和数字不转移为B0或N1的PASS。

## 仍需读取与判断的具体缺口

| 缺口 | 最小现成证据读取 | 可以得出的结论与边界 |
|---|---|---|
| 全12层最终未知统计未带回本地 | 最终report、activity summary的每层statistics/component_activity | 得到真实每层驻留、别名范围和未知例名；不需再解析114MB/层SAIF |
| B0自己的未注释与孤立网证明 | 每层numbers、activity_sources、unannotated前后、native_isolated_connections.tsv | 验证所有默认网是否都有本次零连接证明；不能拿R4的1060替代 |
| 连接到实际负载的未知信号影响 | 现有完整未知网清单、实际映射网表连接/模型内部归属，以及已有knownness monitor回执（如果存在） | 区分无负载声明、外部模型内部状态和真实数据/控制路径；当前摘要的几个例名不足以排除影响 |
| 未知值是否只在无效周期 | 对应有效位、CEN/WEN、在途波前/接收条件的现成逐周期已知性证据 | SAIF只保留累计驻留，不能恢复X与valid/CEN的时间相关性；如未保存这类证明，本次只读现成摘要不能关闭此项 |
| 实际220宏的模型与泄漏 | 本次综合technology/memory verification、PT units、power_sram、power_hierarchy、numbers | 核对92/128归属、两种库SHA和单位、双电源/when条件及各宏实际泄漏；不能因有模型文件就认定激励覆盖全部情形 |
| 工具错误/警告与时钟条件 | 每层power.log、verbose、timing_check、disabled_timing、clock输入/测量、boundary报告 | 逐项审查实际B0警告及禁用弧、时钟/IO边界；旧版本PSW-208/PTE-003解释不直接作本次豁免 |
| 布局前模型边界 | verbose/库/SDC中的线负载、时钟网络和寄生条件 | 如实保留无布局后寄生/时钟树的估算范围；不写物理签核PASS |

上表中的逐周期有效性证明与未知敏感度不是同一事项。旧DMA16的X敏感度及有效MAC已知性扫描不属于本B0网表，不可搬用。若本B0没有相应现成证明，需要根代理决定后续最小范围补证方法；本次没有启动或安排整套B0重跑，也没有将未知数据设为零。

## 新增只读工具

新增`scripts/b0_power_review_inventory.py`，仅Python3.6标准库。它在指定scope内读取固定命名小文件，不递归遍历任务树，不读取网表/库大文件，不扫描SAIF，不调用EDA，不写文件。

- 绑定最终export receipt、report及12层stage/state/summary SHA；逐层核数字、窗口、固件、综合、门级和活动关联。
- 读取固定名单的小报告并复核原artifacts哈希，结束时再次核验所有读取文件；单文件16MiB、包含二次复核的总读取128MiB上限。
- 原SAIF仅检查存在及字节数，明确`saif_fresh_hash_verified=false`；沿用原已绑定的活动审计回执，不伪称重新计算了大文件哈希。
- 输出12层未知统计、实际映射/孤立声明证明、组件功耗、220宏归属/泄漏分布、模型回执、警告及条件摘录；用Decimal独立核加权W和J/task。
- 结果始终`system_power_verified=false`，状态为`read_only_inventory_collected_review_required`，不是功耗验收器。缺文件、哈希不符、未完成stage、路径越界或预算不足则退出2，保留明确错误。

部署到新的个人operations目录后，由根代理在原允许的服务器操作渠道调用。以下是读取目标，不代表本次已执行；stdout可由调用者保存到全新小型JSON回执，不覆盖旧文件。

```text
python3 -B <新operations目录>/b0_power_review_inventory.py
  --scope-root /storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109
  --report /storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_backup_report01/report.json
```

运行后优先读取：输出aggregate及report SHA → 12层unknown/mapping → SRAM模型和泄漏 → 实际工具警告/禁用弧。若出现缺证先记录具体文件及原运行目录；不能启动report exporter重新审全部1200来替代这项小读取。

本地`test_b0_power_review_inventory.py`的11项合成工具检查通过：正确收集但不授予验收、从不读SAIF、不增删证据文件，拒绝改动report/原始报告、未结束stage、scope越界、错阶段、加权不符、缺SAIF、缺层及读取预算超限。它只证明读取工具的行为，不是B0或N1实际PPA结果。尚未在服务器实际运行；本地没有完整B0最终report树。

## 交接与禁止重复项

本代理只新增上述工具、其测试和本文档；没有修改N1/B0生产RTL、冻结包、根server工具或已有报告。没有服务器/VNC操作，没有新仿真或功耗作业，没有提交Git。

下一步由根代理按当前队列/空间状态运行上述只读inventory，并依据真实输出记录能关闭与仍无法关闭的缺口。最终相对功耗准入仍需合格B0：N1整机J/task不增、平均W≤1.1×B0；本B0未知影响未审核前，即使数值满足比值也不能宣称准入通过。N1精度/ASIC/1200/综合/门级/功耗缺项仍按当前主检查点推进，不能进入N2。

不得重复：B0最终报告、B0已完成1200/门级/12活动功耗、R4 SAIF方法对照。不得将统计声明数、注释覆盖率、工具准备PASS或旧型号敏感度结果当未知影响审核PASS。

## 实际补读（2026-11-13 03:08截图后）

根代理已读取inventory02，原B0最终report SHA为`677a1ae11042ffe6aab981b1b0f124b29f604e6dc0d9bb29e96d9f04f4f68a1a`。本代理亲读本地`b0_power_actual_warnings.png`、`b0_power_compact.png`、`b0_power_models.png`及`b0_report_exact_sha.png`，补充如下；它们关闭的是明确的小项，不是完整未知影响验收。

- PWR-601是“Running averaged power analysis”，PWR-602是“Running power calculation with 4 threads”，均为Information，不是功耗错误或未知告警。
- PTE-016也是Information：hf_clk由显示6.667ns扩展到共同base660.000ns并增加196edges；lf_clk原周期为66.000ns，增加18edges。不能把共同base误当实际主时钟降频。精确导入周期仍由原clock回执约束；PTE-003通用警告仍需实际disabled_timing对象/flags解释，不能凭通用文字断言存在组合环。
- L01设置为averaged、initial-X=false、X-transition derate=0.5。switch/static两表均total451386、exact450133、implied0、default1253。1253个默认声明有本B0逐网直接/叶连接均0的证明，活动值未改。独立proof的精确SHA已由根代理按8字符分组核实为`d894ec7e5f9c3b33e6c99a800cd24df6fd66ba68882f63ffac15784849c4a445`，证据截图为本地`r4_archive_postcondition.png`；此前不完整手抄串作废，原inventory02中的完整字段保留。这只证明1253个默认声明的连接性质，不豁免已映射信号的未知活动。
- SRAM实际为加速器92、DTCM32、ITCM32、共享64。小宏每个leakage为4.88099977e-6W，大宏为4.60310002e-5W，均非0。128宏默认双rail为(0.001589+0.003292)mW；4096宏为(0.014038+0.031993)mW。4096的0.014038曾跨截图行，不能误抄为0.004038。
- 默认双rail按92/128累加为0.006341020W；实际220宏报告累加0.00634102000444W，差4.44e-12W属展示舍入。该证据核对单位与实际默认组解释；其他条件组、宏端口活动和整机unknown影响仍须按实际状态审查。
- L01原统计仍为618149声明、41406未知、18620全窗口未知，reported TX ticks4116111454435490；未把这些计数改为功耗误差比例。

完整未知名单及闭环入口另见`B0_UNKNOWN_TOOL_AND_CLOSURE_20261113.md`。不改变原报告的`system_power_verified=false`，后续有范围的审查将单独绑定原报告身份。
