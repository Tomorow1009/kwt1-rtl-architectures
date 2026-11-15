# P80首个真实CPU任务通过；共享空间与串行队列恢复

## 04:40输入状态与防重跑修正

- 唯一输入exec13095，local_runs/p80_b0_cache06_transfer_20261116/transfer.ps1，共14行，当前只在输入，未观察归档或队列PASS。
- cache03/04均在不存在的手工转录路径检查处退出，未归档、未删任何文件；cache05输入因本地CRLF与服务器LF校验不匹配，在创建文件前停止。保留原失败，不能重跑。
- 本次从服务器机器清单b0_cache_candidates01.json直接取得精确路径，清单SHA c5d5e6b4069637e5d720eebaa09ba684e53604a8e6da2a0ebf176a68f5a68cd5。核验目录必须属于本人bundles下systolic-b-v3/已passed的指定SAIF阶段，绝不触及旧八路/T80桌面。
- 正确LF归档脚本P80_B0_CACHE_SPACE_RECOVERY05_20261116.py SHA7d96eff11f42c49df00d41ab9effc0ad520a55b9d2d8fb79dea4f04091c84a4d，部署为cache_space_recovery06.py。成功后启动仍未执行过的p80_sweep05_controller.py。只有实际新PID及锁证据才算恢复。
- 最新本地9622b09，远端已push0573754；854 EDA包未传。首层80471周期结果不变。上述失败只涉及工具入口，没有RTL改动或新增硬件PASS。


## 04:35更新：03身份失败与04建锁失败；正在传入05

以下覆盖04:18状态。当前唯一VNC输入exec95957，入口local_runs/p80_b0_cache_sweep05_transfer_20261116/transfer.ps1共19行。先收完输入和归档终态，不并发键入、不重跑。

- N1 sequence缓存02已完成：35普通文件/7,193,225B，归档SHA aebb47bf12cc63bde45408a3671c16078733f027e10814b4a94e99cb22045269；原stage持久tar和P80根receipt保留。
- sweep03父314814因手工manifest转录多写一字符在身份检查失败，未取锁/未启EDA；旧脚本与失败保留。正确64字符manifest为7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc；服务器原包始终正确。
- sweep04父317100在04:23:25再次原共享锁mkdir ENOSPC，未启EDA。其JSON仍starting/current=None/completed=[]仅因acquire异常未记入，launcher.log证明已失败，不当作live。
- 04:30:23只读清单确认B0包light-light126-systolic-b-v3-20261112_113543-cede0e139a01e的runs/systolic_b_power_final01_activity12/systolic_b_saif已passed；其csrc40普通文件/80,788,435B为本次归档03唯一目标。不是旧八路，也不是桌面T80。尚未观察归档03完成。
- 新控制器05修正建锁异常记录，一把原共享锁连续持有，串行跑深度4/2/8各14；SHA6473175d150bd33df198650b476829601458dba93062ff6e8202e2f0421f971e。归档03脚本SHA04ba69992d366f0ed2c7ec5e925c5d67b587b76fcc19bd4496de264c6298d6e7。来源d75cb76，尚未push。
- 成功归档完整tar成员核验、持久副本与原结果核对后立即启动新sweep05；不重跑03/04。状态根p80_sweep05.json，coordinator在142包/runs/p80_sweep05_coordinator，三个阶段p80_fixed_d4_05/d2_05/d8_05。
- 首层真实CPU PASS维持80471周期/25344输出；三深度14、恢复/竞争/240、PPA仍待，854 ops89行尚未部署。T80桌面/旧八路不动。


记录时间：2026-11-16 04:18（北京时间）。恢复先读AGENTS、根交接、本文件和`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`。

## 固定要求与已完成阶段

- 服务器桌面`T80_Delivery_20261113`及全部旧八路文件不写、不移、不删。
- S0已验收、冻结、持久归档；不重跑。路线仍S0→P80→C80→C32-A/可选B→G32；当前仅P80。最终32PE/≤1.00mm²/150MHz；原32位ICB和原总线缓冲参数保持，成功共享写ACK后必须原总线实际读回。
- 数值X14/W12/acc32/total33/SHIFT10不变；正式只前20条、240任务、6,082,560输出。固定12性能任务独立报告。
- P80本地10,000随机＋32定向块、22完整矩阵、协议/恢复fixture、2拍SRAM等已通过，详情见上一P80_SERVER_PREP检查点和P80_LOCAL_PROTOCOL证据。

## 本轮实际服务器结果

运行根`/tmp/s4_21usr_p80_20261116_0315`，功能包`light-light126-p80-142fae2`。

- 源提交142fae28545759e33fa38de514eabf752cb8c43a。
- 03:58:36完整准备通过：917文件、原S0源保持，manifest SHA **7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc**。
- sweep01父303160在pilot_d4_01建立原共享锁时ENOSPC；没有VCS/EDA，completed=[]，失败保留。
- sweep02父306726：**p80_pilot_d4_02/p80_soc首层passed，真实ASIC/E203，25,344输出和total33/result/sat一致**。完整80471周期，编码31428B，host约4.6802235秒，MAC更新1622016，队列深度4/峰值3。是单层初步结果，不是12层平均或PPA验收。
- sweep02随后在`p80_fixed_d4_02`重建原共享锁时再次ENOSPC，没有启动该14例的VCS；队列failed、completed只有首层。旧编号不重跑。
- 04:01:54共享盘free1,048,576B、剩1089 inode；tmp free92,038,000,640B。其他使用者会继续耗尽刚释放的空间，不能把上次free当实时。

