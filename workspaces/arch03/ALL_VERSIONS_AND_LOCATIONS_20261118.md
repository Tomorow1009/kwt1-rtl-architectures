# 全部探索版本、结果与文件位置

整理日期：2026-11-18。依据仓库版本索引、各阶段报告/冻结回执，以及N1收尾时已读取的服务器终态。本文只汇总，不启动任何仿真、EDA、上传或清理。旧报告中的“当时运行中”按后续回执更新解释，不改写历史原件。

## 先看路线关系

```text
架构一 v1.0 → v1.1 → v1.2 → v1.3
                              ↓
架构二 v2.0：8路MAC＋SRAM
                              ↓
架构三：8路MMIO → 16路DMA（664 task/s）
                              ↓
                 B1 ACK转发试验 → R1（16 MAC）→ R4（64 MAC）
                                                           ↓
                                            B/v2 → B/v3＝B0（80 PE）
                                                           ↓
                                                     N1缩位（5049）
                                                        ├→ N2门控：本地完成，路线终止
                                                        └→ T80：原System Bus真实共享读回
                                                             ├→ T64：功能完成，综合后终止
                                                             │     └→ G64：未实施
                                                             └→ S0分块综合
                                                                   → P80搬运流水
                                                                   → C80无损编码
                                                                   → C32-A（32 PE）
                                                                        ├→ C32-B两宏缓存：本地淘汰
                                                                        └→ G32实际门控（已冻结）
```

N1、R4、B0的ACK后转发路径，与T80之后经原System Bus真实读回共享SRAM的路径不同。早期DMA16虽有共享写后读回，也不能直接等同后期T80的原平台服务时序。不能只按不同路径的task/s排名或将差值归因于MAC数量。

## 每个版本做了什么

