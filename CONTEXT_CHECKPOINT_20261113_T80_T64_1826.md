# T80综合进行中、T64本地验证完成 — 2026-11-13T18:26:06.953737+08:00

**用户最新要求：服务器旧8路所有数据/产物禁止删除、覆盖、归档后删原件。空间管理也不得例外。** 见workspaces/arch03/RETENTION_REQUIREMENTS.md；本接续未执行服务器删除。

有效计划仍为workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md，正式每版前20条240任务。100条未授权，G64等待T64完整验收。

## T80
- 生产硬件876b883仍冻结；原ASIC14、240任务/6082560输出/total/sat通过。固定12平均112569周期(150MHz折算1332.5160568task/s)，本版PPA仍待验。
- 旧t80_finish01在sequence第6阶段因O4混合端口误作CPU专用观察点失败，现场保留。9196556改为仲裁前mem_icb观察CPU，生产RTL/固件不改。
- delta03全部833文件重建核验、ops核验及原竞争报告身份预检通过。新bundle light-light126-t80-v4-9196556-delta03，manifest fcbac79ce3be1446a1c0055a7dad51428a4dcdea7d98bfe0b7fab717d9d3112d。ops light-light126-t80-finishops-9196556，manifest ca77bd7d0388fbd7f79398e254d3511d3c3cbab267ab714d2e8d5fc20c221cf6，请求SHA fca6e03b84c86efc64cec79cc4f73ff84b2006fdb06fda17999ca2923a4e2298。
- **当前唯一服务器队列t80_finish02，驱动PID14008，开始2026-11-13T18:22:51.269828；18:25:26实读running/t80_synth。不要重启。** 目录delta03/runs/t80_finish02。CPU竞争复用经833文件仅观察器差异核验的原报告；新真实CPU10阶段恢复及A/B/A已通过，summary SHA7943123a4ad0b4ed6d4739562947c4962757866c4de5219fe4aca99b6e0c5aa2，目录delta03/runs/t80_finish02_sequence/t80_sequence。
- 队列后续：synth→timing/drc/structure→门级14→SAIF12→功耗12→原240输出与同批浮点精度关联。失败即退出保留。18:22:00启动前锁空、无EDA，空间43009441792B。新阶段开始后锁归其子任务，后续必须重新读取。
- 原先本地传输92632及短命令会话均完成；VNC3正常提示符，无传输占键盘。未碰VNC4，FTP仍没有成功上传，不重试旧上传队列。

## T64
- 独立3份RTL已完成：4×16、25组末3行，保留5行物理X映射60宏+W32宏，同T80 transport，数值不改，无新增ICG。
- 本地10000随机+32定向阵列通过635648输出；14例通过354816输出/total/sat；首层jitter通过；1/2拍SRAM×预取0/1×无复位ABA共12任务304128输出通过，逐次X响应独立按绝对坐标检查，覆盖240次跨五行组窗口/任务、16个末三行块。
- 新恢复fixture10阶段、3负向、76032输出通过。以上仅pin_mock/无CPU/无原mem_fab，不是服务器验收。证据handoff/team/evidence/T64_*.json，说明T64_IMPLEMENTATION_REPORT.md。
- IRQ/WFI、竞争和恢复三套RV32镜像本地编译，元数据10项自检及T64接口3项测试通过。新增独立SoC/前20条/综合/门级/SAIF/PPA工具已准备并通过导入/语法检查，仍需实际服务器验证。新ID4b575309、cap000804bf、layout00100004、SHIFT10。
- 关键本地目录：t64_systolic_array_20261113_180915_841354；t64_datapath_20261113_181252_855428(14)；t64_datapath_20261113_181750_703041(延迟/ABA)；t64_sequence_fixture_20261113_182348_658376；t64_firmware_20261113_1819；t64_sequence_firmware_20261113_1824；t64_contention_firmware_20261113_1825。
- 目前无本地测试仍运行。T64未上传/未运行服务器，G64未开始。新T64包准备后可上传独立目录，但正式作业等T80队列完成及审核。

## 失败与下一步
- 早先4dd hash str/Path预检错误修复于e249，旧目录保留；本次tcsh双引号只读命令失败后改外层单引号；T64准备脚本默认GBK读取中文ABI失败后固定UTF-8，1818不完整固件目录保留，1819重新编译成功；测试误导入旧TestCase触发其GBK扫描后改模块导入，新3项通过。都没有借用失败产物。
- 下一步先看正在运行的T80综合/锁/空间，继续T64工具审查与冻结打包；不启动重复队列、不清理旧8路。T80最终报告工具已在本地，尚未运行最终报告。
- 本次准备把9196556之后T64实现和记录提交并同步个人分支codex/light-light126/n1-t80-t64-g64-20261113；推送结果以Git实际回执为准。
