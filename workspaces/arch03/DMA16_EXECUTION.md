# DMA16独立运行入口

执行状态以CONTEXT_HANDOFF及验收记录为准。以下命令是已实现入口；实际服务器通过项必须附新运行回执，不能把命令存在当成验证完成。

使用已提交干净源码、已独立核对的旧14用例及tile16目录、无任务输入的DMA固件打新包。`package_dma16.py`逐个重核坐标、整数输出和源码/固件哈希；可同时携带polling和IRQ固件。包不含固定平台原始源码、厂商库、凭据、聊天记录或大波形。

```text
python workspaces/arch03/scripts/package_dma16.py --member <成员/本次标识> --data <旧14case> --tile-data <对应tile16> --firmware <polling产物> --irq-firmware <已核验映射IRQ产物>
```

**用户于2026-11-09约21:18明确恢复FileZilla。** 按已有授权经开发板Linux FileZilla上传独立目录，校验ZIP并用既有安全解包器核对每个文件。所有运行入口持同一个`.arch02_team_lock`；先读取现有锁和进程，不清除他人/历史锁，不同时启动多个EDA作业。

21:56更新：首包synth01存在TIM-209取消译码组合反馈，不能验收时序；保留原报告。当前仅取消译码移除多余的access_error依赖，15协议、28数据通路任务、正式monitor/metrics及A/B/A夹具复验通过。新候选必须重跑实际ASIC14和综合，不能沿用首包网表。5bdf88b后续包虽已板端核验但未上传，因已知gate wildcard探测问题一并由修正版替代。门级入口新增原始回路报告核验；功耗入口根据已安装PT手册使用check_timing -verbose及report_disable_timing -nosplit，保存具体对象，仍不自动宣称功耗通过。

```text
python3 workspaces/arch03/scripts/server_run.py dma16_soc --session dma16_smoke01 --cases layer_01
python3 workspaces/arch03/scripts/server_run.py dma16_soc --session dma16_irq01 --cases layer_01 --firmware-root <本包绝对路径>/firmware_irq
python3 workspaces/arch03/scripts/server_run.py dma16_soc --session dma16_full01 --firmware-root <本包绝对路径>/firmware_irq
python3 workspaces/arch03/scripts/server_run.py dma16_synth --session dma16_synth01
```

每个stage都是新目录，错误也保留。首次固定平台安装/编译本身可能发现接口问题，必须修本地源码后生成新包，不能原地改正在验证的包。只有真实CPU14用例通过后才扩大回归。

`dma16_soc`一次编译后按case运行真实E203；`dma16_build`仅编译并生成`batch_contract.json`，不声明CPU已执行。contract冻结可执行文件、全部RTL/头文件、平台、宏和标准单元模型、程序-only物理启动文件、观察器、时钟、布局和编译回执。任务数据只有PC预读的`+LOAD32`，经原SysMem接口进入DMA，再依次共享写ACK/共享读/输出写ACK；ITCM不含输入。

最终批量在编译入口释放锁后独立执行，避免嵌套锁。`boot_by_shift`选择事先校核的程序镜像，任务间不改源代码或已编译配置。

```text
python3 workspaces/arch03/scripts/dma16_batch.py run --data /storage2/2026contest/server4/s4_21usr/Desktop/IC/hex --contract <合格冻结构建>/batch_contract.json --output <全新1200运行目录>
```

旧37组不续跑。只有完全一致配置且重新核验全部已完成回执时才能显式`--resume`新批次；失败尝试不覆盖。此入口不代替最终14门级及12完整活动/功耗任务。

完整时间从首源读VALID发出至最后输出ACK；排空可以稍晚证实但不额外计入末ACK周期。源模型边沿N接受后寄存response，最早N+1握手，单笔在途。VCD在首VALID开始、末ACK结束；现场必须核验文件实际区间。CPU mcycle只交叉核对，IRQ/WFI下不可假定其等于自由运行系统时间。

