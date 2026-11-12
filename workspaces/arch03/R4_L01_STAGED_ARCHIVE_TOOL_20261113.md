# R4 L01独立磁盘暂存归档工具交接

2026-11-13 02:15。根代理新发现`/tmp`位于独立`/dev/sda3`，最后观察可用约771GB；`/storage2`已严重不足。原archive01因2GiB保护阈值停止，原始R4 L01完好，失败partial为3240049537B。该失败及原回执保留；其partial的处理归根代理，本文工具不会读取、删除或重启archive01。

用户已明确授权：R4 L01完整无损归档且还原SHA/字节一致、无人使用后，删除重复raw。新工具将完整归档暂存到独立`/tmp`，释放raw后回存`/storage2`；没有新增扩大到其他R4/B0文件的清理范围。

## 已完成和身份

- 新`scripts/archive_r4_l01_staged.py`，SHA `f8e964eff604562b1da8f909466a2c63c8268d69cf77bf58fad40c6e7756c42b`。
- 新`scripts/test_archive_r4_l01_staged.py`，SHA `06654e2ec88dee1d79204edb6684d184565f5b171ece4f992b6b437b6c4b03d1`。
- 依赖原`scripts/archive_r4_l01.py`，SHA `922c7ade8315b88cc213cdcafcd327b05193f893762cf86704553eee3a5a8570`，本次未修改。
- 19项小型fixture检查通过；Python3.6语法检查通过。Windows测试仅模拟POSIX账户、目录权限、不同设备号及块分配接口，实际文件、gzip、完整还原、SHA及回执均真实执行。
- 未启动服务器作业，未操作VNC/FileZilla，未修改9305冻结N1实现或原R4 summary/state，未由本代理提交Git。

测试覆盖：正常回存/保留raw模式、同文件系统拒绝、非法/重用tmp路径、tmp预算不足、源SHA错误、完整解压错误、回收预算不足、删raw后共享空间骤降、回存ENOSPC、损坏tmp、历史summary变化、文件占用，以及仅回存恢复不删raw。新增两种崩溃边界：raw已unlink但最后回执未落盘；最终gzip已落盘且tmp清理完成但completed回执未落盘。最初两个恢复测试暴露只读文件描述符fsync在Windows失败；改为以r+b打开而不写入后，19项全部通过。不是实际12GB服务器归档PASS。

## 路径和运行合同

生产`base=Path.cwd()`，与工具脚本所在位置无关。因此独立ops目录运行工具时，cwd必须仍为新9305 N1 bundle：

```text
.../bundles/light-light126-n1-v4-20261113_013211-9305c6948c76
```

唯一原始数据固定为其兄弟R4包：

```text
../light-light126-icb32-r4-20261111_011258-49759e108719/runs/icb32_r4_gate01/icb32_gate/layer_01.vcd
```

固定R4 gate summary SHA为`95113a35bf2941e985d8d1b8cbad7d88c0d56f07d3c1f533f0fcf549fb2efc7f`。不能通过CLI覆盖源路径、摘要或原始哈希。

- tmp参数只能是`/tmp/s4_21usr-r4-l01-<唯一标记>`的直接子目录；首次必须不存在，工具用0700原子创建，检查当前账户、owner、全部路径无symlink及权限。
- tmp的`st_dev`必须与源父目录、最终输出目录均不同。不接受`/dev/shm`。
- 最终输出固定为当前N1 bundle的`runs/r4_l01_archive02`，首次必须不存在，私有0700。旧archive01不动。
- 原归档模块放在新ops目录的同级，或用`PYTHONPATH`指定9305包的`workspaces/arch03/scripts`。这只提供模块导入，不改变base/cwd。
- CLI内部设nice19、ionice class3，单gzip6 worker；不调用EDA，不创建并发压缩线程。

由根代理在实际工具上传/哈希核验后执行一次，下面仅为调用合同：