| 版本 | 已实现/探索内容 | 已取得结果与最后处置 | 主要本地证据入口 |
|---|---|---|---|
| 架构一 v1.0.0 | 串行64项点积、bias、定点转换、握手与复位 | 独立RTL回归通过；数值核心起点 | `architectures/arch01_serial_mac/v1.0.0/ORIGINAL_README.md` |
| 架构一 v1.1.0 | 接入真实KWT-1 HEX、独立整数参考 | 软件和两套仿真器各12层通过 | `architectures/arch01_serial_mac/v1.1.0/README.md` |
| 架构一 v1.2.0 | 扩展语音/层批量验证 | 软件1,269,948任务；每套RTL 6,528独立任务。这里不是完整矩阵SoC任务 | `architectures/arch01_serial_mac/v1.2.0/README.md` |
| 架构一 v1.3.0 | 从单点积扩展到完整99×256输出矩阵 | 单样本12层，软件及两套仿真器各304,128输出通过 | `architectures/arch01_serial_mac/v1.3.0/README.md` |
| 架构二 v2.0.0 | 8路MAC、18KiB内部SRAM及官方宏适配 | VCS厂商功能模型304,128输出及DC单角检查；并非架构三真实E203完整任务 | `architectures/arch02_matrix/v2.0.0/README.md`、其`arch02/SERVER_HANDOFF.md` |
| 架构三8路MMIO | 接入E203/ICB，CPU逐字搬运和控制；TCM、宏时序、标准单元、UART修复 | 新加载源口径3,843,121周期；ASIC14、门级14、活动12已完成。旧3,890,080等BEGIN边界记录另保留；不能混用 | `MMIO8_SOURCE_HANDOFF.md`、`MMIO8_SOC_HANDOFF.md`、`ICB32_STAGE_REPORT_20261111.md` |
| DMA16 | 16路MAC、任务级DMA、双权重bank、FIFO、IRQ/WFI；源读/共享写/共享读/输出写 | 225,770周期，664.393 task/s；自己的1200任务、门级14和12层功耗数值 | `DMA16_IMPLEMENTATION_REPORT.md`、`FROZEN_REVIEW_20261110.md` |
| B1搬运试验 | 16路核心，原始输入成功共享写ACK后转发，减少重复读回 | 本地14例抖动与6例nominal；代表性预取开启162,713周期。没有独立服务器PPA | `handoff/team/evidence/ICB32_B1_14_20261110.json`、`ICB32_B1_NOMINAL_20261110.json` |
| R1 | 16 MAC＋32位改进搬运、v2无损编码与缓存 | 真实ASIC14；固定12平均116,280周期，1289.990 task/s；综合面积上界0.618655mm²。未形成自己的完整门级/功耗交付 | `ICB32_LOCAL_COMPARISON_20261111.md`、`handoff/team/evidence/ICB32_R1_SERVER_20261111.json` |
| R4 | 同一搬运/编码改为16列×4行广播，64 MAC | 34,616周期，4333.256 task/s；1200、门级14、活动12、12层功耗及干净ASIC14复现 | `ICB32_DELIVERY_20261111.md`、`ICB32_STAGE_REPORT_20261111.md` |
| B/v2 | 5×16输出驻留脉动，80 PE，五行缓存、双结果接口；仍先加载全X | 实际ASIC14通过，平均36,862周期，慢于R4；保留调试退路 | `SYSTOLIC_B_STAGE_HANDOFF_20261112.md` |
| B/v3＝B0 | 新v3无损流；W0/bias优先、首五行到齐提前启动；源额度3；双结果写回 | 30,502.333周期，4917.657 task/s；1200、门级14、完整活动功耗；生产63da6ba，备份标签固定 | `SYSTOLIC_B_STAGE_HANDOFF_20261112.md`、`N1_FINAL_REVIEW_20261113.md` |
| N1 | 真正缩为X14/F10、W12/F12、乘积26、累加/bias32、total33，SHIFT10；仍80 PE与原缓存 | 29,711周期，5048.635 task/s；自己的1200、total/result/sat、门级14及完整PPA，11月18日完成持久备份与交付 | `N1_FINAL_REVIEW_20261113.md`、`N1_CLOSEOUT_20261118.md` |
| N2 | 在N1数据寄存器上加入实际ICG封装，控制/valid/IRQ仍运行 | 本地10,000随机＋32定向、794,560输出及14例搬运通过，周期与N1一致。新计划终止后未取得独立ASIC/PPA | `PROGRESS_N1_N2_20261113_1505.md`、`N2_ABI.md` |
| T80 | 保留N1的80 PE缩位核心，改为原System Bus真实共享写ACK后读回；严格四段完整计时 | 112,569周期，1332.516 task/s；240任务、恢复/竞争、门级14、活动功耗12。桌面交付禁止改动 | `T80_MEASURED_TRANSPORT_20261113.md`、`S0_STAGE_REPORT_20261116.md` |
| T64 | T80改为4×16、64 PE；保留五行物理X缓存、双结果及相同搬运 | ASIC14、240任务/6,082,560输出和total、恢复/CPU竞争通过；平均112,568周期。原综合完成后旧队列退役，未完成独立PPA | `T64_IMPLEMENTATION_REPORT.md`、`CONTEXT_CHECKPOINT_20261115_T64_PAUSED_FOR_NEW_PLAN.md` |
| G64 | 原计划在T64上加门控 | 没有实施或正式运行；被32 PE新计划取代，不存在G64受测成绩 | `T64_G64_RESUME_PLAN_20261115.md`、`IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md` |
| S0 | T80的CPU/SoC、共享SRAM、加速器分块综合再链接；保持RTL和搬运 | 同为112,569周期；新网表自己的门级/活动/PPA完成并归档。是实现流程基线，不是新的算术架构 | `S0_STAGE_REPORT_20261116.md` |
| P80（S1正式实现） | 原32位总线内有序事务信息队列、归属及信用管理 | 深度2/4/8各ASIC14，周期相同，选深度2。77,545.333周期；240、门级14、完整PPA和归档完成 | `P80_STAGE_REPORT_20261116.md` |
| C80 | 格式6：预测/精确残差、有界Rice、raw回退、两半字bias；保持80 PE | 固定12编码均值29,756→25,790B；70,603.167周期，2124.551 task/s；240及完整PPA归档 | `C80_STAGE_REPORT_20261116.md`、`C80_CODEC_FORMAT_20261116.md` |
| C32-A | C80改为2×16、32 PE，50个行组，末行单独有效；X仍60个小宏 | 72,179.333周期，2078.157 task/s；修复03最终网表240、门级14、活动功耗12及归档通过 | `C32_STAGE_REPORT_20261117.md` |
| C32-B | 两个4096×16 X宏、奇偶行分bank，评估减宏 | 本地14例正确；同条件合计725,798→726,236周期，吞吐下降0.06031%，未晋级服务器PPA | `C32B_LOCAL_SELECTION_20261117.md` |
| G32 | C32-A加入383个真实ICG，覆盖10,306个数据寄存器时钟端点 | 与C32-A逐层周期不变；功耗/能耗下降12.6304%。原20条240任务、门级14、活动功耗12和持久归档均完成 | `G32_STAGE_REPORT_20261117.md`、`FINAL_ROUTE_REPORT_20261117.md` |
| G32追加100条 | 不改冻结硬件，只增加独立100条入口 | 1200与浮点精度队列终态已观察为`full100_and_precision_passed_archive_pending`；报告/持久归档等待器仍暂停。原20条冻结交付独立有效 | `CONTEXT_CHECKPOINT_20261117_G32_FULL100.md`及本次N1交接中的后续终态记录 |

