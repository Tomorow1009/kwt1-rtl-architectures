# S0最终链接完成，验证入口修复 — 2026-11-15 22:58

**23:14:55最新实查：SRAM双清单核对已通过，当前gate已进入VCS编译子174044（已运行10秒），父172535、watcher173225继续，无错误。端口DC173089已完成26秒。全部输入结束，不重启；6683ce5已push。下一步等真实gate14结果，随后原队列SAIF12/timing/DRC/PT12。**

**23:12:55实查：66b9496/s0_finish03父172535运行，structure已完成、completed=1，当前gate端口DC子173089，无错误。开始23:11:48.772018。前台只读watcher173225；全部96034/10794/4606输入已结束，无半截输入。下一次命令前只退出该watcher，不碰后台队列或锁。综合仍是a5f138e/synth08，不重跑；T80桌面及旧八路不动。**

**23:10当前唯一输入exec10794：13行`local_runs/s0_finish04_launch_1881cd3/transfer.ps1`，启动器SHA3b20c94cc969816b8f171808b2c53a62fb9db9a6e2ae2e905fae6b362732a649。66b9496包853文件和manifest2afb9a79e600e4bd1a0493699b50d463f7df8ebef666d99290cde2efbf0426b4已服务器核验，96034输入结束。新目标66b9496/runs/s0_finish03，仍引用a5f138e/synth08已完成网表；尚未观察新PID。1881cd3已push。先收完输入，禁止并发VNC/重跑；下一个只读watch命令在local_runs/s0_finish03_watch_command.txt。最新report请求为S0_BUILD_REPORT_REQUEST04_20261115.py，未部署执行。**

**23:07新失败：finish02父168421在gate的SRAM配置来源核对停止，VCS尚未启动。门级DC端口探针子168925已正常完成27秒；不是数值失败。重链接当前header已被不可变`synthesis_inputs.json`记录，但旧gate仅查`source_inputs.json`。本地仅对明确S0 profile同时核对两份清单哈希、全部历史header、当前header和实际模型；冲突/缺失/任一字节变化仍拒绝，不修改完成综合的任何文件。3项新测试（含6种损坏情形）及2项来源路由测试通过。当前watcher169108已自然结束，Bash空闲、无EDA；全部旧失败保留。下一新工具包/finish03，不重跑synth08。**

**23:03:35实际进展：新a7e7e49/s0_finish02父168421已运行，structure完成，completed=1；当前gate/DC端口探针子168925（common_shell_ex，96%CPU），error=None。队列开始23:02:32.412418；明确使用a5f138e/synth08 summary e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916。所有29202/56347/87739输入已结束。VNC当前为前台只读watcher169108，不能向它盲输shell；仅需命令时Ctrl+C退出watcher，不碰后台队列。转发91027保持，T80桌面/旧八路不动。**

**23:02部署接续：a7e7e49修复包853文件/manifest4d0699ff21c1708484f182e09a934ea918255ddfc116f1f2a179ec7b015e8766已服务器核验，29202输入结束。当前唯一输入exec56347，13行`local_runs/s0_finish03_launch_bc0a897/transfer.ps1`，启动器SHA5650846f3f3c16aba83a87cb839ff456f102adf8692666f350ddf30c3ed7a9d7。bc0a897已push。目标新包runs/s0_finish02，明确引用a5f138e/synth08，注册a5+9ff+05原证据。尚未观察新PID，不要重复执行；收完截图后查新driver/state。`S0_BUILD_REPORT_REQUEST03_20261115.py`已按新包/finish02准备，但未部署执行。**

恢复先读AGENTS、当前用户计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`、本文和STATUS。服务器桌面T80、旧八路不改；S1–S4未开始。

## 已完成

- a5f138e独立包853文件和manifest已服务器核验：`c4774571c8aebe323657a5aaebc017f24324396b28ea6b2852e32e40a213b924`。
- `/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-a5f138e/runs/s0_synth08/t80_s0_synth`最终链接已正常完成。父163793/DC164078结束，22:55:16接续守卫观察passed。只复用经完整核对的9ff三块，不重复映射。
- summary SHA `e77fac98d9ab9032e431e8bcfe7d0e3d42f33d8b28222d37ceb48777c9bd4916`。
- 新最终报告：保守项目面积0.9535222591004618 mm²，明确新增部分0.7926218383005581 mm²，整机library area4475738.758645；setup +0.000386715 ns，hold +0.0055688 ns；92小宏+128大宏=220，latches0。声明时钟6.666666ns/低频66ns。独立时序审核、gate14、SAIF12/PT12仍待，不能把综合完成等同整阶段验收。
- 库冲突已修复：新报告用原DDC的canonical库路径，保留相同字节的新库副本。原三块及全部失败文件未改。
- 14e6b1b自动接续守卫165061成功等待并启动finish父165305；该父在取锁/建queue/启EDA前失败：`common.sha(__file__)`传入str，而函数要求Path。旧`ops-a5f138e/s0_finish01_launch`请求/日志保留，不能重复启动此控制目录。

## 当前修复与下一步

- 本地`s0_finish.py`仅改成`common.sha(Path(__file__))`。新增实际execute入口和17个阶段磁盘回执测试，包含错误工具哈希拒绝；共3项队列测试通过。外部EDA及锁mock，真实哈希和文件写入未mock。
- 新工具包需从a5f138e overlay生成，原综合无需重跑。新finish入口将**新工具bundle与a5综合bundle明确分别注册**，并注册9ff缓存及05seed；使用新独立session/控制目录。
- 最后22:56:55父165305已不存在；VNC18874435/workspace3为Bash空闲。只读watcher165525已Ctrl+C退出，所有输入49908/78220/51072/37467/79863/14118已结束，无半截输入。板端转发91027保持，FileZilla关闭。再次启动前核对真实进程/锁/空间。
- 依次完成新网表structure、gate14、SAIF12、timing/DRC、PT12，汇总及活动模型说明后冻结S0，再进入S1。原T80同源ASIC14/240和FLOAT可引用，旧网表gate/功耗不能替代新网表。
- `S0_BUILD_REPORT_REQUEST02_20261115.py`目前指向a5f138e/finish01，**必须改为实际新finish包与session后再部署**。新a5综合报告作为独立输入保存。

## 历史路径，禁止重启

详`CONTEXT_CHECKPOINT_20261115_S0_RELINK_READY.md`及其之前检查点：synth03无效set_map_only、synth05/06设计容器重复、synth07最终库路径重复。0e首次relink因手工抄错state SHA在EDA前停止；正确state为43294b528a89c8d0239ccd5e92ee597fc26531217fe3c5245052112030744405。

本次未清理任何服务器文件。既有可恢复编译缓存归档回执继续保留；全部桌面T80和旧八路数据保护不变。新/tmp产物最终仍需持久归档。
