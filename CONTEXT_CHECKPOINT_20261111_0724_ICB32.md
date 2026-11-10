# 2026-11-11 07:24 持续执行检查点

用户要求能继续就一直做，不逐步停等；压缩前保存进度，压缩后重新读计划和检查点。当前没有暂停、无需新授权、不新建goal、不主动派子代理。不要因为正在等待服务器就结束本轮。

## 恢复入口与有效要求

先读AGENTS.md、本文件、`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、STATUS和EXECUTION_CHECKPOINT的`icb32_c64_execution`。详细历史见[05:58检查点及07:12增量](CONTEXT_CHECKPOINT_20261111_0558_ICB32.md)，不重复已通过项目或失败旧入口。

有效路线为原32位ICB、无损输入真实写共享SRAM成功ACK后解码转发、16×4 MAC、物理W双bank、原Q12、真实E203 IRQ/WFI。首源VALID含等待至最后结果写ACK和排空，每任务冷启动。不新增宽总线、INT8、跨任务预载或8路DMA。11/11 18:00硬冻结，11/12 17:16交付准备，用户提交截止11/13晚上。

## 最新实际服务器状态

**07:23:40.308949实际：原gate driver209764仍运行，当前L10活动scanner73822（已运行11:27，CPU99.8%）；唯一后继285397处于waiting_gate，completed=[]、error=None，未启动最终batch。** 原gate03:08:13.465421开始，完整通过L01–L09；9/14例、9/12活动。最终summary未生成。07:22:49扫描L10 VCD的6253771163/12300092453B，约50.8%。该偏移不是PASS或最终回执。

原gate包497：`light-light126-icb32-r4-20261111_011258-49759e108719/runs/icb32_r4_gate01/icb32_gate`，无SDF，绑定e65同网表。最终SHA需等实际终态读取，不能用case_progress的变化哈希代替。

后继285397已经核验964包和固定100样本，自动等待原gate全部成功及共享锁释放，随后顺序执行：

1. `icb32_r4_finish01_power_l01`至`l12`，实际PT及数值提取，保留system_power_verified=false。
2. `icb32_r4_finish01_metrics14`，相同DUT/正式固件的真实ASIC14计数及干净目录复现。
3. `icb32_r4_finish01_final1200`，新版自己的100×12实际ASIC/E203任务、30412800输出，一次编译、无大波形。
4. 生成`report_request.json`，不自动导出或审定最终报告。

**不要手动另起上述任务。** 后继状态在964包`runs/icb32_r4_finish01_queue/state.json`，每层数值为同目录`layer_XX_numbers.json`。任何阶段失败即停止，保留原目录，检查日志后用新的修正包/session继续，不清锁或原地重跑。原gate和旧75421、旧ecf队列都不能重启。

## 已完成结果与新进展

- e65真实ASIC/E20314例354816输出和IRQ/WFI通过，12层平均34616周期，150MHz折算4333.2562977 task/s。5000未达到，当前编码量的32位事务下界已经超过30000周期。证据`ICB32_ASIC14_20261111.json`。
- e65综合SS/.99V/125°C/6.666666ns，setup +0.0000715256ns、hold +0.000253469ns，224宏、0锁存器、无组合环/约束违例。保守新增面积上界0.926561671200504mm²，整机4.448778171173114mm²。完整时序和功耗仍待审，见`ICB32_SYNTH_20261111.json`。
- 497真实CPU竞争2例50688输出、10阶段恢复76032输出通过，最大CPU等待1次DMA接受机会；取消/4096超时排空、5次store trap、A/B/A。不要重复，见`ICB32_CPU_DIAGNOSTICS_20261111.json`。
- 本地R1/R4同通路14例逐坐标一致，局部3.359140倍；固定R4 raw/编码12层304128输出一致，平均38052→34616周期，减少9.0297%。这些拆分没有CPU/PPA，不能混成服务器对照。R1服务器只有预检，还没跑ASIC/PPA。
- 被动计数只改TB/报告，未改DUT/固件；本地2例50688输出与17工具检查通过，真实CPU计数待后继metrics14。X读101376/写6336，W读409600/写16384，MAC1622016。R1计数未测。
- **L09新增完整回执已独立核对：** 25344输出、34595周期，实际IRQ/WFI和活动通过；VCD12161796288B，窗口92949.990705..323583.300975ns，未知记录965981。规范化row SHA `eae656e8a5e0ee9d968f3233f4159a3454232d908ea697589b9f82599207a1df`，VCD SHA `bbde16225e248534d6fdef48aff638fab67f9fa047b0cb233958ccb66e770ba4`，07:11:16.117904断言通过。9层证据见`ICB32_GATE_PROGRESS_20261111.json`。
- **新网表端口全量只读复核完成：** 复用`dma16_structural_audit.classify`纯函数，单独核对新ICB32 scope和原网表/报告SHA；未调用旧DMA16限定入口。2014模块、11138端口告警全部只有声明无逻辑引用（10598输入/540输出）。完整结果在964包`runs/icb32_port_review01.json`，SHA `316ee46a76452e2661d2b0a96e2823ed8373c0341e8797758813190ffec07da3`，07:08:29.726025重新核对输入和结果SHA通过。原文件未修改，无EDA启动。小型证据`ICB32_PORT_REVIEW_20261111.json`及中文`ICB32_TIMING_REVIEW_20261111.md`已保存。
- LINT计数1=4、2=706、8=706、28=10432、32=9935、33=1000。LINT1四个旧平台对象已核；LINT2代表样例来自算术未用位，不称全部对象审定。实际PT no_clock/disabled-arc仍待生成，不能复用旧fcd数量。
- 设计报告补充来源/复用/本轮贡献对应表，核心新增提交6a6f6ea，验收仍按e65/497/964实际身份。无个人作者补写、无厂商库或凭据同步。

## 身份、目录与串行约束

共同父目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

- e65主ASIC/综合包`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`，`runs/icb32_r4_first01`。ASIC summary SHA `e5d009732e822cb5cf730e85b652a160f5022ba0197a9e6ff60960d76121d604`；synth SHA `fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`。
- 497诊断/gate包如上，630输入；ZIP SHA `ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4`。
- **当前交互cwd及后继根964：** `light-light126-icb32-r4-20261111_043048-96443c284a1c`，636输入，ZIP SHA `18cf4c4def9fcab43174de974c6ca45851af35b6ac1ea701915bd8c57b41b161`，manifest SHA `3afd9a35da42cc9c237314bd18a2d186ecea693e6bb2e82c716d8b8548f938e5`。
- 后继操作包e093：`light-light126-icb32-ops-20261111_045128-e09331dac7f2`，4文件，ZIP SHA `cb5129b433e8e00462de450ee9c0a9550609799642573a210edd4a06a67cca53`。已在04:56启动，不能重复。队列4项测试本地/服务器通过。
- R1 f95包已607输入预检但未运行，主候选最终链优先。原8路14门级/12活动已完成，旧功耗仍缺；旧ecf队列01:35自然结束。
- 数据固定`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA `0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。
- 964与497的34项RTL/生产/运行映像一致，正式ELF/manifest不变；sequence诊断ELF仅非装载debug/symbol节不同，不能声称全部ELF逐字节相同。证据`ICB32_METRICS_PACKAGE_20261111.json`。
- 共享锁`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock/owner.json`。只允许一个EDA/大活动作业。等待的后继不占EDA许可，不擅自清锁或结束远端任务。

## 未完成与实际下一步

1. 继续原gate的L10–L12活动及extremes/rounding，读取最终14例/12活动summary SHA，确认后继自动接手。不要手工重复power/metrics/batch。
2. 读取首层实际PT数值、单位、宏模型和活动来源。新配置没有功耗结果，不能沿用旧29.627mW。轻量报告复核可以复用964现成纯解析函数：`mmio8_timing_objects.no_clock/disabled_arcs/jtag_cases`、`dma16_power_activity_review.settings/sources/empty_unannotated`。**只复用纯函数并绑定新配置，不能调用硬编码旧DMA16/MMIO8范围的完整audit/build。** 这些函数已读取，别反复重读或重新开发相同解析器。PT报告尚未生成，尚未调用这些函数分析新报告。
3. 新版1200按实际batch_progress宿主时间估算，留20%余量；不能继承旧fcd PASS，不能用芯片速度比例推算仿真速度。
4. 后继完成后审阅report_request，补历史失败/停止/未验项，在新目录串行运行icb32_report.py，独立核对14/12/1200原始回执。报告导出器不会自动批准时序/功耗，而且固定unverified字符串仍含已独立完成的CPU诊断/干净复现；用同身份审阅说明其覆盖范围，不能误说工作没做，也不能随意改false为true。
5. 补最终JSON/CSV/中文报告、设计报告、提交包及创新对照。R1完整PPA和原8功耗后排，有时间再完成；不增加结构优化。官方600精度、布局后功耗/时序、物理签核未验证。

原fcd退路自己的1200与full02有效：225770周期/664.393 task/s、新增上界0.434796781612mm²、29.6273447417mW/44.5930996895µJ布局前估算，system_power_verified=false。不能混入新R4成绩。

## 客户端、同步与失败路径

- 当前本地Git分支`codex/light-light126/undergrad-d1-numerics`；云端最后独立核`dff99a7461f16606d527f74446d760155a03eb3f`。本检查点与设计报告来源表待提交。私人GitHub同范围持续同步已授权，无新审批阻塞。
- 开发板VNC最后实际window20971587，800×450；压缩后先重新盘点窗口。FileZilla关闭并断开，FTP代理21036和VNC relay23793保留。服务器操作仅板端VNC，上传仅Linux FileZilla，禁止隐藏服务器SSH/回传通道。
- Helper`F:/linux_fpga_try/ac820.ps1`沿用已授权提升。type/key需要expect-class；**screenshot只接受window/output，不接受expect-class。** 本次多加该参数被本地参数校验拒绝，改正后成功；只读查询已经执行，未影响服务器。
- **终端最后命令为`takeover_local/icb32_finish_live.txt`，Up Return是后继/子进程/批量概览，不是gate文件偏移。** 现有`icb32_all_live.txt`查完成层与后继；`icb32_gate_live.txt`查driver动态子进程/VCD偏移；`icb32_gate_receipt_compact.txt`读最新完整层。新`icb32_power_numbers_live.txt`等待实际功耗后才用，输出已完成层数和部分/完整加权均值。
- type单条≤1000字符；tcsh不要美元符号和复杂嵌套引号。exec若返回本地session，先poll到完成，再看新截图。不要因旧截图误判。无CUA会话或completion_summary欠项。
- 本地Python`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`。`progress_0712.py`已经执行，不重复追加；所有旧progress脚本同理。UTF8长脚本用显式read_text→compile→exec。不运行旧adapt_icb32_sequence生成器以免恢复8192超时。
- 历史失败保留：旧37组路径、早期功耗/综合/门级工具修复、计数fixture声明次序、诊断ELF调试节身份差异、Windows/POSIX队列测试路径、L04和L08哈希手抄错误（重读后已通过）。本次L09转录无误，未出现新的硬件失败。
- 本地无仿真/构建长任务，只有远端原gate及等待后继。无需重新跑已通过工具测试，不安装matplotlib，不扩大未知活动诊断。继续推进实际结果。

## 07:36增量：第10层完整通过

- **07:35:47.430150实际：原gate209764完整通过L01–L10，当前L11映射仿真90534，CPU95.8%；后继285397仍waiting_gate、completed=[]且进程存在。** 当前10/14例、10/12活动，最终summary未生成，后继power/metrics/final1200还未启动。
- L10：25344输出、34667周期，IRQ/WFI及完整活动通过。VCD12300092453B，窗口92949.990705..324063.300927ns，未知记录1013941。row SHA`eef34f338a7ebd86ad0832dc9025df945691bffa4c6af09c8b5d94b2aa07fe4b`，VCD SHA`f957400a4890c7f387fcaad8b6e8c974db30c4629f4eccd6da031fdef0f38ace`，07:35:14.986429独立断言通过。
- 07:24完整检查点和设计报告来源表已同步并独立核云端`1e7616dee3f4ceaa7888a650ecbd1a2ad7ab9b70`。本增量待提交。工作区没有RTL/固件改动，本地无长任务，旧队列未重启。
- **终端最后已恢复all_live查询**，cwd964，FileZilla关闭；Up Return现在查完整层与队列，而不是前文finish_live。继续等待原gate自然收尾和唯一后继接续，不手工重复。压缩后读本检查点全部增量、有效计划和STATUS。
