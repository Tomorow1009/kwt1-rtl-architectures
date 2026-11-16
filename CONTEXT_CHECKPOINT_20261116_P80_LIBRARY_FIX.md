# P80库引用修复与继续入口

## 08:21恢复入口：映射与只读预检均在运行

48723的16行传输已完整结束，唯一只读预检PID **126699** 于08:20:30启动；最新查询51680也已结束。前台第二标签是Bash空闲，第一标签watcher105419仍保留（其上限约08:34结束）。无待收键盘会话。

08:21:10原加速器DC98857运行1:01:44、CPU99.7%、RSS25,535,112KiB，日志已进入持续打印优化表的阶段，实际Error行0；没有映射终态。原combined05父95253和export05保持同一队列，不重启。

新预检`root/b0_archived_batch_preflight12/intent.json`实际选中**49,200个生成输入文件，共2,616,732,144B**，PID126699运行41秒/CPU99.7%，日志暂空；尚无verified_candidates终态。源脚本`root/p80_b0_archived_batch_preflight12.py`，日志`root/p80_b0_archived_batch_preflight12.log`。本次只有读原归档/重复文件、写新的私有核验回执，没有删除任何源文件或修改B0只读备份。不能把此只读核验当作允许立即删除。

下一步先收原映射和预检终态；P80仍待CPU/顶层综合、精度连接、gate14、SAIF12、PT12、独立审核及归档。C80/C32/G32未开始。服务器桌面T80和所有旧八路数据不动。截图`p80_map_audit_0821.png`；b9dc3da已经push。

## 08:19只读空间核验传输（当前唯一输入）

**exec48723**正在输入`local_runs/p80_b0_archived_batch_preflight12_transfer_20261116/transfer.ps1`，16行。先收完，不得并发键入、重复运行。当前第二终端标签已经显式进入Bash（第一标签watcher105419保持）；此前tcsh多行只读统计被拒绝，没有文件变更，已改为单行查询。

源工具`P80_B0_ARCHIVED_BATCH_PREFLIGHT12_20261116.py`已提交并push b9dc3da；7474B，SHA `b3eecb8d413edf8bb3be3afd1182806f73f54ad5725ce65ed23a20014b9f41e9`。此工具**只有只读全量归档回读和当前重复文件SHA核验，没有删除/压缩/移动功能**。传输完成后在新私有`root/b0_archived_batch_preflight12`写核验记录；实际PID尚未观察，不能预填通过。

只读发现B0原完整备份`SERVER/IC/light-light126-undergrad-d2-20261109/backups/systolic-b-20261112_2320`仍在，manifest SHA `443a49be5abd11b5ab8d5c5bef744ae1c6cef5908ffd933041d06e086193aea9`已再次核对一致。原备份63653文件/7006124866B；tar1261445859B，SHA `dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50`（本轮完整tar回读尚待），原receipt SHA `b798a588f09cc18edc1239df988f6e2779a16e86989e2e88aca8a30acb29f5ee`。备份是只读保护对象，不修改。

候选只限ced0e139a01e的`runs/systolic_b_final02_final1200/systolic_b_batch/cases/`下生成的`.hex/.verilog/.bin`：清单整批统计分别1579033392/943718400/93980352B，约2.62GB；工具将重新核对实际case范围和文件数，不能把统计当删除依据。现有.csv输出/.npz/JSON/日志/源码/网表/SAIF均不在候选中。没有执行任何新删除。T80桌面、旧八路和B0备份都未修改。新预检不证明无人使用，也不授予清理；若以后确需处理，必须另核占用及当前文件身份。

P80原综合保持95253/98857，08:04:52 DC已运行45:26、CPU99.8%、日志180924B/实际Error0，进入DW算术单元处理；没有新EDA。原export96154保持等待。后续先完成原映射/精度/门级/活动/功耗，C80仍未开始。

**07:56:22恢复定位：原combined05仍running/synthesis、仅共享块完成；现已切回第一标签watcher105419，第二标签tcsh空闲。全部键盘输入结束，无需收exec。下一步继续原队列，不重启，若需查询可切第二标签并先看截图。**

## 07:55映射日志继续推进

07:55:04原DC98857 elapsed35:38、CPU时间35:33、CPU99.7%、RSS25,529,944KiB；日志从11,921B增至18,344B，实际Error行0，尾部已完成shift_q常量寄存器优化并进入`Updating timing information`/UID-85。不是先前日志位置。截图`takeover_local/p80_dc_progress_0755.png`；输入72177已结束。当前前台第二标签tcsh空闲，第一标签105419观察器保持，其他进程不变。尚无最终PPA；C80未开始。

