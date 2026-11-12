# N1综合后只读审计准备与B0 DRC06对照

2026-11-13。本记录只涉及N1验证工具，没有修改冻结RTL、`n1_synth.py`、旧网表或约束，也没有连接远端或启动EDA。根代理最后提供的状态为冻结包`9305c69`已上传，真实ASIC14作业PID 130549于01:48:24启动；本子任务未独立查询实时状态，不能据此宣称作业完成。正式N1综合尚待根代理安排。

## 已核对的约束和差异

N1的`task_mode.sdc`与B0初始综合约束逐字一致，SHA256为`751410c789ed1b54f8d8400ae7e687785e6989073d34471913ee4cb7b6054020`。保持HF 6.666666 ns、LF 66 ns、全时钟0.1 ns不确定度、HF接口max 1 ns/min 0 ns、input transition 0.1 ns、output load 0.01；只有四个已有LF timer stage-0同步D端的具体CDC例外。没有加入宽泛clock group、SysMem false path或门控检查豁免。

B0最终DRC06并不等于初始综合：其在同一RTL和任务约束上，对实际检查出的4个驱动及随后3个上游驱动做等价升驱动，最终报告明确没有违反的约束。N1复用的是初始综合入口，不能套用B0的旧U编号或借用DRC06的PASS。即使N1 setup/hold非负，仍须检查max transition、max capacitance、多端口网络及其他约束。

B0最终参考为`ced0e139a01e`包下`runs/systolic_b_v3_drc06/systolic_b_synth`，summary SHA256 `b81780033ef65998c43a874b559e54da0d958524a040eff374b1e8f1a4824ced`。其setup +0.00010252 ns、hold +0.00249085 ns、92小宏+128大宏、0锁存器以及项目面积1.099094695900963 mm²仅属于B0。

N1新增数值容器校验控制实际写入使能，尤其同拍bias符号检查和传播到物理宏的store使能可能改变扇出与关键路径。缩位的面积/时序收益必须由新映射统计，不能凭位宽推算。当前没有发现明确组合反馈环；这属于源码审查，不能代替最终`check_timing`。

N1综合输入清单没有单列`install_systolic_b.py`这个`install_n1.py`的直接依赖，但冻结整包manifest与门级准备核对已经覆盖该文件。新只读工具另绑定原包manifest中的该依赖，不回写或伪造旧综合输入回执。

## 新增工具与验证

新增`n1_drc_audit.py`：

- `constraints_inventory(text)`保留约束违规原行、行号、分类及提取状态。分别记录报告行数、唯一查询对象数，不能把多个引脚行当作相同数量的独立网络。
- 仅存在唯一明确的`This design has no violated constraints`且无矛盾内容时标记`explicit_no_violations=true`。未知行、截断、缺少标记保持未完成，不自动当成0违规。
- `audit(cfg, run, synthesis, expected_sha, call)`验证原N1 summary、state、网表、约束、报告与库身份，然后通过原DDC查询本次报告里的实际对象。输出实际叶级驱动pin/cell/ref、相连端点数量与方向、驱动输入网络，以及可用的电气属性；缺少可选属性用`unavailable`表示，不按0处理。
- 对bus括号使用精确filter，不使用glob猜测。对象未解析、重复端点或缺少驱动记录均明确报错或未完成。工具不compile、不size_cell、不改约束、不写新设计；前后重验输入SHA。
- 结果恒为`strict_timing_verified=false`和`physical_signoff=false`。`constraint_report_clear`仅表示所选原报告明确无违规，不等于完整时序验收。

`test_n1_drc_audit.py`共8项测试通过，涵盖违规重复/换行、未知格式、明确clean标记、对象缺失、驱动记录完整性、bus名、禁止Tcl注入、原manifest补充绑定、只读查询脚本以及生成Tcl在collection夹具中的控制流。夹具不含真实DC模型，因此尚未证明服务器DC命令/属性支持。首版夹具的Windows Tcl临时文件访问异常已改为内存输出夹具；这是测试环境问题，不是RTL或EDA结果。

复现：在`scripts`目录运行`E:/fpga_race-two/.venv-kwt/Scripts/python.exe -m unittest test_n1_drc_audit -v`。小型证据见`handoff/team/evidence/N1_DRC_TOOLS_LOCAL_20261113.json`。

## 综合完成后恢复顺序

1. 根代理先读原作业/锁/空间和新summary终态，不能重启同一综合。校验N1 summary SHA及state，不以日志尾部零碎数字替代回执。
2. 读取该冻结目录的`constraints.rpt`、`metrics.txt`、`check_timing.rpt`、`check_design_mapped.rpt`、`latch_inventory.txt`、`area_inventory.json`。面积硬限1.20 mm²，预期92+128宏；setup/hold、DRC、结构、时钟/CDC各自记录。
3. 先用`constraints_inventory`离线列出实际违规；有需要时在正常串行协作锁内调用新`audit`。保留`constraint_inventory.json`和`drc_driver_inventory.tsv`原始记录。不自动改驱动或旧U号。
4. 用`n1_structure`检查真实mapped.v的80 PE、80 requant、一个array与sum32/total33等边界，用`n1_timing_audit`确认实际高扇出网络。无法观察边界须调查，不通过dont_touch硬件强留测试别名。
5. DC `write_sdc`可能把HF周期显示为6.66667；仍以metrics中的6.666666及原task_mode.sdc为准。交付/功耗用既有精确周期恢复工具，只修已识别的HF clock一行，保留原SDC并重核其余约束。
6. 如需映射修复，必须新目录、新网表及新门级/活动证据；保留原运行、约束、失败与库身份。旧B DRC03的重复库身份错误说明：同内容数据库换目录仍可能不适合对原DDC做增量编译，必须先确认原编译库路径。

已完成的是工具准备和本地工具测试。尚未完成N1服务器综合/DRC、真正mapped数值边界、门级、SAIF功耗、1200任务及完整浮点来源验收。不得进入N2。
