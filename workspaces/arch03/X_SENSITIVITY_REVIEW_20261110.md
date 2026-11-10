# 完整任务窗口的 X 建模敏感性诊断

**11:12实际进展：** b85 frozen复现10:52:11.278534完成，SHA=`68dc61ee3b9b82de2c941696bb00604493419b6b25026b2aba4df0414f86352f`已独立确认；与原27bf正式报告的总数、分组、模块、SRAM、边界及能耗六字段完全相同。a745比较工具681输入/223干净tests核验、已上传并在11:04:06.754693成功实际重读两类报告，五个网表/SDC/库身份和完整窗口/活动一致。当前b85 `dma16_x_queue_remaining_v1` parent188919串行zero/one/initial；zero已于11:09:28.639448 passed，其总功耗0.0296837185W和能耗0.0000446779497038379161700J与默认相同。one/initial及完整四点比较尚未读到完成，不能据zero一项称未知活动没有影响。

**10:50更新：** b85包215干净tests/679服务器输入及40生产文件不变核验通过。原设置复现`dma16_x_frozen_l01_v1`10:42:03.773833启动，driver170842/child171053，最后10:48:39仍读全窗口VCD；zero/one/initial尚未启动。新增比较工具`dma16_x_compare.py`及8项tests，连同既有32项共40通过，尚未提交/服务器执行。比较严格绑定4独立目录和原正式首层报告，逐工件重核并要求frozen完全复现原值，不自动批准功耗。以下“尚未打包”是首版准备历史。

状态：本地7项工具测试、连同来源/数值检查共32项通过，尚未打包或在服务器执行。当前MAC完整波形扫描仍占共享锁，不能同时启动PT。

依据已经读取的服务器安装版PrimeTime T-2022.03-SP5-1手册，`power_x_transition_derate_factor`控制X跃迁的功耗比例，`power_include_initial_x_transitions`控制首次X到0/1是否计入。冻结报告实际为averaged、0.5、false。敏感性使用以下独立点：

| 点 | X跃迁系数 | 计入初始X跃迁 |
|---|---:|---|
| zero | 0 | false |
| frozen | 0.5 | false |
| one | 1 | false |
| initial | 0.5 | true |

每点在全新PT进程和新运行目录执行，同一冻结gate摘要、同一完整VCD、网表、SDC、库、工艺角、时钟和负载。两个设置均在read_vcd之前明确指定，并从实际工具回读；所有工具错误、报告单位、数值合计、模块、162宏、来源表、before/after未标注清单及输入SHA均重新校核。保留完整报告、未知计数和告警，不修改波形、不强制未知为0。

```text
python3 workspaces/arch03/scripts/server_run.py dma16_x_sensitivity --session <新的会话名> --gate-run <a53的runs/dma16_gate03/dma16_gate> --gate-summary-sha256 9ba06d90c32842d1a817ddc2d439964af7b406af10617fca6f7bab43908f24dc --cases layer_01 --x-point <zero|frozen|one|initial>
```

阶段使用现有合作锁。`--x-point`只允许该诊断阶段使用，原正式功耗阶段不接受这个参数。诊断范围、摘要状态和数值schema独立于正式功耗，不能加入既有full02默认设置汇总。冻结点重复运行还需与原首层结果核对，差异应解释，不能直接选择较小的数字。

后续报告应给出各点的内部/切换/泄漏/总功耗、边界网络口径和完整窗口J/task，保留设置、波形、网表和库身份。该试验只能说明选定PT X模型设置的敏感性，**不是所有真实上电状态的上下界或物理绝对误差界**，也不能代替MAC有效消费、CPU/SRAM/互连未知状态与活动覆盖审核。工具始终保持system_power_verified=false、physical_error_bound=false和replaces_frozen_estimate=false。
