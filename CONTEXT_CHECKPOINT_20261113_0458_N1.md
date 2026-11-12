# N1运行工具修复与恢复检查点（2026-11-13 04:58）

## 05:10上传阻塞增量（优先于下文未冻结描述）

### 05:11数值连接解析增量

- 新query8_total33_order已实际执行：counts=[80,80,80,80]，failed75，首3均B侧仅提取到convert[i].bias[30:0]。这表示严格位名模式未匹配，可能涉及最高符号位映射为buffer/别名，**尚不能判硬件错误，也不能忽略后放PASS**。n1_rtl_audit代理正在按实际B token/驱动准备最小补查。截图n1_total33_order_0513.png实际钟05:11:04。原长query8预览与新摘要都保留，RTL未改。
- root末个服务器命令已结束，VNC3空闲。八个旧重复输入ZIP保留/清理命令仍待requirements代理，尚未执行任何复制或删除；新OPS仍FTP未成功，不能启动batch02。

- 新工具已commit/push并ls-remote独立核对：**0f62e41207909904efd544992013c1244b0fd63b**。807文件完整包已生成：`light-light126-n1-v4-20261113_045945-0f62e4120790.zip`，9007722B，SHA`a9e14702e3092292826f1e37fc28fbc08064f2b0444ca744dd83217ba79920ce`，manifestSHA`1c55d5515de4258c77537e52387809ea04a33a334a4fefee8e2600ec2b7209e0`。本地及板端`/home/root/n1_ops_20261113_0502`已实际核ZIP SHA。
- root与独立代理均核新旧完整ZIP及所有成员：107 RTL/TB、4主IRQ固件、94数据文件全部同41b；诊断8文件只有sequence ELF及其manifest变化，bin/verilog一致，旧sequence PASS仍绑定旧ELF。新小证据N1_PROCESS_FIX_PACKAGE_IDENTITY_20261113_0505.json已生成，未再提交。
- 05:00:51共享free34603008B/private748401012736B、原锁无/EDA[]。FileZilla已正常连正确现有站点，但上传返回553 Could not create file、显示786.3KB后失败。**05:08:20实际VNC核新ZIP不存在，无partial可删；共享free1048576B。新包尚未部署，batch02尚未启动。** FZ已AltF4关闭，无FTP占用，VNC3空闲。
- 已只读核server project根的8个旧11/10 DMA16/MMIO输入ZIP（不是R4/B0证据），与本地最大8个ZIP名/大小一致，共133216003B。requirements_plan_audit代理正在逐包核本地receipt、完整ZIP/全部成员，准备ignored精确manifest及≤5条分段VNC命令：先复制private/tmp、核SHA/字节/无占用→rootreview后仅删除8个重复源ZIP并保存回执。**尚未写服务器manifest、尚未复制或删除任何这8个文件**，不得按已清理操作。不要重复删已完成的OPS41b单ZIP。
- 这8个固定包为：mmio-objects 20261110_120027-4231c41f539d；mmio-report-phase 112517-e9fc57cecc73；mmio-timing 111311-ecf3cd4afb3c；x-compare 105208-a74588d97aaa；x-model 102408-b85e908fab38；mac-gcc48 100643-bb25f0843195；mac-use 094741-3dcd35187115；annotation-tables 090821-fd54fd14267d，完整名称见takeover_local/old_upload_inventory_0509.png。本地local_runs全部保留。
- B0已有unknown gzip查N5..N9/read_pending已05:09执行，SHA/41406行核通过，UNKNOWN_MATCH=[]，全部ABSENT_FROM_UNKNOWN；不等于原SAIF有记录且驻留已知。read_pending恒0仍只引用先前558probe。B0完整功耗未知影响未验，不重扫SAIF。
- n1_rtl代理新`takeover_local/n1_mapped_query8_total33_order.txt`978chars已准备（全80A/B/SUM位序摘要），**未执行**；旧query8长滚动输出不可当PASS。query7 sign_drivers仍未执行。
- 当前无待Return/tool session。下一步先收requirements代理8ZIP保留/清理命令并审阅，实际回收空间后重连FZ仅传0f62新ZIP；之后立即服务器SHA/独立private解包/actual runtime identity检查，再唯一新batch02。

恢复必须先读AGENTS、CONTEXT_HANDOFF、有效IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113、本检查点及04:30检查点的04:48失败增量。用户要求持续推进，没有暂停；仍仅N1，不能进入N2/D1。

## 当前主线

- 生产RTL仍9305c6948c764fed01fe86b20bb3db94170299ab。ASIC14/恢复/竞争通过；自己的1200尚未完成。原综合04:15完成，预算0.9511486879005002mm²、正setup/hold、0latch、220宏、全约束报告无违例，声明范围审核与最终门级/功耗未完。
- **batch100_01因共享盘owner.tmp ENOSPC失败**，04:41:07.153847结束；65任务/1647360输出total/result/sat成功前缀，不能算全批PASS。第66仿真04:41:10自行结束，无正式receipt，不补算通过。原运行目录和日志保留，不再启动/续写01。
- 错误来自旧server_run.call在Popen后更新共享owner信息失败，未wait就退出。requirements_plan_audit代理已实现仅N1的ProcessLedger（n1_process.py+n1_server.py、对应测试），原共享lock/owner首次写入仍保持唯一互斥，后续子PID/log写private ledger；任何Popen后异常先wait再抛。原server_run.py及RTL未改。
- 21个新测试及相关runtime联合32检查已由作者通过，独立review代理复核无阻断；最终需收齐作者小回执/说明、核diff，提交冻结并生成**新完整OPS包**。test_n1_paths旧fixture缺新依赖曾失败，已仅补真实依赖/导入路径，不放宽manifest guard。
- 最终Git LF SHA：process `69c0b9396449fde7048e88ec5c58d36770422c9fb24871728988eb8d429eed93`；server `1367c37b18cbb3041be5efef8d86e06eab6075768cfa65f9b35c38551a6877bb`；process test `96165c785c87bf828f0b668999c6a46c116d9e08fe2f45f05787b2e4f9ed6fb3`；paths test `92a8695018ccfa03976d6d6f3792ec614dc83beefdf95e45a2d1808fea514588`。冻结前再核，不混用旧CRLF raw server SHA。
- 最新已验证云端07ce5e1358fe56fa1a886372af745bb56a37aea8；工具修复/新证据尚未提交/打包/上传。agents正停止tracked文件编辑供root冻结，不能在package中途继续写入。

