# C80 服务器验证接续检查点

## 13:56继续：不干扰综合，独立后续入口已准备

13:55:53只读ps显示原加速器子299424运行1090秒、CPU99.8%、RSS约8.2GiB；父279630在等待子进程。日志没有新增行不等于挂起，不重启。tmp剩余84,166,864,896字节。最终综合摘要尚未生成。

新增本地`c80_precision_recovery.py`严格只接受原队列最后精度阶段缺NumPy的失败：前五项自己的硬件阶段必须全部通过、原父/子均退出；新精度目录和同一协作锁，原失败回执不修改。归档器增加显式连接“原五项＋独立精度恢复”的路径，仍不自动验收。八项负向/身份测试、Python3.6语法通过，尚未部署或运行。

准备`handoff/team/evidence/C80_FINAL_FOLLOWUP01_20261116.py`：待原initial02自然结束才允许新作业；仅上述缺依赖失败时恢复精度，再调用原受测包的`c80_finish.py`串行门级/SAIF/PT。此脚本也尚未部署/启动，不能把预备文件当活跃任务。绑定已有NumPy1.19.5收据`c1fe14065d6919ff337f2cbf53551f94941acc35d04d3cadabca311fe742eacd`，不改全局环境或运行包。

## 13:50接续增补（优先于下文历史状态）

- 已按要求重读计划、AGENTS、根交接、状态及本检查点。最新push33f682f，正式受测74f3ae7不变。
- 13:49:21原initial02 PID279630仍running/synth；加速器DC子299424于13:37:42开始，fresh_link296877已完成。尚无最终面积/时序。
- 三个0360ee8审核/归档工具已部署到独立`ops-review-0360ee8`目录，全部111个加载模块绑定原包或三个新文件。回执SHA `b0e9bdd832aebeae46762c213f5a60cdede7ddb2c812c34dc6c64795e1bf0f3f`。payload SHA `d4ae5f8aafcf5b69f905176f0d202f698d47a8c829048bf5d5e5b6d981168c96`。未启动归档或EDA，未修改原运行包。
- 17/17输入已完成，第一VNC标签空闲。第二只读观察器300443于13:39:59开始，40×20秒自然结束；约13:53后须现场确认。18874435窗口本轮已刷新。
- 依赖预检发现服务器默认NumPy缺失，运行父进程PYTHONPATH/OMP/OPENBLAS均未设置。综合、ASIC批量不依赖NumPy，继续原队列；后续精度可能自然失败，准备仅恢复精度的新入口。不能修改活跃进程/全局环境/受测包，也不能把失败原状态改为通过。旧数值运行时1.19.5及收据可只读复用，须单独绑定路径与哈希。
- 本次无删除、无新硬件修改、无C32/G32。T80桌面、旧八路、P80原包和备份不动。

更新到2026-11-16 13:35观察。恢复先读AGENTS、根交接及有效计划 `workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`。时间和PID均为最后观察，不能当实时，更不能据此重启队列。

## 当前目标与保护要求

S0、P80已各自完整验收归档冻结；当前只推进C80，之后才C32-A/可选B、G32。最终32PE、150MHz/6.666666ns、SS/.99V/125°C、保守计入面积≤1.00mm²。四段源读→共享写ACK→原总线读回→完整输出写ACK必须保留。正式批量只前20条×12层。

**服务器桌面T80_Delivery_20261113、全部旧八路不写、不移、不删。** P80冻结原目录和copy03备份同样保留。本次上下文无服务器删除，也未启动旧队列、C32或G32。

工作区 `E:/fpga_race-two/kwt1-c32-g32-20261115`，分支 `codex/light-light126/t80-pipeline-c32-g32-20261115`。最新已push **0360ee8**；受测包仍74f3ae7，不随交接提交变化。唯一历史未跟踪 `handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py` 不添加、不运行。

## 正在运行：唯一 C80 initial02 队列

- 根：`/tmp/s4_21usr_c80_20261116_1245`。
- 包：`light-light126-c80-74f3ae7`，1,008文件。
- 包清单SHA：`d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59`。
- payload SHA：`37f628a694c031547ce30bac9f764e7f0b353b787bf6be6a232a0a6cfe7055ac`。
- 受测提交：`74f3ae7bb479d5fdd7917702c4a2c0671eacb61b`。RTL/固件自首轮本地通过后没有修改。
- 队列源码SHA：`f04f6f4644faf26832c7e757db0a5e98f3e30e2eb844bee7816bdad17aca5500`。
- 启动脚本SHA：`5ca11bfe9beae75c9285b42aeb1b33ee669bfae2fce0b026bfbb36775071d792`，本地 `C80_QUALIFICATION02_LAUNCH_20261116.py`。
- 13:21:31启动，父PID **279630**；主日志 `c80_initial02.log`，启动回执 `c80_initial02_launch.json`，请求 `c80_initial02_request.json`。
- 队列状态：包内 `runs/c80_initial02/state.json`；子进程账本 `runs/c80_initial02/process_ledger`。原团队锁由唯一父进程持有，不能清锁或启动另一个EDA。
- 13:31:03为running/synth，已完成soc、sequence、contention。13:34:57新链接子 **296877** 正常running，始于13:32:06；目录 `runs/c80_initial02_synth/c80_synth/fresh_link`，最新 `c80_link.log` 正在设计展开/uniquify，SysMem端口核对marker已输出。不是最终网表PPA。
- 队列顺序 ASIC14 → 恢复 → CPU竞争 → 新分块综合 → 自身240 → 新FLOAT精度。ASIC14之后已核对同样本吞吐确有改善；综合面积/数值时序不通过会停止长批量。
- 启动时tmp84,608,491,520B、共享19,401,913,336B，后续启动前需重读空间。

