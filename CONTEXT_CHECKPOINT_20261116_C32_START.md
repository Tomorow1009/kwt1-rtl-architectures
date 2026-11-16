# C80已冻结，进入C32-A

更新时间：2026-11-16 20:13（北京时间）。压缩后先读AGENTS、有效计划、根交接、本文及STATUS，核对完成与未完成项，不从旧待办重启队列。

## 20:47 新包已核验，initial01零子任务因共享盘满失败

**C32服务器硬件仍未运行。** 主包重建和1081输入准备已完成。包路径`/tmp/s4_21usr_c32_20261116_2010/light-light126-c32-61246bb`，manifest准确SHA `0b12bff8f9d989e83eb48d4bd5e62185852edf592e442d3bccdbb1070fc849cc`；受测提交仍61246bb。此前人工抄录65字符哈希触发前置拒绝，无任务；之后用prepared回执机器取值启动。

- 差分首次重建被25处基准哈希差异拦住；只读核对25处全是CRLF/LF，无内容变化。新重建器`C32_RECONSTRUCT_LF_61246BB_20261116.py`提交e9c52fe，SHA `d21c6326c6241b13d04dcbd5c90ac0a827972ce84ab185a48cb7bc1dcfc01d65`，先核验原冻结字节，再仅内存换行归一化并检查差分基准SHA，最后完整payload仍精确为`40fed77e347aad1347f1998f19801652770b176c5f5e0e03f405d68d0a11c602`。原工具和失败保留。新根`reconstruction_lf_receipt.json`记录25处，原源未改。
- `c32_initial01`于20:40:42.554042启动PID177134，随后在`.arch02_team_lock`的mkdir即ENOSPC失败。20:41:53状态failed，completed=[]、无stage；20:45机器确认PID不存在、整个队列无child回执。原state SHA `42ffa16c397ab474753eb1cc9ef5617c2bf226bbee1c318f8e752fd5416aa674`；request SHA `49a8fa04de09a5e269c89cc21c99be1fffa5d7018467c469c350ad2ad977cd7a`。**不得重跑/覆写initial01。** 启动时/tmp可用79114158080B，共享盘仅1048576B，仍无法创建锁。
- 已只读找到旧B0 `systolic_b_v3_drc06/systolic_b_synth`三份已归档重复统计：mapped_probe_inventory.tsv 268868363B、area_inventory.json 137502877B、leaf_area.tsv 75261374B，合计481632614B。不是T80/旧八路，也不是源、网表或摘要。完整B0归档及63653成员回读证明不动。
- 新范围限定工具`C32_B0_DUPLICATE_REPORTS19_20261116.py`提交b026f9b，SHA `d87d789ad28b0e2ab2c4d290f52b3997f9d525a755eb7942ceba46af4d06e071`，本地Python3.6语法和6项终态守卫通过。它重新hash完整归档、清单、三源文件，检查无锁/无EDA/无占用，写intent及journal后才删三个重复文件；原B0完整备份留存。**当前本地会话12125仅通过GUI传cleanup19.b64，尚未执行删除。未退出前不发其它VNC输入。**
- 清理成功后应从同一612冻结包新建`c32_initial02`，显式绑定initial01零工作终态和cleanup19回执；原初始启动器写死initial01不可再次调用。本地`C32_FINISH01_LAUNCH_20261116.py`也写死initial01，后续须新增绑定initial02的启动器，不能原地改受测包或冒用旧成功。

截至本段尚无任何新清理完成、无C32 CPU/PPA结果、无C32-B/G32。桌面T80、旧八路、P80/C80冻结与备份全部未动。原删除14/17/18不可重复；16从未执行且已过期。接续先读本段和实际会话，不按下方早期“正在ASIC”文字推断状态。

## 20:31 主传输完成，部署工具传输中

