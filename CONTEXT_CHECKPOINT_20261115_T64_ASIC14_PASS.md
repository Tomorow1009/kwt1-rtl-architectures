# T64十四例通过，准备单锁队列 — 2026-11-15 15:52

有效计划仍T64_G64_RESUME_PLAN_20261115.md及原技术计划。用户恢复T64/G64；桌面T80交付目录绝不修改，旧八路全部保留。每版只前20条240任务，G64必须等T64完整验收。

## 已完成

T64硬件e2e83ce不变，b9155b4工具包880文件预检通过。服务器`/tmp/s4_21usr_t64_20261115_1510/light-light126-t64-resume-b9155b4/runs/t64_soc03/t64_soc`真实ASIC14通过，354816个输出及total/result/saturated全部正确。

summary SHA `8eb6e9822817c2bcdba325b977f7d27e381b8f2b0b2eb6f0331049a474f472e2`。固定12周期：116751、113731、112105、112511、110445、108925、107165、107645、107205、111125、116971、126237。均值112568，150MHz折算1332.5278942505863task/s。截图takeover_local/t64_soc14_summary.png，15:43:17.943597实读。不要重跑。

## 失败路径及当前工作

原包装器268175先完成soc03，随后batch20_01在共享锁mkdir处ENOSPC，包装器自然失败退出。批量尚未编译/执行；日志保留在原bundle/runs/t64_start01/t64_batch20_01.log。soc01、soc02也曾在锁mkdir失败。先前去重只涉及两份相同旧T64包：42个数据文件+6个固件文件，所有路径/字节保留并保留回执；两包部分共享inode，不得原地编辑。没有动T80或旧8路，没有删波形。

当前修改运行工具：n1_process显式注册同bundle兄弟stage目录，用同一个原协作锁与中央child ledger；新增t64_singlelock_queue.py调用原验证函数串行跑剩余阶段；report允许显式固定旧bundle证据身份，复用ASIC14。43项相关本地测试通过，包括真实子进程、模拟ENOSPC、失败排空、独立stage回执和路径拒绝。新工具尚未提交部署/启动；当前不能写240通过、综合通过或功耗通过。

## 下一步

1. 提交冻结新工具，生成新独立bundle，不能改b915受测包。
2. 复查原锁、进程、shared与/tmp空间；队列只取得一次原锁，不清别人锁、不并行EDA。
3. 运行前显式绑定b915 manifest c80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804及ASIC14摘要SHA。
4. 剩余为240任务、竞争/恢复、综合、门级14、SAIF12、timing/drc/structure、PT12、20条FLOAT关联及完整报告/持久归档。G64未开始。

分支codex/light-light126/t64-g64-resume-20261115；工作树E:/fpga_race-two/kwt1-t64-g64-20261115。b437492已push，新工具待提交。板端转发91027保持；VNC18874435/workspace3，FileZilla未开，没有待输入heredoc。后续要明确键入查询，禁止Up重放launch/dedup。原15:36检查点及状态已过时。
