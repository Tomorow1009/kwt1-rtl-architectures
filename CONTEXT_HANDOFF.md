# 05:23检查点：修复网表门级14通过，活动3/12完成

本节覆盖下方旧运行观察。当前有效计划仍为 `workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`（SHA 1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39）。压缩恢复后先读AGENTS、计划、本文件及STATUS。

- 2026-11-17 05:23:05.973746观察：唯一父101802，`c32_finish_repair04`仍running/saif，已完成structure和gate；SAIF L01–L03已通过，L04子119023自05:20:04.728868运行。共享盘1048576 B、/tmp72304087040 B。原锁owner仍存活。报告等待器110729尚待整队列自然成功结束，不重新启动。
- 修复03网表4f6e416402f2a178ec0ae0494fab1cddc53d7cf9113ac19990e108580b47c1dc，综合summary78268481a2fc203ae27102239ac9cdfcf83fdac3fef40dd08c8e1e2e2ef878e5。DRC明确无违反；保守面积0.7224077334997787 mm²、setup +0.0000524521 ns、hold +0.0010598 ns、220宏、0非预期锁存器。
- 自己的新网表门级14已通过354816输出；summary8eaea9b1318f8f8031c3d4f160283140842896b68cb73bbfd93f719b81ed09a9已机器断言，14周期均与同RTL的ASIC证据一致。无SDF。活动12、PT12及最终新网表审核尚未完成，原坏网表48.9738mW不能继承。
- 新产物全部/tmp。旧八路全部数据、Desktop/T80_Delivery_20261113、冻结S0/P80/C80与备份保持不动。清理32/33/34都已结束，禁止重复；34后已归档旧B0 generated expected.npz剩536份81364074B，任何后续操作须重新逐文件证明。
- 05:08以后仅做只读空间排查：旧B0保留的6个大文件合计226706897B，包含最终网表/DDC与R4交叉核对依赖，继续保留。旧B0活动目录已无>1MB原始SAIF，仅有simv及已归档编译缓存；不能据此推断证据丢失或重做清理。旧N1各包runs/*/*/csrc中>1MB普通文件缓存候选数为0。没有启动新的归档或删除。
- 已完成新修复链归档合同及12项本地测试，尚未部署归档入口、没有C32持久归档。当前共享盘不足以保存完整C32归档，继续只读选择可无损归档的非保护对象；不改归档验收门槛、不删唯一证据。
- Git e826337已同步个人分支；当前只有历史S0_SYNTH05_FINISH_LAUNCH_20261115.py未跟踪，勿提交/执行。本检查点及新增观察随后同步。

下一步继续原队列剩余9层活动、严格时序和PT12，检查一次性报告等待器输出；完成新模型/未知活动审核和持久归档后才冻结C32-A。不得开始下一硬件阶段。VNC窗口18874435已重新确认，workspace3；不使用workspace4，无当前待输入GUI会话。

详细身份、失败路径及工具入口见下方05:08/04:55历史段及 `CONTEXT_HISTORY_20261117_C32_0508.md`。

---

# 05:08最新执行检查点：新网表门级14已通过，SAIF第1层正在执行

本节覆盖下方04:55的运行状态。有效计划、原始功能/精度身份、修复03映射和保护范围均不变。

