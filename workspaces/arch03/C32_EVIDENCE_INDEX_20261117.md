# C32-A受测配置与结果入口

截至2026-11-17 02:20，C32-A自身ASIC、240任务、精度、新综合、门级14、SAIF12、时序/约束查询与PT12全部完成，finish03已自然退出，export_review03正在汇总和独立模型审阅。此页是查阅入口；冻结结论以随后生成的本版阶段报告为准。恢复工作先读根交接和[当前检查点](../../CONTEXT_CHECKPOINT_20261117_C32_REVIEW.md)，不要重启以下已有队列。

## 受测身份

- 生产RTL：`61246bb2a21c56a9bfd871fd68de93028d79f5fd`；修复竞争固件后的受测包：`91135f61c97c980039793c6637d0a06888638df0`。修复没有改变RTL或IRQ/恢复固件。
- 包清单SHA：`d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7`，1081个输入。
- 硬件ID `0x4b57530d`、能力 `0x000b02bf`、编码layout `0x00100006`、数值身份 `0x000e0c20`、SHIFT10。
- 32 PE、事务信息队列深度2、源额度3；X/W缓存仍为60/32个128×16宏，原32字输出FIFO。C80编码文件与整数参考保持一致。
- 真实E203、IRQ/WFI、原32位ICB、源读→成功共享写ACK→实际共享读回→解码→计算→最终输出写ACK及排空。

服务器工作根为`/tmp/s4_21usr_c32_20261116_2010`。以下所有相对路径以其中的`light-light126-c32-91135f6`为根。

## 已有结果

| 内容 | 服务器运行目录 | 仓库证据 |
|---|---|---|
| ASIC14、固定12完整周期与输出 | `runs/c32_initial03_soc/c32_soc` | [ASIC与恢复/竞争核对](../../handoff/team/evidence/C32_ASIC_CORRECTED_20261116.json) |
| 无复位恢复、取消及重新启动 | `runs/c32_initial03_sequence/c32_sequence` | 同上；检查本版独立序列回执 |
| E203竞争与公平性 | `runs/c32_initial03_contention/c32_contention` | 同上；竞争周期不参与固定12性能或功耗汇总 |
| 三块映射、最终网表与面积 | `runs/c32_initial03_synth/c32_synth` | [综合数值](../../handoff/team/evidence/C32_SYNTH_INITIAL_20261116.json)、[面积分解](../../handoff/team/evidence/C32_AREA_BREAKDOWN_20261117.json) |
| 前20条、240任务与total核对 | `runs/c32_initial03_batch20/c32_batch20` | [批量回执](../../handoff/team/evidence/C32_BATCH20_20261117.json) |
| 同批浮点精度连接 | `runs/c32_initial03_precision/c32_precision` | [精度回执](../../handoff/team/evidence/C32_PRECISION20_20261117.json) |
| 同网表门级14，无SDF | `runs/c32_finish03_gate/c32_gate` | [门级回执](../../handoff/team/evidence/C32_GATE14_20261117.json) |
| 12层完整活动已完成 | `runs/c32_finish03_saif/c32_saif` | [SAIF12回执](../../handoff/team/evidence/C32_SAIF12_20261117.json) |
| 时序与约束查询已完成 | `runs/c32_finish03_timing_audit/c32_timing_audit`、`runs/c32_finish03_drc_audit/c32_drc_audit` | [诊断事实](../../handoff/team/evidence/C32_TIMING_DRC_DIAGNOSTICS_20261117.json) |
| 12层整机功耗数值已完成 | `runs/c32_finish03_power_layer_01`至`12`下的`c32_power` | [PT12数值及身份](../../handoff/team/evidence/C32_POWER12_20261117.json)，独立模型审阅进行中 |

综合目录中的`mapped.v`、`mapped.ddc`、`mapped.sdc`及面积/时序报告由其`summary.json`逐项绑定。不要使用旧61246bb失败包中的结果冒充修复包91135f6。固定12和240任务分别统计，不能混用均值。

全部阶段均由同一finish03队列生成。它成功退出后，export_review03于02:16:43启动，目标为`runs/c32_report01/c32_report`及独立模型审阅事实。当前导出仍在运行，不能把目标路径当作已经完整交付的最终报告，也不能重复启动该工具。

## 只读恢复与保护

当前状态入口：

```text
python3 -B /tmp/s4_21usr_c32_20261116_2010/c32_status_readonly_v4.py
```

该入口只读取原finish03队列，不派发任务；finish03父308692现已退出。当前活动状态应读`ROOT/c32_export_review03/state.json`，父36287和导出子36484最近仍存活。finish01/02因创建共享锁时空间耗尽退出，零子任务，保留且不重启；恢复24/25已完成，不重复清理。连接查询继续遵守原协作锁，不手工清锁。

所有新产物位于`/tmp`，目前没有声称已有C32持久归档。桌面T80、旧八路、已冻结S0/P80/C80及其备份不改动。完整100条未获本轮自动运行授权；当前正式批量仅前20条。原始工具报告、失败和边界说明均保留，不能把布局前估算或无SDF门级称为物理签核。

## 02:37报告与活动扫描更新

02:32:35通过可见VNC机器断言确认完整报告已生成：`runs/c32_report01/c32_report`下有JSON、逐任务/汇总CSV、中文说明和回执。report SHA为`4f4be422643e0123ec40ff106d3750237e1e1ed79d7c9869b22a590c7a6dc7d7`，网表SHA为`3c116d5a026b7e832030cd0c5a8def5a633ade9eaefb4efd1080851acc4bbd2c`，功耗和能耗原始值再次断言一致。固定12精度最大逐层NRMSE为0.1425636423408142%；20条精度另列，不混用。

02:37:33父36287仍运行、无error；导出子36484已退出，未知活动清单子42011正在读取L09。随后仍需本版DDC连接与model_review_snapshot，未启动C32-B/G32。原始报告保留采集阶段的review=false，最终独立结论另记，不覆盖原报告。证据见`handoff/team/evidence/C32_REPORT_OUTPUT_20261117.json`。最近已同步Git提交f88564d；本次新观察待同步。已完成队列、工具及清理均不重复执行。
