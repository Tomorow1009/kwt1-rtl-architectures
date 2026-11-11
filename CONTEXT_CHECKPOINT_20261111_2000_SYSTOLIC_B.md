# 2026-11-11 20:00：B基础v2本地通过，继续实施

## 有效要求

压缩后读AGENTS.md、CONTEXT_HANDOFF.md、本检查点、workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md。直接5×16脉动B，A取消。H0=19:30:41，11/12 08:00功能收敛，硬冻结11/12 09:30:41，11/13 17:00交付整理。用户要求持续工作，不能完成文档就停下。旧R4保持冻结退路。

## 已完成本地实现与验证

新增arch03_systolic5x16、arch03_linear16x5_systolic、arch03_systolic_b_accel。80个输出驻留PE、首末项/块号同步、60X+32W宏、带延迟标签的读响应、两个80项预约结果区、80路原requantize、每拍相邻双结果、原32字DMA FIFO及真实共享写ACK发布。先支持v2全X装完计算。ID=4b575305、cap=0003053f；单结果debug用半字适配器；v3明确拒绝。旧R4 RTL和固件未改。

以下均是本地pin_mock或整数阵列，不是E203或服务器验收：

- 独立阵列14块1088点积、II64、暂停/取消/复位通过：local_runs/systolic_array_20261111_193632_505682。
- 缓存核心首层无反压22385周期，tile内块启动间隔64：arch03_systolic_b_20261111_194406_322470_pin_mock。
- 核心14例354816输出、随机加载及191拍长反压、取消5阶段/坏偏置/复位通过：arch03_systolic_b_20261111_194523_407101_pin_mock，摘要35540139b83f562c140fc4455365c5afe2c8e26fb330d233e78fcbfd402d604f。
- READ_LATENCY=2、无预取，L01/extremes/rounding各A/B/A，共9任务228096输出通过：arch03_systolic_b_20261111_194523_406101_pin_mock，摘要26fb5ba83389d840bf3a47e219fc8cbaae2c26031cd913d53664d6cf41909a74。
- 完整DMA名义14例354816输出通过：systolic_b_datapath_20261111_194820_275882，摘要792dfb4cffd9ef6367c9b20b0b595247184bb5306143cb98d00edbf501fe11de。12层平均36862周期，按150MHz折算4069.231task/s，比R4的34616周期慢，不能称优化收益。
- DMA等待L01/extremes×预取0/1共4任务101376输出通过：systolic_b_datapath_20261111_194820_932395，摘要26c0b4b12c5339489160f2169e71adab4cc1f3ce9a2f6309e9e84fc8d3a9014a。最后写ACK等待及无复位取消排空覆盖。
- L01故障恢复通过：systolic_b_recovery_20261111_195601_987997，摘要af187d2f008699c4fd304d721a903fc57de84b99d172fc62512bd7a843140ec4；5配置拒绝、3类响应错误、4取消阶段、2格式错误、恢复后25344输出。
- 生产观察器/被动计数fixture L01/extremes共50688输出通过：systolic_b_monitor_fixture_20261111_195602_701203，摘要8583caa9bf3ce379748e35276f542fd7603cb8a5e6f09986b78088a951fe5f86。L01源37428B/37091周期，X读101376写6336、W读327680写16384、实际MAC1622016；fixture明确NO_CPU。
- 单结果MMIO debug extremes/rounding共50688输出通过：systolic_b_debug_20261111_195853_751815，含响应反压、v3拒绝、debug不发DMA、饱和计数及坐标。

新增独立B固件源/build、installer、soc、synth、metrics、package。server_run只添加B build/soc/synth分派，旧stage不改。IRQ/WFI固件local_runs/systolic_b_firmware_20261111_1953编译及源码/映像身份复核通过，shift11/12，无ITCM任务数据；尚无CPU执行。220宏/面积/时钟模板3项本地检查通过，不能代替综合。所有已启动本地session均结束，无本地长任务。

## 未完成与下一步

