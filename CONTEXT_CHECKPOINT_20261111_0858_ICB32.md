# 2026-11-11 08:58接续：功耗已有两层，交付SDC精度修正准备中

用户要求持续推进，不因普通步骤停等。压缩后先读AGENTS、当前有效`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本文件、STATUS/EXECUTION_CHECKPOINT的`icb32_c64_execution`。完整包、原已验结果和自动队列入口沿用[08:35检查点](CONTEXT_CHECKPOINT_20261111_0835_ICB32.md)。不要重启任何原任务或清锁。

## 已完成与当前实际状态

- 原497门级14例354816输出、12个完整活动全部通过，08:29:52自然完成。原driver209764已结束，不再查询它是否活跃。最终summary SHA`95113a35bf2941e985d8d1b8cbad7d88c0d56f07d3c1f533f0fcf549fb2efc7f`。
- e65 ASIC14、CPU竞争/无复位恢复、新综合/面积和结构端口审阅均已完成，不重复。平均34616周期、150MHz折算4333.256task/s；保守新增面积0.9265616712mm²、整机4.4487781712mm²；setup+0.0000715256ns、hold+0.000253469ns。5000未达到，完整PPA审定仍未完成。
- **08:56:38.278611真实观察：原后继285397 running，已完成L01/L02功耗，当前`icb32_r4_finish01_power_l03`。driver158250，PT wrapper158637。error=None。** 服务器cwd仍964运行包根。顺序仍power12→metrics14→final1200→生成report_request，禁止手工重复。
- L01整机72.1431449mW、16.6597743086µJ；L02整机72.097905mW、16.6339463255µJ。均为布局前估算，目前不是12层平均，system_power_verified=false。
- L01详细小型证据`handoff/team/evidence/ICB32_POWER_L01_20261111.json`，中文说明`workspaces/arch03/ICB32_POWER_REVIEW_20261111.md`。原29.627mW/44.593µJ仍属fcd DMA16，不能套到新R4。

## 新完成的轻量首层审阅

全部只读既有报告，不重扫VCD、不启动EDA。

1. L01功耗摘要SHA`18190f6d4021de0ba55ae2b2be00a456f89217a6efbd0c0e3412831617f2d00c`；964队列`layer_01_numbers.json` SHA`a09b654b0165eddd107e37686852722692c806fbbe74fb8938177f89273a7d3b`。
2. 实际单位和数值求和由原队列提取器通过，224宏（shared64、ITCM32、DTCM32、accel96）齐全。首层时长230926.643574ns；功耗internal51.4801964mW、switching13.3940009mW、leakage7.26894895mW。含输入边界网总量72.1453205mW另列，不叠加模块/宏总量。
3. `runs/icb32_l01_annotation01.json` SHA **`873eae618eba1e8266ed19f9279d220ac0f7df2ec8add62fc72a73f28740061c`**。362618个网络的switching及static_probability全部exact，其他来源为0、前后unannotated清单空。216834网至少翻转一次（59.80%），这不是映射率。averaged、X因子0.5、initial-X=false；L01完整VCD有996956未知记录，影响仍未全部审定。
4. `runs/icb32_l01_timing_objects01.json` SHA`3388fbc7c7b242e1f43eb29fbec781d25b8f94a0c9cb0642a1b534ed4423d418`。no_clock189个：DTM186+JTAG reset3，CK182/CKN7；禁用弧78973，p14199/C62570/c1997/d207，无user/loop/false-net标志。用了已有纯函数，未调用旧MMIO8/DMA16限定入口。
5. **08:53:58.582134四份回执独立SHA断言通过。** 初次抄录annotation前缀把873eae写成873aee，断言拒绝；逐字符定位并修正。属于人工回执转写错误，不是服务器报告或硬件失败。相关查询/截图保留。

## 新发现与必须完成的交付修正

实际DC metrics周期6.666666000000ns，原mapped.sdc由write_sdc序列化为6.66667ns、下降沿3.33333ns，PT当前功耗导入了这个原始文件。不能声称原PT已经导入精确6.666666。原DC时序实际为精确周期，原结果保留。

原SDC SHA`b11e22fbe4c880848101243646703323270d68ff0677449f4d5f4b7e08f78f48`；实际PLL bypass/div1、bootrom去抖为1，JTAG TCK/TMS/TDI为0。仅1条false-path命令对应LF到u_tim0..3首级r_ls_clk_sync_reg[0]/D四端点，无clock groups/multicycle；其他SysMem预算不变。详细说明已补`ICB32_TIMING_REVIEW_20261111.md`。

新增`workspaces/arch03/scripts/icb32_delivery_sdc.py`，绑定原summary/stage/metrics/netlist/SDC哈希，**只在新目录**恢复HF周期6.666666和下降沿3.333333；其余约束逐字保留，不写原文件、不改网表、不自动提高任何PASS。`test_icb32_delivery_sdc.py`两项本地检查通过，涵盖实际舍入案例及非法/重复/错误测量时钟拒绝。当前**仅本地准备，尚未提交/上传/服务器执行**；下一步应提交并用独立小操作包正常FileZilla上传，执行只读导出，读取实际回执。当前原功耗队列保持不动。需要精确PT复核时应串行安排独立报告，不原地重跑历史功耗。

可复用`takeover_local/package_icb32_ops.py`的打包方式，但它绑定旧queue脚本，**不要直接重跑该旧打包器或launch**。新包应仅含导出工具、timing_contract、测试及独立launch/manifest，不带硬件/固件/厂商库。同范围上传授权持续有效。

## 仍未完成及后续

- 余10层功耗、同配置12层报告核对/汇总；未知活动影响限制保留，避免无谓新增大扫描。
- 964真实ASIC14被动计数/干净目录复现，以及自己的最终1200任务30412800输出，已在原队列后面，不能手工并发。
- 队列完成后审阅report_request补history，在新输出目录运行`icb32_report.py`。工具会复核全部输出及VCD哈希，需要串行；自动unverified中仍包含已独立完成CPU诊断/未来干净复现，最终配同身份说明，不能误说没做或直接篡改历史false。
- 精确交付SDC、最终JSON/CSV/中文报告、最终提交包/答辩材料；R1服务器完整PPA和原8路完整功耗属次优先对照。实现18:00冻结、11/12 17:16交付准备、用户截止11/13晚上。
- 官方600精度、布局后时序/功耗、物理签核未验证。原fcd已完成自己的1200保留退路，不继承到新R4。

## 恢复操作与文件

- VNC实际window20971587、800×450；新上下文先盘点。板端helper`F:/linux_fpga_try/ac820.ps1`沿用已授权调用。服务器shell只能经板端VNC，上传只能正常Linux FileZilla；FileZilla当前关闭，FTP代理21036/VNC relay23793保持。
- 当前最后命令为`takeover_local/icb32_finish_live.txt`，可Up Return读通用队列。`icb32_power_numbers_live.txt`读全部已完成数值；`icb32_pt_live.txt`查实际PT孙进程。
- `icb32_l01_timing.txt`和`icb32_l01_activity.txt`已经写了排他新JSON，**不重跑**。`icb32_l01_verify_receipts.txt`修正后已通过；metadata/constraints查询可读但没有必要重复。
- 本地helper若返回session必须poll完成后看新截图；screenshot无expect-class参数，type/key才用。只读时终端有滚屏会丢顶部，所以查询保持简短。
- 本轮另有一次本地PowerShell嵌套引号ParseError，导致查询文件没生成；随后用apply_patch新建修复。服务器未改。一次多文件patch因尾锚不匹配被拒，分开应用后已恢复，没有代码丢失。
- 新进度脚本`takeover_local/progress_0858.py`执行后不可重复；本地无仿真长任务。Git最后已确认abbf06f，本轮新增功耗/时序/SDC文件待提交；同范围持续Git同步已授权。
- 先继续原队列，不以“已记好进度”结束本轮。


## 09:10增量：精确交付SDC已完成，功耗进入L04

- **09:09:23.353851实际：原队列285397 running L04，completed=3，error=None；driver165722、PT wrapper166150。** L03总功耗72.0774755mW、16.627310902112076849µJ。09:08轻量复核已完成三层活动sources/settings/unannotated_after，均362618 exact、0 not_annotated、averaged/0.5/false。原队列不改，后面仍metrics14及final1200。
- 云端4638ed924e0715cb14cd91ceb4d78e7187d18048已独立核对，随后正常导出源码小操作包`light-light126-icb32-sdc-20261111_090010-4638ed924e07`，5文件/5400B，ZIP SHA02542b6dea091c1e222929d6b0dd0139899b2a1b66aeffd58722ceeccb17fe78，manifest d4a678a332aa1a56237678a99efaae91fbd91d4cc8e2f6fac9f475b15ce4ad9b。干净包两项工具检查通过（非硬件重测）。
- 板端暂存`/home/root/icb32_sdc_0900`，GUI为`/home/board/icb32_sdc_0900`。正常FileZilla IC-single-connection上传至原授权目录，5.4KB/1秒成功，队列空；已Ctrl+D/Q并窗口确认退出。开发板VNC保持20971587，原代理/relay保留。
- 09:04服务器ZIP安全解包、5文件及manifest核验通过；09:05通过原summary/stage/metrics/netlist/SDC绑定，成功导出964的`runs/icb32_delivery_sdc01/mapped.precise.sdc`。原文件未变，未启动EDA。**不要再次执行sdc_run或原地覆盖输出。**
- 新SDC SHA`9f49557c4aee558232cdb90f65c50ef6264250eb1f9c61e95747394e0348195d`，receipt SHA`7777a8850e91d5283cfd3093bd59173fce3285de01f4a583d0ff16d449850dbb`，09:07:17.360819独立断言通过。服务器与本地证据`ICB32_DELIVERY_SDC_20261111.json`保存精确6.666666/3.333333、其他约束不变、无timing_rerun；不能误写原PT已用精确SDC。
- `takeover_local/icb32_power_annotation_live.txt`951字符可反复只读当前已完成层，复用964已有纯解析器，不扫描VCD。`icb32_sdc_receipt.txt`可读新回执，verify已经通过；不用重复导出/传包。**最后VNC命令为finish_live**，可Up Return读当前队列。
- 还未改`icb32_report.py`。下一项报告收尾必须避免其现有固定文字造成误导：`declared_conditions.period_ns=6.666666`未说明PT导入舍入差异；固定unverified把CPU竞争/恢复及未来metrics14干净复现列为待验，且复制原synth.required_reviews包含已经完成gate/activity。应保留历史提示并在最终同身份说明中区分实际完成状态；不要自动翻转时序/功耗false。可以修正导出器的条件/文字或生成明确陪同审阅，不需更改RTL或再跑已通过硬件。
- 本轮progress_0858.py和progress_0910.py已经执行，勿重复。本次增量与SDC证据待提交；无本地长任务。继续原串行链，勿结束等待用户。
