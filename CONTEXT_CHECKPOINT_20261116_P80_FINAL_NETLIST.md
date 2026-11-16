# P80最终网表验收继续入口

更新：2026-11-16 08:57（北京时间）。恢复时先读AGENTS.md、当前计划、本文件及根交接；下列远端状态仅对应观察时间。

## 有效目标与不可动对象

- 用户计划原件：`E:/UserData/LENOVO/Downloads/T80_搬运编码优化_32PE_时钟门控实施计划_20261115.md`。仓库副本`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。
- S0→P80→C80→C32-A/可选B→G32；最终16×2/32PE、150MHz、SS/.99V/125°C、6.666666ns，项目保守面积≤1.00mm²。每阶段自己的20条/240任务、门级14、活动12/功耗12及交接完成后进入下一阶段。
- 原32位ICB、原平台参数；源读→成功共享写ACK→原总线真实读回→解码→输出写ACK/排空。不能旁路、不跨任务预装载。X14/W12/acc32/total33/SHIFT10不变。
- **服务器Desktop/T80_Delivery_20261113和所有旧八路数据禁止修改、移动、删除。**本轮均未动。
- C80/C32/G32均未开始；原T64/G64旧队列不恢复。不使用旧网表PASS验收P80。

## 本地身份与操作入口

- 工作树`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。
- 最新已push **c8f6a24**；08:57新增精度/进度记录待随后提交。硬件142fae2，当前服务器操作包1023646；文档提交不改变受测硬件。
- Git使用`-c safe.directory=E:/fpga_race-two/kwt1-c32-g32-20261115`；Python用`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`。
- 未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不是本轮内容，不加、不运行。
- 已读computer-use技能及`F:/linux_fpga_try/AGENTS.md`。用`F:/linux_fpga_try/ac820.ps1`控制开发板上的可见VNC，不能绕到比赛服务器隐藏通道。
- VNC18874435、workspace3。**当前第一终端标签Bash空闲**；第二标签只读watcher135257应已在阶段离开synthesis时自然退出，需新截图核对。所有键盘会话已结束，最近68209。不能根据旧位置盲目输入。workspace4不动，FileZilla未使用。

## 当前唯一原队列：不要重启

服务器私有根`/tmp/s4_21usr_p80_20261116_0315`（下简称root）。

- 父**95253**，`root/p80_final_combined05_controller.py`，SHA `46e2a8fb416db99febbc9c2bb6ea09b619b515bb185711c2a3a9782277d11651`。
- 队列`root/light-light126-p80-1023646/runs/p80_finish05/state.json`；根控制`root/p80_final_combined05.json`不包含实时stage，查询应读队列state。
- 原共享锁`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`，不清锁、不另启EDA。
- **08:56:45：running/gate，error=None，已完成extremes、rounding；layer_01的simv子143466运行8秒/CPU99.5%。**编译已成功，VCS编译35.891秒、elab7.095秒。不要重复编译或重跑已完成用例。
- 原队列先precision，再structure/gate14/SAIF12/timing_audit/drc_audit/PTL01～12，总18阶段。终态`reports_ready_review_required`后自然释放锁。
- 原export05父**96154**，`root/p80_export_review05_controller.py`，SHA `952242ef4a1ea2b9ee5bcde89ec0cd4b4c48f2bd504a55ae8a3f1031a31fee4b`；等待原队列，自然导出/未知活动清单/锁内一次连接查询/模型事实。不能重复启动。
- 导出目标：1023646包`runs/p80_report05/p80_report`、`runs/p80_unknown_inventory05`、`runs/p80_unknown_connections05/p80_unknown_p80`；最终事实`root/p80_export_review05/model_review_snapshot.json`。事实文件不自动授予阶段PASS，仍需独立结论。

## 已完成证据，不重跑

### S0

声明条件完整验收并持久归档/冻结，标签`arch03-s0-partitioned-20261116-0215`已push。平均112569周期、1332.5160568task/s；项目保守面积0.9535222591mm²；50.240373mW、37.703387µJ/task（布局前模型范围）。详见S0报告与FREEZE，不重跑S0。

### P80真实CPU与本地

- 硬件`142fae28545759e33fa38de514eabf752cb8c43a`。本地10000随机+32定向块、22矩阵、协议、取消、1/2拍SRAM已通过。
- 元信息深度2/4/8各自真实ASIC/E20314通过，354816输出/版；固定12周期一致，选最小深度2。
- 固定12：平均**77545.33333333333周期、1934.35237882357task/s**。相对S0吞吐+45.1654%；不是芯片实测。源码摘要`142fae2/runs/p80_fixed_d2_05/p80_soc` SHA `43e9ec58048d24ab8ab7d505723f7360b1e7e1e6eeaf5d76c81134cef34222c8`。
- 自己的深度2恢复十阶段、CPU竞争、前20条240任务全部通过，6082560输出及total零差异。`e139032/runs/p80_d2_batch20_02/p80_batch20` SHA `36953e487c757a9980c4ac33760b7a8f65c6f61209e6b2582a8342b582d7e687`。批量均值77545.1583333与固定12不可混用。
- 固定12平均编码29756B，平均34989个事务，符合3B/4+12672；详细搬运及调度读数已保存两个P80_FIXED12_*OBSERVATION JSON。供数空拍50301～62765，首供数等待2811～3707，最后写回尾部141；这些来自原摘要，没有新仿真，重叠等待不相加。

