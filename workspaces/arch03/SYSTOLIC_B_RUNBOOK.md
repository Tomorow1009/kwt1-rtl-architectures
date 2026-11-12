# 5×16脉动B复现与结果收回

本手册对应生产硬件`63da6ba0d6d9c931fbe4a4bdfb9f233d4502ce86`、v3布局`0x00100003`、source credits=3和IRQ/WFI固件。验收状态以[独立验收表](ACCEPTANCE_SYSTOLIC_B_20261111.md)为准。已完成自己的1200任务、ASIC14、DRC06同网表gate14和干净目录ASIC14；活动12和功耗12仍在进行。下列复现命令只供新环境使用，不能在现有运行目录重复启动。

## 当前作业，接手时先检查

**11月12日20:34：唯一运行队列为power_final01，driver320367/activity child320434；L01–L03活动已完成，剩余9层继续，尚无B功耗数值。** 请求`operations/b_power_final01_request.json`已核验并执行，SHA为`e99f9e51d8ddbff5c3921e01d15aac99a7b851018884857089044ccded5479d0`。不要重新生成或启动。当前恢复入口为[20:26检查点及增量](../../CONTEXT_CHECKPOINT_20261112_2026_SYSTOLIC_B.md)。

原final02于19:13结束：1200任务、30,412,800输出、零失败。R4 crosscheck02于19:18通过，主要模块及整机SAIF/VCD差≤1%；1060默认声明逐个证实直接及叶连接均为空。失败的crosscheck01保留，不能把数值接近当作跳过连接审核的理由。

实际接续及最终报告使用16文件工具`operations/systolic_b_tools_4b58ff0`，manifest SHA `bf8e214e70ac92b17b3ecc0c41497995ac0b1d0aa5c483a9662b0225b08f6289`。受测基础包`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`的709输入manifest SHA为`39b127636ecaf61d2cd950efd2f83ef923cacf5274c6f4b3d363cbdb9a51155d`，从未修改。

power_final01只接续activity12→power_l01..12→最终report_request，不重复ASIC14、1200、门级14或R4捕获。终态后再调用同ops的`systolic_b_report.py`，使用实际生成的请求和新的输出目录。工具将独立复核输出、浮点误差来源及完整窗口；报告导出本身不自动批准时序、面积或未知活动影响。

DRC06综合及其gate02均已完成。实际协作锁位于`server_config.server_root`下`.arch02_team_lock`。恢复时先核对队列、实际进程、锁和空间，不能因旧状态文件仍写running就重启作业。

FTP421期间已经通过授权VNC部署上述工具，当前无需重传。gate02使用已核验d48副本，最终功能队列使用52f37cc副本，当前功耗和报告使用4b58ff0副本；这些来源分别保留。直接从ops调用时使用`env PYTHONPATH=workspaces/arch03/scripts python3 <ops脚本> ...`，不要用旧包工具覆盖新修复。

R4 replay01摘要为f7d542dd…3d21a，crosscheck02摘要为a0a9bc62…c662d26，已由接续请求绑定，无需重放。B功耗导入独立`mapped.precise.sdc`，实际HF周期必须6.666666ns；历史R4导入6.66667ns的舍入事实保留披露。

早期运行及失败身份见[阶段报告](SYSTOLIC_B_PROGRESS_20261112.md)和根目录带日期检查点；不续跑validation01/02或旧8路/R1追加队列。

旧synth01及validation01因磁盘满退出，状态文件保存失败而停留在running/waiting，没有最终网表。用户授权的五次旧波形清理已完成，累计524880555968B，保留全部R4/B及旧小型结果、源码和重建输入。旧原始波形若再审计需要重生成；详见[第五次回执](../../handoff/team/evidence/SERVER_WAVE_CLEANUP_FIFTH_20261112.json)及此前四次清单。不要重复执行清理。

## 固定包与输入

当前本地交付工具包：`light-light126-systolic-b-v3-20261112_195820-f56b642e28a0.zip`，11,397,311字节，722项输入，尚未上传或取得该新包的服务器复现。实际受测服务器基础包仍为上文ced709包。详见[新包身份核对](../../handoff/team/evidence/SYSTOLIC_B_DELIVERY_PACKAGE_20261112.json)：诊断sequence ELF容器哈希不同，但入口、全部加载段和boot镜像相同；不能称全部文件字节相同。

