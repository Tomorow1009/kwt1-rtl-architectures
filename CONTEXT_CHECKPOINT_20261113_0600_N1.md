# N1持续运行检查点（2026-11-13 06:00）

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
