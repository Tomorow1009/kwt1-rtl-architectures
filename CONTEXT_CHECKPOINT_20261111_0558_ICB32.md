# 2026-11-11 05:58 持续执行检查点

用户要求持续按计划执行，不逐步等待，不因后台运行中就终止本轮；压缩前保存Markdown，压缩后重新读计划/检查点并核对已完成和未完成。当前不主动派子代理，不新建goal。详细历史和失败路径见[05:10检查点及增量](CONTEXT_CHECKPOINT_20261111_0510_ICB32.md)。

## 有效要求与已完成结果

计划：`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`。原32位ICB、无损输入实际写共享SRAM成功ACK后解码转发、16×4 MAC，保留Q12/物理双bank/真实E203 IRQ-WFI。首源VALID含等待至最终输出写ACK和排空，每任务冷启动。不得改成宽总线、INT8、跨任务预载或新的8路DMA。11/11 18:00冻结，11/12 17:16交付准备，用户截止11/13晚上。

- 新R4真实ASIC/E20314例、354816输出、IRQ/WFI通过；12层平均34616周期，150MHz折算4333.2562977 task/s，5000未达。e65 ASIC摘要`e5d009732e822cb5cf730e85b652a160f5022ba0197a9e6ff60960d76121d604`。
- 新综合SS/.99V/125°C/6.666666ns：setup +0.0000715256ns、hold +0.000253469ns，224宏，0锁存器、无组合环/约束违例。保守新增面积上界0.926561671200504mm²，整机4.448778171173114mm²；完整时序范围、功耗仍待审。摘要`fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`。
- 497真实CPU竞争2例50688输出、10阶段无复位恢复76032输出通过。5次真实store trap、取消、4096周期超时排空、A/B/A，CPU最大等待1次DMA接受机会（限8）。不重新运行这些诊断。
- 本地同通路R1/R4全部输出一致，局部3.35914倍；固定R4 raw/压缩12层304128输出一致，平均38052→34616、周期减少9.0297%、事务减少13.6905%。这些局部对照没有CPU/PPA。
- 被动计数仅改TB/报告，未改DUT或生产固件。本地L01/extremes两例50688输出及17工具检查通过；X读101376/写6336、W读409600/写16384、MAC1622016。真实CPU计数尚待964运行，R1计数未实测。
- 新`ICB32_DESIGN_REPORT_20261111.md`准备稿、创新说明、交付索引已整理并云端同步。当前12层理论事务上界4804.099 task/s，实测/该上界约90.199%；只解释流量瓶颈，不当功耗效率，不据此追加结构优化。
- 原ecf队列已自然完成，旧8路门级14/活动12和原DMA16 MAC有效扫描已收回；旧8功耗仍缺。原fcd自己的1200通过/664.393 task/s、29.6273mW/44.5931µJ布局前估算保留，系统功耗仍false，不能转移给新RTL。

## 原gate：已完成6/14例及6/12完整活动

**05:58:01.408080实际：driver209764仍运行，当前L07映射仿真child4274，CPU95.2%。** PID数值已回绕变小，不能因此认错；它由原driver的/proc children读出。前L06 scanner309313与sim306705已结束。原gate启动`2026-11-11T03:08:13.465421`，不重启或清锁。

运行包497：`light-light126-icb32-r4-20261111_011258-49759e108719`，运行`runs/icb32_r4_gate01/icb32_gate`。无SDF，绑定e65同网表。

L01–L06每层25344输出、真实IRQ/WFI与完整活动均通过；周期依次34639、34607、34603、34595、34587、34591，与ASIC一致。部分证据在`handoff/team/evidence/ICB32_GATE_PROGRESS_20261111.json`，最终summary尚未产生，不能标整批PASS。

L06新增回执：VCD12210217662B，窗口92949.990705..323556.634311ns，未知记录1042209。规范化回执SHA`f3161a798966b855cad0d0870e5c006e1b9d0fb963308e9376c4999037db8a7c`、VCD SHA`f6da529911544d7cc99ff075019b23ee3462200f95a68635be6afa521ab508ab`，05:56:08.301044独立断言成功。未知记录不是覆盖率或翻转次数，功耗待审标记不因此解除。

各层完整活动扫描约22分钟，连同仿真、哈希及保存约25–29分钟。按实际宿主进度加20%余量，不把芯片加速比例当仿真速度。当前剩余8例/6活动，包含正在跑的L07。

## 已启动串行后继285397：不要手动重复其计划任务

**05:58:01.408080实看285397进程存在，waiting_gate、completed=[]，没有新的EDA并发。** 原gate全部成功及锁释放后自动依次运行：

1. 964包`icb32_r4_finish01_power_l01`至`l12`，每项使用原gate最终summary SHA，完成后提取实际单位、总和、224宏与数值；功耗仍review_required。
2. `icb32_r4_finish01_metrics14`普通ASIC14，真实被动计数及干净目录功能复现。
3. `icb32_r4_finish01_final1200`，固定100×12真实ASIC/E203任务/30412800输出，一次编译、每任务冷启动、关闭大波形。
4. 准备`report_request.json`，不自动导出或批准最终报告。

