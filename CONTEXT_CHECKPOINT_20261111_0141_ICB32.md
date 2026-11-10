# 2026-11-11 01:41 ICB32 持续执行检查点

用户明确持续推进，不因常规步骤结束等待。**压缩后先重读AGENTS、有效计划、本检查点、根交接及STATUS的icb32_c64_execution**，再接续。有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`：32位ICB压缩落库成功ACK后解码、16×4 MAC；11/11 18:00冻结、11/12 17:16准备交付、11/13晚上截止。旧生产fcd的664.393 task/s/1200PASS保底不变。

## 本轮新增完成

1. 原ecf串行队列于**01:35:00.026395**完成12命令，plan SHA `db8df26da37f6487c0141fe16cecc8b96e4364e211ba1e4fa622fa0fc8c1a7b6`；没有重启/终止/清锁。L02–L12全部MAC有效采样核验：每层1622016 MAC/25344输出，采样未知和含糊控制均0，但不因此批准系统功耗。
2. 原8路完整门级`runs/mmio8_source_gate_full01/mmio8_gate`通过14例354816输出、12完整活动，均3843121周期。摘要SHA `06e388e1b744494fc00f224a43caf8de2ebf7e764eb1b655541ce7288a408533`已独立重核；无SDF，完整旧8功耗仍缺。证据`handoff/team/evidence/OLD_QUEUE_RECOVERED_20261111.json`。
3. e65唯一后继75421自动接续。**R4真实ASIC/E20314例已全部通过**，354816输出，真实IRQ/WFI证据全通过；12层周期与本地完全一致，平均34616=4333.2562977 task/s@150MHz。极值38052、rounding33914。摘要SHA `e5d009732e822cb5cf730e85b652a160f5022ba0197a9e6ff60960d76121d604`。证据`handoff/team/evidence/ICB32_ASIC14_20261111.json`。正在同队列`icb32_synth`，尚无新面积/时序/功耗结果。
4. ASIC14每例仿真子进程2.218–2.827秒；不包含准备、哈希/捕获检查，不能直接作为批量完整墙钟。最终1200应以新batch_progress实际耗时估算并留20%余量，非芯片加速比外推。
5. 新R1本地14例通过：`local_runs/icb32_datapath_20261111_012652_910910`，354816输出，12层平均116280周期/1289.98968 task/s。与已有R4 `icb32_datapath_20261110_225139_667062`按每坐标逐值比较全部354816输出一致；源码/测试台、编码文件、流量相同，仅R1/R4参数不同，局部加速3.359140×。证据`ICB32_LOCAL_R1_R4_20261111.json`及中文`workspaces/arch03/ICB32_LOCAL_COMPARISON_20261111.md`；本地对照无CPU/PPA，不替代服务器R1验收。

## 三个当前运行包（不要混用）

服务器共同父目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

- **e65 R4主运行包** `light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`：594输入，SHA `b77b5fa349fb48edd2fba10a30496e5645f12fc25b3ee9559c3d26adbb5b6f28`。当前ASIC通过及综合都在其`runs/icb32_r4_first01`，唯一queue75421在`runs/icb32_r4_first01_queue`。**不可重复启动**。
- **497 R4诊断/报告包** `light-light126-icb32-r4-20261111_011258-49759e108719`：11,158,655B/630输入，SHA `ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4`。正常FileZilla已上传，服务器安全解包/全部输入/IRQ、竞争、序列三固件已核验。生产固件manifest/ELF与e65完全相同；新增的诊断尚未服务器执行。后续诊断/报告从此包进入，已有综合可用但工具须正常复核同硬件身份。
- **f95 R1对照包** `light-light126-icb32-r1-20261111_012941-f95e940862ca`：11,009,300B/607输入，SHA `f0d484804f02e37d158bc5da874c65de60b284f3f176b375372eab035801bec1`。已板端SHA、FileZilla22秒成功、服务器安全解包/607输入/ID4b574601/rows1核验。**尚无服务器任务**，不得混为R4结果。

## 当前桌面、同步及失败路径

- 板端VNC窗口20971587仍在线，**第三终端cwd在f95 R1包根**。查询e65需要`../light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`；运行诊断前切497包。FileZilla已断开退出；FTP本机代理21036/VNC会话23793仍运行，不重复开代理。
- 服务器原232492/212822已完成退出，新75421队列仍继续；01:39:25.050333观察到running icb32_synth。原ASICdriver119154曾持锁，综合当前owner应重新读取，不能当实时沿用。
- 云端已实际核`f95e940862ca0da6de2280c741694a1c5c5ed51a`。本轮R1对照/ASIC/原队列回收证据和本检查点尚待提交。无RTL修改。包工具和本地仿真目前无运行：18669/70372均完成。
- Codex Python的Tcl初始化失败；用项目`.python/cpython-3.8.20-windows-x86_64-none/python.exe`完成17检查。打包需要NumPy，裸项目Python缺NumPy一次在import前退出，无目录；改`.venv-kwt/Scripts/python.exe`完成R1包。不要改测试绕过环境问题。
- 上次直接PowerShell中文stdin生成Python脚本编码失败，没有写入；中文脚本保存UTF8文件再执行。JSON更新用Python，避免PowerShell自动转换历史时间或大小写键。
- 历史8192cycle序列超时失败、4096修复及临时adapt脚本不可重跑说明见01:12检查点。新497正确4096；不修改受测快照。

## 接下来持续执行

1. 观察e65综合，核对新224宏（128大/96小）、无组合环、setup/hold、面积（新增DMA/decoder/仲裁等全计≤2mm²）。综合reports_ready不自动等于严格时序通过。若失败保留目录，定位实际日志，必要时修新包。
2. e65队列结束/共享锁释放后，从497运行`icb32_contention --cases layer_01 extremes`与`icb32_sequence --cases layer_01 rounding`，独立新session，顺序执行。实际CPU诊断尚未通过，不能借本地fixture。
3. 同网表门级14/12完整活动、12功耗及严格STA审核、最终1200/30412800输出、干净复现/交付仍缺。固定100样本历史根`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA `0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`，先重新核验。
4. R1已备包，为计划B2对照；主候选硬性验证优先，按实际宿主耗时安排R1 ASIC/PPA。旧8门级收齐后仍需同条件功耗；全系统未知影响审核保持未完成，不将29.627mW旧功耗套于新RTL。
5. 及时保存/同步，不结束等待用户；只有用户暂停时关闭板端两个客户端，远端已运行队列继续。

