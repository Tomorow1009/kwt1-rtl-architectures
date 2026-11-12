# B检查点：2026年11月12日19:50

任务ACTIVE，继续直接5×16脉动B；A取消，R4保护。用户最新要求“同步本版已完成情况到GitHub，然后继续工作”已执行：**云头f6f704c4545efed65363d083c2cc7e1655299bdc，push和ls-remote一致。** 其中有自己的1200通过、SAIF方法通过、验收表、README和19:22检查点。此次19:50增量尚待同步。

压缩后先读AGENTS、有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`、本文件及[19:22完整已完成证据](CONTEXT_CHECKPOINT_20261112_1922_SYSTOLIC_B.md)，核已完成/未完成和失败路径。生产硬件63da6ba/v3/credits3冻结，不能因新采集回到开发A或优化RTL。11/13 17:00前收尾。

## 唯一当前作业：B活动12→功耗12

**19:48:59.519791实际观察：队列driver320367，活动child320434，status running，stage systolic_b_saif，无error；尚无完成层。**

- 队列：`runs/systolic_b_power_final01_queue/state.json`
- 当前child：`runs/systolic_b_power_final01_activity12/systolic_b_saif`
- launcher：`runs/systolic_b_power_final01_launcher.log`
- 新请求：`../../operations/b_power_final01_request.json`
- **实际请求SHA：`e99f9e51d8ddbff5c3921e01d15aac99a7b851018884857089044ccded5479d0`**。
- 工具：`../../operations/systolic_b_tools_4b58ff0/systolic_b_power_queue.py`，runner SHA`e9779c72bae7652cade03ed2f26644a0a2ebbb493c9c269a1bc9bb0c53c90366`；16文件manifest`bf8e214e70ac92b17b3ecc0c41497995ac0b1d0aa5c483a9662b0225b08f6289`。
- 首次启动预算free117758230528B、required4872908231B、12层、最大首例估计189265596B，含20%+2GiB余量；19:48:59实时free115593969664B。共享盘变化快，继续看每例实际体积与空间。
- **只做activity12→power_l01..12，不重复ASIC14/自己的1200/gate14/R4捕获。** 采集先新编译带可见性网表仿真，再逐层独立冷启动，核全部输出与同网表原窗口。
- 此前4个`b_power_request_prepare_00..03.txt`现在已全部执行，968B payload完成，**不得再次append或重复生成**。`b_power_final01_launch.txt`已成功执行一次，**不可再启动**。
- 首次启动因为本地手抄SHA中`...d8ddbf5fc...`与实际`...d8ddbff5c...`不同，被前置断言拦截；没有创建queue/log或启动EDA。错误命令本地保存为`b_power_final01_guard_failed_transcription.txt`。19:46实际两段SHA重新读取，并核LOCK False/QUEUE False/LOG False后修正，随后唯一启动成功。不是硬件失败，不覆盖旧运行。

## 已完成，不得重跑

1. **自己的真实ASIC/E2031200：1200任务/30412800输出、零失败，19:13:30.024913通过。** 摘要`017e7ca728e0c6f647660ef981f8d00541b552c0a38dec103809d9cc0c67fb09`。batch平均30503.34周期，宿主6467.229648秒；与12性能任务30502.333333周期不同。最终导出的独立回执复核和浮点误差汇总尚待。
2. 原final02已正常退出/释放锁，report_request SHA`67b1e150943f6c0d35a08811b31d0067d93a1c3bc6b076c5f15aefbc777e3fb2`；不重启149529/156788。
3. **R4 SAIF方法crosscheck02通过**，19:18:05.488335终态。摘要`a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26`。整机差0.013849%、最大主要模块CPU差0.534759%，均≤1%；1060默认声明actual PT direct/leaf连接均0，证明SHA`5c4bc75c7d9bb02f073fc8fbe6de26a98e86d3b6999fc441799438d159ffb0b1`。原始映射计数不等，排除实际无连接声明后相等；没有设置假活动。旧crosscheck01失败保留，原R4捕获不重采。
4. DRC06自己的gate14/354816、干净ASIC14、真实CPU恢复/竞争/IRQ-WFI、任务模式时序和面积均已通过，详细哈希见19:22。面积上界1.0990946959mm²，setup+.00010252ns/hold+.00249085ns，220宏。非SDF/物理签核。
5. 性能12层平均30502.333333周期，150MHz折算4917.656573task/s；7000未达到。B相对R4整体吞吐+13.4864%，不能单归因脉动。R4仍4333.2563task/s、布局前71.8126319mW/16.5724388µJ，不能当B功耗。

## 第四次授权清理已完成，不能重复

共享盘19:29只剩约7.95GiB；核对旧、已被替代且无占用的两份波形后，19:39仅删除：

- a2e包`runs/mmio8_source_gate01/mmio8_gate/layer_01.vcd`，30231391361B。
- 5946包`runs/d3_gate07_h0/gate_soc/layer_01.vcd`，31246581717B。

完整包名及原摘要哈希见新`handoff/team/evidence/SERVER_WAVE_CLEANUP_FOURTH_20261112.json`。两者原stage/summary均passed，检查实际绝对路径、非symlink、精确大小、摘要/源码清单/CSV哈希和fuser=1后删除。19:40:26独立确认两文件不存在，所有保留文件hash一致。服务器回执`runs/authorized_cleanup_20261112_fourth.json` SHA：

`0c8310269eee5ba94ef8931082ecfde9ef3048cd3f44e72abee91ab761445df5`

本次61477973078B，四次累计421970827967B。观察free127573950464B，包含其它用户同时的空间变化，不能把全部回升归因本次。**R4、B、厂商库及重建资料都未动。** 先前三次ecf3 MMIO8全12VCD也已清完；所有旧cleanup命令不得重复。

旧`light-light126-d3-reports-arch03-20261109_071327-4c8803e509a0/runs/d3_activity01/gate_soc/layer_01.vcd`没有预期summary，**未删**。首次rglob扫描慢主动取消；后来固定深度查询已结束。仍有更早dma16_gate03波形未逐项清理审核，不能盲删。需要空间时再核证据与占用，不删队友文件，不清锁。

## 下一步与桌面

服务器基础包仍：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`，709输入manifest`39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d`未改。ops16已完整部署，不重传。

本机`takeover_local/b_power_final01_progress.txt`是可重复只读查询。下次先读当前活动stage/state、compile.log或层日志，确认实际编译/捕获进度；按首例宿主时间估算剩余，保留20%。尚无B功耗数值，system_power_verified=false。待queue全部结束后，以同ops的`systolic_b_report.py`绑定最终report_request导出、重核1200及精度，并补R4/B表、独立审计和交付材料。

VNC fresh18874436、**workspace3**、ced空闲shell；最后只读进度查询已执行并读图。**无待Return、无悬挂functions exec、无前台monitor**。FileZilla关闭，FTP421不再重复问用户；workspace4不用。不要因过期relay pid重开开发板网络。

代码/功能/方法证据已云同步f6f704c；本增量、清理回执及启动状态待同步。原有ABI参与固件manifest，不能编辑。当前任务继续，不以“已同步”结束后续工作。
