# N1持续执行检查点（2026-11-13 03:01）

## 03:12重要增量（优先于下方03:01状态）

- R4 L01归档02已于03:08:37完成，03:10:40独立核对raw不存在、共享final为6987485022B、临时gzip不存在、回执SHA抄录与服务器相等。全解压12595749229B与原SHA一致后才删除重复raw，净节约5608264207B。证据`handoff/team/evidence/R4_L01_STAGED_ARCHIVE_20261113.json`；不要再启动归档或resume-copy。完整gzip及回执在共享9305的runs/r4_l01_archive02，原结果全部保留，原路径如需VCD须先恢复。
- N1原综合最后03:06仍running，没有终态/新PPA；下一步先查原169157/174746，不重复启动。
- B0原report SHA已精确核对为677a1ae11042ffe6aab981b1b0f124b29f604e6dc0d9bb29e96d9f04f4f68a1a；L01 isolated proof SHA分8字符核实为d894ec7e5f9c3b33e6c99a800cd24df6fd66ba68882f63ffac15784849c4a445（之前手抄漏了一个f，不能用短串）。
- 新B0完整unknown只读工具`b0_saif_unknown_inventory.py`已冻结，SHA c57ed783754a6411bc3d43139dcf90a420d7c5a2f87ca050b12b98e75b20056d；15项测试和独立代码审查通过，尚未服务器部署/运行。仅扫描已有SAIF并对应原B0网表，不新EDA/活动赋值。全部native回执须相等；COND子项非零时明示清单范围未完全覆盖。显式7依赖+tool起止核SHA，输出空间守卫与失败保留，不自动豁免任何连接未知。
- 根将新工具/说明/进度提交到个人分支，并准备独立小reviewops包，依赖现41b OPS的冻结scripts；不能覆盖41b/9305。N1归档runtime工具仍由requirements代理准备，未冻结、不纳入本次小包。
- `N1_STAGE_PROGRESS_20261113.md`及15KB Git可同步`N1_FIXED12_FLOAT_REAUDIT_20261113.json`已完成，明确阶段未验收；不用本机ignored local_runs链接作为唯一团队证据。
- VNC18874436/workspace3空闲shell仍共享9305cwd，FileZilla关闭，无待输入。03:09共享free10195304448B，后续空间需重查。

恢复时先读AGENTS、根CONTEXT_HANDOFF、`workspaces/arch03/IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`、本文件及STATUS，再核实际进程/锁。用户要求持续推进，未发暂停；VNC/FileZilla均已释放给本任务。阶段顺序不变，N1未验收不能进入N2。

## 已完成与冻结身份

- N1生产硬件`9305c6948c764fed01fe86b20bb3db94170299ab`保持不变；B0生产63da及原备份不动。
- 真实ASIC14、恢复十阶段、CPU竞争均已通过，分别354816、76032、50688输出；详见`handoff/team/evidence/N1_SERVER_PROGRESS_20261113.json`，不重跑。
- 新100条4800HEX集合/长度/哈希通过；自己的1200实际任务仍未开始，不能以文件检查替代。
- 固定12平均29711完整周期，150MHz折算5048.635185621487 task/s。旧B0同浮点源重新量化对照为30502.333333周期/4917.65657；数值与编码长度同时变化，只比较整体收益。
- 新工具OPS `41b0846ce71990d1dbf29fcd22baff32febc6c48`完整包已FTP上传、781文件哈希验证并独立解包，真实Linux runtime身份核验通过。原9305 BASE不改。
- 最新已push且ls-remote独立确认的交接提交`18f7960ebd4bc9325af07fb372c959ea5e148f57`。之后代理说明/工具仍有未提交修改，先git status，不覆盖。

## 服务器独立临时运行根

`/tmp/s4_21usr_n1_20261113_0210`，s4_21usr所有/0700/独立磁盘，最终须完整归档到共享存储，不能当永久交付。

- BASE：`light-light126-n1-v4-20261113_013211-9305c6948c76`，manifest SHA `73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d`。
- OPS：`light-light126-n1-v4-20261113_022722-41b0846ce719`，manifest SHA `0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e`；ZIP SHA `17d2e972e0452daf70505a69613423979bc0f1c9f10a50d6fc6ba676dc0a65e3`。
- 两包RTL/主IRQ固件/数据相同，sequence ELF及其manifest ELF摘要不同，但bin/verilog相同；旧sequence回执仍绑定旧ELF，不能宣称新ELF已执行。
- 原共享团队锁仍在`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`。不能建立私有锁替代、清锁或并行EDA。

## 现有作业：不得重复启动

1. **N1综合169157，DC子进程174746**：BASE的`runs/n1_synth01/n1_synth`，02:12:42启动，03:00:38仍running，无最终mapped.v。02:57子进程CPU99.7%、RSS约21.6GB，日志仍处理linear16x5。源/约束不变，不能认作挂死或重启。driver为BASE的`runs/n1_synth01.driver.log`，state在`runs/n1_synth01/state.json`的`stages.n1_synth`，不是顶层status。
2. **R4 L01授权归档186061**：03:00:38仍compressing_to_separate_tmp_original_retained，error=null、original_removed=false；临时partial6152976860B。用户已明确允许全解压SHA/字节一致、无人使用后删重复raw，批准无需再问。工具目录private runtime下`light-light126-n1-archiveops-3b5cf866b337`，driver `archive02.driver.log`，临时目录`/tmp/s4_21usr-r4-l01-20261113_0233`，权威receipt为其receipt.json。原件仍在旧497包；最终输出在共享9305的`runs/r4_l01_archive02`。
3. 03:00:38空间：共享free6945767424B、/tmp758519197696B。共享波动由其他写入造成，不能以旧空闲量启动大波形。N1使用SAIF，无普通大VCD。

