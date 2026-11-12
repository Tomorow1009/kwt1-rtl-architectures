# B检查点：2026年11月12日19:22

任务ACTIVE。用户最新要求：**先把本版已完成情况同步GitHub，然后继续工作**。继续直接5×16脉动B，A取消，R4保护；生产63da6ba/v3/credits3冻结，不再加RTL/编码功能。有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`，11月13日17:00前收尾。压缩后先读AGENTS、本文件、计划和STATUS。

## 两项关键新通过

**B自己的1200已终态通过。** ced包`runs/systolic_b_final02_final1200/systolic_b_batch`于19:13:30.024913完成，1200任务、30412800输出、零失败、真实ASIC/E203执行；平均30503.34周期，宿主6467.2296481919475秒。摘要：

`017e7ca728e0c6f647660ef981f8d00541b552c0a38dec103809d9cc0c67fb09`

原final02队列于19:13:30.060546成为`reports_ready_review_required`，child=null，19:14:44核实真实协作锁不存在且无EDA进程。原driver149529/child156788已结束，**不能重启**。报告请求`runs/systolic_b_final02_queue/report_request.json` SHA：

`67b1e150943f6c0d35a08811b31d0067d93a1c3bc6b076c5f15aefbc777e3fb2`

完整最终报告对全部回执的独立复审、内部100浮点误差汇总仍待执行；不冒充官方600。证据`handoff/team/evidence/SYSTOLIC_B_ASIC1200_20261112.json`。12性能任务平均仍30502.333333周期/4917.656573task/s，不能与1200任务平均混用。

**R4 SAIF方法crosscheck02实际通过。** 19:15唯一启动driver287254，19:18:05.488335完成，新run`runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck`，摘要：

`a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26`

整机VCD0.0721431449W、SAIF0.0721531361W，相差约0.013849%；最大主要模块CPU差约0.534759%，全部≤1%。实际PT证明1060个默认声明各自direct/leaf连接均0；保留原始默认名单及计数，不填造活动。原始映射计数不相同，但排除实际无连接声明后的映射一致。连接证明SHA：

`5c4bc75c7d9bb02f073fc8fbe6de26a98e86d3b6999fc441799438d159ffb0b1`

19:21:22再次核实summary匹配stage SHA、passed和qualified均true、协作锁不存在。旧crosscheck01失败保留，原R4捕获只复用未重采。证据`handoff/team/evidence/SYSTOLIC_B_SAIF_METHOD_20261112.json`。**这不是B功耗；system_power_verified仍false。**

## 已通过的其余B依据

- 原ASIC14/354816、实际CPU恢复十阶段76032输出及两例竞争、IRQ/WFI；DRC06自己的无SDFgate14/354816；干净目录ASIC14均已通过。
- DRC06摘要`b81780033ef65998c43a874b559e54da0d958524a040eff374b1e8f1a4824ced`；7个等价单元升驱动，0约束违规，220宏/0锁存器/无组合环；面积保守上界1.099094695900963mm²，SS/.99V/125°C任务模式setup+.00010252ns、hold+.00249085ns。不是物理裕量或签核。
- DRC06 gate02摘要`7c1a3ade96aa9a6bcb307d291b216667a7c6ff9595632e08bfb0f6d69289de99`；固件`11d860ca0269f962a71250e72925c730def0da79d931a79e3102c82ddaa16b91`。
- clean14摘要是64字符`1aecb2205f4bdc2de4c556e17d446590075c49fa71f78b46ceee7c4f09101bce`，较早63字符转录错误已改。其真实CPU调度证据已在d14d858同步：首feed平均933.67拍，供数空拍9033.67，X/W等待重叠；同tile平均81.7895、换tile305.7111，结果尾19、写尾37。结果区/信用等待在12例中为0。
- R4仍为4333.2563task/s、0.9265616712mm²、布局前71.8126319mW/16.5724388µJ；自己的1200及全部R4活动受保护。

## 下一步：准备请求并启动B活动/功耗接续

ced服务器基础包绝对路径：
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`

709输入manifest仍`39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d`。16文件工具已经完整安装在`../../operations/systolic_b_tools_4b58ff0`，manifest`bf8e214e70ac92b17b3ecc0c41497995ac0b1d0aa5c483a9662b0225b08f6289`，禁止重新append部署块。

本机`E:/fpga_race-two/takeover_local/b_power_request_prepare_00..03.txt` **四个仍全部未执行**。依次执行后读取实际新`operations/b_power_final01_request.json`SHA。生成器会绑定终态final02及已合格crosscheck02，不需要任何手工替换旧结果。尚未准备/执行power launch。使用新`systolic_b_power_queue.py`（SHA`e9779c72bae7652cade03ed2f26644a0a2ebbb493c9c269a1bc9bb0c53c90366`）创建唯一session，环境`PYTHONPATH=workspaces/arch03/scripts`。只接续activity12→power12，不重复ASIC14、1200或gate14。

采集首例按实际时间/体积更新预算，预留20%；最终使用同ops的`systolic_b_report.py`独立复核、导出JSON/CSV/中文。新B PT导入单独6.666666ns精确SDC并核实际时钟；原R4 PT6.66667ns序列化差异公开保留。新B功耗尚无数值，未知活动/宏模型影响仍需披露。

## 空间及桌面：当前没有待删动作

三次已授权删除仅旧ecf3 MMIO8 L01–L12 VCD，共360492854889B/335.735134GiB，已完成并同步。全部小型输出/回执/源码/重建输入和R4/B保留，**不能重跑清理命令**。第三回执SHA`ebe665444c666b1e0d3b67ff6bedc09fee2aade8a4525d6f524682bb5a00d4d5`。

共享盘仍被其他写入消耗，19:17:20只剩40.875GiB（此前19:14约50GiB）。应在长采集前核可用空间，必要时在用户授权内逐项审核其它旧已替代波形；不得删R4/B、队友文件或库。**第四次清理尚不存在。**

`b_old_wave_inventory4.txt`首次用了递归rglob，扫描慢，在19:19以Control_L c主动停止了仅该前台只读目录扫描；没有中断后台crosscheck02或删除文件。`ctrl+c`拼写第一次被helper拒绝，第二次分键正确。该文件现改成固定深度`*/runs/*/*/*.vcd`，排除systolic-b/icb32-r4，**新版查询尚未执行**。它仅列最多四个旧候选，不删除。

VNC fresh18874436、workspace3、ced空闲shell；最后crosscheck02简短查询已完成，**没有待Return/悬挂exec/前台monitor**。旧只读final02 monitor正常结束，不能向它再输入。FileZilla关闭；用户确认无人占FTP，421不再反复询问。workspace4不用。开发板现有relay不要凭过期pid文件重启。

## 同步与剩余工作

本轮之前云头`d14d858e8c89aa5b73c0ae5f6c5d52fc28548b81`已核实。用户刚要求先同步；当前将1200/SAIF通过、更新验收和README、当前检查点及证据提交推送同一私人分支`codex/light-light126/undergrad-d1-numerics`。不含凭据、库、大产物或聊天原文。之后继续空间核对、B activity12/power12、独立报告和交付收尾，不结束在这次同步。

旧失败final01的63字符hash、crosscheck01默认对象、库存扫描取消等保留记录。B RTL/固件/编码未变，不开发A，不重跑旧8路/R1或R4批量。官方600、布局后功耗时序、物理签核未验；赛事入口用户暂缓提供。
