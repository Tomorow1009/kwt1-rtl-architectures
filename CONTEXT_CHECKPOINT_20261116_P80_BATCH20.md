# P80深度2批量运行与综合修复接续

记录时间：2026-11-16 05:55，北京时间。恢复先读AGENTS、根交接、本文及有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，不要根据历史running记录重启。

## 当前目标和保护范围

- 用户授权连续实施S0→P80→C80→C32-A/可选B→G32。最终32PE、150MHz/6.666666ns、SS/.99V/125°C、项目≤1.00mm²；当前仍为P80，后续阶段没有开始。
- **服务器`Desktop/T80_Delivery_20261113`和所有旧八路文件不写、不移、不删。**本轮没有改变这些文件。S0已有冻结及持久备份，不重跑。
- 原32位ICB和平台参数、源额度3、数据FIFO16/16/输出32保持。源读取→共享写成功ACK→原总线真实读回→解码→最终写ACK/排空；X14/W12/acc32/total33/SHIFT10不变。
- 正式仅前20条/240任务/6,082,560输出，固定12性能任务单独汇总；不扩成100条。

## 必须先收当前输入

**唯一VNC输入exec 65394**：`local_runs/p80_ops_transfer_4cf35b6_20261116/transfer.ps1`，44行，向新`light-light126-p80-4cf35b6`传入审核工具，**只部署、不启EDA**。先等待原会话完成、查看截图/准备回执，禁止并发键入和重复传输。

- 新源`4cf35b6359f48ebaef8bd877fc4a3c00d52b6c5d`，116 overlay文件。
- payload SHA `ca268afa2d21023324c6fb0d28d8e9ed0f34711a4a67c55cb1fae778e07b421e`。
- XZ差分14,748B，SHA `2b670e3ec187ccd576695c5a588236f5eb6dc816911aabf497ab5d0159899e8d`。从服务器原`payload_fa43bc2.json`重建，完整目标SHA检查；原包不改。
- 新包准备成功尚未观察；不能预填manifest SHA。
- 之前所有输入18873/32299/94909/96192/99219/88045/97391/58460/24139/23294/3512/18293/66513/16779均已结束。
- VNC当前18874435、workspace3 Bash。workspace4未操作，FileZilla关闭。压缩后仍须fresh windows/screenshot再决定操作。

## 实际远端状态与已完成

P80运行根`/tmp/s4_21usr_p80_20261116_0315`。

1. **三深度sweep05完整完成**：142包深度2/4/8各ASIC/E20314、每版354,816输出通过。固定12周期各版均`80471,78357,77223,77503,76061,74997,73765,74101,73793,76537,80625,87111`，均值77,545.333333、150MHz折算1934.352378824 task/s。临时选最小深度2，尚非面积/时序/功耗合格结论。不要重复这些14。
2. **功能02父42584**：05:52:54实查status running/current batch20/error=None；自己的恢复十阶段及CPU竞争已经通过。原共享锁由该队列持续持有，串行派发，不改锁。
3. **240当前43/240，零失败**，核对1,089,792输出；batch_progress host332.135秒，含20%余量估计剩余1825.973秒，仅当时估计。
4. **综合等待器47889**：最后05:50:36 waiting_functional02、无错误。只有功能02全部三个阶段通过、父退出、锁自然释放，才启动新7430包`p80_synth_d2_02`。失败则停，不自动恢复失败目录。
5. 原综合01父27509、共享块子30930均退出：146条驱动库选择错误（UID-993/库不唯一），虽然exit0并写了mapped，严格入口拒绝。**这些mapped不能当PASS**。失败目录及日志保持。

功能包e139路径：

- `runs/p80_functional_d2_02/process_ledger`：统一进程账本。
- `runs/p80_d2_sequence_02/p80_sequence`：已通过，自己的10阶段/无复位A/B/A。
- `runs/p80_d2_contention_02/p80_contention`：已通过，真实CPU并发共享访问。
- `runs/p80_d2_batch20_02/p80_batch20`：当前运行。进度`batch_progress.json`，完成前无最终summary。
- 根`p80_functional_d2_02.json`、`.launcher.log`保存队列状态。完成的精确summary哈希由机器回执读取，尚未转写本地，不猜。
- 原功能01父39551在创建`runs`父目录时失败、未启动EDA，锁已释放。功能02仅修正parents=True并用新目录；两个干净目录/注入失败演练通过。原01保留。

综合02入口：根`p80_selected_synth02_controller.py`，SHA `f0ce45ad205f6d87be57529998616d0e5397760c64c8972303ab3e665e6b456e`；根`p80_synth02_wait.json`、`p80_selected_synth02.launcher.log`。正式开始后会生成`p80_selected_synth02.json`。**不要再执行17行启动器。**