### P80最终综合

- 操作包`102364644dd181b23358dc2c7fe0d6e8279ae0d2`，manifest SHA `402c08165610ed18bdd772cddd3d527570fd62bdaa6ff820e0ad19b5d7082bcd`，947源文件。
- 运行`1023646/runs/p80_synth_d2_06/p80_synth`，摘要SHA **`75460463afddef3043613822bd58b8ee66e4869a826d49bf0899052d6e664c1e`**；网表SHA **`583e2e8f5ed6e61b357ddf477bab0e3e826e9f39f6ba490f16da275d40d0192c`**。
- 项目保守上界**0.9529288663004588mm²**，已知新增0.7924098895005534；整机4475145.365862um²。setup **+0.000055331ns**、hold **+0.00113887ns**，6.666666ns，92小宏+128大宏=220，锁存器0。
- 共享、加速器、CPU映射分别35.6743365、4470.2956079、748.8967320秒，最终链接133.8648641秒。原98857/132629/138231均已自然结束，没有重启或用失败映射替代。
- `P80_SYNTHESIS_NUMBERS_20261116.json`是初步数字；后续详细STA/DRC、门级、活动/功耗未齐，不提前冻结P80或称物理签核。
- 结构阶段已生成清单：11336项declaration_only，no_load匹配True；数值实例80PE/80转换/1阵列。实际剩余告警LINT32=10741、LINT33=1187、LINT1=4；四个LINT1为debug的ndreset/fullreset、AON porrst和PLIC优先级寄存器。无面积/内部功耗豁免，完整审核仍需后继证据。

### P80新浮点精度连接

- `1023646/runs/p80_finish05_precision/p80_precision`已通过，摘要SHA **`d7fca6e57d2e879b42c89c4e4ab09e7d82aeda1ed8a293267e2a1bf840303f31`**。
- 同批20条240任务，6082560输出重新连接自身ASIC结果，最大逐层汇总NRMSE **0.20198143836753799%**，最大单任务 **0.20953408931848963%**，X/W/b裁剪均0、饱和0。详见P80_FIRST20_PRECISION_OBSERVATION。
- 实际FLOAT包`/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip`，SHA `5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2`。原始成员来源已核对，旧原ZIP容器edb…未获得，不混写。
- 固定12精度会由同队列最终导出再次计算/核对，官方600未验；不能把20条精度称官方结果。

## 空间、备份与准备工具

- 08:34共享盘仍只有1,048,576B；较早tmp可用约89GB，写新大包前刷新空间。
- 早先cache09/10/11已核验归档后清掉普通编译缓存，不能重跑。本次上下文**未删除任何服务器文件**。
- B0完整原备份`SERVER/IC/light-light126-undergrad-d2-20261109/backups/systolic-b-20261112_2320`只读保留：archive SHA `dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50`，1261445859B，63653成员/7006124866B已于08:23全量回读通过。
- 原只读预检12已结束，结果`root/b0_archived_batch_preflight12/verified_candidates.json` SHA `fbb98604283fcac8285dc817f554dd7bcccee37f85faba07d9fefe72906e9bd8`。仅B0完成批次cases里的49200个生成.hex/.verilog/.bin，共2616732144B，与备份一致；没有清理、未证明无占用，预检不重跑。
- 本地`P80_B0_ARCHIVED_BATCH_CLEANUP13_20261116.py`（156e828含保护测试）**未部署/未执行**。要求原P80队列和export05自然完成退出、获取原共享锁、备份和源SHA重新核对、严格无占用、逐文件日志及目录fsync；15个保护路径拒绝/6个状态拒绝场景通过。不可向仍运行队列并发清理；看不全自己的进程则失败，不据此豁免。
- P80最终持久复制归档尚未执行；使用已有`p80_archive_runtime.py`，要求1.2倍实测压缩大小+2GiB空间。不把临时根当最终交付，不自动覆盖原备份。

## 已失败路径与下一步

- 综合01旧驱动库限定符错误；综合02建锁ENOSPC；combined02 Path类型错误；combined03 ENOSPC；combined04重复旧set_local_link_library路径导致UID-15/993。全部保留，不重启。
- 1023646只在核对旧/新同字节DB后修正库引用，没有更改库/角/时钟/负载或RTL；当前真实四段综合已验证修复。
- 下一步继续原gate14→SAIF12→详细STA/DRC→PT12及export05；及时读取终态和失败，禁止重复派发。必须等本轮完整报告、独立结论和持久归档冻结后再实施C80。
- 当所有原队列结束后，按实际空间和严格占用检查决定是否执行已授权范围内的B0重复生成输入清理，保留完整备份与输出；旧八路/T80桌面始终排除。
- 压缩前更新根交接与本文件，记录前台标签、所有未结束输入/作业身份；压缩后先读计划与最新检查点，不能根据历史PID盲目恢复。
