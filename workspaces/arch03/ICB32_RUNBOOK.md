# ICB32 / R4 新版运行入口

当前有效要求为 IMPLEMENTATION_PLAN_ICB32_C64_20261110.md。本文记录工具入口，不是运行通过证明。原 fcd DMA16 仍为交付退路。

## 输入及平台

包由 `scripts/package_icb32.py` 从已提交源码导出并重新编译 IRQ/WFI 固件；数据仍是已有同源 14 例的 tile8 原始格式，每例独立重排和无损编码。ITCM 只含程序与 16B 任务元数据，不含任务输入。服务器先运行 `server_run.inputs()`，再核验固件和新平台副本。

2026-11-11 01:23，49759e1 新包已通过板端 FileZilla 上传、服务器 ZIP SHA 安全解包、630 输入及 IRQ/竞争/序列三套固件哈希核验。新包目录为 `light-light126-icb32-r4-20261111_011258-49759e108719`，SHA256 为 `ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4`。FileZilla 已断开退出。该包仅预检通过，实际新 ASIC、诊断和 PPA 尚未验收。

e65 前包的唯一后继 PID75421 已于00:53启动，目录 `runs/icb32_r4_first01_queue`，等待原串行队列完成后 ASIC14→综合；01:24 实测仍等待，禁止重复启动。原 c019/e65 的预检及历史目录保留；最终运行状态以根交接的带时间记录为准。

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

真实E203无复位恢复入口：`server_run.py icb32_sequence --session <新会话> --cases layer_01 rounding`，打包增加 `--sequence`（当前仅R4）。10阶段包括5种被硬件拒绝的配置及实际store-access-fault恢复、初载取消、4096周期驱动超时排空、A/B/A；A/B的编码长度独立写入元数据和源选择描述符，不预载硬件数据。新观察器要求共享写ACK后才能消费压缩字、按独立原始半字检查解码、动态计数且无共享读回；完成后检查实际MMIO状态和全部输出。独立polling序列不作IRQ性能/能耗。首次本地8192周期超时已进入计算，不符合此项“初载超时”测试的边界，保留失败并改为4096；没有修改RTL。10阶段本地pin_mock与3类故障拒绝通过，76032输出一致，CPU验收解析器明确拒绝这些NO_CPU记录。详见 `handoff/team/evidence/ICB32_SEQUENCE_LOCAL_20261111.json`；真实E203执行仍待服务器。

真实CPU竞争入口为 `server_run.py icb32_contention --session <新会话> --cases layer_01 extremes`；打包时加 `package_icb32.py --contention` 纳入独立polling固件。CPU仅访问共享SRAM空闲区0xa0040000的128B，逐字写/读/比较；被动观察器要求任务窗口中同时有CPU和DMA请求、双方服务及scratch读写，并检查等待CPU时已接受DMA机会不超过8。该固件不作为IRQ性能或功耗样本，生产IRQ固件和RTL保持原实现。当前仅编译/工具检查，真实CPU竞争必须以服务器新阶段回执为准。

新增 `scripts/icb32_report.py --request <request.json> --output <新目录>` 导出逐层及汇总 JSON/CSV/中文报告。请求 schema 为 `icb32-report-request-v1`，asic/synthesis/gate 均提供对应新阶段目录与 summary SHA256；power 为同格式引用列表，batch 可选。工具重新核对真实输出、压缩布局、完整窗口、新224宏配置、同硬件身份及新1200回执，不导入旧DMA16批量PASS。缺失功耗为空，时序/面积/功耗验收保持待审，5000目标按真实总周期判断。本地3项报告防混用检查通过，不代表实际PPA。

R4完整datapath两套14例、错误恢复及合成CPU竞争通过；12名义层平均34616周期、4333.256 task/s只是无E203的pin_mock折算。生成的端口观察器又通过L01压缩34639与extremes原始回退38052周期，目录 `local_runs/icb32_monitor_fixture_20261110_234937_735905`。这两例不是映射网表验证。新版ASIC、综合、门级、功耗、1200及最终报告均以实际新运行回执为准。
