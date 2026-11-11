# 2026-11-11 08:35 接续：门级全部通过，首层功耗进行中

用户要求能继续就持续做，不逐步停等；压缩前保存、压缩后重读有效计划与检查点。不要发“进度已保存、等你指示”的结束答复。没有新暂停或审批阻塞，不创建goal、不主动派子代理。

## 第一时间读取

AGENTS.md、`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本文件、STATUS与EXECUTION_CHECKPOINT的`icb32_c64_execution`。完整已做/未做/失败历史见[07:24检查点及各增量](CONTEXT_CHECKPOINT_20261111_0724_ICB32.md)；以本文件的门级终态覆盖其中“gate运行中”。

有效路线不变：原32位ICB、无损输入真实写共享SRAM成功ACK后解码转发、16×4 MAC、物理权重双bank、Q12、真实E203 IRQ/WFI。首源VALID含等待至最后结果写ACK及排空，每任务冷启动。不要加宽总线、改INT8或跨任务预载。11/11 18:00冻结，11/12 17:16交付准备，用户截止11/13晚上。

## 原门级已经自然完成，不再查询旧扫描PID或重启

- 原driver209764，03:08:13.465421开始，**08:29:52.493379正式passed**。
- 497包`runs/icb32_r4_gate01/icb32_gate`：14例、354816输出、12个完整活动窗口全部通过，真实CPU执行、无SDF。
- 最终summary SHA **`95113a35bf2941e985d8d1b8cbad7d88c0d56f07d3c1f533f0fcf549fb2efc7f`**，08:31:56.431737独立断言等于实际文件和stage state。
- 12层周期与e65 ASIC14逐层相同，平均34616；extremes38052、rounding33914。150MHz折算4333.2562977 task/s，5000未达到。见`handoff/team/evidence/ICB32_GATE14_20261111.json`。
- L12：25344输出、34631周期、IRQ/WFI通过；VCD13242033420B，窗口92949.990705..323823.300951ns，未知记录1009322。row SHA`4299551f8f4b5aaa39a19a665d7287fea8959ede44c2236556301d8c059eee8c`；VCD SHA`a0bd3433614e274f7c0a1410044af7010d3277392fc9208ac1516120bea19cff`；08:30:02.420780独立断言通过。12层详细活动回执保留在原progress证据中，最终14例以新的完整gate证据为准。

## 当前唯一后继正在实际计算功耗

**08:32:28.191700实看：队列285397 running，当前`icb32_r4_finish01_power_l01`，已完成项0、error=None；driver136463、PT shell136925。08:33截图进一步确认实际计算PID136939 `pt_shell_exec`活跃，CPU约124%、RSS约1.46GB，正在读取layer_01.vcd。** 外层shell CPU0不代表停住；不要误停或重启。

功耗日志显示新整机链接成功：334291 leaf cells/ports/hierarchies，504201 nets；SysMem10组106位HF约束已绑定，随后读原497首层完整VCD。尚无首层完整数值回执，不能沿用旧29.627mW，也不能称12层功耗通过。

后继的既定顺序不改、不得手工重复：

1. `icb32_r4_finish01_power_l01`到`l12`，同新网表/活动窗口PT及数值提取。
2. `icb32_r4_finish01_metrics14`，同DUT/正式固件真实ASIC14，被动计数和干净目录复现。
3. `icb32_r4_finish01_final1200`，新版自己的100×12实际ASIC/E203任务，30412800输出，一次编译、不输出大波形。
4. 自动生成`report_request.json`；不会自动导出或审定最终报告。

队列状态在**964包**`runs/icb32_r4_finish01_queue/state.json`；每层数值为同目录`layer_XX_numbers.json`，每阶段日志也在此目录。当前power详细日志在`runs/icb32_r4_finish01_power_l01/icb32_power/power.log`。失败立即停止，保留原目录，诊断后用新包/session修复，不清锁或原地重试。

## 已完成，勿重复

- e65 ASIC14及IRQ/WFI，354816输出；新综合SS/.99V/125°C/6.666666ns、224宏/0锁存器/无组合环和约束违例。setup +0.0000715256ns、hold +0.000253469ns，保守新增面积0.926561671200504mm²，整机4.448778171173114mm²；完整时序仍待PT对象审阅。
- 497真实CPU竞争2例50688输出、恢复10阶段76032输出；5次store trap、取消/4096超时排空、A/B/A。最大CPU等待1次DMA接受机会。
- 2014模块/11138端口告警已全量解析，全部声明之外无逻辑引用（10598输入/540输出）；964`runs/icb32_port_review01.json` SHA`316ee46a76452e2661d2b0a96e2823ed8373c0341e8797758813190ffec07da3`。只复用纯classify，未调用旧DMA16限定入口。记录在`ICB32_PORT_REVIEW_20261111.json`和`ICB32_TIMING_REVIEW_20261111.md`。
- 本地R1/R4同通路14例一致，局部3.359140倍；固定R4 raw/编码12层304128输出一致、周期减少9.0297%。没有R1服务器PPA，不混称完整PPA对照。
- 被动计数本地2例50688输出、17工具检查通过，DUT和生产固件不变；新真实CPU计数待metrics14。队列4项保护测试已本地/服务器通过，不重复测试。
- 设计报告、来源/贡献表、创新说明、交付索引已准备。赛题原图12/14和13/14页已再次核对，不需要追加物理布局验收。

## 目录与身份

共同父目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

- e65：`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0/runs/icb32_r4_first01`。ASIC SHA`e5d009732e822cb5cf730e85b652a160f5022ba0197a9e6ff60960d76121d604`；synth SHA`fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`。
- 497：`light-light126-icb32-r4-20261111_011258-49759e108719`，630输入，已完成诊断和gate。
- **当前cwd/执行包964：**`light-light126-icb32-r4-20261111_043048-96443c284a1c`，636输入；ZIP SHA`18cf4c4def9fcab43174de974c6ca45851af35b6ac1ea701915bd8c57b41b161`，manifest SHA`3afd9a35da42cc9c237314bd18a2d186ecea693e6bb2e82c716d8b8548f938e5`。与497的34项RTL/生产/运行映像一致，sequence诊断ELF仅非装载调试/符号节不同。
- 后继操作包`light-light126-icb32-ops-20261111_045128-e09331dac7f2`，04:56已经启动285397，不重启。
- 固定100数据`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。
- 原fcd退路自己的1200/full02已通过，664.393task/s、0.434796781612mm²、29.6273mW/44.5931µJ布局前估算，system_power_verified=false。新R4不能继承其1200或功耗。
- R1 f95包只有607输入预检，未跑服务器ASIC/PPA；原8路14门级/12活动已收回，完整功耗仍缺。这些对照后排，优先完成当前R4交付链。

