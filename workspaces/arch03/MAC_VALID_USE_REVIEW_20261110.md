# 冻结门级波形的 MAC 有效采样诊断

10:06真实首轮：3dcd包676输入/208干净tests/40生产文件一致核验后上传，09:59:12.167053启动`dma16_mac_use_l01_v1`，09:59:40.385600被`regex_error`拒绝，尚未完成全量扫描。实际g++为GCC4.8.5，其std::regex不兼容；原失败保留且锁正常释放。已本地改严格整数范围解析，增加畸形/超大lane和bit/反向范围拒绝，8tests重新通过；修正尚未打包服务器复验。此前“尚未服务器执行”仅为首版建立时状态，不代表首轮通过。

状态：本地8项定向测试及相关51项检查通过，尚未服务器执行。生产RTL、正式固件、最终1200入口和原始波形保持不变。

实际a53门级波形头已只读核对：MAC位于`tb_top.u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems.u_arch03_accel.core.lanes[n].mac`。向量端口在真实波形中按位声明，工具同时支持完整降序向量和逐位声明；每lane必须有完整的14个端口，缺位、重复位或错误宽度直接拒绝。声明清单保存在e777包`runs/mac_header_v1.json`，仅为声明诊断，不是功能通过结果。

新增独立`activity_mac_use.cpp`，沿用完整流未知定位算法，原`activity_unknown.cpp`不修改。完整扫描仍核对原始声明数、唯一标识、所有活动/未知记录、六组件计数、窗口及VCD前后SHA；新增诊断以每个时间戳开始前的稳定值，审核该时刻观察到的时钟上升沿，避免使用沿后NBA变化代替真正被消费的数据。

- start_valid与start_ready同时为1时检查40位bias和shift已知。
- in_valid与in_ready同时为1时检查x和w已知，逐点积要求64次接受。
- out_valid与out_ready同时为1时检查result和saturated已知。
- 三值握手判定保留0屏蔽未知的逻辑；无法确定是否发生握手时明确失败。
- 每lane要求1584次启动、101376次MAC接受和1584次输出，全16lane共1622016 MAC/25344输出；要求无复位、未完成点积或协议违反。
- 检查时钟边沿间隔、首尾覆盖及16lane一致，保留每端口未知边沿数、首末有效输入时刻和首个违反位置。

入口复用服务器合作锁，必须在当前重任务自然结束后排队：

```text
python3 workspaces/arch03/scripts/server_run.py dma16_mac_use --session <全新会话> --gate-run <a53的runs/dma16_gate03/dma16_gate> --gate-summary-sha256 9ba06d90c32842d1a817ddc2d439964af7b406af10617fca6f7bab43908f24dc --cases layer_01
```

通过只表示MAC接受的控制与数据已知、完整记录与冻结波形一致。不能据此忽略空闲组合逻辑的未知传播，也不能代替CPU、SRAM、互连等未知对象审核或X建模敏感性分析。结果始终保留`system_power_verified=false`。

测试覆盖真实拆位格式、多个lane共用VCD标识、空闲未知、沿后未知与沿前未知区别、握手不确定/被0屏蔽、缺位/重复/越界、同时间戳时钟毛刺、截断、错误操作计数、时钟间隔与冻结全量计数不一致，以及阶段执行后波形不变。合成波形测试不是实际硬件验收。
