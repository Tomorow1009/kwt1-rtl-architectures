# ICB32 / C64 执行检查点：2026-11-10 23:59

**00:03增量：** 前驱队列回执缺失/错误SHA/不完整完成项均正确拒绝，完整回执通过；功耗SRAM数值解析器拒绝旧162宏，接受新224宏独立夹具。均是工具逻辑检查，不是硬件/PPA。全部新Python3.6语法通过，git diff --check通过；56761旧DNS查询已结束，无后台DNS进程。准备提交24文件及干净打包，未启动后继队列。执行状态的checkpoint指向本文件。

用户继续授权按计划实行，并于连接暂故障时要求“再试一下”；已重试成功。有效计划 `workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`，11/11 18:00冻结，11/12 17:16交付准备，用户截止11/13晚上。压缩后先读本文件、AGENTS、有效计划、根交接、STATUS。前期RTL/软件验证路径详见22:57及22:04检查点，不从头重做，不继承原fcd的1200/PPA为新版PASS。

## 已完成与本地待提交

- 云端c019d7ce33066d8744fbc656b62d1f8c71f4e4f7与本地HEAD一致，承接6a6f6ea。原fcd硬件不变。
- 新c019包 `light-light126-icb32-r4-20261110_231731-c019d7ce3306.zip`：10,912,739B、580输入、SHA `70026e7b1b380bdd5b9da2027a1123886618274c6856550b7e951a0ea8fbb2b8`。从Git LF源重建IRQ固件，ZIP校验与板端SHA通过。Linux FileZilla成功上传21秒、成功1且队列空，之后Ctrl+D断开。
- 23:47服务器安全解包/580输入/IRQ固件ID4b574604/原平台安装128大96小宏预检全部通过。新包服务器根：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261110_231731-c019d7ce3306`。预检仅runs/icb32_preflight/platform，没有新EDA/仿真。
- 新本地PPA工具已写：icb32_synth、icb32_gate、icb32_gate_monitor、icb32_activity、icb32_power、icb32_power_numbers、icb32_timing_audit。224宏清单、真实端口探测、动态三段流量、同窗口功耗和原库单位校验；保持审核标记false。工具未上服务器执行。
- 新icb32_batch：固定旧100样本manifest，一次真实ASIC编译，每例独立codec/ITCM元数据/boot/回执/25344输出，合计1200/30412800；尚未实跑。icb32_soc新增layout哈希及batch/server脚本冻结输入。
- 新icb32_bringup_queue仅等待原队列完整done回执及锁释放，然后ASIC14→synth；未启动。它不清锁/重试旧作业，不自动冻结或批准PPA。启动前须核对原parent232492真实cmdline含原绝对runner路径。
- 新生成门级端口观察器在真实RTL datapath上通过L01=34639、extremes raw=38052，目录`local_runs/icb32_monitor_fixture_20261110_234937_735905`，会话95656已完成。无E203、无映射网表；fixture原CPU标记不作为CPU证据。摘要`handoff/team/evidence/ICB32_PORT_MONITOR_20261110.json`。
- 新综合/端口/窗口/功耗模板6项检查通过；连同codec8项共14通过。Python3.6语法通过。新测试的两实际窗口摘录已写test_fixtures/icb32_local_windows.json，干净包不依赖local_runs。最后新增queue/数值提取/时序诊断尚需提交前最终检查，不必重复数值硬件回归。
- 新 `ICB32_RUNBOOK.md` 给出各阶段实际入口和范围。以上新文件、修改及检查点尚未提交；旧生产RTL未改，新本轮RTL也仅新增测试observer，没有改变受测datapath。

## 当前远端与客户端（时间有界）

- **最后实际23:45:42**：原唯一队列ecf `runs/dma16_mac02_12_mmio8_gate_queue_v1`仍在 `mmio8_source_gate_full01/mmio8_gate` 的L10 activity_scan，parent232492、driver212822、child279413（CPU99.7%，elapsed32:38）。共享锁仍归原队列，禁止并发EDA或大扫描。
- 原队列路径在ecf包下（新c019包同级）：`light-light126-mmio-timing-dma16-20261110_111311-ecf3cd4afb3c/runs/dma16_mac02_12_mmio8_gate_queue_v1`。23:56列出plan.json8199B、runner.py674B、launcher.log16926B，无done。23:57已实际读runner：按plan.commands顺序subprocess.run(check=True)，最后才写done.json `{plan_sha256:argv1, finished:iso, completed:len(commands)}`。plan SHA已历史核实为`db8df26da37f6487c0141fe16cecc8b96e4364e211ba1e4fa622fa0fc8c1a7b6`，共12命令。
- VNC当前实际window20971587，800x450，第三MateTerminal页空闲在c019包根。操作前刷新窗口；所有服务器命令仅经开发板VNC键入。
- FileZilla main18874950已断开，站点IC-single-connection目标仍icdesigns0.nicu.cn:18888、`/IC/light-light126-undergrad-d2-20261109`。本地目录GUI `/home/board/undergrad-icb32-r4-20261110-2317/`（实际board `/home/root/...`）。可继续既有上传授权，不能另用FTP/SFTP通道。
- 原系统DNS突然返回198.18保留地址，原FTP代理拒绝；Google HTTPS DNS实际查到FTP58.213.25.66、VNC58.213.25.70。新本地 `E:/fpga_race-two/takeover_local/contest_links_dns.py`仅包装原helper、精确比赛主机解析，不改系统网络配置，不记录载荷。FTP代理exec会话10109、VNC relay40071保持；旧relay76458已仅本地Ctrl-C结束。用户要求重试后VNC认证成功，连接故障已解除。临时helper不入Git/服务器包。
- 无本地仿真/构建正在运行。DoH PowerShell旧会话56761只DNS，须读取完成状态后关闭记录（不可当VNC/EDA）；之前单独握手95862已结束。

## 失败与修复

- FileZilla最初代理127.0.0.1:19080拒绝，实际是DNS fake IP触发原公共地址检查；未绕过服务器身份或更换上传路径。恢复后正常FTP成功。
- VNC最初两次欢迎头前EOF，询问用户后重试正常；未停止远端队列。
- 新综合测试首次缺少fixture standard_library_member/假库文件而失败，补测试配置后三项通过。不是综合失败或硬件修改。
- 一次检查点apply_patch匹配短行失败，随后标题锚点成功保存；一次读取中文JSON未指定UTF-8失败，改显式UTF-8后状态成功更新。失败未伪装为已完成。

## 下一步

1. 核对新queue/数字提取/阶段CLI及Git差异，提交/推送同私人分支，干净源打新工具包；不覆盖c019原包。
2. 正常FileZilla上传新包、SHA解包、服务器核验；保持原队列，核对原runner PID/plan，启动一个只等待的bringup后继进程。未启动前不能写正在等待。
3. 原队列完成后新ASIC14与综合；若新安装/编译/RTL错误，保留失败、改本地新包。读实际时序/面积后继续gate14/activity12/power或修复，不凭本地结果通过。
4. 补实际新协议E203恢复/竞争及正式B1/B2对照（时间受限可减少候选，记录淘汰，不新开发8路DMA/宽总线）。新最终报告导出仍待适配；旧dma16_report/review有硬编码224前的宏/字段，不能直接用于新版。
5. 冻结后自身1200、同网表14门级/12功耗、干净复现、报告答辩。原664版本保底；新当前约4333是pin_mock折算，未达5000，新功耗无数值。原29.627mW仍是布局前估算且system_power_verified=false。
