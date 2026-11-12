# N1只归档runs根修订检查点

有效路线N1→N2→D1→D2不变。继03:18显式B0辅助回执支持，独立审查发现terminal_states
在检查runs本身是否链接前使用exists/iterdir，可能跟随外部目标读取终态。

已改为先lstat，只有真正FileNotFoundError才允许无runs；符号链接（包括悬空链接）和
非目录明确拒绝，再核规范路径/所有权后才遍历。原显式auxiliary_runs与N1阶段闸门不变。
不修改任何生产RTL、运行包、n1_paths、root状态或远端文件。

本地21项测试通过（10.207秒，exit0）。实际NTFS符号链接的live/dangling场景及普通文件
runs场景均在iterdir前拒绝。链接元数据未模拟；Linux owner/proc依旧仅是Windows fixture。
工具SHA：6bfd21fbf42dbce160829f99c8eff2d3075c75857f2ccbe74fec67e141de09f9。
测试SHA：4020d0b92f77ccaf1d75a953ab18d2a5da9c808e18afe24fc9c7881d6dd836d9。
测试回执：local_runs/n1_archive_runtime_toolcheck_20261113_033011/summary.json。

n1_rtl_audit已完成独立只读复核，确认runs边界问题修复，允许冻结上述SHA；未重复全套测试。
未做服务器归档/删除/tmp/迁移复现。
归档仍需全部指定源终态、原团队锁空闲、无进程占用及空间检查通过；只有工具准备完成。
