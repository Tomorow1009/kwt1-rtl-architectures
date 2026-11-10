# 2026-11-11 03:40 持续执行检查点

用户要求按计划持续工作，不因常规步骤停等；压缩后先重读AGENTS、有效计划、本检查点及STATUS的icb32_c64_execution。有效计划仍`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`，原32位ICB/无损压缩落库成功ACK后解码/16×4，不改数值规则、不加宽总线、不跨任务预载。11/11 18:00冻结、11/12 17:16交付准备、11/13晚上截止。

## 已完成和证据

- 新R4真实ASIC/E20314例354816输出及IRQ/WFI通过，12层平均34616周期/150MHz折算4333.2562977 task/s。见`ICB32_ASIC14_20261111.json`。5000未达，不改计时。
- e65新综合完成：SS/.99V/125°C/6.666666ns，setup +0.0000715256ns、hold +0.000253469ns，224宏（128大/96小）、0锁存器、无组合环、constraints无违例；新增面积保守上界0.926561671200504mm²，整机4.448778171173114mm²。摘要SHA `fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`。详见`ICB32_SYNTH_20261111.json`，完整时序/功耗审阅仍待完成。
- 497真实CPU竞争2例50688输出、恢复10阶段76032输出通过。配置错误真实store trap5次，取消/4096cycle超时排空、A/B/A通过；CPU等待最多1次DMA接受，限制8。详见`ICB32_CPU_DIAGNOSTICS_20261111.json`；两摘要已独立断言，polling诊断不作IRQ性能/能耗。
- 497只读网表probe完成，六模块端口可观测；三个高扇出均为既有平台时钟网，详见`ICB32_TIMING_PROBE_20261111.json`。未改网表，不据此跳过PT全时序范围审阅。
- 本地R1/R4同搬运14例354816输出一致，局部3.359140×。新补raw/压缩固定R4对照12层304128输出一致，硬件/TB/配置/布局哈希全部相同；raw38052→压缩34616平均周期，减少9.0297%，事务减少13.6905%。分别见`ICB32_LOCAL_R1_R4_20261111.json`、`ICB32_LOCAL_CODEC_20261111.json`及中文对照。均非CPU/PPA。新raw会话50608已完成，无本地仿真。
- 原ecf队列已自然完成，旧8门级14/12活动及旧MAC有效样本扫描已回收；旧8完整功耗仍缺。原fcd 664.393 task/s、1200任务零失败及旧29.6273mW保留，不能套给新RTL。

## 当前唯一服务器重任务

**497包gate14＋12完整活动，driver209764；最新03:40:47.256872仍running，完成L01，正在L02映射仿真child230178。** 运行目录`runs/icb32_r4_gate01/icb32_gate`，父日志`icb32_gate01_launcher.log`；不重复启动、不清锁、不并发EDA。

L01已实际发布完整用例回执：25344输出、34639周期与ASIC一致，IRQ/WFI通过；12,595,749,229B波形全扫描及SHA完成。部分进度证据`ICB32_GATE_PROGRESS_20261111.json`，不是最终summary，不批准其余13例。活动未知值记录996956，保留待功耗影响审阅，不当作翻转或覆盖百分比。首层仿真CPU250s、全扫描约21.4分钟，12层需数小时；以实际进度加20%余量，不按芯片加速比估宿主时间。

共同父目录`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`：
- e65主ASIC/综合：`light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`，`runs/icb32_r4_first01/icb32_synth`；旧queue75421已结束，勿重启。
- 497诊断/gate/报告：`light-light126-icb32-r4-20261111_011258-49759e108719`，630输入/三固件预检已过，生产IRQ与e65相同；当前gate明确引用e65上述synth SHA。
- R1对照：`light-light126-icb32-r1-20261111_012941-f95e940862ca`，607输入预检已过，服务器ASIC/PPA未运行。

## 未完成与后续顺序

1. 跟进当前gate完成剩余13用例/11活动；遇失败保留目录、查真实问题，不原地重跑。
2. 完成后取得最终gate summary SHA，串行12层`icb32_power`。报告新整机动态/泄漏/平均功耗与J/task，审单位、224宏、活动覆盖/未知值/缺模型和PT no_clock/disabled arcs等。不要重新启动额外旧MAC或X扫描来扩展验证；范围按当前计划和实际问题处理。
3. 优选冻结候选自己的1200真实ASIC/E203/30412800输出、干净目录复现和同配置JSON/CSV/中文报告仍待完成。固定数据`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest `0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`；新`icb32_batch`入口已在497，按实际batch_progress估宿主耗时。
4. R1实际ASIC/PPA、旧8完整功耗对照和最终提交/答辩整理仍待做，优先主候选。当前不追加结构优化或本地测试。

## 操作和失败路径

- 板端VNC window20971587，第三终端**交互cwd仍R1包根**；Popen只改子进程cwd。最后命令是`takeover_local/icb32_gate_status.txt`，Up Return可重复；截图`icb32_gate_status.png`。FileZilla关闭，原代理保持。无CUA会话/无需completion_summary。
- 通过`F:/linux_fpga_try/ac820.ps1`可见VNC输入服务器命令；不SSH服务器/不隐蔽上传。单次type≤1000字符，截图前等1–2s；不得重跑任何start_*已成功命令。旧activity_live脚本固定已结束L01 scanner214920，不再拿它查L02。
- 长命令本地1000字拒绝、tcsh嵌套转义双引号/正则美元符号解析拒绝均未启动服务器任务；改简短Popen参数或Python构造固定bash串行命令成功。历史Tcl/NumPy环境和8192→4096诊断修复见03:10、01:12检查点；不要重跑旧adapt脚本覆盖固件。
- 最新已独立核云端`3d096294d2bee2c94b1ba1de1fc7fb271aa3a453`，此后仅检查点/部分gate证据待提交。受测RTL/生产固件始终未改。同步获用户长期授权，不必再询问；只推现有团队私人个人分支，不含凭据/厂商库/聊天原文/大产物。
- 后续持续执行；仅用户明确暂停才关闭板端两客户端，远端原队列保持。重要进展/暂停/压缩前更新根交接，压缩后再读计划和检查点。