- 2026-11-17 05:08:07.795199：唯一队列父101802，runs/c32_finish_repair04状态running/saif，已完成structure、gate。SAIF第1层子112646自05:05:28.203511运行；尚无完成层，不应标活动12或功耗通过。新网表门级14完整输出354816通过，全部14周期与原同RTL ASIC14机器比较一致，无SDF、门级内部total不可观测。
- 门级summary SHA8eaea9b1318f8f8031c3d4f160283140842896b68cb73bbfd93f719b81ed09a9已机器断言。新证据handoff/team/evidence/C32_GATE14_REPAIR03_20261117.json，原C32_GATE14_20261117.json属于旧网表，保持不动。
- 当前共享盘1048576B、/tmp72495587328B。原队列已持原锁，owner只初始写一次，后续ledger都在/tmp；不需为每层重抢共享锁。清理34已终态，不能重复。归档候选只剩已归档旧B0生成NPZ536份81364074B，后续若需要必须先核对全链journal与当前实际存在。
- 一次性报告等待器父110729于05:02:53.930401启动，ROOT/c32_finish04_export_wait.py；等待101802自然成功退出再调用ROOT/c32_repaired04_export_review.py。失败不重试；当前未启动报告/unknown查询，不推进新硬件阶段。payload SHA4005586b999e322779099eddf53d9de196fd1362dd992429748a2d1e45832441，waiter SHA6afee3001cde7f6e4ffe71ff01737173f014e6fd9c44a39bf4d3f78dcf65e777，exporter SHAa2aaef702e6c241f1bc12da41905c0e4434d5a8c803c6299958f5fd6b28bcebc。部署逐文件哈希核验完成，不重复部署/启动。
- 新报告预定控制ROOT/c32_repaired_export_review03，输出新包runs/c32_report_repair03/c32_report；连接查询已自带原锁空间等待，不能恢复旧export03。新的归档合同和copy-only入口已本地12测试/Py3.6检查通过，尚未部署归档、更未完成持久备份。
- 只读精简查看器已部署ROOT/c32_repair04_status.py，SHA6bf482079317c2363ecbd77e89ff976d56a28dc2e652aa6725d5c5c732388992。VNC执行`python3 -B /tmp/s4_21usr_c32_20261116_2010/c32_repair04_status.py`即可看queue、gate/SAIF数量及唯一子进程。不打印大state字典或重复WAIT日志。
- Git最新已推1aad475；后续0cead09和f2ee84e及本次检查点待同步。当前无未结束GUI输入会话，窗口18874435/workspace3，恢复重查windows。仅历史S0_SYNTH05_FINISH_LAUNCH_20261115.py未跟踪，勿提交/执行。

接下来继续同一队列的SAIF12、严格时序/DRC及PT12，再核对原报告等待器及新模型snapshot。完成审核和持久归档后才冻结C32-A，再按计划评估C32-B/G32。不能借用旧网表48.97mW功耗。桌面T80、旧8全部、S0/P80/C80及备份保持不动。压缩后重新读计划与本检查点。

---

# C32-A修复已通过约束，新网表门级正在执行（11月17日04:55交接）

## 有效要求

先重读AGENTS.md、handoff/team/README.md、SYNC.md、STATUS.json及本文件。有效计划workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md，SHA 1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。路线S0→P80→C80→C32-A→可选C32-B→G32；当前只完成C32-A验收，不提前进入后续硬件。

保留32位原ICB/原平台缓冲参数、150MHz/6.666666ns、SS/.99V/125°C、源读→共享写ACK→原总线真实读回→解码计算→最终输出ACK排空；X14/W12/acc32/b32/total33/SHIFT10。保守项目面积≤1mm²，<.50为努力目标。正式20条×12层，100条未自动授权。旧八路全部数据、桌面T80_Delivery_20261113、冻结S0/P80/C80运行及备份绝不修改。

## 当前唯一正式队列

ROOT=/tmp/s4_21usr_c32_20261116_2010
新包ROOT/light-light126-c32-repair-5828804，工具源码58288044bfbbe344fafc7550647bfc5c29eef0a7；仅工具/映射单元改动，生产RTL仍61246bb，竞争固件91135f6。manifest为321c38f06fe155e491bcb580703eb5fdc96755f4bf4876d7c5545c6ae3b0dd07（启动器/等待器逐项机器验证）。

**ROOT/c32_finish04_driver.py 父101802，04:44:20.534853启动；runs/c32_finish_repair04是当前唯一队列。** 04:49:08状态running/gate；04:52:57.187365已开始第6个子进程106307，日志runs/c32_finish_repair04_gate/c32_gate/layer_02.log。门级14、SAIF12、严格时序/DRC及PT12串行完成，原锁一直持有，所有新产物/tmp。不要重启、不要清锁、不要改冻结包。