不要改受测包中的源码、工具、固件或manifest。现有队列会自然推进，不重新运行已通过项。

## 已通过的服务器结果

1. ASIC/E203十四例354,816输出，total/result/saturated及坐标一致。
   - `runs/c80_initial02_soc/c80_soc/summary.json`
   - SHA `4c3668ebe351804b43edd8cf1ec4a56ab4004ed2c8724cc73a8afcc4929b7cb1`。
   - 固定12周期：73186、71625、70620、70696、69233、67609、66776、66966、67042、69450、73829、80206。
   - 总847238，平均70603.16666666667，150MHz折算2124.550598533116task/s。
   - 同逻辑样本P80总930544，吞吐提升9.832656231188874%；完整四段计时，没有省略共享写/读回。不是芯片实测。
2. 十阶段恢复/无复位A-B-A已通过：`runs/c80_initial02_sequence/c80_sequence`。
   - SHA `a2f821f4971f7624cd7a5990062a90da3a2284183a4b1e96ec2f85035c698b01`。
3. 真实CPU竞争通过：`runs/c80_initial02_contention/c80_contention`。
   - SHA `497b3b05bf4db090886e7f0e6b86a05f102dc2fe1d9067bc5af7171584ba9017`。
   - 竞争L01 92654周期，不混入无竞争固定12均值。

上述摘要转录自可见VNC，冻结前应再用服务器机器断言校对关键哈希。尚无C80综合、240、门级、活动或功耗通过结论。

## 本地已完成与新工具

原本地48解码场景、14矩阵、10阶段/ABA、两拍SRAM、预取开关、raw回退、10000随机＋32定向块，详见C80_LOCAL旧检查点。不重复原已通过测试。

本上下文补查未改的P80搬运及仲裁组件：

- `local_runs/p80_transport_20261116_131300_226444`，SHA `667dc6d26ae4c712471f961a23f3f11d380c615c7590ed7e824a26b7813f20a8`。深度2/4/8各9场景；四类错误、最终ACK、取消多笔、复位、反压等。
- `local_runs/p80_arbiter_20261116_131300_216658`，SHA `7c9d089309da4a426957808fe91c1627b0c6952aee5eed221b9655ac3e152199`。三深度公平性、同时出入、错误转发、归属及复位。这是复用组件验证，不是E203证据。

已提交独立C80模型审核入口 `c80_review_contract.py`、`c80_saif_unknown_inventory.py`、`c80_unknown_connections.py`，10项相关测试通过；这些已在74f包。

**0360ee8新工具尚未部署到服务器：** `c80_model_review_snapshot.py`、`c80_archive_contract.py`、`c80_archive_runtime.py`及3个测试文件，7项测试通过，Python3.6语法/完整导入通过。归档明确核对initial＋finish两个已结束队列及其自身report，只复制并全量回读，绝不删除源。后续作为独立、哈希绑定的工具投放，不修改正在运行74f包。

## 失败及传输路径

第一719afc0仅传输中转；第二083f47a的1003文件包核验成功，但initial01在脚本自身哈希处把str传给Path接口，子276128/poll1立即退出。未创建队列目录、没取得锁、没运行EDA。修复74f3ae7并新增实际入口正负测试，4项通过；原失败目录、日志全部保留。

修复包通过可见VNC输入20段，局部exec76477已结束。所有本地传输/编译/测试会话已结束，不要轮询或重启它们。

FTP因DNS公共地址限制未用，未绕过限制。没有FileZilla传输。开发板helper仍使用既有固定主机密钥，不读凭据。VNC在workspace3，workspace4不操作。

## GUI及下一步

板端窗口最近刷新ID18874435，仅恢复时重新`windows`核实。第一终端标签曾运行只读观察器 **285039**，13:24:27开始，最多30×20秒；预计已自然结束，未再次实时确认。第二标签当前Bash空闲，所有输入完成。刷新截图后才能输入；不能对未确认的前台进程发送Ctrl-C。

工具 `F:/linux_fpga_try/ac820.ps1`，按computer-use/板端AGENTS规则只通过可见VNC操作服务器。截图存在 `E:/fpga_race-two/takeover_local/c80_*.png`。先看原队列和子账本，不能重复启动。

下一步等待当前综合，先读取最终同网表面积/宏/setup/hold；合格后队列自动跑240/精度。队列结束再准备该网表 `c80_finish.py` 的gate14→SAIF12→timing/DRC→PT12。随后C80自己的报告/未知活动及声明模型审核、持久归档、冻结。C80完成前不开发C32/G32。

输入原平台、FLOAT20、DATA100入口和P80冻结/归档身份见C80_LOCAL检查点及P80_FREEZE回执；严禁将旧PASS转移到新硬件。
