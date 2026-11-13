# N1恢复检查点（2026-11-13 09:00）

## 09:01增量（优先于下方上传中描述）

三份文件现已上传成功，FileZilla已关闭。**09:00:29.610646服务器逐项核验全部大小及SHA通过**，shared剩余1741684736B；没有删除任何新文件。截图`takeover_local/n1_precision_upload3_verified_0903.png`。尚未解包或启动精度。新的本地部署命令为`n1_precision_ops_deploy_0903`（两段）与`n1_precision_inputs_copy_0903`（两段），均在takeover_local；必须先检查并仅执行一次，不能当已经部署。

### 09:04后续部署完成（上述两条命令已执行，不再重复）

- 新precisionops已解到`/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-precisionops-20261113_0840`，manifest及2个脚本全部原SHA核验通过；原0f62输入未修改。截图`n1_precision_ops_deployed_0904.png`。
- 两份数据/依赖源已复制到`/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840`，shared源和private副本SHA都再次匹配；无源删除。截图`n1_precision_inputs_copied_0905.png`。后续仍需用机器格式核可用GiB，避免人工读错长数字。
- NumPy已解到`/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905`，**488成员全部解后SHA匹配、import1.19.5、int64矩阵及64项累加自检通过**，系统环境未改。receipt SHA **c1fe14065d6919ff337f2cbf53551f94941acc35d04d3cadabca311fe742eacd**；截图`n1_numpy_private_verified_0906.png`实际09:04:29。
- 新正式精度尚未启动；不得直接绕开原全局协作锁并发跑。下一步准备用原`n1_process.ProcessLedger`包装`n1_recovered_precision._audit`的独立会话，并在当前SAIF完成释放锁后执行。当前原SAIF仍186577，末次实读L03；power12未启动。
- FileZilla已关闭，VNC3空提示符；所有本地exec会话已收完。最新3份部署/NumPy证据和本检查点的云端同步待完成。

## 当前任务与用户最新要求

