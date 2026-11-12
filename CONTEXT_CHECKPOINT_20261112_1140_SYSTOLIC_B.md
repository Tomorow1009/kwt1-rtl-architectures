# 2026-11-12 11:40 起：B综合完成，修复验证工具

继续直接5×16脉动B计划，A取消，63da/Bv3/credits3已冻结，R4保留交付退路。重读AGENTS、有效计划、本检查点及08:30检查点。仍仅按授权删除旧MMIO8 L09–L12四VCD（112.42GiB）；R4/B受保护。

## 新综合完成，不得重跑

8d包`runs/systolic_b_v3_synth02/systolic_b_synth`完成，摘要SHA `3e0f88eeb4855a15f8743f820f587cd90df7e52a748d112e8fd5ba788dd86d03`。

- 周期6.666666ns；setup +0.0002141ns、hold +0.00249085ns。
- 92小宏+128大宏=220；锁存器0；最终组合环检查未检出环。
- 整机4621339.604708µm²；已识别新增0.9383510023010567mm²；含全部整机标准单元的保守预算上界1.0991231047009615mm²，低于2.00。
- 工程时序/结构审阅和门级仍待，不能直接称最终合格；物理签核未验。
- DC CPU6685s、elapsed6780s。旧synth01 ENOSPC失败现场仍保留。

## validation02与结构审计失败，均非新硬件失败结论

validation02在10:44:54启动sequence（PID1723），0.3秒后被`Sequence cases must exactly match firmware A/B order`拒绝；未运行仿真，也未启动contention、SAIF、timing或gate。队列没传--cases而默认14例，序列固件要求A=layer_01、B=rounding。

本地已改队列从核验后的固件manifest读取A/B顺序并显式传入，不放宽CPU检查。新增队列回归3项通过：两种A/B顺序、必需失败停止、可选失败保留并继续gate。子进程为替身，不是硬件证据。

旧8d结构脚本在实例扫描时报`Duplicate mapped instance .rst`，在写结构JSON前退出；不能记录成结构通过。原正则把命名端口连接续行当成实例。本地已改成两个合法Verilog标识符及行内空白，支持DC转义名，保留真实重复拒绝；2项定向测试通过。新的工具包待部署后对原网表重审，不修改网表。

## 现场和下一步

monitor因queue失败自行退出；VNC18874435/workspace3、新8d包shell，FZ关闭。没有活跃EDA或本地仿真（部署前仍须重查进程/锁）；最近154.744GiB是10:44历史值，不是实时空间。

result_ready和structure_ready均已执行；前者已读取，后者失败无JSON。网表误解析只读定位查询已Return，需看`b_structure_parser_actual.png`。timing_ready尚未输入。不要重复任何launch。

先提交本地工具修复和记录，生成新不可变包，验证生产RTL/三固件不变，FileZilla上传新目录。新validation03绑定已完成的8d synth02，不再综合，不重试旧session。之后新B实际sequence/contention、timing/gate14、冻结审阅、干净ASIC14及1200/30412800输出、SAIF/R4交叉核对、B活动12/功耗12。

原B ASIC14/354816仍通过，30502.3333周期/4917.6566task/s。新B自己的1200和功耗仍待。最后已核云端b79e1f52504f123505ab408df018c9e0a8d2b4d5；当前修复尚未提交上传。生产硬件、固件和约束均未改。
