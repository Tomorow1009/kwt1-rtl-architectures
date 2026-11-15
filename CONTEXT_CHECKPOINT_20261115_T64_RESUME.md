# T64/G64恢复检查点 — 2026-11-15 15:12

## 当前授权与保护

用户恢复T64与G64，桌面T80目录完全不可改。有效计划 `workspaces/arch03/T64_G64_RESUME_PLAN_20261115.md`，技术基准 `N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md`。T64通过后才实施G64；前20条240任务，不自动100条。所有旧8路资料不删。

保护目录 `/storage2/2026contest/server4/s4_21usr/Desktop/T80_Delivery_20261113` 本轮未访问修改。原工作树 `E:/fpga_race-two/kwt1-t80-t64-g64` 的未提交交付回执/文档/截图保持原位。新工作树 `E:/fpga_race-two/kwt1-t64-g64-20261115`，分支 `codex/light-light126/t64-g64-resume-20261115`。

## 已完成

- 重读AGENTS、原技术计划、旧1927/1955检查点、T64实现和复现手册。T64 RTL e2e83ce，本地10000随机+32定向、14例、延迟ABA和恢复已经通过；不重复运行。
- 修复T64工具的旧三段SAIF/PT/report窗口，改用自己的四段校验；修复临时目录清单误要求不存在的t64_transport、队列/precision传递显式runtime身份。提交85baa0e已推送。
- 修复precision join残留的row_lanes==5，正确要求4。提交3f2072c。
- 修复未知活动扫描对T64仍选旧三段计时的问题。提交b9155b4。
- 初轮32项测试、新增四行正向身份测试及7项精度测试、21项未知活动/配置检查通过。本地880成员运行副本哈希、全部RTL/三套固件未改变已核对；只改工具。

## 服务器实时观察及输入状态

板端AC820已上电，Linux VNC恢复到workspace3，窗口18874435。不要触碰workspace4。没有启动FileZilla。可见终端仍在T80旧bundle路径，但所有新命令使用T64绝对路径，不写该cwd。

14:58:04.295978：共享锁不存在，无同账号EDA进程；旧T64 fix02没有runs；共享free0，/tmp93.53GiB。15:01前后只读复查共享free6385827840B，由外部变化恢复，本轮没有删除任何文件。原float archive仍存在。旧T64 delta01的874成员与fix02逐字节相同，共21097815B；只读核对，没有清理。

服务器老T64有效包 PROJECT/bundles/light-light126-t64-v4-65d2507-fix02，875文件，manifest6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1。

正在可见VNC传输第一个工具修复副本（不是正式验证）：本地exec **2790**，脚本local_runs/transfer_resume.ps1，状态local_runs/t64_resume_85baa0e/transfer_state.json（最后读34/51，需实时读取）。不要同时输入VNC或重启传输。板端转发长期exec **91027**保持运行。

第一个副本目标 `/tmp/s4_21usr_t64_20261115_1510/light-light126-t64-resume-85baa0e`，880成员manifest448b9be9efc89afa3564bc17fcd6a0f031e580201510d29f816a3482f4ac60b9；ops-85baa0e manifest9e013ee634ea27909324ae4f737e32d11d43bbd655d9a6354df94f532e57e9e0。先等传输完成，截图确认T64_RESUME_READY。**不要在85baa0e副本启动正式作业**，还缺四行precision修正。

准备好的最终小增量为local_runs/t64_resume_b9155b4（10行），从85副本复制到同root下 `light-light126-t64-resume-b9155b4`，保留85原件。最终880成员manifest **c80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804**，ops-b9155b4 manifest **6f0874cbcd5bd2ac3cc98f06de9aaf9188599f57c85a41fc401a30af77f9de78**。生成脚本local_runs/prepare_final_resume.py。本地3f2072c候选也曾生成，但不需部署，不要误用。

尚无新T64服务器ASIC、综合或PPA运行；G64未开始。没有待收本地测试（39189已结束并PASS）。

## 下一步

1. 等2790自然结束，核对截图；再用同可见传输机制发送最终b9155b4的10行。不可重跑已开始heredoc。
2. 最终副本完成预检后，确认实时锁/空间。使用原t64_server.py `soc --session t64_soc01 --runtime-root /tmp/s4_21usr_t64_20261115_1510 --runtime-manifest-sha256 c80e...`，cwd必须是新b9155b4包；日志写ops-b9155b4。不启动T80作业。
3. ASIC14通过后启动batch20。用其实际state里的PID/started/run构造t64_finish_queue request，挂接现有批量，不重启。队列request指定runtime_root、bundle/manifest、operations/manifest及queue source SHA。
4. 依次竞争/恢复、综合、gate14、SAIF12、补充timing/drc/structure、PT12、precision20；最终报告自身证据。G64仅在T64验收后。

依赖：PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109；协作锁在上级IC/.arch02_team_lock。数据IC/hex_short_all。

FLOAT=/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip，SHA5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2。NumPy=/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905。R4 SAIF资格=PROJECT/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_r4_crosscheck02/native_saif_r4_crosscheck，summarySHAa0a9bc6280e7fe5f35b666535157700aac1d9c0b4490873b6199ba9b5c662d26。启动队列前再核对这些身份。

## 已遇到但已处理的路径

- Python默认GBK读取t64_report失败，已明确UTF8后成功；不是硬件失败。
- PowerShell不展开rg文件星号路径；后续用目录与-g过滤。
- T64未使用过的运行工具存在三段计时、错误清单和五行残留，均已分别修复并测试；不能直接运行旧65d包完成后半PPA。
- 不需要删除旧T64重复输入来腾空间；空间自行恢复。整个恢复过程没有任何服务器删除。
