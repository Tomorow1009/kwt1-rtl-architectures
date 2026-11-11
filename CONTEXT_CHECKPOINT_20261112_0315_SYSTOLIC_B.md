# 2026-11-12 03:15：B综合因磁盘满中止，保留现场

## 有效任务和恢复要求

继续直接5×16脉动B，A取消、R4冻结保底。用户已恢复执行并确认开发板上电接网；板端VNC连接正常。有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`，08:00功能收敛、09:30:41硬冻结、11/13 17:00交付整理。压缩后先读AGENTS、根交接、本文件、02:16检查点全部增量、计划和STATUS。VNC只用workspace3，不碰workspace4；不删历史证据、不续旧8/R1、不复制旧PASS。

## 已完成（与本次失败独立）

- 生产63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86的真实ASIC/E20314例354816输出及IRQ/WFI全部通过，12层平均30502.333333周期、4917.656573task/s（150MHz折算）。summary SHA614d9f605996c9dfb302add53254461c62d7ec3c295fdc003c7964b6233a5d5d。该功能结论不因磁盘失败改成失败，但不能证明新PPA。
- 本地READ_LATENCY2的18任务456192输出、门级端口观察夹具6任务152064输出、两例调度计数50688输出均已通过；不冒充E203或映射门级。
- caad8de工具包已FileZilla上传/解包/716输入三固件核验，路径/哈希见02:16检查点02:44段；原35d包是原验证队列所属包，63da包是原综合所属包。
- 69d042b已同步报告导出器；04b5830e86a1d2414d0f1d6e31df37b2f7ad8b9d已push并ls-remote一致，包含冻结后串行队列草稿。报告2项、队列3项定向检查通过，尚未服务器部署。队列要求独立绑定实际阶段的冻结审阅，不会自动批准时序/面积。

## 实际磁盘失败及不能重复的作业

服务器bundles父目录：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`。

1. 原综合`light-light126-systolic-b-v3-20261111_211137-63da6ba0d6d9/runs/systolic_b_v3_synth01/systolic_b_synth`，driver75738/child79637，开始01:14:15.533251。02:59:34还在requantize映射，99.5%CPU；**03:10:44两个PID已不在ps中**。DC日志295188B，尾部正常退出统计CPU6110s/elapsed6193s，但错误为`Could not open output redirect file "check_design_mapped.rpt" (CMD-015)`、`ARCH03_SYNTH_ABORT`。launcher明确`OSError: [Errno 28] No space left on device`写`state.tmp`失败。
2. **原state.json仍是running，是保存失败后的过期状态，不代表进程还活着。** 不改写旧state，不直接按它重启同名作业。锁已不存在，不是本轮删除的。03:13:50实际检查：summary.json、mapped.v/ddc/sdc、metrics.txt、area_inventory.json、area_basis.json、check_timing.rpt全部不存在。因此没有最终网表或PPA可复用，空间恢复后必须新session重新综合，不能伪造报告或从旧v2继承。
3. 原验证队列`35d8ae1.../runs/systolic_b_v3_validation01_queue`，PID103191也已不在ps中。03:15:37 state仍waiting_synthesis，launcher无可见末尾内容，当前没有真实CPU恢复/竞争、tinySAIF、时序诊断或gate14通过记录。不能把旧等待状态当运行；后继必须在空间/进程/锁重新核对后新建，不续这个队列。
4. 03:13:50本目录所在文件系统可用3451912192B（约3.215GiB），inode6743198，说明不是inode耗尽。不能推断其他用户是否正在释放空间；本轮没有删除/移动服务器文件。

已通过异步问题请用户协调共享盘至少12GiB可用空间（不要求新增存储），尚未收到答复。后续核对现有batch初始守卫为1200×8MiB×1.2+2GiB，即13.25GiB，因此完整批量实际需要超过该值；已在评论补充16GiB更稳妥，不擅自放宽守卫。

**03:18:26.256057最新只读检查：可用降至2.5712890625GiB；账号s4_21usr没有common_shell/dc_shell/pt_shell/simv/vcs进程；/proc/75738、79637、103191全部不存在。35d只有validation01_queue及launcher.log，未创建任何后继诊断session。失败synth01目录仅257MiB，本轮没有删除任何数据。** `b_disk_processes.txt`已Return并读取截图，无待输入命令。不要把根交接下面的历史running当实时状态。

## 本地打包发现与修复（没有上传问题包）

- 04b包`light-light126-systolic-b-v3-20261112_030634-04b5830e86a1.zip`11421995B/720输入，SHAa625606a3163fd53f75e03382931c57eec906f5d0c040b3096371ca5eae47275；只在本地，未上板/上传。全部输入哈希和三固件自身校验通过，但不选作正式后继包。
- 原production固件manifest SHA11d860ca0269f962a71250e72925c730def0da79d931a79e3102c82ddaa16b91；04b包变为aa69257b1cf8feb324091aaf495c16454e91b05423c28d28691e727809aa0d36。JSON差异仅source_sha256里的ABI文档哈希；production ELF仍完全相同78599ba8a6f1bdf1a4002a4cb1ee1e53bad84bce88798f6e41a22e6189108827。因为最终报告要求同一固件清单，已将ABI文档恢复为63da受测原文，最新状态改在阶段报告中解释。不能放宽哈希检查来迁就文档更新。
- 比较64个广义生产文件时另发现installer差异只更新manifest描述（v2/v3能力），没有生成RTL接线差异；两份新diagnostic C文件属于原35d已新增路径，不是本轮修改生产硬件。最终应比较真实安装后RTL身份，不能把文件名筛选直接当受测硬件相同的全部证据。
- 打包器会把构建Python模块时产生的`__pycache__`一起按源目录前缀收进包。已改`package_systolic_b.py`：只允许精确Git导出文件和明确firmware/validated_data目录，排除生成缓存。旧包/运行全部保留；新包待提交后重新构建并实际验证无pyc、生产固件manifest恢复原哈希。不要修改已上传的不可变包。
- 当前未提交：ABI恢复、阶段报告解释、打包筛选修复、本检查点/根交接/STATUS；后继队列和报告工具已在04b云端。

## 未完成及下一步

实际B新综合/150MHz/面积、CPU恢复竞争、自己的1200、映射gate14、tinySAIF/R4交叉核对、B活动12/功耗、正式冻结和最终导出均未完成。当前功耗仍未取得，旧R4的71.8126mW/16.5724µJ不能当B结果。

先完成只读进程/空间核对与本地包修复、同步。服务器写入恢复前不启动新EDA/大批量，不删除证据，不重试旧session。空间足够后确认无其它作业/锁，再从同硬件新包建立独立synth02；不要重复已经过的ASIC14，除计划需要的clean14计数复现。新综合通过后才做其自己的诊断/gate/冻结/1200/SAIF。未能满足硬性条件则继续保留R4赛事资格。

现场：板端helper`F:/linux_fpga_try/ac820.ps1`、VNC18874435/class Vncviewer，workspace3 cwd为caad包；FileZilla关闭，无传输，无本地仿真或打包进程。最近本地打包session13741已成功结束。没有CUA会话。服务器可能因空间协调变化，任何状态都必须重新读。
