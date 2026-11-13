# T80/T64复现与接续入口

遵循[有效计划](N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md)和[验收清单](ACCEPTANCE_T80_T64_G64_20261113.md)。此文件提供入口，不表示尚未运行的阶段通过。

## 冻结身份

| 配置 | 生产实现 | 已部署运行目录 | 当前边界 |
|---|---|---|---|
| T80 | `876b883` | `light-light126-t80-v4-9196556-delta03` | ASIC14/前20条/恢复及竞争通过，原队列综合中 |
| T64 | `e2e83ce`，工具`65d2507` | `light-light126-t64-v4-65d2507-fix02` | 本地验证、875文件及三套固件服务器预检通过；实际ASIC/PPA待验 |

上述目录均在本队独立项目的`bundles/`下。T64旧`delta01`遗漏ABI文档，作为失败接收记录保留，不用于正式运行。完整T64 ZIP本身包含ABI；问题发生在提取运行子集时。

T64有效子集manifest SHA：`6632a4f266d48f50fd8a9e542cb6e03f05653d7ade3153903b38c3282c3339c1`。其875个文件均与`65d2507`完整包对应文件逐字节一致。

## 启动前

1. 读取根交接和最新检查点。检查原队列、进程、共享锁、剩余空间，不启动已有任务，不清锁。
2. 按manifest逐项复核文件。必须执行`verify_firmware`核对IRQ、竞争及恢复固件的全部`source_sha256`引用；仅能导入Python模块不代表依赖完整。
3. 保持原平台、厂商宏、库、SS/0.99V/125°C、6.666666ns与负载；不启用功能TCM分支。
4. 服务器旧8路任何文件均不得删除、覆盖或归档后删原件。空间不足时停止新增写入并保留现场。

## 正式功能入口

在已核验的新T64包根目录，使用未出现过的session名：

```text
python3 -B workspaces/arch03/scripts/t64_server.py soc --session t64_soc01
python3 -B workspaces/arch03/scripts/t64_server.py batch20 --session t64_batch20_01 --dataset /storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all
```

第二条须在第一条通过、原共享锁空闲后执行。`batch20`只选原清单前20条、240任务，逐项核对6082560个输出和total/saturated，不运行全部100条。每个入口自行检查空间并占用原`.arch02_team_lock`。

`t64_finish_queue.py`使用显式request锁定原batch PID、开始时间、目录、包及operations哈希；只接续这一次原批量，不重启批量。按顺序运行竞争、恢复、综合、门级14（含必需端口核对）、SAIF12、timing/drc/structure补充诊断、逐层功耗和同批浮点精度。任一失败即保留现场退出，不在同目录重跑。

上述T64顺序由19:27后的新operations实现，须部署并核验新operations身份后使用；已经接收的65d2507 operations仍为旧顺序。当前运行的T80 operations完全不改动。两种顺序都要求全部诊断完成，不减少最终验收项目。

后续队列包装器还修复了子进程启动后状态落盘失败时的收尾：即使共享盘返回ENOSPC，也必须等待已接受的子进程退出，再传播错误，不把失败记录成PASS。满盘、子进程非零退出与正常退出三个场景已分别对T80/T64执行本地注入检查。此修改只适用于新operations，绝不覆盖运行中的T80队列；没有引入VCS/PT并行或改变协作锁。

T80使用对应`t80_*`入口。当前已经存在`t80_finish02`，不得按本说明重建同名或重复功能队列。

## 收集与审查

- `transport_report_stage.py`读取已成功结束的整条队列，核对自己的ASIC、batch、网表、活动和功耗身份，导出JSON、CSV及中文报告。
- 精度stage的summary是ASIC/FLOAT关联报告；实际浮点逐项审计在其`reference`指向的`float20`目录。不能把两个目录混用。
- `--unknown-inventory`仅扫描本版本已有SAIF及网表，生成未知活动清单；后续连接、别名和静态概率诊断仍需独立审查。诊断不是物理功耗误差上界。
- 报告中的`stage_accepted=false`是正常保守状态，收集完成不自动通过面积、时序或系统功耗。完成审查后再明确记录声明范围。
- 真实SoC周期与本地pin_mock周期分开报告。总时间从首源VALID到最后输出成功写响应并排空，重叠阶段不可相加作为总周期。

T64全部验收后才进入G64；G64只增加实际门控，不同时改编码、FIFO、调度或缓存。没有100条回归的自动授权。
