# N1只归档工具准备检查点（子任务）

继承有效N1→N2→D1→D2计划。root安排完整私有runtime最终持久化回共享，不修改原绝对路径
和回执，不删除/tmp。本代理不操作远端，也未启动当前仍running的源归档。

已只读核对B0 freeze_b_server_v2、R4 archive与staged archive。B0的特定排除清单和mtime/size
检查不适合直接迁移为完整N1备份；只复用流式tar/gzip、回读SHA与fsync的思路。

新增独立`n1_archive_runtime.py`与`test_n1_archive_runtime.py`。固定已登记私有根/manifest、
终态、原共享锁和无打开文件检查后，只归档全部常规内容和symlink文字；外部目标不跟随。
确定性gzip先计数、1.2倍+2GiB共享预算、成员及gzip完整尾部验证、全量源前后SHA/元数据检查。
已有备份不覆盖，失败partial不清理，/tmp始终保留。恢复索引不宣称迁移验证或干净复现。

14项本地测试通过，实际Linux权限/进程与服务器归档未执行。当前完整实现说明见
`N1_RUNTIME_ARCHIVE_20261113.md`。root文件、n1_paths/runtime、RTL、旧备份均未修改；未提交Git。

下一步由root审查、冻结并部署独立新工具。先确认所有指定源阶段结束、共享锁空闲、cwd和日志
在源包之外，再使用新共享backups目录。当前running综合不能因工具就绪而提前归档。
