# N1后续队列只读审阅

当前`n1_batch100_02`已启动，后续工作不得并发抢占共享EDA锁。本文件仅核对现有入口、
参数和证据依赖，没有创建服务器会话、自动队列或启动新作业；不进入N2。

## 身份与待核条件

操作包为0f62新OPS，manifest `1c55d5515de4258c77537e52387809ea04a33a334a4fefee8e2600ec2b7209e0`。
受测综合仍为9305 BASE，manifest `73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d`。
原综合summary SHA为`cc7f26115f3158fb69f4575f28b5dfde4dd8e5b3aeefda2a927928ad8418db31`。
两包都是`/tmp/s4_21usr_n1_20261113_0210`下直接子包。

凡gate、saif、power需追溯BASE综合网表，均应在新OPS的`--runtime-root`及自身
`--runtime-manifest-sha256`之外，显式登记`--runtime-evidence <BASE包> <BASE manifest SHA>`。
新OPS的后续run在本包内，不需要把自身再次登记为evidence。不能只给synth-run而省略兄弟包身份。
gate实际`verify_synthesis`仍会复核原summary/state、网表/SDC/源码准备清单及原始输入哈希；
只有准备清单与实际硬件完全相同才能复用原综合，不因是新工具包就跳过这些校验。

## 参数与顺序

| 项目 | 入口要求 | 通过范围 |
|---|---|---|
| 当前batch | 固定100条/1200任务，终态后独立重审 | ASIC RTL整数total33/result/sat；不是浮点、门级或功耗 |
| 固定ASIC14、恢复/竞争 | 各自独立已通过回执；不能用1200替代定向项 | 固定性能/边界及协议行为 |
| 门级14 | `stage=gate`；显式synth-run/summary SHA；默认cases正是extremes、rounding、12层 | 无SDF的实际mapped结果/饱和；内部total不可观察 |
| 完整SAIF12 | `stage=saif`；显式gate-run/SHA和方法qualification-run/SHA；**必须显式cases为layer_01至layer_12，保持顺序** | 回放同网表/固件，输出/窗口/IRQ和原门级一致；不是系统功耗审核 |
| 功耗12 | `stage=power`；显式saif-activity-run/SHA；**每次cases只指定一层**，独立session串行12次 | 完整窗口布局前功耗数字；仍须未知活动/模型影响审阅 |
| 汇总与选择 | 固定14、1200、综合/严格时序、门级、活动、12功耗及同批浮点精度分别绑定 | 缺证据为pending/null，不能借B0数值或自动进入N2 |

SAIF入口默认继承的14个cases不符合`n1_saif.verify`所需12层，直接沿默认会明确拒绝；
power默认14例也会被入口拒绝。这是参数使用要求，不是需要放宽的校验。
SAIF首次使用R4首例实际体积做预算，之后逐例重估；必须保留20%余量和2GiB。

## 既有SAIF方法证明

当前项目STATUS记录：ced包`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`的
`runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck`已完成原生SAIF/VCD方法交叉核验，
summary SHA `a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26`。
整机与主要模块差异均≤1%。启动N1 SAIF前仍须实读该run的state、summary和全部artifacts哈希；
这里只读取了本地索引，没有宣称当前服务器该目录完整可用。

该证明只允许复用采集方法，不转移R4/B0活动或功耗到N1。N1的门级输出只检查实际四列，
不能用参考文件补造total33第五列；total的完整证据由新ASIC RTL批次提供。
功耗用12窗口时间加权平均与总能耗/12，保持SS、0.99V、125°C、6.666666ns，220宏。
报表生成和数值合格仍不等同未知活动、官方面积归属或物理签核通过。

## 本地短命令准备

`local_runs/n1_pending_ppa_20261113_0545`已准备gate14、timing_audit、drc_audit三个独立
启动命令，分别852、860、854字符。均固定新OPS/BASE manifest与原synth summary SHA，
日志独占创建，已有同名session即拒绝；通过Python3.6语法检查，未执行。
文件名带`DO_NOT_RUN_WHILE_BATCH_ACTIVE`，只是供根代理后续审阅，不是已提交队列。

必须先观察当前批次终态、确认全部子进程已退出及原协作锁空闲，再复查实时空间，
由根代理选择一个工作启动。若旧锁仍存在，不可从该命令绕过或删除。
SAIF/power启动还需实际生成并审查的新gate/activity summary SHA，当前未伪造或用占位值冻结。
