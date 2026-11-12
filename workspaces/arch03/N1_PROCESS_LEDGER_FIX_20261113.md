# N1运行可靠性修复：私有子进程记录与异常排空

本次只修N1运行工具，不改RTL、数值格式、数据集、库、硬件时序约束或验收要求。
原9305生产受测包与旧批次证据保留；新工具须冻结到独立OPS包后再部署。

## 问题与修复

原`server_run.common.call`先Popen，再把child_pid/log写回共享盘的owner.tmp。共享盘写满时，
这一步可能抛错而跳过wait，使已接受子进程继续运行且驱动结束。本轮不修改server_run.py，
避免改变旧B0/R4入口；N1启动器改用独立`n1_process.ProcessLedger`。

唯一互斥仍是原共享`.arch02_team_lock`。owner.json仅在首次取得新锁时独占写入一次，包含
driver PID、host、bundle、session、随机token和私有process_ledger路径。后续每个子进程
各写自己的`child_NNNNNN.json`，不会反复更新共享owner，也不会每次重写1200条历史。

先成功写入私有prepared记录，再核共享锁目录inode及owner文件inode/完整原始字节，才允许
Popen。启动后PID记录、print、KeyboardInterrupt、SystemExit或等待中断出现异常，都先
等待该已接受子进程结束。等待期间保留common.ACTIVE_CHILD；确认回收后再清除并报告失败。
日志close异常也纳入失败终态，不把子进程exit 0误记为整个调用成功。

释放锁需再次确认完整身份和目录中只有owner.json；同PID、同host或简单布尔标记不足以证明
归属。初始owner写入失败时，只允许移除本进程刚创建且身份未变的空锁目录；partial owner
或未知成员均保留人工恢复，不形成通用自动清锁机制。

N1入口显式要求n1_process.py列入当前冻结manifest、SHA一致且实际导入路径位于当前包。
新工具不能通过沿用不含该依赖的旧manifest绕过身份校验。n1_paths及原共享锁路径均不变。

## 本地检查与独立复核

最终命令（scripts目录运行）：

```text
E:/fpga_race-two/.venv-kwt/Scripts/python.exe -B -m unittest test_n1_process test_n1_paths -v
```

最终32项检查通过，耗时6.193秒，exit 0。使用真实小型Python子进程和注入故障，覆盖初始
owner ENOSPC、partial owner保留、私有intent/PID/终态写满、Popen失败、子进程失败、错误日志、
owner被换、相同字节的新锁目录、等待中断、SystemExit、close失败，以及N1 main的真实
启动/等待/failed或passed状态写入。runtime测试继续核原共享锁、私有根和manifest边界。

此前17项初版检查通过；补close及main集成后21项通过。第一次追加旧runtime测试出现
14项中1个fixture错误：该旧fixture不含新增n1_process，严格guard按预期拒绝。获根代理
确认后，仅为该fixture复制真实依赖、把其SHA登记进fixture manifest、绑定实际导入路径，
并新增owner的private ledger路径断言；没有放宽生产guard。随后上述32项联合检查全部通过。

四份代码均用Python 3.8.20的`ast.parse(..., feature_version=(3,6))`通过Python 3.6语法检查。
这不是在真实Python 3.6解释器或Linux服务器执行过本修复的声明。最终文件已统一Git LF身份。

`/root/n1_rtl_audit`已只读复核核心实现、close收尾及旧fixture修正，未发现阻断项，也未重复
全套测试。固定文件SHA、失败路径及结果见
`handoff/team/evidence/N1_PROCESS_LEDGER_FIX_20261113.json`。

## 部署与恢复边界

旧failed批次已经完成的65条仍是失败批次的部分证据，不能改为1200通过，也不拼接进入新批次。
旧锁的人工恢复由根代理单独核进程、归属和原始回执，本修复不会接管或自动清除它。
后续新OPS部署、Linux实际运行和新的完整1200批次尚需执行；本地工具检查不产生硬件PASS。

SIGKILL、断电及操作系统默认终止不能保证Python finally执行。保留的owner与私有ledger用于
显式人工恢复；记录直接接受的子进程也不等于证明没有其他无关或脱离父进程的作业。私有盘
持续写满时即使子进程已完成，工具仍按失败处理，不能静默忽略记录缺口。