## 已执行的唯一缓存归档（不触及保护数据）

已通过的N1 ASIC14普通编译缓存：
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-n1-v4-20261113_013211-9305c6948c76/runs/n1_asic14_01/n1_soc/csrc`。

- 35文件、10,643,394B；完整tar成员解压后的size/SHA匹配，再删重复普通缓存。
- archive SHA **2aa12ed47a2c7abbe76da8e382aece92d298cd27ab6ebeb93c0febd24ef538c4**。
- 持久副本在该`n1_soc/csrc_regular_files_20261116_p80.tar.gz`，已经回读核验。临时副本及完整receipt在P80运行根`n1_asic14_csrc_20261116.tar.gz`及`.receipt.json`。
- 原state、summary、全部build输入、simv、结果及日志前后不变；目录和符号链接保留。完成时free9437184B，之后空间又被占用。不能重复归档。
- 先前N1 contention、R4 cache归档也已执行，不能再次清理。旧八路与桌面T80从未操作。

## 当前真实输入／前台工作（04:18）

- 所有本地输入exec **15378、98620、24643、9206、49363、4257、67796均已结束**，没有半截here-document。
- 当前VNC18874435、workspace3，**前台正在执行cache_space_recovery02.py**，04:17:35最后截图尚无终态/新PID。必须先截图确认是否回到Bash，再输入命令；不Ctrl+C中断归档，不重跑。
- 刚传入23行`local_runs/p80_single_lock_transfer_20261116/transfer.ps1`，来源提交**ca564d6**：
  - `handoff/team/evidence/P80_DEPTH_SWEEP_SINGLE_LOCK_20261116.py` SHA **4753d12072bd6bbac4a18dd8cc4fe52cb61fcfa4182701b90c2e279152d63b7c**；服务器`p80_sweep03_controller.py`。
  - `handoff/team/evidence/P80_SEQUENCE_CACHE_SPACE_RECOVERY_20261116.py` SHA **a966f21f1ed2600807f71100f1cbae9a0a92a415ef9409362ea5471de1fd2b66**；服务器`cache_space_recovery02.py`。
- 此次仅针对同一N1包已passed的`runs/n1_sequence_01/n1_sequence/csrc`：只读清单35普通文件、7,193,225B。核验完整frozen_inputs/原结果、无打开句柄/EDA，再无损归档、逐项回读、删除重复缓存并持久复制。**尚未观察完成，不能先写成PASS**。
- 成功后启动新`sweep03`：深度4/2/8各14例，共享原`.arch02_team_lock`由一个ProcessLedger持续持有，使用既有`register_stage_session`能力；不改变锁路径、不清别人的锁、不并发EDA，不修改原功能包输入。
- 新队列控制`root/p80_sweep03.json`，日志`root/p80_sweep03.launcher.log`；账本`142包/runs/p80_sweep03_coordinator/process_ledger`；实际阶段`p80_fixed_d4_03`、`p80_fixed_d2_03`、`p80_fixed_d8_03`。失败停止派发；`root/p80_sweep03.stop`在阶段间协作停止。

## 本地工具与未部署输入

- 8543440已push：P80独立fresh link/三块综合/门级/SAIF/PT/精度工具，本地12项检查通过；不代表服务器PPA。321a217已push：P80报告工具、两个报告检查通过。
- **ops包854仍未传**：`local_runs/p80_ops_transfer_8543440_20261116/transfer.ps1`89行，next_line=0；输入24文件delta/46876B，patch SHA **8b7072327b865bffeac5fb57f92e0805073d2acea9edee2aa78f5b04904cfa77**；完整payload SHA **5915a15ab41d6601684684ecce16272316fa303e645f8732740dc04c3ffd0e89**。仅克隆新`light-light126-p80-8543440`，不覆盖142包。报告工具是后加，不在854包中。
- 旧6ca delta包、旧315aff sweep启动器均过时，不部署。原`p80_sweep_launch14_20261116`已执行过，不重跑。
- `S0_SYNTH05_FINISH_LAUNCH_20261115.py`过时未跟踪，不能提交或执行。
- 新N1缓存归档脚本分别ed4e590及ca564d6；截至04:09已push到c446c55，ca564d6尚需本轮后续同步。

## 后续顺序与缺口

1. 先读归档02终态和sweep03实际PID/state/锁，禁止猜测已启动。若失败，保留脚本/回执，不重试同目录。
2. 在原串行队列上取得三深度14例和固定12性能。选最小且距最佳吞吐≤1%、面积合格的队列；不能仅看首层峰值3就直接宣告选定4。
3. 部署新的独立P80 EDA工具包。综合只引用S0的端口边界预算，不复用旧linked/mapped硬件DDC；新P80必须自己重新综合、面积/时序/结构、gate14、SAIF12/PT12及精度报告。
4. 深度2/8若胜出，恢复/竞争固件也必须按该深度重新构建；当前只有这两套深度4固件。正式批量用自己的前20条240任务，不能借T80或S0 PASS。
5. 初步报告工具不自动授予时序/功耗验收；完整模型/活动/未知状态说明仍须完成。通过P80阶段后才进入C80。
6. 持久归档前再核空间，当前所有新/tmp产物不是最终备份；不得删桌面T80/旧八路来腾空间。

恢复VNC用已核验的板端入口`F:/linux_fpga_try/ac820.ps1`；重读技能/板端AGENTS后fresh windows/screenshot，再选择输入。FileZilla仍未连接，DNS保护未修改；不另开隐藏服务器传输通道。
