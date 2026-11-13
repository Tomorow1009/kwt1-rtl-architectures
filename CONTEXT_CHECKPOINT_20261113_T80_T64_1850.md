# T64传输过半、等待原T80队列 — 2026-11-13 18:50

恢复时先读有效计划 `workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md`、本记录、1839/1826记录及执行JSON。任务没有暂停。用户要求连续推进，**服务器旧8路任何数据、日志、波形、网表和报告均禁止删除、覆盖或归档后删除原件**。

## 实际状态

- 工作树 `E:/fpga_race-two/kwt1-t80-t64-g64`，个人分支 `codex/light-light126/n1-t80-t64-g64-20261113`。`861b7d2`已推送GitHub；此前`d611597`审查工具、`6bcb7ce`本地对照均已同步。旧工作树未提交修改不动。
- T80生产RTL仍`876b883`，前20条240任务、6082560个输出/total/sat零失败，ASIC14、真实CPU竞争及恢复通过。固定12平均112569周期（150MHz折算1332.5160568 task/s）。PPA/同批浮点关联仍未收齐，不宣称全项验收。
- T80唯一队列 `t80_finish02`、驱动PID14008，18:22:51启动。**最后一次服务器状态观察18:35:25.095956：running/t80_synth，free34212937728B。当前状态尚未再读，不能把旧观察当实时。** 目录及哈希详1839/1826记录；不重复启动。
- **本地exec会话60646正在通过VNC输入T64包。18:49:52读取进度70/141行，随后输出71/141。不要向VNC发送其他键盘输入。** 传输脚本`local_runs/transfer_t64_delta01.ps1`；实时位置`local_runs/t64_delta01_65d2507_verified/transfer_state.json`。先poll60646，完成后截图观察回执，不重启传输。
- VNC ID18874436、FileZilla ID20972102已本轮重新确认；使用开发板授权helper `F:/linux_fpga_try/ac820.ps1`。VNC工作区3，勿碰4。18:41截图确认终端仍接收Python heredoc文本；结尾标记为带单引号的`'T64_DELTA01_65D2507'`。FTP此前一次重试仍421、没有成功传包。
- 目标新bundle `light-light126-t64-v4-65d2507-delta01`，874文件，manifest `367eb3d21e0dcacc230f821be609805d9b1789bc3dd9ebca432e9f977f60c8ff`；目标ops `light-light126-t64-finishops-65d2507`，manifest `437a29f65ed61f1f389445ddd16fc457151b87f34fade3ca8548b44c338100f9`。尚未取得服务器重建完成回执，尚无T64服务器作业。
- T64硬件`e2e83ce`，工具包`65d2507`。本地10000随机+32定向、14例、延迟/反压/ABA、恢复和三类固件已通过。当前874文件运行子集还通过14个服务器模块的本地导入/Python3.6语法检查。真实CPU/厂商宏/PPA仍待验。

## 新准备的材料

- 同输入本地T80/T64比较：平均45384.916667与46076.333333周期，T64本地周期增加1.52345%；编码、布局、参数及34989平均事务全部一致。这不是原总线/CPU性能。见`T80_T64_LOCAL_COMPARISON.md`及同名证据JSON。
- 只读审查工具支持T80/T64自己的身份：未知SAIF清单18tests、连接检查3tests、静态概率2tests、新阶段合同2tests、报告队列2tests通过。报告不自动给验收；新RTL或计时未改。
- `transport_report_stage.py`读取完整队列和自己的ASIC/240/PPA，取precision join内部`reference`指向真正的float20审计，再导出JSON/CSV/中文说明，可串行收集未知SAIF。不能把join summary直接当含identity.json的float20目录。
- 尚未发送的审查ops：`local_runs/transport_reviewops_d611597`，8个源码、64行，manifest `669837cebad4edd91988a0247b4b5c87950560756cb49243221b2ba422e1dac3`。目标`operations/light-light126-transport-reviewops-d611597`，源为已提交d611597；依赖T64新bundle完成后才能重建。传输脚本需要另建，当前不要发送。
- T64接收后只读预检已生成：`local_runs/t64_delta01_65d2507_verified/preflight_cmd.txt`及`resources_cmd.txt`。预检874文件与IRQ/竞争/恢复三套固件，资源命令读锁/空间/同账户EDA。先等60646完结再用。

## 下一步与禁止事项

1. poll60646并查看T64重建回执，然后发送预检；任何失败保留新目录，不原地覆盖。
2. 读取原T80 `t80_finish02`状态及日志、锁与空间；只继续现有队列。当前还不知道综合是否结束。
3. 收齐T80综合/时序/门级14/SAIF12/功耗12/20条精度，导出并审阅；T64正式作业等T80结束及所需审阅。不借旧N1/B0的功耗或PASS。
4. T64正式范围前20条240任务；未授权100条。G64等待T64完整验收，不提前开发门控。
5. 既有失败：T80旧finish01观察CPU端口错误已9196556修复并真实CPU重测通过；首次T64重建误要求sequence ELF容器完全相等，失败目录保留；实际BIN/Verilog/RTL及其余metadata相同，verified目录重建成功。没有删服务器旧8路数据。
