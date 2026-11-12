# N1持续运行检查点（2026-11-13 06:00）

## 06:33恢复与执行增量

- 已按要求重读有效计划、检查点和团队规则。唯一batch02 PID18736继续；实际06:30:22.390771已完成488任务，failed0，result/total各12367872，ETA20=5377秒；最后sample041_layer08/cycles28727/host3.323秒。最近child78648已正常回收，78708在跑。不是完整1200通过，不重启。
- 原manifest实际元数据：694870字节，SHA `9900a9bd1addbdeb256020ba9a04f4615791fbd5a624abd411364098c382c97e`，100个sample，每项有sample/rank/split/wav/wav_sha256/sample_sha256/layers。尝试通过现有FileZilla下载这一个小清单，服务器明确返回550 Permission denied，没有下载文件。未改权限、未启新通道；FileZilla现已关闭且窗口清单确认。文件名含0638的截图不是实际时刻，以服务端06:30记录为准。
- 本机已有105829条音频路径/split索引、原音频、官方模型和锁定TF环境。后续改为上传本地小索引后在服务器输出100个索引位置及匹配摘要，再只核对应100条本地WAV；不下载原manifest，不对全数据做新哈希、不运行TF、不以旧单坐标参考代替矩阵。
- 新辅助归档入口只在本地完成；root独立16测试PASS/2.854秒及静态review无阻断，尚未提交/打包/部署/执行。固定九项名单，原锁空闲才可归档，完整回读，无源删除。新的remaining11控制采样不擅自加入名单。
- B0 actual-declaration查询正在核结果；后续64宏A/EMA/EMAW查询已输入但尚未Return，不能重输入。其余11层控制扫描wrapper本地准备中，无远端新扫描/EDA。仍不进入N2。

## 06:06审阅增量

### 06:18后续实测（当前恢复优先）

- 06:10:40.217366新batch02仍running PID18736：completed301、failed0、result/total各7628544；ETA20=6777秒，最后sample026_layer01/cycles30547/host3.42，最近64760/64823均wait=true rc0。下次约06:25监测，不重复启动。
- N1原check_timing.rpt已完整读取509B，唯一TIM-134为4个高扇出网，其他检查无warning/error。批次后需一次当前DDC timing_audit定位4网，不能借B0结论；该诊断本身不是新增STA批准。
- 原mapped.sdc核SHA：2clock/1falsepath/12case。HF序列化为6.66667ns，原综合cfg为6.666666；现有n1_power.py已用同cfg精确恢复副本并要求PT实际读回1e-12容差/Decimal一致，不改原SDC、不需重综合或改工具。功耗阶段实际回执仍待。唯一falsepath fromLF到四tim0..3/u_in_stage/r_ls_clk_sync_reg[0]/D。
- 06:15:40 constraints.rpt253B完整核原artifactsSHA，clean marker1/VIOLATED0/error0，正文无违例；零目标drc_audit跳过，不重复启动DC。
- 06:16:45实际SDC case12为JTAGTCK/TMS/TDI0、aonreset1、dbgmode三位1、bootrom_n0、aonwake1、bootrom_deglitch/io_q1、pll旁路和divby1。SysMem35输入HFmax1/min0、slew0.1；71输出HFmax1/min0、load0.01，共106位/353约束行，未新增DMA/CPU例外。
- 全7组面积已实读，leaf348866/macro220；标准库叶求和4473365.18786784um²与原DC报告4473365.187497分开保留（微小求和差非混用）。known_added0.7904551087005953mm²，保守0.9511486879005002mm²。area_basis实际字符串**identical_library_geometry_proof_reused**，不是先前口述silicon…；官方归属false。代理已保存N1_TIMING_DRC_AREA_REVIEW_*，两条最后实际查询待其补文档。
- B0原厂模型身份链/compile_command核验：+define+ARM_UD_MODEL、+define+functional。readWrite258–321实际读取，异常RET/地址/控制有置X分支；正常GWEN!==1写仅更新mem行，无Q赋值，GWEN==1读才赋Q_int。不能把异常分支概括为所有write置X；正常写保持Q。L01 write-only与fullX Q一致，但其他11层control尚需证据，功耗未通过。
- 06:17:48局部2234未知按现有parser初分internal633/output821/input780，NO_GLOBAL_WAIVER=true。代理需复核633“internal”不是默认未识别；1601端口不能忽略跨层消费。旧no-load精确交集仍0。
- 为看完整模型，root只将远端终端Ctrl-minus两次；现在已经Ctrl0恢复。最后localkind查询已结束，shell空闲/FZ关闭，无待Return。
- requirements代理新任务仅本地准备辅助归档工具/配置及安全测试，严格显式范围、原锁空闲、无源删除，不远端执行。n1_rtl代理收尾时序/面积小证据；n2_d1代理继续B0最小消费边界审阅及是否补其余11控制采样的方案，未启动扫描。仍不进入N2。

