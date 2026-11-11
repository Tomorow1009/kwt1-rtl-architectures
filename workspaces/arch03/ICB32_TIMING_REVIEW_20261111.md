# ICB32 / 16×4 综合时序范围复核

2026-11-11 07:08阶段记录，绑定e65新综合网表，尚未作完整时序审定。旧fcd的审定不转移给本候选。当前setup为+0.0000715256ns、hold为+0.000253469ns；裕量很小，仅用于声明的综合任务模式，不代表布局后时序。

## 已核对的当前工件

- 新综合摘要SHA：`fd36940c164157653d9e4af9233cef436589d1395b2420dea540d03fbb4b4c3d`。
- 工艺SS、0.99V、125°C，HF周期6.666666ns、LF周期66ns；224个SRAM宏、0锁存器，无组合环和约束违例。数值和面积详见[综合证据](../../handoff/team/evidence/ICB32_SYNTH_20261111.json)。
- 原DDC只读查询的三个高扇出对象为`u_e203_subsys_top/core_csr_clk`、`u_e203_subsys_top/hfclk`和`u_e203_subsys_top/u_sirv_aon_top/crossing_clock`，均为原平台时钟网络。查询摘要SHA：`49565632fa09318cd025866883df7dbed1dcfb3e5631ed4030e79011b9647ae1`，见[端口和时钟探测](../../handoff/team/evidence/ICB32_TIMING_PROBE_20261111.json)。
- 再读当前`check_timing.rpt`，最终检查含generated_clocks、loops、no_input_delay、unconstrained_endpoints、pulse_clock_cell_type、no_driving_cell和partial_input_delay；保留TIM-134的三个高扇出及1000扇出建模说明，不把“无约束违例”解释成全部模式签核。

## 新网表结构告警

复用已有解析器的纯`classify`函数，先核对新ICB32综合摘要、实际网表及结构报告SHA，再解析全部2014个映射模块。没有调用绑定旧DMA16范围的旧审计入口，没有启动EDA或修改原网表。

全部11138条LINT-8/LINT-28对象均只有声明、没有逻辑引用：10598个输入和540个输出，无表达式待判对象。独立结果位于964包`runs/icb32_port_review01.json`，SHA为`316ee46a76452e2661d2b0a96e2823ed8373c0341e8797758813190ffec07da3`；07:08:29.726025重新断言结果及输入哈希通过。小型回执见[端口复核证据](../../handoff/team/evidence/ICB32_PORT_REVIEW_20261111.json)。

| 类别 | 当前条数 | 处理状态 |
|---|---:|---|
| LINT-8 / LINT-28 | 706 / 10432 | 全对象已核对为声明之外无逻辑引用 |
| LINT-1 | 4 | 先前已定位debug reset、AON POR和PLIC未消费输出；见综合证据，不是新数据通路缺失驱动 |
| LINT-2 | 706 | 无负载网络；已读到decoder和MAC算术未用位实例，不能把代表样例称为全部对象审定 |
| LINT-32 | 9935 | 子模块引脚接逻辑常量；保留完整原报告 |
| LINT-33 | 1000 | 同一网络连接多个子模块引脚；不是多驱动错误的同义词，仍结合实际连接与无环报告解释 |

## 首层PrimeTime对象与实际SDC

08:54补充：新首层PT已完成，绑定原e65综合和497全部14例门级。独立解析全部189个no_clock对象：186个静态JTAG DTM引脚、3个JTAG复位同步器引脚，CK182、CKN7。全部78973条禁用弧的标志为p14199、C62570、c1997、d207，无user、loop breaking或false-net标志。两个完整表保存在964包`runs/icb32_l01_timing_objects01.json`，哈希及绑定见[首层证据](../../handoff/team/evidence/ICB32_POWER_L01_20261111.json)。未删表内任何对象，也未修改网表。

实际SDC保持TCK/TMS/TDI为0，PLL bypass/div1及bootrom去抖输出为1。只有一条false-path命令，从lfextclk到原计时器u_tim0..3的`r_ls_clk_sync_reg[0]/D`四个首级同步器；无clock groups或multicycle例外。SysMem仍采用HF域1ns/0ns接口预算，不对DMA数据通路设false path。

DC的实际`metrics.txt`周期为6.666666000000ns；`write_sdc`将HF周期/下降沿舍入成6.66667/3.33333ns，PT功耗导入的是该原文件。新增`scripts/icb32_delivery_sdc.py`从摘要及实际metrics绑定原SDC，只恢复6.666666/3.333333并生成新目录和回执，其他约束逐字保留；本地两项精度/拒绝非法时钟检查通过，**尚未服务器执行**。原DC正裕量仍属精确周期证据，不能据此把原PT导入周期写成精确值。

## 后续审阅范围

首层时钟对象、禁用弧和上述模式/例外已核对；继续新12层功耗、最终1200和干净复现，生成精确交付SDC并保留原报告差异。未把LINT-2的代表样例扩大为全对象审定，也不从旧网表复制结论。

现有CPU竞争和恢复、同网表14例门级及12个活动窗口已全部通过；后继ASIC14提供干净目录复现。新功耗已有首层结果，最终1200尚未执行，仍保留未完成标记。后续审定另行绑定实际回执，不修改历史阶段摘要中的原始false字段。物理时钟树、提取寄生、复位释放全过程和活动JTAG模式不在声明的综合任务模式范围内，也不追加为赛题的物理签核要求。
