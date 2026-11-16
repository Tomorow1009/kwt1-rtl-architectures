# C32修复03恢复入口（2026-11-17 04:30观察）

先重读AGENTS.md、有效计划workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md和STATUS。本次只修C32-A，不进入C32-B/G32。原计划正式批量20条；保护桌面T80、旧8全部资料、冻结S0/P80/C80和备份。

## 已完成与实际缺口

- S0/P80/C80已冻结。C32原RTL240任务6082560个输出及total零差异、ASIC14/恢复/竞争/精度已通过，当前RTL未改。原网表门级14、SAIF12/PT12已跑，但原网表有326条max_transition违反，不能作为合格阶段。
- repair01因DC缺省dont_touch返回空字符串、恢复时UID-133失败，已保留且退出。repair02修复此工具问题，并调整3个BUF与一个上游NOR3；等价token/leaf证明通过、DC无工具错误，映射已完成。
- repair02仍有两个真实max_capacitance违反：core/n60014与n60011，报告显示0.03/0.03/0.00 (VIOLATED: increase significant digits)。旧解析器未提取这两条但明确标extraction=false，准入正确拒绝，不能说DRC0通过。
- repair02 summary SHA 057e0dd63d44b38c722ad192d123f8799a6c2d7582e15dac0422d315e27fe02f；保守项目面积0.7224058182997788mm²，setup+0.0000524521ns、hold+0.0010598ns，92小宏/128大宏、0锁存器。网表功耗尚不能沿用原值。
- 04:17静态驱动读取：n60014→U24687 NOR3V2，n60011→U24680 NOR3V2。新repair03从原ee08629b/3c116d5网表重新派生，只改三个BUF V2RD→V4RD与三个NOR3 V2→V4，所有其他Verilog token/leaf必须相同。无compile、无拓扑/约束放宽，报告提高到8位有效数字。
- 新解析器保留rounded-zero VIOLATED为真实违规，无法识别/截断记录继续拒绝。28项相关本地测试于本轮重新通过；工具源码58288044bfbbe344fafc7550647bfc5c29eef0a7。

## 服务器身份与恢复

ROOT=/tmp/s4_21usr_c32_20261116_2010。repair02包ROOT/light-light126-c32-repair-b9f0127，父78851、finish等待器82597与恢复32父85635在04:30:12均已退出，原协作锁不存在。finish等待器因真实约束失败退出，没有新gate/SAIF/PT启动；不重启02。

repair03两文件差量已经生成并正在GUI传输：local_runs/c32_repair_overlay_delta03/gui.txt，4614字符；payload SHA 652403c2598be68a764f48844cf958c28cf6917c50abc12764e448bbfd0b58ce。原1082文件逐一校验、新目录light-light126-c32-repair-5828804；原始seed仍为91135f6包自己的初始综合，不串接02网表。当前GUI unified session61492，恢复必须先确认完成再输入。新启动回执将为ROOT/c32_repair03_launch.json，未观察到之前不得标已启动。

## 空间与已尝试清理

用户确认无团队持续写共享盘。04:30共享1048576B、/tmp73445593088B，全部新运行仍在/tmp；不清锁、不换锁。

恢复32终态query_started_remaining_captures_preserved，304份46085943B旧B0生成expected.npz重复副本被移除，剩896份136070111B；04:11:11.290856结束，当时释放35651584B，随后空间回到1MiB。完整已核验归档、原始数据、汇总/日志和所有保护版本保留。不得重复32。恢复31存在性前检失败零删除；恢复30移除654CSV留9；更早26至29终态见历史。

若仍需要锁空间，只能新建精确剩余文件清理，先核对旧state/journal和当前文件，再核对完整归档与无人使用；不能把归档目录清单当作当前文件存在证据。

## 下一步

1. 查看repair03实际启动、进程、原锁及最终报告，不重启既有任务。
2. DRC、setup/hold、≤1mm²、结构和等价证明全部通过后，新repair03自己的gate14/SAIF12/PT12；保留原未变RTL240证据，不继承旧网表活动/功耗。
3. 适配新报告导出，连接原RTL证据与修复映射身份，完成审核、持久归档和C32-A冻结，再继续计划。
4. 每次压缩前更新本文与STATUS，Git同步同个人分支。不启子代理/goal，不使用workspace4。

