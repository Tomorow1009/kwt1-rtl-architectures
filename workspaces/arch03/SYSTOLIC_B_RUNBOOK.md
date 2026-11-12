# 5×16脉动B复现与结果收回

本手册对应生产硬件`63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86`、v3布局`0x00100003`、source credits=3和IRQ/WFI固件。源码候选已固定，验收状态以[独立验收表](ACCEPTANCE_SYSTOLIC_B_20261111.md)为准。当前已有ASIC14通过；下列待运行步骤不能当作已有结果。

## 当前作业，接手时先检查

**11月12日16:18：下两段08:45状态是历史。** synth02已完成，validation02因入口参数失败，validation03已完成恢复/竞争/原网表门级；不得续跑。当前候选是ced包中的`runs/systolic_b_v3_drc06/systolic_b_synth`（摘要b8178003…4824ced），约束违规清零；当前唯一EDA为新`runs/systolic_b_v3_drc06_gate02/systolic_b_gate`，driver79264。先读[最新检查点](../../CONTEXT_CHECKPOINT_20261112_1506_SYSTOLIC_B.md)，实际锁位置是server_config.server_root下`.arch02_team_lock`。

FTP421时经已授权VNC部署的小工具副本位于团队目录`operations/systolic_b_tools_52f37cc`，13文件manifest SHA `8fa64e620192e45ce99b4faef3bda698ae4d1405821992eae04093cc5c799435`。原ced包709输入未改；gate02使用已核验d48副本，最终功耗使用52副本。不得用ced原SAIF工具覆盖后续修复。直接从ops调用最终队列或报告时，需`env PYTHONPATH=workspaces/arch03/scripts python3 <ops脚本> ...`。

R4 SAIF replay01已完成，摘要f7d542dd…3d21a；跨方法PT请求`operations/r4_saif_crosscheck01_request.json`已部署但未启动。合格后最终队列用`saif_qualification`引用实际结果，避免再次重放R4。新B功耗导入独立`mapped.precise.sdc`，实际HF周期必须6.666666ns；历史R4导入6.66667ns的舍入事实保留披露。

11月12日08:45启动的新综合为`systolic_b_v3_synth02`，driver183038；后继`systolic_b_v3_validation02_queue`为184658。它绑定同一综合开始时间`2026-11-12T08:45:21.455160`，按锁串行运行恢复、竞争、SAIF小试、时序诊断和gate14。读最新检查点，核对实际进程、锁、空间和状态后继续；不要重复执行本页示例启动相同阶段。

旧synth01及validation01因磁盘满退出，状态文件保存失败而停留在running/waiting。没有最终网表可恢复，不是可续跑的综合。用户授权后已清理旧MMIO8 L09–L12四个VCD，其他证据保留，详见[清理回执](../../handoff/team/evidence/SERVER_WAVE_CLEANUP_20261112.json)。这不影响R4或B的输入。

## 固定包与输入

工具包：`light-light126-systolic-b-v3-20261112_032054-8d8f26247b7a.zip`，11,344,790字节，705项输入。

| 内容 | SHA-256 |
|---|---|
| ZIP | `b2d31c9906a3d7f3640581d19fac568682f61e7fa3655fb59df692ed66c7d837` |
| 包manifest | `ac83363a9b3ea5cd88976b13f66a12a6543e68607def89b7ce40496eb359f177` |
| 生产固件manifest | `11d860ca0269f962a71250e72925c730def0da79d931a79e3102c82ddaa16b91` |
| 生产ELF | `78599ba8a6f1bdf1a4002a4cb1ee1e53bad84bce88798f6e41a22e6189108827` |

服务器包目录前缀：

```text
/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/
```

包不含厂商库、许可证、凭据或完整固定平台。`handoff/team/server_config.json`及运行器声明原服务器工具/库路径；每次运行将实际使用的输入指纹写入回执。在其他服务器上需要提供相同平台和工艺条件，不能以功能TCM替换ASIC宏模型。

