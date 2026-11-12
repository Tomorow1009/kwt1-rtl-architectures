# N1空间恢复：八个重复输入ZIP审计

根代理已于服务器时间2026-11-13 05:25:18.281713完成八个旧输入ZIP的保留与重复副本清理。
本审计代理仅核对本地验证记录与两张实际终端截图，没有操作服务器、上传、删除或修改运行目录。
清理使用用户此前明确授权的旧验证文件整理范围；执行前由根代理审查独立复制回执，再执行独立删除命令。

## 实际范围与保留结果

源目录固定为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`。
仅移除清单中八个2026-11-10的DMA16/MMIO历史上传ZIP，共133,216,003字节。
不涉及R4、B0结果、综合网表、运行目录、锁或当前N1源包。完整八文件名称、大小、SHA及本地保留路径见配套JSON。

服务器完整副本保留在`/tmp/s4_21usr_n1_20261113_0210/zip8_20261113_051340`，
本地`local_runs`中的八个原始ZIP也全部保留。复制前本地已经逐包核对原回执、实际ZIP哈希与大小、
成员集合、每个成员哈希及CRC；本次不重复运行这些检查。

服务器复制阶段核对固定目录、实际所有者、无符号链接解析、源与目标文件大小/SHA、源前后stat、
fuser无占用、私有副本fsync及独占回执。删除阶段再次全量核对两份文件与原stat，并逐文件复核、
保存意图回执，仅unlink清单里的精确basename。源码和清单均由完整压缩载荷SHA绑定；
分段传输使用独占p0/p1/p2，重复命令不会追加到旧载荷。复制和删除没有合并为一个自动步骤。

终端证据：

- `takeover_local/zip8_copy_0529.png`显示清单/工具身份及`COPY_VERIFIED`。
- `takeover_local/zip8_removed_0530.png`显示`exact_duplicate_zip8_removed_retained_verified`、
  133,216,003字节、结束时间及`free_after=10,719,592,448`字节。
- 复制回执SHA为`cded38d6c2afe89cbeeedb5c7e58e02925c75bebb7f393f16fed5381467bab53`。
- 清单SHA为`201d2cc6388b7ae4fb519b735100ee714ad5c2e13cab4364dedca8f1fc7f5ace`。
- 实际执行的LF工具SHA为`08659b1bcc1952b14567419e611d19033b18032bb17d17f63e09a937c8fa0511`。
  本地PowerShell保存版本含CRLF；不能把其原始字节SHA当作服务器LF工具身份。

共享可用空间是当时观察值；本次仅移除约127MiB，不能把整个空间变化都归因于本次操作。
本审计没有下载服务器完整`copied.json`与`removed.json`，依据实际截图和本地已核验的工具/清单记录，
该证据范围在JSON中明确保留。`/tmp`是临时保留位置，最终持久化义务不因此取消。

## 当前N1恢复入口与未完成项

新OPS包`light-light126-n1-v4-20261113_045945-0f62e4120790`仅修运行工具；
已独立核对其107项RTL/TB、4项主IRQ固件和94项validated_data与上一OPS集合及哈希一致。
诊断sequence的ELF和manifest存在差异，旧sequence通过记录仍绑定其原ELF，不能转移。

独立启动准备位于`local_runs/n1_batch100_02_launch_20261113_0525`：
先核ZIP哈希并独占解包，再执行status实际校验runtime身份及全部807项清单文件，随后只读核进程、
原共享锁和空间，最后由根代理审查后启动新`n1_batch100_02`。本审计代理未执行这些命令。
新批次必须完整重跑1,200任务，不能续接或拼接旧ENOSPC失败批次的65条。

当前仍须取得新批量终态、同网表门级/活动功耗、严格时序及未知活动审阅；完整100条原始浮点ZIP仍缺，
不能以软件manifest的NRMSE替代同批重新核算。空间维护和进程记录修复都不产生任何新增硬件PASS，
N2/D1/D2尚未进入实施。

配套机器可读证据：`handoff/team/evidence/N1_DUPLICATE_INPUT_ZIP8_CLEANUP_20261113_0525.json`。
