# 新交接入口服务器实测记录

2026-11-08（Asia/Shanghai），通过 FileZilla 上传并在已登录的 VNC Linux 终端执行 `sh t.sh`。本记录来自本次终端实际显示的阶段结果，不引用旧 r03 结果作为验收。

## 输入与运行位置

- 受测源码及工具提交：`115c54dc5a05a5e4f242b51b9c8b1824a41b1ce7`。后续提交仅补充文档和证据，不修改此受测包。
- ZIP：`member1-20261108_111917-115c54dc5a05.zip`，4513941 字节。
- ZIP SHA256：`2a46aa8cf9c61a2a86f0b5bfad93cddb1ccf6ee0867fb6bd713aa039da7f59eb`。
- 本次上传 `t.sh` 2608 字节、`u.sh` 174 字节，三个传输均成功。
- Linux 包根：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/team_runs/member1/member1-20261108_111917-115c54dc5a05`。
- 会话：`team_sessions/acceptance01`；阶段状态和日志留在服务器。

## 实际通过阶段

下表路径相对于上述包根。2026-11-08 12:06 左右读取终端时，作业已结束并返回 shell 提示符。

| 阶段 | 结果 | 本次证据目录 |
|---|---|---|
| 解包完整性 | UNPACK_HASH_PASS，ZIP及123个输入文件校验 | manifest.json |
| 环境预检 | STAGE_PASS preflight | team_sessions/acceptance01 |
| 软件整数校验 | STAGE_PASS software，304128输出 | server_runs/20261108_115715_470102 |
| 宏单测 | STAGE_PASS unit | server_runs/20261108_115722_987957 |
| VCS完整矩阵及定向验证 | STAGE_PASS vcs，304128真实输出 | server_runs/20261108_115727_876924 |
| DC首次综合 | STAGE_PASS synth | dc_runs/synth_20261108_115905 |
| DC hold修复 | STAGE_PASS hold | dc_runs/hold_20261108_120342 |
| 独立审计 | STAGE_PASS audit，重核304128输出和最终DDC | audits/20261108_120417 |

最终终端标记：

```text
TEAM_FLOW_PASS outputs=304128 physical_signoff=false
```

受测入口仅在所有阶段成功、软件/VCS/审计计数为304128、hold结果中max/min裕量非负时打印该标记。审计另检查8个RAMSP128X16、2个RAMSP4096X16、0锁存器和设计检查结果。精确裕量、面积和产物哈希保留在本次服务器JSON及报告中，本记录不将旧r03的数值移植为本次测量值。

## 可复现环境与边界

此次使用既有登录终端环境，直接 `sh t.sh` 成功启动；入口按server_config.json追加EDA工具PATH，无需修改全局.cshrc。厂商模型功能分支ARM_UD_MODEL用于VCS；DC为RVT SS 0.99V、125°C，6.667ns理想时钟及独立模块IO约束。

本机不同路径的干净克隆已通过软件准备、哈希校验及behavioral/pin_mock × Icarus/XSim宏回归；具体证据见clean_local_macro.json。中断防重复启动逻辑通过本地测试验证，本次服务器作业未人为中断。

尚未验证：队友电脑实机接手、厂商时序分支完整矩阵/SDF门级、多工艺角、布局布线后时序、功耗、SoC集成、完整推理及官方精度指标。不把本次成功称为物理签核或识别精度达标。

后续修改必须重新提交、打包并使用新运行目录；本次acceptance01不得原地重跑或覆盖。查看已有运行使用包根下 `python3 server.py status --session acceptance01`，不再次执行t.sh。
