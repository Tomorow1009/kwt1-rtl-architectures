# T64批量通过与竞争固件修复 — 2026-11-15 16:58

恢复先读AGENTS、T64_G64_RESUME_PLAN_20261115.md、原N1_T80_T64_G64计划及本记录。桌面T80和旧8路完全保护；仅前20条240任务，G64须等T64完整验收。

## 已完成

- 生产RTL e2e83ce不变。ASIC14在b9155b4/runs/t64_soc03/t64_soc通过，354816输出，摘要SHA `8eb6e9822817c2bcdba325b977f7d27e381b8f2b0b2eb6f0331049a7474f7e2e`。
- 真实ASIC/E203批量在9934df8/runs/t64_serial02_batch20/t64_batch20通过，240任务、6082560输出与total及饱和核对，failed0。摘要SHA `50c42478461985dfd33f0324aa464dc3d775388d6e54e3de4f06c8d46f190d16`，16:47:13实读；实际宿主1908.727736334秒，批量均值112567.75周期。
- 固定12性能任务均值112568周期、1332.5278942505863 task/s，不能将批量均值替换它。
- 截图takeover_local/t64_batch_final_identity.png保留。原始服务器报告不修改。

## 新失败及修复范围

原主队列serial02/PID289025在竞争测试失败后自然退出，观察器300088也自行退出。竞争stage16:44:39开始，编译成功，仿真在启动DMA前报bad00002/fffffffe，即BAD_ARGUMENT。源码main_t64_contention.c错误检查metadata[3]!=5u；修为KWT_ICB32_ROWS，并加编译时必须四行检查。其他5u值（如恢复测试期望五次trap）不改。共有头文件默认值不改，正式三个构建入口均显式传ROWS4。

已增加队列prior_batch显式复用：核验原passed状态、摘要SHA和240数量，只允许调度工具与独立竞争固件改变，生产RTL、性能/恢复固件、数据、验证器必须相同。队列6项及契约3项测试通过。

本地试构建local_runs/t64_contention_rowfix01成功；错误行数负编译第一次因Zig默认cache权限AccessDenied未验证，须指定项目cache后重做。正式包必须从Git LF源码构建，不能用CRLF工作树源码哈希冒充冻结包。

## 待做

提交修复、新包仅重建竞争固件，校验三套固件和全部文件；新会话引用旧ASIC14与240，从竞争/恢复继续综合、门级14、SAIF12、时序/结构审核、功耗12、精度20。不重启serial02、不重跑成功任务。综合未开始，功耗与G64未开始。

根目录/tmp/s4_21usr_t64_20261115_1510；旧包light-light126-t64-resume-9934df8，manifest32f48cc22391667881476ba6bf6ad7e26b69c6693e19182fb8688a69ac596c68。b915包manifestc80e6f3355832f6a072cc25353c94f5e8825e49ca274b82510361b8201170804。原共享盘基本满，/tmp约93GiB；下次启动前重查进程/原锁/空间，不清锁。以前对两份未运行T64输入做保留路径和字节的硬链接去重，不能原地修改这些包。无T80/旧8路删除。

VNC18874435，workspace3，FileZilla没开，转发session91027保持。当前shell空闲，无半截heredoc；Ctrl+C的正确helper键名是Control_L c，ctrl+c无效。先观察实际窗口再操作。Git上次push3c0f1aa，当前修复未提交。/tmp不是持久备份，归档工具已准备但未执行。
