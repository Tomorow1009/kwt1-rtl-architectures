# 2026-11-10 10:06 接续检查点

**10:23增量：** 新增独立`dma16_x_sensitivity.py`、`test_dma16_x_sensitivity.py`（7tests）及`X_SENSITIVITY_REVIEW_20261110.md`；与来源和数值共32tests通过。server_run增加专用stage及`--x-point zero|frozen|one|initial`，该参数不能用于正式功耗阶段。每点全新PT进程、读VCD前设置双方X参数，实际回读/单位/完整模块和162宏/来源表/错误/哈希均检查；新scope/schema不能混入full02，不自动批准系统功耗。**新X工具尚未提交/打包/服务器运行**，不要说敏感性结果已存在。当前工作树还含10:17的记录更新，待统一提交。现MAC v2仍在bb25旧不可变包里运行，不改其工具。

MAC扫描最后10:19:01.414245仍driver142991/child143321，fd3读到1268646653B（总8745588450B）；比原未知扫描慢，须按实际宿主时间估算后续12层，不假设原速度。没有并发重作业。X敏感性必须等锁空闲后串行排队。

**10:17增量，覆盖下方“修正未提交/无重任务”：** 兼容修正提交`bb25f0843195de883a12dedb12af0d8e3b0c8105`已推送并ls-remote确认。包`light-light126-mac-gcc48-dma16-20261110_100643-bb25f0843195.zip`，16639480B，SHA=`bdf0b13f74761595b7f02d83c633676cfb1afc2953f93208e582516134772c2f`；676输入/208干净tests/5固件/40生产文件与668一致，audit=`local_runs/dma16_mac_gcc48_clean_audit_20261110_1008/receipt.json`，SHA=`aaa14fdc2471c07827227f58704eeceafee88b70d6a5d066d04ca40c969409b0`。板端`/home/root/undergrad-mac-gcc48-20261110`，FileZilla33秒成功、success24、空队列，已断开最小化。10:12:44.410399安全解包，10:13:31.721855输入核验通过。

**当前唯一重作业：bb25包`runs/dma16_mac_use_l01_v2/dma16_mac_use`，driver142991，launcher10:15:24.921109、stage10:15:25.502263。10:16:15.035173 state/owner确认running，child143321执行mac_full_scan.json。** 首次启动缺runs父目录在Popen之前FileNotFoundError，没有启动作业；补建父目录后才真正启动。不要重复启动或清锁。首轮3dcd regex失败v1保留。新v2尚未看到完成，仍不能称MAC有效采样通过。没有挂起的本地测试/上传会话。

补充只读观察：原平台AON源码位于`rtl/e203/perips/sirv_aon.v`，另一个vsim/install副本不是本轮依据。原文件6920行，6870行明确注释backup register无需reset，待继续检查其实际写使能与未知对象关联。最短scope分类的sirv_aon1958标识，与全部AON引用别名2091条不是同一计数；样例包括Queue_1数据和SYNOPSYS_UNCONNECTED，不能只凭名字批准。未改AON复位/模型，尚未得出复位缺陷结论。

压缩后先读AGENTS.md、本文件、CONTEXT_HANDOFF.md顶部、`workspaces/arch03/IMPLEMENTATION_PLAN_DMA16_20261109.md`及三份状态JSON。仍在执行用户要求的三天直接16路DMA计划，不能停在进度汇报；用户已恢复、开发板上电，FileZilla允许，本次及后续同范围私人GitHub同步已授权，不再询问。

## 当前最要紧的事

服务器现无本任务重作业：原8路首层PT已成功；新MAC有效采样v1因GCC4.8.5的`std::regex`抛`regex_error`，09:59:40.385600失败并正常释放锁。**不是RTL数值失败，也没有MAC采样PASS。** 不重启旧目录、不清锁。修正已本地完成并通过8项测试，尚未提交/新包/服务器复验。先提交、干净打包上传，再新`dma16_mac_use_l01_v2`；之后用真实首层结果决定后续12层未知/有效时段审核与X敏感性诊断。

## 已完成且不得重复跑

