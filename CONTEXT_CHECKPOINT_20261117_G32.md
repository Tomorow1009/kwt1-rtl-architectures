# G32 执行检查点：2026-11-17 07:45

恢复先读 AGENTS.md、CONTEXT_HANDOFF.md、本文件、handoff/team/STATUS.json，以及 workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md（SHA 1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39）。旧 C32 详细过程在 CONTEXT_CHECKPOINT_20261117_C32_DRC_REPAIR.md，按其中最后增量为准。

## 当前阶段和保护范围

S0/P80/C80/C32-A 已冻结。C32-B 本地十四例通过，但同数据吞吐下降 0.0603109733%，不晋级。G32 从冻结 C32-A 派生，60 个 X 小宏、32 个 W 小宏不变。最终32 PE，原32位ICB、源读→实际共享写成功ACK→原总线真实读回→解码→计算→输出ACK排空；SHIFT10、数值与编码不变。门控数据，控制和有效标记继续运行。正式批量为20×12，100条未授权。

桌面 T80_Delivery_20261113、旧八路全部数据、冻结 S0/P80/C80/C32 运行包与备份不改不移不删。用户已确认没有团队持续写共享盘的作业。新产物仍放 /tmp。R4 L03 完整无损归档迁移及恢复35均已结束，不能重复执行。

## 已冻结 C32-A

提交02fbd1a、标签arch03-c32a-repair03-20261117-0725已推。最新交接提交a298b6c已推。真实ASIC240任务6082560输出及total零差异，门级14、完整SAIF12/PT12和声明任务模式审阅完成。固定12平均72179.3333333周期、2078.1571825730 task/s，保守面积0.7224077334997787 mm²，48.9738198083341 mW、23.5659820737506 µJ/task；无SDF/布局前范围，不是物理签核。

服务器生产包 /tmp/s4_21usr_c32_20261116_2010/light-light126-c32-repair-5828804，原生产RTL61246bb2a21c56a9bfd871fd68de93028d79f5fd。repair03网表SHA4f6e416402f2a178ec0ae0494fab1cddc53d7cf9113ac19990e108580b47c1dc。完整备份 /storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups/c32-runtime-20261117_0709-repair03-copy01，tar.gz SHA30f111ef8b51cb7ab223cc50a35e7812be4a8f08c53fc54df9b51aea8b56b80f，1572653883 B，成员全回读。源保留。旧坏网表326条DRC历史不复用。

## G32 已实现但未验收

新未提交 RTL：arch03_g32_{icg,systolic2x16,linear16x2,transport,accel}.sv。实际ICG引用CLKLANAQV4_12TR40，静态ICG_BYPASS参数。门控偏斜数据、PE传播/累加/结果、核心暂存/响应数值/偏置/结果、三个FIFO数据。valid/标签/计数/IRQ/ICB控制原时钟；保留原功能更新使能。新硬件ID0x4b57530f、cap0x000d02bf。预期RTL ICG数量不是映射结论。

本地替代ICG仅证明功能，服务器实际库模型和映射/PPA尚未运行。自己的 G32 合同与 ABI 已写入。工具、SW、monitor、安装器、打包和真实SoC功能入口已准备；正式 EDA、门控STA/实例覆盖和新验证队列仍待完成。

## 正在运行的本地测试（不得修改受测文件）

1. 统一工具会话44813：local_verify_g32_array.py --blocks 10000，目录 local_runs/g32_icg_array_20261117_073716_364646。C32-A/G32门控/G32静态旁路三路逐周期比较；10000随机+32定向。07:39已过1500块，无失败；进度待继续读取。
2. 会话47544：local_g32_datapath_verify.py，目录 local_runs/g32_datapath_20261117_073743_152604；同实际DMA响应三路比较，latency1/prefetch1/jitter0，十四例。07:44读取L01/L02/L03通过，周期60581/60555/60535，与C32相同。仍运行。

测试期间不改这些RTL、TB、runner及其跟踪依赖。独立新增EDA脚本可以继续准备。完成后仍需两拍SRAM、pf0/1、jitter1、A/B/A、错误及取消恢复等新增门控场景；不能继承旧C32 PASS。

三套固件07:42仅编译成功：local_runs/g32_firmware_irq_20261117_0742、g32_firmware_sequence_20261117_0742、g32_firmware_contention_20261117_0742。未执行真实CPU。若改ABI或固件依赖必须重建。

本地数据 local_runs/c80_fixed14_software_20261116_1135，原group8参考 E:/fpga_race-two/kwt1-rtl-architectures/workspaces/arch03/local_runs/n1_data14_20261113_02/source。编译器D:/Xilinx/Vivado/2018.3/bin，Python E:/fpga_race-two/.venv-kwt/Scripts/python.exe。不要重跑 takeover_local/prepare_g32_*.py 覆盖正在测试源码。

