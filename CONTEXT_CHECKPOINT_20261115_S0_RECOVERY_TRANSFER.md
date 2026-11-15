# S0 synth03失败后增量恢复准备 — 2026-11-15 21:05

**21:22当前唯一输入exec1192**：14行`local_runs/s0_recovery_launch_e2db114/transfer.ps1`，完成后自动运行已测试的N1竞争csrc归档并尝试synth05。源e2db114已push，脚本SHAcd0261c40066cd2b013409d0d8bc1efa171fc2a48e806d72ab257dfebcc43f74。服务器目标ops-a5ce90a/s0_recovery_launch_e2db114.py。不要并发输入或重跑；先收完最后截图takeover_local/s0_recovery_launch_e2db114.png，核对归档回执和synth05实际PID/state。尚未观察实际归档或新EDA成功。

**21:20当前：所有输入33855/16016均已结束。新包852文件核验及服务器verify_seed严格预检实际通过；synth04父120765启动后在原共享锁mkdir时ENOSPC失败，DC未启动。VNC当前Bash空闲，无EDA，旧失败03及新失败04均保留。** 已只读选中旧N1已通过的竞争测试普通csrc缓存35文件/10,651,815B：`IC/light-light126-undergrad-d2-20261109/bundles/light-light126-n1-v4-20261113_013211-9305c6948c76/runs/n1_contention01/n1_contention/csrc`。本地准备S0_RECOVERY_SPACE_LAUNCH_20261115.py，只对该缓存tar.gz全成员SHA/大小回读后去掉重复普通文件，保留目录/符号链接/原结果，并把压缩包返回原stage；随后新session=s0_synth05。临时35文件夹具完整归档/回读/结果不变检查通过，实际清理及synth05**尚未执行**。桌面T80和旧8路不涉及。

**21:14当前状态：exec33855已70/70结束，服务器S0_INPUTS_PREPARED确认852文件与6d40f4d6…清单相符，S0_NEXT_TOOLS_READY确认没有自动EDA。现在唯一输入exec16016，正在传输12行`local_runs/s0_recovery_launch_b58251a/transfer.ps1`。它结束后会自动执行新synth04启动器的严格预检，全部通过才起新作业。不要并发输入或再次启动。** 启动器SHA3d4faf1840f98de5116ba471c4e6d63b7463be4d1edcb2cf67e1e3e3d319a153，源提交b58251a已push；服务器脚本ops-a5ce90a/s0_recovery_launch_b58251a.py。先收完截图`takeover_local/s0_recovery_launch_b58251a.png`，再查s0_synth04实际PID/state，尚未观察启动成功。

恢复先读AGENTS、当前计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`及本文件。最终路线S0→P80→C80→C32→G32不变；服务器桌面T80及全部旧8路不动。S1–S4未开始。

## 当前唯一正在输入的任务

**exec33855正在VNC传输70行a5ce90a独立工具包**，`local_runs/s0_finish_a5ce90a/transfer.ps1`；状态同目录`transfer_state.json`。最近读取8/70，不能同时向VNC输入或重复传输。前台是Bash完整here-doc；传完只复制/核验输入，不自动启动EDA。最后截图`E:/fpga_race-two/takeover_local/s0_finish_a5ce90a.png`。

VNC18874435/workspace3；旧tcsh未闭合输入不碰，workspace4不碰。只读watcher91575已随原作业失败退出。板端转发91027保持，FileZilla关闭。工具F:/linux_fpga_try/ac820.ps1；所有服务端动作仍经可见VNC。除33855外无未完输入/exec。

## 原作业真实终态

- 原包`/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-05c923f`。
- manifest `4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2`。
- `runs/s0_synth03/state.json`：20:49:56.234720 failed；父75787、DC76822均已退出，CPU块未启动。
- 固定失败state SHA **83a9b896cb541a0631f7888ea796a10a5dcd7fe863b2fdeb91756a57e0e3783d**，已分16字符段读取核对。
- 原共享锁已释放，20:57:58 EDA=[]；/tmp98,378,182,656B、shared1,048,576B，后续须重新读取。
- shared_sram独立DDC完成；accelerator耗时4438秒并输出mapped.ddc/v/sdc，但其日志有两条Error，**不是已通过块**。

错误唯一来源是从旧mapped顶层导出的`set_map_only [get_cells U2055]`和`set_map_only [get_cells U2048]`；原linked RTL没有这两个对象，产生两条UID-95及两条CMD-036。运行器即使exit0仍拒绝，保留正确。旧失败目录完全不改，不用其结果直接当PASS，不重启原队列。

## 本地完成与新工具身份

- 新工具提交 **a5ce90ae4a967f0fddb12e3185fda5444ef9964f 已push**。
- 新包目标`/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-a5ce90a`，ops=`ops-a5ce90a`；852文件。
- 新manifest **6d40f4d67fc94a3b10fe3e1ece27076cf7affc33297602078721397165ca8d78**。
- payload SHA **0cc8b2474d39d038e831c5cd7f653a0a79c971d3f45f44f1906627f46f94b5dd**。
- delta SHA **e82ec3ad00a8f237632996eec639270ac250112fd4318974b9b7a5bd767d11a9**；基于已部署774的payload构建，不能从05c重建此delta。
- 本地全文件清单及136模块静态闭包/Python3.6语法/与受测源码字节相同均通过。
- 20项恢复/分块/来源/报告/复制/队列测试通过；之前拼接漏加号已修复并重跑，失败属于本地工具不是服务器新运行。
- S0功耗未知清单和可选诊断显式身份已实现，26项相关测试通过，纳入新包。7156303/e55c1c8本地候选未部署；e55补齐审核依赖，a5包含全部修复。

新流程保留原始characterize脚本，只去掉严格匹配的旧U编号set_map_only；时钟/端口/负载/延迟预算不变。DC必须先在原linked RTL证明对象不存在，存在或新格式即失败。可选恢复只接受上述精确失败状态/输入/错误日志，加载其DDC作为**未验收起点**，在新目录重新incremental compile、hold及完整报告，再继续CPU和顶层。默认块脚本已与05c旧版逐字比较一致。新run会记录失败输入全部哈希；旧状态不改。不可用“清掉日志Error”代替新编译。

## 启动器与下一步

`handoff/team/evidence/S0_RECOVERY_LAUNCH_20261115.py`已本地准备、Python3.6语法通过，**未传输、未执行**；其固定852manifest及失败state，启动唯一新`s0_synth04`并注册旧05c为只读证据。没有删除、归档或清锁动作。新lock如ENOSPC则保留失败，不重复同session。

1. 先收完exec33855并看最后截图，核对852及manifest，未观察前不能标部署通过。
2. 新包实际import/verify_seed只读预检；若不通过，修本地新包，不修改已传输源码。
3. 提交/同步启动器，然后单独传入ops新文件并执行一次，记录真实PID/state。不要重复synth03或617旧finish launcher。
4. 新synth04完成后必须先读面积/setup/hold/220宏/约束/结构/child identity，再决定同网表gate14/SAIF12/PT12。
5. 收尾工具774仍在但未启动。617cf17的固定synth03完成启动器已过时，**不可执行**；新网表成功后按新摘要另建启动器和request。
6. 全部S0报告/冻结后才进入P80。既有T80 ASIC14/240同源引用；新最终网表门级/功耗必须自己跑。原桌面交付和旧8路始终不写。

前序归档、失败cap01–03/synth01–02、工具传输及完整路径见S0_NEXT_TOOLS_TRANSFER和S0_SYNTH03_DEPLOY检查点，不重复执行已完成清理。新/tmp结果仍需最终持久归档，目前未交付。
