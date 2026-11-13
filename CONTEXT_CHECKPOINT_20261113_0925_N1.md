# N1恢复检查点（2026-11-13 09:25）

## 09:26增量：本地数值探测已完成

下面所列本地exec72577已结束（exit0），不再轮询或重跑。实际09:24:33.559923至09:25:20.358812；100条/1200层/30412800输出，逐k模型与PR矩阵模型全一致。最高逐层汇总NRMSE **0.1933721614699203%**，最高单条单层 **0.20953408931848963%**，X/W/b裁剪和结果饱和全部0。已计算4800个派生HEX SHA，但尚未与服务器原HEX集合关联，仍不宣称正式精度通过。完整本地summary及脚本保存于原run，小型指标、12层汇总与实际脚本文本写入`handoff/team/evidence/N1_LOCAL_FLOAT100_NUMERIC_PROBE_20261113.json`。

## 当前目标与恢复入口

用户要求连续推进：先完成N1精度与功耗验收，通过后直接进入N2，并同步GitHub。有效计划仍为`workspaces/arch03/IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`；没有改路线或取消门槛。**N1尚未验收，N2/D1/D2未开发。**

压缩后先读AGENTS、CONTEXT_HANDOFF、本文件、计划及STATUS的`narrow_execution`。上一份`CONTEXT_CHECKPOINT_20261113_0900_N1.md`保存完整已测路径、全部hash与源恢复过程；其“队列尚未启动”已由本文件更新。

## 运行中的两项身份（仅一个正式硬件作业）

- **原SAIF12**：0f62包`runs/n1_saif12_01/n1_saif`，driver **186577**，08:32:45.846649开始。最后实际09:19:03.475744：L01-L05完成，L06 child **235046**；L05 SAIF97287836B，前child224849退出0并已wait。不要重复启动SAIF。
- **新N1续跑队列**：0f62包`runs/n1_acceptance01`，driver **237710**，09:22:09.356991开始。实际09:23:32.154951为`waiting_original_saif`、child_pid=null、completed=[]、driver.log 0B。原共享锁仍归186577。此队列只观察当前SAIF，完成后按顺序运行一次精度及12个功耗阶段，不重跑SAIF/ASIC/gate，不批准N2。
- 后续精度会话为 **`n1_acceptance01_precision/n1_precision`**；功耗为 **`n1_acceptance01_p01..p12/n1_power`**。早先`n1_precision100_01`命令仅准备过，**不执行它**，否则会重复运行。
- 队列失败则保留已完成前缀、停止后续，不在原目录重试。队列结束状态`numbers_ready_independent_review_required`仍不等于N1通过。
- 只读查询：`takeover_local/n1_saif12_monitor_0836.txt`；`n1_queue_compact_status.txt`（短输出）；`n1_queue_status.txt`（含log/lock，lock不存在时末段会报缺文件，不代表阶段失败）。

## 新部署与已同步代码

Git个人分支仍`codex/light-light126/arch03-n1-n2-d1-d2-20261113`。已push并ls-remote核验 **b87494a7c8f72c78e708d7dd0567d9ba7fd678ab**；生产硬件9305c694、运行依赖0f62e412、B0备份标签不变。

1. `n1_precision_stage.py`新增原锁包装；退出失败不标PASS，保留输出。单独生命周期4测试通过。
2. `n1_acceptance_queue.py`新增受控续跑；精确匹配原SAIF的PID、开始时间、gate/synth身份和12层集合；等待原锁，子进程必须wait后才继续。队列加生命周期共9测试通过。
3. 精度实现仍此前已测`n1_recovered_precision.py`，独立恢复NPZ来源模式，没有放宽原ZIP入口。

### 精度OPS02（已部署/烟测）

目录`/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-precisionops02-20261113_090845`。

- ZIP19831B，SHA `bdb238887de565a1461849a0c95c3bdee3974de158ac65348a62efd4f9c1a5f8`。
- manifest SHA `6acb84a3292dc7d40f3071cc30291ce0af6f23cfa9f998b17679a44a87e1a71e`。
- stage.py4994B SHA `d31e7ffc2a643cd60dfc014e39194e0480f7128a76aec52b6b69c19b02d4b7b4`。
- recovered_precision.py9956B SHA `61a5099fe0d3f8ded611a83067aa035d053ed61dbd6e0204e84553c42f18c585`。
- report.py43738B SHA `6245fbdc5b6b4db022903964d729cd58a76fc614f942adf94cc7c9519dd044a9`。
- 09:13:54服务器NumPy1.19.5、operations_identity、common.ROOT=原0f62包全部通过。

### 队列OPS（已部署/运行，不重复launch）

