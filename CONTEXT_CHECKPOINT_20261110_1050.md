# 2026-11-10 10:50 实施检查点

**11:33当前执行点：** 四点均完成。b85 initial于**11:30:16.464082 passed**；三点队列done=11:30:16.479150，11:30:32.424495观察锁释放。ecf已建立`runs/dma16_x_compare_l01_v1/request.json`，四点summary由实际文件SHA绑定，原27bf默认摘要固定；**已经发送`dma16_x_compare.main()`实际比较命令，结果截图`x_comparison_outcome.png`待读取**。当前没有其他新EDA，不要重复四个点或队列。下一步读比较结果/哈希，再启动ecf已核验的短`mmio8_timing_audit`，之后余11层MAC及原8路完整gate/12PT。

原8路报告相位修复已提交并推送、独立ls-remote确认**e9fc57cecc7393fffe14de614eb9b73bdbec3b26**。新包`light-light126-mmio-report-phase-dma16-20261110_112517-e9fc57cecc73.zip`，16672116B，SHA=`5fda05b9858c5908fef7da585a51631fe1b5e1bfc59f16dcbf5b9bef811f7fdc`，683输入/**228干净tests**/五固件/40生产不变，audit=`local_runs/mmio8_report_phase_clean_audit_20261110_1127/receipt.json`，SHA=`26201989b3e7f9a6cf30d566d0ba5d46007bb413089cc6829b41f795a3c67ef3`。板端`/home/root/undergrad-mmio-report-phase-20261110`已SHA暂存。**FTP返回421人数过多，尚未上传此包，未点击上传。** FileZilla当前最小化，可能已按默认设置重试；先恢复看实际连接/目的地，再正常重试，不问重复授权、不旁路传输。服务器最新实际工具仍ecf，不影响当前四点比较和8路时序查询。

11:28原8路189无时钟对象全量解析已通过：186在JTAG DTM、3在`u_e203_subsys_top/u_sirv_debug_module/u_jtag_ResetCatchAndSync_3_1/reset_n_catch_reg/reg_{0,1,2}/q_reg/CK`；clock pin计182 CK＋7 CKN。首版只认可/CK而被严格拒绝，实际7个CKN为irReg[0..4]、jtag_DRV_TDO、jtag_TDO负沿寄存器；保留原报告，没有略过对象。实际SDC的TCK/TMS/TDI=0已经观察。**尚未保存该189对象派生JSON，也未全量分类disabled弧；不要把它们记为正式时序批准。** 原8路3687端口结构JSON仍有效、SHA已核验。

本地所有测试/打包/暂存会话均已完成，四点比较命令helper已返回，待观察远端完成。当前工作树只有本条/root进度等证据修改，报告代码修复已经提交e9；最新同范围云同步不需再次确认。压缩后先读计划/root/本检查点/三JSON，再看`x_comparison_outcome.png`，不要从旧zero/one运行状态重启。

**11:25最新增量：** ecf原8路时序包FileZilla33秒成功、success27、空队列后断开最小化；11:19:36.081221安全解包，**11:20:36.891532服务器683输入/完整提交核验通过**。云端仍ecf3cd4，尚未启动其mmio8_timing_audit。当前唯一队列parent188919：one于**11:20:12.393155 passed**；**initial于11:20:12.747228开始，owner212936/pt213156，最后11:22:57.901781仍running**。zero/one数值及SHA后续四点比较完整绑定，勿重跑它们。frozen与zero已观察总功耗/能耗相同，不能提前推断initial或全部未知影响。

**新发现并本地修复原8路报告问题：** 11:21直接以原c5 ASIC和a2首层gate摘要的既有SHA核验原始回执，两者都是3843121周期、end_ns=25639874.102679，但ASIC start_ns=19070.998093、phase=1ns、duration=25620803.104586ns；gate start_ns=19069.998093、phase=0、duration=25620804.104586ns。旧`mmio8_report.join_cases`要求纳秒时长完全相同，会在最终导出拒绝这组合法相位差；还未发生实际完整导出失败，此为提前核对发现，不是硬件失败。

新增`compare_windows`分别严格验证两个窗口、要求周期/period一致，差异必须由已观测起始相位解释且小于1周期；保留ASIC/gate时长与相位，能量始终用gate真实窗口。共享`dma16_report.write_outputs`只在存在该证据时增加CSV列及中文说明，默认DMA16内容保持原路径。新增2项测试（真实首层数字、不同周期拒绝、门级能源窗口），与原工具共29tests通过。**修改尚未提交/打包/服务器复验**，涉及mmio8_report.py、test_mmio8_report.py、dma16_report.py；现ecf包仍旧report。不要改或重导出full02，已有默认DMA16报告不受此修复影响。

