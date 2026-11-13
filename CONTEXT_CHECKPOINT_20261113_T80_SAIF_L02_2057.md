# T80持续采集，L02已通过 — 2026-11-13 20:57

必须重读T80_PRIORITY_COMPLETION_PLAN_20261113.md。G64取消，T64暂停；原8路及所有历史结果保留，当前唯一目标完成T80。不要复活旧计划里的N2/D1/D2、G64或T64队列。

## 当前实况

- t80_finish03持续运行，父183563/SAIF驱动183576，20:53:58.534710实际status=running, stage=t80_saif,error=None；/tmp剩160438259712B。
- L01和L02已通过完整输出/IRQ/WFI/实际首VALID至最终ACK窗口：周期116752/113732，SAIF97722100/97710598字节。L01仿真CPU405.330秒。后续SAIF仍在运行，不能按旧门级50秒/层估时。
- 路径 `/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4/runs/t80_finish03*`；同根ops-cef81d4为队列，request正确Linux SHA `e0009ed15805d221489ac441b2019669d79e506ef7ad0bf54274de1d9b35c888`；bundle manifest `181bb96b719363be5350e9e968ac2b2ad29555e2f4606e362721be3c42629b9b`。自动顺序仍SAIF12→PT12→20条FLOAT关联。不能改运行副本或重启队列。
- **无待完成VNC输入或本地传输进程**。exec84865已完成；20:49:57实读新report ops的8文件manifest与导入预检PASS。路径同根`ops-review-cfbca86`，manifest `f35927b878b4fe32caf77fb63d252939fb8aa9d4eb523eff367f2461af8e3c81`。该工具支持显式runtime路径与T80四段窗口；原d611597版不直接用于新/tmp报告。

## 新审阅事实

- DRC无违例、完整解析。结构端口11319全仅声明；243无负载驱动准确对应声明；80PE/1array/80requant。
- 四个LINT-1实际为原平台debug ndreset_dfflr/fullreset_dfflr、AON u_aon_porrst、PLIC flop_0_irq.plic_irq_prio_dffr，都是未消费输出。LINT32=10741（接逻辑常量），LINT33=1341（同网多输入）。原报告不删。
- 原check_timing报告写4个高扇出；实际DDC threshold1000查询列3条平台时钟：core_csr_clk、hfclk、aon crossing_clock。保留这两个不同统计，不编造第四条。旧N1_FINAL_REVIEW_20261113.md采取同样披露，不能借其PASS。等T80自己的PT检查所有no_clock及禁弧和时钟/IO条件后，再决定稳定任务模式时序验收。不得为此重综合或提前阻塞采集。
- 当前预算上界0.9521382079004799mm²，setup +0.000576019ns/hold +0.00623399ns为T80自身初步结果。最终系统功耗尚未得到。

## 下一步

1. 继续只读检查现有队列，不重复运行ASIC240/门级14/综合。
2. 复用即将生成的每层PT时钟/禁弧/活动覆盖及宏模型报告完成T80审核；旧N1审核方法可参考，结果不得转移。
3. 全部21阶段完成后，用ops-review-cfbca86的transport_report_stage.py（--runtime-root和--runtime-manifest-sha256）导出。PYTHONPATH先ops/scripts，再当前bundle/scripts；asic输入为原delta01的t80_soc01。--unknown-inventory会用显式验证路径访问/tmp活动和原共享盘网表，不需复制网表。
4. 同目录另外3个review脚本可做连接/静态概率/别名审核；根据T80实际报告决定最少必要工作，不能用单层/默认翻转替代12层功耗。
5. 最终归档/tmp证据到持久存储；空间不足不删旧8路。报告/源码/小摘要同步GitHub。

最新已push eb6215d（包括cef81d4修复和cfbca86报告工具）；本20:57更新尚待提交。现有worktree E:/fpga_race-two/kwt1-t80-t64-g64，个人分支codex/light-light126/n1-t80-t64-g64-20261113。
VNC18874436/FZ20972102；恢复先windows，仅workspace3；原终端cwd仍共享盘T80 delta01。只读状态命令takeover_local/t80_finish03_compact_cmd.txt。完整原队列、网表与失败身份见20:33/20:47检查点。
