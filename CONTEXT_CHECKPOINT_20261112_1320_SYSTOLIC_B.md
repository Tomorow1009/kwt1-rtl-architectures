# 2026-11-12 13:20 B接续检查点

**13:29增量：原DRC03已失败并释放锁，不能继续当运行中。** 实际DC报OPT-106/OPT-128：原DDC记忆的8d标准库路径，与新复制到drc03/libs的同名库冲突，compile异常OPT-100。没有新合格网表。新本地修复让compile直接绑定原已核验库路径（新目录仍保留同SHA数据库副本用于后续报告），原约束和RTL不变；准备新的drc04，**尚未启动**。

SAIF本地已按实际格式修正：新saif_syntax.py只去除引号外C注释、仅接受整数值小数duration，不舍入；tiny/streaming明确保留VCS合并TX(X或Z)，缺TZ时分离TX/TZ总量为null而非零。请求改1e-15。formal VCS/PT和R4交叉核对仍未运行。13项相关实际格式/流程保护测试通过，只是本地工具检查。

结构04改env后实际解析完成到报告元数据，却因overlay内没有相邻dma16_structural_audit.py而失败，仍未生成JSON。已本地修复为记录实际导入模块__file__的hash，待新工具副本部署；不得修改e6历史工具。之前立即读取structure04摘要的查询因此文件不存在失败，非硬件失败。

当前本地新SAIF/DRC库路径/结构元数据修复尚未提交或部署。VNC workspace3/ced shell，FZ关闭，无本地持续任务。b_drc03_state已输入执行，截图需读取以保存确切结束时间。下一步提交同步、创建新的小工具目录（优先小型差分、每条<1000字符，整个文件SHA核验），再新drc04与正式SAIF小试，串行不重复旧作业。

任务仍ACTIVE，用户明确清理后继续。有效计划：workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md；A取消，B/63da/v3/credits3已源冻结，R4保底。先重读AGENTS、计划、本检查点及前1140检查点。11/13 17:00收尾，官方用户称11/13晚上。

## 已完成与限制

- 两次授权清理旧MMIO8 L03–L12原始VCD，共279.506GiB。原输出/日志/网表等小证据及所有R4/B保留，清单已保存；不重复清理、不碰队友。旧波形重新做活动需重建。
- B自己的ASIC14/354816输出、IRQ/WFI通过，12层平均30502.3333周期/4917.6566task/s（150MHz折算，非实测芯片）。1200仍未运行。
- 原8d包synth02已完成：220宏，0锁存器，无最终组合环，面积保守上界1.0991231047mm²，setup+0.0002141ns/hold+0.00249085ns。**4项max_transition违规**，要求约1.35ns、实际约1.37ns，时序未批准。
- ced包validation03确切结束12:29:55.383784，state SHA d0a35dfd75df95199ec9a18a3cce323ea379f4620bfcbf9789a83f650c7c6b3。实际sequence十阶段/76032输出、CPU异常/超时/无复位ABA通过，host9.629578209秒；phase7预期超时rc=-1。contention L01/extremes各25344输出/35625与43786周期，全部写回应答完成。
- 原synth02的无SDF gate14/354816通过，逐层周期与ASIC相同；摘要55c668a8bf8b8d0437d142ee929d2953b06f92a52c480074f7326aa616f32ca5。新修复网表不能沿用此PASS。

## FTP与工具部署

用户确认没有队友在用；开发板ps无FileZilla，仅VNC。FTP两次返回421（服务器连接用户过多）。FZ已关闭；不改变目标或代理。

完整62faf49包712输入、SHA b9eb6819561e502b092706cbbd25d5128f3b891478b5532d72c3681f07816462、manifest17f72b859ef15ea3d8561a6ae293e691a19d2f551197e80fb868c89e8b2b64eb，仅本地/板端暂存，未FTP上传。该包存在后来修正的两处工具Path实参问题，不直接执行。2b旧包同样未上传。实际硬件/固件镜像一直未改变。

改用已授权VNC终端写新个人operations小工具目录，旧包输入不动。27b的9351字符长命令因shell `Unmatched '`失败，目录不存在已确认；不能重试该入口。后来修复DRC自身模块和SAIF终态sha(Path)两处实参，7项真实文件记账/替身EDA及保护测试通过。

**实际部署成功：**

