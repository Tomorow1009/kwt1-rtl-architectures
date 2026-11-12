# 2026-11-13 02:15 N1执行检查点

有效计划仍为`workspaces/arch03/IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`，N1→N2→D1→D2按完整验收闸门推进。用户要求持续自主工作，VNC/FileZilla已释放；不得自行停止工作或因可独立推进的缺项结束。压缩后先读AGENTS、根交接、本检查点、计划和STATUS。

## 身份与本地成果

- 分支`codex/light-light126/arch03-n1-n2-d1-d2-20261113`。N1生产实现冻结`9305c6948c764fed01fe86b20bb3db94170299ab`，已push并ls-remote复核；B0仍63da6ba，备份标签不动。
- 前一检查点`CONTEXT_CHECKPOINT_20261113_0120_N1.md`记录全部本地10000随机块/794560输出、datapath14/354816输出、latency1/2、格式/恢复/固件/工具测试。均已完成，不重复。
- N1 ZIP：`light-light126-n1-v4-20261113_013211-9305c6948c76.zip`，8816232B/763文件，SHA`6e0aa086526f10485f41260c7c9a623515edd3f35b08941720a9f8e5bb3eb772`，上传/原共享目录解包已通过，不重复传。
- 共享原N1包：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-n1-v4-20261113_013211-9305c6948c76`。

## 新服务器通过结果（不是N1完整验收）

1. `runs/data100_identity01.json`：实际100条/1200层/4800HEX集合、大小及SHA通过，库存SHA为ae052bc1…e997；回执SHA`38fe007403c63075239a3a8b0b27fba47b614329a4bffce6cd807bcb6665542b`。不是float精度或硬件1200结果。
2. `runs/n1_asic14_01/n1_soc`：14例354816输出total33/result16/sat全一致，真实ASIC/E203、物理宏、SHIFT10、IRQ/WFI和完整写ACK边界通过。summary SHA`56fb13bcd320ad1895506ed30399205ad31c30e1dfa0d95d75e944e051bde58b`。固定12平均29711周期、150MHz折算5048.635185621487task/s，非芯片实测。原PID130549已结束，不重启。仿真每例约3.4~3.7秒，整阶段仍有编译/数据/哈希开销。
3. `runs/n1_sequence_01/n1_sequence`：真实CPU十阶段恢复及无复位A/B/A通过、76032输出；summary SHA`ea69582933628c305e3e9502b91dddeff373b0233b1157851bc353f3ba6b52da`。01:55:38完成，原PID138564已结束。
4. `runs/n1_contention_01/n1_contention`：layer_01/rounding两例实际CPU/DMA公平竞争通过、50688输出；summary SHA`0727e713fb9de027f6ebc6d6078a161b65de5c67d54dd45b78ebd053309c4761`。01:59:20完成，原PID147256已结束。

## 空间失败、原始R4保护及新运行磁盘

- 用户已具体批准R4 L01做gzip、完整解压SHA/字节匹配且无人使用后删重复raw。此前自动审批拒绝已由明确新授权解决，不能继续误报未获授权。
- 唯一共享盘归档`runs/r4_l01_archive01` PID131387于01:48:48启动。共享盘被其他写入持续消耗，02:04观察其已因`2 GiB reserve reached; raw and partial archive retained`失败。**R4原始12,595,749,229B完全保留，没有归档成功/删除raw。不得重启archive01。**
- 本轮失败partial为3,240,049,537B。首次清理在写回执时遭共享盘ENOSPC，退出于unlink之前，没有删除。02:11已改在私有/tmp先持久化回执、核原R4不变/路径/owner/fuser/partialSHA，再仅删除该不完整派生文件，回执复制回原归档目录。partial SHA`dc707a1e5670cf1acb01111ce86cc98ff52ff712565da9f465e7f629c3a6041c`。回执名`failed_partial_disposal.json`，同时保存在/tmp私有根；失败receipt原样保留。不要重复删除。
- 旧非B0/R4 csrc前14个多约9MB，回收价值低，关闭该方向，没有删。精确候选和排除依据见`N1_SPACE_RECLAIM_CANDIDATES_20261113.md`。旧已删8.746GB gateprobe及以前6批不重复。
- 开发板只有约1.2GB可用，不能承载12.6GB备份；本机E约18GB/F约99GB，未下载服务器文件/未启新通道。
- **关键：服务器/tmp在独立/dev/sda3，02:12实际可用771027173376B；/storage2已满。** /dev/shm不使用。新私有根`/tmp/s4_21usr_n1_20261113_0210`，当前uid14021、0700、不同st_dev、无symlink，已从相同ZIP再次逐文件核验解包到其直接子目录同名9305 bundle。这是新的临时运行工作区，不是覆写或重复旧验收。
- 临时磁盘结果必须最终完整归档回项目共享目录并记录原路径/哈希；不能把/tmp当永久交付存储，也不能自动删除未备份临时结果。

## 当前唯一EDA任务：N1新综合

- 02:12:42启动`N1_SYNTH_PID 169157`，session`n1_synth01`，原9305工具/源码/约束不变。运行目录：`/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-v4-20261113_013211-9305c6948c76/runs/n1_synth01/n1_synth`。
- driver log为同tmp bundle的`runs/n1_synth01.driver.log`。仍使用原server_config及共享`.arch02_team_lock`，没有启新的独立锁/并行EDA。先读state/lock/process，不重复launch。
- 新综合尚无结果，必须核220宏、真实缩位结构、latch/loop、全部DRC、150MHz及≤1.20mm²。不能套B0 DRC06旧U编号或仅看setup/hold。
- **VNC目前窗口18874436/workspace3，空闲shell，cwd仍为共享盘原9305包；Popen通过cwd参数启动tmp综合。FileZilla关闭。**最后synth启动截图已读，无待Return或local exec session。

## 并行本地工具与所有权（尚未提交/部署）

- requirements_plan_audit：已完成`n1_precision.py`/7项测试、新n1_report可选strict precision和固定12独立float/DRC核验，联合37检查通过。现接管**n1_server.py及新增n1_paths.py**与N1 gate/saif/power等运行目录边界支持：新增明确runtime根/manifestSHA及注册兄弟evidence包，严格私有0700当前uid固定/tmp前缀、全manifest验证；原server_root共享锁保持不变，不接受任意/tmp或config注入。不要并发修改其文件。
- n2_d1_feasibility：已完成B0小报告只读inventory helper及11项合成测试，见`B0_POWER_REVIEW_GAPS_20261113.md`。现正在实现**archive_r4_l01_staged.py**：私有独立/tmp先完整gzip/全还原/fsync；按实际空间预算才删raw，再完整复制校验回共享目录；回存失败保留tmp唯一完整副本、可只恢复复制，不能再次删raw。原archive工具不改。15项测试已过，代理正在补崩溃恢复边界，**不要部署中间SHA**。
- n1_rtl_audit：已完成`n1_drc_audit.py`、8项测试、`N1_SYNTH_READONLY_AUDIT_20261113.md`、N1_DRC_TOOLS_LOCAL证据。只读本次constraints/实际驱动，不修改冻结n1_synth。已结束，可复用。
- 这些工具完成后由root统一审查提交、GitHub同步、打新独立工具包；不改任何运行中的9305 bundle。新工具必须用源码SHA复核关联旧synth，不为工具更新重综合。

## 剩余工作与下一入口

1. 先读tmp原综合state/log/共享锁。并行等待staged归档及runtime边界工具完成，提交并部署新包到同私有根的独立兄弟目录，保持9305原件。
2. 在新工具进行R4 L01第二次归档时，使用新独立run/私有tmp；完整gzip验证前绝不删原始R4，失败保留唯一完整副本。原archive01和失败回执不动。
3. 原综合完成后按实际报告做结构/时序/面积、真实门级14、自己100×12回归、固定12完整SAIF/PT。正式EDA始终串行；不重跑已通过14/恢复/竞争，也不续旧B0/8路/R1队列。
4. Full100浮点源仍缺：`KWT1_WORST100_ORIGINAL_FLOAT.zip`预期SHA edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9，异步问题仍待用户路径。PR#9无新链接，本机和已搜服务器目录未发现；ALL_SPEECH只有单坐标不可替代。可继续全部N1整数/硬件，精度未验不能N2。
5. B0功耗已存在69.8371mW/14.2013µJ；新只读工具尚未在服务器跑。未知连接信号影响/模型条件仍待审，SAIF驻留不能证明valid时间相关性；不转移旧DMA16敏感度PASS。
6. 当前新N1尚无自己的1200、综合结果、门级/活动/功耗或阶段完整PASS。所有缺项保持false/null，不填0、不借B0结果、不进入N2。

## 02:35增量：工具冻结、部署失败保留与新归档启动

- 记录/暂存归档工具提交`3b5cf866b3377336343f7ae1a6688fc2c4066539`已push并ls-remote核对；N1精度/DRC/私有runtime工具提交`41b0846ce71990d1dbf29fcd22baff32febc6c48`也已核对远端。生产RTL仍9305c69，无新增N2。
- 全部代理已完成：runtime边界55项联合检查、staged archive19检查、B0只读inventory11检查；具体脚本/恢复说明见各代理文档。新runtime支持必须提供根/OPS manifest SHA及显式BASE兄弟包/manifestSHA，原共享锁不变。工具尚未在正式Linux路径入口验收，不把本地测试当部署PASS。
- 新完整工具包`light-light126-n1-v4-20261113_022722-41b0846ce719.zip`，8891173B/781文件，SHA`17d2e972e0452daf70505a69613423979bc0f1c9f10a50d6fc6ba676dc0a65e3`，**仅在本地，未上传**。新manifest SHA`0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e`；原9305 manifest SHA`73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d`。
- 136项生产RTL/运行数据/固件比较：除sequence driver.elf与其manifest ELF哈希外均相同，sequence.bin及sequence.verilog亦逐字节相同，manifest唯一字段差是elf_sha256。保留旧sequence回执与旧ELF绑定，不宣称新ELF已服务器运行；正常IRQ固件及RTL完全相同，可同源关联既有综合。比较回执`handoff/team/evidence/N1_RUNTIME_BUNDLE_COMPARE_20261113.json`尚未提交。
- 小ops ZIP`light-light126-n1-ops-20261113_021749-3b5cf866b337.zip`25424B，SHA`f268b0fda7b2ed6df0c232280ea50ab7087a5e7e4dc51ce96c053281d33fa8d6`，含归档与B0只读工具。已传开发板并核SHA，**FTP上传因共享盘满返回553，未成功。** 不误记已上传，不反复重试满盘。FileZilla已关闭。
- FileZilla启动经验：必须`HOME=/root`再进入`/opt/ac820-gui-root`；否则继承宿主/home/root会开启空白profile。原配置本地路径/home/board/n1_upload_20261113。Ctrl-R需要先读密码弹窗，再用现有secret文件输入，绝不向未确认窗口填密码。
- 已采用既有VNC小工具文本恢复方式部署**仅两个归档脚本**到`/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-archiveops-3b5cf866b337`。18段全部完成，无待输入part；packed SHA`ee44495616078a69efbe80f32500b3cdc773d1a1e39b1db85f602946c20670ee`、payload SHA`a24893b741972ebd082d93baa72f0d702081197edd4c404e6d7829b5a348ac38`均已服务器验证；两个源码SHA为原archive922c7ade…8570和staged f8e964ef…c42b，与已提交LF字节完全一致。不要再次粘贴/创建这些文件。
- 第二次归档已从共享9305 cwd启动，临时目录`/tmp/s4_21usr-r4-l01-20261113_0233`，输出固定共享9305 `runs/r4_l01_archive02`。driver log位于上述archiveops目录`archive02.driver.log`。PID186061，02:34:39已确认compressing_to_separate_tmp_original_retained、original_removed=false；不是完成/删raw成功。 原archive01不重启；恢复复制只能用同base cwd、同临时目录和--resume-copy，不可重新压缩或再次删raw。
- 02:32综合169157仍running，已由link171418转入实际synth child174746，日志`icb32_synth.log`。02:32:52共享free1072693248B、/tmp free769787482112B。正式EDA仍只有这一个，不重复启动。
- 当前VNC18874436/workspace3仍共享9305 cwd、FileZilla关闭。新archive02启动和02:34状态截图均已读，全部chunk/helper exec已结束，无待输入；原synth169157/child174746继续，archive186061继续。


## 02:36传输准备增量

02:34共享free521142272B、tmp769396137984B。新41b整包已放开发板/home/root/n1_runtime_tools_20261113并核SHA；Linux FileZilla正重开准备上传，尚未观察成功。仅此目录里一个新ZIP，勿误传旧9305包。VNC仍共享9305 cwd，归档和综合后台继续。

## 02:45增量：新工具部署身份通过，原任务继续

- `41b0846`完整OPS包已通过开发板Linux FileZilla上传；02:38服务器ZIP SHA和781项manifest文件全部核验通过，解包到私有runtime根下独立兄弟目录`light-light126-n1-v4-20261113_022722-41b0846ce719`。原9305包不变。FileZilla已关闭，未恢复旧上传任务。
- 02:39运行新OPS的`n1_server.py status --session n1_runtime_check01`，显式绑定OPS及BASE manifest SHA，Linux真实owner/权限/路径和文件身份核验通过。输出SESSION NOT STARTED是该只读检查session未启动，不是综合停止；原共享锁仍指向PID169157、child174746。/tmp free767319125248B。
- 02:43原综合169157/174746仍在运行，DC子进程约99.7% CPU；原归档186061约99.6% CPU。02:45归档receipt仍为`compressing_to_separate_tmp_original_retained`，error=null、original_removed=false。不得重复启动或宣称已删原始波形。
- 新B0只读inventory首次命令在创建OPS/runs父目录前失败，未启动进程、未写原报告；补齐父目录后唯一PID193812运行，结果`inventory_rejected: Small-file read budget exceeded`。输出在OPS的`runs/b0_inventory01/inventory.json`，保留失败；没有新功耗PASS。正在核查小文件累计预算，不读大波形、不盲目取消预算。
- 02:45共享盘free1107296256B、/tmp free764734582784B。原综合/归档继续，所有临时证据仍需最终完整归档回共享存储。
- 真实ASIC14、CPU恢复和竞争均已通过，验收清单补勾恢复/竞争项；全量新1200、综合/门级/活动/PPA及同批float100仍未验。固定12平均29711周期/5048.635185621487task/s是150MHz折算，不是芯片实测。
- VNC18874436/workspace3目前共享9305 cwd的空闲shell；最后02:45只读查询已完成，无待Return或后台GUI输入。代理只做本地N1结构/批量入口和B0未知活动审查，未操作远端、未开发N2。