- 16路生产仍fcd445fb212a；ASIC/E20314、恢复/实际竞争、同网表门级14及12完整活动通过，225770周期、150MHz标称664.392966task/s。生产RTL/正式固件和668批量runner/parser保持冻结。
- 668最终1200于06:22:56.909362通过30412800输出/0失败，a2完整报告full02于08:38:53.904490完成1200全部回执重审、12层原始功耗数字及JSON/CSV/中文报告。receipt SHA=`06c246af4de0914e1e304fc77cf1b61413e955a350c59d5d8d0df8c521e84e5c`独立确认，不再重复这两项重作业。
- d25独立审定绑定稳定任务模式150MHz时序与项目面积保守上界0.434796781612mm²。系统功耗/官方精度/物理签核仍false；setup裕量极小，不能宣称物理裕量。
- e777包实际annotation_all12_v3于09:32:25.979277完成12层来源/设置/24份未标注报告/统一身份审核；SHA=`697793c6f4ab94aebe16414a8dee1ad0723039e1404a052c3767697db0b78ac4`于09:34:09独立确认。两次真实格式失败保留。修正要求两张具名表分别严格核对；未标注报告自身表确认零未标注后才接受独立行1尾标记。精确映射不等于未知活动无影响。

## 新完成的原8路同源对照

不是8路DMA。新源通路综合1aa `runs/mmio8_source_synth01/mmio8_synth`于08:30:15.335643完成，摘要SHA=`0e33c1d045d063829c34e97b7ba10109d446c381c95fa7003449d0bbc6159fc9`；setup+0.00000905991ns、hold+0.00131008ns、0锁存、130大8小宏、保守面积0.2921861914119108mm²，约束审核仍待完成。

a2 `runs/mmio8_source_gate01/mmio8_gate`于09:31:05.827774 passed：首层25344输出、3843121周期、30231391361B完整VCD。摘要SHA=`b13216142fe97f8341942d53ded9de806fc96cb89feecfe64dc4270f6a4d4dfa`在PT启动前独立确认。首层门级/活动不是完整14/12验收。

e777 `runs/mmio8_source_power_l01_v1/mmio8_power`由driver**106327**、child107249执行，09:35:35.465062开始，**09:55:52.729450 passed**。之前22688是长截图人工误抄，已state/owner纠正。实际摘要SHA=`3321b70941d2667baaf5e143bcaf9db4e53cb01d0ac33f3a34543fe144a48eba`通过数值提取独立确认。

3dcd `runs/mmio8_power_numbers_l01_v1/numbers.json`于09:57:57.095761完成实际工件/单位/层次和138宏校核。正确SHA=`b7176c47b7e574e822e4b7a5fbbd0f7a62c4b3ae1c6b158b8ac2749af6a10711`于**10:03:19.227912**独立确认。第一次人工读错相邻字符，断言拒绝；按8位大写逐行输出后纠正，原文件未改。原始internal=0.0121767968W、switching=0.00148551364W、leakage=0.00627682032W、total=0.0199391320W；窗口25620804.104586ns，能耗0.0005108565949874820593520J。仍非正式系统功耗通过，不能用首层代替其余层。

## MAC有效采样新工具及失败

新增`activity_mac_use.cpp`、`dma16_mac_use.py`、`test_dma16_mac_use.py`，server_run增加`dma16_mac_use`阶段，文档`MAC_VALID_USE_REVIEW_20261110.md`。完整未知定位计数必须与原冻结扫描完全相同，VCD前后SHA不变；以时间戳前稳定值审核上升沿实际start/in/out握手，逐lane1584启动/101376输入/1584输出。保留未知边沿与时钟间隔，不能用沿后NBA数据证明采样正确，不能自动批准系统功耗。

实际声明头已读取，向量拆成单bit，路径为`tb_top.u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems.u_arch03_accel.core.lanes[n].mac`；e777 `runs/mac_header_v1.json`存全部声明，仅元数据。

首版3dcd包运行`runs/dma16_mac_use_l01_v1/dma16_mac_use`，driver129811，launcher09:59:11.678524、stage09:59:12.167053，09:59:40.385600 failed。原错误文件`mac_full_scan.json`内容`MAC_USE_ACTIVITY_AUDIT_ERROR regex_error`；10:02读取实际g++为`GCC 4.8.5 20150623 (Red Hat 4.8.5-44)`。编译通过、头解析失败，未完成完整扫描。

