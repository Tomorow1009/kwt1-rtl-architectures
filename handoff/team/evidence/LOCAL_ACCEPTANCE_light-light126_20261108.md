# light-light126 本机接手记录

2026-11-08（Asia/Shanghai），成员标识 `light-light126-lenovo`。详细哈希和机器可读结果见 [JSON 记录](LOCAL_ACCEPTANCE_light-light126_20261108.json)。个人工具路径和凭据不入库。

- 从团队私人仓库完整克隆并 fetch，基准为 `bda985eedb4b8d97ec705afabade485b827711de`；个人分支为 `codex/light-light126/arch02-takeover-20261108`。
- 日常目录为 `workspaces/arch02`，历史版本未改动。默认使用 v1.3.0 的 `real_sample_001`，24 个 NPZ 与 Git blob 和原始本地副本全部匹配；未训练或重新提取。
- Python 3.8.20、NumPy 1.19.5、Vivado XSim 2018.3。preflight 的本地依赖检查通过；Icarus 未安装，未运行。桌面就绪状态与本地算术通过分开记录。
- 软件通过 12 层、304128 输出；XSim behavioral/pin_mock 各通过 4 个宏用例，pin_mock 写掩码检查通过。11 个 RTL/TB 文件 SHA256 与历史宏验收一致。
- 既有 portability 失败/防覆盖测试 8 项通过；新增只读检查脚本的篡改检测、运行中阶段拒绝、锁保留和无写入测试 8 项通过。新增工具不改变受测 RTL 或服务器阶段入口。
- 本地结果保留在 `local_runs/software_20261108_131651`、`local_runs/macro_20261108_131651`、`local_runs/preflight.json` 和 `local_runs/data_integrity.json`。

## 已准备的服务器输入

源码来自干净、已提交的 `bda985eedb4b`，不是 development 包。后续本机验收文档和只读核对工具提交不改变该包。

- 文件：`local_runs/light-light126-lenovo-20261108_131929-bda985eedb4b.zip`
- 大小：4517406 字节；manifest 列出 123 个输入文件。
- ZIP SHA256：`3efb36ce1816556e475cfb3eb1e7300f01bc38027e5fa4005ca3c8aaf4517c74`。
- 拟上传至 FileZilla `/IC/light-light126-takeover-20261108/`；尚未上传，不将拟定路径表述为实际运行目录。

## 尚未完成的服务器核对

VNC 已连接，用户确认共享桌面无人操作；当前屏幕可见旧 `acceptance01` 的 `TEAM_FLOW_PASS outputs=304128 physical_signoff=false`。这只是历史终端输出，不替代本轮实物校验。现场锁、实际进程、临时修改、包输入与产物哈希仍待核对；本轮没有启动或终止服务器作业。

当前基准相对 `115c54dc5a05a5e4f242b51b9c8b1824a41b1ce7` 仅增加文档和证据，执行输入无变更。可候选复用 `team_runs/member1/member1-20261108_111917-115c54dc5a05` 的历史验收，当前尚未标记复用成功。

下一步：完成 FileZilla 队伍站点登录；检查服务器协作状态；上传独立输入包及已提交的只读检查脚本，校验传输、ZIP 和解包完整性。按 SERVER.md 核对历史证据和本机目标摘要，匹配时复用，缺失或变化时使用新的 session 重跑对应阶段。现场修改必须回写 Git。SDF、多角、布局布线、功耗、SoC、完整推理及官方精度仍未验证。
