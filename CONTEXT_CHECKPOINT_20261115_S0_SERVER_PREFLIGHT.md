# S0服务器预检接续

**19:09优先：** cap04已实际运行DC并输出S0_CAPABILITIES_PRINTED，5秒结束；命令characterize/write_script/read_ddc/compile/report_timing存在，帮助只列命令简介，具体边界脚本仍须实跑。cap04 PID62910；其源/输入预检通过，之前cap01–03失败都保留。R4 metrics14的35份普通编译缓存9,970,277B已完整归档回读并复制回共享盘，SHA7ad3e546fc4c5a7428604c75a70b8322997dbc6e6e92afc64745f0e0587f2a9；原结果/链接/目录未改。共享剩余空间随后又降到1MiB。

当前exec6057正在输入11行新“R4已完成batch编译缓存归档→立即启动S0 synth01”脚本；local_runs/s0_r4_batch_synth/transfer_state.json。脚本handoff/team/evidence/S0_R4_BATCH_CACHE_SYNTH_20261115.py SHA55ef4b2bf15769b990f804b0bd0e965fba6b02528fc6d933193644ae3fa45958，先校验cap04终态/summary，再仅归档旧R4 finish01_final1200/icb32_batch/csrc普通缓存、保留全部1200回执及结果，然后立刻启动冻结c6工具的s0_synth01。**不要并发输入，不要再手动运行synth_command.txt；当前脚本会自动启动。** 完成看takeover_local/s0_r4_batch_synth.png，实际PID记录ops/s0_synth01_launcher.json；主日志ops/s0_synth01.log，状态bundle/runs/s0_synth01/state.json。当前尚未观察到正式映射启动。

**19:06接续优先：** cap03/PID60453也在19:01:02创建原锁处ENOSPC失败，DC未启动；19:04可用空间又回到1MiB，释放的40MiB已消耗。不能称能力已通过。新动作将旧R4 metrics14编译缓存完整归档并立即启动cap04，避免两次GUI操作之间共享空间又满。新脚本S0_R4_METRICS_CACHE_CAP_20261115.py，SHA376c886fdf77852d6d3ef1e15e29af6062b39c6db3a3f795d16a9edff36e89bd；目标严格为light-light126-icb32-r4-20261111_043048-96443c284a1c/runs/icb32_r4_finish01_metrics14/icb32_soc/csrc，只在原stage passed且summary哈希一致时归档，原结果和符号链接不动。输入exec58322运行中，11行，local_runs/s0_r4_metrics_cap/transfer_state.json；先等输入结束并截图，不要并发输入。cap04启动后PID保存在ops/s0_cap04_launcher.json，先查终态和capability.log。synth启动命令已准备local_runs/s0_direct_c6aa1e2/synth_command.txt，尚未执行。

2026-11-15 18:50，北京时间。继续用户新计划T80→P80→C80→C32→G32，最终32PE、项目面积≤1.00mm²。先重读AGENTS、根交接、IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md和本检查点。

**19:00:18最新进展，覆盖下方空间状态：** T64输入421文件合并存储已完成，路径和字节全部保留，但随后共享盘又满；s0_cap02/PID56333同样在mkdir原协作锁处失败，DC未启动。已完成对旧R4门级csrc的38份普通编译缓存归档（48,122,849B），逐tar成员大小和SHA全部回读一致后移除重复缓存文件；符号链接、目录、原state/summary/结果/网表/波形不变。归档已复制返回共享盘：原R4 gate目录/csrc_regular_files_20261115.tar.gz，SHA09351c22679151e1d7dbd7c856877f481ff8c1e058799fa38cb3701dd476a4e8。临时归档和回执保留在新ops/r4_gate01_csrc_regular_files.tar.gz、r4_gate01_csrc_archive_receipt.json，回执记录每个原路径、字节、哈希。只涉及旧R4编译缓存，桌面T80和旧8路完全未动。实查free41,943,040B。

空间脚本S0_R4_CACHE_ARCHIVE_20261115.py SHA4256dd2a859f23571f207139bd30a95cfd7dc71a862d08d273995c6d9fd9d1aa；11行输入exec58660完成。已发起新的s0_cap03命令，先确认对应截图/状态，禁止重复启动。此时没有任何S0映射结果。

## 已完成及身份

- 新工作树kwt1-c32-g32-20261115，个人分支codex/light-light126/t80-pipeline-c32-g32-20261115，文档头4bf1e68已推送；实际S0工具c6aa1e255ae16d0479a6532460548c0f26cbdc58。
- 第二次完整传输exec66349已退出0，59行全部完成；18:41:47服务器实见S0_INPUTS_PREPARED。841文件，manifest SHA fbd6c78675276aad5fffca577c80987bf596846743dd46ba45e672fad28da0e8。
- 新包/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-c6aa1e2，ops为同root/ops-c6aa1e2。原输入833文件保留，新包无runs复用或共享硬链接。T80硬件876b883未改。
- 18:45:28核对原锁不存在，/tmp可用98,730,401,792B，MemAvailable726,368,244KiB；共享盘只有1,048,576B。其他用户EDA进程存在，不操作；本账号无EDA。
- 18:46启动s0_cap01，PID53897；因共享盘ENOSPC无法创建原.arch02_team_lock而失败，**DC没有启动**。失败state和log保留，不重跑同名session。入口已通过原T80来源及841输入核验才到取锁阶段。

## 当前正在处理

- 只读检查确认两个旧T64包均无runs，尚有421份相同但不同inode输入，共4,216,598B。只涉及IC/.../bundles/light-light126-t64-v4-65d2507-delta01和fix02。
- 新脚本handoff/team/evidence/S0_STORAGE_PREPARE_20261115.py，SHA2ad44ac50bee74d8c398b3b5cd4c76b730bb94aca8c62da88430a3da539e5c3b，逐个核验后用硬链接替换重复存储，保留全部路径、内容、清单及前后回执，不涉及T80、旧八路、runs或结果。
- exec15855输入10行已经结束，服务器脚本可能仍在执行。最后截图takeover_local/s0_storage_prepared.png尚未显示完成提示；**先截图看到S0_T64_INPUT_DUPLICATES_CONSOLIDATED或错误及Bash提示符，再输入下一命令**。
- 新脚本在ops/s0_storage_prepare.py，回执ops/s0_t64_dedup_prepared.json及_complete.json。不要重复执行同名脚本/回执。

## GUI与禁止路径

VNC18874435、workspace3的新独立Bash终端。旧tcsh终端仍是未闭合的失败输入，绝不可闭合或键入；自动审批此前拒绝执行它。workspace4不碰。FileZilla已关闭，代理公共地址检查失败，不绕过。板端转发exec91027保留。

桌面/storage2/2026contest/server4/s4_21usr/Desktop/T80_Delivery_20261113与全部旧八路数据不写、不移、不删。旧T64父325056、DC15147在18:30已自然结束，映射结果保留，后继已停止；不恢复旧队列。

## 下一步

确认空间整理完成后，用现成capability_command.txt将session/log均改为s0_cap02再执行。原协作锁不换路径、不清锁。先看安装DC的characterize/write_script/read_ddc实际帮助，随后在新s0_synth01运行分块综合；边界精度和顶层跨块检查不能省略。S0新网表仍需gate14、SAIF12/PT12及面积/时序/结构报告，完成后才能进入S1。S1–S4未开始。

当前本地14项S0工具检查及8项原T80兼容检查通过；尚无S0映射、门级或PPA通过结论。已完成测试不重复运行。同步此检查点、根交接、STATUS和空间处理脚本时检查Git差异。
