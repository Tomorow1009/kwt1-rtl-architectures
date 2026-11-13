# T80优先：取消G64、综合已完成 — 2026-11-13 20:14

**先读新有效计划`workspaces/arch03/T80_PRIORITY_COMPLETION_PLAN_20261113.md`。用户已取消G64；T64全部现有成果保留，但不得再占用T80推进时间，必要时放弃T64。当前只完成T80。旧8路全部资料不删、不覆盖、不归档后删原件。**

## 原任务与初步结果

- T80原综合已自然完成，受测RTL仍876b883。20:10对summary和mapped.v/metrics/area_inventory/latch/check_timing逐个SHA校验后读取：预算上界0.9521382079004799mm²，known-added0.7914963391005749mm²；setup+0.000576019ns、hold+0.00623399ns，6.666666ns；220宏（92小+128大），0latch，无组合环。**只是初步数字，尚未完整验收。** 详`handoff/team/evidence/T80_SYNTH_PRELIMINARY_20261113.json`。
- synth summary SHA **c485b3f77cd7c4f9d7911c5e2052babbc2d8c83811b94ec72c608ffed027f341**；mapped.v SHA **6a9ab02be889d4aecb55576a71c51ce68f324fc8a0897430e0dbe40a1373eff2**。
- 原队列`t80_finish02`仍自然执行。**20:10:49.980968实读running/t80_gate，driver14008、child151885、completed6、errorNone、free10540285952B。** 已完成contention、sequence、synth、timing_audit、drc_audit、structure；三个诊断完成不自动代表审阅通过。后续SAIF12、power12和precision仍原队列负责。
- 门级进度查询刚发送并完成Return，命令`takeover_local/t80_gate_progress_cmd.txt`；下一步截图读输出，不要重复启动门级。

## 交接尝试：没有暂停任何实际任务

- 用户图片建议安全冻结父调度、合并gate/SAIF、逐层功耗及有限并发。本轮先核实父14008与综合驱动23158在do_wait、DC29185运行、锁属于23158；start ticks分别189690906/189704644/189738560。
- 准备了仅SIGSTOP父14008的可逆脚本`local_runs/t80_pause_dispatch_2007.py`。**实际执行时DC29185已经退出，身份读取在发送任何信号之前报FileNotFoundError，故没有发SIGSTOP，没有暂停父/子，也没有创建交接目录。** 不得按旧PID重试，不得声称父队列已冻结。
- 原队列已自动进入门级，此时替换合并入口可能重复已开始工作；保留原队列。尚未实现或启动新的并行/合并采集调度。需根据门级实际进度再判断是否有收益，不能为了新调度拖延当前结果。

## 临时盘退路

- 共享空间下降，未删除任何文件。已仅复制833个manifest文件（不复制runs、不移动活跃任务）到 **/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-v4-9196556-delta03**，manifest仍fcbac79ce3be1446a1c0055a7dad51428a4dcdea7d98bfe0b7fab717d9d3112d。
- 20:13:23截图确认`T80_RUNTIME_SOURCE_READY`，uid14021、root_mode00700、source_only=true、live_runs_copied=false、job_started=false。完整回执`/tmp/s4_21usr_t80_20261113_2012/clone_receipt.json`。**尚未实际调用t80_paths.configure做Linux路径预检。** 用作后续新阶段空间不足时的退路，不改变当前原队列。临时结果必须最终归档回持久存储。
- 新副本脚本`local_runs/prepare_t80_runtime_2012.py`；传输exec72912已全部完成，exec10657失败的冻结尝试、75040初步指标和52615身份查询也都结束。无待输入/Return。

## 恢复入口

工作树`E:/fpga_race-two/kwt1-t80-t64-g64`，分支codex/light-light126/n1-t80-t64-g64-20261113。最近已push cf969b6；新计划、初步指标及本检查点待提交同步。

VNC18874436、FZ20972102，恢复先windows。只用workspace3，终端cwd仍`PROJECT/bundles/light-light126-t80-v4-20261113_165244-876b883d9519-delta01`。FZ断开，不碰workspace4。授权板端helper为F:/linux_fpga_try/ac820.ps1；勿建立隐蔽服务器通道。

优先：读取原gate进度；审阅同网表constraints/诊断结果；持续原队列或经核验的安全接续；收齐T80自己12活动/功耗和20条精度。T64/G64不得恢复。现有report/unknown ops仍为d611597（8文件/669837...）；T64最新4bbd0af ops只保留，不启动。

PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109；原共享锁仍在上级IC/.arch02_team_lock。任何阶段失败、停止或未验证事项如实保留。