尚未提交、打包、上传B；未实际ASIC/E20314、IRQ/WFI/竞争/恢复，未新综合/STA/面积、B1200、门级、SAIF/功耗。新v3编码/早启动均未实现；基础v2正确但慢于R4。B gate/batch/CPU contention/sequence/final report仍需独立适配，不能复用旧R4 PASS。当前B soc禁止普通VCD activity，SAIF需实际工具验证与R4 L01交叉对照。

下一步保存/提交这个可恢复点，同范围云同步并导出B首包；服务器先核其它进程及工具，再串行ASIC14/综合，同时准备v3/按宏逐元素仲裁/提前启动。不能续旧8路或R1队列；不能删历史证据。B不合格仍交付R4。

## VNC与服务器最新实际状态

用户先要求不在workspace4操作。19:48看到4传输终端；CtrlAltLeft未切换远端，随后点击Workspace3成功。19:52工作区3只读查询被传输程序的STATUS输入插入，shell报Unmatched quote，查询未执行。停止VNC后尝试只切回4被自动审批拒绝（可能改变传输焦点、用户要求不在那里工作）；点击没有执行，未绕过。

用户随后明确回复“传输已完成，可以恢复VNC操作”。已重新盘点/观察，确认工作区3空闲shell，cwd=/storage1/admin_public_dir。20:00:01.577083实际查询：旧mmio8_fullpower_l02_v2 passed，结束15:17:11.637795，PID323693无进程，摘要736f0b5a7f6864410fc92d147a44d5549cde516c22bac1626376b98b6dd752ed；协作锁不存在，free148.094GiB。其它进程还未列表检查。没有重启任何旧任务或新B任务，没有删除任何数据。最后截图E:/fpga_race-two/takeover_local/b_resources_final.png。FileZilla未启动。

板端helper F:/linux_fpga_try/ac820.ps1，当前VNC20971587/800×450。每次观察焦点再输入，不用Up历史。type先等完成再Return。命令文本在E:/fpga_race-two/takeover_local；只能既有板端/FileZilla/VNC通路，不开隐藏比赛服务器通道。普通sandbox读板端私钥元信息WinError5，用已批准前缀提权调用，不读取或输出凭据。

## 保留的失败尝试

array runner相对__file__改resolve；首个cached core调用误指不存在prepared/tile8在编译前失败；文档默认GBK读取失败改UTF8；复制面积测试时误将RAMSP4096改4092只影响测试夹具，已修正3项通过。20:01一次大段中文PowerShell→Python stdin更新检查点因UTF8解码失败，整段未执行，改apply_patch保存此文档。没有发生RTL数值失败。所有失败目录保留。

## 提交、云同步及上传增量

基础B已提交 **e11c317c960b18fb60ecbaddf9449f2ff00448be**，38文件。已正常push指定私人分支，并ls-remote独立确认相同SHA；不是仅本地提交。完整小型本地摘要已入库handoff/team/evidence/SYSTOLIC_B_LOCAL_20261111.json。

首个不可变包local_runs/light-light126-systolic-b-v2-20261111_200441-e11c317c960b.zip已生成并逐文件校验：**11172059B、655文件、SHA fe3c47b4276ccb91bddd084b90e58133cc5b8300e5b45f0871437e6a8bf1330b**。从Git导出LF字节重编IRQ固件，包内不含库/凭据/聊天。package session99731已结束。

已板端upload并独立SHA核对，暂存/opt/ac820-gui-root/root/同名ZIP；复制到/home/root/systolic_b_v2_e11c317/，GUI路径/home/board/systolic_b_v2_e11c317/。BusyBox cp不支持-n第一次失败（仅mkdir成功），改先test目标不存在再cp正常，无覆盖。

