# B0未知活动审查子任务恢复点

当前范围：N1阶段内补齐B0功耗基准证据。先读根`CONTEXT_HANDOFF.md`及最新N1检查点、`IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`。本子任务不操作VNC/服务器，不改RTL，不实施N2。根代理控制所有实际作业；N1最新状态以根实际观察为准，不能重启历史作业。

本子任务最近已重读根`CONTEXT_CHECKPOINT_20261113_0530_N1.md`：根05:30记录8个旧输入ZIP的重复上传件已在完整保留/核验后删除，新0f62包已FTP上传成功，但当时仍待服务器解包/runtime核验、尚无batch02。这条根回执优先于本文05:10上传失败/清理待办的历史描述。此后实时进程、锁及启动状态仍只由根查询；本子任务没有远端操作。

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

**05:10之后增量：**根已完成0f62e41207909904efd544992013c1244b0fd63b的新OPS打包，本段为包完成后的文档增量，不改该包。05:09:13实际unknown gzip查询已亲读，原SHA/41406行相等，N5..N9/read_pending全不在未知清单；不证明原SAIF存在这些新名或其T0/T1，read_pending全0仍来自558控制probe。后续两条ASCII只读命令已保存ignored takeover_local，尚未执行：

- `b0_shared_control_drivers_query.txt`，803字符/805B，SHA `0e1a3c180cec8f3fbcb2921c4f1d3dd5ef9b435b12833bbf8d95d77ec19b7cd3`。按原网表SHA追小写n9/read_pending-D n1082/reset n792驱动及n9消费者，前10项截断显式保留；与bankQ的大写N9不同。
- `b0_shared_model_identity_query.txt`，709字符/711B，SHA `a9ce2d2cb77d427fc450f1fd4a0d8a181d378b1cb125e1bf4d3cfabd31c3379c`。原report显式SHA→gate summary→source_inputs逐层核验，仅列4096厂商模型.v路径/SHA；尚未读取模型正文，不能按behavioral推断写时Q行为。

原已执行bank查询文件为`b0_bank_knownness_query.txt`，712字符/714B，SHA `9701cbc0f5f64024c1abada7c95f3c6204c9d8db1d586a44a01f0488e8b6063c`。三条均ASCII、POSIX shlex四项、Python3.6语法和长度核验，所有源哈希64位；没有新EDA或正式工具修改。

根新检查点已确认自身陈旧锁04:52核验释放，新OPS上传05:08因共享盘满FTP553失败、服务器无新ZIP；不能启动batch02。8个旧非R4/B0重复输入ZIP正在根/另一代理核验保留后清理，本文不操作、不认定已完成。原batch01仍只有65个正式PASS。最新状态读根05:10检查点，不沿用本页更早“锁未释放”描述。

**05:21消费锥可读部分：**亲读`vnc_after_minimize_0525.png`实际钟05:21:23。小写n9引用共3：两个BUFV2RD_12TR40 U392/U394分别输出n779/n780，以及NOR2V2_12TR40 U398由read_pending/n11输出n9。原query的其余driver结果没有被可读截图保留，不能补猜；BUF/NOR function未查。新的ignored `b0_shared_control_frontier_query.txt`只打印6个精确节点实际驱动，722字符/724B，SHA `026e8085bc8dcab43af3532c4697c5beab1179c22ac26d3f4072b530ee51655d`，ASCII/shlex/Python3.6 PASS，尚未远端执行。root优先旧重复ZIP保留清理和新OPS上传，不启动额外EDA。本子任务继续只读，不因等待而结束；尚未完整解释shared/AON有负载未知，不新增N2。

另有一个不需新PT的候选小文件查询已准备、尚未运行：原report的L01 power.isolated_defaults包含已取得direct/leaf均0证明的1253个精确名称，可与当前2234局部无引用未知取精确交集；不预设交集数量，未命中仍待审。ignored `b0_unknown_no_load_overlap_query.txt`995字符/997B，SHA `a1cead8e785f5a83d0f44d9573cd978dbac0d2b4fed78aa3f9aa6464affe4481`，校原report677a…、gzip8a57…、已核proof d894…及41406/2234/1253计数，仅读现成小文件。ASCII/shlex/Python3.6及三条64hex通过；没有新增正式工具或EDA。

