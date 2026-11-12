# N1缩位RTL与本地验证交接

2026-11-13，执行`IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`的N1阶段。源码目前在个人分支工作树，以[小型证据JSON](../../handoff/team/evidence/N1_RTL_LOCAL_20261113.json)的SHA256锁定；本记录不是服务器或阶段最终验收。

## 实现完成

新增五个独立N1模块，B0原RTL及公共transport未修改：

| 文件 | N1改动 |
|---|---|
| `rtl/arch03_n1_systolic5x16.sv` | 80个PE；X14/W12传播及偏斜，乘法26位，累加/捕获32位；原块号、首末项、暂停与64项语义不变 |
| `rtl/arch03_n1_requantize.sv` | total33输入，34位绝对值与舍入临时值；半值远离零及signed16饱和 |
| `rtl/arch03_n1_linear16x5.sv` | X响应/队列70位，W192位，bias/slot_bias32位，显式符号扩展33位相加；可观察`converted_total[80]` |
| `rtl/arch03_n1_decoder.sv` | 保留B0 v3段顺序与无损编码算法；只接受layout4和numeric标识；严格拒绝非法X/W/b容器 |
| `rtl/arch03_n1_accel.sv` | version=`4b575306`，capability=`000505bf`，只读0x08c=`000e0c20`；layout=`00100004`与SHIFT10启动检查 |

保留32位ICB、SOURCE_CREDITS=3、32字输出FIFO、共享写ACK后发布、原调度及加载顺序。X60/W32个128×16物理宏不变；实际SoC总宏数还需服务器新综合核对。新增`READ_LATENCY`参数默认1，仅本地额外验证2拍响应。

X和W继续装在16位容器中；bias低16/中16/高8三个半字不缩流量。第三半字高8位必须0，低8位必须等于新bias bit31的8位符号扩展；middle和high同拍时使用本拍middle的符号。DMA解码器和直接debug core分别检查，非法数据不发布有效bank。

数值最坏范围也已核对：64项累加位于[-1073610752,1073741824]，加任意signed32 bias后位于[-3221094400,3221225471]，分别适配signed32和signed33。此结论不代替RTL逐位检查。

## 已通过的本地验证

| 验证 | 结果与证据目录（仓库根相对路径） |
|---|---|
| 阵列压力 | 10000随机块+32定向块，794560输出，total/result/sat、独立64MAC计数、II64、暂停/取消/复位/标签回绕通过；`local_runs/n1_systolic_array_20261113_010306_915102` |
| 完整DMA14 | 14任务、354816输出，逐坐标total33/result/sat零差异；`local_runs/n1_datapath_20261113_011023_922304` |
| 无复位A/B/A | extremes→rounding→extremes，SRAM1/2拍各一次，共6任务152064输出；`local_runs/n1_datapath_20261113_010850_998983` |
| 强制raw与关闭预取 | 1任务25344输出，反压与最终ACK延迟通过；`local_runs/n1_datapath_20261113_011341_886250` |
| 首层反压 | 1任务25344输出；`local_runs/n1_datapath_20261113_010726_111331` |
| 独立解码器 | 17例：压缩/raw、旧layout/numeric、坏头/模式/截断、X14/W12/b32扩展、187拍反压、取消与无复位重启；`local_runs/n1_decoder_20261113_010956_544455` |
| 直接core装载 | 9项，绕过解码器检查容器、SHIFT、长度、同拍/跨拍bias符号与DMA/debug恢复；`local_runs/n1_load_guards_20261113_011159_483032` |

完整DMA测试实际经过源ICB读、共享SRAM写ACK、提交FIFO、解码、宏缓存、阵列、输出FIFO与共享写回。检查每个物理宏的读写冲突、输出坐标唯一性、恰好64次MAC、冷启动无缓存有效残留、最后写响应前不得DONE，以及取消不能撤回已呈现且反压的请求。输出CSV固定为`row,col,result,saturated,total`，按坐标核对。

固定12层在本地pin mock、READ_LATENCY=1、prefetch=1、jitter=0时平均完整周期29711，按150MHz折算5048.6351856 task/s。逐层为30547、29943、29619、29699、29287、28983、28631、28727、28639、29423、30591、32443。这是本地数据通路结果；没有执行E203，不应填入真实ASIC/E203最终成绩栏。新量化也改变了编码长度，不能把全部变化归因于缩位硬件。

## 尚未完成与恢复入口

N1真实ASIC/E203十四例、CPU竞争/恢复、100×12任务、厂商宏、综合面积/150MHz时序、同网表门级及活动功耗尚待根代理的独立服务器入口完成。N1没有面积、功耗或单任务能耗验收值，不能用0或B0值占位；N2不能启动。

本子任务没有连接远端、启动服务器队列、提交Git或改动B0。本地仿真均已结束，无需重启。唯一早期工具失败是WindowsApps的`python`别名不可启动，已改用既有venv解释器，没有产生RTL失败或残留作业。

本地复现工具为`local_verify_n1_array.py`、`local_n1_datapath_verify.py`、`local_verify_n1_decoder.py`、`local_verify_n1_load_guards.py`。DMA工具接收`--source <group8源>`与`--data <N1 prepared>`；`--next-case rounding`开启无复位A/B/A，`--latency 1 2`检查SRAM响应延迟，`--raw`强制整流raw回退。成功输入是`workspaces/arch03/local_runs/n1_data14_20261113_02/{source,prepared}`，由数据代理重新量化原固定12层并生成两个N1定向用例。

## 门级与EDA工具准备增量

新增`n1_gate.py`、`n1_gate_monitor.py`、`n1_timing_audit.py`、`n1_structure.py`，12项本地工具测试通过，其中生成门级观察器的7场景通过XSim夹具核验。证据见[EDA工具小型回执](../../handoff/team/evidence/N1_EDA_TOOLS_LOCAL_20261113.json)。夹具仅模拟公开针脚及两次结果交接，没有执行E203、DUT乘加或实际映射门，不能称门级验收。

按根代理明确的最终范围，真实ASIC十四例及1200任务仍要求actual total/result/sat五列。门级十四例独立使用实际写ACK的四列`row,col,result,saturated`，明确`internal_total_observable=false`、`total_checked=false`。不将参考total填入捕获，不修改`n1_data`严格五列检查。若六个实际映射模块的针脚缺失、宽度/方向错误或与冻结综合清单不同，门级工具直接失败；没有保留内部别名的`dont_touch`。

结构审查另从实际`mapped.v`核对80个PE、80个requant、一个array，以及X14/W12 token、sum32及requant value33的真实边界宽度；这属于静态映射证明，不是动态total捕获。缺失或优化后无法识别的边界必须明确失败并单独调查。

时序工具只读原DDC，要求原150MHz task-mode约束逐字一致，保留原四条CDC例外，不增加门控豁免或宽泛false path。面积继续1.20mm²、92小宏+128大宏。工具输出均保留`strict_timing_verified=false`，等待真实报告审查；没有服务器运行记录或N2实现。