- 小证据及交接已commit/push并ls-remote核验：**0a175676daaed8582fd8e6a9fa57cea5db9d0bb1**。生产9305/运行OPS0f62不变；当前新文档增量可另次同步。
- 06:00:41实际精确交集：LOCAL2234 PROVEN1253 **HIT0 REMAINING2234**。没有任何局部未知因此豁免。06:03:26前2原名为local `u_e203_subsys_top/dcsr_r[0]`、`[10]`；proof为`u_e203_subsys_top/u_e203_subsys_main/inspect_pc[22]`、`[23]`。同根格式，不通过任意prefix替换强造命中。
- 06:01:53原report→gate→source_inputs哈希链全部核过，唯一4096模型为/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP4096X16/verilog/RAMSP4096X16.v，实际SHA `3d1cf053be4cf15573ab8c6197e2ec713be73394d736781e1d9828341bda451d`；原gate ced包runs/systolic_b_v3_drc06_gate02/systolic_b_gate，source_inputsSHA `9034e034d403f814fa87ee70ef0ffc55ff64c32c5433b89fdb2ff43292b11c41`。后续读取使用原引用链动态核对，不手抄更换身份。
- 06:04:26实际库固定5d236…中函数：BUFV2RD Z=I；NOR2BV2 ZN=(!((!A1)|B1))；NOR2V2 ZN=(!(A1|A2))。仅局部逻辑事实，未知影响未通过。
- 06:05:40模型索引MODEL_PIN_MATCH=true、1768行、47项Q赋值/task。240 failedWrite，258 readWrite，262/265/270/272/275等有Q_int置X，310 shifted_readLatch赋Q。**尚未读取完整条件，不能判断全部write行为或功耗影响**；代理正准备关键分支两屏以内查询。不要输出或同步整个厂商模型。
- requirements代理只读审计归档：现工具可完整保存OPS0f62/BASE9305/旧41b，41b的b0_inventory01/02需显式auxiliary_runs登记；root-level控制probe/retainedZIP/cleanup/lockrecovery不在整包工具范围，须独立辅助归档。未运行归档，原锁活动时不启动。
- n1_rtl代理已结束逐门检查，改做严格timing/drc入口只读审阅；其初步意见是原constraint完整clean时不启动零目标DC审计，timing_audit仅高扇出诊断不授STA。待其具体原报告摘要查询后决定后续必要作业，不放宽验收。
- 唯一batch02仍按05:57记录运行；下次约06:10再查，不高频重复。最后modelindex命令已完成，VNC3 shell空闲，无待Return；FZ关闭。

压缩后先读AGENTS、CONTEXT_HANDOFF、有效N1→N2→D1→D2计划、本检查点与05:30检查点。用户未暂停，仍仅N1；保留B0交付退路，不进入N2。

## 正在运行，禁止重复启动

- 唯一正式作业：新OPS0f62包的`runs/n1_batch100_02/n1_batch`，driver **PID18736**，实际started **2026-11-13T05:36:45.043281**。生产RTL仍9305，固定HEX100完整1200从头重跑。
- **05:57:36.835518**实际读取：state running，completed **176**、failed **0**、checked_outputs与checked_totals各 **4460544**；含20%余量的剩余估计 **7730秒**。最后sample_015_layer_08，cycles28723、host3.395秒；最近两个child41664/41727均exited、wait_completed=true、rc0。只是局部进展，不是全批通过。
- 05:44:08实读原shared owner PID18736/session n1_batch100_02；OWNER_MATCH/SHA_MATCH/TOOL_MATCH均true，SHARED_UPDATES=false、DRIVER_PROC=true。原共享锁仍唯一互斥，频繁child记录在private process_ledger。不要并发启动门级/EDA或自动清锁。
- 新包已通过服务器ZIP/全部807成员/actual runtime identity，9.01MB上传成功。包/manifest哈希及恢复细节见05:30。旧batch01 failed65前缀完整保留，不续写，不挪为02 PASS。

