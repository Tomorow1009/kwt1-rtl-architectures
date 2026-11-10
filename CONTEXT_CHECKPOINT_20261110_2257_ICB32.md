# 32位ICB / C64 接续检查点：2026-11-10 22:57

用户已批准“按计划开始”，持续执行中。有效计划：[32位ICB压缩与16×4实施计划](workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md)。11/11 18:00冻结，11/12 17:16交付准备，用户提供截止11/13晚上。压缩后先读本文件、有效计划、AGENTS、STATUS和根交接。旧过程/格式/服务器恢复细节见[22:04检查点](CONTEXT_CHECKPOINT_20261110_2204_ICB32.md)。

**23:01同步增量：** 已提交并推送`6a6f6ea97c10939fa15869e0d09f734eb3f1e4ed`到既有私人分支，`ls-remote`独立确认云端完全一致。首次Windows schannel TLS握手失败，改Git OpenSSL后端重试成功，未关闭证书校验。54文件包含本轮源码/文档/小型证据，无凭据/厂商库/大产物。下方“尚未提交”仅为22:57快照。继续服务器状态核查及新ASIC工具，不以同步结束本任务。

**23:04远端实际状态（覆盖22:10）：** 开发板windows刷新仍Vncviewer18874435、800×450，第三Mate Terminal页已实际观察空闲提示符。23:02读取原ecf队列done.json不存在，锁owner212822、L09 activity_scan、child205531；23:03:28再次实际读取`state.stages`为mmio8_gate/running，ps确认parent212822/232492仍活跃、当时直接子进程已变为activity_scan264277（R、CPU69.5%、elapsed21秒），说明旧队列继续推进，不能把L09旧子PID当当前。未停止/清锁/启动新EDA，FileZilla仍未打开。截图`E:/fpga_race-two/takeover_local/icb32_queue_2303.png`及`icb32_queue_detail_2304.png`。后续先继续本地SoC工具，原服务器队列自然结束后再排新任务。VNC relay76458保持；无本地仿真运行。23:01/23:04两条交接增量尚未再次提交。

**23:08实现增量：** 新`tb/arch03_icb32_source.sv`、`arch03_task_window_icb32.sv`、`arch03_icb32_monitor.svh`已实现动态CODEC_BYTES、原SysMem N+1响应、首源VALID至最后输出ACK/排空、零共享读回、逐编码字成功写入后消费及解码半字逐个核对。新fixture/runner `tb_arch03_icb32_monitor_fixture.sv`/`local_verify_icb32_monitor.py`用实际生产observer/source+真实datapath通过L01压缩34639周期及extremes raw38052周期，目录`local_runs/icb32_monitor_fixture_20261110_230654_140963`，摘要`ICB32_MONITOR_20261110.json`。会话38261已完成。fixture无E203，日志生产observer的cpu_executed=true不作为CPU证据，独立摘要明确false。新增5文件+证据及交接增量尚未提交；原6a6f6ea云端已确认。下一步仍缺`icb32_soc.py`、对应batch/包/服务器入口、动态每例固件元数据和正式E203；不能认为旧dma16_soc硬编码工具可直接使用。现无本地仿真。

**23:10数据工具增量：** 新`scripts/icb32_data.py`已实现标准库独立数据准备/编解码核验、捕获复用校验、ICB32完整窗口解析，并显式拒绝MONITOR_FIXTURE作为CPU证明。正确同源L01/extremes准备、回读、窗口解析通过，目录`local_runs/icb32_data_check_20261110_2310_v2`；首个`...2310`错误把旧核心测试tile8样本（37356B）绑定到新datapath L01（37428B），解析器正确拒绝source_bytes不一致，未改检查放行。准备应使用`local_runs/light-light126-reportfix-dma16-20261110_020049-7dc2617176b6/validated_data`作为服务器14例原tile8数据；其对应`validated_tile16`是本轮datapath用例。旧核心18任务另用172259目录，不能混为同样本PPA对照。新文件仍未提交。下一步真实ASIC compile/每例program-only boot元数据/运行收据，当前仍无新服务器上传或作业。

**23:15工具实施增量：** 新`icb32_soc.py`已写完整真实ASIC编译/每例动态length boot/IRQ及结果校验，`server_run.py`新增icb32_soc/icb32_build阶段并沿用同一共享锁，`package_icb32.py`从已提交LF源重新编译IRQ固件、打包原14例/严格ZIP白名单及逐项哈希，不含缓存。语法/CLI检查和本地固件source/ELF/metadata/IRQ验证通过；这些新服务器功能尚未在真实平台跑。`arch03_tcm_ram.sv`依赖旧`arch03_sram_half`，新compile保留旧shared文件供TCM helper引用，同时新shared_turnover独立模块，无重复命名。尚无新batch1200/synth/gate/power入口。准备再次提交/云同步并实际打包；此时未上传，原队列23:03状态保持，不启动并发EDA。

## 已完成（新结果均为本地，不是新ASIC/PPA）

