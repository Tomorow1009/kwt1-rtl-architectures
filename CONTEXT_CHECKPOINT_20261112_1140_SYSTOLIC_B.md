# 2026-11-12 11:40 起：B综合完成，修复验证工具

继续直接5×16脉动B计划，A取消，63da/Bv3/credits3已冻结，R4保留交付退路。重读AGENTS、有效计划、本检查点及08:30检查点。仍仅按授权删除旧MMIO8 L09–L12四VCD（112.42GiB）；R4/B受保护。

## 新综合完成，不得重跑

8d包`runs/systolic_b_v3_synth02/systolic_b_synth`完成，摘要SHA `3e0f88eeb4855a15f8743f820f587cd90df7e52a748d112e8fd5ba788dd86d03`。

- 周期6.666666ns；setup +0.0002141ns、hold +0.00249085ns。
- 92小宏+128大宏=220；锁存器0；最终组合环检查未检出环。
- 整机4621339.604708µm²；已识别新增0.9383510023010567mm²；含全部整机标准单元的保守预算上界1.0991231047009615mm²，低于2.00。
- 工程时序/结构审阅和门级仍待，不能直接称最终合格；物理签核未验。
- DC CPU6685s、elapsed6780s。旧synth01 ENOSPC失败现场仍保留。

## validation02与结构审计失败，均非新硬件失败结论

validation02在10:44:54启动sequence（PID1723），0.3秒后被`Sequence cases must exactly match firmware A/B order`拒绝；未运行仿真，也未启动contention、SAIF、timing或gate。队列没传--cases而默认14例，序列固件要求A=layer_01、B=rounding。

本地已改队列从核验后的固件manifest读取A/B顺序并显式传入，不放宽CPU检查。新增队列回归3项通过：两种A/B顺序、必需失败停止、可选失败保留并继续gate。子进程为替身，不是硬件证据。

旧8d结构脚本在实例扫描时报`Duplicate mapped instance .rst`，在写结构JSON前退出；不能记录成结构通过。原正则把命名端口连接续行当成实例。本地已改成两个合法Verilog标识符及行内空白，支持DC转义名，保留真实重复拒绝；2项定向测试通过。新的工具包待部署后对原网表重审，不修改网表。

## 现场和下一步

monitor因queue失败自行退出；VNC18874435/workspace3、新8d包shell，FZ关闭。没有活跃EDA或本地仿真（部署前仍须重查进程/锁）；最近154.744GiB是10:44历史值，不是实时空间。

result_ready和structure_ready均已执行；前者已读取，后者失败无JSON。网表误解析只读定位查询已Return，需看`b_structure_parser_actual.png`。timing_ready尚未输入。不要重复任何launch。

先提交本地工具修复和记录，生成新不可变包，验证生产RTL/三固件不变，FileZilla上传新目录。新validation03绑定已完成的8d synth02，不再综合，不重试旧session。之后新B实际sequence/contention、timing/gate14、冻结审阅、干净ASIC14及1200/30412800输出、SAIF/R4交叉核对、B活动12/功耗12。

原B ASIC14/354816仍通过，30502.3333周期/4917.6566task/s。新B自己的1200和功耗仍待。最后已核云端b79e1f52504f123505ab408df018c9e0a8d2b4d5；当前修复尚未提交上传。生产硬件、固件和约束均未改。

## 12:07增量：新工具包已部署，validation03实际运行

- ced0e139a01ee810ea4f98e43cd703ff6fccf2f0已push并ls-remote一致。一次Git TLS握手临时失败后重试成功，未改TLS设置。
- 新包`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`，ZIP11358423B，SHA9995decabb854511e5e92e392b8319207f79731681f44cf1c7ed91406d12b579；709输入，manifest39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d。全部ZIP输入重核、无pyc缓存；服务器已安全解包/709输入/三固件检查通过。FileZilla22秒上传成功、队列空；已断开关闭。
- 67个RTL/SW/固件受保护文件核对：生产及contention固件完全一致；sequence的实际bin/verilog加载字节一致，仅ELF的.debug_info/.debug_line/.debug_str/.symtab四个非分配节变化，manifest仅elf_sha256更新。新sequence manifest97ec7c557782cde45d93cd313c5e7c20cdbf491791fb1856e4182806d7241c0d；生产仍11d860ca。最初全ELF逐字节等同断言失败后已逐节定位，不虚称完整ELF相同。
- FileZilla起初在板端外层shell启动找不到命令，随后GUI chroot启动继承了错误HOME出现空白配置；该空白实例已关闭，没有连接/传输。最终通过桌面Alt+F2输入filezilla使用正确既有站点，正常上传。下次沿用桌面启动，不重复错误启动。截图/正常密码框登录，不输出凭据。
- 12:01:31预检：无锁，同账号无EDA，旧183038/192693/184658/1723均退出；可用69.276GiB。
- **12:03:36.100240唯一启动validation03 PID102905**，新ced包`runs/systolic_b_v3_validation03_queue`，准确复用原8d synth02，绝不再次综合。12:04:37实际running sequence，child103007，无错误，可用68.813GiB。launch已执行，不可重复。
- 新结构解析器尚未服务器执行；旧结构JSON没有生成。实际旧正则误匹配片段已读：`clock), .rst(`。新版本修复保留真实实例重复拒绝。
- 共享空间持续消耗；12:05核验旧MMIO8 L03–L08六VCD共167.090201664716GiB，原摘要06e388...仍匹配、CPU/gate通过、fuser返回1无人打开。依据已有授权准备第二次定向清理，保留原8 L01/L02及所有小型证据、R4/B。
- **b_cleanup_second_manifest.txt已输入并Return，正在保存`authorized_cleanup_20261112_second.json`；清单输出尚待截图读取。b_cleanup_second_execute.txt尚未执行，六文件尚未删除。** 当前VNC18874435/workspace3、新ced包shell，FZ关闭。无本地长期任务，无待Return输入。先读清单结果，再路径/大小/占用重核并执行已授权删除；之后继续观察validation03，不重启任何作业。

