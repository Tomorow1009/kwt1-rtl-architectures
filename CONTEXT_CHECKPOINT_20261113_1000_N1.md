# N1执行检查点（2026-11-13 10:00）

## 10:12 增量

- 云端已独立核对为 `012743cd74ebe0e0eda6b44ba5126b73d4eec5a6`，工作在原个人分支。
- 实际10:12:02.109023：原SAIF driver186577仍运行，L01–L10完成；L11 child314052已退出0并wait，但L11最终PASS行尚未出现，先不记成完成11层。最后已确认L10 SAIF97292306字节。
- 新增最终只读导出启动脚本准备：`local_runs/n1_final_export_launch_20261113.py`，SHA `e4308e158a7bba448735d71a50c938933fc841f965aa30e6b3dd6846c13ca33d`。VNC命令为`n1_final_export_launch_00.txt`至`06.txt`共7片，已检查Python3.6语法和单引号编码回环。**未运行**；仍须先执行原final_request准备、确认队列13子项结束且原driver退出/锁空闲。
- 启动脚本只调用已部署的原`n1_report`，控制记录为精度OPS02内`final_export_control01`，输出为`final_report01`。不会自动批准N2。
- 现有B0未知活动清单工具增加N1独立身份支持，本地17检查通过。N1必须匹配自己的格式、布局、shift、行数、活动、综合和门级身份；不借B0结论。尚未部署/运行，后续在最终N1导出完成后用于真实未知活动审阅。没有RTL改动，也没有重跑任何已完成硬件任务。
- 工具代码/测试SHA和导出脚本完整文本记录在 `handoff/team/evidence/N1_FINAL_REVIEW_TOOLS_20261113.json`。旧B0工具和证据留在原运行包内不改。

## 恢复原则

用户要求持续推进，完成N1精度和功耗验收后直接进入N2，并同步GitHub。有效计划仍为`workspaces/arch03/IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`。先读AGENTS、CONTEXT_HANDOFF、本文、计划和STATUS的`narrow_execution`；完整老路径和SHA见09:00/09:25/09:35检查点。**N1仍未验收；N2/D1/D2没有开始实现。**

## 原作业与队列：不重复启动

- 唯一正式活动采集仍为0f62包`runs/n1_saif12_01/n1_saif`，driver **186577**，08:32:45.846649开始。
- 最后实际**09:56:30.070018**：L01–L09完成，L10 child **284416**运行；L09 SAIF **97262320 B**，前child268257退出0且已wait。尚无完整SAIF12终态，不能提前填summary SHA。
- 原续跑队列`runs/n1_acceptance01` driver **237710**，09:22:09.356991开始。最后实际09:43:28.130300为`waiting_original_saif`、child_pid=null、completed=[]，原锁归186577。
- 此队列会自动串行运行一次`n1_acceptance01_precision/n1_precision`及`n1_acceptance01_p01..p12/n1_power`。**不要手动启动同批精度/功耗，也不要再运行已通过的ASIC1200/门级14。**队列结束仍需独立报告和准入判断。
- 查询文件：`takeover_local/n1_saif12_monitor_0836.txt`、`n1_queue_compact_status.txt`。VNC终端当前空闲，最近只运行已结束的只读du。

## 已完成与本轮新成果

- N1生产硬件9305c694、旧运行工具0f62e412不变；自己的ASIC14、恢复/竞争、10000随机块、1200任务30412800输出及同数量total、同网表无SDF门级14均已完成。原始摘要不重写。
- 本地100个原FLOAT成员精度复算完成，最高合并逐层NRMSE **0.1933721614699203%**，最高单条单层 **0.20953408931848963%**，裁剪/饱和0。正式服务器原4800HEX与ASIC回执关联仍待原队列和最终导出。
- 固定12平均29711周期、5048.6352task/s；相对B0吞吐+2.6634%。全部12层周期下降量等于编码字节下降量的一半，不能全部归因于MAC缩位。
- 面积保守上界0.9511486879mm²；全部SoC标准单元和92内部宏计入，仅排除128复用大宏。新`N1_PRE_POWER_SCOPED_REVIEW_20261113.json`审阅了归属和结构；仍需实际PT时钟/禁用弧。
- 原DDC阈值1000查询3条平台时钟网，原TIM-134曾报告4条，保留差异及综合模型限制。结构11324个仅声明端口、262无负载驱动全部对应，其他警告为常量/同网多引脚和4个原平台未用实例。
- 当前N1叶单元表有15个`CLKLANAQV4_12TR40`，该库族在加速器内为0；面积合计67.032µm²。记录为现有库族统计，不能称N1已经完成加速器实际门控。证据`N1_EXISTING_CLK_GATES_20261113.json`。