该入口只对原锁创建时的ENOSPC等待5秒重试；保留原ProcessLedger、原stage函数及错误/子进程排空。既有锁仅等待；部分创建锁不删。3项本地测试通过。driver SHA 69d8a2cfa69b692953ce1dbddea77f491f85d288cd5a077ccaa5e4d0bc3ceeac。回执ROOT/c32_finish_repair04_launch.json，请求同前缀_request.json，日志同前缀.log。请求记录wrapper哈希和旧失败身份；不能伪称原队列续跑。

## 修复03已取得的真实结果

映射run：新包/runs/c32_repair03/c32_synth。

- summary SHA 78268481a2fc203ae27102239ac9cdfcf83fdac3fef40dd08c8e1e2e2ef878e5；后续入口按此值机器验证。
- mapped.v SHA **4f6e416402f2a178ec0ae0494fab1cddc53d7cf9113ac19990e108580b47c1dc**，04:54另作机器断言通过。注意此前手工转录f46e/7c95是错误，未用于运行/验收。
- constraints.rpt明确“This design has no violated constraints.”；精度8位报告，未放宽原约束。
- 保守项目面积0.7224077334997787mm²；setup +0.0000524521ns，hold +0.0010598ns；92小宏、128大宏，共220；非预期锁存器0。
- 从原始C32映射派生，只替换core下U16528/U16527/U16523的BUFV2RD→BUFV4RD及U24686/U24687/U24680的NOR3V2→NOR3V4。同库引脚及布尔函数、所有其他Verilog token和leaf一致，无compile、无拓扑变化。修复身份明确DDC复用，未伪称新三块综合。
- 原始seed来自ROOT/light-light126-c32-91135f6/runs/c32_initial03_synth/c32_synth，summary ee08629b7cc9181d6e6db4ae21205ae931c6b1fe28f5c4420afd83097e8cef87，网表3c116d5a026b7e832030cd0c5a8def5a633ade9eaefb4efd1080851acc4bbd2c。严格时序例外/活动模型仍要结合新队列最终审核，C32-A未冻结。

## 已完成的功能与历史结果（范围不能混用）

- S0/P80/C80已冻结。C80固定12平均70603.1667周期、2124.5505985task/s、保守.9611361367mm²、55.3675891mW、26.0608448µJ。
- C32未改RTL的本地10000随机＋32定向、14例、1/2拍、ABA/取消，以及ASIC14、恢复、CPU竞争、20×12真实任务均通过；6082560输出和total零差异，不重复。
- 同批浮点20最大逐层NRMSE .20198143836753799%，固定12最大 .1425636423408142%；官方600未验。
- 固定12平均72179.3333333周期、2078.1571825730357task/s；完整编码均值25790B，四段事务均值32014.5。240批量均值70929.4083另列，不能代替固定12。
- 原网表自己的gate14/SAIF12/PT12已完成，原功耗48.9738373173mW、23.5659904990µJ/task；因原网表326条max_transition违反，该组只能保留历史，**不能继承给修复网表**。
- 原初始包manifest d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7；initial03 state SHA37e1279f0c165b6fb50493c4d87edb2a994e159a90e22e48b92c41ef8ab500c0。原证据详见C32_EVIDENCE_INDEX_20261117.md和JSON。

## 已失败路径，禁止重复

1. 原DRC报告326条违反被旧解析器漏识别；已撤回早期DRC0文字，保留原始报告。修复后的解析器明确识别decorated net/PIN及rounded-zero VIOLATED，未知格式拒绝。28项相关测试通过。
2. repair01/c7c7f6c因缺省dont_touch空字符串导致UID-133，退出。repair02/b9f0127修复工具问题且调整4单元，但剩两个max_capacitance 0.00(VIOLATED: increase significant digits)，仍未合格；父78851和等待器82597均退出，无新gate/PPA。
3. repair03/5828804父96263于04:31:54.592615启动并完成，summary见上。等待器98732于04:37:20.882361启动，放行新finish_repair03父99561；该队列04:39:46.674070创建原锁时ENOSPC，completed=[]，零子进程。保持失败目录，不重启。当前finish_repair04是新的依赖核验恢复入口。
4. 旧export_review03因为原网表真实约束失败退出，不重启。原report01、unknown清单/连接保留，不当新网表审核。