- 旧GUI会话13372已正常退出，97332字符和结束行全部发出，20:30截图确认第一终端回到Bash提示符。**不要重复传delta03**。服务器尚未重建或启动EDA。
- 新GUI会话70703正在输入`deployment_tools02.b64`（6588字符），结束后自动写`C32TOOLSEND`并截图。未退出前不要另发VNC输入。该工具payload SHA `34829ef86778d18293f812fe00c21b4a42297068c2811812d41ce8e2a0b3c39a`，3文件。
- 本地`local_runs/c32_overlay_20261116_2002/prepare_remote01.py`已准备1477字符ASCII，先语法检查。待工具传输结束后，通过可见终端运行此代码：核验工具payload、独占创建`ops-deploy01`，执行重建器核验完整612 payload，再提取其prepare工具创建新C32包。若失败保留现场，不跳过哈希。
- 当前已push `643398e`：新增本地带范围的报告`C32_LOCAL_BRINGUP_20261116.md`及终态后显式启动门级/功耗的`C32_FINISH01_LAUNCH_20261116.py`，SHA `6a7ab5a948c33cdecd96642f03b9ad484c8e1dc0f556a069ed52c8b5b051196f`。此工具只准备，不能在initial01完成退出前运行；本地Python3.6语法与CLI检查通过。硬件受测提交仍61246bb。
- 本次没有新增硬件改动、重跑测试或清理服务器文件。T80/旧八路/P80/C80保护不变。新包完成校验后继续原计划自己的ASIC14/恢复/竞争/综合/240/精度。

## 20:13 受测提交已同步，GUI传输正在运行

**C32-A受测源码及工具已提交并push：`61246bb2a21c56a9bfd871fd68de93028d79f5fd`。** 三套固件绑定当前源码检查通过。C32自己的真实CPU/PPA仍未运行，所有本地结果范围不变。

- 完整传输资料：`local_runs/c32_overlay_20261116_2002/payload.json`，114文件，5485929B，SHA `40fed77e347aad1347f1998f19801652770b176c5f5e0e03f405d68d0a11c602`。普通zlib445715B未传。
- 精确差分传输：同目录`delta03.zlib`，72999B，SHA `64d6f32d905cd59decb73a08a7120d31634d95dc4503b3717feccf1ea22525b5`；base64文件`delta03.b64`共97332字符。基于冻结C80成员做只读重建，最终完整payload SHA必须相同。早先delta01/02/XZ只是本地压缩尝试，没有上传。
- **本地exec会话13372正在连续GUI输入，不能另发VNC键盘输入、切换标签或重复启动传输。** 它每段900字符，进度`local_runs/c32_overlay_20261116_2002/gui_transfer_chunks.txt`；最后观察20:11已9900字符。循环将自动发送全部内容及`C32PAYLOADEND`结束行，并保存`takeover_local/c32_transfer_payload_done.png`。恢复先poll该会话/读本地进度和截图；未见退出不要发送下一命令。可继续纯本地工作。
- 新私有根已于20:07建立：`/tmp/s4_21usr_c32_20261116_2010`，0700。第一终端当前在`cat > .../delta03.b64 <<'C32PAYLOADEND'`中，窗口18874435/workspace3。最后截图`takeover_local/c32_transfer_start.png`。没有FileZilla；原FTP DNS约束仍保持，未尝试绕过。
- 下一步上传本地重建器`handoff/team/evidence/C32_RECONSTRUCT_61246BB_20261116.py`（SHA `5092484b3a34ab1d3d32549c67784217f1d7e96419237d5c450794bc7fcf09d2`），本地完整重建/损坏拒绝通过。服务器先验证C80 manifest及每个引用成员，再独占创建`payload_61246bb.json`。若基准成员不存在/哈希不符，保留失败并修复传输资料，不能跳过检查。
- 从核验payload取出`c32_prepare_bundle.py`到新根bootstrap，运行`--payload ... --root ... --bundle light-light126-c32-61246bb`。新包只读复制C80原包1008文件并写新C32覆盖；源不会修改。核对prepared回执/新manifest全部文件。
- 新启动器已本地准备`handoff/team/evidence/C32_QUALIFICATION01_LAUNCH_20261116.py`，**尚未上传或执行**。需要显式`--manifest-sha256`，绑定payload612、prepared回执、冻结C80报告SHA、S0预算、DATA100和FLOAT、私有NumPy、进程/锁/空间。将启动唯一`c32_initial01`，顺序CPU14→恢复→竞争→综合→240→精度；C32-B/G32不会自动启动。
- 当前qualification源码SHA `147af697f797cfcd84796a66fa7daecd24910f1527f8d08422fb9c216ae63afb`。冻结C80对照报告`/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7/runs/c80_report02/c80_report/report.json` SHA `46d13e9cbfac0730bec8eb7ea0b7927a9612462cf4b5cd056402c06155711cf4`。新队列要求同源、同编码SHA；不要求C32-A必须超过C80才测自己的PPA。

