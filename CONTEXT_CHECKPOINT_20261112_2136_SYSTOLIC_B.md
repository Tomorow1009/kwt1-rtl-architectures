# B恢复检查点：2026年11月12日21:36

**21:40后增量：L02前台还原校验已经成功，屏幕打印`ARCHIVE_VERIFIED 12567832939 766947572 True`，VNC已返回空闲shell。** 原R4 L02仍在，尚未移除。`runs/r4_l02_lossless_archive01/verified.json`现已存在，实际hash字段还未读回。新增本地存储工具`workspaces/arch03/scripts/archive_verified_r4_waves.py`：仅L03–L12，最多两个nice19/ionice3低优先级归档worker，每文件源hash、完整解压hash和字节数核对、落盘receipt后才可移除重复raw，L01/L02排除。两个本地小型检查（无损还原与错误hash保留原始文件）通过，Windows测试只mock Linux fuser/uid；**工具尚未提交、部署或运行，不存在L03–L12归档作业**。下一步先同步工具，再决定部署；不得把本地准备写成服务器完成。

任务ACTIVE，用户要求同步本版已完成情况到GitHub后继续工作。直接5×16脉动B，A取消，生产63da6ba/v3/credits3冻结；不加RTL或编码特性。压缩后先读AGENTS、`workspaces/arch03/IMPLEMENTATION_PLAN_SYSTOLIC_B_20261111.md`、本文件及[20:26完整检查点](CONTEXT_CHECKPOINT_20261112_2026_SYSTOLIC_B.md)。那里保存全部1200、DRC06、gate、SAIF方法与队列哈希。

## 同步与完成状态

- 最新已push且ls-remote独立确认：`315a8f67538b209869345491591497b5639c4acf`，私人分支`codex/light-light126/undergrad-d1-numerics`。完成1200、SAIF方法、五次清理、新包哈希及修正后的复现/创新/验收文档已上云。当前2136检查点、STATUS增量及候选清理JSON尚未同步。
- B自己1200任务、30412800输出已通过；DRC06同网表gate14、干净ASIC14、CPU恢复/竞争、任务模式时序/面积均已具备证据。12层平均30502.333333周期/4917.656573task/s，面积上界1.0990947mm²。未达7000。
- R4 SAIF方法crosscheck02通过。B活动12和功耗12仍未完成，不能填R4数值为B功耗；未知活动影响、官方600及物理签核仍未验。
- 新本地722文件交付ZIP为f56b642包，已哈希/身份核对，尚未上传或新包服务器复现。不重复构建或把新包标PASS。

## 仍运行的B队列（没有重启）

基础包为`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`，路径前缀`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`。

- `runs/systolic_b_power_final01_queue/state.json`：driver320367，activity child320434。
- 最新21:32:46：running、无error，activity7/12、power0/12。同一队列之后串行PT12，不再跑ASIC14/1200/gate14。
- 工具`../../operations/systolic_b_tools_4b58ff0`，16文件manifest `bf8e214e70ac92b17b3ecc0c41497995ac0b1d0aa5c483a9662b0225b08f6289`。
- 结束后用实际最终report_request运行同ops`systolic_b_report.py`独立复核全部回执及浮点误差，导出JSON/CSV/中文。尚未做最终独立导出。
- 当前共享盘21:32 free68205674496B，持续被其他共享写入消耗；B自身SAIF每层约115MB。要监测空间，不并行启动别的EDA队列。

## 清理及无损压缩：精确区分已做与未做

前五次旧波形删除**全部完成**，累计524880555968B；不要再执行任何cleanup1–5命令。所有小型回执/日志/输出/源码/重建输入保留。

旧4c8803e/d3_activity01的L01波形另找到371316a/d3_activity02完整独立复核，摘要`cc75446e2f0c01ca4e57bd13af697be0f8a82f6b9d94566a40111f2e19f2d72f`。该29,860,998,380B文件**尚未删除，没有第六次执行脚本或服务器receipt**；只读候选记录为`handoff/team/evidence/SERVER_WAVE_CLEANUP_CANDIDATE_20261112.json`。如后续需要清理，重新查占用、真实路径、保留哈希，并另存回执。它的复核目录有指向原文件的软链，删除后软链会待重建。

### 正在做的R4无损副本（非常重要）

为保留R4全部波形内容并减轻空间压力，仅对**L02**生成压缩副本，**原始L02还在，未删除任何R4原文件**。R4 L01及B文件不动。

- 原R4包：`light-light126-icb32-r4-20261111_011258-49759e108719`。
- 原run：`runs/icb32_r4_gate01/icb32_gate`，summary SHA `95113a35bf2941e985d8d1b8cbad7d88c0d56f07d3c1f533f0fcf549fb2efc7f`，state passed。
- 原文件`layer_02.vcd`，12,567,832,939B，真实普通文件，预期波形hash由原summary读取；不要手工重录。
- 新副本目录在**当前ced包**：`runs/r4_l02_lossless_archive01`，内含`request.json`、`gzip.log`、`layer_02.vcd.gz`。
- 压缩命令`/usr/bin/nice -n 19 /bin/ionice -c 3 /usr/bin/gzip -1 -c <原L02>`；仅一个存储维护进程134929，约21:27启动，21:34读取/proc时已退出。原服务器96 CPU。未启动任何额外EDA。
- 当前**前台正在执行完整解压哈希验证**，本地命令文件`takeover_local/b_r4_archive_verify.txt`，已type和Return，截图`b_r4_archive_verifying.png`已读取，21:35还没有shell提示符。不要再按Return或输入其它命令，不要中断它。它读取整个gzip，要求还原字节数及SHA与原受测summary一致，再计算gzip自身SHA，成功时写`verified.json`并打印`ARCHIVE_VERIFIED ... True`。程序没有删除步骤。
- 原压缩启动文件`b_r4_archive_launch.txt`已执行一次，**不要重跑**；副本目录存在。
- `b_r4_archive_progress.txt`可在空闲shell只读查原文件/副本大小、原gzip PID及B队列。PID134929已结束，不能据PID复用推断作业。
- 校验成功后先读取`verified.json`及hash、确认gzip无占用和仍在同一固定目录；只有无损证据齐全且另存原文件移除回执后，才可按用户已有大文件清理授权移除重复原始副本。须说明R4原始路径将需从gzip还原再复审；内容不丢失，不能称原文件仍在。当前还没到这步。
- 尚未尝试L03–L12压缩；没有并行压缩脚本。可根据实测压缩耗时/空间决定后续，不能删除未压缩或未经完整还原验证的R4文件。

## UI与下一步

VNC fresh18874436，workspace3；工作区4不用，FileZilla关闭。**目前前台是L02 gzip还原校验，不是监视器或空闲shell。** 只读monitor此前已经Control_L c停止，B后台未受影响。无本地exec，无待Return，无CUA会话。下一动作先截图等当前校验终态，再继续空间维护和原B队列；不要向正在校验的终端输入。

候选失败/诊断记录：原候选查询打印过长导致截图截断，后续小字段查询已补齐；一次`/proc/134929/fd`只读查询因压缩刚结束FileNotFound，没有修改任何文件。源/冻结硬件/库均未动。所有新进度写入检查点和交接后再压缩上下文。
