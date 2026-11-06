# 架构一 v1.1.0：真实 KWT-1 HEX 验证

发布日期：2026-11-06。基于 [v1.0.0](../v1.0.0/ORIGINAL_README.md)，旧版完整保留。

本版本新增真实模型数据接入和可复现验证，**没有改变硬件运算、数值格式或握手接口**。详细比较见 [CHANGELOG](CHANGELOG.md)。

## 快速运行

先克隆私人仓库，再进入本版本目录。需要 Python + NumPy；RTL 仿真需要 Icarus 和/或 Vivado。运行已有数据不需要 TensorFlow、原始音频或 checkpoint。

```powershell
cd architectures/arch01_serial_mac/v1.1.0
python scripts/verify_real_hex.py
./scripts/run_real_kwt1.ps1
# 只运行 Vivado
./scripts/run_real_kwt1.ps1 -Simulator xsim
# 未加入 PATH 时指定安装目录
./scripts/run_real_kwt1.ps1 -Simulator xsim -VivadoBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'

# 原人工回归：先生成确定性向量
python scripts/gen_vectors.py
./scripts/run_iverilog.ps1
./scripts/run_xsim.ps1
```

真实数据位于 `KWT1/model_data/outputs/real_sample_001`，已包含 manifest、84 个 HEX 及验证所需的 float/integer NPZ。完整 NPZ 用于对照，RTL 本轮只执行每层的 Y[0,0]，共 12 个独立点积。没有逐元素仿真全部矩阵。

每次运行的报告、日志和波形写到本版本 `sim/real_kwt1/<运行编号>/`。数据与旧证据不被覆盖。波形重建后按 [操作说明](REAL_KWT1.md) 打开 WDB/WCFG；文档中的原 D: 盘路径需替换为自己的克隆位置。

## 验证结果

| 项目 | 本机实际结果 |
|---|---|
| 软件：HEX、整数 NPZ、浮点量化复核 | 12/12 PASS |
| Icarus / Vivado 2018.3 XSim | 各 12/12 PASS，三项整数结果完全一致 |
| 原人工/随机回归 | 两套仿真器均通过 1103 组向量 |
| 缺文件、行数、答案、padding、格式异常 | 5/5 正确检出 |
| 数据与硬件 | 84 个 HEX 校验一致，RTL 与上一版本相同 |

逐层数值见 [验证记录](REAL_KWT1_VERIFICATION.md)，原始文本证据保存在 [evidence](evidence)。证据来自原开发机的运行 `20261106_170636_29021d7b`，其中绝对路径不代表队友机器路径。

## 文档导航

- [架构与接口](ARCHITECTURE.md)
- [版本差异](CHANGELOG.md)
- [真实数据验证及软件参考](REAL_KWT1.md)
- [本机结果与证据](REAL_KWT1_VERIFICATION.md)

尚未进行真实数据的全矩阵 RTL 验证、SoC 集成、综合/时序验收或完整数据集分类精度验收。仓库中的版本号表示交接目录，本次不创建 GitHub Release 或 Git tag。
