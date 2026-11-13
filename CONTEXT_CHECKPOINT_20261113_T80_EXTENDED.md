# T80扩展工具传输与前20条回归检查点 — 2026-11-13T17:41:57.331361+08:00

有效计划：workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md。当前独立分支codex/light-light126/n1-t80-t64-g64-20261113；原工作区和所有历史证据保留。

## 已完成
- T80生产RTL876b883：真实共享写ACK后经原mem_fab读回，解码仅消费读响应；80PE、原数值/缓存/并发限制保持。ASIC/E20314例354816个total/result/saturated全部通过；原总线四类事务逐笔检查通过。
- 固定12任务平均112569周期，150MHz折算1332.5160568task/s。不是芯片实测；不继承历史N1/B0的面积、时序或功耗PASS。
- 本地10000随机+32定向阵列、7协议用例、双拍SRAM/ABA和恢复fixture已通过，详见前检查点。本地不等同真实SoC。
- 扩展包aa1d15b已完整打包校验，923文件、9386985B。实际生产RTL与876b883相同；新增门级、SAIF/PPA、真实CPU竞争/恢复工具及诊断固件。
- delta02在本地从不可变delta01重建833文件全部SHA匹配；manifest8f0f675ab510ba43de8e5275e9dba5d0f88e861a7c0562ae52220ce1ca7c6e0a。为缩小可见传输，诊断镜像从包内ELF与元数据按原构建函数重建，结果与完整ZIP逐字节同SHA。
- 新独立精度工具：T80前20条浮点复算+真实240任务逐坐标total/result/sat关联；4项范围/失败排空测试通过。尚未服务器执行。

## 当前实际作业
- 服务器delta01/t80_soc01已PASS，勿重跑。
- delta01/t80_batch20_01：驱动PID247023，开始17:27:35.377905。最后17:36:42实读至少50/240PASS，无失败。不能把此观察当作实时终态。
- delta01路径：/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/light-light126-t80-v4-20261113_165244-876b883d9519-delta01。
- VNC工作区3正在接受delta02的tcsh Python here-document。传输脚本本地exec会话78586；精确进度local_runs/t80_delta02/transfer_state.json及line_*.txt。**不要在传输结束前额外向VNC键盘输入**。服务器delta02尚未完成核验。
- 关闭here-document必须发送带引号的'T80_DELTA_AA1D15B'。上一delta01首次未引号结束触发末尾NameError，但重建与后续807文件独立核验已通过；保留此失败路径。
- FileZilla17:31仍421，未上传扩展ZIP；未碰工作区4。共享盘最后空闲43665850368B(17:20:22)，后续启动前重新看。

## 下一步及未验
- 收取现有delta02传输结果、逐文件校验；读取原batch20终态，不重复启动。
- batch完成释放锁后：真实CPU竞争/恢复、新综合、严格时序/面积/结构、同网表门级14、SAIF12及系统功耗。精度新ops小包尚待部署。
- T64/G64尚未开发；按阶段冻结与测量后推进。禁止恢复N2/D1/D2、A广播或宽总线/省略共享写入路线。
- 本轮正式只20条240任务6082560输出；完整100条必须另获用户明确授权。
