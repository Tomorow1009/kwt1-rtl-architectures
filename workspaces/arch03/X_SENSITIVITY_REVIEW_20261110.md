# 完整任务窗口的 X 建模敏感性诊断

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
