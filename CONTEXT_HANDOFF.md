# C32-A服务器交接：竞争固件修复准备中

**最新22:33：C32修复包initial03已启动（PID238916，22:31:59），22:32:59正在ASIC14。** 恢复23已完成575文件/31.82MB归档回读清理，所有.so及实际证据保留，两份压缩包核验通过。禁止再执行清理。后继只读检查此队列，详情见C32_SERVER检查点最顶部。C32自己的综合/240/门级/功耗仍待完成，不能提前进入C32-B/G32。

**最新恢复入口（22:27）：** 先读 CONTEXT_CHECKPOINT_20261116_C32_SERVER.md 顶部。恢复23在VCS共享对象链接检查时安全退出，未归档/删除；initial03尚未启动。修复9a48632保留全部.so及链接，待部署新ROOT/r4_metrics_recovery23_fixed.py，不能重跑旧脚本或恢复22。新脚本SHA 45b5e51ec22494371b0674b81d29589622b2a01e69cd83635d2a78c81023c6c7。VNC workspace3第一终端空闲，旧会话33837等均已结束。

## 22:17 实际元数据探测亦ENOSPC；小范围恢复23工具传输中

metadata工具55447传输完成并执行；22:12:43在新探测目录mkdir时报ENOSPC，尚未创建目录、协作锁或initial03。ROOT/c32_initial03_metadata_probe.json保留失败回执，不能再运行同一probe工具覆写它。用户明确回复没有团队正在向共享盘写入的任务。本轮没有额外数据清理，91135f6包仍完整。

22:14:27只读确认旧R4 metrics14已通过：PROJECT/bundles/light-light126-icb32-r4-20261111_043048-96443c284a1c/runs/icb32_r4_finish01_metrics14/icb32_soc，summary SHA bb0ee4cf23b31730d72c196bfc5101f3d2f49e7d1dea33b49e366a72de54e576，stage与summary绑定、14例ASIC通过。其生成输入/编译缓存578文件48520513B；实际CSV/日志/JSON/源码/网表/SAIF都排除。

新 C32_R4_METRICS_RECOVERY23_20261116.py（提交1d566a3，SHA b444d190cb76fb81d12f06b5137323bc0e7138a587e14ffa671d63e2b7d6b0b7）先独立归档上述精确文件并全成员回读，重核源和进程，再删除可恢复副本。完整压缩包留ROOT/r4_metrics_generated_recovery23，并另核验持久副本 PROJECT/backups/r4-metrics14-generated-20261116_2216。所有非选中文件前后hash保持。尚未执行23。

成功后工具立即生成并调用新 C32_QUALIFICATION03_RECOVERED_LAUNCH_20261116.py，SHA f40276324f849b6a9eff62bb8f1841fb47487c424c57c696924d0d2f8b8918c2；与已有metadata启动器仅更换新的probe目录/回执身份，不改既有文件。新探测目录 PROJECT/c32_lock_metadata_probe_20261116_2216、回执 ROOT/c32_initial03_metadata_probe23.json；通过实际32768B写入后原锁启动initial03。新运行仍全部写/tmp，完整验收条件不变。若23失败先读原状态，不能重跑删除。

**当前GUI会话33837只传 recovery23_tool.b64。退出前不可追加键盘输入。** 完成截图 takeover_local/c32_recovery23_transfer.png；然后核验源码SHA并显式启动后台，保留launch/log。current initial03尚未创建。原22已完成不得再跑，T80/旧八路及所有冻结备份继续保护。最新工具提交1d566a3及ee094bd文档尚待push，最后已push3143002。


## 22:10 新包已准备，initial03被共享空间阈值挡住；准备实际元数据探测

两工具传输24760已退出并核验。prepare完成，新包 ROOT/light-light126-c32-91135f6 共1081输入，manifest SHA d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7；完整payload SHA bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc，服务器打印确认。旧包未改。文件为 ROOT/payload_91135f6.json 和 light-light126-c32-91135f6.prepared.json。Git修复及证据已push3143002。

22:05:30执行已部署c32fix_launch03_tool.py时在共享>=64MiB启发式检查停止，尚未创建initial03的请求、队列、日志或启动回执；没有硬件作业。此前initial02失败SHA守卫已经通过，证明0acf...终态抄录正确。原启动器仍保留。用户22:07回复没有团队正在运行的共享盘写入；不能推断具体是哪一个其它账号导致空间耗尽。

