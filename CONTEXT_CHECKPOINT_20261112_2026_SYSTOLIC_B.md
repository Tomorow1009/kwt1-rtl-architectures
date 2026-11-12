# B检查点：2026年11月12日20:26

**20:34:04.308726增量：原队列320367/activity320434继续运行，无error。活动L01/L02/L03已通过，SAIF分别114841176、114816275、114795630B；其余9层继续。实测free147345089536B，剩余存储预算3390740552B（1.2倍及2GiB预留）。已完成3/12不等于最终活动/功耗PASS。** 本次恢复已重读AGENTS、实施计划、本检查点、交接及STATUS，五次清理均已结束，不再执行。最新只读命令b_power_final01_progress已完成，VNC工作区3空闲shell，无待Return。

**任务ACTIVE，继续执行，不要结束于同步。** 用户最新要求“把本版完成情况同步GitHub，再继续工作”已完成同步；原要求是直接5×16脉动B，A取消，R4保护。生产63da6ba/v3/credits3冻结，11/13 17:00前交付收尾。有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`。压缩后先读AGENTS、计划、本文件、STATUS；细节见[19:50含20:07增量](CONTEXT_CHECKPOINT_20261112_1950_SYSTOLIC_B.md)和[19:22已完成证据](CONTEXT_CHECKPOINT_20261112_1922_SYSTOLIC_B.md)。

## 唯一实际运行任务

**20:25:22.531462：B power_final01仍running，queue320367、activity child320434，无error；完整SAIF已通过L01/L02，第三层继续。** L01 114841176B，L02 114816275B；每层25344输出与原门级完整窗口一致。当前不是activity12最终PASS，尚无B功耗数值。

服务器基础包：
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`

- queue：`runs/systolic_b_power_final01_queue/state.json`
- child：`runs/systolic_b_power_final01_activity12/systolic_b_saif`
- 总launcher：`runs/systolic_b_power_final01_launcher.log`
- 请求：`../../operations/b_power_final01_request.json`，SHA **`e99f9e51d8ddbff5c3921e01d15aac99a7b851018884857089044ccded5479d0`**。
- ops：`../../operations/systolic_b_tools_4b58ff0`，16文件manifest **`bf8e214e70ac92b17b3ecc0c41497995ac0b1d0aa5c483a9662b0225b08f6289`**。
- base709输入manifest **`39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d`**，从未修改。
- 队列只接续activity12→power_l01..12，最终生成report_request。不能重跑ASIC14、1200、gate14或R4捕获。
- `b_power_request_prepare_00..03.txt`和唯一launch **已经全部执行**，不要再次append/生成/启动；16文件ops也已完整部署，不再传输。
- 首次launch只是SHA转录`d8ddbf5fc`错字，前置断言阻止启动；后来实际双段读取`d8ddbff5c`并确认无queue/log/lock才唯一启动。没有失败的实际power阶段，不原地重复任何任务。

本地可重复查询：`takeover_local/b_power_final01_progress.txt`、`b_power_child_process.txt`（按当前child取实际进程树）、`b_power_final01_health.txt`（层日志）。最后实测simv322040是L01，后续PID可能不同，**不要固定该PID判断当前仿真**。stage320434保持运行，逐层另起子进程。

## 宿主时间与空间

L01脚本19:48:51.277409，完成receipt20:02:42.636384，约831.36秒/13.86分钟；此前编译约83秒。按首例剩11层+20%约3.05小时，再加PT12和独立报告。此为估算，不能写成完成。L01窗口93003.324033→301929.969807ns、31339周期。

首层实测最大案例体积115169610B，剩11层预算3667722500B，含20%+2GiB。20:25实际free**156026011648B**（约145GiB）。共享盘其它写入持续消耗空间，要继续监测，不能只看静态首例预算。

## 已完成的硬件/方法结果

- B自己真实ASIC/E2031200于19:13:30.024913终态passed：1200任务、30412800输出、零失败，batch均值30503.34周期，宿主6467.229648秒。摘要 **`017e7ca728e0c6f647660ef981f8d00541b552c0a38dec103809d9cc0c67fb09`**。
- 原final02退出并释放锁；报告请求 **`67b1e150943f6c0d35a08811b31d0067d93a1c3bc6b076c5f15aefbc777e3fb2`**。最终导出对全部回执的独立复核和100样本浮点误差汇总尚待，不能标官方600。
- R4 SAIF crosscheck02于19:18:05.488335passed，摘要 **`a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26`**。整机差0.013849%，最大主要模块CPU差0.534759%，全≤1%。1060默认声明actual PT direct/leaf连接均0；连接证据 **`5c4bc75c7d9bb02f073fc8fbe6de26a98e86d3b6999fc441799438d159ffb0b1`**。原始映射计数不同，剔除实际无连接声明后相同，没有填造活动；旧crosscheck01失败保留。
- DRC06合格任务模式：面积上界1.0990946959mm²、SS/.99V/125°C/6.666666ns，setup+.00010252ns、hold+.00249085ns；220宏、0锁存器/组合环、0违规。仅七个等价单元升驱动，不改RTL/约束。
- DRC06摘要 **`b81780033ef65998c43a874b559e54da0d958524a040eff374b1e8f1a4824ced`**；其gate14摘要 **`7c1a3ade96aa9a6bcb307d291b216667a7c6ff9595632e08bfb0f6d69289de99`**。真实CPU恢复/竞争/IRQWFI和新干净ASIC14均通过。gate无SDF，不是物理签核。
- 生产固件 **`11d860ca0269f962a71250e72925c730def0da79d931a79e3102c82ddaa16b91`**；clean14摘要 **`1aecb2205f4bdc2de4c556e17d446590075c49fa71f78b46ceee7c4f09101bce`**（旧63字符错字已修正）。
- 12性能任务均值30502.333333周期/4917.656573task/s，不能与1200均值混用。7000未达；当前流量下界约28341.33事务，理想上限5292.62。整体比R4吞吐+13.4864%，不能单归因脉动。
- R4保底：4333.2563task/s、0.9265616712mm²、布局前71.8126319mW/16.5724388µJ；这些不是B功耗。

