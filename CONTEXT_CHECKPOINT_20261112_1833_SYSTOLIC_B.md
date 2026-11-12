# B 检查点：2026-11-12 18:33

**任务ACTIVE，继续实施，未暂停。** 用户要求直接5×16脉动B，取消A；保留R4退路。有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`。生产硬件63da6ba/v3/credits3冻结，150MHz/Q12/原32位ICB/真实共享写ACK不改。11/13 17:00前收尾。压缩后先读AGENTS、本文件、计划、STATUS，核已做/未做/失败路径，不重启已运行队列。

## 唯一运行任务：B自己的1200

服务器ced包：
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`

**18:33:05.778119实际观察：final02 driver149529，batch child156788，running，无error。761/1200任务、19,286,784输出、零失败。** 宿主约4041.77秒，含20%余量剩余2797.90秒。实际free104467529728B，剩余439任务预算3587990855B。约19:12能跑完是按当前速度估算，终态必须重新读取。

- 队列`runs/systolic_b_final02_queue/state.json`，批量`runs/systolic_b_final02_final1200/systolic_b_batch`。
- clean14已通过，SHA **1aecb2205f4bdc2de4c556e17d446590075c49fa71f78b46ceee7c4f09101bce**。
- final02 request SHA **99e5b3330e4f89d8e94ea723cc936876da4ea3dffcf4d7431fe83c1f471d9f39**，冻结review **e41a5c0107eb4071d8b9454d3d4370d06793978532c4670eb8cc584bd7522c54**。
- 本队列只执行clean14→own1200→report_request，不执行未合格SAIF。完成后status应`reports_ready_review_required`，不是系统功耗PASS。
- final01在启动EDA前因手抄旧队列hash少一字符失败，无队列目录；旧请求/日志保留，不重跑。原validation03正确SHA **d0a35dfd75df95199ec9a18a3cce323ea379f4620bfcbcf9789a83f650c7c6b3**，不是旧63字符版本。
- 不要重新运行R4的1200，也不要在B批量完成前并发PT/VCS/DC。

## 已通过的B独立证据

自己的ASIC14/354816、真实IRQ/WFI、无复位CPU恢复76032输出及两例CPU竞争已过。DRC06综合SHA **b81780033ef65998c43a874b559e54da0d958524a040eff374b1e8f1a4824ced**，七个等价单元升驱动后0约束违规，220宏/0锁存器/无组合环。面积保守上界**1.099094695900963mm²**，声明SS/.99V/125°C任务模式setup+.00010252ns、hold+.00249085ns；只适用综合模型，不是物理裕量/签核。

DRC06自己gate02于16:36:07通过14/354816，SHA **7c1a3ade96aa9a6bcb307d291b216667a7c6ff9595632e08bfb0f6d69289de99**，真实CPU、无SDF。12层完整平均**30502.333333周期/4917.656573task/s**，与ASIC一致。固件manifest **11d860ca0269f962a71250e72925c730def0da79d931a79e3102c82ddaa16b91**。自己的最终1200、B活动12/功耗12、最终报告审计仍未完成。R4为4333.256task/s、71.8126mW/16.5724µJ布局前估算，不能转移为B功耗。

## SAIF现状及新修复准备

R4 replay01完整25344输出/34639周期窗口通过，SAIF94632798B，summary **f7d542dd8e741c008c37c8f50385de451742a4e9125da685228056698e23d21a**。旧crosscheck01 **failed**：362618 nets中361558 file、1060 default；原PT运行正常，但旧覆盖审核拒绝。它没有方法资格或comparison summary，不能改写旧终态。

只读诊断：1060全部No-Driver且不在SAIF中；1049在所属模块无逻辑引用，11是复杂转义内部名，识别端口0。第二清单在`runs/r4_saif_missing_inventory02.json`；SHA需用`b_isolated_sha_brief.txt`重新短读，先前长输出被截不可手抄猜测。诊断工具02 SHA **368ae0dce140cd484826e1fb0c82ad64fd85c5429ad56a7aba5a86864d03380c**已部署；01因转义路径失败保留，无JSON。不要重跑诊断。

已有报告只读数值对照：R4 VCD0.0721431449W，SAIF0.0721531361W；CPU差约0.5345%，其它主要模块0或更小，全部≤1%。**数值接近不能代替缺失对象的连接证明。**

新`native_saif_isolated.py`依据实际安装PT官方all_connected文档，在同一linked netlist中对每个真实默认对象同时检查direct与全局leaf连接数。仅两者均0且前后名单/数量完全一致，才能记为无实际连接声明；保留原始默认数量及表格，不赋零、不填造活动。只在比较时另外报告剔除这些已证明无连接声明后的分母。任何有连接、遗漏、驱动对象或其它未知来源仍失败。11项相关本地检查通过，**实际新PT未运行，方法仍未合格**。

## 最新工具已完整部署，下一步不能重复传

最新源码/云提交 **4b58ff0abdff071165194574c569693b15d711f3**，push/ls-remote一致。新16文件ops：

`../../operations/systolic_b_tools_4b58ff0`

manifest **bf8e214e70ac92b17b3ecc0c41497995ac0b1d0aa5c483a9662b0225b08f6289**。

18:22:29已看到`OPS_DELTA_VERIFIED 16`；5796B payload、00..11全完成。**禁止再次append/安装。** 前一0b082fd15文件也完整保留；原batch仍用52f37cc13文件、ced709输入不改。