**等待期间补充：** P80_RUNBOOK.md已完成入口/哈希/状态说明，CLI参数及9个列出脚本路径核对通过，ABI旧状态已更新；文档提交f2b1008已push，不改服务器包。查原S0_NEXT_TOOLS_TRANSFER/S0_RECOVERY_RUNNING：synth03加速器曾耗时约4438秒才写出映射（该轮因2条边界命令错误被拒绝，CPU未执行）；197秒只是后来的增量种子恢复。当前P80冷映射不能以197秒判断卡住，亦不保证与4438秒等时。

**07:46:22观察器仍显示running/synthesis，仅shared_sram完成；07:45已切回第一标签的watcher105419，第二标签tcsh空闲保留。当前前台不是命令提示符，恢复后先fresh截图再输入。**

## 07:44进程与资源核对

原加速器98857仍在R状态，elapsed24:44、CPU时间24:40、CPU99.7%、RSS17,987,448KiB（07:44:10）。父95253/export96154仍在。tmp可用89,383,219,200B，共享可用1,048,576B；07:44:40主机MemAvailable707,533,244KiB、SwapFree134,215,676KiB，无内存不足迹象，未干预原作业。

为只读检查在workspace3的同一MATE终端新开第二标签；**当前前台是第二标签的tcsh空闲提示符**，原第一标签watcher105419仍运行。最近输入18925及内存查询全部结束；不可把第二标签当Bash执行here-document。截图`p80_resources_0744.png`与`p80_memory_0745.png`。P80完整PPA仍待，C80未开始，受保护目录未变。

**07:34:21终端状态补充：VNC18874435/workspace3前台只读观察器105419正在运行，每60秒打印原队列与三个块的完成状态，最多60次，综合结束自动退出。输入29625已经结束，当前不是Bash空闲提示符，不要直接往观察器键入命令。combined05/加速器/export05保持原进程；07:32:32加速器已运行14:06、CPU99.7%，日志11,921B。c5e4e11已推送。**

## 07:31恢复后实测

已重读当前计划、AGENTS、交接及状态。07:31:10，原combined05父95253仍在synthesis、error为空；加速器DC子98857运行11分44秒，CPU99.6%、RSS8,599,916KiB，日志实际Error行0。export05父96154仍等待。没有重新启动、修改受测包或并发EDA；全部VNC输入结束（最近只读69172）。截图`takeover_local/p80_live_0732.png`的实际时刻为07:31:10。

已完成证据保持：三个队列深度各ASIC14、深度2恢复/竞争及自己的240任务。共享块已mapped；加速器/CPU/最终整机综合、自己的FLOAT精度连接、门级14、活动12、功耗12及最终审核/持久归档仍待。下一步继续原combined05及export05，不重跑旧队列。C80/C32/G32未开始，桌面T80与全部旧八路数据不动。

## 07:20真实DC修复已通过共享块

07:23:29补充：加速器仍运行、实际Error行0，尚无cache终态。重新读取原launcher日志确认子PID为**98857**；本地07:20条目曾将屏幕数字抄为99675，现纠正。服务器记录没有改变，从未对误抄PID执行操作。最近只读67752也已结束，无当前输入。

原combined05父95253保持、export05父96154等待，所有输入结束（最近只读32287也已结束）。07:20:36实际读取：新综合06的`blocks/shared_sram/cache.json`为mapped，耗时35.674336516764015秒，`compile.log`实际Error行0；加速器子**98857**已经启动。此前fresh_link96331、characterization97905、shared98527均由原ledger顺序接续，没有重启作业。

`boundary_contract.json`已记录两个子块各自旧/新标准DB逐字节一致及统一路径；修复验证范围现在是共享块实际映射通过，不能据此提前宣称加速器/CPU/整机时序或面积通过。截图`takeover_local/p80_boundary_fixed_0719.png`、`p80_shared_map_fixed_0720.png`。继续读原队列，下一步等待加速器、CPU及顶层链接，取得整机数值后原18项后继自动继续。当前P80仍未冻结，C80未开始；T80桌面/旧八路保持。

## 07:14实际接续（当前恢复入口）

