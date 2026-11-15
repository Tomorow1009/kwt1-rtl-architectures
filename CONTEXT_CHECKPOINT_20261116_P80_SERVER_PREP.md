# P80本地收敛，准备独立服务器验证 — 2026-11-16 03:05

## 03:15 实际传输进行中（优先于下方旧状态）

142fae28545759e33fa38de514eabf752cb8c43a已提交并推送。完整87文件payload已生成，本地SHA为ae9ac56a16fdef489c508368fd224082bbb6b1cb1e4d7fc319d880a3c6a7b3a8。另用长度前缀＋原始字节＋XZ无损封装，132124字节、SHA369f009655205d866a153584480209f43e21b759b266af78872433b64a587338，解包后整个JSON逐字节一致。没有采用早先wire差分实验，实验文件仅留本地，不部署。

**唯一VNC输入会话15378**正执行`local_runs/p80_transfer_142fae2_0315/transfer.ps1`，共202行；进度在同目录transfer_state.json。目标全新`/tmp/s4_21usr_p80_20261116_0315/light-light126-p80-142fae2`。此脚本仅核验并克隆输入，不启动EDA。恢复时先收完该会话，禁止第二路VNC输入、重复执行脚本或按旧ID盲输。

03:14:05新鲜只读观察：VNC18874435工作区3/Bash，锁不存在；tmp空闲92072710144字节，共享盘8115978240字节；XZ支持已确认。桌面T80和旧八路不动。P80服务器正式作业仍0。传输期间只做本地P80综合/功耗接入准备。

### 03:34 传输中完成的本地EDA接入

- 新增`p80_link.py`：从真实P80源码和所选深度固件重新ASIC链接，生成厂商宏头；禁止旧T80加速器/仲裁进入源列表，不复用旧linked.ddc。
- 新增`p80_partition_synth.py`、`p80_validation.py`和`p80_eda_server.py`：S0只提供已测边界预算，逐bit端口和工艺核对后转换设计选择器；三块DDC重新映射，最终链接核对子块不变和跨块时序。不是旧网表PASS转移。预算源S0状态键是`t80_synth`，已按原入口核对。
- 新增P80门级端口绑定、多笔完成证明、SAIF/PT、结构/时序/DRC入口。门级只采实际result/saturated；total仍由ASIC RTL严格观察，不用参考值填充。
- 本地`p80_gate_observer_20261116_032629_469475`三深度完成证明仿真及完整门级观察器elaborate通过；10项边界/端口/捕获/深度选择工具检查通过，41个P80 Python文件通过3.6语法/import。证据`handoff/team/evidence/P80_EDA_TOOLS_LOCAL_20261116.json`。这些工具尚未部署、没有服务器综合/门级/PPA结果。
- 第一次`p80_gate_observer_20261116_032531_824245`因XSim Tcl把Windows反斜杠解释为转义而失败，修为正斜杠后新目录通过；失败保留。60868失败/84324通过，两会话均退出，不再等待。
- 本地批量入口增加显式已核验固件参数，支持最终选择深度2/4/8；仍只20条240任务。正在传入的142fae2包没有这些后加工具或入口变更，不能原地补写，待独立新工具包。
- 深度选择工具按真实12任务、相同数据/结果和RTL身份、面积合格集合，使用精确吞吐比例≥99%选择最小深度；目前没有实际深度比较结论。

**唯一远端输入15378仍运行（03:33约81/202行，以transfer_state.json为准）；不并发VNC输入。** 尚未启动P80首层。下一步先等完整包核验，再显式启动新的深度4首层；后加EDA工具不能干扰当前传输快照。

恢复先读AGENTS、根交接、`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`、本检查点及STATUS的`c32_g32_20261115`。

## 不变约束及已完成阶段

原32位ICB、原平台SPLT_FIFO_OUTS_NUM=1/FIFO_OUTS_NUM=4不改；源读→成功共享写ACK→原总线真实读回→解码→最终输出ACK。X14/W12/acc32/total33/SHIFT10，当前80PE保持。后续C80→C32→G32，最终32PE，≤1.00mm²/150MHz。正式只前20条240任务；不运行100条正式硬件批量。

**服务器`Desktop/T80_Delivery_20261113`及旧八路所有数据绝不写、移、删。** 新P80目录与旧版本独立，旧队列不恢复。没有子代理。

S0已技术验收、持久归档并冻结；8d92e46及标签arch03-s0-partitioned-20261116-0215已push。原网表、PPA及归档身份详见`CONTEXT_CHECKPOINT_20261116_S0_FROZEN_P80.md`，不重复跑S0。所有S0队列/helper已退出。

## P80源码与本地结果

957838b已推到个人分支`codex/light-light126/t80-pipeline-c32-g32-20261115`；包含新独立RTL/固件/观察器及本地协议初始回执。之后新增服务器准备工具、安装器Path类型修复和后续测试回执，待本次提交。旧T80源码未改。