共享盘最后仍仅1MiB，私有/tmp约79GB；未做任何新删除。桌面T80、旧八路、P80和C80冻结证据禁止动。压缩后先解决当前传输和新包校验，不回到旧综合或旧240。上面两个现场辅助脚本和本次进度待下一提交；不改变612受测硬件。

## 20:01 本地验证齐备，准备独立服务器包

- 完整本地14例通过354816输出及total，目录`local_runs/c32_datapath_20261116_194814_422485`。此替代总线jitter0周期约60k，不作为原平台性能。
- 两拍SRAM、预取0/1各A/B/A共6任务通过152064输出，目录`local_runs/c32_datapath_20261116_194815_001509`。
- 独立恢复fixture通过10阶段/3完整任务/76032输出及3项预期拒绝，目录`local_runs/c32_sequence_fixture_20261116_195223_950804`；不是CPU执行。
- 正向/竞争/恢复生产观察器编译完成；门级观察器本地端口编译和完成条件协议测试通过，目录分别`c32_monitor_elaborate_20261116_195109_914742`、`c32_gate_observer_20261116_195535_514696`。不等于真实网表门级。
- 独立固件三族`local_runs/c32_fw_{irq,sequence,contention}_20261116_1952`编译并绑定当前源码。新的安装器严格2行、32PE、220宏和布局6；保留原C80安装链5行检查，最终清除继承的80PE/旧布局字段。
- 新增C32自己的SoC/240/综合/门级/SAIF/PT/报告/归档入口；57个Python文件通过Python3.6语法及导入，54项工具测试通过。数值运行时前置检查既有私有NumPy，避免C80曾发生的长队列末尾缺包。
- `C32_LOCAL_QUALIFICATION_20261116.json`绑定上述摘要；服务器实测均未开始。生成过程中UTF8读取修复、测试模板缺依赖/旧ID已修正；没有硬件功能失败。删除了本轮误生成的、依赖尚不存在C32现场导出脚本的测试副本，原C80测试未动。

19:57:54只读VNC预检：本账号无DC/PT/simv/阶段队列，无协作锁；私有/tmp可用79155372032B，共享盘仅1048576B。未清理文件。窗口18874435、workspace3第一终端空闲，workspace4不操作。接下来提交本地受测源码、构建带哈希的新C32传输资料；从冻结C80源包只读复制新目录，不复制其PASS。部署前继续核对新包全量清单；原T80/旧八路/C80/P80保护不变。

新qualification对照冻结C80固定12同源、同编码SHA及长度，记录C32-A速度变化，不擅自要求它必须快于80PE后才测面积功耗。可选C32-B仍必须不慢于已验收C32-A。C32自己的真实CPU14/恢复/竞争/240、PPA、完整归档冻结仍待完成。

## 19:46 C32-A开发进度（优先于下方早期快照）

C80标签`arch03-c80-codec-20261116-1930`已在c7f3c00创建并推送。现已新增独立C32阵列、线性核、加速器、两套TB和两套本地运行器，共7文件；尚未提交。旧C80/P80/T80代码未改。硬件ID确定为`0x4b57530d`、能力`0x000b02bf`，两行结构；编码布局仍`0x00100006`，与C80字节相同。两32项结果区、32转换器、10位块号、800块/51200供数拍。C32-A仍60X＋32W小宏。

