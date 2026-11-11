# 2026-11-11 20:55：B/v3本地打通，继续搬运优化及服务器验证

## 必须先读

压缩后读AGENTS.md、CONTEXT_HANDOFF.md、本检查点、20:00检查点全部增量、workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md，以及STATUS的systolic_b_execution。用户要求连续实施，不要在进度汇报后停止。A取消，直接B；R4冻结保底；H0=19:30:41，功能收敛11/12 08:00，硬冻结09:30:41，交付11/13 17:00。不得删除历史证据、续旧8/R1队列或重复R4的1200。

用户已明确确认传输完成、VNC可恢复。使用workspace3，workspace4不作为工作区。板端helper F:/linux_fpga_try/ac820.ps1，VNC现20971587/class Vncviewer/800×450。每次看图再输入；type完成后单独Return；不用Up历史。FileZilla已关闭。没有CUA会话欠completion_summary。

## 已完成的服务器B/v2证据

受测不可变提交e11c317c960b18fb60ecbaddf9449f2ff00448be，已push且ls-remote独立核对。包light-light126-systolic-b-v2-20261111_200441-e11c317c960b，ZIP11172059B/655输入/SHA fe3c47b4276ccb91bddd084b90e58133cc5b8300e5b45f0871437e6a8bf1330b。

