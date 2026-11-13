# T80活动工具修复接续 — 2026-11-13 20:33

先读 `workspaces/arch03/T80_PRIORITY_COMPLETION_PLAN_20261113.md`。G64已取消；T64暂停，不占用T80资源。旧八路与所有历史证据禁止删除、覆盖或归档后删原件。

## 已完成

- 受测硬件仍876b883；T80 ASIC14、前20条240任务/6082560输出与total/saturated、竞争及恢复均已通过。固定12任务平均112569周期，150MHz折算1332.5160568 task/s。
- 原综合自然完成，初步预算面积上界0.9521382079004799mm²，setup +0.000576019ns、hold +0.00623399ns；220宏、0锁存、无组合环。严格警告/条件审核仍待完成。
- **同网表门级14已通过（无SDF）**。原运行 `PROJECT/bundles/light-light126-t80-v4-9196556-delta03/runs/t80_finish02_gate/t80_gate`；summary SHA `918d256b4081e116100169b33cabe7f977255b9f9194e43c08667208ce29df2c`。
- 20:28:55只读确认原队列PID14008不在、child=None、共享锁不存在。原队列20:22:45.012957退出FAILED，state SHA `5e3e269e207cf5783a1e230baf443e7cb6a68dc9f8efd03a4e63e81eab5af289`。没有人为停止综合或原队列。

## 失败与修复

- 原SAIF驱动167734于20:22:44.997271失败，**原因不是空间不足**：`native_saif_replay.capture_commands`调用旧icb32_power三段窗口校验，拒绝T80四段搬运。原始失败完整保留，未开始正式活动采集。
- 新提交cef81d4增加T80独立四段窗口验证；旧通用SAIF/PT函数仅增加显式window_reader参数，默认旧三段校验不变。T80采集、流式活动审核与PT建脚本全部显式传T80验证器，保留实际时间/ACK/排空检查。
- 本地16项活动/旧方法/契约测试通过；另新增工具差异克隆保护测试通过。第一次测试受Windows默认GBK影响，设置PYTHONUTF8后通过，不是RTL失败。
- 新接续仅允许7个活动工具差异，逐项哈希验证833文件；不允许改RTL、固件、数值/布局或库。原门级、综合、240任务不重跑。

## 正在部署（尚未启动新队列）

- 新目录 `/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4`，manifest `181bb96b719363be5350e9e968ac2b2ad29555e2f4606e362721be3c42629b9b`。
- 操作入口同根 `ops-cef81d4/t80_resume_evidence.py`，SHA `9f1cb186e74b59d59e15dce2358b7d773a999f05183cce24d7303e6c15bdf8ff`；request SHA `56ab33b3b472fdb72e3d9df91cbfba5da9294369c0ce07b36d276921fd8a39ad`。
- **VNC传输exec28932仍在运行，19行，state位于local_runs/t80_activity_fix_cef81d4/transfer_state.json。不得同时输入VNC。** 完成后截图确认`T80_ACTIVITY_FIX_PREFLIGHT_PASS`再启动。
- 原17df21b接续工具已部署并预检，因未包含窗口修复不再使用。原/tmp同字节源副本也保留。
- 新队列计划只继续SAIF12→power12→first20浮点精度关联。仍同共享锁、串行；未启用新的并行调度。临时盘证据最终需持久归档。

## 下一步

1. poll28932，读取可见预检回执；确认通过后用新ops在新session启动。
2. 审阅已生成timing_audit、drc_audit、structure，不能把诊断生成PASS当严格时序审核PASS。
3. 核对L01完整活动/实际窗口，再完成剩余层、功耗与精度；新工具不允许把finished时间当最后ACK。
4. 生成完整报告和未知活动审核。现有通用report入口尚未适配/tmp根，需要显式运行路径配置，不能假定可直接使用。
5. 同步代码及本记录到授权个人Git分支；不上传大数据/厂商库/凭据。

PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109。
VNC18874436、FileZilla20972102；恢复先windows，仅workspace3。板端helper F:/linux_fpga_try/ac820.ps1。原VNC终端cwd仍PROJECT/bundles/light-light126-t80-v4-20261113_165244-876b883d9519-delta01。