- 仲裁归属FIFO和DMA已接受类型/地址FIFO，深度2/4/8；源信用3、源/读回FIFO16/16、输出32、未呈现描述符8保持。
- ABI ID4b57530b、cap000905bf；90h深度、94h数量/峰值、98h信用停顿。固件核对身份、数值与深度。
- 仲裁：三深度601/1040/1496笔响应全部排空；DMA：每深度9场景通过，四种错误/取消/复位/最后ACK等待。
- 窗口：每深度5完整/9拒绝场景；首次VALID和最后DMA ACK及延后排空证明。溢出错误仍跟踪实际响应数量，不能提前结束失败窗口。
- 路由：每深度160笔（CPU64/DMA96），CPU低地址和共享访问交错；原输入→O4→物理从端→O4响应→输入响应→正确CPU/DMA全核对；6类故意错误被拒绝。不取DUT内部归属指针。
- 完整数值块：10000随机＋32定向、794560输出、201275暂停周期、11取消/11复位，恰好64MAC及sum/total/result/sat通过。`p80_systolic_array_20261116_025155_411936`。
- 矩阵：19个1拍任务覆盖所有12层＋极值/舍入，另3个2拍A/B/A，共22个完整矩阵557568输出，total/result/sat/坐标、真实共享读回一致；不是CPU或原mem_fab验证。
- 序列：十阶段本地fixture通过（拒绝配置、取消、超时恢复、A/B/A），3个故意错回执/源切换被拒绝，3成功任务76032输出。此fixture不执行E203、真实异常或驱动超时。
- 正例、CPU竞争和恢复三套完整观察器针对实际P80团队模块全部elaborate通过，仅编译，没有整机仿真结论。
- IRQ固件深度2/4/8及序列/竞争深度4已编译，均无ITCM任务输入；P80 Python3.6语法与imports通过；安装delta/独立克隆范围5项单测通过。

全部回执与源码哈希在`handoff/team/evidence/P80_LOCAL_PROTOCOL_20261116.json`。详细local_runs：

- arbiter_20261116_022220_377239、transport_20261116_022612_746819、window_20261116_023913_247689、route_20261116_024953_796864（均加p80_前缀）。
- p80_datapath_20261116_025156_036756：初始9任务。
- p80_datapath_20261116_025452_754463：其余10层。
- p80_datapath_20261116_025452_181353：2拍3任务。
- p80_sequence_fixture_20261116_025408_554187。
- p80_monitor_elaborate_20261116_025840_965377。

**本地所有exec会话已结束：34263、52105、3081、40080、13833。** 不再等待/重启它们。

## 尚未完成

真实E203/原mem_fab三深度测量、选距最佳≤1%的最小深度、ASIC14/恢复/竞争/240；P80自己的分块综合、门级14、完整SAIF12/PT12/面积时序尚未执行。C80/C32/G32未开始。

新`p80_server.py`只开放status/build/soc/sequence/contention/batch20，绝不把T80 gate/PPA套到P80。PPA工具须建立P80自己的分块/身份契约。`p80_paths.py`使用新private根s4_21usr_p80_日期_时分，仍使用原共享协作锁。

## 打包与恢复入口

- 新`p80_prepare_bundle.py`从已核验S0工具包66b9496的853个输入复制到全新P80根，仅新副本替换P80源码和固件；旧源前后核验、无删除/硬链接/旧结果继承。
- BASE `/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-66b9496`，manifest `2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4`。
- `make_p80_overlay.py`只在本地生成payload，要求所选源码已commit；源、数据不传大型文件，运行复用服务器已核验数据。尚未生成/部署本次payload。
- 固件目录：`local_runs/p80_firmware_d4_20261116`、d2/d8同式；`p80_sequence_firmware_d4_20261116`、`p80_contention_firmware_d4_20261116`。
- 本地固定14数据仍只读使用旧工程`E:/fpga_race-two/kwt1-rtl-architectures/workspaces/arch03/local_runs/n1_data14_20261113_02/{source,prepared}`，从未修改。
- 过时未跟踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不得提交或执行。

## 远端最后观察及失败路径

02:47:24原官方mems只读检查确认split1/FIFO4/O4高地址范围；截图`takeover_local/p80_platform_parameters.png`。02:41共享盘剩5,371,854,848B；同机其他团队有DC/PT进程，未干预。自己的P80远端作业仍0。VNC18874435/workspace3终端Bash空闲，FileZilla关闭，workspace4不动；重连/压缩后先windows＋截图，不能凭旧ID盲输。

工具`F:/linux_fpga_try/ac820.ps1`；使用现有板端Linux桌面/VNC可见输入，不隐藏直连赛事服务器。最近多次只读查询在新S0包内找不到platform，原因是S0复用了原T80链接DDC而非复制platform；实际官方源为`/storage2/2026contest/server4/s4_21usr/Desktop/e203_hbirdv2-master`，已读取。不是数据丢失。

本地失败保留：窗口首次测试realtime精确相等受浮点误差影响，改为半fs容差并保留周期精确核对；route负例Windows批处理拆FAULT=1，改options文件，6类负例重跑通过；安装器sha(str)修成sha(Path)，3项delta测试通过。服务器没有因这些问题启动失败EDA。

下一步：提交新工具/最终本地证据→生成核验payload→新P80服务器目录→只读核对锁/进程/空间→depth4真实ASIC首层；通过后测depth2/8。硬件候选独立编译/运行，所有旧结果和保护目录保持。