---

# 04:11执行状态更新：repair02与原依赖等待器仍在，不能重启

本节覆盖下方旧repair01与恢复30的运行状态。有效计划、保护范围及旧功能证据不变。

- 最新服务器观察2026-11-17 04:10:59.170434：repair02父78851、依赖等待器82597、恢复32 worker85635均存活；repair02尚无stage目录，仍WAIT_ORIGINAL_LOCK_STORAGE。当前无DC或新门级/PPA子进程被观察到。
- 新包ROOT/light-light126-c32-repair-b9f0127，源码b9f012707be7c557ac717138dc4060d23fd603b4；03:53:23.740263启动。manifest屏幕值aa329cd1a7137f857068cde6ee100946f9aa55953ecc1cf1c03cc4615e559b2e；来源和逐文件身份由准备器及等待器机器验证，字符串尚未另作人工转录断言。差量payload SHA90d6ef80ca4b3d5e74bd02c83b3d7bec0bfc8693a997260e64194b1126419e5c，仅2个工具文件，4422字符，逐字节往返及Py3.6通过。
- repair01已失败并退出，DC实际执行52秒、日志7条UID-133错误：缺省dont_touch返回空字符串而非Tcl异常。新代码处理空值并恢复属性缺省，增加真实Tcl回归；相关27项测试通过。
- repair01候选还暴露一个上游n60013、34条max_transition记录；静态驱动NOR3V2_12TR40 U24686。新repair02从原始ee08629b网表重新派生，只改3个BUFV2RD→BUFV4RD及U24686 NOR3V2→NOR3V4；同库引脚/函数等价、token/leaf证明，无compile、无拓扑/约束更改。旧尝试不能当合格结果。
- repair02先前脚本固定路径runs/c32_repair02/c32_synth。ROOT/c32_repair02_launch.json、request和launch.log为状态入口。不要运行repair01或修改任何既有包。

## 单次后续验证接续

ROOT/c32_finish_repair02_wait.py父82597于04:01:54.153666启动。它等78851自然退出，然后必须通过完整修复身份、DRC、setup/hold、≤1mm²、0锁存器、原锁空闲及所有子进程退出检查才调用ROOT/c32_finish_repair02_tool.py。任何失败保留并退出，不重试。目标队列为新包runs/c32_finish_repair02；当前尚未启动。

等待器SHA e88671019a689f3f7ff6cc5b49b92a4cd886350cc56dde0bc09cfd73c06c34bb；启动工具SHA93c9f4aa26ce21ea485e3249ea0cdbc6f88b368ab22ca7eede5ae0109059372d；payload51088235b927c67464f77c9a330653c9e86a5357fc34ee4bade43f978a53d6b6。部署哈希机器验证。不要重复启动等待器或手工并行启动finish。

新门级/PPA完成后的报告工具已提交：handoff/team/evidence/C32_REPAIRED_EXPORT_REVIEW_20261117.py（尚未部署/运行）。它明确连接“原未变RTL功能/精度＋新等价映射＋新门级/活动/功耗”，不使用旧export03同包假设，不继承旧网表结果。

## 空间恢复终态与当前唯一清理

- 恢复30已终止：654份210149660B已归档CSV重复副本被移除，余9份2898594B保留；取得原锁即停止，状态query_started_remaining_captures_preserved。原清理工具不要重复。回执哈希还未独立机器转录核验。
- 恢复31 worker81140于03:58:42.064777启动后在首次文件存在性检查失败；任务固件镜像已经由更早清理移除，未创建b0_archived_firmware31目录，因此零删除。保留日志/脚本，不重复31。
- 04:04:55对磁盘实际存在文件只读复核：该旧B0批量仅expected.npz1200份182156054B仍较大，另有9份CSV及小型回执/汇总/日志。04:06:48确认精确路径cases/sample_000001_layer_01/task_data/expected.npz等。
- 恢复32仅处理上述1200份已核验完整归档内的生成参考NPZ副本，canonical模型/数据、所有汇总日志、完整归档和受保护版本保留。worker85635于04:08:47.613846启动，04:10:59仍在验证，无终态/错误。工具SHA ef70a9db4d61f9e286dd5bd994556d12639a141eadf10fe6d33ce65dd13e5519；ROOT/c32_recovery32.log，终态ROOT/b0_archived_expected32/state.json。原修复取得锁即停止；不能重复32。
- 用户已确认无我方持续共享盘写入。共享盘仍反复接近1MiB；所有新验证产物在/tmp，原协作锁不改、不清。不要依据旧归档清单猜测文件仍在，应先只读检查实际存在。

