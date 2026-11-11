# 2026-11-11 10:30：功耗9层完成，继续最终串行队列

用户要求能继续就一直做；压缩后必须重读AGENTS、有效`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点、STATUS/EXECUTION_CHECKPOINT的icb32_c64_execution，再核已完成/未完成。完整包身份、失败路径和命令来源见[09:56检查点及10:12/10:20增量](CONTEXT_CHECKPOINT_20261111_0956_ICB32.md)；不要按旧暂停记录停止已授权工作。

## 当前真实状态

**10:28:04.057916观测：原唯一queue285397 running `icb32_r4_finish01_power_l10`，completed=9、error=None，driver249722/PT wrapper250112。** 第9层71.3076741mW、16.4459249253µJ；10:28:46前9层活动来源与设置均复核，362618网exact、未标注0，averaged/X0.5/initial-Xfalse。尚无完整12层均值，system_power_verified=false。

当前cwd和运行包为`light-light126-icb32-r4-20261111_043048-96443c284a1c`；bundles父目录`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

队列顺序始终为power12 → `icb32_r4_finish01_metrics14`（真实ASIC14计数/干净复现）→ `icb32_r4_finish01_final1200`（自己的30412800输出）→原report_request。**后两项还没执行，不手动重复启动。** 状态`runs/icb32_r4_finish01_queue/state.json`，数值`layer_XX_numbers.json`。失败保留原运行，不清锁、不自动重试。

10:26按已完成8层的实际stage started/finished计算，每层平均799.541791375秒；当时余4层（当前层保守按整层）加20%预算3837.8005986秒。它不包括后续ASIC14、1200和报告，不能作整体完工时间。批量开始后读取已有batch_progress的真实宿主ETA，不按芯片周期加速比例外推。

## 已完成，不再重跑

- e65真实ASIC/E20314例354816输出与IRQ/WFI；497真实CPU竞争2例/恢复10阶段；同网表功能门级14例354816输出和12活动全部通过，无SDF。
- 12层平均34616周期、150MHz折算4333.256task/s，5000目标未达；原fcd664task/s及其1200独立证据保留。
- e65综合DC精确6.666666ns，setup+0.0000715256ns、hold+0.000253469ns；224宏，无锁存器/组合环，新增面积保守上界0.9265616712mm²。声明的任务模式、接口条件及未审范围保留，不宣称物理签核。
- 当前库/DB指纹与固定标准单元和两种SRAM一致；各80内部功耗组、4非零双电源泄漏组（含默认/条件）。首层实际96小宏各4.88099977e-06W、128大宏各4.60310002e-05W，匹配固定模型默认组，不按零处理。9层功耗数值进度见`ICB32_POWER_PROGRESS_20261111.json`；未知活动影响尚未完成审核。
- 11138端口告警、首层189静态JTAG无时钟引脚/78973常量或条件禁用弧已复核；详细证据和范围见时序说明。未将代表样例扩大为所有结构告警批准。
- 精确交付SDC已在964/runs/icb32_delivery_sdc01导出；receipt SHA7777a8850e91d5283cfd3093bd59173fce3285de01f4a583d0ff16d449850dbb，SDC SHA9f49557c4aee558232cdb90f65c50ef6264250eb1f9c61e95747394e0348195d。原PT导入周期6.66667ns，历史报告未重算；不能改写为PT已用精确值。
- 当前8份实施/验收/设计/功耗/时序/创新/检查点文档中49个本地链接全部存在；未重复RTL测试。

## 最终报告工具全部已在服务器就绪

报告包cedb：`light-light126-icb32-report-20261111_091554-cedb648f3b74`，8文件/8项工具检查服务器通过，manifest SHA4436e191de57d60ae8ebc08883c2d8a2bc9aca68d01c9f4ade413fc86bf6d037。执行新report，PYTHONPATH为964/workspaces/arch03/scripts。

锁包装器包ff181：`light-light126-icb32-export-lock-20261111_093509-ff181611dfaa`，4文件/4777B，ZIP aab947a1a6a9939ad432bbc28f1f8b51a9221b3357ba344343a3450a4df8e573、manifest aa979998df77370f5bd4bcbabe24bacc20a4b4c31a382d6d74d4b0d8381b5380。**10:08正常FileZilla上传成功，10:09服务器安全解包/4文件SHA/2项工具检查通过，不再有FTP阻塞，不重传/重解包。** 原09:37/09:50的421仅历史。见ICB32_LOCKED_EXPORT_PACKAGE_20261111.json。