表内无目录前缀的阶段报告均在仓库`workspaces/arch03/`。`handoff/team/evidence/`及`CONTEXT_...`分别相对于仓库根。旧文档可能保留早期状态，最终结论按后续审阅/冻结回执读取。

## 可用数值放在一起看

吞吐按150MHz折算；功耗为同完整窗口的整机布局前估算；面积为项目保守上界。不同路径或服务条件不是受控的单变量比较。`—`表示未形成该版完整可用结果，绝不补零。

| 版本 | 固定12平均周期 | task/s | 面积mm² | 功耗mW | µJ/task |
|---|---:|---:|---:|---:|---:|
| 旧8路MMIO | 3,843,121 | 39.03 | — | 仅L01可确认19.9391 | 仅L01为510.8566 |
| DMA16 | 225,770 | 664.393 | 0.434797 | 29.6273 | 44.5931 |
| R1 | 116,280 | 1289.990 | 0.618655 | — | — |
| R4 | 34,616 | 4333.256 | 0.926562 | 71.8126 | 16.5724 |
| B0 | 30,502.333 | 4917.657 | 1.099095 | 69.8371 | 14.2013 |
| **N1** | **29,711** | **5048.635** | **0.951149** | **61.7773** | **12.2364** |
| T80 | 112,569 | 1332.516 | 0.952138 | 50.2316 | 37.6968 |
| T64 | 112,568 | 1332.528 | — | — | — |
| S0 | 112,569 | 1332.516 | 0.953522 | 50.2404 | 37.7034 |
| P80 | 77,545.333 | 1934.352 | 0.952929 | 53.7759 | 27.8004 |
| C80 | 70,603.167 | 2124.551 | 0.961136 | 55.3676 | 26.0608 |
| C32-A修复03 | 72,179.333 | 2078.157 | 0.722408 | 48.9738 | 23.5660 |
| **G32** | **72,179.333** | **2078.157** | **0.727972** | **42.7882** | **20.5895** |

旧8路的L01不是12层平均；L02历史队列状态不冒充最终整套功耗。DMA16/R4的已取得功耗数值和各自历史审阅范围按原报告保留；不把后期N1/G32的模型审阅结论转移给早期配置。B0与N1的模型/活动审核后续在N1最终审阅中闭环。官方600条、SDF、布局后寄生/时钟树、硅片功耗不属于上述内部仿真结果。

## 其他确实讨论或试过的路径