- 阵列压力通过：`local_runs/c32_systolic_array_20261116_193552_854669`，10000随机＋32定向，317824输出，sum/total/result/saturated及每输出64次MAC零差异；暂停201275拍，取消11、复位11，块号回绕及连续II64通过。种子0x7834a9f1。只证明独立阵列/转换，不含CPU、SRAM或PPA。
- 首层完整本地搬运通过：`local_runs/c32_datapath_20261116_194127_101770`，1拍SRAM、预取开、jitter=1，25344输出/total零差异，83308完整周期（带随机等待，不是正式性能）。实际源/共享写ACK/共享读回/结果ACK四段检查；独立按逻辑行算式检查每个物理X宏地址、跨五行组和尾行屏蔽。
- X到齐改为50个行对标志；读取流水保存实际RB/G，单端口冲突逐宏仲裁。尾row99禁止读取/写回。编码器、搬运及平台参数保持。
- 本地生成脚本曾遇文本模板断言；已另行生成正确文件并完成以上测试，原失败输出留local_runs。不要重跑一次性create_c32_array/datapath生成脚本覆盖实际源。

下一步完整14本地任务、两拍SRAM/预取开关/无复位A-B-A，再创建独立C32固件/安装/SoC观察器/统计/结构检查及服务器运行包。不放宽C80的5行/80PE检查。C32自己的真实CPU14/恢复/竞争/240、综合/门级/活动/功耗/归档均未做，不继承C80 PASS。服务器19:27终态仍是最后观察，本段未操作服务器。

代码摘要与原始summary身份保存于`handoff/team/evidence/C32_LOCAL_INITIAL_20261116.json`。历史未跟踪S0_SYNTH05_FINISH_LAUNCH_20261115.py继续不添加、不运行。桌面T80、旧八路及所有冻结备份保护不变。

## 当前目标与保护