22:08:15只读du已结束，第一终端回到提示符。旧R4包剩余944357376B，其中原批量目录约627MB主要为应保留的实际输出与证据，metrics14约63.76MB；此后没有删除任何文件。不再重跑归档21或恢复22。

所有大型C32产物都写私有/tmp（约78GB）；共享只写原锁owner。为不以额外64MiB阈值代替实际可写性，本地新 C32_QUALIFICATION03_METADATA_LAUNCH_20261116.py（提交0f3ffa8，SHA 60da852cc133dbb5001f9f15d273f487a455aec9719e7fb96ce9d189a9b122ee）将独占创建 PROJECT/c32_lock_metadata_probe_20261116_2210，写32768B并fsync、回读，然后只删除刚创建且身份仍匹配的探测文件/空目录。原协作锁不改变；实际队列仍通过原ProcessLedger原子申请锁，/tmp运行容量及所有源码/数据检查不变。

探测回执 ROOT/c32_initial03_metadata_probe.json 用独占创建。若失败，尚未启动队列，先读失败信息，不能盲目再次运行同探测工具，因为回执/路径不覆盖。探测成功后继续同一新包initial03。源元数据检查不是缩减功能、时序或活动验收条件。

**当前GUI传输会话55447只在输入 c32fix_launch03_metadata_tool.b64（4464字符），未退出前不能另发VNC键盘。** 完成截图 takeover_local/c32_metadata_launch_transfer.png；然后解压为新py、核验上述SHA，使用prepared回执机器取manifest后执行。此刻尚未执行探测，initial03仍未创建。新元数据工具提交0f3ffa8尚待push，旧结果/保护目录不动。


更新：2026-11-16 22:02，北京时间。恢复先读AGENTS、本检查点、有效计划和STATUS；当前不是旧摘要里的“正在综合”或“仍因共享盘满未启动”。

## 当前目标与保护

用户持续授权实施 T80→S0→P80→C80→C32-A/可选B→G32，最终32 PE、150 MHz/6.666666 ns、SS/.99 V/125°C，项目保守面积≤1.00 mm²。X14/W12/acc32/total33/SHIFT10不变。原32位ICB，源读→共享写成功ACK→原总线读回→解码→计算→最终写ACK并排空，不允许旁路。

**服务器桌面T80_Delivery_20261113、所有旧八路、P80/C80冻结运行与备份不能修改、移动或删除。** 本轮正式批量仅20×12=240；完整100未自动授权。阶段完成后再进入下一阶段；没有子代理。持续推进并同步私人GitHub；不因等待自动结束任务。

有效计划 workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md，SHA 1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。早前全部过程在 CONTEXT_CHECKPOINT_20261116_C32_START.md；根旧正文另存 CONTEXT_HISTORY_20261116_C32_2202.md。

## 已完成阶段和本地C32

S0/P80/C80已正式冻结，不重跑。C80标签 arch03-c80-codec-20261116-1930，冻结回执 C80_FREEZE_20261116.json，报告 workspaces/arch03/C80_STAGE_REPORT_20261116.md：固定12均70603.1667周期/2124.5505985 task/s，保守项目面积0.9611361367 mm²，setup+0.000216007 ns、hold+0.00623399 ns，220宏，时间加权55.3675891 mW/26.06084485 µJ，自己的ASIC14/恢复/竞争/240/精度/门级14/SAIF12/PT12与独立模型结论、持久归档完成。布局前限制保持。

C32-A受测RTL自61246bb2a21c56a9bfd871fd68de93028d79f5fd未改：2×16、32 PE，两32项结果区、32转换器、10位块号、800块、尾row98单行；X60个/W32个小宏，仍23 KiB。布局0x00100006、硬件ID0x4b57530d、能力0x000b02bf。原C80编码/源信用3/32字FIFO/事务队列深度2不变。

本地10000随机+32定向块317824输出、完整14例354816输出、两拍SRAM预取0/1 A/B/A六任务、恢复fixture、固件/观察器及54工具检查全部通过，范围见 C32_LOCAL_INITIAL_20261116.json、C32_LOCAL_QUALIFICATION_20261116.json、workspaces/arch03/C32_LOCAL_BRINGUP_20261116.md。不重新运行这些已完成测试；固件修复另验证。

