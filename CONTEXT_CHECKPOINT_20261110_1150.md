# 2026-11-10 11:50 实施检查点

**11:59增量：** e9已FileZilla33秒成功（success28、空队列、断开最小化），11:50:16.166838安全解包，11:51:32.267913核验683输入/完整提交。新相位比较目录`runs/mmio8_phase_review01`第一次因新包没有runs父目录失败，后续依赖查询也未执行；11:58:29.677742补建父目录、独立验证两份原摘要并建立请求成功。实际compare_windows命令已发送，结果`e9_phase_actual.png`待读取，不重复执行到同一输出。

队列计划正确SHA为`db8df26da37f6487c0141fe16cecc8b96e4364e211ba1e4fa622fa0fc8c1a7b6`，约11:54独立断言通过。G5中e/f此前抄反，ASCII索引45=101、47=102确认并修正，原计划未改。runner只在全部完成后写`done.json`，运行中看launcher及子stage；不存在queue/state.json是预期。剩余11MAC＋完整8路gate仍唯一重队列。

原8路禁用弧初步全表55719条（C40708/p12819/c1991/d201）。新增完整对象保存工具`mmio8_timing_objects.py`及7tests，与既有相关检查合计27通过；尚未提交/打包/实际服务器运行。工具绑定原8综合/PT，保留189对象与每条禁用弧/原因，截断和未知格式失败，不自动批准时序。详情`workspaces/arch03/MMIO8_TIMING_REVIEW_20261110.md`。下一步提交/同范围云同步、干净包和实际分类。生产与最终批量仍不变。

继续用户已恢复的直接16路三天计划。每次压缩后重读AGENTS、根交接、本文件、`workspaces/arch03/IMPLEMENTATION_PLAN_DMA16_20261109.md`及三JSON。用户授权的私人GitHub同范围后续同步、板端FileZilla上传持续有效，不重复询问。

## 已完成及当前运行

- 生产fcd、正式固件和668最终批量入口保持冻结。最终1200 ASIC/E203任务、30412800输出、0失败；full02已独立重审全部回执并导出JSON/CSV/中文报告，**不重复1200/full02**。150MHz名义吞吐664.3929662931301 task/s、225770周期；声明范围的稳定任务模式综合时序及0.434796781612mm²保守面积上界已审定。系统功耗、官方精度、物理签核仍false。
- 四点X诊断全部完成：initial于11:30:16.464082 passed，b85三点队列于11:30:16.479150结束。ecf `runs/dma16_x_compare_l01_v1/comparison.json`于11:32:05.166608生成，SHA `bc9da5d6231aa44ce0bdf2bda619989ce614bc34217d0bbeb0733ee388a90934`于11:34:51.009392独立确认。zero/frozen/one/initial四点总功耗均0.0296837185 W、能耗均0.0000446779497038379161700 J；frozen六字段与原27bf完全复现。仅说明所选工具设置下打印精度内相同，不是物理误差界，也不代替整机未知活动审核。
- 原8路只读DDC查询ecf `runs/mmio8_timing_review01/mmio8_timing_audit`：driver226469，11:34:15.174492开始、11:34:30.932198 passed。摘要SHA `e9df8a749359e800f4218b284f4c17a0682ecf8d257f6067e9943bcd2fcea95f`已独立断言。高扇出3条为core_csr_clk、hfclk及AON crossing_clock；原网表未变，尚未批准原8路时序。
- **当前唯一重队列**：ecf `runs/dma16_mac02_12_mmio8_gate_queue_v1`，parent232492，11:40:10.832432启动；启动时空闲2518825304064 B。依次11层MAC有效采样扫描（l02—l12）和原8路完整14门级/12活动（`mmio8_source_gate_full01`），共12个命令。每阶段独占共享锁、任一失败停止；进入8路gate前检查至少500GiB空闲。禁止重复启动或与其他EDA/大波形扫描并发。
- **11:46:24.927617实际观察**：第二层`dma16_mac_use_l02_v1/dma16_mac_use`运行中，driver232496、child232863；stage自11:40:11.544068开始，owner与路径相符。本地首次转抄队列plan SHA失败，尚待重新读取确认；只读查询错误未改变队列。队列没有state.json，先查看实际文件名及launcher，不以文件不存在认定队列失败。

## 同步与上传

最新源码提交e9fc57cecc7393fffe14de614eb9b73bdbec3b26已推送并ls-remote确认。包`light-light126-mmio-report-phase-dma16-20261110_112517-e9fc57cecc73.zip`，16672116 B、SHA `5fda05b9858c5908fef7da585a51631fe1b5e1bfc59f16dcbf5b9bef811f7fdc`。683输入、228干净tests、5固件、40生产文件不变；audit `local_runs/mmio8_report_phase_clean_audit_20261110_1127/receipt.json`，SHA `26201989b3e7f9a6cf30d566d0ba5d46007bb413089cc6829b41f795a3c67ef3`。

板端`/home/root/undergrad-mmio-report-phase-20261110`已SHA核验。FTP最初421人数过多，后续曾取得目标目录但空闲超时；11:48左右已在FileZilla选择唯一ZIP按Return上传，**成功回执、服务器安全解包、683输入仍待观察**。不要重复上传。远端目标仍`/IC/light-light126-undergrad-d2-20261109`。服务器已核验工具当前为ecf，不受此报告修复包传输影响。

e9只修原8路报告对RTL/gate起始VALID相位的比较：两者3843121周期，但实际RTL时长比gate短1ns；分别保留观测相位，用gate真实窗口计算功耗，不修改硬件、VCD或full02。上传后用实际两份首层摘要核验compare_windows即可，不为此重跑硬件。

## 缺口及下一步

1. 观察FileZilla成功/空队列，断开最小化后安全解包并核验e9；在服务器验证真实相位比较。
2. 只读确认新队列plan SHA及实际进度文件；不重复启动l02或旧X队列。保存每层结果，完整8路gate结束后安排12PT。
3. 原8路3687端口已全declaration_only；189 no_clock已完整分为186 JTAG DTM＋3 reset同步（182 CK、7 CKN），实际TCK/TMS/TDI=0；仍需保存派生JSON、全量disabled弧及其他结构警告分类，再作独立限定范围审定，不能借16路结论。
4. DMA16其余11层MAC正在队列中；CPU/SRAM/互连/AON未知有效使用及建模影响仍待审核。四点相同不能自动批准功耗。
5. 最终干净服务器复现、完整对照、提交包和答辩材料继续准备。11月13日晚上为用户给定截止，内部H28=11月10日21:16:08、H72=11月12日17:16:08不后移。

## 操作与失败保留

只通过开发板VNC操控服务器、Linux FileZilla上传；不SSH、下载或用隐藏传输。服务器base和各冻结SHA见10:50检查点及三JSON。`F:/linux_fpga_try/ac820.ps1`先刷新windows；11:44 VNC18874435/FZ20972102/panel10485764。UI命令单物理行<1000字符，先本地长度检查，长type会话完成再操作。哈希每行8字符且字符间留空，避免误抄；不要输出长state/owner遮住哈希。旧MAC GCC4.8 regex失败、哈希转抄拒绝、旧37批和所有历史失败目录完整保留。