| 路径 | 结果/处置 |
|---|---|
| PR #5 / PR #6软件坐标递推 | 作为8路来源与软件优化思路保留；没有给PR #6安排独立完整PPA轮次 |
| 8路DMA中间版 | 新计划明确取消，直接推进16路DMA；不要与8路MMIO混称 |
| 64/128位数据侧、C64/C128 | 完成带宽预算；32位四段47,904事务说明只扩MAC不能达到5000。未获框架确认前未接入正式SoC；这些命名不等于后来T64/C32 |
| 80 MAC广播A | 为缩短工期取消，直接开发脉动B；没有同规模A/B硬件对照 |
| 省掉共享写入/任意私有SRAM旁路 | 没有作为正式实现；R4/B0/N1仍实际写共享SRAM，ACK后转发不同于省掉共享写 |
| R4 raw与v2编码 | 同本地12层输出一致；38,052→34,616周期，减少9.03%。没有独立CPU/PPA，不能把压缩率当能耗收益 |
| B/v3源信用16/3及2/4/6/8局部筛选 | 信用16本地12层35,316.83周期；信用3为30,502.33并经ASIC确认；2/4/6/8仅局部层筛选 |
| N1计划中的D1/D2 | 未按该旧阶段名形成独立验收版本；后来的C80和P80实现了相关编码/搬运优化，但配置和路径已变，不能倒填旧阶段PASS |
| P80队列深度2/4/8 | 实际CPU周期相同，冻结最小深度2；证明继续加深不是当前瓶颈的有效解法 |
| 工具/物理映射修复 | B DRC04→05→06、C32 repair01→02→03等是修复迭代，不另造性能版本。旧失败保留，最终功耗/门级绑定修复后网表 |
| VCD→原生SAIF | 小型与R4完整窗口交叉对照通过，解决大波形空间问题；属于测量流程变化，不是RTL加速收益 |

## 本地文件位置

本次总览所在且包含各阶段源码/报告的工作树：

```text
E:/fpga_race-two/kwt1-legacy5000-20261117
```

| 内容 | 本地完整地址 |
|---|---|
| 本总览 | `E:/fpga_race-two/kwt1-legacy5000-20261117/workspaces/arch03/ALL_VERSIONS_AND_LOCATIONS_20261118.md` |
| 架构一各版快照 | `E:/fpga_race-two/kwt1-legacy5000-20261117/architectures/arch01_serial_mac/` |
| 架构二v2快照 | `E:/fpga_race-two/kwt1-legacy5000-20261117/architectures/arch02_matrix/v2.0.0/` |
| 架构三所有RTL | `E:/fpga_race-two/kwt1-legacy5000-20261117/workspaces/arch03/rtl/` |
| 固件、测试台、运行/编码工具 | 同工作树`workspaces/arch03/sw/`、`tb/`、`scripts/`，以各运行包manifest为受测身份 |
| 所有小型验收证据与冻结回执 | `E:/fpga_race-two/kwt1-legacy5000-20261117/handoff/team/evidence/` |
| B0独立备份（含源码ZIP、Git bundle及本地历史产物） | `E:/fpga_race-two/backups/systolic-b-20261112_2320/` |
| 原8路/DMA16/R4/B0/N1/N2开发树 | `E:/fpga_race-two/kwt1-rtl-architectures/` |
| T80/T64原工作树 | `E:/fpga_race-two/kwt1-t80-t64-g64/` |
| T64/G64后续工作树 | `E:/fpga_race-two/kwt1-t64-g64-20261115/` |
| S0/P80/C80/C32/G32及追加100条工作树 | `E:/fpga_race-two/kwt1-c32-g32-20261115/` |
| 本地截图、转录校验与连接记录 | `E:/fpga_race-two/takeover_local/`；不是生产源码 |

旧工作树的根交接可能停在较早时刻，不能只看mtime判断最新结果。查版本请以受测提交、独立冻结回执及本总览的后续状态为准。

