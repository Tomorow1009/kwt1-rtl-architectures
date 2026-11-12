# B 进度与恢复：2026-11-12 14:38

## 14:50增量

ee621bf已push，八工具通过7条短命令部署并核验，operations/systolic_b_tools_ee621bf，manifest be92e8b86f3b89e862f2f3692abda730d75692e8e041ac98650970422650944b。不可重复部署/append。

inspect02 PID266412于14:44:46.218811结束，**status failed**：查询不存在的BUF可选规格没有用quiet，产生UID109；实际driver_inventory.tsv已产生，不能称整轮通过。其可读数据：n298364由U3777 NOR3CV2驱动，n298366=U3778 NOR3CV2，n298367=U3776 NOR3CV2。DRC05实际网表已有NOR3CV0/1/2/4/6/8实例，证明V4存在。BUFV2RD输入cap .000960、BUFV4RD .001599，BUFV4RQ .000871；这些是库原始数值。备选低输入cap缓冲规格仅诊断，未实施。

下一定向DRC06本地拟从DRC05摘要55fc...复制，只将上述三个NOR3CV2等价升NOR3CV4，仍核pin方向/函数、原8d库身份、原task_mode约束，保护已修的四个下游驱动。尚未提交/部署/启动；不要用旧60工具启动06。只读候选查询已加quiet，不再将不存在的可选型号作EDA错误。

本地systolic_b_ops扩展带hash请求的R4 SAIF重放/交叉核对及B活动/功耗入口，复用同一锁/新session/原base.inputs；防路径越界和引用摘要改变，运行后复核request。10项相关保护检查通过，只是工具检查。新ops和测试未提交部署。正式1200仍禁止提前批准。

当前VNC工作区3/ced空闲shell，FZ关闭，无已知EDA，无本地持续session/待Return。最后b_inspect02_compact查询完成。下一步提交同步新工具、小差分新目录，先新DRC06；完成后按实测决定R4 SAIF与新gate次序，禁止并发EDA。

任务 ACTIVE，继续直接B计划；63da6ba/v3/credits3生产源冻结，不加架构；R4保底。用户已授权旧验证大文件清理并要求继续；两次清理279.506GiB已完成不重复。VNC工作区3，禁止工作区4。FTP421用户确认无队友使用，未再尝试FileZilla。

先读AGENTS、IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md、本检查点、1350检查点和STATUS。旧完整ZIP62/2b未上传且含旧工具问题，不执行；ced包输入未变。所有ops副本/失败目录保留。

## 新完成

- Git HEAD 60df7725e729edab7f8550bc5b9545f2c77b7711已push及ls-remote核对；60工具8文件已9条短命令完整部署，manifest7a839b60e16b738a5dc078b0f0d5036b845ecda39940d3b8600a22f6e194f262。目录operations/systolic_b_tools_60df772，禁止重复append。前0d目录也已部署。
- **正式SAIF小试probe04通过**：ced runs/systolic_b_v3_saif_probe04/systolic_b_saif_probe，PID251446，14:24:57.106218完成；summary SHA5b89541639df84d147f76b407bfd13c906b9fdf7bcbee912650cef716687a25b。12–72ns共60ns，1fs单位；PT文件注释toggle概率.333333、每ns翻转率.0666667，符合4次翻转。VCS合并X/Z于TX，不能称分离测量。证据SYSTOLIC_B_SAIF_PROBE_20261112.json已本地写，未提交。
- 已读安装PT官方get_switching_activity文档，用该API而非不支持的get_attribute。probe02 ANSI失败、probe03端口属性失败保留。小试通过不等于R4完整交叉核对或B功耗通过。
- 只读driver inspect01通过，原4驱动无dont_touch/dont_size/size_only，候选更强驱动存在；摘要详1350增量。现本地inspect又增加输入电容/上游驱动查询，并改回原8d库身份避免重复库，尚未提交部署。

## DRC05实际：仍不合格

ced `runs/systolic_b_v3_drc05/systolic_b_synth`，driver253324/child253408，14:27:02.409315开始、**14:33:35.246720报告完成**。summary SHA55fcf35b3d2d01ea782f7f543bc00b1ae49078e9f1b9c66534ab33c1e8765bbe。

实际针对DRC04：U32684/U32686/U32433由BUFV2RD升BUFV4RD，U30602由AOI22V2升AOI22V4。替换前核同pin方向/函数，保持这些驱动不再降规格，运行普通high effort incremental；约束、RTL未变，compile仍绑定原8d库路径。4处旧transition局部改善，但上游引入新的转换时间/电容违规。**完整报告实际只含max_transition和max_capacitance两类，multiport已消除；72个VIOLATED字符串含同一网络各引脚重复列示，不能称72个独立违规。** 两类各Total3，需精确复核。面积保守上界1.098423737500962mm²。此前根据部分截图误推更多multiport的口头更新已纠正，以完整类别为准。

上游net n298364/n298366/n298367出现max_cap，新的transition包括U32684/I、U3776/ZN和n298366；下一步查精确驱动和各BUF输入电容，避免盲目重复升驱动。官方set_fix_multiple_port_nets接受design_list，默认current design；当前multiport已经消除，暂不为它继续改映射。DRC05 setup+.0002141ns/hold+.00249085ns，整机4620640.237510µm²。未修改任何规范，不得批准1200或新gate。新映射仍需自己的gate14。

## 目前操作状态

当前VNC18874435工作区3/ced包空闲shell，FZ关闭，无待Return，无本地持续会话。DRC05已结束；新EDA前用server_config.server_root的真实锁路径/进程核对。**临时b_60_*_status等脚本用../../.arch02_team_lock是错误位置，显示False不能证明无锁**；ops本身始终使用cfg的真实锁，未并发EDA。13:58实际资源是405.94GiB，需重读。

最后执行b_drc05_metrics_short.txt，截图同名.png刚读取，包含setup/hold与set_fix_multiple_port_nets文档摘要。所有现有launch均已执行，不重复。

本地待提交：systolic_b_drc_repair.py新增read-only cap/upstream诊断，SAIF通过证据，本检查点及根交接更新。最新5项工具保护测试通过，但新cap查询尚无服务器结果。

## 尚未完成与下一步

1. 以实际库电容/上游驱动和修复层级为依据继续局部映射修复，重核完整约束、面积、结构、宏、setup/hold。
2. 小试通过后安排R4 L01完整SAIF重放及同网表PT与原VCD≤1%交叉核对。现有native_saif_replay/其他代码在ced基座还是旧版，ops副本有新版模块，但目前ops CLI只支持probe/units/synth/inspect；需扩展受控入口或新完整包，不能误运行旧parser。
3. 时序/面积合格后新网表gate14、冻结审核、干净ASIC14、自己的1200/30412800、B活动12/功耗12、报告。B仍无最终1200和功耗，R4不重跑1200。

现有B功能ASIC14/原synth02 gate14、CPU恢复/竞争已过；平均30502.3333周期/4917.6566task/s。R4自身4333.256task/s、71.8126mW、16.5724µJ保留；系统功耗未知影响仍未完全验收。

下一工具部署可运行takeover_local/build_b_ops_delta.py <上一已部署commit>按Git差分生成新8文件目录；上次60相对0d仅9命令，已全执行。type每条<1000字符，先等完整结束再Return，批次使用PowerShell循环顺序执行，检查退出码。exec_command若返回session需write_stdin收尾。远端tcsh用env PYTHONPATH，python外层双引号内避免美元符号。只用VNC/已授权FTP，无新增SSH通路。