## 接下来

先看78851/82597/85635和原锁。若repair02完成，读取真实报告并跟进原等待器；不另开重复队列。如果仍有约束/工具/等价证明问题，保留失败，在新目录修复。C32-A仍未冻结，不启动C32-B/G32。正式仅20条，100条未授权。T80桌面、旧8全部数据、冻结S0/P80/C80及备份不改动。

最新本地459dd79；已推b9f0127，后续操作工具/检查点待同步。当前GUI空闲，窗口18874435、workspace3第一终端；恢复重查windows。不使用workspace4。不启子代理/goal。下方为较早完整证据索引，旧活动状态以上述为准。

---

# C32-A修复恢复入口（03:44实际观察）

先读AGENTS.md、有效计划、本文和STATUS。有效计划为workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md，SHA 1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。路线S0→P80→C80→C32-A→可选C32-B→G32，当前只修复C32-A。

## 当前唯一服务器任务

- ROOT=/tmp/s4_21usr_c32_20261116_2010。
- 新工具包ROOT/light-light126-c32-repair-c7c7f6c，代码c7c7f6c3505ca54b90d1fa54893b925866d3c3ee；仅工具改动，RTL仍61246bb，竞争固件仍91135f6。
- manifest屏幕显示45448653c5cc0c1edc74598b1e9ec81a5567961e89850fc023c6d3d506e5f809，准备器按已提交工具字节、旧manifest及逐文件SHA机器验证后生成；此字符串人工转录尚需独立断言。
- GUI差量包SHA07dbf1b62ad6c16128909ed2b6c8be035edd15939033594b2eaeafc8424caa54；7工具文件，19097字符；本地逐字节往返及Python3.6语法检查通过。
- 修复父72614于03:39:20.358366启动；03:44:16.140201仍在WAIT_ORIGINAL_LOCK_STORAGE，尚无DC子进程，runs/c32_repair01尚不存在。不要重复启动。启动回执ROOT/c32_repair01_launch.json、request同前缀、日志ROOT/c32_repair01_launch.log。
- 恢复30 worker74341于03:43:12.405144启动，03:44未终态，日志无错误。只处理恢复29留下的663份已核验归档B0 task.csv副本（213048254B），获得原锁即停止。原始归档、日志、汇总、源码、活动、最终网表全保留；不要重复30或29。工具SHA b25320301ff5d4fb62bbf89419374b5afac23b6f4ef32f2602d94f3cbf72d2b8，源码handoff/team/evidence/C32_B0_ARCHIVED_CAPTURES_RECOVERY30_20261117.py。
- 最近空间03:27：共享1048576B，/tmp74567278592B；用户确认没有团队持续共享盘写入。当前状态不能用这个旧观察代替，恢复先查进程、原锁和space。
- 当前无GUI输入会话。VNC18874435/workspace3第一终端，实际操作前重查windows；不使用workspace4。

## 必须修复的真实问题

旧最终网表有326条max_transition违反记录，完整解析为三个网：core/n9882→U16528，n9916→U16527，n9950→U16523，均BUFV2RD_12TR40；上游分别n60014/n60013/n60011。要求1.35ns，实际约1.36–1.37ns。旧摘要“DRC0”是人工转录错误，已撤回，服务器原报告未修改。不能用正setup/hold代替DRC通过。

修复脚本仅尝试三个BUFV2RD→BUFV4RD：同库引脚/布尔功能等价，临时解除并恢复精确祖先保护，无compile、无拓扑/约束变更；全网表token与leaf证明只允许三个引用及对应面积变化。修复路线显式复用自身映射及原三块证明，绝不伪称新完成三块综合。26项相关测试通过（原25项＋修复身份拒绝测试）。源已提交推送c7c7f6c，后续2d1faef/d50ecfc/1e9ffe0待同步。

