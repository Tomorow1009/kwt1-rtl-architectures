# N1 综合结束后的最小检查清单

2026-11-13，只读准备，未执行下列服务器命令。生产 RTL 仍为 `9305c6948c764fed01fe86b20bb3db94170299ab`。最后由根代理提供的状态：原综合 169157/DC 174746 仍运行；共享盘约 1 MiB 可用，后续输出只在已登记私有 `/tmp`。开始时必须重新检查实际状态。

后续增量：根代理确认原综合已于04:15:04完成；summary SHA为 `cc7f26115f3158fb69f4575f28b5dfde4dd8e5b3aeefda2a927928ad8418db31`，初读0 latch/220宏/DRC清、项目保守面积0.9511486879005002 mm²。仍需映射和声明范围审核。当前VNC shell为 **tcsh**，因此不能直接粘贴本文Bash变量/数组示例；交互查询采用 `python3 -B -c` 构造完整参数。任何摘要在生成命令前须通过 `re.fullmatch("[a-f0-9]{64}", value)` 并核实际文件。structure01在configure前因操作者命令误抄BASE摘要失败，未建session/未取得锁，不是硬件失败；保留driver，后续使用新02。本文BASE摘要经长度和regex核验为正确64字符。

## 1. 先确认原作业终态及身份

在服务器已有 Bash 中设置本次专用变量；不是新建运行包，也不启动综合：

```bash
task_n1_runtime=/tmp/s4_21usr_n1_20261113_0210
task_n1_base="$task_n1_runtime/light-light126-n1-v4-20261113_013211-9305c6948c76"
task_n1_ops="$task_n1_runtime/light-light126-n1-v4-20261113_022722-41b0846ce719"
task_n1_synth="$task_n1_base/runs/n1_synth01/n1_synth"
task_n1_lock=/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock
ps -p 169157,174746 -o pid,ppid,stat,etime,args
cat "$task_n1_base/runs/n1_synth01/state.json"
df -h "$task_n1_runtime" /storage2/2026contest/server4/s4_21usr/Desktop/IC
```

若进程仍运行、state 未完成或原锁仍在，先读取原锁 owner，**不启动下面的阶段、不清锁、不重启综合**。进程退出但 state failed 时保留报告并诊断，不伪造 passed summary。

只有原 `stages.n1_synth.status=passed` 后才取得完整摘要身份：

```bash
task_n1_synth_sha=$(python3 -B - "$task_n1_synth" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); raw=(p/'summary.json').read_bytes()
h=hashlib.sha256(raw).hexdigest(); s=json.loads(raw)
r=json.loads((p.parent/'state.json').read_text())['stages']['n1_synth']
assert r['status']=='passed' and r['summary_sha256']==h
assert s['synthesis_completed'] is True
assert s['scope']=='n1_whole_soc_task_mode_preliminary_synthesis'
print(h)
PY
)
```

命令返回非零或摘要为空时停止。`passed` 在这里仅表示综合报告收集成功，不是时序、面积或阶段验收通过。

## 2. 先读已生成的证据，不重复启动 DC

以下检查绑定同一个 summary SHA、`mapped.v`/`mapped.ddc` SHA。逐项核原 `summary.artifacts`，不可混用 B0 网表或修复后的其他目录。

| 项目 | 必须满足的证据 |
|---|---|
| 数值身份 | 原五个 N1 RTL、固件/格式/数据和安装器哈希一致；新布局 `00100004`、NUMERIC `000e0c20`、SHIFT10。 |
| 时钟/库 | SS、0.99 V、125°C，metrics HF `6.666666 ns`、LF `66 ns`；原 task_mode.sdc 完全一致。mapped.sdc 文本可能将时钟近似写为6.667，不能将其近似值冒充精确约束。 |
| setup/hold | metrics.max/min 均非负，并审阅 timing_max/min、所有路径组及 check_timing。正 slack 不自动豁免未约束路径或被禁弧。 |
| 0 latch/loop | `metrics.latches=0` 且 `latch_inventory.txt` 空；check_timing 含实际 Checking loops，无 TIM-209/loop breakpoint。其他 check_design/check_timing 警告逐类解释。 |
| 220 宏 | 92×RAMSP128X16、128×RAMSP4096X16；叶清单加速器92、ITCM32、DTCM32、共享64。另按真实路径核 X bank0..59、W bank0..31各恰一实例。 |
| 面积 | `area_inventory` 唯一叶实例和官方宏面积、单位证明与整机面积相等；`conservative_budget_mm2<=1.20`。其口径是全部SoC标准单元+内部92宏，仅剔除128个复用大宏。整机面积另列。 |
| 全部 DRC | `constraints.rpt` 只有明确 clean marker 且无任何违反；不得仅过滤 transition/cap 而漏 setup/hold、fanout、multiport、clock-gating、pulse等。解析未知行保持待审。 |
| 约束范围 | 只存在原四个 LF timer stage0 CDC 例外；核原时钟传播/门控检查、固定启动/PLL条件、SysMem max1/min0输入输出预算和复位释放范围。无新增宽泛 false-path/disable-timing。 |