## 服务器最后观察与后续

07:23:38 C32归档及模型回执已机器绑定、全部我方C32作业退出、原锁不存在；这是最后观察，不是实时证明。当前无G32服务器作业。VNC窗口18874435曾确认workspace3，无未结束GUI输入；恢复必须重新看窗口，不用workspace4。只用F:/linux_fpga_try/ac820.ps1及已规定技能通路，不使用新后门、FTP绕行或批量结果回传。

下一步：收本地测试；准备G32独立综合/实际ICG门控检查；完成两拍/恢复/竞争本地验证；提交源码、重建需要的固件、准备新独立包；读取实时进程/锁/空间后顺序跑自己ASIC14、恢复/竞争、240、新综合、门级14、SAIF12/PT12、模型审核及持久归档。周期必须不增加、能耗实测下降后才可接受门控收益。

当前未跟踪的历史 handoff/team/evidence/S0_SYNTH05_FINISH_LAUNCH_20261115.py 不提交、不执行。没有新goal或子代理。

## 08:04 本地验证全部完成，准备服务器包

10000随机+32定向317824输出通过；十四例354816输出及total通过、固定12各周期与C32相同。两拍SRAM、pf0/1、jitter1的A/B/A六任务均通过；恢复10阶段、三路搬运协议depth2/4/8共27场景、三个生产观察器及门级观察器本地展开通过。证据 G32_LOCAL_VALIDATION_20261117.json 保存七个独立运行及哈希。会话44813/47544/63845/60028/8209/60601/77065均已退出，无本地活动仿真。

新增G32独立综合、门级、SAIF、PT和审核工具；23项工具测试通过。实际ICG→寄存器时钟端点清单、原生PT report_clock_gating_check、E端点max/min与TE静态0检查已准备，尚无服务器EDA结论。普通物理缓存、数值与搬运参数不变。三套固件仍07:42编译，依赖未改。

07:50:06服务器只读观察：原锁不存在，无我方dc/pt/vcs/simv作业，/tmp59753811968B，共享盘1048576B；唯一显示的185978是该只读查询自身。尚未启动G32。VNC workspace3/18874435，无未结束输入。共享盘再次近满，继续/tmp产物，不修改桌面T80/旧8，不重复归档或清理。先提交和构建独立包，再确认原锁和空间后启动自己的队列。

## 08:19 传输正在进行：先恢复这一会话

生产源码及本地验证提交 **0e16994675bb15e53642017a88f6307da9af4a01** 已推GitHub；后来补充原锁等待测试，工具测试总数26。所有生产源码、固件依赖不再更改。

**唯一GUI输入统一exec会话11581正在运行**，通过VNC第三工作区窗口18874435分段输入，每段900字符。08:19:07本地进度27900/50005；剩余未完成，不能同时发送其他GUI输入、不能重启传输或输入新命令。先write_stdin轮询到退出，再截图读取最终结果。进度文件 E:/fpga_race-two/takeover_local/g32_delta04_progress.txt。输入文件 local_runs/g32_delta04_0e16994_20261117_0810/gui.txt；PowerShell还给第一行加了目标不存在检查，所以实际总字符50005。最后Python会重建并核验包，但**不启动EDA**。

原完整overlay local_runs/g32_overlay_0e16994_20261117_0805，106文件、payload SHA864ddb7f2c1e18cbeb27155353dabb5bc2442316129e972f5e8edf03fb195d4e。服务器运行版仅排除17份本地测试/计划/验收文档，保留全部生产RTL、固件、综合/活动/功耗工具；89文件运行payload SHA **3c0a0f9156b6e40093bc5f9f5d91ae6cb5f95c207ba54e51bb2136a5bc44ab57**。

增量zlib35569B，SHA **9e23ca825460067d868089c993e0f20721bfc56543a0318f96c9d43957f53492**。仅从已冻结 C32 repair5828804 包读取源；先校验完整manifest321c38...、每个原文件哈希，再做显式LF规范化/名称变换和字节补丁，还原目标精确字节并逐个核验。所有输出在新目录 **/tmp/s4_21usr_g32_20261117_0810/light-light126-g32-0e16994**。根目录overlay.json、prepare.py、prepared.json；VNC中间base64为/tmp/g32_delta_0e16994_20261117_0810.b64。源不修改。前三个较大本地delta未发送，不可混用。

FileZilla尝试因既有代理“Expected public FTP server addresses”校验失败，未连接或上传至比赛服务器；不绕过校验。板上已SHA核验的/home/root/g32_0e16994_20261117_0810.zlib仅是完整包暂存。空队列FileZilla窗口20972102已正常关闭。此失败与共享盘无关，不反复重启代理。

