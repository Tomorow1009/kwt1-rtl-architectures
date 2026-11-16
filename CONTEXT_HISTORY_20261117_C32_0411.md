# C32-A修复恢复入口（03:44实际观察）

先读AGENTS.md、有效计划、本文和STATUS。有效计划为workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md，SHA 1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。路线S0→P80→C80→C32-A→可选C32-B→G32，当前只修复C32-A。

## 当前唯一服务器任务

- ROOT=/tmp/s4_21usr_c32_20261116_2010。
- 新工具包ROOT/light-light126-c32-repair-c7c7f6c，代码c7c7f6c3505ca54b90d1fa54893b925866d3c3ee；仅工具改动，RTL仍61246bb，竞争固件仍91135f6。
- manifest屏幕显示45448653c5cc0c1edc74598b1e9ec81a5567961e89850fc023c6d3d506e5f809，准备器按已提交工具字节、旧manifest及逐文件SHA机器验证后生成；此字符串人工转录尚需独立断言。
- GUI差量包SHA07dbf1b62ad6c16128909ed2b6c8be035edd15939033594b2eaeafc8424caa54；7工具文件，19097字符；本地逐字节往返及Python3.6语法检查通过。
- 修复父72614于03:39:20.358366启动；03:44:16.140201仍在WAIT_ORIGINAL_LOCK_STORAGE，尚无DC子进程，runs/c32_repair01尚不存在。不要重复启动。启动回执ROOT/c32_repair01_launch.json、request同前缀、日志ROOT/c32_repair01_launch.log。
- 恢复30 worker74341于03:43:12.405144启动，03:44未终态，日志无错误。只处理恢复29留下的663份已核验归档B0 task.csv副本（213048254B），获得原锁即停止。原始归档、日志、汇总、源码、活动、最终网表全保留；不要重复30或29。工具SHA b25320301ff5d4fb62bbf89419374b5afac23b6f4ef32f2602d94f3cbf72d2b8，源码handoff/team/evidence/C32_B0_ARCHIVED_CAPTURES_RECOVERY30_20261117.py。
- 最近空间03:27：共享1048576B，/tmp74567278592B；用户确认没有团队持续共享盘写入。当前状态不能用这个旧观察代替，恢复先查进程、原锁和space。
- 当前无GUI输入会话。VNC18874435/workspace3第一终端，实际操作前重查windows；不使用workspace4。

## 必须修复的真实问题

旧最终网表有326条max_transition违反记录，完整解析为三个网：core/n9882→U16528，n9916→U16527，n9950→U16523，均BUFV2RD_12TR40；上游分别n60014/n60013/n60011。要求1.35ns，实际约1.36–1.37ns。旧摘要“DRC0”是人工转录错误，已撤回，服务器原报告未修改。不能用正setup/hold代替DRC通过。

修复脚本仅尝试三个BUFV2RD→BUFV4RD：同库引脚/布尔功能等价，临时解除并恢复精确祖先保护，无compile、无拓扑/约束变更；全网表token与leaf证明只允许三个引用及对应面积变化。修复路线显式复用自身映射及原三块证明，绝不伪称新完成三块综合。26项相关测试通过（原25项＋修复身份拒绝测试）。源已提交推送c7c7f6c，后续2d1faef/d50ecfc/1e9ffe0待同步。

独立驱动检查inspect02已完成：57941/DC63231退出，summary SHA5fb1e75174bc4fa325963d1a2f394ac0767cc67a5af8c62664a78d3c36531781已机器核对。原export_review03因Unresolved C32 constraints失败退出，不重启；unknowninventory/connection/aliases旧网表查询完成，snapshot未生成。

## 已完成证据与边界

旧完整包ROOT/light-light126-c32-91135f6，manifest d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7。