归档02只能等待其完整终态。若出现回存失败，先检查权威/tmp receipt与进程；`--resume-copy`只恢复复制，必须同原共享9305 cwd和同临时目录，不重新压缩/删raw。archive01失败及其partial删除回执保留，不能重跑；历史旧gateprobe清理已完成也不重复。

## B0只读功耗审核的新事实

- OPS `runs/b0_inventory01/inventory.json`因128MiB累计预算停止，保留失败。首次mkdir命令未创建runs父目录即失败，没有启动核对，随后才启动该一次失败inventory。
- 只stat固定272文件共206165590B，最大13773448B（disabled_timing.rpt），无单文件超过16MiB。明确采用512MiB累计预算、保留16MiB单文件限制，新`b0_inventory02`成功，读取418724302B，没有EDA或大波形读取。
- inventory SHA `ca3a4bc43cd7d3871f9837349a04fff1d8133f2cc354f88ab8c459dd1936a1fe`，状态read_only_inventory_collected_review_required。
- 原总duration_ns2440186.422648、energy_j0.0001704154782132198078564，Decimal复算weighted=`0.06983707336109641885320248724W`，J/task=`0.0000142012898511016506547`。纠正早期文档长小数手抄错误，不是新功耗运行。小证据已18f7960云同步。
- PWR601/602只是averaged/four-threads Information；PTE016只是共同base660ns时钟展开Information（hf旧6.667，lf旧66.000）；PTE003是禁用弧通用Warning，尚需具体flags/objects解释，不能凭通用文字断言有loop。
- L01 switch/static均451386，exact450133，default1253，已有实际零direct/global leaf连接证明；这是默认声明豁免，不是未知活动影响豁免。
- 两份模型回执存在，宏92+32+32+64=220；每小宏泄漏4.88099977e-6W，每大宏4.60310002e-5W，非零，与无条件两rail组和匹配。4096的VDDPE无条件0.014038mW，不能误抄0.004038。
- L01未知声明41406/全未知18620；含真实committed_data，不能整体归为厂商模型内部或以valid=0自动豁免。完整未知名单/连接与剩余条件影响审核仍未做，system_power_verified=false。

## N1后继入口与缺口

- 02:59新OPS直接调用n1_saif.qualification读取既有R4 crosscheck02成功，25个具名artifact通过。路径为共享ced包`runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck`，SHA `a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26`。方法activity大小94632798B。这个入口核原交叉审核产物，不重新读取已归档的R4 VCD，无需恢复原大波形。
- 综合完成后先读原state/summary和锁；核新220宏、面积≤1.2、全部DRC、setup/hold/结构。不能套用B0修复的旧U编号。N1结构脚本证明80PE边界但内部实际14×12锥及32累加要结合新网表，见N1_MAPPED_REVIEW_DECISIONS。
- 新100回归入口已代理独立审查：OPS n1_server.py batch --session n1_batch100_01 --dataset `/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all`，加runtime-root/OPS manifest。它不读synth-run，不需BASE evidence参数。必须等原EDA锁释放，正式串行。
- batch固定一次编译1200任务，`--cases`不会筛选。首1与首12回执分别25344/304128输出，观察同一批次前缀，最终30412800每字段。初始空间13.25GiB，后按实际单例最大估算；末尾还重审全部capture。失败以state为准，batch_progress可能只是最后成功前缀。
- 门级14明确无SDF，只比实际result/sat，total由ASIC RTL自己验证，不从参考伪造门级total。
- 新full100 FLOAT仍缺，既有异步问题待用户给匹配原始包路径；预期SHA edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9。缺源不能N1精度验收/N2，但不妨碍整数硬件工作。

## 当前本地并行任务与界面

- n2_d1_feasibility：独占b0_power_review_inventory改进/测试、B0说明、新完整unknown SAIF→mapped只读工具。13项size-plan/去重测试已过，后续unknown工具未定稿，不能部署中间版本。无N2/D1硬件开发。
- requirements_plan_audit：独立n1_archive_runtime.py准备，仅在阶段完成/原锁空闲时完整归档注册OPS/BASE到新共享目录；不删/tmp、不改旧回执/路径、symlink不跟随。当前未运行，不把索引迁移当干净复现。
- n1_rtl_audit：写独立N1_STAGE_PROGRESS_20261113.md；不改硬件，不填缺失PPA。
- VNC18874436/workspace3仍共享9305 cwd的空闲终端，FileZilla关闭；03:00状态截图已读，没有待Return或exec session。当前Linux VNC需每次重新观察后输入；type工具返回session_id时先wait_stdin完成再发Return，避免长命令未打完。
- 没有使用mcp CUA会话，不需该工具的completion_summary。使用既有F:/linux_fpga_try/ac820.ps1控制板端Linux，比赛服务器只经VNC/FileZilla，不建立直连SSH/隐藏传输通道。