- 云端 e6b211eed7830cb339308a5b244fb37966ebb5b4，push和ls-remote一致。
- operations目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/operations/systolic_b_tools_e6b211e`。
- 4文件：systolic_b_ops.py、systolic_b_drc_repair.py、native_saif_units.py、systolic_b_structure.py。
- manifest SHA **8d6756834afff64c3ae453c45b5fc1894c3f65d3fec0cec000312ddeea8bfe86**。
- payload SHA0870f6da6b9357733f694e5fd228356b1e0a0a34e7564645107a899ec9c9ab89，8312字节；16个短命令（每条<1000字符）分段核尺寸/末尾完整hash后写文件。13:11:06实际4源文件SHA核验成功；所有16条均已执行，严禁重复append/展开。
- 基座仍ced包`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`，manifest39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d。新工具入口复用原锁、base.inputs和新session，所有副本/来源hash写入报告。

## 实际正在执行的唯一EDA

13:12:03预检：无锁、无EDA，可用418.935546875GiB。这是共享盘当时读数，增量不能全归功于本任务清理。

**B DRC修复：PID180611，session `systolic_b_v3_drc03`，ced包`runs/systolic_b_v3_drc03/systolic_b_synth`。13:15:19唯一启动，13:16:19实际进入`Beginning Pass 1 Mapping (Incremental)`。**

- 从原8d synth02的映射DDC复制到全新repair_seed.ddc；原综合摘要3e0f88eeb4855a15f8743f820f587cd90df7e52a748d112e8fd5ba788dd86d03。
- 原RTL/安装器/源码与原task_mode.sdc逐字核验，保持6.666666ns、SS/.99V/125C及原I/O负载，220宏保护。
- 安装DC官方`doc/syn/man/cat2/compile.2`已确认`-only_design_rule`只修设计规则；实际命令`compile -incremental_mapping -only_design_rule`。
- 原网表/约束不修改，新结果需重审约束、面积、结构并新gate14。不要重启原综合、validation03或本修复；禁止改正在使用的e6 operations文件/manifest。
- 查询`takeover_local/b_ops_drc_status.txt`，会打印state+实际日志尾。结果尚未读取，不能猜已通过。

## SAIF实际诊断，尚未资格通过

ced `runs/systolic_b_v3_saif_units01/systolic_b_saif_units`，PID178557，13:13:05.874909至13:13:15.604927。诊断运行本身status passed（完成10种试验），**所有10种条目均失败，不代表SAIF通过**。摘要SHA **a8af5c6ab790b734bb91e1b25ed2f3695ad2ffa8839c3bc00c1a6a744f593879**。

- 无tres：VCS说参数数目错误、没有输出。
- 1ns/1ps/ps/1fs/fs/带空格单位：拒绝，日志全部保留。
- `1e-12`与`1e-15`：实际生成native.saif，现解析器因前导C风格注释报Unexpected SAIF text。
- 读实际`exp_fs/native.saif`：`/* This file was generated with saif_region command flow. */`，TIMESCALE 1 fs，DURATION **60000000.00**。probe T0=30000000,T1=10000000,TX=20000000,TC=2,IG=0；toggle T0=40000000,T1=20000000,TX=0,TC=4,IG=0；没有TZ。**VCS将X/Z合并为TX，不能把缺TZ当零或声称分离统计。**
- 下一步本地修正SAIF解析：保留精确窗口/计数核对；支持真实注释和整数值的小数duration；明确记录combined TX（X或Z），不宣称未知为零。正式probe用科学计数法，之后真实VCS/PT小试、R4全窗口≤1%交叉核对才可采B功耗。未实现此修改时不要自动宣布资格。
- 当前native_saif_probe.py要求1ps，native_saif_replay.py要求1fs，仍会失败。流式native_saif_activity同样需支持上述真实格式。改工具须新副本，不碰正在用的e6目录。

## 结构审计与待办

旧解析器的实例`.rst`误判和LINT统计表行误判已本地修复并在e6部署。最新结构04命令失败是**远端tcsh不支持`PYTHONPATH=... command`形式**，报command not found，JSON未生成。改成`env PYTHONPATH=... python3 ...`即可，仍需真实审计；不修改旧脚本，不虚称通过。

待办顺序：原DRC终态→实际全约束/宏面积/结构检查→新网表gate14；SAIF解析/正式小试可本地准备，EDA仍串行；时序/面积通过后冻结审阅与自己的1200/30412800输出、干净ASIC14、活动12/功耗12、R4/B对照和最终材料。当前不满足最终队列审批前置，R4始终保底。

当前VNC18874435/workspace3/ced包空闲shell；workspace4不操作，FZ关闭，无本地持续任务、无待Return命令。最后是失败的结构04命令。`b_ops_units_launch`及`b_ops_drc_launch`已执行，禁止重复。旧`synth01`磁盘满、validation02缺cases、SAIF原probe失败均保留。