**05:40–05:43增量优先于上述未执行描述：**frontier实际05:40:46完成、6个driver全部可读，已亲读`b0_frontier_result_0541.png`：INV2 U39 n793→n792；INV2 U73 n13→n1082；NOR2BV2 U227 A1=n15/B1=n14/ZN=n11；两个BUFV2RD n9→n779/n780；NOR2V2 U398 read_pending/n11→n9。只有INV2实际function此前已读；NOR2B/NOR2/BUF真实函数未读取，不能按名字推导。

no-load overlap05:41:36及macro identity05:42:26均在某条assert停止，未产生交集/模型候选结果。原一行含多个assert，暂未定位失败分支；不能猜是报告变更、抄写或声明去重，也不能改期望SHA以通过。已亲读两张失败图及原`b0_report_exact_sha.png`，准备新的带TAG诊断：

- `b0_report_proof_identity_diagnostic.txt`937字符/939B，SHA `c706dd4795fe830c07cbcb6cc6f73476440eec35531504b58ba2e9cd247f1f64`。先打印报告路径末段、inventory pin、实际报告SHA和8字符分组，再严格assert原677a；通过后打印proofSHA/条数/唯一名数，再assert原d894/1253。
- `b0_no_load_unknown_diagnostic.txt`780字符/782B，SHA `51d12a6698bc69297f6a334c516589121e4c070bf38dc348d6736a7bfbb55429`。先打印gzipSHA再严格assert原8a57，统计41406总声明、2234局部声明、去重名称和重复例；不把声明数自动当唯一名数。

这两条尚待根实际读取，ASCII/shlex/Python3.6/64hex已核。失败不授予任何新功耗批准；原SHA不变，原B0文件未修改，无新EDA/SAIF扫描。本子任务仍只做只读证据审查。

**05:46纠错尝试仍失败（以下05:50分行核对为准）：**当时已确认inventory pin与实际报告相同，但长行后半仍误读，导致新_v2也在首assert失败。原_v1/_v2命令及截图均保留；没有报告变更，也没有产生交集或模型批准。此前通知的_v2手抄值作废，根证据JSON需以分行实证值更正。

已废弃的_v2查询身份保留：`b0_report_proof_identity_diagnostic_v2.txt`937字符/939B/SHA `0bbd724f88d6f13be671dacb40b2ebee947854adaeeaae3197dc6b6092ac9d21`；`b0_shared_model_identity_query_v2.txt`709/711B/SHA `bec361b36e6dcaf896ef44df521e5e61c13d8f0df50a4e604876bf64d11607f1`；`b0_unknown_no_load_overlap_query_v2.txt`995/997B/SHA `bf3646178afe040ed99f78c1dca3d489152cf09865e990f2911572e54a7371a3`。它们含错误手抄值，禁止再执行。原unknown diagnostic只绑定正确gzipSHA，无需改。

**05:50–05:55纠错历史：**_v3最后一组仍误读，05:54实际DIFF指出offset60/61的a8被抄成8a；_v1/_v2/_v3均保留并禁止再执行。05:55:16修最后组后取得HASH_MATCH=True/True、DIFF=[]、长度64，原inventory pin与实际报告一致。最终正确八组如下，按`''.join(groups)`生成：

```text
0  677a1ae1
8  1042ffe6
16 aab98fb1
24 b0f124b2
32 9f604e6d
40 c0d9bb29
48 e96d9f04
56 f4f6a81a
```

最终正确值 **`677a1ae11042ffe6aab98fb1b0f124b29f604e6dc0d9bb29e96d9f04f4f6a81a`**，64位、offset40=c、offset60:62=a8。_v1第三组误抄，_v2后半误移，_v3末组对调，失败均保留。GAPS/CLOSURE/SELECTED及新model/overlap_v4已按最终数组join更正；原B0文件/工具不改，不是报告变化。原报告身份已经机器匹配，无需重复核跑。