## 当前冻结包身份

| 包 | manifest SHA | 文件数/用途 |
|---|---|---|
| 142fae2 | 7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc | 917；三深度真实ASIC14 |
| 8543440 | 42ff74ed50d2da1b348bf69c7750ac231da5a83166519d2c700d43260e681850 | 938；失败综合01，保持 |
| e139032 | c5429439f979357154736a30a2024a8c84fd615b545a2d8974b7ead52ecc52c8 | 940；默认d2、恢复/竞争/240 |
| 7430bb6 | f3406e930f048a73f344736f8b10c2c91651a4b1f43ad3e9b79ebdf785e5ad1a | 940；综合工具修复，等待02 |
| fa43bc2 | 7268edcebeb44b2918bbadba72daaec17395eb466f7bae120c083a4d50a63b6d | 942；新单锁17阶段finish工具，已准备但未运行 |
| 4cf35b6 | 尚未观察 | 当前传输；审核工具，不能先算部署成功 |

上述工具包RTL均与受测P80一致，默认IRQ固件是原已通过的d2字节；e139之后只有工具变化，不能因此转移新网表PASS。原生产硬件实现仍142fae28545759e33fa38de514eabf752cb8c43a。

## 新修复和本地工具准备

- 7430修复只重新绑定characterize导出的标准库限定符：`文件.db:逻辑库`→同一逻辑库名。新旧标准DB必须SHA相同，加载后检查库/单元/引脚唯一。所有驱动弧、转换时间、输入输出延迟和负载保留；12项相关测试通过，实际新DC仍待。
- `p80_finish.py`及3项流程测试通过：同一个原协作锁，结构→门级14→SAIF12→时序/DRC→12层PT，17阶段；源码fa43bc2。新映射面积>1或setup/hold不通过则不能启动。**尚未写/部署其实际request及启动器**。
- 4cf新增P80自己的活动身份、四段窗口、未知活动清单和模型事实连接：`transport_review_contract.py`、`b0_saif_unknown_inventory.py`扩展明确P80身份，`p80_model_review_snapshot.py`只读汇总。33项相关测试通过，含完整P80小型SAIF收集夹具、损坏身份/错误窗口/未知控制端点/环切断拒绝；不是服务器功耗验收。
- `p80_prepare_bundle`仅额外允许两个明确审核helper；其他非P80文件不放开。没有改RTL、算法、数值或原门控状态。
- `p80_report.py`已在e139及后继包中，导出数字不自动批准阶段；尚未创建本轮正式report请求。

## 精度输入与空间

05:45:44重新只读核验：

- FLOAT：`/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip`，143258826B，SHA `5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2`。来源模式exact_original_npz_members；原edb98e容器不是已取得的包。
- NumPy：`/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905`，receipt SHA `c1fe14065d6919ff337f2cbf53551f94941acc35d04d3cadabca311fe742eacd`，记录488成员/1.19.5、系统环境未改。后续显式sys.path及OPENBLAS_NUM_THREADS=1，不能忘记私有环境。
- 数据：原`Desktop/IC/hex_short_all`，正式仅前20；`p80_precision_join.verify`要求本轮240完成，再从完整FLOAT重算并连接，当前未执行。
- 05:44:28 tmp剩91,292,098,560B。共享盘上一观察05:28约1.733GB，不是实时值；没有可删除的预留空间文件。
- 四份N1/B0普通csrc缓存无损归档已完成且持久回读；**不能重复清理**。所有空间恢复及失败身份详见旧P80_SYNTH_STARTED；没有碰T80桌面或旧八路。

## 继续顺序和未完成

1. 收65394输入、核对4cf准备回执，继续观察原42584批量及47889等待器，不启动重复队列。
2. 240通过后原等待器启动综合02。先读取最终同网表面积/setup/hold/宏和结构，立即报告初步结果；工具错误不能吞掉。
3. 用4cf包作为后继操作包，注册7430综合、e139批量、142固定14的显式manifest；创建新精度与finish队列。相同原锁串行，必须先等当前综合结束。SAIF方法qualification仍为原B0包`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck`，summary SHA `a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26`；只复用采集方法，不复用硬件结果。
4. 完成自己的精度、门级14、活动12、PT12、时序/面积/未知活动事实审核、JSON/CSV/中文报告和持久备份，再冻结P80进入C80。
5. C80/C32/G32均未开始；不借旧PASS，不更改样本数或面积口径。

本地：`E:/fpga_race-two/kwt1-c32-g32-20261115`，个人分支`codex/light-light126/t80-pipeline-c32-g32-20261115`，最新已push4cf35b6。唯一旧未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不要提交或执行。没有活跃本地XSim；压缩前/重要进展继续更新本文和根交接。