继续有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`。用户再次明确：先完成N1精度和功耗验收，通过后直接进入N2，不逐步等确认；记好进度并同步GitHub。N2/D1/D2均未开发。阶段门槛不省略，B0保底不动。

压缩后先读AGENTS、CONTEXT_HANDOFF、本文件、有效计划和STATUS的`narrow_execution`。较早环境与清理细节参照`CONTEXT_CHECKPOINT_20261113_0755_N1.md`及其链接。不要重复清理、重跑成功批次或启动第二个活动作业。

## 已完成的N1硬件结果

- 生产硬件`9305c6948c764fed01fe86b20bb3db94170299ab`，当前服务器运行工具`0f62e41207909904efd544992013c1244b0fd63b`，均未改变。
- 本地10000随机块＋定向测试、ASIC14、恢复和CPU竞争已通过。
- `n1_batch100_02/n1_batch`真实ASIC/E203全1200任务通过，30412800个result及同数量total全部一致，failed0。05:36:45.043281至07:51:46.415505。summary SHA `7d4b2b7c68fafbf0b45b0a85c4de4cac9785fd9879d9382e3bbcf0ee0662c507`。最终独立报告尚未导出，不重跑。
- 综合在9305目录`runs/n1_synth01/n1_synth`，summary SHA `cc7f26115f3158fb69f4575f28b5dfde4dd8e5b3aeefda2a927928ad8418db31`；mapped SHA `59c75a4930d82a417e8ac77386751f9cb53c7813964e329729ed9f2a3bfdc82e`。项目面积保守上界0.9511486879005002mm²，220宏、0锁存器、无组合环；setup +0.0000510216ns、hold +0.00153732ns。独立最终审核仍需汇总，不能当物理签核。
- 固定12任务平均29711周期，150MHz折算5048.6351856 task/s，比B0约+2.66%。未达6300；不是芯片实测。
- `n1_timing_01`诊断完成：实际≥1000扇出3个时钟网，原综合日志有4条TIM134，保留差异。summary SHA `2ebc69c279fed69b4b78f5f85e72b9a2dd9e9cc0a304df87196ffffd3a982758`。不重跑已知零目标drc。
- **同网表门级14通过**：`n1_gate14_01/n1_gate`，driver161539，08:11:56.626113至08:26:38.135991，14例354816输出。summary SHA `a804235fd382cc5c7acd3bf088bb4fa3b6f14bc2ef4565727b8bb3b0b4d79fba`。08:30:51实读SHA与state一致、CPU=true、SDF=false、锁已释放；不声称门级核验了内部total。

## 当前唯一正式服务器作业：SAIF12

- `n1_saif12_01/n1_saif`，driver **186577**，开始 **08:32:45.846649**。在0f62目录使用原共享锁，显式12层，不含两个定向用例。
- 最后实际 **08:57:24.419562**：running；L01/L02已完成，L02 SAIF97319662B，当前L03子进程198325；前一子进程193161 exited/wait=true/rc0。无失败。
- 不重复启动、不改运行包。下一步原作业完成后收summary、检查锁释放，再串行功耗12个单层作业。**N1自己的功耗尚无数值**。
- 资格依据保持R4原`ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck`，SHA `a0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26`。
- 只读监视命令`E:/fpga_race-two/takeover_local/n1_saif12_monitor_0836.txt`；新的命令输入前确认空提示符。一次查询曾与历史libc命令拼接，SyntaxError，未影响作业；Ctrl+u清空后已正确查询。

## 完整浮点100条：来源缺口已解决，精度仍待新核算

- 100个原WAV的路径、排名、split与SHA均已和服务器原manifest逐项匹配。
- sample001先恢复并精确匹配原NPZ SHA `275444a4f5d895cd0fdf8a10a23705fb784ba7151a6d4980aa4ff50793f8533e`。
- 08:19固定同一模型/profile恢复100个完整X/Y/logits NPZ，总142487371B，未从HEX反推、未训练、未改模型或排名。每条重复推理逐位相同，162个模型变量、共享W/b核验通过。
- **08:27:31服务器原清单比较通过：100个NPZ SHA全部一致，W/b一致，排名/WAV/split/音频SHA一致。** 证明`handoff/team/evidence/N1_FLOAT100_SOURCE_RECOVERY_20261113.json`，SHA `988e5e96a42eea61c2c348626b24f1252556da166f48653d30218452af905f89`。
- 原`KWT1_WORST100_ORIGINAL_FLOAT.zip`容器仍未取得，不伪造其SHA。新来源模式显式为`exact_original_npz_members`，成员内容精确一致，不等于原ZIP归档字节相同。
- 本地恢复目录`local_runs/n1_float100_recovery_20261113_0824`（实际开始08:19，不能用文件名推时间）；summary SHA `bfbecc01704c791c96789975d29221c677a7f885c60c96d34ca56d85232ecc02`；candidate_hashes34248B SHA `f43e42d4df5c94516e14c8a82ddde49cfa3398dd50d1e6ce8f5f06be8a6f13b5`，后者已上传并服务器比较。
- 新`n1_float_recover100.py`实际运行完成；`n1_recovered_precision.py`和`n1_report.py`的显式来源分支已提交。本地恢复选择测试5例、旧/新数值fixture11例、PPA与精度连接测试23例通过。真实100条精度运行尚未启动。
- 新精度入口仍重新量化、独立逐k整数累加、检查原始四种HEX、重新合并SSE/参考能量。报告必须连接本轮ASIC1200，不借B0误差。原`n1_precision.py`严格原ZIP入口保留原样。

## 精度部署：三个文件正在经FileZilla上传

本地`local_runs/n1_precision_delivery_20261113_0840/`，开发板对应`/home/root/n1_precision_delivery_20261113_0840`（GUI`/home/board/...`）。三份开发板副本已逐项SHA核验。

| 文件 | 字节 | SHA256 |
|---|---:|---|
| n1-recovered-float100-20261113.zip |143258826|5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2|
| light-light126-n1-precisionops-20261113_0840.zip |17806|bcaf7ca61d10efe09dbc3329247d7b0dd981f284a0b73c835044fae1b4032d84|
| numpy-1.19.5-cp36-cp36m-manylinux2010_x86_64.whl |14835495|a4646724fba402aa7504cd48b4b50e783296b5e10a524c7a6da62e4a8ac9698d|

- 目标仍原独立项目`/IC/light-light126-undergrad-d2-20261109`。最后截图`n1_precision_transfer_final_0900.png`：工具包成功；浮点包143MB/286秒成功；NumPy轮子64.4%、尚在传。**不要提前说三份均上传成功或关闭FileZilla**，先再观察完成/空队列。
- 三文件服务器核验命令已准备`takeover_local/n1_precision_upload3_verify_0900.txt`，858字符，拆分part1/part2；尚未执行。可直接用完整文件，因为<1000字符。上传全成功后关闭FZ释放连接，再VNC执行核SHA。
- 新precisionops manifest SHA `ea65bcaa647e84f6e8dc4d16dffc754522243f975716617a46894a2a02c80108`，来源提交d390d879。只含2个脚本：`scripts/n1_recovered_precision.py`9956B SHA `61a5099fe0d3f8ded611a83067aa035d053ed61dbd6e0204e84553c42f18c585`；`scripts/n1_report.py`43738B SHA `6245fbdc5b6b4db022903964d729cd58a76fc614f942adf94cc7c9519dd044a9`。依赖原0f62完整包，不改其文件。
- 尚未服务器解包、部署NumPy或运行新精度。后续在原private/tmp下新目录解包，保留所有源文件及manifest；限制member集合、先核ZIP SHA与成员、确认目标未存在。
- 正式服务器作业串行；N1 SAIF运行时先部署/检查环境，不并发启动新正式精度或功耗批次。精度与功耗按原锁排队。

## 服务器数值环境与依赖缺口

- 服务器实际`/bin/python3`3.6.8，没有NumPy；没有conda、/usr/local或用户现成Python环境。`platform.libc_ver()`误报2.3.4，已用`os.confstr("CS_GNU_LIBC_VERSION")`核到实际 **glibc2.17/x86_64**。
- 本地旧TF虚拟环境也没有pip，下载尝试立即失败，未改任何环境。改从官方PyPI固定链接下载NumPy1.19.5 cp36m/manylinux2010轮子并核官方SHA，兼容glibc≥2.12。只用于项目私有精度环境，不安装系统Python、不改EDA库。
- wheel488成员、解压51042594B，WHEEL明确cp36-cp36m-manylinux2010_x86_64。保留内含LICENSE。新来源记录`handoff/team/evidence/N1_PRECISION_NUMPY_DEPENDENCY_20261113.json`尚未提交。
- 计划解压到private/tmp的新numpy目录，通过该单个精度进程的sys.path引用，OPENBLAS_NUM_THREADS=1。先核路径安全/无覆盖/成员哈希，再做版本和小型整数/矩阵烟测；不要依赖系统pip、联网安装或改系统环境。

## B0审核新增事实与未关闭项

- B0功耗仍69.8371mW/14.2013µJ布局前估算，`system_power_verified=false`，不能宣称N1相对能耗准入已通过。
- 08:42对remaining11实际summary重新核SHA `b7f704f1bc678f2d6e90732ddaeed6051f393693169b5530fdd69ed1fe463991`，且11子summary SHA全匹配；每层selected558、selected_unknown0、required_missing1356。read_pending每层T1=0、unknown=0。这是已完成结果读取，没有重扫SAIF。
- 证明`handoff/team/evidence/B0_CONTROL_REMAINING11_REVIEW_20261113.json`，SHA `b673dcba83aa530a46dfb9dd4e6ddd55116118dcaa5b97dfcf954abe851867a1`，尚未提交。选中信号已知不等于全部宏引脚或联合时序已证明；不得把缺失/未知按0功耗处理。
- 历史B0完整12层unknown inventory、L01control、映射2234未知声明、宏连接/模型等已有证据参见07:55和06:00检查点。停止逐门无界扩展。剩余需把实际宏写时Q保持/全窗口read_pending0与全层控制证据合理关联，并明确未覆盖部分。

## 仓库、存储与桌面

- 分支`codex/light-light126/arch03-n1-n2-d1-d2-20261113`；最新已push并ls-remote独立核验 **d390d879e489d38f0187c0db229e141cfbdc6ad6**。生产9305/运行0f62与B0标签不变。Git不含大型数据、库、凭据。
- 原项目`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`；原共享锁在其父目录`.arch02_team_lock`；运行根`/tmp/s4_21usr_n1_20261113_0210`，0700。08:30private空余653060173824B。最终/tmp持久归档仍未执行，不能当最终备份交付。
- VNC窗口18874436、workspace3；终端cwd仍shared9305原包。workspace4不使用。开发板FileZilla23069254目前在前景传输末个wheel；没有队友使用。
- 窗口被遮挡时截图会黑，**用Alt+Tab切换，不用Escape**；Escape曾触发tcsh历史文本，造成只读查询拼接SyntaxError。执行新命令前Ctrl+u及确认空提示符。不要在未知命令上盲按Return。
- 输入单次上限1000字符，建议拆650；每次type内层exec要等exit完成再下一段。使用helper `--keys Control_L a`，不能写成单字符串`Control_L+a`。FileZilla各输入需要`--expect-class Filezilla`。
- 当前没有未完成本地exec会话；不要重复处理早期上传错误或已完成清理。

## 紧接着做

1. 收FileZilla三份上传成功，空队列后关闭；执行服务器三份SHA核验。
2. 在新的private目录部署两脚本、恢复FLOAT容器和私有NumPy；验证环境/源数据身份，不改原运行包。
3. 监控原SAIF186577到12层终态；依据实测速度评估剩余时间，不用理论MAC速度估宿主耗时。
4. 串行完成自己的精度重算与12层功耗，收完整独立报告、时序/面积/未知活动与B0比较；缺项继续显式未验。
5. 收齐N1准入后自动进入N2，不再向用户逐步确认。同步上述新增证明/检查点，准备压缩前更新本文件及CONTEXT_HANDOFF。