独立驱动检查inspect02已完成：57941/DC63231退出，summary SHA5fb1e75174bc4fa325963d1a2f394ac0767cc67a5af8c62664a78d3c36531781已机器核对。原export_review03因Unresolved C32 constraints失败退出，不重启；unknowninventory/connection/aliases旧网表查询完成，snapshot未生成。

## 已完成证据与边界

旧完整包ROOT/light-light126-c32-91135f6，manifest d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7。

- C32本地10000随机＋32定向、14例、1/2拍、ABA及取消恢复通过。
- ASIC14/恢复/CPU竞争通过；前20×12=240任务，6082560个输出和total逐项零差异。RTL未变，不重复这些。
- 同批浮点20最大逐层NRMSE0.20198143836753799%，固定12最大0.1425636423408142%；官方600未验。
- 固定12平均72179.3333333周期、2078.1571825730357 task/s（按150MHz折算）。
- 旧未合格网表保守项目0.722402954997787mm²、整机4.244619443828mm²；setup+0.0000524521ns/hold+0.0010598ns、220宏/0锁存器。
- 旧网表自己的门级14、SAIF12/PT12完成：时间加权48.9738373173mW、23.5659904990µJ/task，布局前估算。不得转移给修复网表或标为阶段验收。
- 旧报告runs/c32_report01/c32_report SHA4f4be422643e0123ec40ff106d3750237e1e1ed79d7c9869b22a590c7a6dc7d7；网表3c116d5a026b7e832030cd0c5a8def5a633ade9eaefb4efd1080851acc4bbd2c；synth summary ee08629b7cc9181d6e6db4ae21205ae931c6b1fe28f5c4420afd83097e8cef87。
- 初始各任务及精度哈希见C32_EVIDENCE_INDEX_20261117.md和对应JSON；最新状态以本文为准，旧索引中的“export运行中”已过时。

## 空间恢复历史

恢复26/27/28完成，不重复。26/27回执已机器断言；28 SHA dd6940df48aa7e24cd7e2c6d8d68d7cb4eecbb8ff66f0930dea08e366644ea45已机器断言。

恢复29在查询取得锁时停止：537份172434752B移除，剩663份。正确state SHA为a1170088c32ca7f91ac01916c351e96215dcdc1510b8f97ebd7fb7ebe35b8663（十进制分组重新读取；此前dccd/dcc转录错误不得沿用）。恢复30启动前机器核验此SHA和journal，不重跑29。归档为原B0 backups/systolic-b-20261112_2320/completed-evidence.tar.gz，SHA dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50；63653文件7006124866B完整回读证据保留。更早19/20/22/23/24/25均终态，见历史检查点。

## 下一步

1. 跟进原72614和74341，不重复启动，不清锁。核对新repair01终态、工具错误和token/leaf证明。
2. 若DRC转移到上游或setup/hold失败，保留该尝试，在新目录修复实际问题，不放宽约束；当前目标是完整32PE版本。
3. 若修复全部约束/面积/结构通过，用已准备的handoff/team/evidence/C32_FINISH_REPAIR01_20261117.py（未部署/未运行）启动新网表自己的gate14/SAIF12/PT12；不能继承旧finish03。运行前绑定新summary SHA，核对原锁和所有子进程。
4. 新最终网表的报告/模型审核需显式连接“原未变RTL功能批量＋等价映射修复＋新门级/PPA”；旧export03只支持同包旧网表链，不可直接重启。
5. 完成新审核、持久归档及C32-A冻结后，才继续可选C32-B/G32。当前C32没有持久归档，不虚构备份完成。

## 固定保护和同步

桌面T80_Delivery_20261113、旧八路全部数据、S0/P80/C80冻结运行及备份不写不移不删。保持原32位ICB四段真实传输、原共享写ACK/读回、X14/W12/b32/SHIFT10、150MHz/SS/.99V/125°C、项目≤1mm²。正式仅20条，100条未自动授权。不恢复旧8路/R1追加队列，不开发宽ICB/旁路/A版。

本地E:/fpga_race-two/kwt1-c32-g32-20261115，个人分支codex/light-light126/t80-pipeline-c32-g32-20261115；仅S0_SYNTH05_FINISH_LAUNCH_20261115.py未追踪历史文件勿提交/执行。禁止新增子代理或goal。更早详记保留CONTEXT_HISTORY_20261117_C32_0339.md。压缩后重新读计划和本文。
