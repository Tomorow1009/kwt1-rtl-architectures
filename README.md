# KWT-1 RTL 架构版本与团队交接

私人协作仓库，用于保存各阶段架构的 RTL、验证代码、数值协议与设计说明。

## 版本索引

| 阶段 | 版本 | 状态 | 内容 |
|---|---|---|---|
| [架构一：串行 64 项 MAC](architectures/arch01_serial_mac/v1.0.0/ORIGINAL_README.md) | v1.0.0 / 2026-11-06 | 独立 RTL 回归通过 | 点积、偏置、定点转换、握手及复位 |
| [架构一：真实 KWT-1 HEX 验证](architectures/arch01_serial_mac/v1.1.0/README.md) | v1.1.0 / 2026-11-06 | 软件与双仿真器各 12/12 通过 | 真实数据接入、独立定点校验、验证证据 |
| [架构一：全量语音批量验证](architectures/arch01_serial_mac/v1.2.0/README.md) | v1.2.0 / 2026-11-06 | 软件全量与双仿真器分阶段通过 | 1269948 软件任务；每套 RTL 6528 独立任务 |
| [架构一：完整矩阵验证](architectures/arch01_serial_mac/v1.3.0/README.md) | v1.3.0 / 2026-11-06 | 软件及双仿真器全矩阵通过 | 单样本 12 层，各 304128 个独立输出 |
| 架构二：矩阵加速器 | 待实现 | 规划 | 缓存、地址生成、多通道、参数加载 |
| SoC 集成 | 待实现 | 规划 | E203、总线、驱动、内存映射 |

当前已用架构一逐点验证单样本 12 层完整第一线性层矩阵；矩阵硬件、端到端量化推理、SoC、综合及时序收敛尚未完成。

最新版本：[v1.3.0](architectures/arch01_serial_mac/v1.3.0/README.md)，[与 v1.2.0 的区别](architectures/arch01_serial_mac/v1.3.0/CHANGELOG.md)。旧版目录完整保留。

## 从这里开始

1. 阅读 [团队交接流程](docs/HANDOFF.md) 和 [版本管理约定](docs/VERSIONING.md)。
2. 阅读 [架构一设计与仿真说明](architectures/arch01_serial_mac/v1.0.0/ORIGINAL_README.md)。
3. 提取模型数据前阅读 [HEX 格式交接说明](architectures/arch01_serial_mac/v1.0.0/README.md)。
4. 历史回归证据见 [验证记录](architectures/arch01_serial_mac/v1.0.0/ORIGINAL_VERIFICATION.md)。

```powershell
git clone https://github.com/Tomorow1009/kwt1-rtl-architectures.git
cd kwt1-rtl-architectures/architectures/arch01_serial_mac/v1.0.0
python scripts/gen_vectors.py
./scripts/run_iverilog.ps1
# 已安装 Vivado 时
./scripts/run_xsim.ps1
# 单点积人工 HEX 样例
./scripts/run_single.ps1 -Simulator xsim
```

每个版本目录自包含代码、测试和说明。完整回归向量由固定种子生成；小型单任务样例直接随仓库提供。波形/仿真工程可本地重建。文档内旧 D: 路径仅代表最初开发环境，脚本按自身位置定位。

仓库不保存原始语音数据集、预训练模型大文件、完整波形或本机安装目录。相关来源、版本和校验值应写入对应版本的资料说明，所需小型输入样例可放在 examples。

私人仓库成员需由仓库所有者逐一邀请；仓库链接本身不授予访问权限。
