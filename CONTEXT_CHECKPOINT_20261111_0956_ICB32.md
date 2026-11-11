# 2026-11-11 09:56：功耗6层完成，继续原队列

用户要求持续按计划实施，不因普通步骤停等。压缩后先读AGENTS、`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点、STATUS/EXECUTION_CHECKPOINT的icb32_c64_execution。完整既有包身份和恢复细节见[09:22检查点及增量](CONTEXT_CHECKPOINT_20261111_0922_ICB32.md)。旧计划、失败和全部原运行目录保留。

## 已完成与当前观察

- **09:52:22.478346实际：唯一queue285397 running `icb32_r4_finish01_power_l07`，completed=6、error=None，driver198924/PT wrapper199532。** L06为71.4343694mW、16.4733024292µJ；目前不是12层均值。09:54:05轻量核对L01–L06的原活动报告，均362618网exact、未标注0，设置averaged/X0.5/initial-Xfalse。
- e65真实ASIC14、354816输出及IRQ/WFI；497真实CPU竞争/恢复；同网表门级14、354816输出及12完整活动均已通过。平均34616周期、150MHz折算4333.256task/s，5000未达。新最终1200还未执行，不能继承旧fcd PASS。
- e65综合DC精确周期6.666666ns，setup+0.0000715256ns、hold+0.000253469ns；224宏，无锁存器/环，新增面积保守上界0.9265616712mm²。稳定任务模式的完整说明和未审范围保留，物理签核不在本轮范围。
- 09:51:07核对实际新综合的标准单元/SRAM库回执哈希。标准Liberty为5d236b15…；两种SRAM为已固定68bd174a…/a75e37ed…，各80 internal_power组、4非零条件泄漏组、1mW泄漏单位。3个当前DB与原source_inputs全部一致，未启动新EDA。新证据`handoff/team/evidence/ICB32_POWER_PROGRESS_20261111.json`。
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