## 服务器运行与失败（必须保留）

ROOT=/tmp/s4_21usr_c32_20261116_2010，0700。

旧C32包 ROOT/light-light126-c32-61246bb，1081文件manifest SHA 0b12bff8f9d989e83eb48d4bd5e62185852edf592e442d3bccbdb1070fc849cc。全payload ROOT/payload_61246bb.json SHA 40fed77e347aad1347f1998f19801652770b176c5f5e0e03f405d68d0a11c602。此包及其运行原样保留。

- initial01/PID177134在创建共享锁时ENOSPC，零子任务失败；不能重启。
- initial02/PID205526于21:44:35.190599启动，21:52:48.406007在contention失败，所有子进程已排空，21:57:43确认父进程不存在且原协作锁不存在。
- **initial02的ASIC14和恢复通过。** ASIC摘要SHA 859eea742125cb9c0af818107b913e7946b1c22ceaf9beef0cc881ce85ea1580；恢复摘要SHA 3f67bf80d74ed883f8b6e5bca7e0274a74521a8761fe971505bbd77608d90d3d。21:53:37已机器断言两摘要与实际文件一致。
- 固定12完整周期 [74750,73187,72186,72264,70798,69193,68427,68604,68610,70970,75393,81770]，合866152、均72179.3333，150MHz折算2078.1571826 task/s。同逻辑数据且同C80编码，吞吐比C80低2.18368%。极值57532、舍入56822。不是芯片实测，也不是最终PPA验收。
- 初始证据 handoff/team/evidence/C32_ASIC_INITIAL_20261116.json。此文件描述21:52:12通过部分和当时运行状态；随后发生下面的竞争失败，不能据其旧queue_stage推断仍运行。
- 失败终态 ROOT/light-light126-c32-61246bb/runs/c32_initial02/state.json SHA **0acf9538cd1faa74d4b63f273f6053a4f42eb79fc4800e09cb9d4663a9b3b1e9**。队列status=failed、stage=contention、completed=['soc','sequence']。
- 错误是竞争固件启动前拒绝参数：monitor报 magic=bad00002、rc=fffffffc(-4)、count=0。根因 main_c32_contention.c 第34行遗留 metadata[3]!=5u；新包实际metadata为2。没有执行到DMA任务，不能归因于总线仲裁或MAC。
- 竞争、综合、240、精度、门级/活动/功耗都未完成；C32-B/G32未开始。

## 已修复内容与正在传输（先处理此处）

本地修复提交 **91135f61c97c980039793c6637d0a06888638df0**，只把上述5u换成KWT_ICB32_ROWS；生产RTL、IRQ性能固件及恢复固件所有字节不变。新竞争固件 local_runs/c32_fw_contention_fix_20261116_2156 已重新编译并核验。不要覆盖旧firmware_contention。

新完整payload在 local_runs/c32_fwfix_20261116_2200/payload.json，SHA **bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc**。114成员中仅6处改变：main_c32_contention.c和竞争固件build_command、driver.elf、manifest、shift_10.bin/verilog。新source_commit=91135f6。未改RTL，未新开发架构。

精确前后缀差分 patch02.json SHA **115050d5f291747f25ff822abdbb1d3662d9e4b344cdf5587cba8708c680a489**，base64 3760字符、6成员；本地完整重建逐字节相同，旧/补丁损坏拒绝通过。早先23976字符的完整patch仅本地未上传。服务器 **contention_fix_patch02.b64已经传完**，会话9664退出，不能重复传。

**当前GUI会话24760正在传两份工具，未退出前不可再发VNC输入。** 目标 ROOT/c32fix_prepare_tool.b64、ROOT/c32fix_launch03_tool.b64；完成后自动发送结束行并截图 takeover_local/c32_contention_fix_tools_transfer.png。此时未执行prepare或initial03。

工具（均在handoff/team/evidence）：