Linux FileZilla已打开并经现有IC-single-connection站点成功登录；主窗口**23069254、1198×645、class Filezilla**。密码仅用现有受保护文件内部输入，未输出。远端明确选择**/IC/light-light126-undergrad-d2-20261109/**。已选本地唯一11.2MB新包并按Return发起上传，**当前尚未截图确认传输完成**，不要重复发起。下一步先截图检查队列/成功项，成功后Ctrl+D/Q正常断开关闭，再核服务器包SHA并安全解包。

VNC最后仍工作区3shell /storage1/admin_public_dir，但现在被FileZilla覆盖，关闭后重新观察焦点再输入。还没有在服务器解包或运行B。文件传输涉及的本地exec70359已正常结束，没有本地pending session。下一轮继续先读本计划和此检查点。

## 20:16增量：上传/安全解包/655输入和固件核验通过

FileZilla实际成功11.2MB、22秒、队列空，已Ctrl+D/Q关闭并windows确认消失。服务器经原已校验unpack.py安全解包，回执UNPACK_HASH_PASS，目录为上述根的bundles/light-light126-systolic-b-v2-20261111_200441-e11c317c960b。**不要重复上传或解包。**

工作区3 shell现cwd为新B包。已实际运行server_run.inputs和systolic_b_soc.verify_firmware：655文件及IRQ固件ID4b575305均通过，LOCK False。随后的ps列表解析因空行IndexError失败，未启动任何作业。已输入并按Return执行修正版b_process_tools.txt（加len>1），**下一步截图读取结果**，再启动B自己的systolic_b_soc/新session。尚无ASIC作业身份。工具查询和包验证均只读，未清锁或停止其它任务。

根交接指向本检查点；当前只新增检查点文档未提交，e11c317受测硬件不改。所有本地仿真和打包session均已结束，VNC20971587工作区3，没有FileZilla窗口，无CUA会话欠completion_summary。

## 20:19增量：首个B真实ASIC14已启动，禁止重复

20:17实际只读检查EDA_PIDS=[]、LOCK=False。工具VCS=/eda/synopsys/vcs/vcs_2020.03-SP2-6/bin/vcs，DC=/eda/synopsys/dc/dc_2022.03-SP5-5/bin/dc_shell，LC=/eda/synopsys/lib_compiler/lib_compiler_2022.03-SP5/bin/lc_shell；PT路径未核。

已执行b_asic14_launch.txt，启动 **PID87707 / session systolic_b_v2_first01 / stage systolic_b_soc**。包根为上述e11c317，运行目录runs/systolic_b_v2_first01/systolic_b_soc，launcher日志runs/systolic_b_v2_first01_launcher.log。20:19截图实际看到锁owner PID87707/host RDserver04/bundle新B/session匹配，尚无child_pid，launcher tail为空；state内容因屏幕滚动未读到，不据此宣称编译或案例通过。

下一步用紧凑字段查询state、PID存活/CPU和实际日志，不要重启或改运行包。本地v3尚未开始。当前VNC工作区3为新B包shell，原查询已结束；没有前台监控或悬空工具session。FileZilla保持关闭。

## 20:24增量：B真实ASIC14通过，新综合99451已启动

原systolic_b_v2_first01于20:20:50.929163自然完成。独立重读summary及state并核对摘要一致：14例、354816输出、IRQ/WFI全部通过，12层平均36862周期（150MHz折算4069.2311866task/s），各例仿真宿主耗时合计45.297351秒，不含编译。截图b_asic14_verified.png保留摘要，完整SHA以服务器原文件为准，尚未回传完整JSON。此证据仅对应e11c317 B/v2，不转移至未来v3。

确认旧锁释放后已启动新session **systolic_b_v2_synth01 / systolic_b_synth / PID99451**。包仍为不可变e11c317。20:24:19截图b_synth_started.png明确B_SYNTH_STARTED 99451。运行目录runs/systolic_b_v2_synth01/systolic_b_synth，launcher为runs/systolic_b_v2_synth01_launcher.log。不得重启综合。下一步读取原作业状态，继续本地v3与SAIF准备。B CPU竞争/恢复、1200、门级、功耗仍待办；旧R4不重跑。
