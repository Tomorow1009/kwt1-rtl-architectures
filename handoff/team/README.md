# 架构二：换电脑接手入口

团队代码：https://github.com/Tomorow1009/kwt1-rtl-architectures （私人）。模型来源：https://github.com/ARM-software/keyword-transformer （公开上游，只读参考，不是上传目标）。

先读 [当前状态](STATUS.json)、[再次同步](SYNC.md)、[通用提示词](PROMPT.md)。已验证历史见 [服务器交接](../../architectures/arch02_matrix/v2.0.0/arch02/SERVER_HANDOFF.md)。

新交接入口已于2026-11-08完成本机干净路径演练及服务器软件/VCS 304128输出、DC综合、hold修复和审计，见[本次验收记录](evidence/SERVER_ACCEPTANCE_20261108.md)。队友首次仍需在自己的电脑完成预检与小规模验证。

## 本地到底需要什么

日常开发位于 `workspaces/arch02`；历史 `architectures/*/v*` 不直接修改。共享 `rtl` 与 `arch02/rtl` 都要保留，不能只拿后者。

| 用途 | 文件/目录 | 依赖 |
|---|---|---|
| 人工向量与宏单测 | 工作区 rtl、arch02/rtl、arch02/tb、scripts/gen_vectors.py、arch02/scripts | Python≥3.8、NumPy、Icarus或Vivado |
| 12层完整矩阵 | 上述文件、v1.3.0的单样本 manifest 和24个 tensors.npz | Python/NumPy；RTL运行另需仿真器 |
| 服务器功能/综合 | local.py生成的完整包、server.py及阶段脚本、显式配置 | 服务器Python3.6标准库、VCS、DC、LC和实际库 |
| 重新提取（本次不做） | 官方kws_streaming完整目录、models_data_v2_12_labels/kwt1中的flags.json、labels.txt、best_weights.index和best_weights.data-00000-of-00001、团队提取脚本及指定语音 | 独立TensorFlow环境 |

现有NPZ校验不需要TensorFlow、训练脚本、KWT2/3权重、全量语音HEX或整个Speech Commands数据集。官方README/requirements.txt/LICENSE.txt用于来源、依赖和许可证。已保存数据的manifest记录实际TF2.4.0、官方请求2.4.0rc1；源码提交号未由Git元数据验证，文件哈希才是已有提取记录的证据。

## 新电脑准备

1. 登录自己的GitHub账号并确认私人仓库访问权，克隆完整仓库，不只下载单个RTL文件。
2. 安装可用的Git、Python/NumPy、Icarus和/或Vivado；保持各自许可证有效。Python调用者就是所选解释器，不用固定D盘。
3. VNC和FileZilla由成员安装、配置站点并登录；不要复制带密码的配置到Git。Codex电脑控制插件/技能须在新机器实际可用；工具存在不等于已登录或可控制。
4. 将config.example.json复制为config.local.json，填写member、需要覆盖的工具bin/桌面应用路径。相对data_root按仓库根解析；默认复用已入库v1.3.0数据。个人配置已被忽略。
5. 在仓库根运行：

```powershell
python handoff/team/local.py preflight --config handoff/team/config.local.json
python handoff/team/local.py macro --config handoff/team/config.local.json
python handoff/team/local.py software --config handoff/team/config.local.json
```

仅有Icarus时对前两条增加 `--simulator iverilog`。预检中的desktop_ready=false不是本地算术失败：桌面控制与登录需由当前会话观察。成功输出与详细结果保存在local_runs；失败返回非零，不将缺工具说成通过。

完整本地矩阵可运行工作区 `arch02/scripts/run.py --mode all --backend pin_mock --simulator both --data-root <单样本目录>`，先用工作区scripts/gen_vectors.py生成向量。这里的data-root是数据目录，不是官方源码目录。

## 上传服务器

先提交受测源码和工具，再运行：

```powershell
python handoff/team/local.py package --config handoff/team/config.local.json
```

产生独立ZIP、SHA256回执及完整包目录。`--development`只用于明确标记未提交状态的开发演练，不作为正式交接结果。包内manifest锁定全部输入，运行中不能改RTL或配置。不要上传个人配置、聊天原文、库、许可证或整个local_runs。

FileZilla `/IC` 对应 `/storage2/2026contest/server4/s4_21usr/Desktop/IC`。上传至独立目录，检查传输成功及字节数，在服务器校验包SHA256并安全解包；不得覆盖同名目录。运行入口及路径见 [服务器流程](SERVER.md)。

没有电脑控制工具时，成员手工完成相同步骤，给Codex提供阶段摘要或截图。不得通过隐藏通道绕过服务器传输限制。

## 结论边界

历史r03为VCS厂商ARM_UD_MODEL功能分支304128输出通过，单SS角DC检查通过；默认厂商时序分支的旧hold失败仍保留。当前工具重跑结果看STATUS和本次运行，不能借历史PASS验收新代码。尚未完成SDF门级、多角、布局布线、功耗、SoC或官方识别精度验收。