后续独立入口已经新增，须在包含这些文件的新运行包中执行。第一包`2bd6b0f`不含以下后续入口，不能在其中原地添加脚本。

`--mmio8-firmware`可将已验证的原8路驱动源加载固件打包为`firmware_mmio8`。它仍由CPU搬运，没有8路DMA；本地3任务/76032输出和6项拒绝测试不代表真实CPU执行。

```text
python3 workspaces/arch03/scripts/server_run.py mmio8_soc --session mmio8_source01 --cases layer_01
python3 workspaces/arch03/scripts/server_run.py dma16_sequence --session dma16_sequence01 --cases layer_01 rounding
python3 workspaces/arch03/scripts/server_run.py dma16_gate --session dma16_gate01 --synth-run <实际新DMA16综合目录> --synth-summary-sha256 <其summary摘要> --firmware-root <本包>/firmware_irq --activity-cases layer_01
python3 workspaces/arch03/scripts/server_run.py dma16_power --session dma16_power01 --gate-run <实际DMA16门级目录> --gate-summary-sha256 <其summary摘要> --cases layer_01
```

`dma16_gate`先读取同一 mapped.ddc，以只读DC探测实际模块边界，再生成端口监视器；缺少模块或完整位宽时拒绝，不猜内部别名。每个门级任务仍用真实E203及程序-only启动，最终排空由末ACK之后的新MMIO响应证明。`dma16_power`要求完整窗口VCD审计与同配置网表；报告生成不自动表示活动覆盖、功耗单位或模型已经通过审核。首层成功后仍需最终14门级及12独立功耗任务。

`--sequence-firmware`打包独立程序-only序列固件到`firmware_sequence`，严格绑定A/B源payload及shift。`dma16_sequence`不接受activity参数，只验一次真实CPU启动的10阶段：5配置拒绝、装载取消、原驱动短timeout恢复、A/B/A三完整任务；每成功任务各有独立窗口，不能把整段序列当单任务功耗。阶段trap/输出/回执须真实观察，NO_CPU夹具日志一律不能作为ASIC通过。

新版批量每case记录宿主开始/结束UTC、仿真耗时、准备和重核总耗时；state用实际均值估算剩余任务并加20%余量，明确另留编译、排队、门级和功耗时间。芯片cycles不代替宿主耗时。生产RTL、固件或编译进模拟器的观察器变更后重新构建冻结contract。纯回执表示/解析工具修正若未改变模拟器输入，可保留原构建，但必须另建新批次、显式绑定runner及实际导入helper的SHA并逐项严格复核；668修正批次采用此路径，不把旧失败批次改为通过。不更改既有运行的文件或身份。

后续包的dma16_soc/dma16_gate只在TB增加被动bus_metrics模块，不纳入生产RTL或综合输入。模块使用实际accel/arb端口；门级路径必须来自同DDC的probe。四段计数、等待/响应延迟、接受间隔、读写切换和CPU竞争直方图随逐任务摘要保存，并与原window逐周期核对。最终批量contract要求完整统计块，逐任务receipt复核时重新解析；不能只凭结束标记通过。阶段统计包含重叠与计算间隙，不可相加充当总周期。

## 独立CPU竞争验证

`build_dma16_contention.py`构建独立轮询固件；生产IRQ固件、原驱动和RTL不修改。CPU在共享SRAM的`0xa0040000..0xa004007f`反复写入、fence、读回检查，与原ICB DMA竞争；该区不占用任务输入、输出或完成邮箱。至少16轮检查完成后才允许报告成功，输入/参数仍只经原SysMem源加载。构建完成不代表真实竞争已发生。

```text
python workspaces/arch03/scripts/build_dma16_contention.py --zig <zig> --output <新固件目录>
python workspaces/arch03/scripts/package_dma16.py <原打包参数> --contention-firmware <新固件目录>
python3 workspaces/arch03/scripts/server_run.py dma16_contention --session <新会话> --cases layer_01 rounding
```

