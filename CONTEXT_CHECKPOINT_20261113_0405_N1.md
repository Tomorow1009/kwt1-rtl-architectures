# N1持续执行检查点（2026-11-13 04:05）

## 04:10重要增量

- 原综合04:10:03仍running169157/174746，无新验收结果。共享盘仅1048576B可用，不能复制控制小回执或启动共享盘输出；私有/tmp结果保留。不要重复已关闭的旧VCD/csrc清理路径，不删除B0/R4备份。正式下一作业仍须原共享锁；实际锁写入是否有空间必须重新核。
- 控制补查254486已结束，04:04:54 summary存在/failure不存在：558条selected、unknown0、COND0、duplicate0。1280个宏引脚全缺失；adapter缺wenable64，shared顶层缺fire/mapped/bank_q[0..4]共7，AON缺io_in_0_valid/ready、Queue_1_io_enq_valid/ready及Queue_1_io_deq_valid共5。不能把已选558无未知扩大为宏控制已验。
- 控制summary570051B，request5196B，均仍在private root/b0_control_l01_20261113_0403。正确summary SHA为`2c06372156a5f80e50e6c0634002f6686dc1768966d65bde32cc7a51b0060f7d`，04:10实际assert已通过。先前把首8位抄成e206/2e06的两次查询assert失败，未改任何文件/未重跑扫描；错误串不得使用。
- actual shared read_pending在全208926.645774ns为0、TC0；cmd_ready全1、TC0；cmd_read有T1=65753326758ticks/TC13286，不能说cmd_read恒0。bank_q未记录，仍需实际mapped声明/连接证据。宏无SAIF记录可先由实际adapter到macro pin表达式追溯，缺wenable不自动解释为常量。
- n2_d1代理正在给最小只读mapped查询，工具保持冻结；源网表路径取原unknown summary.netlist，先校SHA，不猜reference/实例名，不新EDA或活动赋值。
- VNC3空闲shared9305cwd，最后身份/空间查询已执行；FileZilla关闭，无待命令。最后截图n1_control_identity_space_0411.png的钟为04:10:09。

恢复先读AGENTS、CONTEXT_HANDOFF、当前IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113及本检查点，再读03:32检查点中的03:55增量。用户没有暂停，要求持续推进。仅N1，未完成全部验收不得进入N2。

## 冻结与已完成

- 生产硬件仍9305c6948c764fed01fe86b20bb3db94170299ab。ASIC14/354816输出、恢复/76032、CPU竞争/50688均通过。固定12平均29711周期、150MHz折算5048.6351856 task/s。自己的1200/PPA/门级/功耗/100完整float未验；不借B0 PASS。
- 最新GitHub提交3165fb3cab281d744e5f61161972ba13e7046e66已push及ls-remote核对。它新增审核工具/文档，不改变受测RTL。
- R4 L01授权归档已完成，raw重复已在全解压哈希/字节一致及无占用后删除，共享gzip6.987GB保留，净省5.608GB；不要重复归档或resume。详见R4_L01_STAGED_ARCHIVE_20261113.json。
- B0完整12层原SAIF未知清单完成：单L01及其余11两次输出身份完全一致，case并集恰12；unknown合计496471（含别名），全未知各层18620，COND均0；gzip合计15791726B。只完成清单，不是未知功耗影响PASS。具体SHA与逐层数见B0_UNKNOWN_INVENTORY_PROGRESS_20261113.json。
- 新100原始float缺口仍在。新只读排查已确认本地旧600全validation，而目标training83/testing13/validation4；即使W/b相同也至少缺96条X/Y，不能混用。记录docs/data/x14-w12-b32/N1_FLOAT_SOURCE_SEARCH_20261113.md。原ZIP预期edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9，异步问题待用户，勿重复搜索/替代。

## 当前真实作业