## 当前已完成与缺口

- N1已过本地压力、ASIC14、CPU恢复/竞争；综合初步面积0.9511486879005002mm²、220宏/0锁存、正setup/hold、约束报告无违例。声明条件完整审核与门级/SAIF/功耗仍待。
- 全80mapped乘法14×12、product26、acc32及32实际累加寄存器已查。新有限结构检查：B33最高两位同网、低31位坐标顺序0失败；A33符号复制与SUM33坐标顺序各0失败。正式小JSON/中文N1_MAPPED_TOTAL33_STRUCTURE_*已落盘，仍numeric_function_verified=false。
- 旧B75项与A80项“失败”为要求保留源信号名的解析限制。实际MUX2NV2为反相选择，代表输入来自两个slot_bias寄存器QN；未凭名字推断其库极性或扩大为功能证明。query7高6位符号锥未执行；本轮手工逐门查询停止，下一必要证据为同网表门级14。
- N1自己的完整1200继续运行；下一串行门级14→SAIF12→12功耗及timing/drc正式审阅。`N1_PPA_QUEUE_REVIEW_20261113_0545.md`及ignored短命令已准备但**未执行、未创建自动队列**。SAIF/power必须等待实际新gate/activity SHA。gate/saif/power登记BASE9305兄弟包runtime-evidence；SAIF显式12层，power每次一层。
- 完整100条浮点源仍缺，原异步问题待用户；不以旧误差/单坐标float代替，不进入N2。
- 所有private/tmp运行结果最终需持久归档，不能以临时盘作为交付完成。

## B0功耗审阅与哈希纠正

- B0原功耗仍69.8371mW/14.2013µJ布局前估算，system_power_verified=false。全12未知清单/L01控制probe已完成，不重复扫活动。
- **原B0报告正确SHA（已机器比对通过）**：`677a1ae11042ffe6aab98fb1b0f124b29f604e6dc0d9bb29e96d9f04f4f6a81a`。
- 为防再次转录，8组为：`677a1ae1 / 1042ffe6 / aab98fb1 / b0f124b2 / 9f604e6d / c0d9bb29 / e96d9f04 / f4f6a81a`。05:55:16 `b0_report_join_proof_pass_0556.png`实际HASH_MATCH True True64、DIFF[]、CASE_COUNT12；inventory pin=实际报告。旧v1/v2/v3失败是手抄字符错误，原文件没有改变；不要继续使用旧677…aab981…或末组f4f68a1a。
- 同次实读L01isolated proof SHA `d894ec7e5f9c3b33e6c99a800cd24df6fd66ba68882f63ffac15784849c4a445`，count/names/unique均1253。05:56:18完整unknown gzip SHA8a579a…核通过，41406总行、2234local行且2234唯一，无重复。这两个范围的精确交集尚未运行；代理新`b0_unknown_no_load_overlap_query_v4.txt`准备好，旧失败查询保留。
- 新`b0_shared_model_identity_query_v4.txt`也准备好，未执行。先从原门级source_inputs锁定真实4096宏模型，再查Q写入行为；不猜输出保持或把X功耗记零。
- B0共享控制frontier实际6驱动已读：INV n793→n792、INV n13→n1082、NOR2BV2(n15,n14)→n11、BUF n9→n779/n780、NOR2V2(read_pending,n11)→n9。实际门函数查询已准备未执行。read_pending全窗0仅引用既有probe，macro控制已知性有限证据不代表完整未知影响关闭。

## 清理、同步与桌面

- R4L01批准归档已03:10完成；8个旧输入ZIP05:25按完整copy/hash/fuser核验后删除重复源件，共133216003B，本地及private保留副本。不重复任何清理；原结果/波形未在8ZIP步骤删除。
- 最新已核云端0f62e41207909904efd544992013c1244b0fd63b；当前恢复、结构、清理、B0纠正小证据准备同步。冻结硬件和运行包不因文档提交改变。
- VNC18874436/workspace3，cwd仍shared原BASE，FileZilla已关闭，workspace4未使用。最后命令monitor已完成，截图n1_monitor_0558.png，shell空闲，无待Return或helper execsession。所有实际状态附时间，恢复后不能把此处当实时。
- root唯一远端操作者；requirements代理后续PPA准备已完成；n1_rtl审计结束；n2_d1代理只做B0审阅/文档。长type必须poll完成再Return。所有新正式启动先查原state/lock/进程/空间，不能重复启动。
