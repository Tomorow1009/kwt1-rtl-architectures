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
- 已上传至 FileZilla `/IC/light-light126-takeover-20261108/`，传输与落盘核对结果见下文。

## 服务器现场只读核对与证据复用

2026-11-08 13:47–13:56（Asia/Shanghai），在用户确认无人操作的 VNC 终端，通过只读命令和 Python 标准库读取、重算哈希。没有运行新 EDA 作业，没有修改服务器文件，也没有直接执行尚未上传的 inspect_existing.py；以下是现场逐项核对结果。

- 当前账号进程名称过滤 python/vcs/simv/dc_shell/lc_shell/verdi 无匹配；IC 根目录不存在 `.arch02_team_lock`。这是检查时刻的状态，新作业前仍需重新协调。
- 实际包根：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/team_runs/member1/member1-20261108_111917-115c54dc5a05`。123 个 manifest 输入全部重算匹配；本受测包的受管输入没有临时修改，不据此推断其他目录没有修改。
- 原始数据清单、源码/向量、运行 HEX 的三组规范摘要以及 server_config.json SHA256 均与本地 JSON 记录一致；全部 14 组 layout shift 正确。当前基准相对受测提交仅改变文档/证据，执行输入无变更。
- `team_sessions/acceptance01/state.json` 关联 manifest 一致，preflight/software/unit/vcs/synth/hold/audit 全部 passed；除无子进程退出码的 preflight 外，各阶段 exit_code=0。software/unit/vcs/audit 的已记录 summary 哈希均匹配。
- 软件摘要实际为 passed、304128 输出。VCS 摘要实际为 passed、functional、304128 输出，22 个 job 全部通过；manifest、11 个源码（含实际厂商模型）、14 组 CSV 捕获及 rounding 第二次捕获哈希全部匹配。
- 审计实际为 passed，重核 304128 输出；8 个 RAMSP128X16、2 个 RAMSP4096X16、0 锁存器。最终网表、DDC、SDC、VCS 摘要四个产物哈希匹配。max/min slack 分别为 0.000641823 / 0.00111431 ns，仍仅为文档所述单 SS 角理想时钟检查，physical_signoff=false。

据此复用上述 acceptance01 的历史软件、宏单测、VCS、DC synth/hold 和 audit 证据，不重复启动。各实际运行目录见同目录 SERVER_ACCEPTANCE_20261108.md；这是历史结果完整性复核，不标记为本轮重新执行。

## 独立上传、落盘校验与同步完成

2026-11-08 15:06 再次核对当前账号相关进程和 IC 协作锁，均未发现。FileZilla 客户端恢复启动并由用户完成站点登录后，新建上述独立目录；5 个文件均上传成功，ZIP 为 4517406 字节。最初的 FTP 421 并发连接错误通过串行传输和释放本机浏览连接解决，没有终止队友连接或作业。

Linux 独立目录为 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-takeover-20261108`。ZIP 与 unpack.py、inspect_existing.py 的 SHA256 均与本机回执一致。安全解包输出 UNPACK_HASH_PASS，新副本位于该目录的 `bundles/light-light126-lenovo-20261108_131929-bda985eedb4b`；不存在原地覆盖。

15:14–15:16 运行已提交的只读检查器，历史 acceptance01 返回 existing_evidence_integrity_passed。再次重算新副本全部 123 个落盘输入，比较原始数据、源码/向量、运行 HEX、配置的规范摘要，全部与已验收包相同，输出 `SYNC_INPUT_PASS bda985eedb4b8d97ec705afabade485b827711de 123 existing_evidence_integrity_passed`。

服务器个人目录新增 `reuse_receipt_20261108.json`，以独占新建方式写入。其本地归档为 [SERVER_REUSE_light-light126_20261108.json](SERVER_REUSE_light-light126_20261108.json)，SHA256 为 `89b33070dd474e1600f08ae0908a9f03c60e7ffdb5266ffb75461442029da452`。下载回执时 FTP 浏览重连再次被限流，因此本地副本按现场可见字段重建，并以服务器原文件 SHA256 核实逐字节一致；不将其描述为成功下载。

当前运行输入的本地版本、独立服务器副本、历史验证记录已建立对应关系，接手同步完成。后续 Git 提交仅补充本机接手工具和证据，不改变 bda985e 输入包；GitHub 文档更新不视为服务器自动部署。未进行新软件/VCS/DC作业；历史包保持只读，没有服务器临时源码修复需要回写。只有个人目录新增上传、解包和复用记录。

Icarus 本机未安装，SDF、多角、布局布线、功耗、SoC、完整推理及官方精度仍未验证。后续改变执行输入时必须重新提交、打包并在新目录执行对应阶段。