1. N1原综合PID169157/DC174746，BASE/runs/n1_synth01。最后03:56:45仍running，无summary/mapped/metrics/constraints。03:52 CPU99.7%、RSS约25GB，日志进入优化表格；不是挂死或可重启依据。原团队锁由169157持有。不要启动第二个综合或并行正式EDA。
2. 新B0 L01控制驻留补查PID254486，04:03:13启动，低优先级nice10，不是EDA/仿真。输出：`/tmp/s4_21usr_n1_20261113_0210/b0_control_l01_20261113_0403`。driver在下述controlops/control_l01.driver.log。只读取原L01 SAIF一次，全部原native统计/哈希/窗口须一致；缺失宏引脚不得当已知。启动后尚未读取终态，禁止重复启动。

共享project为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`。原团队锁在它的父目录`Desktop/IC/.arch02_team_lock`，不能改为私有锁。

## 私有运行根与工具

根：`/tmp/s4_21usr_n1_20261113_0210`，s4_21usr/0700/独立文件系统，最终需归档回持久盘。

- BASE=`light-light126-n1-v4-20261113_013211-9305c6948c76`；manifest73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d。
- OPS=`light-light126-n1-v4-20261113_022722-41b0846ce719`；manifest0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e。源码/主固件/数据同BASE；旧恢复测试仍绑定旧sequence ELF，不宣称新ELF已执行。
- reviewops=`light-light126-n1-reviewops-20261113_0313-1f86fc70d41e`已部署，完整unknown工具c57ed783...，两批扫描均结束，不再重复。
- archiveops=`light-light126-n1-archiveops-20261113_033430-0f3a46d3f3fb`已03:40部署/哈希通过，工具6bfd21fbf42dbce160829f99c8eff2d3075c75857f2ccbe74fec67e141de09f9，21本地检查及独立复核通过。真正归档未启动，必须全部登记源终态/锁空闲/无打开使用；不删/tmp。两个B0inventory辅助回执SHA见03:55增量。
- **controlops=`light-light126-n1-controlops-20261113_035653-3165fb3cab28`**已04:01:31独立解包，04:02:21核5个实际OPS依赖及manifest全部匹配。ZIP7797B SHA cbe60db67006c4132f69ba75fad3446f2c6997f09ce775103fe693e98ee976cf；manifest319c6d8c6b1e65db99942951ea2938039e94dc1cc12a93c57d2cac35c60de73e；工具b1c6df556c7df0f2b8e13c1be6c2ba8babb4b994f50c2d99b5f78af24d7bc963。9本地fixture/Python3.6/独立审查通过，旧290e版本不用。实际运行PYTHONPATH=OPS/workspaces/arch03/scripts，python3 -B。

## 后继动作及边界

- 先读控制补查summary/failure、missing/duplicate/COND/unknown，再取shared cmd_read/read_pending/bank_q与宏/adapter/AON控制驻留。累计SAIF不能证明联合时序；全未知TC0/未消费/模块名均不能自动豁免。B069.8371mW/14.2013uJ仍布局前估算，system_power_verified=false。
- 原综合结束后核state/summary/实际锁，检查220宏、80PE数值映射、面积<=1.2、全DRC/setup/hold/无锁存与组合环。不要套B0旧U编号，不能仅看正slack。
- 锁释放后优先自己的batch100一次编译1200任务：OPS n1_server.py batch --session n1_batch100_01 --dataset /storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all，加runtime-root及OPS manifest。首1/12作同批前缀观察，不另起重复小批。末尾重审全部30412800个total/result/sat。以实测宿主耗时加20%预算，不只用单例仿真秒数。
- 后续同网表门级14无SDF、12完整SAIF/PPA及精度/报告缺项继续补。SAIF方法资格已核既有R4crosscheck02，不用恢复R4大VCD。
- 03:52共享free3665821696B，04:02私有/tmp754415706112B。旧六批VCD及gateprobe已删、csrc小缓存已核无价值，不重复清理或计入回收。新小分析输出在/tmp，完成后若有空间可复制完整小回执至shared新目录核SHA，不能丢弃唯一临时证据。

VNC18874436/workspace3，当前空闲shell仍shared9305cwd；FileZilla上传成功后已关闭，workspace4未用。最后控制启动命令已执行，无待Return或本地exec session。只用现有F:/linux_fpga_try/ac820.ps1控制板端Linux VNC/FileZilla，不建立新服务器通道。