新启动器 **E:/fpga_race-two/takeover_local/g32_launch_initial01.py**（SHA5fdf50e0c3b3a87034c65a6f3366633a43e0619722b0094e51438485cbaecb74）仅在本地准备，未传未执行。它要求prepared.json、运行payload、冻结C32-A完整report SHAea4b916...及源码身份一致，18GiB/tmp余量；新queue名g32_initial01，运行自己的ASIC14→恢复→竞争→三块新综合→实际ICG/PT检查→240→精度，原共享锁无损等待。request/process/log均新独立文件，禁止重跑相同名字。

传输终态读取后先确认G32_PREPARED及新manifest哈希；若出现源哈希或缺文件错误，保留失败，不直接跳过检查。通过后才部署启动器、观察进程/锁并显式启动g32_initial01。旧T80/旧8/冻结S0/P80/C80/C32全部保护。后续仍需要自己的门级14、SAIF12/PT12、ICG/模型审核及持久归档；当前G32无服务器PASS。

## 08:31 传输完成，初始队列等待共享锁存储

原GUI会话11581成功结束；服务器G32_PREPARED：1059份文件，新manifest **3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a**，源保留。5eb5d86进度提交已推GitHub。启动器已传并执行：**g32_initial01，PID202586，2026-11-17T08:26:14.737666**。不可重启同名队列。

08:26:47观察：NumPy1.19.5已核验，队列状态acquiring_lock，日志G32_WAIT_ORIGINAL_LOCK_STORAGE，completed=[]；没有派发EDA，原锁未创建。08:24只读/tmp可用59113680896B，共享仅1048576B。等待器保持原锁和队列不变。

新恢复36已通过GUI会话70782部署，输入已结束；执行结果尚待读取。脚本 **handoff/team/evidence/G32_B0_ARCHIVED_EXPECTED_RECOVERY36_20261117.py**，SHA **99bd06f1c69a85e16e2e4b5c164574807e565032e5686dd1b62f950b510eaba9**。目标G32根/recovery36.py，日志recovery36.log，进程回执recovery36_process.json。仅复用原32固定SHA安全逻辑，逐一核验32～35 journal并排除已删项；剩余408份61976206B中最多128份旧B0 generated expected.npz副本。全部完整持久archive/hash/字节/路径/无人使用检查，原锁一出现立即停止。G32状态必须仍为同PID/同request的acquiring_lock；不删除锁、不重启队列。新清理日志保存在G32根/b0_archived_expected36；旧32～35不再执行。不能声称已释放空间或已开始ASIC。

08:33终态更新：恢复36 PID204236完成全部128份核验重复副本删除，19398857B；剩余280份42577349B，不再执行36。state SHA8f08fc401e7fc262176d2265b824ab4483ba176c7b2d6bc9075befd0cb5e085d，free_after19922944B，已留完整归档/日志。08:31:45 G32原PID202586已经取得原锁，stage=soc、status=running，自己的ASIC编译完成（VCS 65modules，CPU compile8.366+elab.991+link.471s）。尚未读取逐例终态。输入会话全部结束，无GUI后台输入，窗口18874435第三工作区。证据G32_STORAGE_RECOVERY36_20261117.json。

08:36:46 ASIC14正式通过：354816个输出及total，summary SHA **e1ed982103f15f60701eb383d327b18725135ba8a8871d69e34707662a0b9610**。固定12总866152周期，逐层相同数据/编码/周期与冻结C32-A一致。真实CPU、IRQ/WFI、总线路径和末写ACK通过。新证据G32_ASIC14_20261117.json。原队列进入sequence；后续competition/synth/ICG/240/精度未读终态，不能标PASS。

新G32归档工具g32_archive_{contract,runtime,capacity}.py及3测试文件已本地准备，11项测试和Python3.6语法通过，尚未传服务器；不改生产0e16994包。归档连接初始七阶段与最终17阶段，并绑定实际ICG检查到相同最终网表；归档不隐含验收、绝不删除源。后续需要独立操作目录传这些辅助文件，再完成自己的门级/活动/功耗/模型审阅与归档。

## 08:48 恢复/竞争通过，综合运行，独立操作工具传输中

最新已推GitHub提交 **2ab70b5d37ed80d908139225a46e2bccb82a7ca6**；生产受测包仍0e16994，不变。STATUS已记seq/contention通过：sequence SHAa9e837c637a8b5ccaa2beef978f319f7d5c98f2064357879859911d4b2939904；contention SHA4e0bd443f0b778c7ce1bd61214eef840325e99d6634a1ca867bea281625456e4。08:43:26原G32 PID202586在synth，fresh_link结束、characterize child222634运行；只是最后观察，不能当实时终态。未启动240、正式ICG时序、门级或功耗。新摘要workspaces/arch03/G32_PROGRESS_20261117.md。