## 空间与精确清理

用户确认无团队持续共享盘写入；未判断其他来源。最近共享盘仍反复1MiB、/tmp约68GiB。新产物均/tmp。原协作锁/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock不迁移不清。

完整B0归档仍在PROJECT/backups/systolic-b-20261112_2320/completed-evidence.tar.gz（PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109），SHA dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50。63653文件/7006124866B全量回读证明保留。

- 32：304份46085943B旧B0生成expected.npz副本移除，余896；state SHA9e611c92d59228486b163e9ce624867ebf4a93a5b0b47dae3666e70b9973b951已由33机器核验。
- 33：父97746，04:35:09.202417启动，04:36:51.249194结束；64份9718967B移除，余832。state SHA8f4d2d6fd2db747d1402b98d07fdabf84b01ec2816a7b1e602bbcd8691f5f441已由34机器核验。
- 34：父102523，04:46:06.733541启动，04:49已退出；296份44987070B移除，取得原锁即停止，余536份81364074B。终态query_started_remaining_captures_preserved。state屏幕SHA a4130c4109113e6b3295b9bcc1bdfdaa787c2802be632233938da4ca8c4da51e尚未独立断言。脚本SHA4daf30e6623f9d8c7a6b8484361b03f10fc7424de6fac7fbd36109e8f3785f1a。
- 以上均先核验完整归档、原始大小/哈希、以前journal、当前实际文件及无人使用。所有小型日志/回执/汇总、原始数据、最终网表、活动、备份及受保护版本保留。不得重跑32/33/34。31前检失败零删除；30移除654CSV余9；更早清理见历史，均不重复。

## 当前本地工作与下一步

本地E:/fpga_race-two/kwt1-c32-g32-20261115，个人分支codex/light-light126/t80-pipeline-c32-g32-20261115。已推b56b184；此后e45152f/f2eee46/2212242工具及本文待同步。仅历史S0_SYNTH05_FINISH_LAUNCH_20261115.py未跟踪，勿提交或执行。

新准备（尚未部署运行）handoff/team/evidence/C32_REPAIRED04_EXPORT_REVIEW_20261117.py，绑定repair03映射＋finish_repair04＋原initial03功能；不是旧export03。后续控制目录ROOT/c32_repaired_export_review03，输出新包runs/c32_report_repair03等。

新归档合同c32_repaired_archive_contract.py显式核对不同包之间的等价修复链，新gate/SAIF/PT不能借旧结果；旧同包合同仍拒绝混合。c32_archive_runtime仅新schema分支使用它，复制/完整回读/容量余量/原锁规则不变。12项相关测试、Py3.6语法通过；尚无C32持久归档，不能声称已备份。

接下来：
1. 仅跟进父101802和其ledger，不重复队列。门级case_progress.json、SAIF case_progress.json、queue state为读取入口，所有进程观察附时间。
2. 全门级14/活动12/PT12完成后，适配工具导出新报告、未知活动连接/别名/模型snapshot。共享盘若再次阻挡新的锁，不重启旧作业；使用独立入口和明确剩余范围。
3. 完成新映射严格时序、面积、模型及活动审核、持久归档、C32-A冻结；再继续可选C32-B/G32。不要把新网表数值空缺填零或复用旧功耗。
4. 压缩前记进度，恢复重读计划与本文，重要进展同步GitHub。无子代理/goal。VNC18874435 workspace3，恢复重查windows；不使用workspace4。当前GUI无待输会话。

较早完整状态保留CONTEXT_HISTORY_20261117_C32_0455.md及0430/0411/0339历史。
