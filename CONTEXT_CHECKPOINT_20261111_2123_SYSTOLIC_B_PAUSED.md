# 2026-11-11 21:23：用户下电前暂停，直接脉动B交接

## 当前要求与恢复入口

用户明确暂停：开发板准备下电，关闭板端两个程序，电脑端准备暂停，远端已有任务继续。未经用户再次继续，不恢复连接、上传或启动验证。仍按直接5×16脉动B计划，A取消，R4冻结保底。

恢复先读AGENTS.md、CONTEXT_HANDOFF.md、本文件、20:55检查点全部增量、`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`及STATUS的systolic_b_execution。H0=11/11 19:30:41；原收敛11/12 08:00、硬冻结09:30:41、交付11/13 17:00。暂停不自动延长赛事截止，恢复核对剩余时间。

## 已完成暂停

- FileZilla密码框用Escape取消，未提交登录、未开始新包上传；随后Ctrl+Q退出。
- VNC通过F8菜单的Exit viewer退出，仅断开客户端；未向远端终端发送退出、Ctrl+C或停止作业指令。
- 21:22板端窗口清单确认FileZilla和Vncviewer均消失，远端桌面未关停。
- 21:23电脑端没有Python验证或Vivado/xsim/xelab/xvlog任务；只有项目`contest_links_dns.py ftp` PID21036和`vnc` PID11340。核对完整命令身份后已停止二者，再查没有这些本地任务。
- 没有执行开发板系统shutdown，不声称文件系统已卸载。用户自行安排下电。
- 暂停记录保存在本地，尚未提交/云同步；硬件和工具63da6ba在暂停前已推送及独立核对。

## 实现及验证范围

当前提交 **63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86**，私人分支`codex/light-light126/undergrad-d1-numerics`。旧R4受测文件未改。

B已实现80PE脉动、60个X宏、32个W双bank宏、双80结果区、双结果32位写回、32字FIFO、真实共享写ACK后发布和IRQ/WFI。v3无损编码、W0/b→X→后续W加载、首五行提前算、原子响应缓冲和逐物理宏加载仲裁已接通。保留v2，明确布局/能力检查。source credits=3只改变调度额度，仍原32位单在途ICB及相同源服务时序。

新v3本地14例354816输出通过，12层平均 **30502.333333周期 / 4917.656573task/s**（150MHz折算、pin_mock无E203、非芯片实测）。v2兼容14、v3反压/故障/取消无复位恢复、debug、生产观察器夹具及固件编译核验通过。v2核心READ_LATENCY2通过；v3加载重叠READ_LATENCY2尚未独立验证。全部本地仿真已结束。

证据见`handoff/team/evidence/SYSTOLIC_B_V3_INTEGRATION_20261111.json`和`SYSTOLIC_B_CODEC_V3_20261111.json`，目录明细见20:55检查点。**新63da6ba还没有实际CPU、综合、门级或功耗PASS。**

旧B/v2 e11c317已实际ASIC/E20314例354816输出及IRQ/WFI通过，12层36862周期/4069.231task/s。它不能替代新版验收。R4自身1200/门级/活动保留，不重跑、不继承给B。

## 新包只到开发板，尚未上传FTP

`light-light126-systolic-b-v3-20261111_211137-63da6ba0d6d9.zip`：11197550字节、663输入，SHA256 **3433af44f5f80ec6c3b2d78a2a90accbf16d67dcd1312af981ef4045f391d0f2**。

- 本地repo `local_runs/`保留ZIP、展开目录和回执，从已提交LF源码重编IRQ固件。
- 板端`/opt/ac820-gui-root/root/`同名ZIP上传成功并核SHA。
- 另复制到`/home/root/systolic_b_v3_63da6ba/`再次核SHA；GUI目录`/home/board/systolic_b_v3_63da6ba/`。
- FTP目标仍`/IC/light-light126-undergrad-d2-20261109/`。**新v3从未上传比赛FTP，未服务器解包/运行。** 21:12暂存待核记录已由此更新。
- 恢复重新观察窗口和ID。FileZilla本地目录可能仍指v2，要改为v3唯一目录。凭据只经helper内部输入，不记录内容。

## 原服务器综合保留，当前终态未知

目录`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-systolic-b-v2-20261111_200441-e11c317c960b`。

作业`systolic_b_v2_synth01/systolic_b_synth`，driver **99451**、DC child **108110**。最后实际健康观察 **21:09:28.967388**：running，driver45:25、DC39:50、CPU99.7%、MEM3.1%，log23763B、mtime20:31:06，尾部Processing arch03_linear16x5_systolic。暂停没有重查终态，没有停止、重启或清锁。不能把21:09当21:23实时结论。

恢复首先核原state/进程/锁/空间并收结果，**不得重复launch**。新v3等原锁释放后串行排队。20:00 free148.094GiB只是历史。旧MMIO8 L02已自然通过，不续8/R1旧队列，不删证据。

## 尝试路径、缺口和下一步

- B/v2全X后算36862周期，比R4慢，结果保留。v3 credits16为35316.83周期；扫2/3/4/6/8/16后选3，已补完整14。不能用理论80PE峰值代替完整吞吐。
- v3平均31338.67B、保留共享写事务下界28341.33周期，7000不承诺，本轮不实现共享写旁路。
- 首次v3 pilot因TB仍旧布局坐标比较失败，已修观察器；monitor fixture漏layout_arg编译失败已修，失败目录保留。
- SAIF仅定位VCS `etc/ucli/saif.tcl`、`libmxsaif-0.a`和PT手册，未采集或交叉核功耗。最后VNC为SAIF Usage查询后的空闲shell、workspace3、无待执行文本。后续读Report/Region/Examples，禁止盲启大VCD。
- 恢复顺序：收原综合→新包FTP/服务器SHA及663输入核验→新v3 ASIC14及真实CPU恢复/竞争→新版综合/时序/面积→SAIF小夹具和R4 L01同窗口差≤1%→冻结B自己的1200、同网表gate14/activity12/PPA及报告。
- B batch/gate/SAIF/report入口仍需适配。新硬件不能继承旧PASS；按实际时限优先正确性与参赛资格，B未合格时交付保留R4。

## 21:52再次暂停

用户先说继续，随后立即再次要求暂停。期间只重读计划/检查点，并在21:51只读执行开发板status和windows：开发板已重新上电，uptime约1分钟，桌面正常；没有FileZilla或VNC窗口。未重启电脑端FTP/VNC辅助进程，未打开客户端、登录、上传或执行任何服务器命令，未启动本地开发/仿真任务。远端原综合没有被触碰，最后可用健康观察仍是21:09。新包仍为此前板端暂存状态，本次未重新核验重启后的文件。等待用户下一次明确继续。