本地已去掉std::regex，以严格十进制/冒号/方括号解析，保留降序/宽度/完整性守卫并避免uint64缩窄绕过lane/bit越界。首次本地编译因Binding偏移量窄化被拒绝；在已验证bit<40后显式转换，重新编译8tests通过。新增畸形、多冒号、空边界、超大bit/lane、反向范围反例。当前新二进制`local_runs/activity_mac_use_v2.exe`，修正尚未提交/打包，生产不变。首版208干净测试不是修正版的干净包验收。

## 最新已上传/云端工具包

`light-light126-mac-use-dma16-20261110_094741-3dcd35187115`，源码**3dcd351871153aadbd4b991a8884be1948727945**已推送并ls-remote确认。ZIP16635627B，SHA=`9537abe61269aae66152b675e33aa7d25468c116204c85803d91d1b50f79f0e7`；676输入、208干净tests、5固件、40生产文件与668一致。clean audit=`local_runs/dma16_mac_use_clean_audit_20261110_0952/receipt.json`，SHA=`3a431d3e368aee6bb95d2f901b2bdc7459a0c06da121fc041c5a184124a97881`。

板端`/home/root/undergrad-mac-use-20261110`（GUI /home/board/...），FileZilla33秒上传成功、success23且空队列，随后断开最小化。服务器09:54:30.266365安全解包，09:56:16.888624核验676输入。该包仍含不兼容regex的首版，不能在包内修文件。

本地clean helper `local_runs/audit_dma16_delivery_bundle.py`已增加第二个C++编译及`ARCH03_MAC_SCANNER`、test_dma16_mac_use；新包应208tests，需重新执行，不覆盖旧audit目录。

## 其余未知审查与待办

- 首层原始389025未知记录及34742对象网表关联已完成（见09:06检查点/UNKNOWN_ACTIVITY_REVIEW）。32967有表达式，不得一概忽略；19733有引用MAC标识中位/最大未知约92694.0045周期，需有效采样证明。
- 09:52只读统计：窗口结束仍未知且有引用的标识8078，按最短有引用scope的实际reference分为215类。top为sirv_aon1958、arch03_shared_sram992、两种TCM448/384、e203_exu_regfile192等。第一次筛选使用错误分类字符串得到空集，已丢弃；正确enum为`mapped_expression_requires_time_review`，加入非零断言。尚未审定这些对象，不能凭名字判闲置。
- X设置敏感性诊断仍未实现/启动。安装手册已读：x_transition_derate_factor控制X跃迁功耗比例；include_initial_x_transitions控制首次X→0/1计入。冻结0.5/false。未来用相同完整窗口单独0/0.5/1和initial true诊断，不混入正式汇总、不宣称物理绝对误差界。
- 原8路完整14门级/12活动与12功耗、其约束审核、DMA16余层未知/有效使用、干净服务器复现、最终提交包与答辩仍缺。不重复1200/full02；不开发8DMA。
- H28=11月10日21:16:08，H64=11月12日09:16:08，H72=11月12日17:16:08；用户截止11月13日晚。

## 操作恢复

仅通过开发板Linux VNC操作服务器，FileZilla上传，不直接SSH/下载/隐蔽旁路。工具`F:/linux_fpga_try/ac820.ps1`，先刷新windows列表；最近VNC18874435、FileZilla20972102、panel10485764。VNC5终端页，第3页空闲。最后工具会话均已完成；没有后台本地编译/上传待轮询。服务器锁10:02为False，必须重查后才启动重任务。

服务器base `/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`，包在bundles，共享锁父IC的`.arch02_team_lock`；不自动清锁，不动他人进程，单EDA/大扫描。远端单物理行Python命令<1000字符，先本地长度守卫；哈希按**每行8位大写**打印，再独立断言，不再打印一行长列表。新目录安全解包/完整输入核验。FileZilla100%不是成功，等33秒成功回执/空队列再断开。

更早生产SHA、路径、数值和配置见09:06检查点及三份JSON；此前历史状态不可当实时状态。