- C32_CONTENTION_FIX_PREPARE_20261116.py，SHA **5f31ca5abed929adaaa69f17caab1307843e1d2bb28ca4065b5ab62b8e84c6a6**。先核原payload及补丁，严格只允许6文件，生成新 ROOT/payload_91135f6.json，再复用已核验 ROOT/prepare_61246bb.py 从冻结C80源复制 **ROOT/light-light126-c32-91135f6**，不继承旧运行。该新包尚未创建。
- C32_QUALIFICATION03_LAUNCH_20261116.py，SHA **8f595d8c4ab34702e3cd32ac420e69dad969cdfa7cb75884986b11b6fca2b34f**。绑定initial02已退出失败终态及新payload，显式参数 --manifest-sha256。新包核验后启动独立c32_initial03，顺序soc→sequence→contention→synth→batch20→precision。仍使用原共享锁。旧initial02不可续跑。
- 新启动器最初仅日志标记写INITIAL01，已在传输前改INITIAL03；当前SHA以上为准，早先3322...无效。
- 旧finish启动器绑定612/initial02，**不能用于新包**。initial03运行后再准备对应911/initial03的finish工具；它只能在该队列成功退出后启动自己的门级/SAIF/PT。

工具已经本地Python3.6语法/CLI/重建与损坏拒绝检查。当前修复提交及新工具/文档尚待git提交推送；最后已push4a609e7。历史未跟踪S0_SYNTH05_FINISH_LAUNCH_20261115.py不添加、不运行。

## 空间恢复：已经完成，严禁重跑删除

旧B0cleanup19/20分别精确清理481632614B、98453710B，完整B0备份保留。旧R4原始VCD早已gzip核验并删除重复原始，唯一7GB gzip不能再删除。

归档21逐文件核验49200个旧R4任务生成.hex/.bin/.verilog，原始2639224198B、gzip508256874B。ROOT/r4_generated_archive21/receipt.json SHA 1b8ae10a78a0fb8f094ff34d55fc0e245bb4ed4b7c3fd17418cbb813b3e5e6ef。旧结果CSV/日志/JSON/源码/网表/SAIF均不动。历史R4 identity哈希抄录第8/9字曾倒置，依据原summary绑定修正；首次失败归档零输出，保留记录。

recovery22/PID202397已退出并完成精确清理全部49200副本，私有/tmp归档保留，持久副本在 PROJECT/backups/r4-generated-inputs-20261116_2135，三文件SHA/字节数核验通过。PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109。

- recovery22/state.json SHA **dae7017bafacdd32784772b70ddcf8fc133c652a62a82b51c67810a0b2672e97**。
- persistent_copy.json SHA **f6c223bfd1ec66b8d96a4cb458eff7eba3b0eff52cecb8a248ba1f38a6e53bac**。
- followup.json SHA **2c2a85f4accffae49109014ac47365f05cce75c030f390c0550c322159bb9f4f**，returncode0。
- 本地早先两处回执哈希人工抄录倒序，已通过逐字符差异纠正，21:50:46机器断言通过；见 C32_SHARED_SPACE_RECOVERY22_20261116.json。不得使用旧错误哈希。
- 21:45:30共享约1.40GB、/tmp约78GB；之后仅只读，当前空间须重查。不能继续删已清文件或任何保护目录。

## 操作与恢复入口

仓库 E:/fpga_race-two/kwt1-c32-g32-20261115，分支 codex/light-light126/t80-pipeline-c32-g32-20261115；Python E:/fpga_race-two/.venv-kwt/Scripts/python.exe。Windows原生shell对中文Python stdin两次编码失败，未改文件；中文文档用apply_patch写UTF-8文件，再用ASCII Python读取。

Linux板控制 F:/linux_fpga_try/ac820.ps1，须读该目录AGENTS和computer-use skill。当前VNC窗口18874435、workspace3第一终端；workspace4不操作。不能并发GUI键盘输入。每次传输/异步后台命令后确认真正回到提示符，截图可能早于最后几字显示。

FTP旧DNS约束仍保持，不绕过；继续通过可见VNC。type每次≤1000字符，通常900；Python源码分段时不能在中途额外插入换行。所有长命令进程必须先poll，不能把命令打进未结束的cat或Python。

下一步：先poll24760并读截图→核验解压两工具→执行prepare创建911新包→从prepared回执机器取manifest并校验→显式启动initial03。若任何前置失败，保留原目录和日志后查原因，不改已冻结源、不跳过守卫。随后沿计划当前C32-A阶段继续，完成再进入可选C32-B和G32。
