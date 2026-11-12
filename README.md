# KWT-1 RTL 架构版本与团队交接

换电脑与持续同步：[团队接手入口](handoff/team/README.md)、[修改后的同步流程](handoff/team/SYNC.md)、[Codex提示词](handoff/team/PROMPT.md)。日常开发使用 `workspaces/arch02`，历史版本目录保持不变。迁移工具验收进度见 [STATUS](handoff/team/STATUS.json)。

私人协作仓库，用于保存各阶段架构的 RTL、验证代码、数值协议与设计说明。

## 版本索引

| 阶段 | 版本 | 状态 | 内容 |
|---|---|---|---|
| [架构一：串行 64 项 MAC](architectures/arch01_serial_mac/v1.0.0/ORIGINAL_README.md) | v1.0.0 / 2026-11-06 | 独立 RTL 回归通过 | 点积、偏置、定点转换、握手及复位 |
| [架构一：真实 KWT-1 HEX 验证](architectures/arch01_serial_mac/v1.1.0/README.md) | v1.1.0 / 2026-11-06 | 软件与双仿真器各 12/12 通过 | 真实数据接入、独立定点校验、验证证据 |
| [架构一：全量语音批量验证](architectures/arch01_serial_mac/v1.2.0/README.md) | v1.2.0 / 2026-11-06 | 软件全量与双仿真器分阶段通过 | 1269948 软件任务；每套 RTL 6528 独立任务 |
| [架构一：完整矩阵验证](architectures/arch01_serial_mac/v1.3.0/README.md) | v1.3.0 / 2026-11-06 | 软件及双仿真器全矩阵通过 | 单样本 12 层，各 304128 个独立输出 |
| [架构二：8 路 MAC 与 SRAM](architectures/arch02_matrix/v2.0.0/README.md) | v2.0.0 / 2026-11-08 | VCS 功能与 DC 单角检查通过 | 304128 输出、18 KiB SRAM、服务器交接 |
| [架构三：E203、ICB DMA与脉动B](workspaces/arch03/README.md) | 2026-11-12 验收中 | R4与B各自最终1200通过；B的DRC06门级14、任务模式时序/面积审核和SAIF方法对照通过 | B完整4917.6566task/s、面积上界1.0990947mm²；B活动/功耗和最终报告仍待完成，见[B交付索引](workspaces/arch03/SYSTOLIC_B_DELIVERY_20261112.md) |

架构二已完成单样本 12 层全部 304128 输出的厂商 SRAM 模型功能验证，以及指定 SS 角、6.667 ns 下 DC 综合检查。多角物理实现、功耗、端到端推理和 SoC 尚未验收。

最新版本：[v2.0.0](architectures/arch02_matrix/v2.0.0/README.md)，[修改与验证结果](architectures/arch02_matrix/v2.0.0/CHANGELOG.md)，[服务器交接](architectures/arch02_matrix/v2.0.0/arch02/SERVER_HANDOFF.md)。架构一 v1.0.0–v1.3.0 与旧交接资料完整保留。

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

## VNC 与 FileZilla 操作交接

[队友交接文档](handoff/eda_audit_20261106_01/CODEX_VNC_FILEZILLA_HANDOFF.md)包含操作流程、路径映射、已完成盘点和未确认事项；配套提供[环境盘点报告](handoff/eda_audit_20261106_01/AUDIT_REPORT.txt)、[inventory.sh](handoff/eda_audit_20261106_01/inventory.sh)及[probe.sh](handoff/eda_audit_20261106_01/probe.sh)。这些是 2026-11-06 的交接记录，先阅读已有结果；本次归档未执行脚本或重新盘点服务器。