主要RTL名：8路`arch03_icb_accel.sv`；DMA16 `arch03_dma16_accel.sv`/`arch03_linear16.sv`；B1 `arch03_dma16_forward_accel.sv`；R1/R4 `arch03_icb32_accel.sv`/`arch03_linear16x4.sv`（行并行配置不同）；B0 `arch03_systolic_b_*`、`arch03_linear16x5_systolic.sv`；N1/N2/T80/T64/P80/C80/C32/C32B/G32分别看`arch03_n1_*`、`arch03_n2_*`、`arch03_t80_*`、`arch03_t64_*`、`arch03_p80_*`、`arch03_c80_*`、`arch03_c32_*`、`arch03_c32b_*`、`arch03_g32_*`。模块有复用，不能仅复制一个前缀就视为完整工程；完整文件集看冻结包manifest。

## 服务器文件地址

下表`P`完整展开为：

```text
/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109
```

优先查看持久备份或结果目录。`/tmp`是原始运行位置，不等于持久备份；有持久副本的版本优先保留恢复索引。表中历史路径来自已保存回执，本轮没有逐个重跑或改写。

| 版本 | 持久结果/备份位置（`P/`按上方展开） |
|---|---|
| 架构二v2 | `/storage2/2026contest/server4/s4_21usr/Desktop/IC/arch02_server_r03/`；r01/r02失败记录同级保留 |
| 旧8路 | `P/bundles/light-light126-mmio-timing-dma16-20261110_111311-ecf3cd4afb3c/`；门级`runs/mmio8_source_gate_full01/mmio8_gate/`、功耗各独立`mmio8_fullpower_*`session |
| DMA16生产包 | `P/bundles/light-light126-dma16-loopfix-dma16-20261109_215719-fcd445fb212a/` |
| DMA16完整汇总 | `P/bundles/light-light126-power-sumchain-dma16-20261110_081342-a2e2bc682696/runs/dma16_report_full02/output/` |
| R1 | `P/bundles/light-light126-icb32-r1-20261111_012941-f95e940862ca/`；ASIC在`runs/icb32_r1_compare01/icb32_soc/` |
| R4报告、1200及复现 | `P/bundles/light-light126-icb32-r4-20261111_043048-96443c284a1c/`；报告`runs/icb32_r4_final_report01/`，批量`runs/icb32_r4_finish01_final1200/icb32_batch/` |
| R4综合网表 | `P/bundles/light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0/`，原独立综合session |
| R4门级/活动 | `P/bundles/light-light126-icb32-r4-20261111_011258-49759e108719/runs/icb32_r4_gate01/icb32_gate/`；部分大波形已按回执无损迁移 |
| B0完整证据备份 | `P/backups/systolic-b-20261112_2320/completed-evidence.tar.gz`，同目录manifest/receipt；早期备份不含后来生成的最终汇总 |
| B0最终汇总、综合及后续工具 | `P/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/`；最终汇总`runs/systolic_b_backup_report01/`，综合`runs/systolic_b_v3_drc06/systolic_b_synth/` |
| **N1可直接阅读的交付** | **`P/operations/n1-closeout-20261118_0110/`**：README、results、review、synthesis、key_rtl、closeout.json |
| N1完整3包备份 | `P/backups/n1-runtime-20261118_0110/runtime-evidence.tar.gz` |
| N1报告/精度来源等辅助备份 | `P/operations/n1-aux-archive-20261118_0015/auxiliary-evidence.tar.gz` |
| **T80桌面交付（禁止改动）** | **`/storage2/2026contest/server4/s4_21usr/Desktop/T80_Delivery_20261113/`** |
| S0完整备份 | `P/backups/s0-runtime-20261116_0209/` |
| P80完整备份 | `P/backups/p80-runtime-20261116_1155-copy03/` |
| C80完整备份 | `P/backups/c80-runtime-20261116_1923-copy03/` |
| C32-A修复03完整备份 | `P/backups/c32-runtime-20261117_0709-repair03-copy01/` |
| G32正式20条完整备份 | `P/backups/g32-runtime-20261117_1326-final01/`；`runtime-evidence.tar.gz`和manifest/receipt |