上传通过开发板Linux FileZilla进入已授权独立目录。使用包内`handoff/team/unpack.py`进行ZIP哈希和安全解包，输出到新的目录，不能覆盖现有包。进入已解包目录后执行：

```bash
python3 - <<'PY'
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, 'workspaces/arch03/scripts')
from server_run import inputs
from systolic_b_soc import verify_firmware
from build_systolic_b_sequence import verify_firmware as verify_sequence
manifest = inputs()
assert len(manifest['files']) == 705
assert hashlib.sha256(Path('manifest.json').read_bytes()).hexdigest() == 'ac83363a9b3ea5cd88976b13f66a12a6543e68607def89b7ce40496eb359f177'
verify_firmware(Path('firmware'))
verify_firmware(Path('firmware_contention'))
verify_sequence(Path('firmware_sequence'))
print('INPUTS_AND_THREE_FIRMWARES_VERIFIED')
PY
```

实际任务数据从原SysMem ICB源接口响应，TB只预读文件。生产固件镜像不包含预装任务输入。每个任务冷启动；必须真实写共享SRAM并成功收到ACK后才供解码器使用，首源VALID等待至最终输出写ACK及排空全部计时。

## 独立新目录的基础复现顺序

以下为新复现示例，当前已有队列时不重复启动。每条命令完成并收回状态后才进行下一条；所有阶段通过团队协作锁排队。

```bash
python3 workspaces/arch03/scripts/server_run.py systolic_b_soc --session b_repro_asic14
python3 workspaces/arch03/scripts/server_run.py systolic_b_synth --session b_repro_synth
python3 workspaces/arch03/scripts/server_run.py systolic_b_sequence --session b_repro_sequence
python3 workspaces/arch03/scripts/server_run.py systolic_b_contention --session b_repro_contention --cases layer_01 extremes
```

默认ASIC和gate均包含12层、extremes、rounding共14例。`systolic_b_build`只编译，不是功能通过；本地pin mock、端口观察夹具或旧v2/R4结果不能替代这里的真实ASIC/E203执行。

读取新综合summary与state确认同一阶段passed，再由实际summary计算哈希并绑定后续命令：

```bash
B_SYNTH_RUN="$PWD/runs/b_repro_synth/systolic_b_synth"
B_SYNTH_SHA=$(sha256sum "$B_SYNTH_RUN/summary.json" | cut -d ' ' -f 1)
python3 workspaces/arch03/scripts/server_run.py systolic_b_timing_audit --session b_repro_timing --synth-run "$B_SYNTH_RUN" --synth-summary-sha256 "$B_SYNTH_SHA"
python3 workspaces/arch03/scripts/server_run.py systolic_b_gate --session b_repro_gate14 --synth-run "$B_SYNTH_RUN" --synth-summary-sha256 "$B_SYNTH_SHA"
```

综合必须来自B新网表，核实92个内部小宏、128个复用大宏、无锁存器/组合环、声明条件下setup/hold及项目面积≤2mm²。严格范围审阅需要查看约束、结构告警、时钟与例外，不能仅以一行正裕量代替。门级是同网表功能仿真，不含SDF；工具直接禁止B gate通过`--activity-cases`产生大VCD。

## 最终批量、SAIF和功耗

当前执行的`systolic_b_validation_queue.py`完成后，仅生成`validation_complete_review_required`。它不会自动授予时序或面积合格。源码候选记录`source-candidate-freeze`也不能用作最终队列要求的`freeze-review`。

独立审阅实际ASIC、综合、gate、sequence和contention五个摘要后，准备绑定各自路径与SHA的`freeze_review`和最终请求。已有`systolic_b_finalize_queue.py`核验全部来源后按以下顺序执行：

1. 新干净目录ASIC14复现及被动调度统计。
2. B自己的100样本×12层，一次编译检查30,412,800输出；不续旧37组，不继承R4的1200。
3. 如原生SAIF小试通过，使用受保护的R4 L01相同网表、固件及完整窗口重放，核对整数输出和窗口。
4. 原生SAIF与既有VCD功耗对照：整机及主要模块差≤1%，否则保留失败并停止该功耗路径。
5. B同网表12层完整SAIF、活动范围/驻留审核和12层系统功耗。