现有 `n1_synth`、`n1_gate.verify_synthesis` 并不强制全部这些准入条件；它们保留 diagnostics-only 标记。`conservative_budget_within_1_2mm2`、`setup_hold_nonnegative` 为 false 或 latches 非零时，即使 runner 打印 PASS，也不能宣布验收通过。

## 3. 用已部署 OPS 读取 BASE，仍占原共享锁

以下公共参数按已登记身份固定。每阶段使用全新 session；如果同名目录已存在，先读其终态，不覆盖或重跑。共享盘写满时需确认原锁目录仍能正常创建；**不换成私有锁**。

```bash
cd "$task_n1_ops"
task_n1_args=(--runtime-root "$task_n1_runtime"
  --runtime-manifest-sha256 0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e
  --runtime-evidence "$task_n1_base" 73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d
  --synth-run "$task_n1_synth" --synth-summary-sha256 "$task_n1_synth_sha")
python3 -B workspaces/arch03/scripts/n1_server.py structure --session n1_structure01 "${task_n1_args[@]}"
```

该阶段纯解析，无 DC；输出为 OPS `runs/n1_structure01/n1_structure`。需检查 numeric counts、所有 `expression_present_requires_review`、其他 warning 及 no-load driver 是否与 declaration-only 清单一致。零 LINT-8/28、端口被优化或未知网表格式可能使当前解析器停止；先确认原报告/实际模块，不为观察增加 dont_touch。

仅当原 DRC 非清或存在需解释的驱动/连接问题时，在 structure 结果读取后单独运行：

```bash
python3 -B workspaces/arch03/scripts/n1_server.py drc_audit --session n1_drc_audit01 "${task_n1_args[@]}"
```

该阶段读原 mapped.ddc，不编译、不改网表；核 `constraints.extraction_complete`、每个违反、真实驱动/负载/上游输入和 missing/unresolved。目标由本次报告生成，不复用 B0 旧 U 号。空 clean 报告无须为了再取得一次相同结论启动 DC。

仅当 TIM-134/高扇出延迟模型仍待解释时单独运行：

```bash
python3 -B workspaces/arch03/scripts/n1_server.py timing_audit --session n1_timing_audit01 "${task_n1_args[@]}"
```

该工具只提取 threshold1000 高扇出网络和映射接口，**不是独立严格 STA 验收**；无 TIM-134 审核需求则不额外运行。两个诊断都有 `strict_timing_verified=false`，必须人工完成声明范围审核。

## 4. 数值映射仍须补的最小证明

结构工具只验证 80个PE、1个array、80个requant 的边界。PE x_in26/w_in24 包含控制标签；它们不是乘法器的26×24输入。array70/192/2560、PE result_sum32、requant value33 不能单独证明内部运算缩位。

从实际新 mapped.v/reference清单取得80个PE路径及各 unique reference，逐种reference核一次并关联全部80实例：

1. 乘法独立数据源恰为 X[13:0]、W[11:0]，signed26乘积；DW形式端口若更宽，明确高位是否只是符号复制。metadata不能进入乘积。完全门级展开时报告实际逻辑锥，不虚构“80个乘法宏”。
2. 32位 accumulator状态及32位 next_sum、当前乘积符号扩展、first覆盖/last含当前项、advance保持；不要把result保存寄存器或计数器混作累加状态。
3. bias32、sum32各显式扩展33后相加，total33进入转换；requant内部34位绝对值/舍入暂存为防溢出设计，不是旧宽位残留。

若实际映射将相关状态合并/重命名，按连接解释；不能仅数寄存器名放行。只有真实格式出现后再准备最小只读查询，不猜DW名称或改 frozen 工具。详见 `N1_MAPPED_REVIEW_DECISIONS_20261113.md`。

## 5. 后继判定

所有上述检查通过才能写“本N1声明任务模式的综合/面积/时序审核通过”，仍不能写物理签核。若要等价升驱动修 DRC，必须另立运行目录及网表身份，重做对应门级与活动，不把修前/修后最佳结果拼接。

自己的1200、同网表无SDF门级14、完整活动/功耗12及匹配的100条原始浮点精度仍各自验收；本清单不替代这些项目，也不授权进入 N2。真实RTL检查total/result/sat；门级只检查实际写ACK的result/sat，明确total不可观察。

本次只新增清单，未改冻结工具、RTL或约束，未启动服务器命令、重复本地测试或综合。
