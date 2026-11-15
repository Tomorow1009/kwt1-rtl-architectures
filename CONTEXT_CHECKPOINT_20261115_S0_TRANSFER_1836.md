# S0工具完成、旧队列已退出、新包传输中

记录时间2026-11-15 18:36，北京时间。有效计划仍是workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md，原文SHA1d4827306ca07371f522126af6e3744bfbb3912b2e3aeef318176fe026935b39。恢复重读AGENTS、根交接、此检查点、计划和验收表，不能回到旧T64/G64或旧N1阶段。

## 已完成

- 新树E:/fpga_race-two/kwt1-c32-g32-20261115，分支codex/light-light126/t80-pipeline-c32-g32-20261115。
- 566816a、1e90782、c6aa1e255ae16d0479a6532460548c0f26cbdc58均已推送私人GitHub；最新受传输工具为c6aa1e2。之后仅新增本轮验收表、README入口及进度文档，尚未提交。
- S0分块/归属/缓存/characterize、独立映射和顶层链接、完整子块网表token不变检查、独立S0来源验证及门级/活动/PT入口已实现。14项S0本地工具测试、8项T80四段计时/活动兼容检查通过，Python3.6语法通过。不是硬件或EDA PASS。
- 选定24份T80硬件/安装器/固件来源与876b883逐字相同；服务器预检还要核验完整原综合输入和库。S0未改RTL，S1–S4未开始。
- 用户要求的桌面/storage2/2026contest/server4/s4_21usr/Desktop/T80_Delivery_20261113及所有旧八路文件完全未写、未移动、未删除。

## 旧T64已安全退出

原ROOT=/tmp/s4_21usr_t64_20261115_1510，active=ROOT/light-light126-t64-resume-3552163。

17:41仅向调度父325056发送SIGINT+SIGCONT，原ProcessLedger等待当前DC子15147完成后退出，没有对子进程发信号。回执ROOT/ops-3552163/new_plan_stop_after_child_20261115.json。

**18:30:28.444824实查：父/子均消失，原协作锁False。** queue为failed、stage=t64_synth、error空字符串，原因是预排的KeyboardInterrupt，不是综合工具失败。DC日志已经完成写mapped.ddc、输出ARCH03_T64_SYNTH_REPORTS_READY，Elapsed3598秒，memory16193MB。原网表和报告保留，最终数字尚未读取；不要重启队列或运行其gate/SAIF/PT/G64。

## 传输问题及当前GUI

第一轮exec29518的80行主机输入结束，但服务器是tcsh，结束符规则不同，整段未执行。18:30已经从独立新终端确认/tmp/s4_21usr_t80_20261115_1810不存在。旧终端仍停在未闭合输入；多次Ctrl-C未成功取消，**自动审批拒绝闭合残缺脚本**。不再向该旧终端输入，不尝试绕过拒绝执行它。

已在workspace3新开独立MATE终端，并显式进入bash --noprofile --norc，实见bash-4.2$。后续只使用此新终端。VNC18874435；旧终端在同工作区另一个任务按钮中，勿误切。workspace4始终不碰。

FileZilla尝试启动后，既有ftp_proxy因“Expected public FTP server addresses”DNS安全检查失败而退出，没有连接服务器或上传。未更改安全限制，FileZilla窗口20972102已正常关闭。板端VNC转发exec91027继续。F:/linux_fpga_try/AGENTS.md已读；其历史“VNC保持断开”由用户后续明确释放/允许覆盖。

## 当前正在执行，先收完它

**主机exec66349仍运行**：local_runs/s0_direct_c6aa1e2/transfer.ps1；59行，最新状态在同目录transfer_state.json，18:35附近已超过16行。不要并发向VNC输入任何命令。

目标为/tmp/s4_21usr_t80_20261115_1830/light-light126-t80-s0-c6aa1e2；ops目录ops-c6aa1e2。完整payload SHA6c038eefd6301d99fbfcf65a69471e2c9bcba46887ee0241d948f15807b957c2。文件通过新Bash的完整here-doc输入；开始及结束符为S0BASH_c6aa1e2（Bash端无需保留引号）。本地已核验Python3.6语法、全部字节差分重建和payload哈希；解码及所有哈希匹配后才创建新root。

新包从/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4的833个输入复制，原manifest SHA181bb96b719363be5350e9e968ac2b2ad29555e2f4606e362721be3c42629b9b。新工具overlay白名单11个文件；不复制旧runs，不创建指向旧输入的硬链接，不改原件。源码/数据/固件都按manifest逐项复核。输出应出现S0_INPUTS_PREPARED及新manifestSHA；当前尚未看到成功回执。

旧local_runs/s0_update_c6aa1e2是依赖未执行首包的废弃传输方案，**不要运行**；旧s0_transfer_1e90782也不要续传。只接续当前s0_direct_c6aa1e2。

## 原T80综合与下一步

原综合目录：/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-t80-v4-9196556-delta03/runs/t80_finish02_synth/t80_synth。

summary SHA c485b3f77cd7c4f9d7911c5e2052babbc2d8c83811b94ec72c608ffed027f341；mapped.v SHA6a9ab02be889d4aecb55576a71c51ce68f324fc8a0897430e0dbe40a1373eff2。只读原运行目录，不动桌面交付副本。

1. 轮询66349完成，查看takeover_local/s0_direct_prepared_c6aa1e2.png，确认新Bash回到提示符及S0_INPUTS_PREPARED。不要在未结束输入上键入查询。
2. 读取新manifestSHA并核对本地预期；查询实时锁、进程、内存和空间。18:30锁已空，不代表此时仍空。共享盘此前仅1MiB，/tmp约99GB。
3. 独立s0_server.py capability，带--session、--origin、--runtime-root和--runtime-manifest-sha256。入口严格核验原T80来源并持有原共享锁，再运行安装DC的help；先实际核对characterize/write_script/read_ddc支持情况。
4. 检查characterize输出的时钟精度、边界端口/延迟语法。当前工具保留精确6.666666守卫，不允许因序列化舍入放宽。必要修复新工具/新包，失败回执保留。
5. 新独立S0 synth：共享→加速器→CPU/SoC→最终top，子块固定并比较前后网表。最终链接不compile。三块DDC已包含只读输入指纹；原T80未映射linked.ddc仅在完整输入一致后复用。
6. S0新最终网表自己的gate14、SAIF12/PT12、时序/面积/结构及报告。源码/固件/数据保持同一原T80时才能引用既有ASIC14/240/精度。S0完整交接后才进入S1；最终仍32PE，不恢复T64/G64。

新验收表workspaces/arch03/ACCEPTANCE_T80_P80_C32_G32_20261115.md，已补README新入口。下次同步文档时更新STATUS的旧队列终态与新的传输身份；本检查点及根交接当前尚未推送。