## B0功耗模型审阅

新证据`B0_MODEL_AND_DISABLED_ARC_REVIEW_20261113.json`：

- 12层宏泄漏值一致：128宏4.88099977e-6W，4096宏4.60310002e-5W，符合RET1N高时两电源轨默认泄漏之和。
- 共享SRAM L01 internal约4.447735mW、总约7.393719mW；net switching单列为0不代表宏总功耗0。
- 完整12层原disabled_timing均经原SHA核验，各77806行：p14128、C61492、c1985、d201。全部为常量传播/条件/case/default弧，没有l/L循环切断或u/U用户禁用弧。
- B0均值仍69.8371mW/14.2013µJ布局前估算，**未知活动全系统影响还未宣告通过**。现有所有12层未知清单和控制采样不重跑；不能把缺少宏别名或全程未知声明简单当0。

## 归档工具已更新、部署；归档未开始

旧归档器不识别本次续跑队列的独立终态schema，已增加明确支持：仅终态/无活动child，绑定原request和已完成子阶段摘要；失败前缀保留，归档不授予PASS。runtime24测试通过，辅助17测试更新helper SHA后通过。首次辅助pin更新使用错工作目录，测试正确拒绝旧pin，已修正。见`N1_ARCHIVE_QUEUE_SUPPORT_20261113.json`。

新独立工具目录：`/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-archiveops-fe65a94dc736`。

- ZIP **17399 B**，SHA `bf8e5ae82da537c56b1bd8d0c721540aae015382473ca54119d54bc9c7235a12`。
- manifest SHA `0138db31e048709dccb84fd4b9fc29eb2e728b1eea95ec448b3cf31b17115394`。
- runtime.py SHA `fe02e6774de23bdccf4cc817823de1728bbfdac08110ebb76c423617265df616`。
- auxiliary.py SHA `35aa58afc2ee37653643465321236c07175f82bba088fd67bcef636f0e894627`。
- paths.py仍`fe301e1e5f87852103c537b8191c7064f1b8c44a8979f1977901bf26ed16e39d`。
- 09:52:36.210387实际解包，全部成员哈希与随后导入依赖检查通过。**未运行归档、未删除文件。**FileZilla上传已完成并关闭。新ZIP本身留在共享项目根目录。

共享空间实际09:44:30为**9036627968 B**，无需本轮再删除。09:58的近似du：9305包740644KiB、41b包254132KiB、0f62包4981440KiB；后者仍增长。正式归档仍需结束后检查原锁、进程及工具实际压缩预算，不能用du代替最终清单。

## 最终报告准备（未执行）

`local_runs/n1_final_request_prepare_20261113.py`，SHA `be2e94e358c6f587ced401090dcc0b41db410a0e5b9a2aa97f5745f2e8c1b367`，3302B。对应VNC命令分为`takeover_local/n1_final_request_prepare_00.txt`到`05.txt`（650字一段，共3603字）。仅在原队列终态且13项齐备后执行，它会核对原request SHA、各阶段summary SHA，再新建**精度OPS02目录中的`final_request01.json`**。现在没有运行，也没有待输入片段。

计划使用原已部署`precisionops02/scripts/n1_report.py`，配合私有NumPy和0f62脚本路径，对原产物做一次只读独立导出。建议输出新目录`precisionops02/final_report01`，该目录随已有辅助归档白名单中的整个OPS02保存。还未编写/执行正式launch；启动前核对锁和原队列终态。报告可能保持原`stage_handoff.allowed=false`，必须另写独立准入证据，不能直接改布尔值。

## 下一步

1. 看原SAIF完成及续跑队列自动进入精度；按实际进度更新宿主耗时，不重复启动。
2. 首个N1功耗出来后核对时钟、映射、宏功耗、未知活动和B0同条件；12层齐后独立导出。
3. 对精度、面积、声明时序和相对P/J门槛作独立结论。按当前周期，能耗不增加对应平均P约≤71.6971388mW，比单独110%约76.8207807mW更严格；仍须用最终原始值。
4. 满足N1阶段要求后冻结、同步并直接实施N2。未满足的真实缺口先解决，不用旧B0或本地软件PASS代替。
5. 原任务全部终止、原锁空闲时，使用新归档工具做完整持久化备份，保留/tmp原件直到全量核验成功。

当前Git云端已核验`fe65a94dc7360892bfe3f7d4c052cb4e4efd6add`；本检查点、部署和ICG小证据待同步。没有未结束本地工具会话、没有未按Return命令。VNC18874436/workspace3，workspace4不操作。