## 自身陈旧锁已人工核验释放

- 04:46同session所有进程为空、04:47精确275224/287728不存在，task66日志显示正常退出；只剩本作业owner.json350B。没有杀进程。
- 04:50:57先保存原owner、failed_state与receipt到`/tmp/s4_21usr_n1_20261113_0210/n1_batch01_lock_recovery_0452`。原owner SHA `d97bf037dfd2499137292f6f13e37dfbc4586e99374ee7845efa398bec51fa9d`。
- 04:52:03.401062再次核原锁绝对路径、非symlink、目录dev/inode/uid、仅owner.json、owner完整bytes与已存副本/SHA、精确自己session/PID、两PID仍无/proc后，只unlink自身owner并rmdir空锁。receipt状态`own_exited_job_lock_released_after_review`。不是自动清锁规则，不得用来删除他人的锁。
- 当前没有已知N1活跃EDA/仿真。新作业前仍检查实际进程/原锁/空间，不能把这次观察当以后实时状态。

## 已补数值与B0证据

- N1实际mapped SHA59c75a4930d82a417e8ac77386751f9cb53c7813964e329729ed9f2a3bfdc82e；全80乘法连接14×12/TC1、乘积26/累加32声明、每PE实际accumulator_reg恰32位都已实际检查0失败。小JSON与中文已由n1_rtl_audit保存。原结构03 SHA95a3bde42e44fe1aabcbb0b450a683acbfc3d5b298a423b4607daab0a7158652。
- query8 total33实际执行但逐位拼接太长，仅滚动尾部可见，**不能据此通过全80total连接**。n1_rtl代理会准备摘要查询，query7 sign_drivers尚未执行。所有query文本在takeover_local，不属正式源码。
- B0全部64共享宏adapter逻辑已读取：3组33/30/1，各226字符完整，只有INV2_12TR40与NAND2CV2_12TR40。实际固定库SHA5d236b1571f5bc791895328fa3f6f94e3873e985ee7963b9ac5e3e849b48949f核通过，函数分别(!I)与(!(A1&A2))。所以CEN=!cs、GWEN=!(cs&we)、WEN高/低8各=!(mask[1/0]&cs&we)。全部adapter这些输入已有SAIF known，支持宏控制已知性，不是直接leaf活动采样，也不能重建联合翻转。
- 04:55:19实际bank状态查询：5个bank_q_reg[4:0]保留，Q=N9..N5，均DRNQV2_12TR40，CKclk/RDNn792；read_pending_reg也保留。bank_q原名消失是重命名，不能说被优化成常量。后续可用N5..N9实际SAIF条目核选择/读MUX消费，B0未知活动影响仍未PASS。
- B0完整12未知清单及L01控制扫描已经完成，禁止重扫或借宏控制局部结论宣布system_power_verified。正式功耗69.8371mW/14.2013µJ仍为布局前待审核。

## 新OPS打包与恢复步骤

1. 收齐21/32测试和独立review，根检查diff/JSON/全部长hex64；保存本检查点与STATUS，提交个人分支，push+ls-remote核验。
2. 从新commit运行package_n1.py，数据可复用本地旧41b包validated_data，zig已知路径，--diagnostics --member light-light126。包完整manifest/所有文件核验；逐项证明RTL、主固件、固定14数据与9305/41b一致，不声称新运行工具已服务器通过。
3. 上传前用VNC查共享盘空间；仅经板端LinuxFileZilla原FTP通道到项目独立文件，不建立新SSH/下载通道。旧OPS上传ZIP已删除重复，本地及private retained_ops_upload_20261113_0428.zip保留，不重复删。若新FTP包没空间，可核其他重复输入ZIP的完整副本再按用户授权清理，不能删R4/B0/唯一结果。
4. 新包在同private root唯一目录解包核全SHA与actual runtime identity，再启动唯一新batch100_02完整1200，使用原共享锁与新ProcessLedger。不复用旧65为新batchPASS；旧综合/RTL身份相同可继续对应门级/PPA，工具与受测硬件分开报告。
5. 后续同网表门级14/完整SAIF12/功耗/完整float100仍待。原FLOAT100 ZIP缺口未解决，异步问题待用户，不能进入N2。最终临时证据必须归档持久盘，不能删唯一/tmp结果。

private root `/tmp/s4_21usr_n1_20261113_0210`；BASE9305 manifest **73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d**，旧OPS41b manifest0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e。旧04:05记录漏f6，不能使用62字符错误串。

VNC18874436/workspace3/cwd仍shared9305，FileZilla关闭、workspace4未用。最后Liberty查询已结束，shell空闲，无待Return或tool session。只用F:/linux_fpga_try/ac820.ps1原板端helper。