包内该固件单列为`firmware_contention`。入口要求实际ASIC CPU输出检查通过、完整47904次DMA事务，且被动观察器记录同时请求、CPU获得服务及DMA获得服务均非零；缺任意一项就失败。结果scope为`dma16_asic_cpu_shared_contention_validation`，不混入正式IRQ版吞吐、功耗或最终1200性能配置。观察到该流量模式下的服务不等于穷尽所有仲裁序列。

## 干净目录复现与最终报告

以下是最终执行入口，尚未完成整轮干净复现。首先按所选包回执校验ZIP并安全解包到不存在的新目录，执行本包`server_run.inputs()`及五套固件验证；不得复制个人配置、厂商库或修改包manifest来通过。外部固定平台、库、工具和数据必须满足既有配置及哈希。

确认共享锁空闲、无他人EDA后，先在新session执行正式IRQ的`dma16_soc`默认14例，取得真实ASIC编译contract。再在不同新session执行`dma16_sequence --cases layer_01 rounding`和`dma16_contention --cases layer_01 rounding`。同一生产RTL/正式固件还需新综合；综合摘要、库和面积依据确认后，使用该目录与实际摘要SHA做门级。完整14门级的活动参数须明确包含12层：

```text
python3 workspaces/arch03/scripts/server_run.py dma16_gate --session <新的完整门级session> --synth-run <本次综合目录> --synth-summary-sha256 <实际SHA> --firmware-root <本包绝对路径>/firmware_irq --activity-cases layer_01 layer_02 layer_03 layer_04 layer_05 layer_06 layer_07 layer_08 layer_09 layer_10 layer_11 layer_12
```

逐层功耗每次只指定一个case，必须使用同一门级摘要；每层单独新session，不在旧失败目录重跑。未知活动完整定位入口见`UNKNOWN_ACTIVITY_REVIEW_20261110.md`。所有大波形扫描及EDA串行占用共享锁；原始完整活动不下载到Git。

最终1200使用已通过的真实ASIC contract，通过上述`dma16_batch.py run`进入全新输出目录；目录存在或配置不同不能覆盖。最终报告请求schema为`dma16-report-request-v1`：`asic`、`synthesis`、`gate`分别给出实际stage目录和summary SHA，`power`列出12个同配置stage目录和SHA，`batch`给出已完成批次目录及state SHA，`history`保留失败/停止/未验项。运行：

```text
python3 workspaces/arch03/scripts/dma16_report.py --request <哈希确认后的请求JSON> --output <不存在的新报告目录>
```

汇总器逐项重核1200回执、全部捕获输出及原始工件，不以文件数或完成标志代替验收。默认/含输入边界网络的功耗与能耗分列；缺项为null。时序、面积和功耗的正式审核仍须绑定具体报告及模型范围，不能因导出成功自动变为最终合格。

06:22新增可选`review`请求：`record`为`{path,sha256}`，指向`FROZEN_REVIEW_20261110.json`；`document`为其绑定的Markdown绝对路径；`timing`为实际只读时序stage的`{run,sha256}`；`ports`为完整端口诊断的`{path,sha256}`；`first_power`为提供no_clock/禁用弧证据的首层PT `{run,sha256}`。消费者重核工件、来源和具体数值，仅接受该记录已审定的任务模式综合时序与项目面积上界，绝不由首层PT批准12层系统功耗。没有review时继续保持未审核；原阶段summary不修改。JSON/summary.csv/中文报告显示独立审定状态，官方成绩和物理签核仍为false。此入口本地24项相关测试通过，实际服务器导出尚待执行。

当前3178工具包的干净本地检查为159tests、660输入、五套固件，不能冒称已完成这份实际服务器复现清单。生产实际完整证据仍分别位于fcd、a53、27bf和668冻结目录，借助哈希确认同一RTL/正式固件/数据，而不是拼接不同设计的最佳指标。
