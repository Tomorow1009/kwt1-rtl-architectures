# ICB32恢复检查点：2026-11-11 00:54

**01:01增量（压缩前）：** 报告工具/暂停恢复记录已提交并推送，云端独立ls-remote为`022274d015e57b85c00640b2ae752b156f45b1ab`；服务器待运行快照仍e65，勿混淆。00:59:37实测新PID75421仍waiting_predecessor；旧driver212822、child72155运行`layer_12_activity_scan.log`。没有新ASIC结果。

本地新增尚未提交的真实CPU竞争工具：`build_icb32_contention.py`、`icb32_contention.py`、`sw/main_icb32_contention.c`；改`icb32_soc.py`仅新增可选独立诊断monitor生成（生产默认不变）、`server_run.py`新增icb32_contention阶段、`package_icb32.py --contention`可把独立polling固件纳入新包、ICB32_RUNBOOK入口。真实CPU在0xa0040000空闲128B逐字写/读/比较，观察器统计任务窗口内双方请求/服务和最多8次DMA机会CPU公平性；不当IRQ/PPA数据。当前R4固件已实际Zig编译、2shift模板和哈希通过，`local_runs/icb32_contention_fw_20261111_0101`；旧0100只CLI调整前构建保留。Python3.6语法和monitor生成模板检查通过，真实CPU/新增monitor尚未在服务器执行，勿写PASS。

下一项独立本地任务是适配真实E203无复位A/B/A及取消/错误恢复入口。已读原`dma16_sequence_soc.py`、`build_dma16_sequence.py`、`main_dma16_sequence.c`和source/monitor前半，尚未新增任何ICB32 sequence文件。原序列有5配置拒绝真实store fault、初载取消、超时排空、A/B/A共10phase；需要改动态编码长度、零共享读回、6bitFIFO掩码、row4core和多元素解码供数，不能机械替换旧11744/46976计数。原完整序列文件均保留，未修改。下一次继续按实际需要读取剩余monitor/check_phase后实现，不重复已有本地pin_mock恢复。

用户已明确“继续”，暂停撤销。有效计划仍为workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md；11/11 18:00实现冻结，11/12 17:16交付准备，11/13晚上用户截止。上下文压缩后重读AGENTS、有效计划、本文件与STATUS，不重做已有本地14例，也不把原fcd硬件1200/PPA算到新RTL。

## 本轮完成

- 开发板重启后已在线，板端e65 ZIP再次SHA匹配。FTP起初421用户过多，间隔重试后连接正常；本轮FileZilla成功上传22秒、成功1、队列空，已Ctrl+D断开和Ctrl+Q退出。实际新ZIP名字、路径与SHA均再次核对，没有上传/覆盖旧c019。
- 新e65包10,963,107B、594输入，SHA `b77b5fa349fb48edd2fba10a30496e5645f12fc25b3ee9559c3d26adbb5b6f28`，来源提交 `e65e8dc8c4c0f5c7ba94dfc792e382565c9f0d53`。00:51服务器安全解包通过，00:52 INPUT_HASH_PASS594、FW_HASH_PASS0x4b574604。服务器根 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`。
- 旧队列00:46:13实测仍运行L12 `layer_12.log`，driver212822、child64762、parent232492；done不存在、锁保持。00:52再次核parent cmdline确为原ecf队列runner及正确planSHA。
- **新版唯一后继已启动**：00:53:17 PID75421；00:53:43实测state=`waiting_predecessor`、completed=[]。新目录 `runs/icb32_r4_first01_queue`，launcher=`runs/icb32_r4_first01_launcher.log`；完成原队列并释放锁后顺序ASIC14→synth，未并发新EDA。新任务尚未实跑，不能写ASIC通过。
- 新本地`icb32_report.py`已写，逐层JSON/CSV/中文、动态编码/传输量、224宏、同硬件/固件/数据/活动检查；新batch原回执与输出重审。三项报告检查通过，Python3.6语法通过。报告缺功耗保持null、目标5000、审核标志仍false。新增工具尚未提交/上传，服务器当前e65包不含报告工具。

## 运行与连接身份

- 前驱ecf包 `light-light126-mmio-timing-dma16-20261110_111311-ecf3cd4afb3c`，队列`runs/dma16_mac02_12_mmio8_gate_queue_v1`，planSHA `db8df26da37f6487c0141fe16cecc8b96e4364e211ba1e4fa622fa0fc8c1a7b6`。不要重复启动、停止、清锁。
- board VNC PID1591，实际window20971587，800×450；当前第3终端页空闲在e65包根。先刷新窗口再操作。所有服务器命令仅经板上VNC打字。
- VNC relay exec session23793活跃。FTP relay本机PID21036，原exec sessionID在压缩截断中丢失，板端19080监听；FileZilla已退出，代理本身不占比赛FTP登录。需要暂停时只停本机代理/板端客户端，保留远端队列。
- 原连接包装器 `E:/fpga_race-two/takeover_local/contest_links_dns.py`，只为精确比赛主机查公共DNS，未改系统设置；本轮VNC解析58.213.25.70后正常连接。

## 已知边界和未完成

- 新RTL本地12层平均34616周期/4333.256 task/s仅pin_mock；14名义/抖动、恢复、synthetic CPU竞争等详见22:57/23:59检查点。新版真实ASIC/E203、综合、严格时序/面积、门级14、活动/功耗12、最终1200/30412800、干净复现均未验收。
- 原fcd生产664.393 task/s和原1200PASS保留；29.627mW/44.593µJ为原版布局前估算、system_power_verified=false，新版不得沿用。
- 下一步补真实E203恢复/竞争入口与报告适配，读取原队列完成和新队列阶段结果。服务器队列失败时保存原目录并本地修复新包，不改运行快照，不重启同一stage。
- 本轮PowerShell JSON解析因C/c同名键失败，改AsHashtable后日期自动缩短，已用Python仅恢复历史日期字符串并保存新子树；不改变历史数值/含义。后续JSON用Python UTF8，避免同问题。
- e65上传时第一次截图命令超过10秒仍在运行，读取图片失败；已poll18933/81442取得实际完成结果，未重复执行远端命令。这些会话现已完成。

下一次压缩前继续更新本文件/根交接。用户当前仍要求持续推进，不是暂停或只读规划。
