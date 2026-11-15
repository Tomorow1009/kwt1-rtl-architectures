# S0只重链接恢复准备 — 2026-11-15 22:30

**22:33传输中：0e31e5b1977583070dbe4ba22e045455d5088834已push，独立包853文件/137模块闭包通过。当前唯一VNC输入exec78210，`local_runs/s0_finish_0e31e5b/transfer.ps1`共32行；勿并发输入或重跑。目标bundle light-light126-t80-s0-0e31e5b，manifest5dd2d2153435037c34026456879cd840fa6253c6dcf3c500d6c177b9c0ad67ab，payload9e7d9e2f347cbb13742d40cbb4274e4ffb2a022e7d9f623a7ae2387059696f07。传输只准备独立输入，不自动启动EDA。synth08启动器已本地准备，尚未部署/运行。**

恢复先读AGENTS、CONTEXT_HANDOFF、本文、STATUS以及有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`。T80桌面和旧八路禁止修改；S1–S4未开始。

## 真实终态和当前控制状态

- synth07/9ffb2a9父139859已在**22:20:13.543084 failed**退出；final DC148878结束。原锁22:22实查False。
- 三块映射全部完成，耗时：shared40.45153220905922秒、accelerator197.2824583069887秒、CPU770.6193923819821秒；三份完整cache.json已写，CPU后两子块module token一致检查通过。
- 最终链接130秒后因**同名工艺库从原目录和复制目录重复加载**失败：1578条`doesn't specify a unique library`，最终`Error: ARCH03_SYNTH_ABORT Unmapped/ambiguous leaf DRNQV2_12TR40`，退出1。没有可验收的最终面积/时序；失败结果不改成PASS。
- 固定失败state SHA **432940528a89c8d0239ccd5e92ee597fc3625312f23c05245123102030744405**。
- 源包manifest **d397b97768c6ce5089aeda32a5e2e22d50e30f0b5a34c6edfae12e71ea9988ba**；源运行`/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-9ffb2a9/runs/s0_synth07/t80_s0_synth`。
- 七项child ledger中前六项passed/exit0，仅final failed/exit1。characterization目录全部普通文件，已实际核查。
- 自动接续等待器143305正确停止，`ops-9ffb2a9/s0_synth07_followup_wait/result.json`为stopped，22:20:22.833347；**没有启动finish01**。旧守卫及启动器不再执行。
- 前台watcher147221已自行结束，VNC18874435/workspace3现Bash空闲；3975、33670、32926等全部输入结束。无当前EDA，无半截输入。板端转发91027保持；FileZilla未连接。实时恢复仍须检查。

## 本地已准备，尚未部署

1. `s0_partition_synth.top_script`改为使用DDC内原有的canonical工艺库路径；先核对新目录保留的三份DB与原DB逐字一致。仍保留新库副本用于交付/PT，不删除库，不更改corner/负载/约束。
2. 将最终链接及所有报告收集提取为`finalize`，普通完整流程继续调用同实现。
3. 新`s0_relink.py`只接收固定synth07失败：核对state/manifest/所有旧输入、精确错误集合、全部子进程终态、原seed、三份cache指纹/全部产物、实际编译器及库/端口预算，并重建三个compile脚本逐字核对。仅复制通过检查的缓存到独立新stage，不运行compile；重新最终link、子块一致性、全部面积/时序/结构报告。
4. `s0_server.py`新增互斥的`--reuse-blocks-run`和`--reuse-blocks-state-sha256`；原团队锁不变。新模块需加入独立853文件包，不编辑旧9ff包。
5. 报告保留原块耗时、cache来源、failed state、最终link耗时及seed恢复耗时。不得把缓存恢复时间当从零完整综合时间。
6. **23项相关检查、Python3.6语法通过；三个生成的块compile脚本与9ffb2a9逐字相同**。实际服务器cache预检和新link尚未执行。

## 下一步

- 提交/同步当前修复，生成新独立包；当前准备的是`s0_synth08`（尚未启动）。注册9ff源缓存包及05c原seed包作为明确runtime evidence；不能重启synth07或旧finish等待器。
- 新运行先验证缓存，再持原锁只做finalize；保留旧失败全部文件。
- 成功后读取新最终summary的面积/时序/宏/子块，准备与新包和synth08一致的新finish守卫，随后gate14、SAIF12、timing/DRC、PT12。
- `S0_BUILD_REPORT_REQUEST_20261115.py`目前固定9ff/finish01，是本地准备物，**因synth07失败现在不能执行**。待新包成功后更新指向新final/queue；原T80请求SHA仍有效，见S0_SYNTH07_RUNNING检查点。
- S0自身报告/活动模型说明及冻结完成后才进入S1。新/tmp结果最终仍需持久归档。

旧synth03无效set_map_only、synth05设计重名、synth06短探针失败以及N1/R4可恢复编译缓存归档全部保留，详先前检查点。此次没有新清理操作；服务器桌面T80与旧八路保持不动。
