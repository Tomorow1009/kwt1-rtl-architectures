# T80继续映射、T64最终队列工具已就绪 — 2026-11-13 19:55

## 当前要求

重读`workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md`与`T80_RESULT_PRIORITY_20261113.md`。用户要求持续推进，当前没有暂停。每版前20条240任务，未授权100条；T64完整验收后才进入G64。**服务器旧八路全部文件不删、不覆盖、不归档后删原件。** 本轮没有服务器删除。

## 原T80队列

- 生产RTL876b883，当前工具/观察器运行包`PROJECT/bundles/light-light126-t80-v4-9196556-delta03`，833文件，manifest fcbac79ce3be1446a1c0055a7dad51428a4dcdea7d98bfe0b7fab717d9d3112d。
- 唯一正式队列`t80_finish02`，PID14008，child23158，实际DC29185。原ops仍`light-light126-t80-finishops-9196556`，没有更换或编辑。19:44:26实读DC R态、99.5%CPU、CPU时间1:13:20。19:54:56截图读到最新日志为映射时序优化迭代；最后完整可见队列state仍为19:42:28的running/t80_synth，尚未观察到最终summary。
- 原计划队列仍自动依次执行synth→timing/drc/structure→gate14→SAIF12→power12→precision。不要重启或插入新EDA，也不要改运行目录。综合完成立即读初步结果，不等最终功耗。
- 已通过：ASIC14、真实CPU竞争/恢复、前20条240任务/6082560输出及total/sat。固定12平均112569周期、150MHz折算1332.5160568task/s；PPA与同批新浮点精度关联待完成。
- 已从原summary逐项SHA核验后读出实际计数：源读/共享写/共享读/输出写延迟3/3/4/3拍，MAC利用率18.0114%，成功事务0.310823/拍。详`T80_MEASURED_TRANSPORT_20261113.md`及`T80_ASIC12_COUNTERS_20261113.json`。等待可重叠，不相加作总时间。

## T64及审查工具

- T64生产RTL e2e83ce，实际运行包仍`light-light126-t64-v4-65d2507-fix02`，875文件，manifest6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1。三类固件及全部包文件服务器预检通过；尚无T64正式ASIC/EDA。
- **后续T64应使用最新ops：`PROJECT/operations/light-light126-t64-finishops-4bbd0af`，3文件，manifest c8d77f164f4f1c798f85741ae1dd6ffe3be5c8691193e5a6071cb131f0e45028。19:52:24实读服务器预检PASS。** 新ops保留gate/SAIF优先于补充诊断；额外修复Popen成功但状态写入ENOSPC时仍等待子进程退出的收尾。3场景×两队列本地注入通过。源提交4bbd0afa078c48c07e7c774fae9bdfbdaae75c7b。旧65d2507、fbfdc2e ops均保留但不作为接下来首选。
- 本地`t80_finish_queue.py`也修复相同收尾问题，仅供未来导出；**并未部署替换原T80正在执行的9196556工具**。
- 审查ops `light-light126-transport-reviewops-d611597`，8文件，manifest669837cebad4edd91988a0247b4b5c87950560756cb49243221b2ba422e1dac3，已服务器预检通过。完整报告仍需21阶段全部完成，precision取join内部float20引用。
- 最新VNC传输exec61820已经结束，26行全部发送并核验。没有本地后台验证或待输入任务，1953查询已完成。不要继续poll旧session。

## 空间和恢复

- 19:39:35共享free19545456640B，/tmp free246422388736B，当前synth目录261464KiB。19:42:28共享free19186843648B。空间下降需要观察，但不能动旧八路。可在后续新阶段必要时采用已有显式私有/tmp支持；不能搬动当前运行综合。临时盘不是最终交付存储。
- VNC18874436、FileZilla20972102，本轮已核。恢复先调用windows确认。只用workspace3；终端cwd还是`PROJECT/bundles/light-light126-t80-v4-20261113_165244-876b883d9519-delta01`。FileZilla断开，最后421；不连续重试，不碰workspace4。
- 现成只读命令在`E:/fpga_race-two/takeover_local/`：`t80_finish02_compact_cmd.txt`、`t80_synth_status_cmd.txt`、`t80_process_cmd.txt`、`t80_space_scope_cmd.txt`。`t80_preliminary_cmd.txt`仅在synth passed后执行，校验summary及mapped.v/metrics/area/latch/loop报告SHA，打印最终网表对应初值。
- 通过`F:/linux_fpga_try/ac820.ps1`操作已授权板端VNC。截图有时早于终端输出，等后再截图，不能因此重复启动命令。当前无交互阻塞或待Return。

## Git和下一步

工作树`E:/fpga_race-two/kwt1-t80-t64-g64`，分支`codex/light-light126/n1-t80-t64-g64-20261113`。d7969bd已推送，4bbd0af和本检查点正在同步；原其他工作树不动。下步先读原T80状态，在综合完毕后立即报告初步面积/时序/宏及结构，再持续原队列、读取失败或完整结果。T64正式运行等原T80必要证据收齐；G64继续未开始。

PROJECT=/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109。原共享锁在上级IC/.arch02_team_lock，不自动清锁。历史失败与所有旧8路数据保留。


19:56增量：19:55:45.042179实读原队列仍running/t80_synth，driver14008、child23158、completed=2、error=None，共享free17054040064B。该状态比前述日志截图更新，未出现最终摘要。