接续：先完成本修复的提交/干净包（预计228tests，实际待核验）及同范围同步上传；与此同时initial继续。队列结束后用已上传a745/ecf比较器对四点实际报告生成request→comparison（source均b85），再用ecf新mmio8_timing_audit短阶段检查旧8网表。其后必须排余11层MAC完整扫描以及原8路完整14gate/12活动与12PT，不重复单层/1200/full02。原8路189 no_clock/disabled全部分类仍待办。生产fcd/正式固件/668batch无改动。所有本地工具会话截至此条已完成，无挂起上传；VNC空闲查询页，FileZilla断开。

**11:18增量：** 原8路只读高扇出工具已提交并云端ls-remote确认`ecf3cd4afb3c96b9580687b5ab42db60e0372292`。包`light-light126-mmio-timing-dma16-20261110_111311-ecf3cd4afb3c.zip`，16662114B，SHA=`b2a21eb5fc1722c7c6d467f4ceafec78d23e92081c573842bd4318228663d0b5`，683输入/226干净tests/五固件/40生产文件不变；clean=`local_runs/mmio8_timing_clean_audit_20261110_1114/receipt.json`，SHA=`0f9783fb1e365c89812c47f34de7f9e8e897813c5e6590df1369d58288dee60e`。板端`/home/root/undergrad-mmio-timing-20261110`已SHA暂存，当前正由FileZilla上传，**成功回执/服务器解包/683输入仍待观察**。不要重复上传；完成后断开最小化。

三点队列最后**11:12:52.894388**：zero stage10:59:00.585559开始、11:09:28.639448 passed；**one stage11:09:28.948502开始，owner200283/pt200523 running**；initial尚未启动。parent仍188919，唯一队列，其他MAC/8路EDA均未启动。下方“zero当前owner”是历史。

原8路PT小报告继续只读：timing_check明确189 no_clock，实际行格式为Clock Pin表，示例属于`u_e203_subsys_top/u_sirv_debug_module/jtag_dtm_gen.u_sirv_jtag_dtm/.../CK`；下一段Information为partial_delay。实际mapped.sdc的TCK/TMS/TDI均set_case_analysis 0。**尚未完整189对象分类或禁用弧计数**，不能凭几个示例套用16路结论。禁用弧表实际为Cell or Port / From / To / Sense / Flag / Reason，行按空白分列，第5项为flag；需检查完整表覆盖再归类。截图`mmio8_no_clock_format.png`、`mmio8_timing_headers.png`。结构SHA独立确认时间统一记11:10:37（微秒此前转抄有误，不作为结果身份）。

下一步：等FileZilla成功→安全解包/输入→重查one/initial队列；空闲后ecf新`mmio8_timing_audit`短查询，再余11层MAC全扫描和原8路14/12完整gate/PPA。四点全部完成时用a745或ecf中的`dma16_x_compare.py`生成request与全四点比较；load_point/load_baseline实际格式已通过，不重跑frozen/zero。保持fcd/668生产冻结及full02不重复。此次本地打包、clean、板端暂存会话均已完成。

**11:12增量：** a745比较包FileZilla33秒成功、success26空队列后断开最小化；11:02:13.024915安全解包，11:02:45.038248核验681输入/完整提交及三点队列plan SHA。11:04:06.754693实际新`load_point/load_baseline`重读成功，5个网表/SDC/库身份及完整活动窗口一致；尚未完整四点比较。三点队列唯一parent188919继续：zero driver188920/pt189212于**11:09:28.639448 passed**，数值total=0.0296837185W、energy=0.0000446779497038379161700J，与默认同；one/initial最新owner待查，勿另启。zero摘要SHA尚未单独读取，后续由四点比较请求绑定。

原8路新结构全分类已完成于a745 `runs/mmio8_struct_review01/ports.json`：1179模块，3687端口全declaration_only，输入3574/输出113，LINT1/2/8/28/32/33=4/88/88/3599/3600/411。SHA=`0b3918d6b1cc56cf7cba9a93d3b2a7caa86bbb64eeec175988c11c1969e85b57`于**11:10:37**独立断言。该只读诊断使用现有generic classify，前后`dma16_report.load_stage(ref,'mmio8_synth')`校核1aa原综合工件，JSON独立mmio8 schema；不修改原网表、不批准时序。PT timing_check尾部已读，disabled表头已读，但189 no_clock具体归类/禁用弧全量原因未完成，不能套用DMA16结果。

