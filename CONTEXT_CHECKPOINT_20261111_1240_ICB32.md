# 2026-11-11 12:40：最终1200已过九成，准备锁内报告

用户要求持续按计划执行，不逐步等确认。压缩后先重读AGENTS、`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点、STATUS/EXECUTION_CHECKPOINT的`icb32_c64_execution`。原计划与全部尝试详见[11:20检查点及增量至12:26](CONTEXT_CHECKPOINT_20261111_1120_ICB32.md)。本轮不新增结构优化、不重启已有作业。

## 当前实际状态

**12:37:59观测：原queue running/errorNone，1086/1200任务、27523584输出、零失败，含20%余量ETA11.2分钟。** 原queue PID285397、batch driver292229最后已核身份未改变；当前前台还有轻量只读monitor。最终1200尚未完成，最终报告尚未启动。

VNC第三终端当前**不是shell提示符**：运行`takeover_local/icb32_batch_readonly_monitor.txt`（608字符），每30秒读取原state和batch_progress，原queue离开running后自行退出；最长360次。现在只需截图查看，勿直接type新shell命令。窗口20971587、800×450，字体已放大一次。FileZilla关闭，无本地长任务，无CUA会话。恢复先用helper的windows确认窗口。

本机helper `F:/linux_fpga_try/ac820.ps1`。查询只用明确文本，type成功后才Return，不使用Up历史；文本≤1000字符。远端shell不接受此前嵌套引号monitor，已改成当前单行lambda，正常运行。不要把查询失败当作仿真失败。

## 完成项，不重复运行

- e65真实ASIC/E20314例、354816输出、真实IRQ/WFI；497真实CPU竞争/无复位恢复、同网表14功能门级354816输出及12完整活动；无SDF。
- 964干净目录metrics14再次通过14例354816输出；原日志计数和摘要/queue/stage SHA独立匹配。每例MAC1622016，X读101376/写6336，W读409600/写16384。
- 12层均值34616周期，150MHz折算4333.2562977task/s，未达5000。当前格式平均31223.333事务本身已超过30000目标，不改计时追数。
- 完整12层布局前整机加权平均71.8126318538mW、平均16.5724387711µJ/task；动态约64.544、泄漏约7.269mW。相对fcd平均44.5930996895µJ能耗降62.8363%，但平均功耗增至约2.424倍。全部12层362618网exact、无未标注；**system_power_verified=false**，未知活动影响尚未完全审核。
- 声明的SS/.99V/125°C、精确6.666666ns稳定任务模式综合时序及项目面积保守上界已独立接受：setup+0.0000715256ns、hold+0.000253469ns、上界0.9265616712mm²。见`ICB32_SCOPED_REVIEW_20261111.json`；只接受该范围，不修改原阶段false标记、不批准官方面积/精度或物理签核。
- 全11138未用端口和706无负载net均已核对应声明无逻辑引用；189 no_clock均静态JTAG，78973禁用弧无user/loop/false-net。新LINT2回执964/runs/icb32_lint2_01.json SHA8a67d41bf37ecff3e16986c8f6e134782f7d7eb3617358c907974d891b576371。
- 精确交付SDC已在964/runs/icb32_delivery_sdc01导出一次。原PT仍导入原6.66667ns SDC，不声称已重跑。新SDC SHA9f49557c4aee558232cdb90f65c50ef6264250eb1f9c61e95747394e0348195d，receipt SHA7777a8850e91d5283cfd3093bd59173fce3285de01f4a583d0ff16d449850dbb。
- 44个当前文档链接、7份范围审阅证据引用已检查；创新说明已补完整窗口fcd/R4收益和代价。R1/raw局部实验明确为本地，不冒充完整PPA。

## 后继报告：所有包已上传，不再传送

VNC cwd为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261111_043048-96443c284a1c`，简称964。

原state：`runs/icb32_r4_finish01_queue/state.json`；batch：`runs/icb32_r4_finish01_final1200/icb32_batch`。完成后必须读实际终态和完整1200/30412800/failed0、核共享锁释放，不能仅看monitor到1200。

本机`E:/fpga_race-two/takeover_local`的三个prepared入口均**尚未执行**，只在原queue达到`reports_ready_review_required`后按顺序使用：

1. `icb32_final_request_prepare.txt`：核原request SHA，排他建立reviewed副本，绑定精确SDC。
2. `icb32_final_request_history.txt`：写旧37任务用户停止及8192诊断前提错误/后续4096修复历史，不改原request。
3. **`icb32_final_report_locked_launch.txt`**：启动ff181锁包装器，原子取得共享锁，session`icb32_r4_export01`，输出`runs/icb32_r4_final_report01`；状态/日志在`runs/icb32_r4_export01`，外层`runs/icb32_r4_export01_launch.log`。**禁止旧无锁icb32_final_report_launch.txt。**

报告包：`light-light126-icb32-report-20261111_091554-cedb648f3b74`，manifest4436e191de57d60ae8ebc08883c2d8a2bc9aca68d01c9f4ade413fc86bf6d037，8文件/8检查服务器通过。执行此新report，PYTHONPATH绑定964/scripts；不能误用964旧report。

锁包装器：`light-light126-icb32-export-lock-20261111_093509-ff181611dfaa`，manifest aa979998df77370f5bd4bcbabe24bacc20a4b4c31a382d6d74d4b0d8381b5380，4文件/2检查服务器通过。10:08已上传核验，旧FTP421早已解决。wrapper只释放自己PID/host/bundle/session锁，遇现存目录/锁不清除，不原地重试。

原ASIC/综合e65、gate497、运行964身份已绑定，生产RTL/IRQ ELF/加载映像一致；诊断序列ELF非装载调试节有差别，不能说所有ELF相同。

| 摘要 | SHA256 |
|---|---|
| e65 ASIC14 | e5d009732e822cb5cf730e85b652a160f5022ba0197a9e6ff60960d76121d604 |
| e65综合 | fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d |
| 497 gate14/activity12 | 95113a35bf2941e985d8d1b8cbad7d88c0d56f07d3c1f533f0fcf549fb2efc7f |
| 964 metrics14 | bb0ee4cf23b31730d72c196bfc5101f3d2f49e7d1dea33b49e366a72de54e576 |

## 剩余与云端

当前剩余最后114任务、全回执/12活动同配置锁内汇总、交付收尾及真实限制说明。原fcd完整功能/1200退路不变；R1/原8完整PPA次优先，不为了新对照挤占最终链。官方600、布局后时序/功耗及物理签核未验证。硬冻结11/11 18:00、交付准备11/12 17:16、用户截止11/13晚上不变。

云端最后独立确认 **833342d696146f508d655c56cdc356f7c17a70d5**；本检查点及九成进度准备同步。远端服务器到本机不另开回传通道，大产物保留服务器目录/哈希；小型源码/证据继续已授权私人分支同步。不要因等待而结束本轮，原queue终态后继续完成报告。