## 12:21增量：第二次清理完成，真实CPU诊断通过，门级继续

- 第二次清理已于12:08:35.577864执行完成，只删除旧MMIO8 L03–L08六VCD，179411737908B=167.090201664716GiB；与第一次合计300117732486B=279.506419306621GiB。执行时再次核路径、非链接、大小、摘要和fuser；六路径不存在已独立确认。清单SHA c923e1708ea0bda863c7ddbc2bb07d833c582450073d47286689426c754be6a4；`SERVER_WAVE_CLEANUP_SECOND_20261112.json`记录。原MMIO8仅保留L01/L02波形，L03–L12未来原始活动/新功耗需重新生成；原输出/日志/摘要/网表/输入及全部R4/B保留。清理后234.6123046875GiB，12:18为232.6357421875GiB。不要重复清理命令。
- validation03 PID102905已实际完成sequence、contention、timing_audit；12:18:29仍running gate14，driver117191；12:20观察已生成case_progress，simv子126389，已完成的某用例宿主70.36s。**当前用例总数尚未查询，不猜测已完成14。**
- 三摘要SHA：sequence `3219d1b6d7b93474d315dfe2895ddb8b71f3f8c352c987e8521741dc75bbb53e`；contention `95ac18a1fbdd205b26e3c8a9ca13c332356a7088b8c07e2167d9291c3495cebe`；timing `b05ac8e7379c722e05f9574773f5765a16fc2ecd0310e6b78b522fc2b0f45b93`。实际细节尚待独立读摘要，未作最终时序审定。
- SAIF小试`runs/systolic_b_v3_validation03_saif_probe/systolic_b_saif_probe`失败，PID114323，12:08:07.728944至12:08:10.919638。VCS region/start/run/stop执行到72ns，在`saif -report native.saif -region r1 -tres 1ps`返回`SAIF_REGION_INVALID_TIMESCALE`。PT未运行，不是系统功耗结果。原失败保留，队列按设计继续gate。
- 已只读核 installed `/eda/synopsys/vcs/vcs_2020.03-SP2-6/etc/ucli/saif.tcl`：help为`-tres <timeunit>`，示例第353行为`-tres 1ns`；未查明该版本细单位有效写法，**不要未经实际小试直接把1ps改成ps或放宽完整窗口**。当前正式整机SAIF脚本请求1fs且严格要求窗口duration完全一致；必须核兼容性。可在原gate队列结束且锁空后，用全新独立目录做短小串行时间单位诊断，不能并行占用EDA或改旧捕获脚本。
- 新ced结构审计再次在写JSON之前退出：旧循环误把末尾统计行`Unloaded nets (LINT-2) 263`当成详细告警。已有合法实例解析修复生效；本地增加只处理以Warning开头的LINT-2详细行，测试夹具新增真实统计行，2项定向检查通过。**此后续修复未提交/部署，正式结构仍未通过，structure03.json尚未生成。** 所有真实Warning仍严格解析，没有忽略未识别告警。
- 当前VNC18874435/workspace3、新ced包空闲shell，FZ关闭，没有本地待续exec/仿真/待Return命令。最新查询`b_gate03_progress.txt`已完成，但输出被大量FILES挤出case名称；下次用紧凑`[(x['case'],x['cycles'])...]`读进度。`b_saif03_head.txt`/failure/help查询均已执行，相关截图已读。
- 尚待：门级14终态、实际check_timing/结构/高扇出/例外审阅，自己的1200，SAIF/R4交叉核验/B活动12功耗12和最终报告。优先继续固定配置验证，不重综合、不重复队列。云ced已核；本地后续parser修复、清理和部署记录尚待提交同步。

## 12:24：小型SAIF兼容性诊断工具本地准备

新增`systolic_b_saif_units`阶段（`native_saif_units.py`），使用统一server_run协作锁，编译同一独立小夹具，每个候选时间单位写独立子目录/日志并检查实际0/1/X/Z驻留及翻转。仅诊断VCS参数，不调用PT，不自动授予SAIF/系统功耗资格；后续仍须正式小试及R4全窗口交叉核验。不会在当前gate占锁时运行。

