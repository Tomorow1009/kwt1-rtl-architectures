# N1 进程回收与锁修复独立复核

2026-11-13，仅阅读实现、21项进程测试源码、补充runtime路径集成fixture和相关运行/打包入口，没有重复执行测试、启动服务器作业或修改被审文件。结论：以下冻结身份未发现阻断部署的问题。

| 文件 | 受审SHA-256 |
|---|---|
| n1_process.py | `69c0b9396449fde7048e88ec5c58d36770422c9fb24871728988eb8d429eed93` |
| n1_server.py，初审本机CRLF历史身份 | `b293ee89e5232d9eb5dd8de27e7bcd701914596ab7868563f8aa7d0c372be394` |
| n1_server.py，最终实际LF身份 | `1367c37b18cbb3041be5efef8d86e06eab6075768cfa65f9b35c38551a6877bb` |
| test_n1_process.py | `96165c785c87bf828f0b668999c6a46c116d9e08fe2f45f05787b2e4f9ed6fb3` |
| test_n1_paths.py，新增依赖的集成fixture | `92a8695018ccfa03976d6d6f3792ec614dc83beefdf95e45a2d1808fea514588` |

LF摘要最初由本机实际源码仅替换CRLF为LF后计算，随后作者已将server实际文件统一LF并经独立读取确认；process/test原文件已为LF。部署包最终仍须按其实际manifest逐项核验，不靠上述摘要代替包身份检查。

## 故障与修复范围

原 `server_run.call` 在Popen后改写共享owner.json，ENOSPC可使其在wait前抛错，留下已启动子进程。新N1入口将调用统一交给ProcessLedger，不修改共享旧runner或生产RTL9305。

- 仍在原 `server_root/.arch02_team_lock` 执行mkdir互斥；owner.json仅首次以xb创建一次，不再对共享盘反复写owner.tmp。owner包含token、原bundle/session及私有ledger路径。
- 初始owner写失败，只清理确定属于本次且仍为空的锁目录。部分owner和未知文件保留；已有锁不接管。释放前两次核锁目录/owner文件inode、完整owner字节和成员集合，外来owner或替换目录不被删除。
- 每次Popen前先写独立private prepared回执，再核原锁身份；准备写入失败时不启动子进程。
- Popen成功返回后记录ACTIVE_CHILD，后续PID记录、输出、KeyboardInterrupt/SystemExit或等待中断均先drain。确认wait/poll终态后才清ACTIVE_CHILD，随后报错；不会因私有回执ENOSPC把已接受子进程遗弃。
- 持久wait故障继续保留锁与active状态，不假定退出。Popen失败、非零退出和fatal日志均进入失败回执。
- 新增收尾覆盖日志close异常：子进程已回收后将close异常加入errors，仍尝试写失败终态。初审指出的“close失败可能跳过终态记录”边界已修正。
- N1入口显式核新依赖的导入路径与本包manifest SHA；所有阶段使用processes.call。package_n1会导出已提交的新工具，旧9305硬件/综合输入无需改动。新的工具版本不能覆盖旧运行包或旧失败回执。

## 验证与边界

作者报告21项真实小子进程和故障注入检查通过；补全已有runtime fixture后，进程与路径工具联合32项通过。独立阅读覆盖了共享初始写入失败、部分owner、私有准备/PID/持续写入失败、Popen失败、子进程失败、owner替换、等待中断、SystemExit、日志close故障，以及三个实际n1_server.main集成分支。本代理未重复运行。

runtime fixture实际复制n1_process.py、登记其manifest摘要，并将导入路径指向该副本，同时核对原共享锁和私有child_ledger位置；没有放宽生产依赖守卫。旧fixture因缺少新依赖失败的记录保留，不能将其误标为硬件失败或删除后声称一直通过。

这是进程管理修复，不是新的ASIC功能、1200任务或PPA证明。强制SIGKILL、解释器崩溃或不执行Python清理的外部终止仍需依据原锁、ledger和实际进程人工恢复；不能把新工具用于自动接管或释放此前已遗留的旧作业。新完整运行必须使用新包、全新session，先确认原作业/锁终态。