已部署只读状态脚本 **/tmp/s4_21usr_g32_20261117_0810/status01.py**（SHA0f02e5922400e6c02057a913813097a1f6ec0542c4e2aae391c048bc8ed9ccf6），可用VNC命令`python3 .../status01.py`读取当前stage/child/log/回归数量/终态哈希；不改作业。GUI52970已结束。

**唯一GUI输入会话1742正在运行，必须先轮询结束再操作VNC。** 正将5个交付操作辅助文件放到新目录 **/tmp/s4_21usr_g32_ops_20261117_0845**，不修改生产包、不自动启动EDA。输入E:/fpga_race-two/takeover_local/g32_ops01_gui.txt，总13790字符；进度g32_ops01_progress.txt。payload SHAe6b8867f67f329be2b258e7b0b8648238c6fcc441f96cff3d4d1f637393d4e55，manifest **86f015d5d33e689dc0bbb668e79976ab81ad637b9b45bf95ededb228e9cfbf26**。源2ab70b5，详情G32_OPERATIONS_PREPARATION_20261117.json。结束应显示G32_OPS_PREPARED；未看到前不得视为已部署。

5个文件为g32_archive_contract/runtime/capacity.py、G32_FINISH01_FROM_INITIAL01_20261117.py、G32_EXPORT_REVIEW01_20261117.py。归档11测试、出口request2测试通过。finish启动器要求初始队列完整成功并退出、显式`--initial-state-sha256`和`--ops-manifest-sha256`，核验原包/实际ICG/精度/空间/锁后只启动g32_finish01。export要求两队列终态SHA和ops manifest，跑自己的报告/完整未知活动/连线/模型审阅；不自动验收。两者仅准备，未执行。

接下来：1742退出后截图核验操作目录，运行status01看综合；若初始队列失败保留原失败，按具体原因新目录修复，不改受测文件、不弱化检查。通过synth+ICG后队列自动240/精度。初始队列完整结束后显式启动finish01，再export/审阅/能耗对照/持久归档。共享盘可能还满，原锁无损等待；恢复36已完成不要重跑，旧B0剩余280份42577349B副本。R4 L04仅阅读了既有L03工具以考虑未来存储，不曾探查、暂存、归档或删除L04；没有任何新R4作业。旧八路/桌面T80和所有冻结阶段保持保护。

## 08:53 工具部署成功；新只读存储抽查准备

GUI1742已成功结束，08:49:16截图G32_OPS_PREPARED，5份文件、manifest86f015d5d33e689dc0bbb668e79976ab81ad637b9b45bf95ededb228e9cfbf26准确。finish/export仍未执行。交接2774e30已推。08:50:56 G32原PID202586仍在synth，child223529 compile.log运行，无错误终态；completed为soc/sequence/contention。没有240或PPA完成结果。

08:50只读容量：/tmp58451927040B、共享1048576B，96CPU/load3.11。为最终归档预备空间，开始新R4 L04只读压缩样本探查（非删除）。源为原r4_waves_lossless_archive02/layer_04.vcd.gz，既有receipt status lossless_archived_raw_removed，archive7649800109B、raw12564314076B。旧L03不会重复操作。

**唯一GUI输入会话97426正在部署并启动只读probe，先等退出，再操作VNC。** 输入takeover_local/g32_l04_storageops_gui.txt，5402字符；进度g32_l04_storageops_progress.txt。新操作目录 **/tmp/s4_21usr_g32_l04_storageops_20261117**，部署payload SHA9678f5b6f2731700aac2f2610466fb777a96c6a4aaaf94945922924f83c97d05。

两个新脚本保存在handoff/team/evidence：G32_R4_L04_STORAGE_PROBE_20261117.py SHA8d23bde78a0f86069c29defc5a89cafccb3357ec68ef9978b4535dc5b5ced928；G32_R4_L04_XZ_STAGE_20261117.py SHAa19afa203ee1c52566f7a9e8bd9583c6ff59a035e2a58f1db8c1525315605716。仅由既有L03工具逐字替换明确L04路径/身份派生，Python3.6语法通过；全部源只读、无unlink/delete。探查一个低优先级核(nice15)，3份64MiB样本，结果 **/tmp/s4_21usr_g32_storageprobe_20261117/result.json**。probe.log及probe_process.json在新ops目录。源文件、receipt、已有归档均保留；样本通过绝不授权删除。

stage脚本只是部署，**尚未启动**。若probe完成且资源仍合适，可用确切probe SHA启动全量gzip副本→XZ→独立全解压核验，输出/tmp/s4_21usr_r4_l04_xzstage_20261117；需原gzip+raw最坏大小再加12GiB余量，持续保留12GiB。仍只写新/tmp，不动共享源；本轮没有任何L04持久迁移/删除代码或操作。先收GUI97426终态和G32原队列状态，避免把存储准备抢在硬件失败处理之前。