| 内容 | SHA-256 |
|---|---|
| ZIP | `4654aa32bd8d89fc8d58f2228d01cf998c2924924f2817fa3d8fa6be423ba479` |
| 包manifest | `47f6350037218b6d712cf3c24f5fa0e2f0759c262826ee9b68c1c044bca736c2` |
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
assert len(manifest['files']) == 722
assert hashlib.sha256(Path('manifest.json').read_bytes()).hexdigest() == '47f6350037218b6d712cf3c24f5fa0e2f0759c262826ee9b68c1c044bca736c2'
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

### 当前DRC06映射的复现边界

上述从RTL开始的`systolic_b_synth`命令只产生新的综合结果，**不会自动得到已受测DRC06的零违规结论**。当前合格映射经过独立、保留历史输入的DRC04→05→06修复链：先执行仅设计规则增量优化，再对四个实测驱动及其三个上游NOR3作等价升驱动。脚本检查旧单元身份、库引脚方向与逻辑函数，不改变原任务约束。

当前最终DRC06来自同ced包`runs/systolic_b_v3_drc05/systolic_b_synth`，该种子摘要SHA为`55fcf35b3d2d01ea782f7f543bc00b1ae49078e9f1b9c66534ab33c1e8765bbe`。精确重放这一修复使用新session调用已核验ops的`systolic_b_synth`阶段，并以`--synth-run`、`--synth-sha256`绑定该原种子。入口为`operations/systolic_b_tools_4b58ff0/systolic_b_ops.py`，其`--bundle`、`--bundle-sha256`和`--ops-sha256`见本页当前作业段。原种子、原编译库路径和摘要均须可读且哈希一致；不复制厂商库到提交包。

修复脚本的两种定向方案显式绑定原DRC04/05摘要，因此不能把全新综合摘要改名后直接冒充原种子，也不能据源码相同而借用原DRC06 PASS。新综合网表需要自己的约束、面积、门级与功耗审核。当前干净目录复现是独立重新编译的真实ASIC/E20314；受测DRC06网表另有自己的14例功能门级。它们不等于从任意新版工具或布局条件自动复现相同时序。

## 最终批量、SAIF和功耗

已完成的`systolic_b_validation_queue.py`仅生成`validation_complete_review_required`。它不会自动授予时序或面积合格。源码候选记录`source-candidate-freeze`也不能用作最终队列要求的`freeze-review`。

独立审阅实际ASIC、综合、gate、sequence和contention五个摘要后，准备绑定各自路径与SHA的`freeze_review`和最终请求。已有`systolic_b_finalize_queue.py`核验全部来源后按以下顺序执行：

1. 新干净目录ASIC14复现及被动调度统计。
2. B自己的100样本×12层，一次编译检查30,412,800输出；不续旧37组，不继承R4的1200。
3. 如原生SAIF小试通过，使用受保护的R4 L01相同网表、固件及完整窗口重放，核对整数输出和窗口。
4. 原生SAIF与既有VCD功耗对照：整机及主要模块差≤1%，否则保留失败并停止该功耗路径。
5. B同网表12层完整SAIF、活动范围/驻留审核和12层系统功耗。

固定内部100样本数据目录为`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`，manifest SHA为`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`。批量已逐例保存输出、CPU/IRQ/WFI、窗口和来源回执。空间按实测例大小加20%余量及2GiB保留检查。R4原始VCD仍保留，SAIF方法已实测通过。

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
| 实际ASIC和综合前后功能一致性 | B自己的ASIC14、同DRC06网表gate14、最终1200及干净ASIC14均已通过；最终报告独立复核待完成 |
| SDC、综合网表、时序和面积 | DRC06实际工件及范围限定审核已完成，面积上界1.0990947mm²、任务模式150MHz通过；无物理签核 |
| SAIF/VCD、整机功耗和能耗 | 原生SAIF小试、R4同窗口交叉核对通过；B活动3/12，其后功耗12待完成；缺值不记零 |
| 创新对照及答辩 | [B创新说明](SYSTOLIC_B_INNOVATION_20261112.md)、R4完整交付证据；B新增PPA齐备后补同配置对照表 |
| 版本与校验值 | 包manifest、源码候选记录、每阶段summary/state、报告receipt及实际库/网表/活动哈希 |

原图明确性能用冻结后统一抽取的12任务，并按每层3%门槛检查；当前12层与100样本为内部数据，不能称官方抽样。未标注电路不能当零活动，未建模SRAM不能当零功耗。正式附件入口、大小等用户暂缓提供，不影响继续验证；服务器路径与哈希清单只表明产物位置，不等于已经向赛事入口提交附件。
