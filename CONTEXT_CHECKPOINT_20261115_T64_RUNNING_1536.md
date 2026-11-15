# T64真实ASIC运行中 — 2026-11-15 15:36

恢复先读AGENTS、根交接、本文件、`workspaces/arch03/T64_G64_RESUME_PLAN_20261115.md`及原T80→T64→G64技术计划。用户恢复T64/G64；**桌面T80目录保持原样、旧八路全部保留**。不启动100条，当前只前20条240任务。T64通过后才实施G64。

## 当前实际作业

15:36:07屏幕实读：`t64_soc03`为running，driver **268189**，started **2026-11-15T15:33:23.604195**；原共享锁owner.session=t64_soc03。layer_01已通过，完整116751周期、宿主4.93269898602739秒；下一层实际simv PID273345。此前固定顺序为extremes、rounding、layer01，完整case_progress待下一次汇总读取。不能把单层周期当十二层均值。

唯一串行包装器PID **268175**（启动截图），脚本 `/tmp/s4_21usr_t64_20261115_1510/ops-b9155b4/t64_start_pipeline.py`，SHA **016dfbb037e43d50d981fb653d43847768792c4a4000b78132a72e6a5f5eb7d4**。源码副本已入库 `handoff/team/evidence/T64_START_PIPELINE_20261115.py`。

包装器已执行独立预检，核验FLOAT archive与R4 SAIF方法资格；依次自动执行 **t64_soc03 → t64_batch20_01 → t64_finish01**。不手工并开或重启任何一个阶段。ASIC14未结束，240任务及PPA尚未开始，G64未开始。

ROOT=/tmp/s4_21usr_t64_20261115_1510

BUNDLE=ROOT/light-light126-t64-resume-b9155b4

OPS=ROOT/ops-b9155b4

- BUNDLE 880文件manifest **c80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804**，服务器逐文件与三套固件预检通过；硬件仍e2e83ce，RTL/固件字节未改。
- OPS三文件manifest **6f0874cbcd5bd2ac3cc98f06de9aaf9188599f57c85a41fc401a30af77f9de78**。
- 当前控制状态 BUNDLE/runs/t64_start01/state.json；子作业日志同目录/t64_soc03.log。外层日志OPS/t64_start_pipeline.log，外层日志在子任务运行时可以为空。
- 后继证据队列状态 BUNDLE/runs/t64_finish01/state.json（当前尚未生成）；wrapper在batch通过后按真实PID/started生成finish_request并立即接续。
- 所有正式输出在独立/tmp；最终需持久归档，尚未执行。不改桌面T80目录。

## 本轮完成与失败记录

- 85baa0e修复T64四段活动/功耗窗口、runtime清单、queue与precision传递显式runtime；3f2072c修正precision里错误的五行身份；b9155b4修正未知活动扫描T64窗口。共54项相关工具检查通过。没有新RTL改动，不重跑此前本地10000随机及14例。
- 第一次`t64_soc01`（15:17:25 PID261262）和第二次`t64_soc02`均在共享锁mkdir处ENOSPC，未进入编译/仿真，没有stage目录；两份launch.log保留。不能称ASIC失败，也不能删除这些失败日志。
- 共享盘反复0～几MiB。15:21对两份**已核验相同的旧T64输入副本**做硬链接存储去重：42个validated_data文件，释放重复块6,995,968B；路径、内容、清单全部保留。后又被外部写入占满。
- 包装器随后对同两份旧T64中的6个固件文件去重，释放3,145,728B，并立即启动，成功取得原协作锁。所有原路径/内容仍保留；没有删除T80、旧八路或任何波形。第一份回执OPS/duplicate_storage_receipt.json，第二份BUNDLE/runs/t64_start01/firmware_dedup_complete.json。
- 只读扫描旧R4/B/N1原始VCD结果0；R4波形已在历史授权流程归档，不能重复归档。共享原旧T64delta01/fix02现在部分输入共享inode，二者均为冻结包，禁止原地编辑。

## 接续

1. 只读当前队列及case_progress，不重启。已有源码工具与数组测试PASS不是新服务器PASS；持续读取本次完整ASIC14结果。
2. 包装器自动做batch20与后继队列。后继为竞争、恢复、综合、门级14、SAIF12、timing/drc/structure、PT12、20条完整浮点关联；任一错误保留并停止自动派发，修复后新session接续。
3. 综合完成可先报告同网表面积/时序初值；全项齐全后导出独立报告并审阅。G64在T64符合计划后才开发。
4. 本地分支`codex/light-light126/t64-g64-resume-20261115`，工作树`E:/fpga_race-two/kwt1-t64-g64-20261115`。a04e73d已推送，16be782及本次更新待同步；冻结工具b9155b4不变。

## UI与本地会话

板端转发exec **91027**长期保持，不终止。VNC **18874435**，workspace3，终端空闲。没有FileZilla运行，没有待输入heredoc或未完成传输；15345和42353已结束。旧传输2790/64983/35249以及所有launch输入会话均结束。

查询文件 `E:/fpga_race-two/takeover_local/t64_pipeline_watch.txt` 可明确键入再Return。不要用Up重复任何启动/去重命令。最近截图t64_soc03_actual_state.png。板端helper F:/linux_fpga_try/ac820.ps1，操作前核对windows；只用可见VNC，不能隐藏直连服务器。

原T80交付路径 `/storage2/2026contest/server4/s4_21usr/Desktop/T80_Delivery_20261113` 未修改。原工作树T80未提交文档及截图均保持原位。T64新归档/同步不能写到该目录。
