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