新ops含`systolic_b_power_queue.py`，SHA **e9779c72bae7652cade03ed2f26644a0a2ebbb493c9c269a1bc9bb0c53c90366**。它只接续已完成final02的activity12/power12，不重复ASIC/gate/batch，必须绑定实际1200、同硬件/固件和已合格R4方法。3项本地检查通过；首次负向夹具共享字典导致未触发失配，改成独立引用后通过，非硬件问题。**新队列未启动。**

准备入口位于本机`E:/fpga_race-two/takeover_local`：

1. `b_final02_progress.txt`：读取原队列/批量与空间，已多次只读执行，可继续查询。
2. `b_crosscheck02_launch_after_batch.txt`：**只准备，未执行**；现已引用4b16文件，内置要求final02 status reports_ready_review_required。新session `systolic_b_r4_crosscheck02`。必须先核真实锁/进程释放，再执行一次。原请求`operations/r4_saif_crosscheck01_request.json` SHA **bcc2cc0fe8b62f0e960cf651405fd8d6b1551040f12fd184e436db8462928346**继续绑定同一R4捕获/基线。
3. `b_power_request_prepare_00..03.txt`：**全部未执行**。只有batch与crosscheck02实际通过后才生成新`operations/b_power_final01_request.json`；会验证实际原队列、report_request、资格summary/终态和ops身份。请求JSON使用chr(10)换行，未落盘过旧转义版本。
4. 观察请求SHA后再准备唯一power队列启动（尚无launch文本）。以`env PYTHONPATH=workspaces/arch03/scripts python3 ../../operations/systolic_b_tools_4b58ff0/systolic_b_power_queue.py ...`调用，单独session，源码ROOT仍ced。
5. 资格通过才采B12活动/12功耗；失败保留原始证据、修工具后新session，不填零。最终用新ops报告脚本独立核验全部1200/精度/活动/功耗并导出JSON/CSV/中文。原R4捕获不重采，自己的gate14不重跑。

## 三次清理全部完成，无待删动作

用户授权清理已验证且很可能不再使用的大文件。最新第三次仅删除旧ecf3 MMIO8 full01 L01/L02 VCD，**60375122403B/56.228714GiB**。18:31:13独立确认两文件不存在，summary/source_inputs/两份CSV都保留；回执SHA **ebe665444c666b1e0d3b67ff6bedc09fee2aade8a4525d6f524682bb5a00d4d5**，文件`runs/mmio8_source_gate_full01/authorized_cleanup_20261112_third.json`。精确名称/绝对父路径/非symlink/大小/summary及fuser=1在删除前再次检查，B任务未中断。

三次累计**360492854889B/335.735134GiB**，旧ecf3原MMIO8全12层VCD均已删除。小型报告、功能输出、源码/固件/重建输入保留；未来若要重新原始波形审核或功耗分析必须重生成，不能声称这些VCD仍可用。**R4、B、数据集、厂商库全部未动。不要再次执行任何cleanup。** 新本地证据`handoff/team/evidence/SERVER_WAVE_CLEANUP_THIRD_20261112.json`待提交同步。其它旧D3/a2e波形没有逐项核验、不删。

## 桌面与恢复

VNC窗口fresh **18874436**、workspace3、ced空闲shell。最后批量查询已结束，**没有待输入命令、没有悬挂exec**。FileZilla关闭；FTP421且用户确认没有队友连接，不再询问。workspace4不用。开发板relay原进程14084/31004存在，pid文件25104过时，不盲重开中继。若窗口BadWindow/End of stream，先枚举再用既有viewer恢复，不复用旧ID，不重启服务器任务。

新增接续/连接工具均已部署但未实际验收；尚缺最终1200终态、精度/报告独立复核、R4真实连接证明、B activity12/power12及交付审计。官方随机600、布局后时序/功耗及物理签核不在当前已验范围。继续原任务，不能把当前进度写成全部完成。

## 18:51增量：实际CPU统计与批量进展

- 18:49:41.965838批量仍149529/156788，950/1200、24,076,800输出、零失败；free93395615744B，剩余250例含20%时间余量1590.82秒。原队列未重启，后继仍未运行。
- 18:45干净ASIC14摘要与原队列reference自动匹配，提取真实CPU12层调度：首feed平均933.6667拍、供数空拍9033.6667、X等待6340.6667、W等待4248.3333（后两项重叠）；slot/credit等待0；同tile启动平均81.78947，换tile305.71111；结果尾19、写ACK尾37；已接受源读/共享写/输出写响应延迟均1拍。
- 新证据`handoff/team/evidence/SYSTOLIC_B_CLEAN14_SCHEDULE_20261112.json`；新交付索引`workspaces/arch03/SYSTOLIC_B_DELIVERY_20261112.md`。尚未填B功耗或最终1200 PASS。
- clean14手抄摘要旧值只有63字符，导致第一次只读统计断言失败；实际64字符为`1aecb2205f4bdc2de4c556e17d446590075c49fa71f78b46ceee7c4f09101bce`。已修正本检查点和STATUS；新查询读取并匹配服务器reference，不改任何实际结果或请求。首次本地文档编辑因PowerShell管道中文编码失败，无写入；随后ASCII脚本及apply_patch成功。
- 23330b2已经云同步；新的统计/交付/文档修改待提交。无生产RTL、固件、编码或服务器输入变化。VNC18874436仍workspace3/ced空闲shell，无待Return或本地挂起exec。