固定内部100样本数据目录为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA为`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。批量入口逐例保存输出、CPU/IRQ/WFI、窗口和来源回执，空间按实测例大小加20%余量及2GiB保留检查。旧R4的原始VCD仍保留，SAIF方法尚未实测通过。

最终队列命令接口：

```bash
python3 workspaces/arch03/scripts/systolic_b_finalize_queue.py --request <实际请求JSON> --request-sha256 <该请求SHA256> --session <唯一新队列名>
```

尖括号是待实际证据填写的占位符，不是可直接执行的值。最终队列不自动导出或批准；失败阶段保留独立目录，不原地重试。

## 报告与赛事材料

`systolic_b_report.py --request <报告请求JSON> --output <新报告目录>`重新核对实际输出和所有绑定来源，生成JSON、逐任务CSV、汇总CSV、中文报告与哈希回执。12层功耗按完整任务时长加权，同时保留逐层数值及算术平均。内部100样本浮点误差在逐位核对B输出后复用固定参考SSE/能量汇总，不称为新的浮点前向或官方600样本验收。

报告数值与独立工程审阅并列阅读。原DC实际周期6.666666ns；若映射SDC序列化发生舍入，记录PT真正导入值，不能把精确交付副本误写成已重跑PT。功耗始终注明布局前估算及未知活动/模型限制。最终R4/B对比只能使用同一配置的功能、面积、时序、吞吐和功耗，不拼接旧v2面积或R4功耗。

当前R4完整交付退路见[原交付入口](ICB32_DELIVERY_20261111.md)。B未完成硬性验收前，不替换它。

## 提交附件与评分证据对应

11月12日再次读取用户提供的赛题原图：`赛题图片11.webp`至`赛题图片14.webp`，印刷页码10–13/14。原图确认功能/数值40分、SoC/综合/复现20分、创新20分；效率得分相对同组合格设计计算，不能由本项目单独数字预测名次。官方面积上限2.25mm²，本项目继续采用更严格2.00mm²。每项硬性条件通过后才能进入效率及创新评分。

| 提交内容 | 当前入口与状态 |
|---|---|
| RTL、驱动、布局和参数转换 | 固定包、[B接口](SYSTOLIC_B_ABI.md)、[v3布局](SYSTOLIC_B_LAYOUT_V3.md)、`scripts/systolic_b_codec.py`。ABI末尾旧开发状态不覆盖最新验收表 |
| 软件数值模型与浮点误差 | `scripts/numeric.py`、`scripts/evaluate.py`、`scripts/systolic_b_precision.py`。Q12数学规则沿用[数值说明](NUMERIC_FORMAT.md)；该旧文档的8路LOAD/ITCM加载示例不是B传输路径 |
| 实际ASIC和综合前后功能一致性 | B自己的ASIC14已通过；同网表gate14、最终1200与干净目录复现等待本轮实际结果 |
| SDC、综合网表、时序和面积 | 等当前synth02的实际工件与独立审阅；源代码宏数与旧v2结果不能代替 |
| SAIF/VCD、整机功耗和能耗 | 原生SAIF小试、R4同窗口交叉核对、B活动12/功耗12均待；不提交空占位功耗为零 |
| 创新对照及答辩 | [B创新说明](SYSTOLIC_B_INNOVATION_20261112.md)、R4完整交付证据；B新增PPA齐备后补同配置对照表 |
| 版本与校验值 | 包manifest、源码候选记录、每阶段summary/state、报告receipt及实际库/网表/活动哈希 |

原图明确性能用冻结后统一抽取的12任务，并按每层3%门槛检查；当前12层与100样本为内部数据，不能称官方抽样。未标注电路不能当零活动，未建模SRAM不能当零功耗。正式附件入口、大小等用户暂缓提供，不影响继续验证；服务器路径与哈希清单只表明产物位置，不等于已经向赛事入口提交附件。
