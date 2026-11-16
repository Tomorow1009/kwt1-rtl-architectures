# C32-A受测配置与结果入口

截至2026-11-17，C32-A自身ASIC、240任务、精度、新综合和门级14已完成，finish03仍在采集活动。此页是查阅入口；冻结与最终功耗结论以随后生成的本版阶段报告为准。恢复工作先读根交接和[当前检查点](../../CONTEXT_CHECKPOINT_20261117_C32_FINISH.md)，不要重启以下已有队列。

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
| 12层活动，正在完成 | `runs/c32_finish03_saif/c32_saif` | `case_progress.json`只列已完成核对的层；最终以本阶段summary为准 |

综合目录中的`mapped.v`、`mapped.ddc`、`mapped.sdc`及面积/时序报告由其`summary.json`逐项绑定。不要使用旧61246bb失败包中的结果冒充修复包91135f6。固定12和240任务分别统计，不能混用均值。

后继由同一finish03队列生成`c32_finish03_timing_audit`、`c32_finish03_drc_audit`及`c32_finish03_power_layer_01`至`12`。队列成功退出后才运行已部署的export_review03工具，生成`runs/c32_report01/c32_report`与独立模型审阅事实；截至本页更新，该导出尚未运行，不能把计划路径当作已有报告。

## 只读恢复与保护

当前状态入口：

```text
python3 -B /tmp/s4_21usr_c32_20261116_2010/c32_status_readonly_v4.py
```

该入口只读取原队列，不派发任务。父进程308692只是启动时身份，恢复时核对实际命令、台账和状态。finish01/02因创建共享锁时空间耗尽退出，零子任务，保留且不重启；恢复24/25已完成，不重复清理。原协作锁由finish03统一持有，不手工清锁。

所有新产物位于`/tmp`，目前没有声称已有C32持久归档。桌面T80、旧八路、已冻结S0/P80/C80及其备份不改动。完整100条未获本轮自动运行授权；当前正式批量仅前20条。原始工具报告、失败和边界说明均保留，不能把布局前估算或无SDF门级称为物理签核。
