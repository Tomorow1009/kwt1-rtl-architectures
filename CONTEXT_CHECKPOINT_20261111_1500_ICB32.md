# 2026-11-11 15:00：原8路完整功耗L01完成，L02 v2运行

压缩后先读AGENTS、有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`、本检查点及14:35检查点。用户要求持续推进，不逐步等待。R4最终1200/报告/交付包已完成，不重跑、不修改RTL。R1 ASIC14/综合已完成，新门级尚未启动，仍受可用磁盘空间限制。

## 新完成和当前作业

- 原8路L01已14:46:48.307203正常完成。session `mmio8_fullpower_l01_v1`，PID293690结束；summary SHA `f639d2dfe8c4c6dbd263d5a0851afc5d1e3e883c51ee28a6bbf966101d621f01`。独立`mmio8_power_numbers.extract`核验全部报告后生成`mmio8_power/numbers_v1.json`，SHA `799a02a447102f14e5da0fc40979a4387b15f107a092cb978006769028b54c26`。
- L01整机总功耗19.939132mW、能耗510.856594987482µJ，完整窗口25620804.104586ns，3843121周期。SRAM138个=32ITCM+32DTCM+64共享+10加速器。112585 nets全部注释，17178不变点全部注释；这不代表未知活动影响审核通过，system_power_verified仍false。数值来自本次全14gate对应波形，不复用旧单层摘要。
- 第二层第一次启动`mmio8_fullpower_l02_v1`/PID313115因启动文本宽泛替换把`full01`误改成不存在的`full02`，读取gate摘要即退出，未进入PT；原失败目录和日志保留，锁正常释放。已修为只替换session和case字面值。
- **当前唯一EDA作业为`mmio8_fullpower_l02_v2`，PID323693，开始14:57:38.893275。** 14:58:48.075132核对running/errorNone、锁对应同PID/session/bundle、PT尚在输入预检。原ecf3包、正确`runs/mmio8_source_gate_full01/mmio8_gate`、gate SHA `06e388e1b744494fc00f224a43caf8de2ebf7e764eb1b655541ce7288a408533`。不得重复L02。

## 磁盘和后继准备

14:51 free22.247GiB，14:58 free17.0908GiB。完整R1综合目录425MiB；旧8 L01新增11MiB；R4每层功耗目录16MiB。磁盘下降原因尚不清楚，不归责其他作业、不删除历史。已有波形功耗采用4GiB可用空间预留；新R1波形仍独立预算，不因小报告体积而盲降其门槛。

新增外置`workspaces/arch03/scripts/mmio8_power_queue.py`准备在L02成功后串行L03–L12。等待原L02固定PID+start；校验其通过回执；每层使用现有server_run的协作锁，空间不足4GiB时等候；任何失败保留现场且不重试。每层直接读取原波形，提取真实数值，不再仿真。不修改ecf3不可变输入。Python3.6语法和前驱身份/摘要变化拒绝检查通过。

**15:00队列还未上传或运行。** 待提交脚本、打小操作包，经已授权Linux FileZilla上传独立目录，服务器核验后启动。FileZilla刚在板端启动，VNC窗口20971587第三终端shell/cwd964；原L02后台运行。没有CUA会话或本地长任务。最新云端仍464f4856a52e5a85ecae2c8dd9f19fc10a693387，当前脚本/证据/本检查点待同步。

## 仍缺与下一步

继续L02→L03–L12原8路功耗；齐12后用已修正1ns ASIC/gate相位差的报告工具导出同配置对照，不能套R4宏数/周期。R1门级/功耗在空间预算允许后另评估；当前只报已取得ASIC和综合初筛。R4系统功耗未知影响审核、官方600、物理签核仍未验。正式赛事入口/附件限制/队名署名及附加存储信息问题仍待回复，不重复问、不阻塞其他工作。R4交付入口`workspaces/arch03/ICB32_DELIVERY_20261111.md`。