- 17240的24行与后继93763输入均已完整结束；没有当前键盘输入，VNC18874435/workspace3 Bash空闲。
- **cache11成功**：35文件无损归档/全成员回读/持久复制核验，SHA `2918ba44fb0c373f6dcd7ea5b622702f8926fbb69b3fed47cf2e14a4567145d5`，成功出口共享剩9,437,184B；原结果/输入/可执行文件/波形保持。不要重复任何缓存归档入口。机器回执root/b0_contention_csrc_20261116.receipt.json。
- **combined05父95253**，07:13:07control为running（started07:11:41），已取得原锁；新1023646包的新综合`runs/p80_synth_d2_06/p80_synth`。共享又剩1,048,576B，任务输出仍写tmp；原队列保留，不重启。尚未见本次映射终态或PPA。
- **export05父96154**，07:13:44启动等待原队列。只在原队列成功自然退出后收集自己的报告，不自动验收或进入C80。
- 截图：`takeover_local/p80_cache11_outcome_0712.png`、`p80_combined05_state_0713.png`、`p80_export05_launch_0714.png`。文件名近似时间，以图中时刻为准。
- 最近push ff22ab9，当前要更新此07:14记录。自己的240/三深度14不重跑；P80尚待新综合、精度连接、门级/活动/功耗与审核。C80/C32/G32未开始；T80桌面与旧八路不动。

## 07:09恢复补充（优先于下方旧输入状态）

52140输入已完整结束，新1023646包**947文件准备核验通过**，manifest为下文402c0816…82bcd，源保持；截图`takeover_local/p80_1023646_prepared_0707.png`。07:07:58又只读核对cache11候选：索引4/35文件/10,760,211B，原两例真实CPU竞争PASS、contract存在，旧82946/84918均退出，共享剩1,048,576B。

**现在唯一输入exec17240**：`local_runs/p80_combined05_cache11_transfer_20261116/transfer.ps1`，24行。payload SHA `660987ebf346fb59e5d2faae81c5bb33837db9a70fcbe1a6eb7f285c95b8fbaf`，逐字节差分重建combined05/helper02/cache11/export05（四个文件SHA见下文），先校验新包SHA，再归档cache11，成功后立即启动combined05；export05只部署不启动。先收17240并看截图，禁止并发键入、重复运行。**cache11和新队列PID尚未观察，不能预填完成。**

新控制脚本、检查点和P80进度报告已提交并push **99dd9f2**；1023646工具包不改。当前只有旧未跟踪S0_SYNTH05_FINISH_LAUNCH_20261115.py，不能提交或执行。后续确认combined05运行后才启动已部署export05等待器。

