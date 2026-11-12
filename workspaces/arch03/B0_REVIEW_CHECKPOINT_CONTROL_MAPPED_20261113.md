# B0未知活动审查子任务恢复点

当前范围：N1阶段内补齐B0功耗基准证据。先读根`CONTEXT_HANDOFF.md`及最新N1检查点、`IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`。本子任务不操作VNC/服务器，不改RTL，不实施N2。根代理控制所有实际作业；N1最新状态以根实际观察为准，不能重启历史作业。

## 完成与冻结

- 原B0报告完整12层功耗已经存在，准确加权69.8370733610964mW、14.20128985110165µJ/task；未知影响尚未批准，不能称没有功耗或已经系统功耗验收。
- 完整12层现成SAIF未知清单已由根代理分两批完成，496471条（含别名），每层18620条全窗口未知，COND均0。共同report/netlist/activity/tool身份及case并集已核，见`handoff/team/evidence/B0_UNKNOWN_INVENTORY_PROGRESS_20261113.json`。
- `b0_saif_unknown_inventory.py`冻结SHA `c57ed783754a6411bc3d43139dcf90a420d7c5a2f87ca050b12b98e75b20056d`，15本地检查/独立审查通过，实际两批完成，禁止再重复。
- `b0_saif_control_probe.py`冻结SHA `b1c6df556c7df0f2b8e13c1be6c2ba8babb4b994f50c2d99b5f78af24d7bc963`；test SHA `0c0c3b2439483dcfeca007d42532f0b16a80f1d66b6ce1721b5c538e75b1044a`。9本地fixtures/Python3.6/独立审查通过。宏WEN及adapter mask也逐项列missing；旧290e候选不用。
- 实际控制probe唯一254486已完成，输出`/tmp/s4_21usr_n1_20261113_0210/b0_control_l01_20261113_0403`；summary570051B，准确SHA **2c06372156a5f80e50e6c0634002f6686dc1768966d65bde32cc7a51b0060f7d**。旧e206/2e06手抄串错误，不能使用；对应assert失败只读查询未改文件。
- 558条selected unknown0/COND0/duplicate0；缺macro全部1280pin、adapter wenable64、shared fire/mapped/bank_q[0:4]、AON五个valid/ready名。不能将558已知转为全部macro控制已验。

## 实际证据与尚待解释

- L01完整窗口208926.645774ns，单位1fs；committed_data32各未知14.666652ns，valid/ready已知。未知时间位置/联合关系尚未证明。
- L01 shared read_pending恒0，cmd_ready恒1，clk正常翻转、rst_n恒1；cmd_read有65753326758 ticks为1且TC13286，不是恒0。不能由cmd_read边际值推导有效读。
- 本地确认shared/router两份RTL与B0生产63da的git diff为空。router无条件将同一cmd_read送mem和src，仅对各自cmd_valid按目的地限定；这是shared cmd_read可在无效/源访问周期翻转的明确源关系，不是有效shared读计数或mapped读状态证明。
- shared全未知为32bank×32bit的bank_data加160个N*组合节点。AON包含T_*、n*、Queue_1 index/mask和io_in_0载荷等，不能按名字豁免；SYNOPSYS_UNCONNECTED显示过滤也未作电气豁免。
- 04:12实际网表SHA匹配，shared ref为`arch03_shared_sram_turnover`、有64适配子模块。bank_q原名无网声明或直接assign；这不是常量0证明，需看寄存器实例/选择锥。
- 04:18实际单例`banks[0].high.memory`、adapter ref `_62`：CLK=clk、CEN=n2、GWEN=n8、RET1N=1'b1、WEN高8=n6/低8=n7。目前只是一个实例，不能推广全部64或猜库逻辑极性。
- 04:24:49根已完成全部64macro表达式分组，本代理亲读`b0_macro_groups_0425.png`：63个沿用上式，1个GWEN=n3、WEN高8=n5/低8=n4；其余CEN=n2、CLK=clk、RET1N=1'b1相同。网名差异不等于功能差异。全部64的常量RET1N和直连已知adapter clk已有明确依据；其余控制仍需逻辑/function，不提升整体功耗状态。

## 正在推进的最小动作

根代理已收到两条<1000字符、`python3 -B -c`的只读mapped查询；均先校原网表SHA，不打开SAIF。第一条已04:24:49完成，第二条已04:50:08完成：

1. 全部64宏按完整五类控制pin表达式分组。
2. 全部64adapter移除宏实例后的完整逻辑分组，作为控制锥保守超集；每组打印实例数/完整长度/前1800字符，超出长度只说明截断。

查询源及语法演练仅在ignored `local_runs/b0_mapped_query_syntax_20261113/query1.py`、`query2.py`；Python3.6语法已检查，没有执行服务器路径。本子任务等待根代理实际结果继续解释，不能另开EDA/重扫SAIF。

