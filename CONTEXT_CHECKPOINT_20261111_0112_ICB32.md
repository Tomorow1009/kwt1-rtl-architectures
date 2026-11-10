# ICB32 检查点：2026-11-11 01:12

用户再次明确按计划持续推进，不因常规步骤结束等待。当前有效计划仍`workspaces/arch03/IMPLEMENTATION_PLAN_ICB32_C64_20261110.md`，11/11 18:00冻结、11/12 17:16准备交付、11/13晚上截止。压缩后重读AGENTS、本文件、计划、STATUS和根交接，核对完成/待办再继续。

## 本轮新增完成

- `icb32_report.py`及3项防混用检查已云端同步022274d；真实PPA尚无新报告。原生产fcd与其664.393 task/s、1200PASS保底不变，新候选本地34616平均周期/4333.256 task/s仍是pin_mock。
- 真实E203竞争独立入口已实现：`build_icb32_contention.py`、`icb32_contention.py`、`sw/main_icb32_contention.c`；生产`icb32_soc`新增可选隔离monitor，正常性能模式不改。R4两shift固件`local_runs/icb32_contention_fw_20261111_0101`已编译及哈希核验，无真实CPU执行。
- 新真实E20310阶段恢复入口已实现：`build_icb32_sequence.py`、`icb32_sequence_soc.py`、C主程序/专用trap启动、`arch03_icb32_sequence_source.sv`及monitor。动态编码长度通过描述符高15bit记录字数、bit16选A/B、低5bit为shift；源仍实际32bitICB，数据只写共享成功ACK后解码。完整沿用Q12；观察器逐半字独立检查解码，禁止共享读回，6bit结果FIFO计数，真正CPU store异常仅恢复指定故障指令。
- 新序列固件`local_runs/icb32_sequence_fw_20261111_0109`，A=layer_01 37428B/descriptor491a000c、B=rounding 36548B/descriptor4763000b；实际Zig编译/ELF故障指令/metadata/源码哈希通过，当前仅R4 polling诊断。
- `local_verify_icb32_sequence.py` +新fixture，真实新RTL/pin_mock、无E203，10phase通过。5拒绝、初载取消79cycle、超时3988cycle窗口、A/B/A=34639/33914/34639cycle，76032输出逐项正确。3负例（过早切源、异常PC错误、缺回执）均拒绝。目录`local_runs/icb32_sequence_fixture_20261111_010913_076864`，证据`handoff/team/evidence/ICB32_SEQUENCE_LOCAL_20261111.json`。CPU解析器直接拒绝该NO_CPU日志；单独10phase计数/排空解析也通过。
- 首次旧8192cycle预算到超时时新核心已经开始输出，不满足诊断“初载超时”的原前提，目录`local_runs/icb32_sequence_fixture_20261111_010731_266143`保留。改诊断short_timeout=4096后通过，未改RTL或性能固件。旧0108固件保留，当前0109对应4096。
- `server_run.py`新增icb32_contention/icb32_sequence，包工具新增`--contention --sequence`纳入独立诊断固件。所有新Python3.6语法/差异检查通过；新诊断尚未提交/打包/服务器执行。准备提交及新独立运行包，不覆盖e65待跑包。

## 服务器和客户端最后实测

- 最新服务器实测仍**00:59:37**：新e65后继75421=`waiting_predecessor`；旧driver212822、child72155扫描L12 activity。原ecf parent232492/plan `db8df26da37f6487c0141fe16cecc8b96e4364e211ba1e4fa622fa0fc8c1a7b6`，未动旧作业/锁。
- e65服务器根`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`，后继`runs/icb32_r4_first01_queue`。00:51/52已安全解包/594输入/固件SHA核验；该包不含本轮新报告和诊断，不能说它执行了新诊断。
- 板端VNC PID1591/window20971587，01:02窗口再次核实；第三终端页空闲在e65包根。VNC relay会话23793；FTP代理本机PID21036，FileZilla已退出。新工具包下一次仍只经板端Linux FileZilla上传。服务器命令仅VNC输入，禁止旁路/清锁/并发EDA。当前无本地仿真在运行，63156首次失败/70450第二次通过均已完成。