新增本地`mmio8_timing_audit.py`、3tests及server_run新stage，相关26tests通过；读取原8路DDC并按真实原8路探针查询高扇出，保留原前后身份，不改约束/网表。**尚未提交/打包/服务器运行**，与本段文档/三JSON更新一并待提交。clean helper已加入test_mmio8_timing_audit，下一干净包预计226tests、683输入（仍需实际核验）。生产及668最终batch入口不变。下一步先新包、云同步/干净验证/上传；当前重队列自然结束后先运行短mmio8_timing_audit，再排余11层MAC扫描和8路完整gate/PPA。不要延迟完整对照到最后一天。

所有本地exec会话截至此条均已结束，无挂起上传；FileZilla已断开，VNC第3页空闲。当前工作树新8路工具和证据尚未提交。下一操作应查询三点队列当前owner/进度；若正在one/initial则不启动任何重任务。

**11:00增量：** b85 frozen诊断于**10:52:11.278534 passed**，准确摘要SHA=`68dc61ee3b9b82de2c941696bb00604493419b6b25026b2aba4df0414f86352f`已**10:57:33.784894**独立断言；之前抄错第3组首位导致队列创建前失败，未启动任何任务。10:54:39.730504用原正式27bf PT重新提取比对，总数/分组/模块/SRAM/边界/能耗六字段完全一致，0.0296837185W、0.0000446779497038379161700J。系统功耗仍false。

**当前唯一重队列：b85 `runs/dma16_x_queue_remaining_v1`，parent188919，10:58:59.937100启动，依次zero/one/initial。** plan SHA打印为`c49598b1484a7fd0eaab67ca8d832d2eeb9c43d62f7a782561756f79e7718e79`，尚待独立断言；runner逐项subprocess.run(check=True)，任一失败停止，单stage仍拿共享锁。下一步先查state/owner。勿另开三个点或MAC/8路EDA。runner两次本地命令长度守卫失败，未发服务器；缩短后只建立一个runner/launcher。

新比较工具已提交并推送**a74588d97aaa18cbd72abdefe3b899759d652f4d**，ls-remote独立确认。包`light-light126-x-compare-dma16-20261110_105208-a74588d97aaa.zip`，16654613B，SHA=`b488fd3d2933f9052f79bf860701c75201ec1c0c84c94bfd66f764f168f168ce`，681输入/**223干净tests**/五固件/40生产文件与668相同；audit=`local_runs/dma16_x_compare_clean_audit_20261110_1054/receipt.json`，SHA=`32dce79c4467b6fa772cb261c687bf70d1f6e45445002e7e5d45eded5411c39a`。板端暂存SHA通过，FileZilla已选择正确`/IC/light-light126-undergrad-d2-20261109`并开始上传，**成功回执/解包/681服务器输入尚未观察**。先等传输成功/空队列，再断开最小化；不可重复传输。下方“比较未提交/新包尚未打包”均已被本条覆盖。

继续用户已恢复的三天直接16路DMA计划。压缩后先读AGENTS、根交接、本文件、有效计划及三份状态。开发板已上电、FileZilla允许，私人GitHub同范围后续同步持续授权。不得停在进度汇报；生产fcd、最终批量668保持冻结。

## 本段新完成

- b85工具提交`b85e908fab388f07027b7b4e983d36635651ee1c`已推送且本轮再次ls-remote确认。包`light-light126-x-model-dma16-20261110_102408-b85e908fab38`，16644393B，ZIP SHA=`475375b33f3ed516d6f24b2b21066cc05dbadd0c1e5991fcba038715051e77a9`。679输入/215干净tests/五固件/40生产文件与668一致。clean audit=`local_runs/dma16_x_model_clean_audit_20261110_1026/receipt.json`，SHA=`57d94eab7a7b38ac4a2aa335dbc34fbf9baa53c1365ec5fe131e7466fc9befee`。
- 已经FileZilla33秒上传，success25、空队列后断开最小化。板端暂存`/home/root/undergrad-x-model-20261110`。服务器**10:30:51.445480安全解包，10:38:37.395611核验679输入及完整提交**。不要重复上传。
- bb25 `runs/dma16_mac_use_l01_v2/dma16_mac_use`于**10:38:43.356180 passed**，原driver142991/child143321正常结束并释放共享锁。完整扫描文件18873069B；8.745GB原始VCD前后哈希与原全量计数一致。准确摘要SHA=`7c1bba6b91b7bfb0aa08ddcbe5fc9a9ecb1ae8c0bdc04b5925b4dfd851fcd298`，**10:44:47.489867独立断言通过**。
- 每路1584 starts/101376 feeds/1584 outputs；共1622016 MAC/25344输出，有效采样未知0、不确定控制0、协议违反0，无复位或未完成点积。各路225770时钟边沿，首93683323965tick、末1598809840119tick；lane0 X/W未知采样边沿92691/92694，但不在被接受的数据上，其余端口未知采样0。该结论仅为MAC有效消费证明，不批准整机功耗。
- 原未知计数保持389025（起点29654＋后续359371）、34128未知标识、9576结束未知、614初始未观察。不能把它们删除或按零功耗处理。
- 两次哈希人工抄录错误均由断言拒绝，没有修改原摘要；逐字符定位并纠正27/28位置c/9后最终通过。以后每行8字符、字符间加空格，不打印长列表造成截断。
- 已更新ACCEPTANCE、DELIVERY_INDEX、README、VERIFICATION_MATRIX和创新稿的当前状态：12层来源/设置审核完成；原8路首层门级/PT及数值完成，完整对照仍缺。

