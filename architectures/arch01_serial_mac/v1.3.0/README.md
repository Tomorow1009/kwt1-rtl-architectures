# 架构一 v1.3.0：12 层完整矩阵验证

基于 v1.2.0，使用一个语音样本的完整 NPZ，复用串行 64 项 MAC 计算每层 99×256 输出。12 层共 304128 个独立输出，软件、Icarus、Vivado XSim 2018.3 全部逐项通过。RTL、数值尺度及握手协议保持不变。

- [与 v1.2.0 的区别](CHANGELOG.md)
- [完整数据格式、运行与波形说明](FULL_MATRIX_KWT1.md)
- [逐层验收结果](FULL_MATRIX_KWT1_VERIFICATION.md)
- [原架构硬件说明](../v1.0.0/ORIGINAL_README.md)
- [运行证据与发布校验值](evidence/README.md)

## 从仓库运行

本目录包含原小型完整 NPZ 和 manifest；默认入口可直接定位。需要 Python/NumPy，以及 Icarus 和/或 Vivado。先进入本版本目录：

```powershell
# 软件全矩阵检查，输出报告
.\scripts\run_full_matrix_kwt1.ps1 -Mode software
# 12 层、两套仿真器全部输出及代表波形
.\scripts\run_full_matrix_kwt1.ps1
# 指定一层
.\scripts\run_full_matrix_kwt1.ps1 -Mode layer -Layer 1 -Simulator both
# 工具不在 PATH 时指定实际安装目录
# .\scripts\run_full_matrix_kwt1.ps1 -VivadoBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'
# 原单样本及人工回归
.\scripts\run_real_kwt1.ps1 -Simulator both
python .\scripts\gen_vectors.py
.\scripts\run_iverilog.ps1
.\scripts\run_xsim.ps1
# v1.2.0 抽样兼容回归需要外部全量语音资料包
# .\scripts\run_batch_kwt1.ps1 -Mode smoke -Simulator both -DataRoot '<all_speech_dot00实际路径>'
```

每轮输出到本版本下 `sim/full_matrix_kwt1/<运行编号>`。故障检测命令为 `python scripts/test_full_matrix_failures.py <运行目录>`，只在新的临时副本中修改数据。其他文档中的原 D: 路径代表最初开发环境；在仓库运行时以本页说明和脚本输出目录为准。

## 验证边界

软件以及每套仿真器分别覆盖 304128 个独立输出。每套额外 3096 次波形执行与主作业重叠，总执行数 307224，不能增加独立覆盖。原 1103 组向量、12 个真实任务、432 个抽样任务双工具回归均通过；9 个错误案例正确拒绝，2 个正常对照通过。

每层使用原浮点模型独立捕获的输入，并非将上一层量化结果串接到下一层；不是端到端分类精度、SoC 或综合时序验收。v1.2.0 的多语音选定坐标覆盖与本版本单语音完整矩阵覆盖互补。

本次按版本目录发布，保留 v1.0.0/v1.1.0/v1.2.0，不创建 Git tag 或 GitHub Release。生成的大型展开 HEX、波形、仿真编译产物和负例临时数据不入库；随仓库提供原 NPZ、实际 CSV/NPZ 输出与文本证据，可重建全部验证输入。