## 尚缺与紧接工作

1. 提交、推送本轮诊断及交接，干净源打包--contention --sequence，校验及暂存板端，正常FileZilla上传。可在旧队列运行时上传/只读核验，不并发新EDA。
2. 继续观察e65原后继。真实ASIC14、综合150MHz/面积尚未有结果；出现失败保存原目录并修新包，不重复同stage。根据实际新PPA决定后续，不能沿用旧面积/29.627mW功耗作为新版结果。
3. 新诊断包正式运行竞争layer_01/extremes、序列layer_01/rounding，排在已有队列之后；需要正常VCS/vendor模型和E203证据，不能把本地fixture算ASIC。
4. 同网表门级14、活动/功耗12、严格时序审定、100×12=1200真实ASIC任务/30412800输出、干净复现与报告交付仍缺。旧8路完整PPA、未知活动影响审核仍按旧队列结果收回；缺项明确保留，必要时减少候选保住交付时间。

原源码/证据路径、连接故障和上传规则见00:54、23:59及22:57检查点。临时生成脚本`takeover_local/adapt_icb32_sequence.py`不入包/Git，且含初始8192默认；**不要重新运行它覆盖已修为4096的当前源码**。

## 01:23 增量（压缩恢复已逐项重读计划）

- 本轮诊断已提交并推送，云端49759e108719d53173648fa3de49b267c6169bbe。干净源包light-light126-icb32-r4-20261111_011258-49759e108719.zip，11,158,655B、630输入，SHA256 ba62ea8ad2b10554a2c211eee33a87e4519d54dd038878d3dc9b259679c538e4；IRQ/竞争/序列三固件均新编译。开发板暂存SHA已实际核对一致。
- 干净包17项工具检查用项目自带Python3.8/Tcl全部通过。Codex内置Python的Tcl初始化失败，先前2 errors属于环境；没有修改源码绕过检查。PowerShell直接管道中文Python脚本有编码错误，未修改文件，改保存UTF8脚本执行。
- FileZilla窗口18874950正常连接，选择/home/board/undergrad-icb32-diag-20261111-0113/，上传至原独立目录；01:22显示100%/11158655B但队列仍1，尚未确认最终成功。禁止重复上传。
- 服务器最新实测01:13:53仍旧L12 activity_scan、212822/72155；e65唯一后继75421 waiting_predecessor。新497诊断包尚未服务器解包核验，不能借用e65预检。
- 下一步确认FTP完成并断开，VNC只读核验原队列/后继，安全解包497并核验630输入及三固件，再顺序推进实际ASIC/综合/诊断。新ASIC/PPA/最终1200/门级14及活动功耗12仍未验收。

## 01:25 服务器新包核验完成

- FileZilla最终成功1、队列空，已Ctrl+D断开、Ctrl+Q关闭。中间满量11,158,655B后再次续传尾部6.4KB，最终服务器ZIP SHA完整一致，安全解包成功，未覆盖旧目录。
- 01:23服务器新497包实际INPUT_HASH_PASS 630、THREE_FIRMWARE_HASH_PASS；新根为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-icb32-r4-20261111_011258-49759e108719`。只做预检，不是CPU/EDA通过。
- 最新服务器实测**01:25:05.856561**：e65后继75421仍waiting_predecessor；旧L12扫描已结束，原driver212822正在extremes.log、child112654。剩余极值与rounding仍属旧队列，不提前启动新EDA。旧72155已退出，锁由原driver正常保持。
- VNC窗口20971587继续在线，第三终端cwd已切新497包；e65队列路径需从`../light-light126-icb32-r4-20261111_000349-e65e8dc8c4c0`引用。FTP已关闭，代理未停止。
- README最上方和ICB32_RUNBOOK补当前入口；历史IC/hex为固定100样本数据根，执行前仍需manifest核验。新配置ASIC14/综合、竞争/恢复、门级/功耗/1200/干净复现均待实际执行。
- 上一01:23增量的分钟标题是记录名，不替代远端实际观察时间；以本条带微秒服务器时间为准。继续运行，不因记录检查点停等。
