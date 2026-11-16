# C32-A：完整验证队列结束，导出与模型审阅进行中

最后观察：2026-11-17 02:20:48（北京时间）。恢复后读AGENTS、有效计划、根交接、本检查点及STATUS。以下PID仅为最后观察，先核对实际进程，不重启已完成队列。

## 有效范围及已完成

- 用户计划：`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。
- S0/P80/C80已冻结；当前C32-A自己的本地14、10000随机＋32定向、两拍/恢复、ASIC14、CPU恢复/竞争、新三块综合、240任务/FLOAT20、同网表门级14、SAIF12、独立timing/DRC查询、PT12全部完成。
- 正式批量仅20×12=240、6082560输出及total零差异。固定12单独为866152总周期、平均72179.3333333、150MHz折算2078.1571826 task/s。不能混用240平均70929.4083333。
- 精度最大逐层NRMSE0.20198143836753799%，最大任务0.20953408931848963%，裁剪/饱和0。不是官方600。
- 保守项目面积0.722402954997787mm²，明确新增0.5618935446998727，整机4.244619443828；220宏/0锁存器。setup+0.0000524521ns、hold+0.0010598ns，SS/.99V/125°C、6.666666ns。最终声明条件结论仍待模型审阅。
- SAIF12：304128输出、761444514B，完整周期全部匹配门级/ASIC；无SDF，内部total另由自己的ASIC240核对。
- PT12初步整机时间加权功耗W **0.04897383731730862481412038534**，平均J/task **0.00002356599049899043666325**。比C80功耗低11.547824%、能耗低9.573191%，吞吐低2.183681%、面积低24.838644%。数值已机器核验，最终阶段尚未验收/冻结。

## 当前唯一活动进程

ROOT=`/tmp/s4_21usr_c32_20261116_2010`；BUNDLE=`ROOT/light-light126-c32-91135f6`。

- **finish03已自然完成退出**：原父308692、最后子35079都已退出。终态`BUNDLE/runs/c32_finish03/state.json` SHA **6b11814712c7b5580f2dc47c8f3c743736e77cdc2dd1fbe66ba9f2a53b90f09c**，17阶段齐全，status=reports_ready_review_required。不要再启动它，也不要重跑任何已完成阶段。
- **export_review03已启动**：父PID **36287**，2026-11-17T02:16:43.092249启动；02:20:48状态exporting、无error。报告导出子PID **36484**最近仍存活。原finish03的v4状态工具只会显示已完成队列，不能据此误判当前没有工作。
- 控制目录`ROOT/c32_export_review03`；状态`state.json`，进程/退出回执为`*_process.json`/`*_exit.json`；主日志`ROOT/c32_export_review03.log`，启动回执`ROOT/c32_export_review03_launch.json`。
- 工具`ROOT/c32_export_review03_tool.py` SHA **86247880c807fe298943b8a4913fa80fa5fd3a83fe6b62c739665deaec7d7dfc**。**已执行，不重复启动。** 启动前已断言本工具哈希、finish成功终态SHA、17阶段及原父退出；输出目录使用exclusive创建。
- 本工具顺序：报告`BUNDLE/runs/c32_report01/c32_report` → 未知活动清单`BUNDLE/runs/c32_unknown_inventory01` → 原协作锁下查询本版DDC连接`BUNDLE/runs/c32_unknown_connections01` → aliases与model_review_snapshot。它只收集事实，不自动批准验收。
- 连接查询会按原协作锁等待；共享盘01:27仍仅1048576B可用。全部大产物在/tmp，最近69.52GiB。若等锁/空间，不重启、不清锁、不绕过原机制。
- 当前GUI窗口18874435、workspace3第一终端空闲，无活跃输入。恢复先重新查windows，不用workspace4。最后GUI命令已全部结束。

## 身份与重要哈希

- 受测包91135f61c97c980039793c6637d0a06888638df0；生产RTL61246bb2a21c56a9bfd871fd68de93028d79f5fd，后续仅竞争固件旧五行检查修正。manifest **d877234086f471acb3c7f4ea0c69bb280606d6bbb45fdd212e8bf30366b316c7**；payload **bc73ccd413657fd527628be76f5973de10f8cc30705580c3d5970ccbaed143bc**。
- initial03成功终态 **37e1279f0c165b6fb50493c4d87edb2a994e159a90e22e48b92c41ef8ab500c0**；批量 **2b51abd8844c73e342487e0be3e69c3cccfa4528296ef01ba15f1dca22621e81**；精度 **ca5a8e3afdac539bcad08367611cf38c5c602754c5eddf152e307be13e4775ca**。
- 综合 **ee08629b7cc9181d6e6db4ae21205ae931c6b1fe28f5c4420afd83097e8cef87**；门级 **fde3abb19c8de0f4de3329141109783ad02135408c91b226382e89100cefdb7f**；SAIF **7a9cdba2de2efcbe131b08071076202eaf27e86731a468e0e3c8661466e6353f**。
- timing **968a02165572b84192c141dfd492062b7e975062150c7da216341fa3b4390543**；DRC **e345c6a1326fc33e3a00f313efdd32d06a82af602e4740ee8877d03897e44034**；结构 **e7c2a91b88ce496776f59a110f91b60bec08d1969f5dc0aefb4d18d08ccfb7eb**。以上均已机器核验。
- 功耗完整数值/单位/映射证据：`handoff/team/evidence/C32_POWER12_20261117.json`。237428直接映射+1274孤立默认=238702，未注释0；全部12层单位、settings、toggle/static probability、时钟与220宏覆盖一致。不是未知驻留影响的物理误差证明。

## 待完成与下一步

1. 跟进已启动export_review03，不再使用旧export01/02。报告完整导出后读取JSON/CSV/中文路径及实际哈希；检查子进程与日志，不重复启动。
2. 全12未知活动/连接/aliases和model_review_snapshot完成后，独立审核本版事实，形成声明稳定任务模式、保守面积及布局前功耗的阶段结论。保留静态JTAG、X/Z合并、X跳变因子0.5和无SDF边界，不称物理签核。
3. 原始运行保留，整理归档并回读。当前尚无C32持久副本；共享盘空间不足时不得虚构备份或删除受保护数据强行复制。用户计划不要求用额外第二份持久副本替代技术验收，不擅自增加阻断条件。
4. C32-A报告/冻结完成后才评估C32-B缓存及G32。当前没有开始这两个硬件阶段，不自动运行100条。

## 失败、尝试及保护

- initial01/finish01/finish02均为锁创建ENOSPC，保留、零子任务、不重启。initial02是竞争固件遗留五行检查，91135f6已修复后initial03通过，旧失败保留。
- 空间恢复19/20/22/23/24/25全部完成，不重复。归档原件完整性及逐项哈希已核验，保留其回执。用户确认没有团队持续写共享盘，不再询问相同问题。
- 桌面T80_Delivery_20261113、全部旧八路数据、S0/P80/C80冻结运行及备份不写、不移、不删。FileZilla代理DNS检查失败未绕过，当前通过可见VNC操作。
- 本轮只读diagnostic哈希曾抄错，断言拒绝后按十进制字节重读并核验；临时complete_cycles键名错误改为cycles；截图会话未结束时读取文件失败，等待完成后成功。均未修改受测输入或重跑队列。
- 本地历史未追踪`handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py`不提交、不执行。

本地`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`，最近已push2a3862f；本次完整功耗及新检查点随后同步。原详细检查点`CONTEXT_CHECKPOINT_20261117_C32_FINISH.md`和11月16日SERVER文件保留。不要启动子代理或新goal。

## 02:37报告与活动扫描更新

02:32:35通过可见VNC机器断言确认完整报告已生成：`runs/c32_report01/c32_report`下有JSON、逐任务/汇总CSV、中文说明和回执。report SHA为`4f4be422643e0123ec40ff106d3750237e1e1ed79d7c9869b22a590c7a6dc7d7`，网表SHA为`3c116d5a026b7e832030cd0c5a8def5a633ade9eaefb4efd1080851acc4bbd2c`，功耗和能耗原始值再次断言一致。固定12精度最大逐层NRMSE为0.1425636423408142%；20条精度另列，不混用。

02:37:33父36287仍运行、无error；导出子36484已退出，未知活动清单子42011正在读取L09。随后仍需本版DDC连接与model_review_snapshot，未启动C32-B/G32。原始报告保留采集阶段的review=false，最终独立结论另记，不覆盖原报告。证据见`handoff/team/evidence/C32_REPORT_OUTPUT_20261117.json`。最近已同步Git提交f88564d；本次新观察待同步。已完成队列、工具及清理均不重复执行。
