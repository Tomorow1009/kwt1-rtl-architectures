# 2026-11-11 09:56：功耗6层完成，继续原队列

用户要求持续按计划实施，不因普通步骤停等。压缩后先读AGENTS、`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点、STATUS/EXECUTION_CHECKPOINT的icb32_c64_execution。完整既有包身份和恢复细节见[09:22检查点及增量](CONTEXT_CHECKPOINT_20261111_0922_ICB32.md)。旧计划、失败和全部原运行目录保留。

## 已完成与当前观察

- **09:52:22.478346实际：唯一queue285397 running `icb32_r4_finish01_power_l07`，completed=6、error=None，driver198924/PT wrapper199532。** L06为71.4343694mW、16.4733024292µJ；目前不是12层均值。09:54:05轻量核对L01–L06的原活动报告，均362618网exact、未标注0，设置averaged/X0.5/initial-Xfalse。
- e65真实ASIC14、354816输出及IRQ/WFI；497真实CPU竞争/恢复；同网表门级14、354816输出及12完整活动均已通过。平均34616周期、150MHz折算4333.256task/s，5000未达。新最终1200还未执行，不能继承旧fcd PASS。
- e65综合DC精确周期6.666666ns，setup+0.0000715256ns、hold+0.000253469ns；224宏，无锁存器/环，新增面积保守上界0.9265616712mm²。稳定任务模式的完整说明和未审范围保留，物理签核不在本轮范围。
- 09:51:07核对实际新综合的标准单元/SRAM库回执哈希。标准Liberty为5d236b15…；两种SRAM为已固定68bd174a…/a75e37ed…，各80 internal_power组、4非零双电源泄漏组、1mW泄漏单位。3个当前DB与原source_inputs全部一致，未启动新EDA。新证据`handoff/team/evidence/ICB32_POWER_PROGRESS_20261111.json`。
- 精确交付SDC已在964 `runs/icb32_delivery_sdc01`生成，receipt SHA7777a8850e91d5283cfd3093bd59173fce3285de01f4a583d0ff16d449850dbb、SDC SHA9f49557c4aee558232cdb90f65c50ef6264250eb1f9c61e95747394e0348195d；不要重复导出。原PT使用6.66667ns序列化SDC，历史结果没重算。
- 当前工具/文档修改只更新交付说明和阶段证据，未改RTL/固件/运行包。新最终报告尚未运行；系统功耗仍false，不能因模型存在或映射完整而自动解除未知活动限制。

## 当前任务与后续

964运行包`light-light126-icb32-r4-20261111_043048-96443c284a1c`为VNC终端cwd，共同bundles父目录仍`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles`。

原顺序不变：power12 → `icb32_r4_finish01_metrics14`（真实ASIC14计数/干净复现）→ `icb32_r4_finish01_final1200`（自己的30412800输出）→生成原report_request。不手动重复、不清锁、不并发大型VCD扫描。batch_progress按实际宿主耗时估ETA并留20%余量。原fcd664task/s退路不变。

最终报告cedb工具包已正常FileZilla上传、8文件及8检查服务器通过。使用它的新report/delivery_sdc，PYTHONPATH指964/workspaces/arch03/scripts。正式目标964/runs/icb32_r4_final_report01。只在原队列终态后新建reviewed request，保留原request，加入精确SDC和两项历史记录；具体文本已本地准备。

共享锁包装器ff181小包**仍未上传**：`light-light126-icb32-export-lock-20261111_093509-ff181611dfaa`，4文件/4777B，ZIP aab947a1a6a9939ad432bbc28f1f8b51a9221b3357ba344343a3450a4df8e573，manifest aa979998df77370f5bd4bcbabe24bacc20a4b4c31a382d6d74d4b0d8381b5380。板端/home/root/icb32_export_lock_0935已SHA暂存，GUI路径/home/board/icb32_export_lock_0935/。09:50正常站点重试仍421连接数过多，已关闭FileZilla，当前无传输。不归因队友、不重复打包；稍后同一路径重试。

## 已准备但尚未执行的命令

均在`E:/fpga_race-two/takeover_local`：

- `icb32_export_lock_unpack.txt`、`icb32_export_lock_preflight.txt`：FTP成功后安全解包、4文件哈希与2项服务器测试。
- `icb32_final_request_prepare.txt`、`icb32_final_request_history.txt`：原queue完整结束后才执行，生成新的审阅请求。
- **`icb32_final_report_locked_launch.txt`是新正确入口**：核wrapper包，后台启动包装器，独立launch.log、新session icb32_r4_export01、原子共享锁，实际报告子进程/state由wrapper记录。尚未执行。
- **旧`icb32_final_report_launch.txt`是无锁直接入口，禁止使用。** 保留文件仅便于识别历史，不能误用。

## 恢复操作和本轮问题

- helper F:/linux_fpga_try/ac820.ps1，VNC最后20971587；先windows再操作。**最后VNC命令为annotation_live**；Up Return会重复活动来源检查，状态查询请type `icb32_finish_live.txt`。
- 此轮未开Windows CUA，无completion_summary欠项。Linux FileZilla已退出；原VNC/relay及服务器进程保持，不需要重启。Get-NetTCPConnection此前确认21036仅有板端SSH，无残留FTP连接；无需再次检查。
- PowerShell ConvertFrom-Json因实际禁用弧键C/c冲突读失败，已用Python正确读取。一次Alt_L+F2被helper拒绝，改为`--keys Alt_L F2`后成功。一次patch同文件delete/add被拒绝，改建独立locked_launch文件；均未影响服务器或硬件。
- `progress_0954.py`已执行，不能重复；09:54文档中的观察时间均取09:52实际。新README/设计/功耗/验收/交付索引已同步事实，未重新测试无改动硬件。
- 后续仍缺：余6层功耗、metrics14、1200、最终报告/交付；R1/旧8完整PPA为次优先，官方600、布局后及物理签核未验证。18:00冻结、11/12 17:16交付准备、用户11/13晚上截止不变。


## 10:12增量：功耗7层完成，锁包装器已服务器就绪

- **10:10:19.302199实际：原285397仍running，L08、completed=7、error=None；driver217238/PT wrapper217567。** L07为71.0550174mW、16.3762850726µJ。10:09:55全部已完成7层的活动来源/设置均复核通过；未知状态影响未自动批准。
- 10:03:20轻量读取首层全部宏泄漏：96小宏各4.88099977e-06W，128大宏各4.60310002e-05W，与固定库默认双电源组吻合；不是0，计数按新网表。证据已加到ICB32_POWER_PROGRESS_20261111.json。还补首层互斥模块表，仅解释构成，不当12层均值。文档泄漏组措辞改为4个非零双电源组（包含默认/条件），未改原库或数值。
- **FTP障碍已解决。** 10:06现有站点正常连接，10:08上传4777B锁包装器ZIP成功、队列空，Ctrl+D/Q关闭后确认FileZilla窗口消失。10:08服务器安全解包ZIP SHA通过，10:09:09 manifest/4文件SHA和两项锁工具检查通过。包身份仍ff181/aab947a1…/aa979998…，不用重传、不再重复解包。
- 独立回执`handoff/team/evidence/ICB32_LOCKED_EXPORT_PACKAGE_20261111.json`。当前报告工具cedb、精确SDC、锁包装器全部在服务器准备好，**正式报告尚未启动**。原request/reviewed request均须等queue终态，不得现在执行。届时用`icb32_final_request_prepare.txt`→`icb32_final_request_history.txt`→**`icb32_final_report_locked_launch.txt`**；这三个是依赖顺序，不能并行。旧`icb32_final_report_launch.txt`禁止使用。
- 本地三条unpack/preflight/locked_launch已Python AST/长度检查，193/585/773字符；其中前两条已执行通过，locked_launch未执行。一次内嵌shell引号检查命令失败，改用PowerShell单引号here-string后通过；无硬件改变。
- 云端994d1157336b9c5474d8707dd2616e61cd0cb58d已于09:56独立ls-remote核对；本增量和小证据待新提交同步。`progress_1012.py`执行后不可重复。当前没有本地长任务，**最后VNC已恢复finish_live**、cwd964、窗口20971587。FileZilla已退出，未有CUA或completion_summary欠项。
- 下一步继续原L08–L12→metrics14→1200。缺口仍是完整新功耗、最终1200、干净复现、最终汇总/提交；R1/旧8完整PPA次优先。不要新增EDA/大波形扫描与当前原队列抢锁，不重启旧作业。


## 10:20增量：功耗8层完成；明确使用查询文本，勿用终端历史执行

- **10:17:29.358582实际：原285397 running L09、completed=8、error=None；driver241591/PT wrapper241973。** L08为70.7083568mW、16.3454135124µJ；10:18:12已核前8层活动来源/设置一致。汇总仍不是12层均值。
- 云端`0832f077276bdad750be49d9c01946e12d93f915`于10:12独立ls-remote核对通过；本次进度增量待再同步。锁包装器已经服务器4文件/2测试通过，**没有FTP阻塞，不要重复上传**。正式report/request尚未执行，原队列继续。
- 10:14自动审批拒绝了“Up+Return”历史重执行，原因是历史内容未获确认、可能造成未授权副作用。已向用户说明，无需用户授权；随后读取并重新type明确的`icb32_finish_live.txt`只读查询，审批允许且10:14/10:17正常返回。**后续不再使用Up+Return，统一type已核验查询文本再Return。** 未停止或改变远端作业。
- `icb32_finish_live.txt`已去掉已结束的旧gate PID209764，只查当前queue/child，873字符。`icb32_power_numbers_live.txt`改为每层总mW/µJ紧凑行及加权均值，并明确COMPLETE_12标记，772字符。`icb32_power_annotation_live.txt`改为SETTINGS顺序的三值tuple，988字符，方便完整12层显示；三者均AST/长度检查。后两种新紧凑版本尚未执行，均只读原小报告，不重扫VCD。
- 当前最后VNC为旧版annotation_live；状态查询请重新type新版finish_live。FileZilla仍关闭，无本地长任务/无CUA。新报告启动入口仍只用`icb32_final_report_locked_launch.txt`，原prepare/history两步等终态后依次执行。
- `progress_0954.py`、`progress_1012.py`、`progress_1020.py`均只执行一次，勿重复追加层记录。下一步原L09–L12→metrics14→final1200→reviewed request/locked report→交付；旧候选和官方未验项不变。
