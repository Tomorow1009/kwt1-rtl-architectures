# ICB32 / R4 新版运行入口

08:54当前状态：原497门级14例/12层完整活动已于08:29:52完成；964唯一后继285397已完成首层功耗，正运行第2层，随后自动metrics14及自己的final1200。**以下通用命令不是要求重新启动已有任务。** 当前回执见根检查点、验收表和[新版功耗记录](ICB32_POWER_REVIEW_20261111.md)。

交付SDC由`scripts/icb32_delivery_sdc.py --synthesis <原icb32_synth目录> --summary-sha256 <原摘要SHA> --output <新目录>`导出。该工具只恢复被DC序列化舍入的HF周期和下降沿，核对实际metrics为6.666666ns，其余约束不变，原文件不覆盖。09:05小操作包已正常上传、解包及5文件哈希核验，服务器成功导出到964包`runs/icb32_delivery_sdc01`，09:07回执独立哈希通过；不是新增综合或原功耗已重跑的证据。

当前有效要求为 IMPLEMENTATION_PLAN_ICB32_C64_20261110.md。本文记录工具入口，不是运行通过证明。原 fcd DMA16 仍为交付退路。

## 输入及平台

包由 `scripts/package_icb32.py` 从已提交源码导出并重新编译 IRQ/WFI 固件；数据仍是已有同源 14 例的 tile8 原始格式，每例独立重排和无损编码。ITCM 只含程序与 16B 任务元数据，不含任务输入。服务器先运行 `server_run.inputs()`，再核验固件和新平台副本。

49759e1包于01:23完成FileZilla上传、服务器安全解包/630输入及三固件核验。目录`light-light126-icb32-r4-20261111_011258-49759e108719`，ZIP SHA `ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4`，FileZilla已退出。03:01前真实CPU竞争2例及10阶段无复位恢复均通过，03:06只读网表端口probe通过；03:08启动同网表gate14/12活动，PID209764，`runs/icb32_r4_gate01`。PPA/最终1200尚未完整验收。

e65前包唯一后继PID75421已完成真实ASIC/E20314例354816输出及IRQ/WFI，12层平均34616周期；ASIC摘要SHA `e5d009732e822cb5cf730e85b652a160f5022ba0197a9e6ff60960d76121d604`。新综合也已完成，摘要SHA `fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`；setup/hold为正，新增面积上界0.926562mm²。02:55已确认队列正常结束/锁释放，禁止重复启动。详见[03:10检查点](../../CONTEXT_CHECKPOINT_20261111_0310_ICB32.md)和[综合证据](../../handoff/team/evidence/ICB32_SYNTH_20261111.json)。

R1对照包 `light-light126-icb32-r1-20261111_012941-f95e940862ca` 已正常FileZilla上传，服务器607输入和ID4b574601/rows1固件核验通过，尚未执行服务器ASIC/PPA。本地同通路14例与R4全部输出逐坐标相等，12层平均116280周期，见[局部对照](ICB32_LOCAL_COMPARISON_20261111.md)。后续诊断/报告用497 R4包；R4主ASIC/综合仍引用e65受测目录，不能混用R1配置。

## 顺序执行

从新包根目录执行，每个阶段使用原共享锁；失败目录保留，不原地重试。`icb32_bringup_queue.py` 仅等待指定旧队列的完整 `done.json` 与共享锁释放，然后串行运行新 ASIC 14 例和综合；它不批准时序、面积或冻结选择。前驱 PID 必须先实际核对，其 plan SHA 与完成项数须一致。

```text
python3 workspaces/arch03/scripts/server_run.py icb32_soc --session icb32_r4_first01
python3 workspaces/arch03/scripts/server_run.py icb32_synth --session icb32_r4_first01
```

新综合独立生成 DDC/网表，不读旧 synth07 或 fcd 网表。128 个大宏复用 TCM/共享存储，96 个小宏属于加速器，总224个；加速器、DMA、decoder、仲裁、路由及共享控制逻辑均计入新增预算。保守上界另外计入全部系统标准单元，不能漏掉总线外的新增胶合逻辑。1.8 mm²预警、2.0 mm²硬限；工艺与周期仍 SS/0.99V/125°C/6.666666ns。

通过功能后读取实际 setup/hold、环路、约束和面积，按计划选择继续或修复。综合摘要的 reports_ready_review_required 不等于严格时序验收。

```text
python3 workspaces/arch03/scripts/server_run.py icb32_gate --session icb32_r4_gate01 --synth-run <实际综合目录> --synth-summary-sha256 <实际SHA> --activity-cases layer_01 layer_02 layer_03 layer_04 layer_05 layer_06 layer_07 layer_08 layer_09 layer_10 layer_11 layer_12
python3 workspaces/arch03/scripts/server_run.py icb32_power --session icb32_r4_power_l01 --gate-run <实际门级目录> --gate-summary-sha256 <实际SHA> --cases layer_01
python3 workspaces/arch03/scripts/server_run.py icb32_timing_audit --session icb32_r4_timing01 --synth-run <实际综合目录> --synth-summary-sha256 <实际SHA>
```

门级入口只绑定实际探测到的六个模块边界端口；不依赖综合可能删除的寄存器别名。完整窗口从首源 VALID 到最后结果写 ACK，随后检查真实 MMIO 完成/空队列证明。功耗使用同网表12个实际窗口，带动态编码长度、224宏归属、活动与未知值记录；实际数值由 `icb32_power_numbers.py` 提取。没有实际报告前不能沿用原29.627mW，也不能用零补缺项。门级不含 SDF，功耗为布局前估算。

## 最终批量

