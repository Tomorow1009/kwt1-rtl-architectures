# N1临时证据只归档工具（未在服务器执行）

新增`workspaces/arch03/scripts/n1_archive_runtime.py`，不改`n1_paths.py`、运行包、原回执和RTL。
当前仍运行的源不能归档；这里是最终收尾工具准备，不是服务器备份完成记录。

## 已有路径的复用与差异

`E:/fpga_race-two/takeover_local/freeze_b_server_20261112_v2.py`已经用于B0备份。复用其
“新目的目录、tar.gz、逐成员内容回读及源前后检查”的做法，但不直接调用：它硬绑B0，排除
simv/库/波形/链接，只核前后mtime和size，且没有持有原团队锁，不足以作N1完整临时目录归档。

`archive_r4_l01.py`及`archive_r4_l01_staged.py`提供流式哈希、fsync、私有目录和余量守卫经验；
本工具不调用它们含删除的主流程，也没有源删除、清理/tmp、覆盖旧备份或原地恢复选项。
唯一移除的文件是工具自己创建、核对token和inode后释放的团队锁元数据。

## 归档范围和通过条件

1. 复用现有N1 runtime注册：固定`s4_21usr` Linux账号、0700私有根、OPS与逐个显式登记的
   BASE包、manifest与全部打包源码SHA。导入的`n1_paths.py`还须与OPS清单里的校验器完全一致。
2. 原共享`.arch02_team_lock`必须空闲；工具持有该锁直到结束，不并行启动新的正式阶段。
   每个登记包的runs/session必须有可识别且已结束的N1 state。成功阶段的summary SHA再次核对；
   失败、停止和取消的终态可保存，但不改为PASS。另仅允许下述显式绑定的B0只读辅助回执；
   未绑定、未知或缺state的目录会停止，不静默排除。
   读取终态前先lstat检查每个包的runs根；真实链接、悬空链接和非目录均拒绝，随后核规范路径
   和所有权，不能先通过exists/iterdir跟随外部目标。真正不存在runs的源码包可以继续归档。
3. 对当前账号进行`/proc`的fd、cwd、exe和maps检查，包括归档进程自身。包目录仍被使用、
   自己的driver log写在源包中、或不能读取当前账号进程信息时均停止。**启动cwd、请求文件及
   driver log应位于登记源包以外。** 不终止任何占用者。
4. 全部regular文件、空目录及symlink条目均进入清单和归档，无后缀排除。服务器内部已有
   自产网表/编译库会包含在内，厂商外部目标不会被跟随或复制。这类大备份不能上传GitHub。
5. symlink只保存原target文字、字节数和SHA，分类为登记runtime引用、外部厂商引用或其他
   外部/未解析引用；不验证或宣称目标内容已备份。特殊文件或无法安全表达的名称直接停止。
6. 先产生不落盘的确定性gzip计数流，按实际压缩长度的1.2倍加2GiB检查共享盘空间，再写新
   `.partial`。写入期间继续保留2GiB余量；任何失败保留源和已产生的partial。
7. 完整回读每个tar成员，核类型、内容SHA、字节数及元数据，继续读到gzip EOF以核CRC/ISIZE。
   再次全量读取源树，要求文件集合、SHA、inode、size、mtime/ctime、owner/mode等前后不变，
   重新检查终态和无占用后，才将本次partial发布为新归档并写verified回执。

## 新目的地与请求

目的地固定在原团队共享根的
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups/`
下，使用新的`n1-runtime-YYYYMMDD_HHMM`目录，要求与/tmp属于不同文件系统。已有目的目录拒绝，
失败重试必须使用另一个新目录，原失败记录和partial保留。

以下为**待源全部终态后的请求模板**；目的目录时间需按实际归档选择新名称：

```json
{
  "runtime_root": "/tmp/s4_21usr_n1_20261113_0210",
  "ops_bundle": "/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-v4-20261113_022722-41b0846ce719",
  "ops_manifest_sha256": "0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e",
  "evidence": [[
    "/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-v4-20261113_013211-9305c6948c76",
    "73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d"
  ]],
  "destination": "/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups/n1-runtime-20261113_1700"
}
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 <独立已核验工具路径>/n1_archive_runtime.py --request <源包外的request.json>
```

实际原始ZIP/新OPS部署若增加别的登记包，应明确增加对应manifest；不能假设本模板覆盖后来
未登记的目录。新工具可单独部署，不需要修改已冻结41b包。

已部署41b包还有已结束的`runs/b0_inventory01`与`runs/b0_inventory02`，它们是只读收集，
没有N1 state。请求必须另加`auxiliary_runs`，每项只有`run`与`receipt_sha256`两个字段，
分别填写登记包内`runs/b0_inventory01`/`02`的绝对路径和其`inventory.json`的实际SHA256。
不猜写哈希，不修改原回执，也不排除目录里的其他文件。

工具只识别`b0-read-only-power-review-inventory-v1` schema，且状态仅限`inventory_rejected`
或`read_only_inventory_collected_review_required`。两者都必须保持`system_power_verified=false`；
前者须有明确error，后者须有`no_eda_or_simulation_started`、`no_files_written`和
`no_large_wave_read`三个true标记。绑定须为登记包直接runs子目录，回执固定inventory.json，
禁止symlink、重复绑定或覆盖已有N1 state。全程重复核对绑定SHA，所有文件照常完整归档。
这些记录只表示只读工具已终止，不产生N1阶段通过或B0功耗审核通过的结论。

## 恢复范围与未完成项

归档中的JSON和绝对路径原样保存。`recovery_index.json`只提供“原bundle路径→tar成员前缀”，
逐文件映射在manifest的source/member字段。它不是路径重写器，也不是迁移后验证已通过。

工具不执行文件系统解包。以后只能向新空目录恢复并逐项核验；不得自动创建/跟随symlink，
不得把原绝对路径当作覆盖授权。外部库、工具和数据引用仍须单独确认；迁移验证和干净目录
复现都明确false。本工具成功也不授权删除/tmp，根代理还需审查正式交付、存储及恢复入口。

本地21项小数据检查通过，新增实际文件系统runs目录链接及悬空链接、普通文件根的遍历前拒绝；
覆盖显式B0辅助回执roundtrip、缺绑定/错SHA/未知状态/非只读标记/
重复绑定/N1 state覆盖拒绝和回执变化；也覆盖完整roundtrip、gzip尾部损坏、错误成员SHA、源变化、空间前置/
途中不足、已有锁和目的目录、运行中/未知终态、打开文件/映射/权限失败、链接与特殊文件。
Linux权限和进程信息在Windows测试中使用明确fixture；runs链接检查使用真实NTFS符号链接，
并非模拟链接元数据。未执行生产备份，不能当作Linux实际
归档或新硬件/PPA验收证据。
