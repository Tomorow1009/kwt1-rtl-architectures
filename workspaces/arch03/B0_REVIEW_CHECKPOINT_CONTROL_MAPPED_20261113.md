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

根代理已收到两条<1000字符、`python3 -B -c`的只读mapped查询；均先校原网表SHA，不打开SAIF。第一条已04:24:49完成，第二条尚待根实际执行，N1批量优先：

1. 全部64宏按完整五类控制pin表达式分组。
2. 全部64adapter移除宏实例后的完整逻辑分组，作为控制锥保守超集；每组打印实例数/完整长度/前1800字符，超出长度只说明截断。

查询源及语法演练仅在ignored `local_runs/b0_mapped_query_syntax_20261113/query1.py`、`query2.py`；Python3.6语法已检查，没有执行服务器路径。本子任务等待根代理实际结果继续解释，不能另开EDA/重扫SAIF。

后续依实际cell/Liberty function及64实例覆盖，解释宏控制的确定性连接；bank_q缺名追实际cell，而非把缺名当0。无论接线如何，未解析n*/T*、局部无引用2234条的全局连接、真实有负载未知的模型影响仍是独立待办。L01局部结果不自动继承其余11层。

## 文件所有权及限制

本子任务只更新自有B0说明/只读工具；正式工具均已冻结。当前新增实际说明在`B0_SELECTED_CONTROL_PROBE_20261113.md`，总体闭环在`B0_UNKNOWN_TOOL_AND_CLOSURE_20261113.md`。根代理持有root handoff/server/package，其他代理持有N1硬件/报告，不覆盖。

根04:10观察共享盘仅1MiB可用；控制回执仍保留private/tmp，不强行回存。正式后续空间和队列身份以根新的实际观察为准。归档02早已完成，不能重启或再清R4/B0；原共享锁不能删，N1旧综合不能重复启动。