废弃_v3身份：`b0_report_proof_identity_diagnostic_v3.txt` SHA `f44c62abb0ffc7bdb62900b3b5f313f7088d86cbf16040a33f7e7bf82cb0ceda`；model_v3 SHA `b2f8454afe4e4b005113c70f3b8063f3222a628200bcb43dc7a3baae2852f260`；overlap_v3 SHA `6bac1513b59722651c55915da8fc1601de4294aa7bceb5d3d71ca0791335b519`。仅作为失败记录，不再执行。

05:55–05:56实际诊断已亲读：CASE_COUNT12；proof SHA d894ec7e5f9c3b33e6c99a800cd24df6fd66ba68882f63ffac15784849c4a445，declared/rows/unique均1253；原gzip SHA8a579…匹配，TOTAL_ROWS41406、LOCAL_ROWS2234、LOCAL_UNIQUE2234、DUPLICATE_ROWS0、DUP_EXAMPLES[]。因此原overlap并无重复名称问题；此前只因错误报告常量停在首assert。

可执行的新_v4仅两份：`b0_shared_model_identity_query_v4.txt`709字符/711B/SHA `3cc96f6c8dac04a5d517ed483ea896e2f0b3aa17f3039c1164110f9337e6ac4a`；`b0_unknown_no_load_overlap_query_v4.txt`995/997B/SHA `3059414bafa59a1df685a40f60171ae3fc29918fc31ce936e022042c4d6a6924`。ASCII/shlex/Python3.6通过，所有其它断言不变，尚无实际交集或模型结果。root准备06:00同步，本子任务至此停止tracked文件编辑，后续新结果另次提交。

后续依实际cell/Liberty function及64实例覆盖，解释宏控制的确定性连接；bank_q缺名追实际cell，而非把缺名当0。无论接线如何，未解析n*/T*、局部无引用2234条的全局连接、真实有负载未知的模型影响仍是独立待办。L01局部结果不自动继承其余11层。

## 文件所有权及限制

本子任务只更新自有B0说明/只读工具；正式工具均已冻结。当前新增实际说明在`B0_SELECTED_CONTROL_PROBE_20261113.md`，总体闭环在`B0_UNKNOWN_TOOL_AND_CLOSURE_20261113.md`。根代理持有root handoff/server/package，其他代理持有N1硬件/报告，不覆盖。

根04:46消息优先于04:34：batch01于04:41:07更新共享owner.tmp时ENOSPC失败，成功前缀65任务/1647360个total、result、sat，不能称1200通过。原锁记录自身driver275224、lastchild287728；RELATED ps为空，但根仍须exact PID及task66核对，不能直接清锁。requirements代理只修N1工具的ProcessLedger，共享owner一次写、后续private ledger及Popen异常wait；RTL不变。本子任务不操作锁/进程，B0 query2/3仍待根执行。

根04:47:38已再核：exact driver275224和child287728均不存在，相关session进程为空；task66日志记录04:41:10的$finish/VCS退出。自身owner仅350B、SHA d97bf037dfd2499137292f6f13e37dfbc4586e99374ee7845efa398bec51fa9d，身份为自己的OPS/session。根拟先保存owner/state/ps/日志尾证据，再在原路径非symlink、owner身份/内容未变且目录仅此文件的前提下，只删除已核owner并rmdir空目录。本子任务已只读审查该边界，未操作远端；**实际释放是否完成仍须根回执，不在此推定**。task66退出不补算正式通过。

此前04:34共享945MB/private约750GB、04:10共享仅1MiB均是历史瞬时观察，后续空间以根新值为准。控制回执仍保留private/tmp，不强行回存。归档02早已完成，不能重启或再清R4/B0；保留失败批次，不重复启动旧综合或未经核对的批量。