目录`/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-queueops-20261113_091833`。

- ZIP4236B，SHA `61c306f2e23b8be0c77e4572e9b64a6f39d40da01a6e70c76298400ec10c6b3c`。
- manifest SHA `da964f9fc151680348e5b05f4793c5c03a815666d69abe5ed6895fc2b6434dfe`。
- queue.py8105B SHA `c211b117ad1c9e117e989c66543f9bbd2a8b2ed2680772b47fa3a8e1e3ac5ef2`。
- request.json1595B SHA `53028caf11703f75c159e19de43627f12cf7a63cde6e14b886c71937a424b944`。
- 实际上传成功、所有成员SHA核验、旧作业/锁核验、唯一新队列启动均已观察。原文件均保留。

## N1已通过与待完成

- 自己的ASIC14、恢复/竞争、10000随机块、完整1200/30412800 result+total均通过；新同网表gate14/354816输出通过，无SDF。原各summary SHA见09:00检查点，不重跑。
- 原综合220宏、0锁存、无组合环；面积保守上界0.9511486879005002mm²；setup +0.0000510216ns、hold +0.00153732ns。独立任务模式最终审阅仍待，不能当物理签核。
- 固定12平均29711周期、150MHz折算5048.6351856 task/s；不是芯片实测，不到6300。
- 完整100个原FLOAT NPZ与原W/b哈希全部匹配。原ZIP容器未获得，已用明确的新容器身份，不伪造原ZIP SHA。
- 正式完整精度尚未开始；队列会做与4800原HEX逐字段/字节检查，然后最终报告关联已通过的N1 ASIC1200。N1实际功耗尚无数值。
- 最后需要一次`n1_report`独立导出及原1200回执重审、N1/B0未知活动与模型/时序/面积审阅、准入比较、持久化归档。原报告工具有意保持`stage_handoff.allowed=false`，不能直接改布尔值当作独立审核。

## 当前本地软件任务

为在等待服务器时推进精度，开始`local_runs/n1_float100_numeric_probe_20261113_0925/run.py`：对同100个已证实原NPZ重新量化，用已有逐k独立整数模型与PR矩阵模型比较，计算合并SSE/参考能量和四种派生HEX的SHA。不读服务器原HEX，不当作正式精度/硬件通过。

截至09:24:54本地exec **72577**仍运行，已到40条。恢复先收此会话或检查其`summary.json`，不要重复运行。源码脚本保存在该run，最后必须记录它的hash、summary与结果。后续正式服务器精度依然必要。

## B0未知活动审阅进展及边界

- 完整12层未知清单和全部12层selected-control采样已齐；L02-L12 hash重核通过，selected558/层、selected_unknown0、required_missing1356；shared read_pending全窗口为0。这不等于全宏引脚无缺失。
- 新只读L01分类：全程未知18620条的TC非零数为0。高频名字为未读rdata/qout、FIFO/rf存储、闲置AON接口。部分未知包括committed_data每位14.666652ns、X缓存响应x_q示例6726.675994ns；不能仅由驻留总长推定其时间位置。
- 共享控制器源码在read_pending时才取bank_data；实际全窗口read_pending0。已核验宏正常写时Q保持、泄漏/内部写模型存在，因此Q未知不等于共享SRAM功耗为0。全局声明别名、空闲接口及部分未知影响仍需最终解释；禁止一概豁免。
- 本轮没有新增B0/VCD/PT作业或修改活动。停止无界逐门审阅；保留所有工具数值与未知限制。B0仍69.8371mW/14.2013µJ布局前估算，system_power_verified=false。

## 空间、桌面、失败尝试

- 实际09:13显示private可用522.179GiB、shared约0.005GiB。新队列/正式输出全部在private；最终持久化空间仍待。没有新清理/删除。
- 原库/数据/平台仍从shared只读使用。新上传都只有小工具包，均成功并核SHA。不要再次上传数据或恢复已取消任务。
- VNC18874436，workspace3，当前空提示符；FileZilla已关闭，workspace4不用。远端shell tcsh，cwd仍shared9305包。
- helper为`F:/linux_fpga_try/ac820.ps1`；type单次最多1000字，拆650并逐段等待返回。FZ key/type/click需`--expect-class Filezilla`，screenshot不接受该参数。
- 本轮一次FZ key忘记class被保护拒绝、一次BusyBox cp -n不支持、一次upload缺父目录失败：均已用明确创建新目录/重新upload修正，无覆盖或数据丢失。不要重试旧失败命令。
- 新queue启动已执行一次；没有待按Return文本或未收functions cell。Git新增本文件/队列运行证明待同步。
