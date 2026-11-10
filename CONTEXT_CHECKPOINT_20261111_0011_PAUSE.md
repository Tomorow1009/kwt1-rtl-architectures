# 2026-11-11 00:11 暂停交接

**当前指令是暂停，覆盖所有此前“持续推进”要求。** 用户准备开发板下电，要求关闭板上两个程序、暂停电脑任务、远端Linux已有任务继续。未经用户明确恢复，不重新打开客户端、上传包或启动新作业。恢复后先读AGENTS、本文件、有效计划和STATUS，核对已完成/未完成。

## 已完成的暂停动作

- Linux FileZilla已Ctrl+D断开、Ctrl+Q正常退出；传输队列为空。
- VNC本地查看器PID1823已退出；只关闭开发板客户端，未关闭远端终端、未发远端停止命令、未清共享锁。
- 开发板windows清单及ps均再次确认两个客户端不在。可以下电。
- 电脑端FTP代理会话10109、VNC relay40071均Ctrl-C结束；旧relay76458早已结束。新包构建21359、端口观察器fixture95656、旧DNS查询56761均已完成。当前无本任务构建/仿真正在运行，没有新后继队列。

## 本轮完成与同步

- 当前本地及已独立ls-remote确认的云端提交：`e65e8dc8c4c0f5c7ba94dfc792e382565c9f0d53`，私人仓库Tomorow1009/kwt1-rtl-architectures，个人分支codex/light-light126/undergrad-d1-numerics。本次暂停记录仅先保存本地，尚未再次推送。
- 已实现32位ICB无损输入压缩、成功共享写ACK后解码转发、R1/R4计算、物理bank、IRQ/WFI固件、真实ASIC运行入口；已有本地完整14例/恢复/竞争等证据见23:59及22:57检查点。12名义层平均34616周期、4333.256 task/s仅pin_mock折算，无E203/PPA。
- 新synth/gate/activity/power/numbers/timing/batch/bringup_queue工具已在e65提交。端口观察器完整datapath L01压缩34639、extremes raw38052两例通过；软件契约14项在当前及干净导出目录通过。后继回执/224宏功耗清单的正反检查通过。以上不是真实门级/PPA。
- 原生产fcd445fb212a81469c900c6aa1cbb544daad08a5仍保留：225770周期/664.393 task/s、原1200真实ASIC任务通过。原29.627mW、44.593µJ/task仍是布局前估算且system_power_verified=false；新版没有实际功耗，不能沿用。

## 两个包的准确位置（勿混淆）

1. **c019包已经服务器核验：** `light-light126-icb32-r4-20261110_231731-c019d7ce3306.zip`，10,912,739B、580输入，SHA256 `70026e7b1b380bdd5b9da2027a1123886618274c6856550b7e951a0ea8fbb2b8`。正常FileZilla成功上传21秒；服务器23:47安全解包、580输入、固件ID4b574604、平台新副本128大/96小宏预检通过，未编译/仿真。服务器目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261110_231731-c019d7ce3306`。
2. **e65新版包仅本地和开发板暂存，尚未FTP上传：** `local_runs/light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0.zip`，10,963,107B、594输入，SHA256 `b77b5fa349fb48edd2fba10a30496e5645f12fc25b3ee9559c3d26adbb5b6f28`。干净Git源重建固件/ZIP校验通过，包内14项软件检查通过；板端上传helper独立SHA通过。实际暂存 `/home/root/undergrad-icb32-ppa-20261111-0003/`，GUI路径 `/home/board/undergrad-icb32-ppa-20261111-0003/`。用户暂停前新目录尚未成功切换到FileZilla，因此未上传新包。

FileZilla操作时窗口被VNC遮挡，helper只设置焦点而不抬升窗口，点击路径没有实际切换，Return误选了旧c019包。出现Target file already exists后已经Escape取消；实际日志为Skipping upload / File transfer skipped、队列空，**没有覆盖旧包，也没有上传e65包**。成功记录显示2包含这次skip，不能据此写两个包上传成功。恢复时先点击FileZilla可见空白工具栏将其抬到前台，再逐步观察路径；不得对黑色遮挡区域盲点。截图`takeover_local/icb32_ppa_fz_raised.png`保存了skip结果。

## 远端最后实际状态（不是暂停后的实时查询）

**2026-11-11 00:04:27**：原唯一串行队列parent232492，其cmdline实际包含原ecf绝对runner.py及正确plan SHA；协作锁driver212822、child31787，日志 `layer_11_activity_scan.log`。原队列继续运行，未发停止或重启。

原ecf包为 `light-light126-mmio-timing-dma16-20261110_111311-ecf3cd4afb3c`，队列 `runs/dma16_mac02_12_mmio8_gate_queue_v1`，阶段 `runs/mmio8_source_gate_full01/mmio8_gate`。plan SHA=`db8df26da37f6487c0141fe16cecc8b96e4364e211ba1e4fa622fa0fc8c1a7b6`，12命令；runner仅全部完成后写done.json（plan_sha256、completed=len(commands)、finished）。不要把客户端断开当成队列停止或完成。

## 连接故障与恢复经验

本机DNS一度返回198.18保留地址，旧FTP代理公共地址检查拒绝。Google HTTPS DNS核到比赛FTP58.213.25.66、VNC58.213.25.70；本地 `E:/fpga_race-two/takeover_local/contest_links_dns.py`仅包装原helper并替换精确比赛主机解析，不修改系统设置，传输仍是Linux FileZilla。用户要求重试后VNC成功恢复。该helper不入Git或服务器包；恢复时必须重新核DNS和窗口，不复用旧session/window ID。

## 未完成与恢复顺序

1. 用户明确恢复并确认开发板上电后，先读取本文件及 `workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、23:59检查点和状态。11/11 18:00冻结、11/12 17:16交付准备、11/13晚上用户截止仍保留，按实际暂停时间重新评估剩余运行预算。
2. 保存/同步暂停记录；恢复既有客户端，先只读查看原队列和共享锁。未经核实不重启旧任务或清锁。
3. e65新包正常FileZilla上传到既有独立比赛目录，安全解包、核验594输入。先确认原queue done及锁状态，再启动一次新ASIC14→synth的bringup；**目前后继进程没有启动**。
4. 新版真实ASIC/E203、综合150MHz/面积、门级14/12活动功耗尚未开始；真实E203恢复/竞争、B1/B2正式PPA对照仍缺。失败保留，新包修复，不修改已运行快照。
5. 新最终报告导出与严格时序审定需要适配实际新网表；旧dma16_report/review有固定旧宏数/结果字段，不能直接套用。冻结后自身1200真实ASIC/30412800输出、同网表门级14/活动功耗12、干净复现及交付收尾仍未完成。

更多已试路径和本地运行目录见 `CONTEXT_CHECKPOINT_20261110_2359_ICB32.md`、22:57、22:04检查点。当前不继续开发、不创建后台等待/上传作业，等待用户恢复。
