# N1 SAIF、功耗与报告工具准备

有效计划：`IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`。本轮仅新增N1工具，不修改B0工具，不实施N2门控，不启动服务器作业。

## 新增入口及身份

- `scripts/n1_saif.py`：`verify(cfg, run, gate, gate_sha, qualified, qualified_sha, cases, call)`。要求自己的N1门级14例、完整12层固定顺序、真实IRQ/WFI和已通过的R4 SAIF/VCD方法交叉核验。只增加调试可见性并回放已冻结门级命令；原网表、固件、源、完整窗口和输出不能改变。记录原始SAIF及0/1/X/Z驻留信息，保留VCS合并TX语义，不将未知活动当零。
- `scripts/n1_power.py`：`estimate(cfg, run, activity_run, activity_sha, case, call)`。每次读取一个自己的N1完整窗口SAIF，覆盖E203、互连、相关SRAM和加速器。固定92个内部小宏及128个复用宏，单列层级/SRAM数值避免重复相加。保持SS、0.99V、125°C，导入独立精确6.666666ns约束并验证PT实际时钟。原综合SDC保留。采用原已验证的通用PT报告解析器，但重新核验N1身份、220宏、映射、单位及所有输入，不继承B0数值或PASS。
- `scripts/n1_report.py`：请求schema=`arch03-n1-report-request-v1`，要求`asic`、`synthesis`、`gate`三个`{run,sha256}`引用；可追加`activity`、12个`power`引用、自己的`batch`、`history`。可用`baseline={report:<冻结B0的report.json>,sha256:<哈希>}`仅比较原始数值。输出新N1 JSON、逐任务/汇总CSV和中文报告。

固定数值身份`000e0c20`、layout `00100004`、SHIFT10。新报告schema为`arch03-n1-evidence-export-v1`，不接受旧Q12报告或旧100样本批量作为新N1证据。

## 观察范围与阶段闸门

- ASIC RTL/E203使用严格五列`row,col,result,saturated,total`，核对实际signed33 total。自己的1200例必须重审30412800个结果与total。
- 门级采用主代理确定的实际端口/写响应四列`row,col,result,saturated`；`internal_total_observable=false`、`total_checked=false`。SAIF回放使用门级自己的四列检查器和`ARCH03_N1_GATE_PROOF`，不填参考total伪造第五列，也不宣称门级核验了内部total。ASIC与门级各自保留捕获哈希，按相同参考、坐标、结果/饱和和窗口比较。
- N1报告不引用旧Q12 SSE/NRMSE。当前新100尚缺完整同批浮点源，整数通过与浮点精度分别报告；NRMSE、裁剪数未知时为null，不填零。
- 平均系统功耗采用12个完整窗口的时间加权值，单任务能耗为12任务总能耗/12。缺任何一层功耗时，汇总平均功耗及能耗保持null。
- 项目面积数值限制为1.20mm²。相对B0的能耗不增加、平均功耗增幅≤10%分别给出原始数值判定；未完成未知活动、模型、精度、时序或面积归属审核时，不批准阶段准入。
- 报告导出器只整理证据，始终保留`stage_handoff.allowed=false`和独立审核待办；不会仅凭数值收齐启动N2或转移B0资格。
- 存储预算保留20%余量和2GiB公共剩余空间；不删除旧证据，不盲启普通VCD。

## 已验证与尚未验证

12项本地逻辑/Tcl检查通过，覆盖精确约束、SAIF入口与220宏、完整窗口加权、缺测不填零、非法数值/不一致能耗、1.20mm²及相对B0数值限制、旧身份或轮询门级拒绝、证据篡改、固定12层和空间余量。

- 回执：仓库根`local_runs/n1_ppa_tools_20261113_01/summary.json`
- SHA-256：`77de3d5007e6ea05c0bd808d7432221fa715f84e321ebe19f3f26e4224cdbfe2`
- 日志：同目录`tests.log`。
- 所有回执明确`actual_N1_SAIF_replay_executed=false`、`actual_N1_PT_power_executed=false`、`system_power_verified=false`。

N1新网表尚未交给本工具执行。完整SAIF回放、PrimeTime功耗、真实覆盖/未知影响、功耗差异、最终报告实际多阶段贯通均待服务器。上述本地通过仅说明工具逻辑准备完成，不能当作N1 PPA通过。

已尝试路径：首次读取含中文的旧报告源码遇到Windows默认GBK解码失败，在写入新报告之前停止；随后明确UTF-8读取并生成独立N1文件。未修改旧文件、未生成虚构PPA结果。

恢复时先核对主计划、最新检查点及实际N1 gate/synthesis回执。正式启动仍由主代理统一检查进程、锁和可用空间。本子任务未连接远端，没有待续服务器作业或本地长进程。