- 软件codec600/7200无损回读及全部独立坐标、8项软件定向、21配置RTL decoder通过；B1原16路ACK转发14反压及6名义通过；独立turnover fabric386事务/306同拍交接通过。详情与原始路径见22:04检查点，原模块未改。
- 新R1/R4核心、压缩transport和MMIO wrapper已实现：`arch03_linear16x4.sv`、`arch03_icb32_transport.sv`、`arch03_icb32_accel.sv`。X64小宏、W32小宏，向量最多4半字，双结果bank，末3行屏蔽；transport源16/提交16/命令8/输出32，成功ACK发布，寄存命令与旧pending owner分离，取消保留已发VALID。总线始终32位单在途。
- R4核心18任务（L01/extremes/rounding × pf0/1 × A/B/A，B=L12）通过精确41bit总和/结果/sat、五阶段cancel、badbias、复位、末3行、向量1..4检查。目录`local_runs/arch03_linear16x4_20261110_223725_260527_pin_mock`。
- R4完整14例jitter1通过354816输出：`local_runs/icb32_datapath_20261110_224515_893045`。同14例名义通过：`local_runs/icb32_datapath_20261110_225139_667062`；12层平均**34616周期=4333.2562977 task/s@150MHz**（pin_mock、无E203）。L01=34639；extremes raw回退38052；rounding33914。不得转为ASIC/PPA结论。
- R1三例×pf0/1名义6任务通过：`local_runs/icb32_datapath_20261110_224527_681115`，L01pf1=116303。R4 L01强制raw双pf通过：`local_runs/icb32_datapath_20261110_225510_415689`，pf0=50580/pf1=38052；压缩版pf1=34639。这是局部拆分对照，R1尚无正式12层PPA。
- 恢复测试通过：5非法配置、source/stage/output三种响应错误归属与排空、badmagic、总头长度同步修改后的真实末载荷截断(error22)、4阶段cancel、无复位后真实25344输出任务。目录`local_runs/icb32_recovery_20261110_225115_784225`。前一224916_209813只覆盖头长不符，保留旧目录，采用新版摘要。
- 合成CPU主设备竞争通过：96次访问、byte mask、共享宏bank边界、响应反压、公平性、完整25344输出。目录`local_runs/icb32_contention_20261110_225458_662773`，L01jitter1=88081。不是E203竞争验收。
- 上述小型证据均已保存`handoff/team/evidence/ICB32_*_20261110.json`，含源/数据/原回执哈希。原始运行日志/波形不入Git。
- 新IRQ/WFI固件`sw/kwt_icb32.{h,c}`、`main_icb32.c`、`start_icb32.S`和`build_icb32_firmware.py`已写。动态encoded_bytes，load_acks应为0，PLIC/CLINT与IRQ复用原验证实现。ITCM仅固件和fff0 shift、fff4 length、fff8 layout、fffc rows；输入区全零。R4 IRQ shifts11/12编译通过：`local_runs/icb32_firmware_r4_20261110_2254`，8项ELF/boot边界检查通过，新Python脚本3.6语法通过。编译不是CPU执行。
- `install_icb32.py`已写但未实际安装验证：复用严格ASIC/TCM/SysMem/PLIC安装，再只改新副本的加速器/fabric及新monitor include；宏清单128大/96小，加速器0大/96小。原平台本地未找到，待服务器独立目录验证。

## 失败及已修复路径

- 核心首次223649_885305由Windows .bat拆分generic参数的等号导致xelab失败；改options文件后通过。
- turnover首次222736_316471由TB误放counter声明域编译失败；修TB后通过。
- CPU竞争首版225127_792774超时：TB只拉高ready一拍，但随机response_gate可能关闭，未等真实ACK就发下一请求。仅TB修为等待rsp握手后通过，生产RTL未改。
- 本次一次长中文Python stdin写文档因UTF-8编码失败，无文件写入；改apply_patch保存本检查点，不把失败当已写。
- 所有旧失败目录保留；不续旧37任务/功能TCM批次，不用BEGIN窗口或旧网表证明新设计。

## 当前进程与同步

- 本地仿真会话66399/6284/17616/84809/33729/20398/39818均结束（84809首竞争TB失败）。当前无本地仿真运行。
- VNC relay会话76458保留。开发板22:06在线，VNC18874435在22:10实际观察；重用前刷新窗口。FileZilla本轮尚未打开。
- 服务器最后实际观察**22:10**：L02–L12 MAC全部passed；原ecf唯一队列parent232492继续，8路`mmio8_source_gate_full01` driver212822、child127804在L08活动扫描。不是实时状态；不得重启队列/清锁/并发新EDA。旧队列base和操作细节在22:04检查点。
- 当前分支`codex/light-light126/undergrad-d1-numerics`；检查点创建时原HEAD57d62f6，新代码/证据尚未提交推送。下一步保存Git并按既有同范围授权推送私人团队仓库，具体回执须后续补记。未上传服务器新包。

## 尚未完成与下一步

1. 保存本阶段源码/证据及云同步；实际读取原服务器队列/锁，不重复作业。
2. 实现独立动态source、完整计时观察器、ASIC SoC运行入口、按每任务encoded length生成固件元数据/boot；当前新`arch03_icb32_monitor.svh`尚不存在，安装器不能被当作已可运行交付。
3. 新真实E203/厂商宏14例、真实IRQ/WFI和恢复/竞争；新综合、严格150MHz、面积、12层功耗。同配置哈希，不继承旧fcd的PASS。
4. 按实际时间与结果减少候选，冻结优选后自己的1200真实ASIC/E203任务30412800输出、同网表14门级、12活动功耗、干净复现和交付。
5. 保留原fcd 664task/s退路；原29.627mW是布局前估算且system_power_verified=false，旧8路完整PPA/未知审核/交付缺口不抹去。新版本没有功耗数值，不能沿用旧29.627mW。

无需再开发宽总线/128MAC或8路DMA。简单codec统计平均总事务已超30000，5000不是已达目标；继续按真实结果和原数值规则推进。不得擅自调用子代理（当前developer限制主动委派）。