04:50:08第二条实际结果已亲读：adapter逻辑33/30/1三组，均226字符全文，只有INV2_12TR40、NAND2CV2_12TR40，共五个门。不能凭名字决定逻辑极性；下一步是实际标准Liberty的function补读。

根已要求的完整ASCII命令另存于`E:/fpga_race-two/takeover_local/b0_adapter_logic_query.txt`（895字符，文件SHA928627cf13402bdcda9849a476d0cde8ada675219d3dcbe09797e01cda432188）及`b0_bank_state_query.txt`（880字符，文件SHA804f58768533e763fd70b14e0d3577cb09efe1a0aa053cb3a34cd6e1114a57f7）。均含完整`python3 -B -c`，ASCII/POSIX shlex四项/单行/原代码逐字一致/Python3.6语法已核。query3追shared中所有bank_q/read_pending的实际cell/assign语句，先打印总数，再最多八项；该第三条尚无实际结果，不写成已执行。

实际Liberty下一查询已存`E:/fpga_race-two/takeover_local/b0_adapter_liberty_query.txt`（970字符、971B，SHA f66a5994b64396bb40228e14fdc092ab68e83fdce33eac68cd9d81d9cbaefbd6）。从原summary.link_report.library_inputs按固定stdlib SHA 5d236b15…唯一取原.lib，限256MiB/完整SHA核验，输出两种实际cell的pin/direction/function；仅语法及合成字段提取已核，尚未服务器运行。无新EDA。

**04:57增量优先于上段待执行描述：** query3实际04:55:19完成，本代理亲读截图。5个bank_q_reg仍为DRNQV2_12TR40，Q[4:0]映射为N9..N5，D=n72..n76，CKclk/RDNn792；read_pending_reg同类D=n1082/Q=read_pending/CKclk/RDNn792。原网名缺失是改名，不是寄存器不存在/常量。04:56:35实际Liberty查询完成，完整5d236b15…SHA相等；INV2实际function `(!I)`、NAND2CV2实际`(!(A1&A2))`。结合64适配器完整五门逻辑，全部宏CEN=!cs、GWEN=!(cs&we)、WEN高8=!(mask1&cs&we)、低8=!(mask0&cs&we)，CLK直连clk、RET1N常量1。原L01控制probe全部64的clk/cs/we/mask已记录且unknown0，故可按实际组合锥证明这些控制输入在L01已知；不能说leaf SAIF direct mapping或整体未知影响通过，也不继承另11层控制驻留。

当前文档已保存该实际范围；根准备commit/package，本子任务随后停止文件编辑，仍继续只读分析/消息。下一最小查询从现成L01未知gzip精确查shared/N5..N9，不在未知清单中的信号不能据此还原T0/T1。实际read mux消费和AON未知锥仍待补证，原SAIF不重扫。

后续依实际cell/Liberty function及64实例覆盖，解释宏控制的确定性连接；bank_q缺名追实际cell，而非把缺名当0。无论接线如何，未解析n*/T*、局部无引用2234条的全局连接、真实有负载未知的模型影响仍是独立待办。L01局部结果不自动继承其余11层。

## 文件所有权及限制

本子任务只更新自有B0说明/只读工具；正式工具均已冻结。当前新增实际说明在`B0_SELECTED_CONTROL_PROBE_20261113.md`，总体闭环在`B0_UNKNOWN_TOOL_AND_CLOSURE_20261113.md`。根代理持有root handoff/server/package，其他代理持有N1硬件/报告，不覆盖。

根04:46消息优先于04:34：batch01于04:41:07更新共享owner.tmp时ENOSPC失败，成功前缀65任务/1647360个total、result、sat，不能称1200通过。原锁记录自身driver275224、lastchild287728；RELATED ps为空，但根仍须exact PID及task66核对，不能直接清锁。requirements代理只修N1工具的ProcessLedger，共享owner一次写、后续private ledger及Popen异常wait；RTL不变。本子任务不操作锁/进程，B0 query2/3仍待根执行。

根04:47:38已再核：exact driver275224和child287728均不存在，相关session进程为空；task66日志记录04:41:10的$finish/VCS退出。自身owner仅350B、SHA d97bf037dfd2499137292f6f13e37dfbc4586e99374ee7845efa398bec51fa9d，身份为自己的OPS/session。根拟先保存owner/state/ps/日志尾证据，再在原路径非symlink、owner身份/内容未变且目录仅此文件的前提下，只删除已核owner并rmdir空目录。本子任务已只读审查该边界，未操作远端；**实际释放是否完成仍须根回执，不在此推定**。task66退出不补算正式通过。

此前04:34共享945MB/private约750GB、04:10共享仅1MiB均是历史瞬时观察，后续空间以根新值为准。控制回执仍保留private/tmp，不强行回存。归档02早已完成，不能重启或再清R4/B0；保留失败批次，不重复启动旧综合或未经核对的批量。
