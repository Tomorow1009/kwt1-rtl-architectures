# 原8路同源加载版本时序对象审核

本记录仅对应1aa `runs/mmio8_source_synth01/mmio8_synth`，摘要SHA `0e33c1d045d063829c34e97b7ba10109d446c381c95fa7003449d0bbc6159fc9`。该参考版本没有DMA，不能继承旧BEGIN窗口、synth07或DMA16的审定。

同一SS、0.99 V、125°C、6.666666 ns条件下，当前报告setup +0.00000905991 ns、hold +0.00131008 ns，0锁存器；数字非负不自动构成全项时序接受。原8路完整14门级与12活动已排在剩余11层MAC扫描之后；首层已通过，完整对照仍待运行。

## 实际对象证据

- ecf `runs/mmio8_timing_review01/mmio8_timing_audit`于11:34:30.932198完成，摘要SHA `e9df8a749359e800f4218b284f4c17a0682ecf8d257f6067e9943bcd2fcea95f`独立核验。只读原DDC得到3条高扇出网络：`u_e203_subsys_top/core_csr_clk`、`u_e203_subsys_top/hfclk`、`u_e203_subsys_top/u_sirv_aon_top/crossing_clock`，网表与约束未修改。需结合实际时钟路径和工具扇出假设审定。
- a745 `runs/mmio8_struct_review01/ports.json` SHA `0b3918d6b1cc56cf7cba9a93d3b2a7caa86bbb64eeec175988c11c1969e85b57`独立核验。1179模块中3687端口警告全部仅有声明，无逻辑引用，3574输入/113输出。完整警告计数LINT-1/2/8/28/32/33为4/88/88/3599/3600/411；其余类别仍需解释，不把端口诊断当整体批准。
- 原e777首层PT摘要SHA `3321b70941d2667baaf5e143bcaf9db4e53cb01d0ac33f3a34543fe144a48eba`。实际189 no_clock对象为186 JTAG DTM和3 JTAG reset同步，包含182 CK和7 CKN；mapped.sdc实际TCK/TMS/TDI均case=0。首版只处理CK被拒绝，已保留CKN负沿对象。
- 11:54对原disabled_timing.rpt全表初步统计为55719行：C40708、p12819、c1991、d201。没有u/U/l/L/f标志；每条实际条件仍需完整保留，不能只看前几行或用16路61740条替代。

## 可复现完整分类工具

新增`mmio8_timing_objects.py`，绑定原8路综合和PT摘要及阶段、逐工件SHA，完整保留no_clock对象和禁用弧的对象/From/To/Sense/Flag/Reason。要求表头、数量、唯一时钟引脚、完整终止及静态JTAG三项约束；未知格式失败，不过滤无法解析的行。禁用弧重复外观行仍逐条保留，以免遗漏不同条件。输出标记timing_verified/system_power_verified/physical_signoff均false。

本地7项新检查及20项相关检查共27通过，涵盖CKN、未知对象、截断/重复/异常表行、保留手工/回路禁用标志、混合来源拒绝及文件只读。**新工具尚未在服务器实际运行**，当前初步统计不是其验收结果。

请求格式为`schema=mmio8-timing-objects-request-v1`，`synthesis`和`power`分别含实际`run`和`sha256`；运行`python3 workspaces/arch03/scripts/mmio8_timing_objects.py --request <请求JSON> --output <新的对象JSON>`。只读报告，不启动EDA或重扫VCD，可与独占重作业并行进行轻量整理。

最终限定范围审定仍需原8路实际约束、全部结构警告、完整功能和面积归属证据。物理时钟树、寄生、活动JTAG、复位释放和启动过渡不在稳定任务模式综合结论内。
