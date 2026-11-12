# N1实施启动检查点：2026-11-13 00:55

用户已批准完整B0→N1→N2→D1→D2计划并要求实施，当前Default模式。H0=00:49:49+08:00，分支`codex/light-light126/arch03-n1-n2-d1-d2-20261113`从cd4a63ad4a4c7ab5e07b471bf70d7fd2fbc6bc5f新建。原B0标签/源码/本地255MB与服务器1.261GB备份不动。

## 必须先读

AGENTS、`workspaces/arch03/IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`、本检查点、`handoff/team/STATUS.json`。用户架构图已保存为`workspaces/arch03/assets/N1_N2_D1_D2_ARCHITECTURE_20261113.jpg`。旧B计划只作历史。新硬限1.20mm²、80PE/32ICB/150MHz/共享写ACK发布不变。

## 已完成与事实

- 新计划/图及独立分支已建立。实现起点工作树干净；未继承旧硬件PASS到N1。
- PR#9固定50c1261f3f7fafe1531e05e023aadd926cefa24a，完整100条数据说明与转换脚本只读已核实；本轮数据代理负责导入到指定新路径，不整分支合并。
- 服务器hex_short_all已只读确认manifest100条/1200层，inventory SHA ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997。还没有本轮逐项核完4800实际HEX。
- 对应完整FLOAT ZIP预期SHA edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9；目录目前只有HEX/JSON，manifest来源仍队友D盘，服务器Desktop深度3内未发现原浮点zip/npz。本机ALL_SPEECH原float包只有单坐标，不能替代。N1整数/硬件可做，完整新精度未验，N1未验前不能开发N2。
- B0实际报告已在ced包`runs/systolic_b_backup_report01/report.json`完成，01/13 00:34与00:39读取：12活动/12功耗/1200 true；时间加权P=0.06983707361964885320248724W，E=0.0000142012898511016506547J/task，固定12平均30502.333333周期。system_power_verified仍false，独立时序面积原证据另行挂接；不是重新变成时序失败。
- 原报告进程293353已经结束并有完整report.json，不重新导出/重跑。原B power队列/归档/backup都完成。规划阶段客户端7167已关闭且windows确认无VNC/FileZilla。当前没有本轮新服务器任务、无待Return。

## 当前并行分工（共享工作树，禁止互相覆盖）

1. `/root/n1_rtl_audit`：真正实现新N1五个RTL文件：arch03_n1_systolic5x16、arch03_n1_requantize、arch03_n1_linear16x5、arch03_n1_decoder、arch03_n1_accel。旧B0文件不改，复用transport/SRAM wrapper。阵列端口名沿用，in_x70/in_w192/result_sum2560；linear外部load16容器/双result32不变，core.array层次保留，converted_total[0:79] signed33可观察。
2. `/root/n2_d1_feasibility`：本轮任务是N1压力测试，不做N2。新增tb_arch03_n1_systolic5x16和local_verify_n1_array；独立Python参考，seed7834a9f1，10000随机块及定向；每20块四行掩码，随机输出792000，不能把未运行或smoke当完整PASS。
3. `/root/requirements_plan_audit`：PR说明/转换器原样导入；新增n1_data/n1_codec/test_n1_data；group8独立解码/符号/total33检查，tile16与旧v3编码算法，固定12原float重数量化＋两极值源准备，软件测试。暂不远端、不提交Git。
4. root：计划/交接/分支、N1固件与本地集成/SoC工具、服务器数据审计/状态与统一排队；不改代理拥有的文件。

共同契约：layout00100004，NUMERIC_FORMAT000e0c20，global magic/version仍3343574b/00030000，32B头word7使用数值ID，word5/6仍23488/46976。N1版本4b575306，0x08c只读numeric，SHIFT只能10。N1只接新layout，旧固件/格式拒绝；debug同样标layout4但内部原tile16顺序，不默认v3。保持源码已验证transport SOURCE_CREDITS3。Vivado D:/Xilinx/Vivado/2018.3/bin；Python E:/fpga_race-two/.venv-kwt/Scripts/python.exe。

## 未完成与推进边界

当前N1 RTL/固件/数据适配/本地10000块均未通过；真实ASIC/E20314、100×12、门级、综合/时序/面积、活动/功耗也未开始。不可复制B0 PASS。B0未知活动功耗审核和100条完整float源仍缺。

下一步接收并集成代理新文件，运行本地数值/格式与阵列压力，建立新N1固件/SoC入口；恢复服务器前重读真实进程/锁/空间，再只做本轮未开始阶段。下一硬件N2/D1/D2在N1完整交接之前禁止实施。重要进展和压缩前续写本记录/CONTEXT_HANDOFF，不只依赖聊天摘要。
