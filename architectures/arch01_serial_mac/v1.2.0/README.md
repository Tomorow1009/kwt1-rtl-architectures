# 架构一 v1.2.0：全量语音 HEX 批量验证

本版本发布于 2026-11-06。保留 v1.0.0、v1.1.0 原目录；版本以目录管理，本次不创建 Git tag 或 GitHub Release。

计算仍为每条语音在 12 层各取 Y[0,0] 的 64 项 XW+b，不是卷积、完整矩阵或 SoC。RTL 与 v1.1.0 逐字节一致。新增流式批量 testbench、软件全量检查、分阶段仿真入口和故障检测。

- [与 v1.1.0 的区别](CHANGELOG.md)
- [批量数据格式、协议检查与波形操作](BATCH_KWT1.md)
- [本机验收结果](BATCH_KWT1_VERIFICATION.md)
- [硬件设计与原人工回归说明](ORIGINAL_README.md)
- [证据与源码清单](evidence/README.md)

## 已完成验证

| 范围 | 结果 |
|---|---|
| 软件全量 | 105829 条语音、208 分片、1269948 点积全部通过 |
| Icarus / XSim（每套） | 432 抽样 + 6144 完整分片执行通过，重叠 48，独立任务 6528 |
| 兼容回归 | 原单样本 12 任务与原 1103 组向量，两套仿真器均通过 |
| 错误检出 | 软件 7 类、Icarus TB 8 类拒绝，另 1 个正常对照通过 |

未执行全量 RTL 仿真。双仿真器验证同一组数据，不能把独立覆盖相加。误差统计仅描述选定坐标，不能证明完整矩阵精度或分类准确率。

## 从仓库运行

需要 Python/NumPy、Icarus 和/或 Vivado（本机验证版本 2018.3）。在本版本目录打开 PowerShell：

```powershell
# 全量 HEX/NPZ/samples.csv/manifest.json 位于外部目录，不随 Git 上传
$dataRoot = 'D:\IC_compeyition\Fast_coding\KWT1\model_data\outputs\all_speech_dot00'
python .\scripts\verify_batch_hex.py $dataRoot
.\scripts\run_batch_kwt1.ps1 -DataRoot $dataRoot -Mode staged -Simulator both
# 工具不在 PATH 时添加 -VivadoBin '实际安装目录\bin' / -IcarusBin '实际安装目录\bin'
# 仅软件并保存报告
.\scripts\run_batch_kwt1.ps1 -DataRoot $dataRoot -Mode software
# 将来运行全量 RTL（本次未运行）
# .\scripts\run_batch_kwt1.ps1 -DataRoot $dataRoot -Mode all -Simulator both
# 故障注入，仅修改新建的临时副本；替换实际运行编号
# python .\scripts\test_batch_failures.py .\sim\batch_kwt1\<运行编号> --data-root $dataRoot

# 旧单样本使用仓库保留的 v1.1.0 数据
.\scripts\run_real_kwt1.ps1 -DataRoot ..\v1.1.0\KWT1\model_data\outputs\real_sample_001 -Simulator both
python .\scripts\gen_vectors.py
.\scripts\run_iverilog.ps1
.\scripts\run_xsim.ps1
```

也可将完整数据放到本版本的 `KWT1/model_data/outputs/all_speech_dot00`，使用默认路径。约 855 MB HEX、浮点 NPZ 和原语音不纳入本次 Git 上传；请从已有资料包单独交接。数据身份及逐分片哈希见 `evidence/software.json`。

每次重跑生成本版本下 `sim/batch_kwt1/<运行编号>`；代表性波形由脚本重建。其他文档的原 D: 路径代表开发环境，外部数据运行请以此页显式 `-DataRoot` 命令为准。历史单样本文档仅为兼容背景；本次批量结果以批量验收报告为准。