## 当前唯一重作业

b85包`runs/dma16_x_frozen_l01_v1/dma16_x_sensitivity`，**driver170842、child171053**。launcher10:42:03.165301、stage10:42:03.773833；10:42:30.795539独立state/owner确认，10:48:39.905505仍running读完整layer_01 VCD。采用同a53波形/fcd网表/库、averaged/0.5/false；这是新诊断入口的原设置复现，尚未看最终结果。不得并发EDA/大扫描或清锁。

最新已发状态/数字查询，截图`takeover_local/d2_20261109/x_frozen_state_numbers.png`待读取；本地exec会话12482可能需先poll完成。若其后收到结果，以最新增量覆盖本段。

## 本地新工具（尚未提交/上传）

新增`dma16_x_compare.py`、`test_dma16_x_compare.py`，8项定向＋32既有检查共40通过。读取4个独立实际诊断和原正式首层PT：严格校验摘要/state/工件、重新解析数值、实际设置、同网表/SDC/至少三库/波形/窗口/固件/布局；frozen复现需与原值逐项完全相同，再给出四点有符号差值与选定设置离散范围。始终保持system_power_verified/physical_error_bound/replaces_frozen_estimate=false。

首个测试把Decimal零写法限定为0E-15而实际0E-20失败，改为数值零断言后40通过；不是功耗数值失败。临时dummy.tmp已经删除，未入库。新比较工具未用于服务器，也不能称四点结果已有。

## 接续顺序与禁止重复

1. 读取frozen实际完成状态。通过后核对原首层实际数值和摘要，再串行zero/one/initial；准备单一停错队列，不重复frozen。
2. 完成比较工具的干净包审计、同范围云同步和上传后，运行四点比较。队列不依赖比较工具，不改正在执行的b85快照。
3. 其余11层MAC完整未知/采样扫描待办；每层可能约23分钟，以实际宿主耗时计划，保留至少20%余量。可使用b85中的同bb25扫描源码。不要再单独重跑旧unknown工具造成双份扫描。
4. 原8路尚需完整14门级/12活动及12层PT、严格约束审核；只有首层新gate/PT/numbers完成。原8路不是8DMA，不复用旧BEGIN窗口或synth07证明新加载。
5. CPU/SRAM/互连/AON未知有效使用及建模判断仍缺；原AON备份寄存器无reset注释不是全量豁免依据。干净服务器复现、最终包及答辩材料仍待办。
6. **不得重复最终1200或full02独立重审**：已1200/30412800/0失败；报告receipt=`06c246af4de0914e1e304fc77cf1b61413e955a350c59d5d8d0df8c521e84e5c`。任务模式150MHz和0.434796781612mm²已绑定；系统功耗/官方精度/物理签核false。FROZEN_REVIEW.md的规范LF哈希绑定不随意修改。

## 操作恢复

服务器base=`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`，包在bundles，锁为父IC/.arch02_team_lock。只经开发板VNC执行服务器命令，只经FileZilla上传，不SSH/下载/隐藏旁路。`F:/linux_fpga_try/ac820.ps1`先刷新windows；本轮VNC18874435/FZ20972102/panel10485764，第3终端空闲。新启动需重查锁与pgrep，先建runs父目录、新目录独占打开launcher，不覆旧失败。

远端命令单物理行<1000字符，本地先检查；长type返回session则poll结束后再操作。不要在functions.wait里填exec session。查询需短输出，避免整个manifest/长JSON遮住实际结果。其余历史路径、准确SHA和既有成果见10:06检查点及三份JSON。