```text
python3 workspaces/arch03/scripts/server_run.py icb32_batch --session icb32_r4_final1200 --dataset <既有100样本原始数据根目录>
```

批量入口要求原固定数据 manifest SHA `0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`，100个样本各12层；历史用户指定根目录为 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，执行前重新核对该清单。一次新ASIC编译，1200次独立冷启动，逐项25344输出校验，总30412800。每任务保存压缩数据/固件元数据/真实CPU回执及哈希，关闭大波形；不接受旧37任务或原DMA16批量PASS。最终版本仍需自己的门级14、活动功耗12及干净目录复现。

## 本地检查范围

真实E203无复位恢复入口：`server_run.py icb32_sequence --session <新会话> --cases layer_01 rounding`，打包增加 `--sequence`（当前仅R4）。10阶段包括5种被硬件拒绝的配置及实际store-access-fault恢复、初载取消、4096周期驱动超时排空、A/B/A；A/B的编码长度独立写入元数据和源选择描述符，不预载硬件数据。新观察器要求共享写ACK后才能消费压缩字、按独立原始半字检查解码、动态计数且无共享读回；完成后检查实际MMIO状态和全部输出。独立polling序列不作IRQ性能/能耗。首次本地8192周期超时已进入计算，不符合此项“初载超时”测试的边界，保留失败并改为4096；没有修改RTL。10阶段本地pin_mock与3类故障拒绝通过，76032输出一致，CPU验收解析器明确拒绝这些NO_CPU记录。详见 `handoff/team/evidence/ICB32_SEQUENCE_LOCAL_20261111.json`；03:01已在497包通过真实E203全部10阶段，见`ICB32_CPU_DIAGNOSTICS_20261111.json`；此段前述是本地开发历史。

真实CPU竞争入口为 `server_run.py icb32_contention --session <新会话> --cases layer_01 extremes`；打包时加 `package_icb32.py --contention` 纳入独立polling固件。CPU仅访问共享SRAM空闲区0xa0040000的128B，逐字写/读/比较；被动观察器要求任务窗口中同时有CPU和DMA请求、双方服务及scratch读写，并检查等待CPU时已接受DMA机会不超过8。该固件不作为IRQ性能或功耗样本，生产IRQ固件和RTL保持原实现。03:01前已完成真实E203两例竞争，最大CPU等待仅1次DMA接受机会，见`ICB32_CPU_DIAGNOSTICS_20261111.json`。

新增 `scripts/icb32_report.py --request <request.json> --output <新目录>` 导出逐层及汇总 JSON/CSV/中文报告。请求 schema 为 `icb32-report-request-v1`，asic/synthesis/gate 均提供对应新阶段目录与 summary SHA256；power 为同格式引用列表，batch 可选。工具重新核对真实输出、压缩布局、完整窗口、新224宏配置、同硬件身份及新1200回执，不导入旧DMA16批量PASS。缺失功耗为空，时序/面积/功耗验收保持待审，5000目标按真实总周期判断。本地3项报告防混用检查通过，不代表实际PPA。

04:24补充：`icb32_bus_metrics.py`向新的ASIC测试台插入仿真专用计数，不改DUT或固件，原生产观察器与当前映射门级保持不变。计数覆盖X/W宏端口读写、有效MAC更新、三段接受至响应延迟、ready等待、响应反压、同拍退旧接新及结果反压；SRAM单位是一次16位逻辑宏端口请求。等待和延迟可能重叠，不相加当总周期，不用计数推断功耗。后续新ASIC/最终batch回执和报告导出这些字段，并补100样本编码字节分布；旧e65/497回执没有的字段保持缺失。

新增观察器已用现有本地首层及极值两例通过50688输出，周期仍34639/38052；两例均测得X读101376/写6336、W读409600/写16384、有效MAC1622016。首层全任务MAC利用率73.166%、事务率0.90609/周期；这是无CPU局部测量，R1计数尚未实测，详见[证据](../../handoff/team/evidence/ICB32_PASSIVE_METRICS_LOCAL_20261111.json)。新包尚须真实ASIC14复现，可同时作为干净目录功能复现；不得把本地计数标成服务器结果，也不因此重跑已有同网表gate。

04:46已完成964测量包的正常FileZilla上传、安全解包及636输入/三固件预检；生产RTL、正式IRQ ELF和所有运行映像与497一致，诊断序列ELF只有非装载调试/符号节不同。见[新包身份](../../handoff/team/evidence/ICB32_METRICS_PACKAGE_20261111.json)。当前497门级队列保持原样继续。

`icb32_finalize_queue.py`是独立的执行工具，不修改已上传运行包。它绑定原gate的PID、启动时间和综合摘要，只有原14例及12活动全部成功、共享锁释放后才串行运行12层功耗、964普通ASIC14和最终1200。每项失败立即停止，独立session不重试、不清锁；每层功耗数值提取检查实际单位、求和及224宏，仍保留`system_power_verified=false`。结束时生成`report_request.json`，不自动导出或批准最终报告。该工具可单独随小型操作包从已提交源码导出并经FileZilla传送，不必再次打包相同DUT/固件。排队进程不占EDA许可证；状态记录在目标包`runs/<session>_queue/state.json`。当前本地4项队列边界检查通过，是否已启动必须查最新检查点及服务器状态。

R4完整datapath两套14例、错误恢复及合成CPU竞争通过；12名义层平均34616周期、4333.256 task/s只是无E203的pin_mock折算。生成的端口观察器又通过L01压缩34639与extremes原始回退38052周期，目录 `local_runs/icb32_monitor_fixture_20261110_234937_735905`。这两例不是映射网表验证。新版ASIC、综合、门级、功耗、1200及最终报告均以实际新运行回执为准。