## 下一步与剩余缺口

1. 持续原自动队列，先读首层实际PT结果、单位、宏分量和工具错误；12层按各自完整持续时间汇总E与平均功耗。任何失败保留日志再修，不重复启动。
2. 轻量报告审阅复用964已有纯函数：`mmio8_timing_objects.no_clock/disabled_arcs/jtag_cases`；`dma16_power_activity_review.settings/sources/empty_unannotated`。这些函数已读取，尚未分析新PT报告。必须绑定新ICB32配置，不能调用旧DMA16/MMIO8限定的完整audit/build。不要新增大波形扫描或无关物理签核。
3. 读同配置no_clock对象、禁用弧、实际SDC/时钟/四个LF首级例外及SysMem预算。结构端口复核不自动等于完整时序通过；旧fcd审定不转移。
4. 等metrics14和自己的1200完成，按batch_progress宿主ETA+20%估算，不按芯片加速比估仿真速度。
5. 后继完成后审阅report_request并补失败/停止/未验history，在新目录串行运行icb32_report.py，独立重审原14/12/1200回执。导出器固定未验字段仍包含已独立完成的CPU诊断/复现，需配同身份审阅说明，不误说这些没做，也不随意改false为true。
6. 补最终JSON/CSV/中文报告、设计报告、提交包和必要对照。新功耗、新1200、完整时序审阅及最终交付尚未完成；官方600精度、布局后时序/功耗、物理签核未验证。

## 客户端与同步

- Git私人个人分支`codex/light-light126/undergrad-d1-numerics`；云端最后独立核`0f612818c313e768335680f59ac486805c4a9ea4`，本门级终态记录待提交。持续同范围同步已授权，无自动审批拒绝。
- 板端VNC最后实际window20971587，800×450；恢复先盘点。FileZilla断开关闭，FTP代理21036/VNC relay23793保留。服务器只经板端VNC操作、上传只用Linux FileZilla；不启用隐藏服务器SSH/新回传通道。
- **当前最后VNC命令为`takeover_local/icb32_pt_live.txt`**：递归查实际PT子进程并读当前power.log末10行。屏幕可能把时间/外层进程挤出，可用`icb32_finish_live.txt`看简洁阶段及队列。`icb32_power_numbers_live.txt`用于已有数值回执；当前还没有完整数值。
- 旧`icb32_gate_live.txt`绑定209764，原gate已结束，不再用它查当前作业。固定L12回执和gate最终哈希查询已实际成功，不重跑gate。`icb32_all_live.txt`仍可看全14/队列，但功耗完成项一多会换行，用finish_live更清楚。
- Helper`F:/linux_fpga_try/ac820.ps1`沿用授权提升；type/key用expect-class，screenshot不接受它。单条type≤1000字符。若exec返回本地session，先poll完成再看新截图，避免旧图误判。无CUA会话或completion_summary欠项。
- 本地无仿真/构建长任务。所有progress脚本执行过就不能重复追加；最新到progress_0804.py，后续终态脚本另建。Python为`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`，长UTF8脚本显式read_text→compile→exec。
- 历史失败全部保留；本轮L09–L12哈希均一次断言通过，没有新硬件失败。不重跑旧37组，不运行旧adapt序列生成器，不安装绘图依赖，不增加无关验证。继续当前串行交付链。