记录：2026年11月16日07:06，北京时间。恢复先读AGENTS、根交接、用户计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`和本文件。服务器桌面T80_Delivery_20261113及全部旧八路数据不写、不移、不删。

## 唯一当前操作

**exec52140** 正在输入`local_runs/p80_ops_transfer_1023646_20261116/transfer.ps1`，共44行；07:05观察约21行。先收完整会话并查看`takeover_local/p80_ops_transfer_1023646_20261116.png`，禁止并发键入、重新传输。当前无自己的EDA在跑，只有这次新包输入。VNC18874435/workspace3；workspace4未操作。

新包：`/tmp/s4_21usr_p80_20261116_0315/light-light126-p80-1023646`。源提交`102364644dd181b23358dc2c7fe0d6e8279ae0d2`已push，947文件。

- payload SHA `2a1b6f16a10f84b664d6c9db83dca38e1ed6e25ea20c4da972d7026ce8b995be`。
- 预期manifest SHA `402c08165610ed18bdd772cddd3d527570fd62bdaa6ff820e0ad19b5d7082bcd`。
- 传输xz SHA `f8387b0ccb86f06e655293e7a9c740ab94365bb3bd54b496f34aae96142a607f`，14,804B，6个变化文件；从原4cf payload重建，原始字节保持。已本地独立重建验证，服务器准备尚待观察。
- `server_script.py`的序列化分隔符已用AST核对为单个真实换行，不能把PowerShell/JSON显示中的转义误当双重编码。

## 本轮真实观察及失败

cache10已成功：B0 R4-SAIF replay的40个普通csrc缓存完整压缩/逐成员回读/持久副本核验后移除重复缓存；SHA `583863ce923f05dd5caaf0931c9b7c5c17036b8cee53397ab36971650097d59b`。SAIF/VCD、原日志/输入/可执行文件及输出未动，T80桌面和旧八路未动。此前cache09等同样已结束，禁止重跑。

combined04父82946进入4cf包新综合`runs/p80_synth_d2_05/p80_synth`，06:51:48失败，export04父84918正确停止；06:54:14确认两PID不存在、原锁不存在、共享只剩1,048,576B。全部日志、失败网表/目录保留，不作为PASS。

具体根因：导出的`shared_sram.characterized.tcl`与`accelerator.characterized.tcl`均含原T80运行目录的`set_local_link_library`。它在新库加载后又加载旧路径的同名库，产生UID-15/UID-993；之前仅修`set_driving_cell -library`不够。旧库实际路径为Desktop/IC原T80运行，绝非受保护的桌面交付目录；只读其库身份，不修改。

1023646在`p80_partition_synth.py`新增`local_link_library_budget`：只接受单个绝对标准DB路径，核验旧/新库同名、同SHA，替换为新link的canonical DB路径。其余操作条件、驱动弧、transition、延迟、负载、时钟保持。14项本地工具测试通过，真实DC验证未完成；RTL、固件、编码/缓存/平台参数没有变化。

## 已完成P80证据，不重跑

- 原142包深度2/4/8各ASIC14通过，354816输出/版。固定12周期一致，均值77545.3333333；150MHz折算1934.3523788task/s。暂选最小深度2，面积和时序资格仍待。
- e139包自己的十阶段恢复、CPU竞争、前20条240任务全部通过。6082560输出及total零差异；batch摘要SHA `36953e487c757a9980c4ac33760b7a8f65c6f61209e6b2582a8342b582d7e687`。均值77545.1583333不能混用固定12。
- 新只读搬运统计详见`workspaces/arch03/P80_STAGE_PROGRESS_20261116.md`。固定12源码摘要SHA `43e9ec58048d24ab8ab7d505723f7360b1e7e1e6eeaf5d76c81134cef34222c8`；编码总357072B、事务419868，平均每任务29756B；实测比`1.75B+25344`条件模型前11层多128周期、末层132。四阶段延迟统计来自原观察器，非追加仿真。
- S0已完整验收和持久归档，不重跑。C80/C32/G32未开始。

## 本地准备的新接续（尚未部署/启动）

`handoff/team/evidence/P80_FINAL_COMBINED05_20261116.py`：SHA `46e2a8fb416db99febbc9c2bb6ea09b619b515bb185711c2a3a9782277d11651`。使用新1023646包，新队列`runs/p80_finish05`、综合`runs/p80_synth_d2_06/p80_synth`，root控制`p80_final_combined05.json`。增加旧04及export04失败、自然退出核对；一个原共享锁跑新综合→自己的FLOAT连接→17项最终网表检查。严格Path SHA/成功与失败全main演练两例通过。

`P80_PRECISION_HELPER02_20261116.py`：SHA `aa506efa781e76928fbd16aa614c47b47e4e927ff2e63cf396a319cbd849b2e4`。从原helper只更换BUNDLE到1023646，仅供导入调用precision_stage，**不要直接运行旧main入口**。计划部署名root/p80_precision_helper02.py。

`P80_EXPORT_REVIEW05_20261116.py`：SHA `952242ef4a1ea2b9ee5bcde89ec0cd4b4c48f2bd504a55ae8a3f1031a31fee4b`。等待新combined05自然成功后收集同队列报告/活动/连接/模型；输出`p80_report05`、`p80_unknown_inventory05`、`p80_unknown_connections05`，不自动验收或进C80。

`P80_B0_CONTENTION_CACHE_RECOVERY11_20261116.py`：SHA `3cbc51a964cc9b70cebdd80e37976cc9f57a4ee7f44dfa3c6056776bda3a319f`，**本地准备，实际候选摘要仍待只读核对**。固定旧`b0_cache_candidates01.json`索引4，B0包`...ced0e139a01e/runs/systolic_b_v3_validation03_contention/systolic_b_contention/csrc`，35普通文件/10,760,211B。07:00仅大小扫描一致；先核对原2例竞争PASS、source_inputs/build_contract及无人使用再执行。脚本自带全身份检查、逐成员回读、原证据保持、持久复制和排他检查；只归档csrc，不启动EDA。新tmp文件`b0_contention_csrc_20261116.tar.gz`及receipt；已通过的cache入口绝不重复。

因为共享盘不断满，若cache11核对通过，计划在它成功返回后立即启动combined05，避免再次在传输等待期间耗尽锁目录空间。所有新启动器还需提交和部署。正式归档工具14c6dab已包含于新包，但未运行，最终持久归档仍需实际足够空间；不能预填成功。

## 下一步

1. 收52140，观察新包947文件准备回执和真实SHA。
2. 只读核对cache11候选摘要/契约、当前进程/锁/空间。输入期间禁止并发。
3. 提交并部署05/helper02/cache11/export05；完整核验归档后立即单锁运行新综合。所有旧失败不重启、不覆盖。
4. 真正取得映射后先报告面积/setup/hold/宏，再完成自己的精度/门级14/SAIF12/PT12和独立模型审核；阶段归档冻结后再进C80。
5. 上述新控制脚本和进度报告目前未提交；旧未跟踪`S0_SYNTH05_FINISH_LAUNCH_20261115.py`不加入、不执行。Python用E:/fpga_race-two/.venv-kwt/Scripts/python.exe；不使用WindowsApps别名。