状态在**964包**`runs/icb32_r4_finish01_queue/state.json`；操作包`launcher.log`保存启动/失败。每层数字在队列`layer_XX_numbers.json`。任何阶段失败即停止，保留目录；新修复用新包/session，不能重启同一阶段。

操作工具源码提交`e09331dac7f285521acd7bf98522d3c730ec1798`，单独小包`light-light126-icb32-ops-20261111_045128-e09331dac7f2`已FileZilla上传、安全解包/4文件/4保护测试通过。ZIP6330B，SHA`cb5129b433e8e00462de450ee9c0a9550609799642573a210edd4a06a67cca53`；manifest SHA`b5ff86370dabada2f02f3da376ad1e892daf75536e86606aa4ba7ee6c9ae1568`。只调度既有包，没有改运行快照。

后继04:56:04.647646启动，核验964全部输入和固定100数据后于04:56:43.020316建立state。首次过早状态查询无文件，随后正常；不曾重启。绑定原gate PID、启动时间和e65综合SHA，等待不占EDA许可证、不清锁。

## 运行目录与身份

共同父目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

- e65主ASIC/综合：`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0/runs/icb32_r4_first01`。原75421后继已完成，不重启。
- 497诊断/gate：上述497包，630输入三固件已核验；ZIP SHA`ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4`。
- **当前交互cwd/新后继根964：**`light-light126-icb32-r4-20261111_043048-96443c284a1c`。ZIP11139802B/636输入，SHA`18cf4c4def9fcab43174de974c6ca45851af35b6ac1ea701915bd8c57b41b161`；manifest SHA`3afd9a35da42cc9c237314bd18a2d186ecea693e6bb2e82c716d8b8548f938e5`。04:42三固件/生产身份预检通过。
- R1 f95：`light-light126-icb32-r1-20261111_012941-f95e940862ca`，607输入预检通过，服务器ASIC/PPA未运行。
- 最终100数据：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。

964与497的34项RTL/生产固件/运行映像一致。生产FW manifest=`fde6cbea29cda15a066a9f3710d8684ae0ba14f73dfd497a80e0a68b3952849b`、ELF=`8cf32dcdfd842936127292652b21b4f7c2bd0529da73620f1c0949fe213ec233`。序列诊断ELF仅非装载debug/symbol节不同，sequence.bin/verilog相同；不能称所有ELF相同。测试计数工具不要求重综合或重跑已有同网表gate。

## 后续未完成

- 继续原gate和后继，不手动启动重复power/metrics/batch。读取原gate最终summary和锁释放，确认后继实际接手。
- 实际12层PPA、单位/模型/活动/未知值、任务模式时序范围说明仍缺。新配置功耗尚未生成，不能沿用旧29.627mW。不要扩展无关大扫描或物理签核。
- 自己的1200未完成，不能继承旧PASS。看batch_progress实际宿主ETA加20%。新计数及干净目录复现由metrics14提供。
- 队列完成后审阅report_request并补保留的失败/未验history，在新输出目录运行`icb32_report.py`独立重审同配置活动与新1200回执，串行执行。
- 导出器目前固定保留时序/面积/系统功耗false及部分unverified字段。真实竞争/恢复已独立通过，metrics14也将提供干净复现；最终要明确关联同身份审阅和摘要，不能误把固定待办表述成这些实际工作未做，也不能无证据改成通过。
- 最终JSON/CSV/中文报告、设计报告结果补齐、提交包/来源/创新材料。R1服务器PPA与旧8功耗后排，主候选合格交付优先。官方600样本、布局后功耗时序和物理签核未验证。

## 客户端、同步与失败路径

- Linux VNC最后有效window20971587；**当前最后命令`takeover_local/icb32_all_live.txt`，可Up Return**。gate_live动态读子进程/VCD偏移；gate_receipt_compact分行读最新完整回执；固定哈希断言不用于看实时进度。压缩后先重新盘点窗口。
- FileZilla已断开关闭；FTP代理21036/VNC relay23793继续，不重复启动。服务器命令只经板端VNC，上传只经Linux FileZilla；本地到板端暂存允许既有helper。无CUA会话或completion_summary欠项。
- `F:/linux_fpga_try/ac820.ps1`沿用授权提升/prefix，不能读取打印凭据。type≤1000字符；tcsh避免美元符号和复杂嵌套引号。工具返回运行session后先poll完成再看新截图，防旧图误判。
- 本地Python`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`，Zig在父目录takeover_local/tools。一次性progress脚本已执行者不能重跑。05:10长中文脚本直接执行的编码报错用显式UTF-8读取compile/exec解决，项目文件复读正常；不涉及RTL。
- 保留的失败：最初计数fixture变量声明次序编译失败已修、过宽固件身份断言被诊断ELF调试节差异触发后查明、队列测试Windows/POSIX路径期望已修、L04哈希f/1转录错误已分行重读并断言成功。均不混作DUT失败。历史硬件失败及早期37组等仍保留，不重走这些入口。
- 云端最后独立核`3df333cbcb9599ea54629b972c91e000bf80ec8b`；本检查点及L06更新待提交。私人仓库个人分支持续同范围同步已授权，未发生自动审批拒绝。本地无长任务，只有服务器原gate和等待后继。