## 五次空间清理全部结束，无待删除动作

用户已明确授权删除已验证且很可能不再需要的旧大文件。五次累计**524880555968B**。全部R4/B、厂商库、小型回执、输出和重建输入保留；旧VCD将来需重生成，不能声称仍在。

1–3：旧ecf3 MMIO8 full01全12层，共360492854889B，已早先完成。

4：a2e旧MMIO8单层重复波形和5946旧D3gate07_h0 L01，共**61477973078B**。回执`runs/authorized_cleanup_20261112_fourth.json` SHA **`0c8310269eee5ba94ef8931082ecfde9ef3048cd3f44e72abee91ab761445df5`**。本地总数首次转录37078错误，由两文件求和断言发现，已改为73078，服务器原receipt未错，修正已推f56b642。

5：**刚完成**旧`light-light126-vcd-bits-dma16-20261110_003213-a53e4186a13a/runs/dma16_gate03/dma16_gate/layer_01.vcd`至`layer_12.vcd`，总**102909728001B**。原stage/summary于11/10 03:41:09passed，原摘要 **`9ba06d90c32842d1a817ddc2d439964af7b406af10617fca6f7bab43908f24dc`**。20:25:22独立确认12文件均不存在，摘要/源清单/12CSV哈希仍相同，B队列未中断。

第五回执`runs/authorized_cleanup_20261112_fifth.json` SHA **`45ffee0f7659bc842ae39143d7fe78713680ec5ba9377cc49ec07269aef48c29`**。所有prepare00..03和execute都已执行，不能重复。命令长度两次本地检查超1000，未发送；最终987字符经路径/清单/大小/保留哈希/fuser=1检查后执行成功。

仍未删除的旧D3activity01 L01没有预期summary.json，不自动处理。现在不要再运行任何cleanup；如之后空间又不足，先另行核清可再生的大文件，尤其不能盲删R4/B或队友数据。

## 同步及新本地包

用户要求的已完成结果在**f6f704c**推送核实。最新已云同步HEAD为**f56b642e28a0c3b18abe906b3ccd169e57e94c72**（第四次清理及启动身份、字节纠错）。当前20:26检查点、第五回执、新包证据及后续STATUS改动待下一次同步。

新本地源码/固件包`local_runs/light-light126-systolic-b-v3-20261112_195820-f56b642e28a0.zip`：11397311B，722文件，ZIP SHA **`4654aa32bd8d89fc8d58f2228d01cf998c2924924f2817fa3d8fa6be423ba479`**，manifest **`47f6350037218b6d712cf3c24f5fa0e2f0759c262826ee9b68c1c044bca736c2`**。仅本地准备，**未上传/未新包服务器复现**。

187项生产/数据/固件对比中185项字节相同，差异仅诊断sequence ELF容器和manifest里的elf_sha；独立ELF解析证明入口与全部PT_LOAD一致，sequence.bin/verilog逐字节一致，生产固件manifest仍11d860ca…。不能写所有文件完全相同或授予新包PASS。证据`handoff/team/evidence/SYSTOLIC_B_DELIVERY_PACKAGE_20261112.json`。本地构建8454已退出，无本地运行任务，不重建。

## 下一步与UI恢复

持续原power_final01，按真实层完成和空间更新估算；活动12完成后队列会串行PT12。只修必要工具问题，不改冻结RTL/位宽/布局。队列终态后以同ops`systolic_b_report.py`绑定最终report_request，独立复核1200/精度、导出JSON/CSV/中文，完善R4/B对照与交付。

VNC fresh**18874436**，workspace3、ced空闲shell；最后`b_cleanup5_receipt.txt`已Return、截图已读。**没有待输入/未读tool输出/本地exec/前台monitor。** FileZilla关闭，FTP421无需再问用户；workspace4不用。不要按旧relay pid重启网络。ABI属于固件身份输入，不能编辑进度文字。

官方600、布局后时序/功耗、物理签核和未知活动/模型影响仍未验；即使后续功耗数值齐全，system_power_verified不自动变true。赛事入口/署名用户暂缓，不能阻止当前验证。
