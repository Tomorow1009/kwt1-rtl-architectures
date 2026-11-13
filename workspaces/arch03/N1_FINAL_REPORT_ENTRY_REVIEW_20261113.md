# N1最终报告入口只读审阅

本次只读检查现有`n1_report.py`及其数据、门级、活动、功耗和精度依赖；未修改报告工具、运行测试或启动服务器作业。N1 batch02仍须以根代理实际终态为准，不能提前记1200通过。

## 参数与证据关联

入口为`python3 -B n1_report.py --request <新JSON> --output <不存在的新目录>`。request的schema须为`arch03-n1-report-request-v1`；run指实际stage目录，不是其session父目录。

| 字段 | 真实输入及检查 |
|---|---|
| `asic`、`synthesis`、`gate`（必填） | 各为`{run, sha256}`，sha为summary.json；parent state对应n1_soc/n1_synth/n1_gate必须passed。固定ASIC14与同网表门级14绑定同硬件、固件、布局和完整周期。门级未完成时不能调用build生成最终报告。 |
| `batch` | 实际batch02的n1_batch目录及summary SHA；必须1200任务、30412800个total/result/sat、SHIFT10、零失败。逐个重读receipt、五列capture、源HEX、codec、boot、log、IRQ/WFI及窗口，检查硬件/固件与固定14一致。不能用failed01前缀或旧B0替代。 |
| `activity` | N1自己的n1_saif目录及summary SHA，精确12层；同gate/synthesis/firmware、逐层布局及窗口完全相等，重新审计现成SAIF。 |
| `power` | 12个独立n1_power引用列表，每层一次；每份同activity/gate/synthesis/firmware/window，从原小报告重新提取动态/泄漏/平均功耗和能量。缺层保持null/pending，不填0。 |
| `precision` | `{run, sha256}`，可用`archive`给完整FLOAT ZIP的实际位置；必须先完成本报告自己的ASIC1200重审，再绑定固定ZIP SHA、DATA100 inventory/root manifest、样本顺序及逐任务新量化结果。没有完整FLOAT时保持未验，不能继承旧Q12误差。 |
| `baseline` | `{report, sha256}`，指定B0原report.json及其SHA，仅生成原数字比率，不转移B0验收。 |
| `history` | 保留失败、主动停止与未验证事项；不将其计入通过任务。 |

固定12精度独立读取ASIC运行所属包中的`validated_data`及`architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001`。`fixed12_precision.verified`表示复算一致，最终还须看`internal_three_percent_task_threshold_passed`；它不能代替100条精度。

## 必要边界

- 没有发现SHIFT12或total41旧parser混入：ASIC使用n1_data严格五列和signed33参考，门级使用n1_gate四列且total_checked=false；旧通用模块仅复用哈希、窗口、硬件清单和数值报告解析。
- 跨9305/0f62等工具包通过实际RTL/platform哈希关联，没有固定“最新OPS”目录代替身份核验。原source_inputs中的绝对路径、固件、可执行文件、数据和库必须仍可访问；不能先清理原件再导出。
- 最终导出是重新读现成capture/HEX/SAIF的I/O审计，不是重新仿真。完整证据到齐后一次导出即可，避免重复全量读取。
- 独立时序/DRC/面积、恢复/竞争、B0/N1未知影响审核不在build的准入参数内；`stage_handoff.allowed=false`有意保留。最终阶段review须绑定这些独立证据，不能直接修改布尔值宣布N2准入。

## B0与N1的时钟和负载

本地B0原`systolic_b_power.py`及`systolic_b_report.py`已经要求每层实际PT测量hf_clk=6.666666ns、lf_clk=66ns，并逐字核独立mapped.precise.sdc及其余约束未改。B0不沿用更早R4的舍入SDC；PTE-016显示6.667只是显示格式，不能据此认定与N1条件不同。

已完成服务器inventory02保存全部12层`power_clock`和原conditions；本地轻量观察JSON目前未转存这些字段。B0 DRC06 scope证据已保存SysMem输入35位、输出71位、输入transition0.1ns、输出load0.01库单位（外部接收器规格未验证）。需要补回实际摘录时，只读既有inventory02的12层clock分组及其绑定的mapped.precise.sdc中set_load/set_input_transition行分组即可，无需新EDA。N1最终按自己的实际power_clock/精确SDC逐项对照，不能只以统一150MHz标题证明同条件。

两个有界查询已准备、尚未执行：`takeover_local/b0_clock12_existing_receipt_query.txt`（767字符，SHA `907e6983e8b0be7a1ac588dfe5ac259d0c33b0eafd9f1dac521d72e797e391bb`）绑定inventory02固定SHA并输出12层测量分组、SDC哈希集合与conditions；`b0_load_existing_sdc_query.txt`（873字符，SHA `1d16ef26268e51c19531005c162d87ac99d3b77f6f51e28b99ffb22f1a4d2cf9`）只读取L01原精确SDC并按其原SHA核验，聚合负载/transition行。若12层SDC哈希不一致，不能将L01约束泛化。两条均ASCII、单行shell引号及Python3.6语法已核，不重读波形、不启动工具。

**06:50:06实际增量（优先于上述未执行状态）：**已亲读`takeover_local/b0_clock12_0650.png`。固定inventory02的SHA检查通过，全部12层只有一个clock组：实际hf=6.666666000000ns、lf=66.000000000000ns，other_constraints_unchanged=true、original_sdc_modified=false；全部12层的精确SDC SHA集合仅一个值。conditions仍为SS、0.99V、125°C，原DC序列化周期6.66667保留，功耗采用独立6.666666ns。因此B0原12层确实使用与N1要求相同的精确功耗clock合同；N1自己的实际PT回执仍须完成。当前只关闭该时钟条件小项，不批准未知活动影响。负载查询尚未取得实际结果，暂不把历史0.01/0.1配置直接提升为本次PT约束补证。

06:51:06负载查询已实际完成，亲读`takeover_local/b0_load_sdc_0651.png`：同一精确SDC按原SHA核验成功，439行中set_load -pin_load 0.01共215行，set_input_transition -max/-min 0.1分别112行，OTHER_SYNTAX为空。这是全端口计数，不是SysMem35/71的子集计数；负载保留库单位，不在此转换SI或证明外部接收器规格。12层SDC哈希相同，故同文件约束身份覆盖全部12层。N1自己的实际PT导入/负载记录仍待完成，未知活动影响不因此批准。小证据保存于`handoff/team/evidence/B0_CLOCK_LOAD_CONDITIONS_20261113.json`。