原始运行/研发位置：

| 版本 | 原始服务器路径或本地研发入口 |
|---|---|
| B/v2、B/v3中间版本 | B0备份的manifest及本地`E:/fpga_race-two/backups/systolic-b-20261112_2320/`的11个历史运行包索引 |
| N1原运行根 | `/tmp/s4_21usr_n1_20261113_0210/`；已有上述完整持久备份 |
| N2、B1、C32-B | 本地源码和`handoff/team/evidence/`，不列不存在的服务器PPA目录 |
| T64 | `/tmp/s4_21usr_t64_20261115_1510/`；`light-light126-t64-resume-b9155b4/runs/t64_soc03/t64_soc/`、`light-light126-t64-resume-3552163/runs/t64_serial03*` |
| S0 | `/tmp/s4_21usr_t80_20261115_1830/`；报告`light-light126-t80-s0-66b9496/runs/s0_report01/t80_s0_report/` |
| P80 | `/tmp/s4_21usr_p80_20261116_0315/light-light126-p80-1023646/runs/p80_report05/p80_report/` |
| C80 | `/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7/runs/c80_report02/c80_report/` |
| C32-A最终报告 | `/tmp/s4_21usr_c32_20261116_2010/light-light126-c32-repair-5828804/runs/c32_report_repair03/c32_report/` |
| G32最终20条报告 | `/tmp/s4_21usr_g32_20261117_0810/light-light126-g32-0e16994/runs/g32_report01/g32_report/` |
| G32追加100条 | `/tmp/s4_21usr_g32_20261117_1530/light-light126-g32-full100-398a58b/`；队列`runs/full100_02`、批量`runs/full100_02_batch100/g32_batch100`、精度`runs/full100_02_precision100/g32_precision100`。追加收尾尚未发布，不把计划备份名写成已存在 |
| N1/G32缩位100条原HEX | `/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all/` |

R4 L04/L05/L06的持久无损XZ分别在`P/backups/r4-l04-xz-20261117/`、`P/backups/r4-l05-xz-20261117/`、`P/backups/r4-l06-xz-20261118/`。恢复按各receipt核对原始字节和SHA，不能把历史gzip路径不存在解释为原波形内容丢失。旧八路和桌面T80保护规则继续生效。

## GitHub身份与使用建议

私人仓库：`https://github.com/Tomorow1009/kwt1-rtl-architectures`。

- 当前全量汇总/N1收尾分支：`codex/light-light126/legacy5000-closeout-20261117`。本次收尾前完成提交`feb62f7cbcc5763bc2523e51c91e0d72d1b8a103`；文档后续提交不改变受测硬件。
- B0硬件`63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86`；备份tag `arch03-b-backup-20261112-2320`。
- N1硬件`9305c6948c764fed01fe86b20bb3db94170299ab`；运行工具`0f62e41207909904efd544992013c1244b0fd63b`。
- T80硬件`876b883d95199f2d1889019cbfec4c93c42d1be5`；T64硬件`e2e83ce121963d499ea67914b4c34a05a0c58f27`。
- P80硬件`142fae28545759e33fa38de514eabf752cb8c43a`；C80受测包`74f3ae7bb479d5fdd7917702c4a2c0671eacb61b`，硬件自2896d5d后不变。
- C32-A tag `arch03-c32a-repair03-20261117-0725`，修复03最终网表身份见冻结回执。
- G32硬件`0e16994675bb15e53642017a88f6307da9af4a01`，tag `arch03-g32-final-20261117`；追加100条入口398a58b不改变硬件。

要找“约5000”的版本，直接用N1交付目录和N1冻结身份。要找后期真实共享读回、32PE、实际门控的最终实现，用G32的20条冻结包及其原PPA；追加100条结果与收尾状态单列。要作架构路线对照，使用本总览和各阶段报告，保留路径、量化和计时条件差异，避免拼接不同版本的最佳数字。