正式大报告、reviewed request均**尚未执行**。原队列终态后，依次用`E:/fpga_race-two/takeover_local`的：

1. `icb32_final_request_prepare.txt`：核原request SHA，排他建立reviewed request并加精确SDC。
2. `icb32_final_request_history.txt`：补旧37功能TCM主动停止和8192诊断前提失败历史，原request不改。
3. **`icb32_final_report_locked_launch.txt`**：后台启动已核wrapper，原子取得同一共享锁，session `icb32_r4_export01`，输出`runs/icb32_r4_final_report01`。自身state/log在`runs/icb32_r4_export01`，外层launch.log另存。原目录存在则检查，不原地重试。

**旧`icb32_final_report_launch.txt`为无锁直接入口，禁止使用。** wrapper只释放自己的PID/host/bundle/session锁，活子进程或所有权变化保留供检查；大报告将核VCD和1200回执，不能与重EDA并发。

## 恢复操作与限制

- helper F:/linux_fpga_try/ac820.ps1；VNC最后window20971587、800×450，恢复先windows。当前最后是紧凑annotation_live查询。FileZilla已断开退出，VNC/原relay保持，无本地长任务，无CUA会话或completion_summary欠项。
- **所有查询都重新type已核验文本再Return，禁止Up+Return历史重执行。** 10:14该快捷操作被自动审批以历史内容未确认而拒绝，已解释给用户并用明确只读查询安全完成，无待审批或任务阻塞。
- `icb32_finish_live.txt`873字符（不再查结束的gate PID）；`icb32_power_annotation_live.txt`988字符（每层exact/total/unannotated及SETTINGS顺序mode/derate/initial-X）；`icb32_power_numbers_live.txt`772字符（每层mW/µJ，COMPLETE_12明确）。都已在服务器实际使用。`icb32_pt_live.txt`递归看真实PT子进程，外层shell CPU0正常。
- 本地exec返回session时先poll完成再view_image；截图无expect-class。所有服务器操作仍经板端VNC，上传仍用Linux FileZilla，不开隐藏回传/SSH通道。
- 云端已独立确认633ab0079eb3027e7f806da4345165a3be49dcc4；本检查点/第9层证据待提交同步。progress_0954/1012/1020/1030等记录脚本只执行一次，勿重复追加层数据。
- progress_1030首次因缺少显式UTF-8声明在解析阶段被拒绝，未执行任何写入；加声明后Python3.8.20实际执行成功。该本地记录脚本问题不影响远端硬件/队列。
- 后续仍缺余3层功耗、metrics14、候选自己的1200、最终报告/交付收尾；R1/旧8完整PPA次优先。官方600样本精度、布局后功耗时序、物理签核未验证。18:00冻结、11/12 17:16交付准备、用户11/13晚上截止不变。继续完成原计划，不发只报等待的结束答复。


## 10:44增量：功耗10层完成，第11层运行中

- **10:41:40.908382实际：原285397 running L11、completed=10、error=None；driver261567/PT wrapper263202。** L10为71.4054257mW、16.5027443013µJ；10:43:01紧凑活动查询确认前10层362618网exact、0未标注、averaged/0.5/false、未标注清单空。尚未有12层均值。
- 云端0a41eb9b54ef7895bd7b0244e7e1b74fb50f0674于10:32前已独立核对，本增量待再同步。全部报告/SDC/锁包装器仍已服务器就绪，不再上传。新metrics14和1200仍未启动；原队列会自动接续，不要手动重复。
- 当前最后VNC为紧凑annotation_live，FileZilla关闭，无本地运行任务。10:41截图命令曾把helper目录try误写成rty，本地截图步骤失败；查询已输入，改正确路径截图后读到新状态。一次较早截图仍显示命令行，待屏幕更新并对已核验只读命令发Return后仅多出空提示符，无远端变更。以后继续明确type查询、不用历史Up。
- progress_1044.py已执行一次，不能重复追加第10层。剩余：L11/L12功耗→metrics14→1200→reviewed request/history/locked report→最终提交材料。持续执行，不把尚未结束的批量或报告写成PASS。
