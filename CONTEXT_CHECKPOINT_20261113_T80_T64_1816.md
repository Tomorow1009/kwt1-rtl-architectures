# T80恢复观察器修复与T64本地进度 — 2026-11-13T18:15:41.129048+08:00

有效计划：workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md。正式回归仅前20条240任务，100条仍未授权；G64需T64完整验收后开始。

- T80生产硬件876b883未改；ASIC14及前20条240任务通过，6082560个输出/total/sat零失败，固定12平均112569周期。尚无本版PPA验收。
- 服务器原t80_finish01驱动306658于18:08:20.803679失败退出：CPU竞争已通过，summary SHA32304ab2fd2c241377d576d1b35c7f672a67b18b5b44b8952124209d385e21f4；sequence第6阶段把原mem_fab O4的DMA读取误当CPU非法读取。18:10:40实读日志：arch03_t80_sequence_monitor.svh:322，时间84776658189fs。不是数值输出不符；恢复仍须真实CPU重测。
- 修复提交9196556d64b560d0836c6885acc78890a1e00ad2：CPU观察改到仲裁前mem_icb，保留O4四类DMA路径证明。修复后本地10阶段/3负向/76032输出fixture通过；仍不代表真实CPU重测通过。队列仅允许在除该被动观察器外全部833文件身份相同的条件下复用原CPU竞争结果；6个范围/身份/锁测试通过。
- 正在通过VNC3传输delta03及新ops，本地exec会话92632，进度local_runs/t80_fix03_9196556/transfer_state.json；**传输完成前勿发额外VNC键盘**。新bundle light-light126-t80-v4-9196556-delta03，manifest fcbac79ce3be1446a1c0055a7dad51428a4dcdea7d98bfe0b7fab717d9d3112d；ops light-light126-t80-finishops-9196556，manifest ca77bd7d0388fbd7f79398e254d3511d3c3cbab267ab714d2e8d5fc20c221cf6；request fca6e03b84c86efc64cec79cc4f73ff84b2006fdb06fda17999ca2923a4e2298。此时新服务器队列尚未启动。
- T64已新建独立accel/linear16x4/systolic4x16及本地测试入口，不修改T80/N1生产文件。保留60X+32W宏、原五行物理映射；四行窗口跨组读映射带响应标签，25组末三行，2×64结果槽，32字输出FIFO。
- T64阵列10000随机+32定向通过，635648有效输出，恰好64次MAC，连续II64，201275暂停拍，11取消及11复位。运行local_runs/t64_systolic_array_20261113_180915_841354，证据handoff/team/evidence/T64_ARRAY10000_20261113.json。独立整数模型；无CPU/宏/PPA。
- T64首层带jitter本地完整DMA/共享SRAM fixture通过25344输出/total/sat，89754周期，FIFO峰值32；local_runs/t64_datapath_20261113_181028_413671。正在本地14例无jitter，exec48491，目录local_runs/t64_datapath_20261113_181252_855428。随后补2拍SRAM、跨组独立检查、无复位ABA及错误/取消测试。
- 已失败/保留：旧4dd预检str/Path错误已e249修复；本次tcsh双引号嵌套只读命令报Unmatched，已改文件传递单引号命令；原sequence观察点错误如上。均不删原目录，不复跑旧队列。
- Git本地HEAD9196556，远端最后3606046；后续提交T64及本检查点并推送。新包只有观察器变更，T64尚不进服务器。

下一步：收取92632传输结果→新833文件/ops/原竞争证据预检→检查锁、进程与空间→新t80_finish02串行恢复测试及综合/严格STA/门级14/SAIF12/功耗12/同批精度。不得重复原batch20、原contention、旧失败队列；不得占用VNC4。
