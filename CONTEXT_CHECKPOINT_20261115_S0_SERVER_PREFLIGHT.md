# S0服务器预检接续

**19:31当前终态：** exec57781已结束31/31，0bf新包841文件和manifest93be0a4c…实际匹配；旧R4竞争csrc35普通文件9,639,341B完整归档回读并返回共享盘，SHA07de94123ee8ec5de802b5ca7f34bc216c6f568c24710edd736fd3de753c0a75，原结果/链接/目录未动。synth02/PID71485于19:26:01.309989启动，19:27:02.251476因characterize中waveform返回嵌套列表而失败退出，原锁释放；无后台EDA。版本查询修复已在服务器通过，新工具确实进入characterize，导出accelerator.characterized.tcl；尚无三块映射。

现本地追加CLOCK_EDGES Tcl适配，按安装get_attribute官方“每对象一个值”语义，仅展开一层列表，不改数字；13项相关检查通过，尚未新部署。下一步提交新修复、基于已部署0bf的payload生成更小差分包，建立新bundle/session（拟s0_synth03），不能改原0bf运行目录。VNC18874435新Bash空闲，旧tcsh终端不动。GitHub已到2e85053，当前追加修复和本条尚未提交。

**19:23当前活动，恢复必读：** 修复已提交并推送0bf4af395a6830b17b4666ae6affd5994381ec95。exec57781正在VNC新Bash输入31行完整差分引导，状态local_runs/s0_fix_0bf4af3/transfer_state.json；没有其他键盘输入。该引导会从旧c6输入payload恢复新overlay，逐字重建已在本地独立执行验证通过（167,522B），然后生成新包、核验manifest、归档旧R4竞争测试普通编译缓存并自动启动s0_synth02。**未输入结束前不得向VNC发送其他命令；结束后不要重复手动启动。**

新包=/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-0bf4af3；ops=同root/ops-0bf4af3。新manifest预期93be0a4c5e6e16ebe575d73fa7249e2002c0e1a0db41c371f47302236a2d7475；payload SHA7f2688856e3c3ebbf106690f2b76de1a4752892eed1a5f7f7dc7bda83d3fe167；delta SHA1d465aa099d96ccd4f5b50d53bc9df2d7e2e5d62317879177f15cccd109a7a89。启动脚本handoff/team/evidence/S0_R4_CONTENTION_CACHE_SYNTH02_20261115.py，实际传输SHA5c946de61cb322ccd00aed7a6bc4e6a40ffe8bba3f0df7d8af731b5a4e89d413，待下一次文档提交。只有旧R4 contention01/icb32_contention/csrc普通缓存参与归档，原所有结果和符号链接不动。新stage PID将保存在ops/s0_synth02_launcher.json；日志ops/s0_synth02.log；状态新bundle/runs/s0_synth02/state.json。完成截图takeover_local/s0_fix_0bf4af3.png，先确认包准备回执、归档和启动PID，再查询state/日志。此时尚未看到服务器新包或启动成功。

当前完整完成项：新计划/独立分支；S0工具；16项工具覆盖中本次改动相关12项重测通过；8项原兼容检查前次通过；原T80来源校验及新c6包841核验；cap04真实DC能力检查通过。未完成：S0真实characterize、三块映射、顶层链接/时序/面积、新gate14/SAIF12/PT12。S1–S4完全未开始；不修改T80桌面/旧8路，不恢复T64/G64。失败路径：原tcsh未闭合输入不动；FTP公共地址守卫失败不绕过；cap01–03共享盘ENOSPC；synth01的-version非零退出。所有失败目录均保留。

**19:19本地修复完成：** s0_partition_synth和partition_synth_contract已改为正常退出Tcl会话读取版本、精确命令选项，并新增原生clock TSV→仅恢复create_clock period/waveform序列化精度的实现；原始导出另存raw，任何大于舍入误差的差异或未知/缺失/重复时钟均拒绝，不改端口时序预算。两个新增测试，相关12项检查通过。下一步提交后生成基于c6包输入的差分overlay，新包新session重试；服务器c6包不可修改。当前VNC新Bash空闲，全部输入结束，cap04过、synth01失败且无在途EDA。空间仍需旧可再生缓存归档与启动连续操作，不能普通GUI先释放再慢慢启动。

**19:16最新结论：** 正式s0_synth01/PID64154于19:09:16.856580启动，19:09:20.175020失败并自然释放原锁，尚未characterize或映射。原因是安装DC的`-version`打印正确版本T-2022.03-SP5-5却退出1；保留tool_version.txt及失败state。本地已修改s0_partition_synth.py：从正常退出的DC Tcl会话启动banner读取完整版本及patch后缀，不放宽ProcessLedger非零退出检查；6项映射测试通过。按安装自带官方手册将characterize改为准确`-constraints`，write_script明确`-format dctcl -nosplit -output`；11项相关检查通过。**这些新工具还未提交/部署，不可改服务器c6冻结包。**

安装手册实际路径/eda/synopsys/dc/dc_2022.03-SP5-5/doc/syn/man/cat2/{characterize,write_script,write_sdc}.2。write_sdc没有-significant_digits选项，不猜测添加。原T80 mapped.sdc实读hf_clk导出period6.66667、waveform0/3.33333，说明导出文本会舍入；S0的精确时钟守卫不能放宽。下一步将边界导出的原生clock period/waveform高精度属性另存，然后只恢复create_clock的序列化精度，保留characterize得到的端口预算和其他约束，测试后新包部署。此前尚未实现该精度恢复。

exec6057已完成，R4最终批量csrc的35普通缓存9,970,979B已完整归档回读并放回共享盘，SHA02e87edaedd8cacb7d5cb4f21ff7136ca24559981151cba01644124248202fe4；原240/1200数据、回执及summary不动。所有当前输入已结束，VNC18874435/workspace3新Bash空闲，旧tcsh未闭合终端仍不要碰；无S0后台EDA存活。当前GitHub头d497c19已推送，版本/语法修复为本地未提交。s0_cap04已真实通过工具marker，cap04 summary完整SHA尚未抄录，后继launcher已在服务器核验state passed与summary匹配。S1–S4未开始。

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