本地结构/队列/SAIF解析相关6项检查通过，CLI帮助已确认新阶段接入；**未上传/未运行此新诊断**。正式probe及整机SAIF请求尚未改动，不能猜测有效单位。下一步提交包含结构统计表修复与诊断工具的新包，上传后先重审原网表；等原gate结束后串行小试。不要重新运行已通过的CPU诊断或综合。

## 12:28：诊断包已板端暂存，尚未FTP上传

- 2b39c6d347b33112fc4210ad77bffedbd01bab54已提交/push且ls-remote一致。当前本地只有新包证据/本段文档未提交。上述小工具提交时间为12:24:13，原段标题误写12:26已更正。
- 新包`light-light126-systolic-b-v3-20261112_122414-2b39c6d347b3.zip`，11360106B，ZIP SHA eb47f16b049684172051540467328cc9887d4b8e0fae29302a0e3fc5e4d7562f；710输入，manifest67968c24b0d8856ae0ca9ccf4e99915d28e3cca3a58bb1e85e7fdc3a0fe360b5。全部输入/无缓存核验；67受保护RTL/SW/固件比较仍仅sequence ELF调试/符号四个非分配节不同，实际加载镜像、生产和contention全部相同。
- 已板端暂存并SHA核验：`/home/root/systolic_b_units_2b39c6d/`，GUI映射`/home/board/systolic_b_units_2b39c6d/`。**没有FTP上传、服务器解包或新EDA启动。**证据`SYSTOLIC_B_SAIF_UNITS_PACKAGE_20261112.json`。
- 原gate12:24:56已完成9/14例L01–L09，周期逐层与ASIC一致，无错误；原117191继续，不能重跑。当前前台VNC仍为ced包空闲shell。
- 已通过桌面Alt+F2打开appfinder20972260，输入filezilla并Return，正在打开正确配置FileZilla。下一步读取最新窗口清单；原VNC workspace3不变。原队列继续，先完成新包传输再串行安排小型诊断，不能操作workspace4。

## 12:38 接续记录：gate14完成，但4项max_transition超限阻止时序批准

validation03在12:32:45观察已为validation_complete_review_required，14个功能门级任务/354816输出全部通过，周期与ASIC一致；无SDF。gate摘要SHA55c668a8bf8b8d0437d142ee929d2953b06f92a52c480074f7326aa616f32ca5，队列状态SHAd0a35dfd75df95199ec9a18a3cce323ea379f4620bfcbf9789a83f650c7c6b3。原作业已完成，不重复启动。

12:33–12:34实际constraints.rpt发现4项max_transition违规：要求约1.35ns，实际约1.37ns，每项约-0.02ns、合计约-0.09ns。示例core/n5271。setup/hold虽为正，不能批准完整时序，不能启动以已批准时序为前提的最终队列。需查安装DC官方compile手册，再在全新目录做原约束下的映射修复；若网表改变，必须重跑新网表gate14。RTL/固件仍63da冻结，不增架构或编码功能，不放宽限制。

2b39诊断包12:31 FTP尝试返回421用户过多，FileZilla已关闭；仅本地和板端暂存，未上传/解包/运行。可合并必要修复工具后发新包。正式结构审计仍被旧解析器阻塞，SAIF小试仍失败，自己的1200及功耗未验。旧失败和两次清理清单保留。

最后VNC18874435/workspace3/ced包空闲shell。b_dc_compile_doc_find已执行，截图已读：官方compile手册在/eda/synopsys/dc/dc_2022.03-SP5-5/doc/syn/man/cat2/compile.2。没有本地运行任务/待Return命令。操作前重新查进程/锁/空间；所有历史PID只作历史记录。硬冻结已过，仅修已知问题和补证据。R4保持交付退路。

## 12:48 增量：独立映射修复工具准备，尚未服务器执行

12:43:20实际无EDA/无协作锁，可用227.953125GiB。已读取安装DC compile.2：only_design_rule仅修设计规则，不进行mapping optimization。新工具systolic_b_drc_repair使用显式原摘要哈希，核对同B RTL、安装器、原约束逐字相同，复制原mapped.ddc至新repair_seed；保留全部原输入来源并新增本包/数据库核验。经标准server_run锁在全新systolic_b_synth阶段运行compile -incremental_mapping -only_design_rule，不放宽约束，不修改旧目录，新网表须新gate及PPA。

12项相关本地工具检查通过，包括拒绝改动输入、既有输出、约束变化及保留报告/宏约束；不是实际DC修复通过。实际check_timing已单独读：3条高扇出网TIM-134，其余列出的generated clocks/loops/input delay/unconstrained endpoints/pulse/no-driving/partial-delay检查没有新告警；高扇出对象为已读三条时钟，仍按稳定任务模式范围审核。

下一步提交并打含结构修复/SAIF单位诊断/DRC修复的新工具包；2b包FTP421失败保持历史，不重复部署它。当前VNC仍workspace3/ced空闲shell，FileZilla关闭，无本地进程或待输入命令。功能RTL和固件未改。
