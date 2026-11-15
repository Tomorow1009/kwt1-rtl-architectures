# P80库引用修复与继续入口

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
