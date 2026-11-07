# 架构二 v2.0.0：8 路 MAC、SRAM 宏适配与服务器验证

发布日期：2026-11-08。基于架构一 v1.3.0 数值核心，首次发布架构二版本；接口改为矩阵任务、16 位加载流及带行列坐标的输出，因此使用 v2.0.0。旧版目录保留。

- [修改与验证结果](CHANGELOG.md)
- [服务器交接文档](arch02/SERVER_HANDOFF.md)：实际路径、运行编号、约束、告警和后续边界。
- [架构与本地仿真](arch02/README.md)、[SRAM 适配](arch02/SRAM_ADAPTER.md)
- [服务器观察摘要](evidence/server_observed_summary.json)、[本地宏单测结果](evidence/local_adapter/summary.json)

## 内容与复现

保留原 Fast_coding 相对布局：共享 rtl/、scripts/ 和 arch02/。核心代码与本次服务器验证后的本地文件逐字节一致，文件哈希见 SOURCE_MANIFEST.json。arch02 文档中的旧路径和“未上传 GitHub”是当时验证记录；本次发布动作由本文记录。

先在本版本目录执行 `python scripts/gen_vectors.py` 生成 1103 组人工向量。完整 NPZ 是外部输入，默认放在 `KWT1/model_data/outputs/real_sample_001`，也可指定路径：

```powershell
python arch02/scripts/run.py --mode software --data-root D:/IC_compeyition/Fast_coding/KWT1/model_data/outputs/real_sample_001
python arch02/scripts/run.py --mode all --backend pin_mock --simulator both --data-root D:/IC_compeyition/Fast_coding/KWT1/model_data/outputs/real_sample_001
```

服务器已验证快照位于 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/arch02_server_r03`；在该目录执行交接文档里的 VCS 命令。仓库提供相同 runner 为 `vcs_run.py`，但运行前必须具备 `validated_data/`、`vectors/`、哈希 `manifest.json`、显式 `vendor_config.json` 与 `vendor.f`。这些输入在已验证服务器快照中保留，不可仅复制 RTL 后声称复现完成。

本仓库未打包厂商 SRAM/工艺库、完整模型 NPZ/HEX、波形、DDC 或完整服务器日志；它们留在授权服务器/已有模型资料中。`arch02/server_delivery` 是本次实际运行的历史脚本，包括失败诊断与固定基线路径，不是任意机器的一键安装器；a0 依赖既有 r02，d/f/g 依赖交接文档所列基线，勿盲目重复运行。若迁移到新目录，先按脚本核对路径、数据清单和实际库版本。

服务器报告通过 VNC 阅读后整理；evidence/server_observed_summary.json 不是下载的原始日志。本次发布只校验打包源码与已验证来源一致，没有重新跑一遍完整 VCS/DC。