有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`，SHA `1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39`。路线S0→P80→C80→C32-A/可选B→G32。最终32PE、150MHz/6.666666ns、SS/.99V/125°C、项目保守面积≤1.00mm²，<0.50mm²仅争取目标。

原32位ICB/平台缓冲、X14/W12/acc32/total33/SHIFT10不变，完整源读→共享写ACK→原总线读回→解码→计算→最终写ACK/排空。不能以ACK数据旁路提速。

**服务器桌面T80_Delivery_20261113、全部旧八路、P80及新冻结C80包/备份不修改、移动或删除。** 用户持续授权推进和私人GitHub同范围同步；不额外开启子代理，不因等待自动结束任务。

## 已完成与冻结

S0/P80此前已冻结。C80技术结论及全量持久归档已完成，冻结回执`handoff/team/evidence/C80_FREEZE_20261116.json`，标签预定`arch03-c80-codec-20261116-1930`（本页首次写入时待提交并打标签）。阶段报告`workspaces/arch03/C80_STAGE_REPORT_20261116.md`；早前完整经过见C80_POWER和C80_SAIF检查点，不重做。

C80受测提交74f3ae7bb479d5fdd7917702c4a2c0671eacb61b，RTL自2896d5deaed9e669ca23e12616e8d5091d72e034后不变。包1008文件manifest `d0f18e4a6aa8a928df37d4347f1a8853c448e823f0685a83c5b710732e5e7a59`，运行根`/tmp/s4_21usr_c80_20261116_1245/light-light126-c80-74f3ae7`。

- 本地48解码、完整14、恢复/raw/1与2拍SRAM，10000随机＋32定向块；真实ASIC14、恢复及CPU竞争通过。
- 自身240任务6082560输出及total零差异；FLOAT20逐层最大NRMSE0.20198143836753799%，固定12最大0.1425636423408142%，裁剪/饱和0，非官方600。
- 固定12总847238、均70603.1666667周期，名义150MHz吞吐2124.5505985task/s，编码均25790B、四段384174事务。240均69352.7125，不能混用两组。
- 保守项目0.9611361367002672mm²，明确新增0.8005131007003622mm²，整机4.483352635935mm²；setup+0.000216007ns/hold+0.00623399ns，220宏/0锁存器。
- 同最终网表无SDF门级14、完整SAIF12及PT12通过；时间加权55.3675890516mW、26.0608448455µJ/task。比P80吞吐+9.8327%、功耗+2.9599%、能耗−6.2574%。
- 全12层374565直接映射＋1336孤立默认、未注释0；39930未知目标中37879直接解析、2051分类，关键显式控制未知0。保留原X活动政策与布局前限制，不宣称物理功耗误差上界。
- 模型快照SHA `81517233df218c5738a1e3950bef1dd1f5b8ca0de15a4948d1e6a85877f04071`，报告SHA `46d13e9cbfac0730bec8eb7ea0b7927a9612462cf4b5cd056402c06155711cf4`，网表SHA `6a62a3aa792865390549dd11a841d0888501902c449c61c74aa82eecd2523b00`。

备份`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/backups/c80-runtime-20261116_1923-copy03`，752263487B，SHA `81123521ea325f7f9b89f23e7c132ee8ed62f1ae5b702d2b69139d124b219d39`。19478文件/1293目录/6链接全部回读，源前后相同、源未删。回执SHA `f4531ad245395a3de7388dcad55c550d8b73b08600da195e493abf7ae77fbc8c`，清单SHA `5b87c5d35021e22f3d43e7b79f70464b2fdc1c8de8a3144b2e132f00e8e9acb0`；19:28:49机器断言。独立技术结论提交120b477，SHA `4c4d3a70fcdbee758817718a4b0d4088d1248951003e3579c5cf056ddb37e218`。

## 原队列/空间终态与禁止重复项

19:27观察：58047验证、59705汇总、134382连接查询、DC137120及归档143417均自然退出，无协作锁。汇总19:11:17结束，状态facts_joined_manual_conclusion_required，终态SHA `311c74f6b83c2020458f20b49d9ef8d60c16b466ec7d0af9a2ebf977b6ed97e3`。不要再启动综合、240、门级、活动、功耗或旧export。

共享盘满曾使连接查询等待原锁：single17(6dabb3f)核验完整归档与占用后，仅删除旧B0 drc05/mapped_probe_inventory.tsv，268811341B，原查询自行继续。之后remaining18(120b477)在所有队列退出/无锁/无EDA时清理其余17份旧B0重复SAIF/DRC明细2070730031B。完整B0备份`backups/systolic-b-20261112_2320/completed-evidence.tar.gz`及全部结果保留。两项回执在Git对应JSON。**cleanup14/17/18均完成，不重复；cleanup16从未执行且已不适用，禁止运行。** 没有删除T80、旧八路、P80、R4方法资格、当前C80或任何源文件/网表/日志。

共享盘19:27只剩463470592B（会变化），新服务器运行继续用独立私有/tmp及原团队锁。copy03已完成，不重复启动。未采用后续只读列出的B0 drc06候选，没有新增清理。此前失败initial缺NumPy、followup01空间失败、export01失败均完整保存入本次归档。

## C32-A接续准备与未完成项

先读`workspaces/arch03/C32_PREPARATION_READONLY_20261116.md`。以下为19:29时的准备清单；已有RTL和本地结果以顶部19:46更新为准。固件、运行包和服务器任务仍未开始：

1. 新独立2×16阵列和线性核，32PE/32转换器、两32项结果区、10位块标签、50行组/800块、最后仅row98。X/W token27/25位，波前跨度16/15，不重置普通连续块。
2. C32-A保留60个X小宏＋32个W小宏。逻辑pair与旧五行物理G区分；row4/5跨bank/G，迟到响应携带真实RB/G。按逻辑行/对发布到齐，最后禁止row99访问/输出；1/2拍和实际宏冲突需重新验证。
3. 复用C80编码字节、DMA/仲裁/原平台参数与参考，独立ID/能力和安装/测量/结构入口。当前4b57530d/e/f只检查过未占用，尚未正式分配。不要放宽旧C80的5行/80PE检查。
4. 本地完整数值协议与10000随机块，自己的ASIC14/恢复/竞争/240、综合时序面积、同网表gate14/SAIF12/PT12，独立报告后冻结。不要继承C80 PASS。
5. 之后才评估可选C32-B（两4096×16奇偶Xbank）及G32，原80PE不自动恢复。当前编码均25790B下搬运仍限制约2128task/s，不能用51200计算下界宣称C32接近3000。

本地`E:/fpga_race-two/kwt1-c32-g32-20261115`，分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。Python3.8为E:/fpga_race-two/.venv-kwt/Scripts/python.exe；Vivado2018.3、Zig已可用。历史未跟踪S0_SYNTH05_FINISH_LAUNCH_20261115.py不添加、不运行。120b477已push，本页及冻结回执待提交。GUI恢复先刷新windows/screenshot，既有ac820.ps1，当前18874435/workspace3，两终端空闲，workspace4不操作；FileZilla未用。
