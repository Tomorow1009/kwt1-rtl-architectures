# DMA16 完整波形未知值定位

当前为工具准备，尚未执行真实服务器扫描，不是系统功耗验收。

首层已通过完整活动审计，但有389025条含未知值的记录，12层该计数各异。必须查明对象与时间段，不能用152986精确映射／1 implied证明未知活动没有影响，也不能把未知值或未观测前缀改成零。

新增`activity_unknown.cpp`逐条读取完整VCD；保留全部别名、宽度、所属层级、初始时刻与之后的未知记录数、首次/最后未知记录时间、含任意未知位的持续时间及结束时是否仍未知。持续时间不是未知bit数量或功耗误差估计。CPU/TCM等角色可能重叠，不能相加当系统唯一数目。

`dma16_unknown_activity.py`复用已通过门级/综合/固件/原平台的来源校验，先核对原VCD SHA，完整扫描后再核对SHA和文件状态；声明数、唯一标识数、全部值记录数、未知记录数及各角色计数必须与冻结完整活动审计完全相同。新阶段不修改原VCD、原活动回执或生产RTL，审核标记保持false。

执行时须由`server_run.py`取得共享锁，当前最终1200批次运行期间不得启动。选择新session，先扫描layer_01并审查全部明细，再据对象决定其余层的审核安排：

```text
python3 workspaces/arch03/scripts/server_run.py dma16_unknown_activity --session <新session> --gate-run <a53的dma16_gate03/dma16_gate> --gate-summary-sha256 9ba06d90c32842d1a817ddc2d439964af7b406af10617fca6f7bab43908f24dc --cases layer_01
```

输出`unknown_full_scan.json`保存全部受影响标识；`summary.json`仅保存范围和计数，二者哈希绑定。先按实际路径分组审查，再结合冻结网表、宏片选、有效位和测量阶段解释。不能仅查看前若干对象后宣称全覆盖；剩余11层功耗报告也不能用首层替代。

本地小型波形测试覆盖初始/稍后未知、恢复、重复未知、同拍变化、位向量、别名、缺少初始观测、结束dump排除、窗口/计数篡改、非法格式和来源保留。默认Zig缓存曾AccessDenied，改为项目local_runs缓存后编译成功；出现的是工具自身Windows unwind属性警告。初次Python导入名误用verify_gate，改为已有gate_activity后相关测试通过；这些工具问题未影响服务器任务。
