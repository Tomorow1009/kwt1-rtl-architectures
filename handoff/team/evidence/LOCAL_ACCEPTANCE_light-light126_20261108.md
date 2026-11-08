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

## 服务器现场只读核对与证据复用

2026-11-08 13:47–13:56（Asia/Shanghai），在用户确认无人操作的 VNC 终端，通过只读命令和 Python 标准库读取、重算哈希。没有运行新 EDA 作业，没有修改服务器文件，也没有直接执行尚未上传的 inspect_existing.py；以下是现场逐项核对结果。

- 当前账号进程名称过滤 python/vcs/simv/dc_shell/lc_shell/verdi 无匹配；IC 根目录不存在 `.arch02_team_lock`。这是检查时刻的状态，新作业前仍需重新协调。
- 实际包根：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/team_runs/member1/member1-20261108_111917-115c54dc5a05`。123 个 manifest 输入全部重算匹配；本受测包的受管输入没有临时修改，不据此推断其他目录没有修改。
- 原始数据清单、源码/向量、运行 HEX 的三组规范摘要以及 server_config.json SHA256 均与本地 JSON 记录一致；全部 14 组 layout shift 正确。当前基准相对受测提交仅改变文档/证据，执行输入无变更。
- `team_sessions/acceptance01/state.json` 关联 manifest 一致，preflight/software/unit/vcs/synth/hold/audit 全部 passed；除无子进程退出码的 preflight 外，各阶段 exit_code=0。software/unit/vcs/audit 的已记录 summary 哈希均匹配。
- 软件摘要实际为 passed、304128 输出。VCS 摘要实际为 passed、functional、304128 输出，22 个 job 全部通过；manifest、11 个源码（含实际厂商模型）、14 组 CSV 捕获及 rounding 第二次捕获哈希全部匹配。
- 审计实际为 passed，重核 304128 输出；8 个 RAMSP128X16、2 个 RAMSP4096X16、0 锁存器。最终网表、DDC、SDC、VCS 摘要四个产物哈希匹配。max/min slack 分别为 0.000641823 / 0.00111431 ns，仍仅为文档所述单 SS 角理想时钟检查，physical_signoff=false。

据此复用上述 acceptance01 的历史软件、宏单测、VCS、DC synth/hold 和 audit 证据，不重复启动。各实际运行目录见同目录 SERVER_ACCEPTANCE_20261108.md；这是历史结果完整性复核，不标记为本轮重新执行。

## 未完成的传输

独立包尚未上传；FileZilla 官方客户端已准备，但队伍站点尚未连接，凭据仅由用户在客户端输入。下一步连接后上传上述 ZIP、已提交的 unpack.py/inspect_existing.py 至个人目录，核对传输 SHA256 并安全解包，再核对新副本与已复用证据的输入对应关系。在此之前不宣布整个接手同步完成。SDF、多角、布局布线、功耗、SoC、完整推理及官方精度仍未验证。