## 01:47增量

- 以上证据已提交并推送，云端独立核验`d78cc6a0e972c7a00f60a356e10dd3d632e3d740`。新ASIC摘要于01:40:57.632661独立哈希复核通过。
- 综合最后01:45:23.724291仍running且METRICS_NOT_READY；01:42:54.946240实际owner125556/child128047、icb32_synth.log正在映射，显示正常OPT-1206常量删除，未宣称最终无错误。唯一queue75421继续；当前无本地构建/仿真。
- 01:46:19服务器实际空闲884.82GiB；原8路12份VCD合计335.74GiB。历史产物未删。固定`IC/hex/manifest.json`重读SHA为`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`，与最终100样本入口一致；此时只核清单，未重哈所有任务文件。
- 已新增`workspaces/arch03/ACCEPTANCE_ICB32_20261111.md`，有效计划/旧验收/交付索引增加新版入口，这些文档增量尚未提交。不得把README下方旧状态当当前待办。
- 后续必须先看正在跑的新综合实际结果和共享锁，再新CPU竞争/序列；当前R4只有ASIC14通过，不能自动批准时序面积功耗，亦不能复用旧1200。

## 01:55增量（准备后续上下文接续）

- 云端及本地HEAD已核`21e55334595aeaca6587e3f7b67cd35de21c9585`，含新版验收、交付索引、`ICB32_INNOVATION_20261111.md`设计/答辩说明；无RTL改动。下面进度记录增量会使工作区再次变脏，按实际git status判断。
- **服务器最新实际01:54:36.696703**，e65综合子进程128047 elapsed12:22、CPU99.7%、RSS7996672KiB，icb32_synth.log22832B，已处理decoder/dot64/宏适配，正在`arch03_linear16x4_ROW_LANES4`。当前没有metrics/面积/裕量结果，不判断通过或失败。owner125556、唯一queue75421保持；勿并发新EDA。
- 当前VNC第三终端仍在f95 R1包根，窗口20971587；FileZilla已退出。全部本地构建/仿真完成，无本地任务在跑。正式R4ASIC14回执在e65，不在497/R1；下游诊断用497，R1只有本地14和服务器预检。
- 继续观察现有综合。通过报告收集后，先读setup/hold/面积/宏数/环路和实际约束；从497包按共享锁顺序执行`server_run.py icb32_contention --session icb32_r4_contention01 --cases layer_01 extremes`及`icb32_sequence --session icb32_r4_sequence01 --cases layer_01 rounding`（这些session尚未启动）。不要把本地恢复fixture算CPU通过。
- 同网表gate14/12活动、12功耗、最终1200、严格STA范围审定、干净复现继续待办，命令见ICB32_RUNBOOK。R1 ASIC/PPA在主候选后排队。不要因大项排队而结束本轮让用户重复说继续。

## 02:05增量

- 服务器最后**02:04:29.446193**仍running icb32_synth、无error、METRICS_NOT_READY。02:02:41实际日志已经越过新核心，处理平台FIFO/比较器/定时器/时钟门控等模块；这是进度，不是最终时序或面积通过。仍等待同一queue75421、owner125556/child128047，不重启、不另起EDA。
- README及ICB32_RUNBOOK已更新“R4实际ASIC14通过、综合进行中”，R1对照包状态也写入运行手册，避免后续误读旧的未验证状态。没有新增RTL、固件或重跑测试。
- 工作区当前只包含后续检查点/状态/README/运行手册的文档增量；云端最后21e5533。正式受测R4仍e65，诊断包仍497，R1仍f95，三者目录与哈希见上文。
- 下一步保持：等待并读取新综合真实PPA；队列完成且锁正常释放后，从497依次运行实际CPU竞争与序列，然后同网表gate/活动/功耗及最终1200。当前没有等待用户提供的信息。