- C32本地10000随机＋32定向、14例、1/2拍、ABA及取消恢复通过。
- ASIC14/恢复/CPU竞争通过；前20×12=240任务，6082560个输出和total逐项零差异。RTL未变，不重复这些。
- 同批浮点20最大逐层NRMSE0.20198143836753799%，固定12最大0.1425636423408142%；官方600未验。
- 固定12平均72179.3333333周期、2078.1571825730357 task/s（按150MHz折算）。
- 旧未合格网表保守项目0.722402954997787mm²、整机4.244619443828mm²；setup+0.0000524521ns/hold+0.0010598ns、220宏/0锁存器。
- 旧网表自己的门级14、SAIF12/PT12完成：时间加权48.9738373173mW、23.5659904990µJ/task，布局前估算。不得转移给修复网表或标为阶段验收。
- 旧报告runs/c32_report01/c32_report SHA4f4be422643e0123ec40ff106d3750237e1e1ed79d7c9869b22a590c7a6dc7d7；网表3c116d5a026b7e832030cd0c5a8def5a633ade9eaefb4efd1080851acc4bbd2c；synth summary ee08629b7cc9181d6e6db4ae21205ae931c6b1fe28f5c4420afd83097e8cef87。
- 初始各任务及精度哈希见C32_EVIDENCE_INDEX_20261117.md和对应JSON；最新状态以本文为准，旧索引中的“export运行中”已过时。

## 空间恢复历史

恢复26/27/28完成，不重复。26/27回执已机器断言；28 SHA dd6940df48aa7e24cd7e2c6d8d68d7cb4eecbb8ff66f0930dea08e366644ea45已机器断言。

恢复29在查询取得锁时停止：537份172434752B移除，剩663份。正确state SHA为a1170088c32ca7f91ac01916c351e96215dcdc1510b8f97ebd7fb7ebe35b8663（十进制分组重新读取；此前dccd/dcc转录错误不得沿用）。恢复30启动前机器核验此SHA和journal，不重跑29。归档为原B0 backups/systolic-b-20261112_2320/completed-evidence.tar.gz，SHA dbfd6e93ea6257995e61e6fce8bff0aaf0d0f9d47c0d33cc38d6ce08ea536a50；63653文件7006124866B完整回读证据保留。更早19/20/22/23/24/25均终态，见历史检查点。

## 下一步

1. 跟进原72614和74341，不重复启动，不清锁。核对新repair01终态、工具错误和token/leaf证明。
2. 若DRC转移到上游或setup/hold失败，保留该尝试，在新目录修复实际问题，不放宽约束；当前目标是完整32PE版本。
3. 若修复全部约束/面积/结构通过，用已准备的handoff/team/evidence/C32_FINISH_REPAIR01_20261117.py（未部署/未运行）启动新网表自己的gate14/SAIF12/PT12；不能继承旧finish03。运行前绑定新summary SHA，核对原锁和所有子进程。
4. 新最终网表的报告/模型审核需显式连接“原未变RTL功能批量＋等价映射修复＋新门级/PPA”；旧export03只支持同包旧网表链，不可直接重启。
5. 完成新审核、持久归档及C32-A冻结后，才继续可选C32-B/G32。当前C32没有持久归档，不虚构备份完成。

## 固定保护和同步

桌面T80_Delivery_20261113、旧八路全部数据、S0/P80/C80冻结运行及备份不写不移不删。保持原32位ICB四段真实传输、原共享写ACK/读回、X14/W12/b32/SHIFT10、150MHz/SS/.99V/125°C、项目≤1mm²。正式仅20条，100条未自动授权。不恢复旧8路/R1追加队列，不开发宽ICB/旁路/A版。

本地E:/fpga_race-two/kwt1-c32-g32-20261115，个人分支codex/light-light126/t80-pipeline-c32-g32-20261115；仅S0_SYNTH05_FINISH_LAUNCH_20261115.py未追踪历史文件勿提交/执行。禁止新增子代理或goal。更早详记保留CONTEXT_HISTORY_20261117_C32_0339.md。压缩后重新读计划和本文。
