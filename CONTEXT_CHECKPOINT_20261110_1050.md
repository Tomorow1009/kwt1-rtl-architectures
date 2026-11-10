# 2026-11-10 10:50 实施检查点

继续用户已恢复的三天直接16路DMA计划。压缩后先读AGENTS、根交接、本文件、有效计划及三份状态。开发板已上电、FileZilla允许，私人GitHub同范围后续同步持续授权。不得停在进度汇报；生产fcd、最终批量668保持冻结。

## 本段新完成

- b85工具提交`b85e908fab388f07027b7b4e983d36635651ee1c`已推送且本轮再次ls-remote确认。包`light-light126-x-model-dma16-20261110_102408-b85e908fab38`，16644393B，ZIP SHA=`475375b33f3ed516d6f24b2b21066cc05dbadd0c1e5991fcba038715051e77a9`。679输入/215干净tests/五固件/40生产文件与668一致。clean audit=`local_runs/dma16_x_model_clean_audit_20261110_1026/receipt.json`，SHA=`57d94eab7a7b38ac4a2aa335dbc34fbf9baa53c1365ec5fe131e7466fc9befee`。
- 已经FileZilla33秒上传，success25、空队列后断开最小化。板端暂存`/home/root/undergrad-x-model-20261110`。服务器**10:30:51.445480安全解包，10:38:37.395611核验679输入及完整提交**。不要重复上传。
- bb25 `runs/dma16_mac_use_l01_v2/dma16_mac_use`于**10:38:43.356180 passed**，原driver142991/child143321正常结束并释放共享锁。完整扫描文件18873069B；8.745GB原始VCD前后哈希与原全量计数一致。准确摘要SHA=`7c1bba6b91b7bfb0aa08ddcbe5fc9a9ecb1ae8c0bdc04b5925b4dfd851fcd298`，**10:44:47.489867独立断言通过**。
- 每路1584 starts/101376 feeds/1584 outputs；共1622016 MAC/25344输出，有效采样未知0、不确定控制0、协议违反0，无复位或未完成点积。各路225770时钟边沿，首93683323965tick、末1598809840119tick；lane0 X/W未知采样边沿92691/92694，但不在被接受的数据上，其余端口未知采样0。该结论仅为MAC有效消费证明，不批准整机功耗。
- 原未知计数保持389025（起点29654＋后续359371）、34128未知标识、9576结束未知、614初始未观察。不能把它们删除或按零功耗处理。
- 两次哈希人工抄录错误均由断言拒绝，没有修改原摘要；逐字符定位并纠正27/28位置c/9后最终通过。以后每行8字符、字符间加空格，不打印长列表造成截断。
- 已更新ACCEPTANCE、DELIVERY_INDEX、README、VERIFICATION_MATRIX和创新稿的当前状态：12层来源/设置审核完成；原8路首层门级/PT及数值完成，完整对照仍缺。

## 当前唯一重作业

b85包`runs/dma16_x_frozen_l01_v1/dma16_x_sensitivity`，**driver170842、child171053**。launcher10:42:03.165301、stage10:42:03.773833；10:42:30.795539独立state/owner确认，10:48:39.905505仍running读完整layer_01 VCD。采用同a53波形/fcd网表/库、averaged/0.5/false；这是新诊断入口的原设置复现，尚未看最终结果。不得并发EDA/大扫描或清锁。

最新已发状态/数字查询，截图`takeover_local/d2_20261109/x_frozen_state_numbers.png`待读取；本地exec会话12482可能需先poll完成。若其后收到结果，以最新增量覆盖本段。

## 本地新工具（尚未提交/上传）

新增`dma16_x_compare.py`、`test_dma16_x_compare.py`，8项定向＋32既有检查共40通过。读取4个独立实际诊断和原正式首层PT：严格校验摘要/state/工件、重新解析数值、实际设置、同网表/SDC/至少三库/波形/窗口/固件/布局；frozen复现需与原值逐项完全相同，再给出四点有符号差值与选定设置离散范围。始终保持system_power_verified/physical_error_bound/replaces_frozen_estimate=false。

首个测试把Decimal零写法限定为0E-15而实际0E-20失败，改为数值零断言后40通过；不是功耗数值失败。临时dummy.tmp已经删除，未入库。新比较工具未用于服务器，也不能称四点结果已有。

## 接续顺序与禁止重复

1. 读取frozen实际完成状态。通过后核对原首层实际数值和摘要，再串行zero/one/initial；准备单一停错队列，不重复frozen。
2. 完成比较工具的干净包审计、同范围云同步和上传后，运行四点比较。队列不依赖比较工具，不改正在执行的b85快照。
3. 其余11层MAC完整未知/采样扫描待办；每层可能约23分钟，以实际宿主耗时计划，保留至少20%余量。可使用b85中的同bb25扫描源码。不要再单独重跑旧unknown工具造成双份扫描。
4. 原8路尚需完整14门级/12活动及12层PT、严格约束审核；只有首层新gate/PT/numbers完成。原8路不是8DMA，不复用旧BEGIN窗口或synth07证明新加载。
5. CPU/SRAM/互连/AON未知有效使用及建模判断仍缺；原AON备份寄存器无reset注释不是全量豁免依据。干净服务器复现、最终包及答辩材料仍待办。
6. **不得重复最终1200或full02独立重审**：已1200/30412800/0失败；报告receipt=`06c246af4de0914e1e304fc77cf1b61413e955a350c59d5d8d0df8c521e84e5c`。任务模式150MHz和0.434796781612mm²已绑定；系统功耗/官方精度/物理签核false。FROZEN_REVIEW.md的规范LF哈希绑定不随意修改。

## 操作恢复

服务器base=`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`，包在bundles，锁为父IC/.arch02_team_lock。只经开发板VNC执行服务器命令，只经FileZilla上传，不SSH/下载/隐藏旁路。`F:/linux_fpga_try/ac820.ps1`先刷新windows；本轮VNC18874435/FZ20972102/panel10485764，第3终端空闲。新启动需重查锁与pgrep，先建runs父目录、新目录独占打开launcher，不覆旧失败。

远端命令单物理行<1000字符，本地先检查；长type返回session则poll结束后再操作。不要在functions.wait里填exec session。查询需短输出，避免整个manifest/长JSON遮住实际结果。其余历史路径、准确SHA和既有成果见10:06检查点及三份JSON。