服务器目录为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`加包名。上传、SHA、安全解包、655文件及IRQ固件核验均完成，不要重复。

`systolic_b_v2_first01/systolic_b_soc`已于20:20:50.929163通过14例354816输出和IRQ/WFI，12层平均36862周期/4069.231task/s。仿真case宿主合计45.297351秒，不含编译。原PID87707退出，不重跑。

`systolic_b_v2_synth01/systolic_b_synth`原作业**PID99451 / DC子108110**。20:55:05实际仍running，锁匹配，log=icb32_synth.log，尾部Processing arch03_linear16x5_systolic。尚无最终时序/面积，不称通过，也不重启。最后截图takeover_local/b_synth_2055.png。20:00 free148.094GiB为历史，不视为实时值。

## 本地新v3已实现，尚未提交/上传

新`systolic_b_codec.py`和`arch03_systolic_b_decoder.sv`，layout00100003，格式见SYSTOLIC_B_LAYOUT_V3.md。W逐tile raw/旧块/列位宽择短，X逐行signed/base+unsigned delta/raw择短，整流raw回退。W0/b→X99行→W1/b至W15/b。8项软件测试通过；14组原数据按原始坐标核对23488半字一致。12层平均31338.6667B，理想总线下界28341.3333事务，仍不能宣称7000。

独立v3 RTL解码器25情况通过（14数据、all_modes、forced_raw、9坏流），每正常流取消后无复位跑两次、187拍反压。目录`local_runs/systolic_b_decoder_20261111_203643_913485`。证据`handoff/team/evidence/SYSTOLIC_B_CODEC_V3_20261111.json`。

新B core已接入：layout_v3锁存、20组X有效位、W tile标签、8半字stash、按实际宏读优先并逐元素消费无冲突前缀；原子5X+16W响应队列深READ_LATENCY+2并保留在途信用。v2仍直接原加载顺序、全X后启动；新响应队列适用于两布局。80PE/双80结果区/双结果输出保持。新增B双decoder选择及能力000405ff，ID仍4b575305；未知layout拒绝，debug只接受旧原始流。

v3初次完整DMA pilot因TB仍按v2序比较half0失败，**是观察器顺序尚未适配**，未发现数值失败；已加独立wire→canonical地址函数（前1072映到6336，随后6336映到0，其余不变）。失败目录204317保留。

v3完整本地14例通过354816输出：`local_runs/systolic_b_datapath_20261111_204614_747656`，12层平均35316.8333，仍比R4慢约2%。初始source credits16，不能拿新额度结果替代其完整14。每个实际输出64MAC、宏无读写冲突、X组有效后读、最后ACK/取消排空通过。L01首issue1010拍，块间空隙14950，missingX8849/missingW7808，结果区等待3、信用等待0；这些重叠计数不能相加当总周期。

新响应队列下v2核心L01无抖动/预取1也通过，22386周期、tile内II64；取消5阶段、预取取消、复位、坏偏置恢复通过：`arch03_systolic_b_20261111_204648_117383_pin_mock`。

## 搬运优化已测路径

连续源读不能在同一源端完成响应并换下一读，源码队列过深会形成源读串。未改变加载源时序；新增独立`arch03_systolic_b_transport.sv`，从已验证transport复制，仅把source_reserved上限参数化，旧R4 transport文件不改。仍单outstanding、真实共享写ACK、原FIFO深度及取消排空。

| source credits | L01周期 | L12周期 | 本地目录后缀 |
|---|---:|---:|---|
| 16 | 36498 | 39198 | 204614_747656，完整14 |
| 2 | 31937 | 34307 | 205147_603029 |
| 4 | 31541 | 33437 | 205148_259065 |
| 8 | 35516 | 37860 | 205148_989491 |
| 3 | 31339 | 33235 | 205335_350135 |
| 6 | 33103 | 35085 | 205336_070233 |

全部两层输出一致，prefetch1/jitter0；选3作为当前B默认，尚需完整验证。credits4的L01/extremes×prefetch0/1+jitter1四任务通过：205336_700158。现有小摘要合并在`SYSTOLIC_B_V3_INTEGRATION_20261111.json`，3/6/jitter4尚待追加。

## 当前仍在运行的本地任务（不要修改其受测RTL/TB/脚本）

已将B transport、accel、datapath TB和runner默认设为SOURCE_CREDITS=3，之后新启动：

- **exec session64478**：v3/credits3完整14，prefetch1/jitter0。
- **exec session74926**：v3/credits3 L01/extremes×prefetch0/1、jitter1。
- **exec session71074**：新core v2，READ_LATENCY2、prefetch0、jitter1，L01/extremes/rounding各无复位3任务。

先poll这些session并核摘要/源码未变；不能把启动当通过。其余本地session均已结束。

## SAIF核查目前范围

只读发现VCS2020.03-SP2-6有`etc/ucli/saif.tcl`和`linux64/lib/libmxsaif-0.a`。VCS doc/UserGuide仅examples-pdf，没有完整用户手册；help_vcs无saif条目，示例中未找到toggle_report。PT2022.03-SP5-1已安装`doc/pt/man/cat2/read_saif.2`及html手册。pdftotext=/bin/pdftotext。不能据这些文件存在宣称SAIF采集已验。

当前VNC cwd为e11包、workspace3空闲shell。**最后已type b_saif_ucli2.txt（读saif.tcl第18..36行），尚未按Return**；下一步可执行这条已准备只读命令并截图。20:55综合查询已完成。不启动新的VCS/PT直到原综合释放锁；小SAIF夹具、R4 L01与VCD≤1%交叉核对尚未实现/运行。禁止盲开大VCD。

## 未完成和下一步

1. 收原综合99451终态/严格时序/面积/220宏审阅，不覆盖运行包；新v3仍需自己新综合。
2. 收3个本地任务，选定credits3后补v3故障/取消/READ_LATENCY2与v2兼容、debug。v3本地ASIC未验，不能继承e11。
3. **固件仍只v2**：main_systolic_b从metadata[0:1]取shift/length，常量layout2；必须适配metadata[2]的明确layout、配置校验/mail8。build/metadata_image/manifest、systolic_b_soc、data准备、生产monitor也尚只v2；不能直接打新正式包。建议独立systolic_b_data支持2/3，不改R4数据工具；同一firmware运行时明确选择布局。
4. B CPU恢复/竞争、batch1200、gate、SAIF power/finalreport仍未独立适配。先验证主体，再收敛工具及冻结。全部交付需同一冻结配置、自己的1200/门级14/活动12，功耗未知覆盖明确保留。
5. 默认credits3源码未提交，e11云端/服务器不变。下一可恢复点提交并同范围push，再新包/FileZilla上传，当前不要复用e11 PASS。

ABI文档已经更新能力及v2/v3范围；debug TB未知layout测试改为4（原3现正式支持）。旧R4源码/固件/运行证据没有修改。所有失败路径和历史大文件保持。

## 保存后增量

`b_saif_ucli2.txt`已按Return执行，下一步截图读结果，不要再Return重复。VNC仍workspace3 shell。

本地session74926已完成：credits3/v3/L01/extremes×prefetch0/1/jitter1，4任务101376输出通过，目录`systolic_b_datapath_20261111_205544_924353`。session71074已完成：READ_LATENCY2/v2/prefetch0/jitter1三种数据各ABA，9任务228096通过，目录`arch03_systolic_b_20261111_205545_606610_pin_mock`。

session64478仍运行，已通过L01–L09；对应周期31339、30735、30423、30491、30079、29775、29423、29511、29419。继续原session至14终态，勿改受测RTL/runner/TB。尚未更新其余证据JSON/STATUS为上述完成结果，下一步收齐后统一追加。

## 21:08增量：选定credits3的v3完整14通过，固件与工具已适配

session64478已完成，`systolic_b_datapath_20261111_205544_253173`：14例354816输出通过，12层平均**30502.333333周期 / 4917.656573task/s**（本地pin_mock，非ASIC），比R4吞吐约高13.49%。L10/L11/L12=30215/31383/33235；extremes38337，rounding33707。已经把所有credits探索和新latency2/反压摘要纳入SYSTOLIC_B_V3_INTEGRATION_20261111.json。

当前默认credits3的新硬件另通过：

- v2完整14：`systolic_b_datapath_20261111_210059_312447`，354816输出，session82591结束。
- debug extremes/rounding：`systolic_b_debug_20261111_210100_044386`，50688输出，未知layout4拒绝，单读适配/响应保持，session22456结束。
- v3生产monitor+metrics fixture L01/extremes：`systolic_b_monitor_fixture_20261111_210338_469481`，50688输出、真实源/共享写/输出计数通过，明确NO_CPU。首次210321因TB漏声明layout_arg编译失败，已修复，失败目录保留。
- v3错误恢复L01×prefetch0/1：`systolic_b_recovery_20261111_210542_660516`，每种配置5非法配置、3响应故障、2坏流、4取消后无复位真实任务通过；总50688输出。session32379已结束。
- 独立数据准备v2/v3 L01/extremes4配置：`systolic_b_data_preflight_20261111_2104`，prepare/verify/hash/坐标核对通过。
- IRQ固件`local_runs/systolic_b_firmware_v3_20261111_2100`编译且verify_firmware通过。cfg新增layout，main从metadata[2]读取、mail8返回；驱动明确只允许2/3。metadata_image两布局/shift11/12核对、非法0/1/4拒绝、无任务预填检查及8个ELF边界测试通过。仍没有实际CPU执行。

已适配独立`systolic_b_data.py`、B soc契约schema v3、package --layout（默认3）及生产monitor的原始坐标映射/布局身份。当前可以进入新包准备，但尚未提交、打包、上传或运行v3 ASIC。旧icb32数据工具/R4不改。11项codec/synth契约单测、17个B Python文件的3.6语法检查和git diff --check通过。

**所有已启动本地仿真均已结束，当前没有本地exec长任务。** 新v3 READ_LATENCY2加载重叠、实际CPU恢复/竞争、B1200、gate/SAIF/PPA仍待做；latency2已通过的是v2核心，不偷换为v3通路。下一步先保存提交/云同步/新包，原综合保持串行。

VNC最后已执行`b_synth_health.txt`，截图`takeover_local/b_synth_health.png`已生成但**尚未读图**。下一步先view此图。新的`b_saif_usage.txt`已在本地准备，未type；它读取VCS saif.tcl 255..280行Usage/Start帮助。SAIF定位最新：文件366行，_manSaifUsage256、Start271、Stop281、Reset290、Report299、Region331、Examples344。仅只读定位，尚未跑SAIF。最后终端无待执行输入，workspace3 shell，FileZilla关闭。

## 21:12增量：新v3已提交/云核对/打包，开始板端暂存

新提交 **63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86**（36文件）已push团队私人原分支，并ls-remote独立确认。原R4文件未修改，e11运行包不变。

不可变新包`light-light126-systolic-b-v3-20261111_211137-63da6ba0d6d9.zip`，**11197550B / 663文件 / SHA3433af44f5f80ec6c3b2d78a2a90accbf16d67dcd1312af981ef4045f391d0f2**。package从已提交LF源码重编IRQ固件并核验全部归档条目，session81354已结束。已发起ac820 upload到`/opt/ac820-gui-root/root/`同名包；**尚待查看该tool结果及板端SHA**。FileZilla仍未打开，新v3尚未上传比赛服务器/解包/运行。

21:09:28原综合健康查询已读：driver99451运行45:25、DC108110运行39:50、CPU99.7%、MEM3.1%，log23763B/mtime20:31:06，尾部仍Processing B核心。没有停止或重启；不能因日志长时间静默判断完成或失败。最后VNC为已执行的SAIF Usage查询，workspace3 shell，无待输入命令。