```text
PYTHONPATH="$PWD/workspaces/arch03/scripts" python3 -B <独立ops目录>/archive_r4_l01_staged.py --temporary-directory /tmp/s4_21usr-r4-l01-<唯一标记> --output runs/r4_l01_archive02 --remove-verified-raw
```

## 保存顺序和空间条件

1. 原固定summary/state、source大小/owner/inode/时间戳/fuser检查通过；tmp空间至少`1.2×完整未压缩raw大小＋2GiB`。不用乐观的压缩率估算降低tmp预算。
2. 原始文件顺序流入gzip6，流式原始SHA/字节数必须与冻结记录一致；压缩文件flush/fsync。
3. 完整解压到内存块，逐块核原始SHA和字节，不写第二份还原raw；计算gzip SHA并核稳定性，以hardlink原子发布tmp完整gzip，再fsync目录。
4. tmp保存主receipt，并尽量镜像最终目录。`/storage2`写回执失败时，主回执仍在独立tmp；不能因共享盘满丢失恢复入口。
5. 删raw前再次核原始文件与gzip、原summary/state及fuser；raw必须`st_nlink=1`。采用实际`st_blocks×512`作为可回收量，要求`共享当前free＋raw可回收量 ≥ gzip实际大小×1.2＋2GiB`。不足则同时保留raw和完整tmp，不删除任何原始数据。
6. 删除raw的意图先持久化到tmp回执，随后只unlink固定原raw并fsync原目录。之后再次检查回存空间；共享竞争导致不足时停止在`verified_tmp_waiting_for_return_space`，保留完整tmp。
7. 回存使用新唯一`.copy-<uuid>.partial`，每块保留2GiB空间阈值。完整复制后flush/fsync、重新读取实际目标文件核gzip SHA/字节，再原子发布最终gzip并fsync目录。
8. 只有最终完整归档再次核验后，才删除tmp的完整gzip。tmp小回执保留；原R4 summary/state保持原字节。旧失败copy partial不自动删除或覆盖。

## 状态、失败与恢复入口

主回执：`/tmp/s4_21usr-r4-l01-<唯一标记>/receipt.json`。最终镜像：`runs/r4_l01_archive02/receipt.json`。回执含源、tmp、输出、恢复命令、源码冻结summary/state、完整原始/恢复/压缩哈希及字节、设备号、预算、原raw是否移除、最终回存是否核验及历史记录未修改声明。

- 完成状态`completed_returned_archive`，退出0。
- 完整tmp已验证但空间不足，状态`verified_tmp_waiting_for_return_space`或`verified_tmp_and_raw_retained_insufficient_return_budget`，退出3。
- 异常非0，主回执记录具体错误和剩余副本；原raw未删时保持raw，已删时保留tmp完整归档。中断的目标copy只作为partial保留。

恢复只能从同一N1 cwd、同一tmp路径执行，仅回存模式不再删除任何raw：

```text
PYTHONPATH="$PWD/workspaces/arch03/scripts" python3 -B <独立ops目录>/archive_r4_l01_staged.py --temporary-directory /tmp/s4_21usr-r4-l01-<唯一标记> --resume-copy
```

恢复会重新核固定历史摘要/状态、tmp所有权/权限/设备及完整gzip SHA和还原证明。已有最终gzip必须相同哈希才能接受，绝不覆盖不同文件；失败copy仍保留。原raw缺失仅在本run已有持久化“验证后删除意图”时允许继续，否则拒绝。

回存完成前，tmp可能是唯一完整波形副本，必须把其精确路径留在根检查点；不清理该tmp目录或重启会清空tmp的服务器。只有实际最终回执与文件哈希通过才能报告空间恢复/归档成功，不能将本地19测试或`complete_tmp_archive_verified`提前称为最终回存完成。

根代理下一步负责部署、唯一启动、记录PID/精确tmp路径并监视；本代理代码与本文档冻结，不再改中间版本。
