# 旧 8 路源加载 ASIC 入口交接

更新于 2026-11-09 19:23。子代理 `/root/contest_requirements` 的本轮接续记录；上下文恢复时先读主计划 `IMPLEMENTATION_PLAN_DMA16_20261109.md`，再读本文件和 `MMIO8_SOURCE_HANDOFF.md`。不替代主代理总进度。

## 已完成

仅新增 `scripts/mmio8_soc.py`、`scripts/test_mmio8_soc.py` 和本记录。没有修改主代理新增的 `install_mmio8_source.py`、`tb/arch03_mmio8_source_monitor.svh` 或 `server_run.py`；没有修改已冻结 DMA16 文件、旧驱动或向量。

入口是：

```python
verify(cfg, run, platform_source, cases, call, activity_cases=(), firmware=None)
```

默认固件 `ROOT/firmware_mmio8`；原向量 `ROOT/validated_data`；允许固定 12 层及 extremes/rounding，无重复。server_run 持共同协作锁，入口不再次取锁。主代理负责新增 stage 和打包集成，本子代理没有服务器操作或 git 提交。

- `verify_firmware` 独立接受 `single_cpu_mmio8_source_v1`，不调用 DMA16 的模式校验。强制精确 7 项源码集合、源码 SHA、ELF/segment、源/共享/输出地址、原 ID/布局标签、IRQ 禁用、每个 shift 的 program-only 镜像逐字节一致。所有任务所需 shift 在编译前检查。
- 编译只使用旧 `arch02_linear`、旧 `arch03_icb_accel`、原 dot64/数值逻辑、arb/router/shared/tcm、标准单元与官方 SRAM 模型。不编入 `arch03_dma16_accel` 或 `arch03_linear16`。
- 使用主代理 `install_mmio8_source`，复用公用实际 SysMem 1 拍响应加载模型、ASIC 模式守卫和真实物理 ITCM 转换。每个 shift 独立 boot 目录。
- 冻结编译源、全部修改后平台文件、标准单元/SRAM 模型、固件 C/h/start/link/builder/helper、监视器/头文件、布局/验证/活动脚本、ELF/镜像、boot 文件与编译回执。原任务 layout 和全部文件哈希也加入 `frozen_inputs.json`；每例前后检查，捕获修改即拒绝继续。
- 每例用 `mmio8_source_layout` 将原 tile8 流封装至新 run 目录；`+LOAD32` 仅供实际 ICB 源，`+DATA_DIR` 只给 observer，`+BOOT_DIR` 按 shift，`+CAPTURE` 为实际响应捕获。
- 捕获逐坐标检查 25344 个输出和全部饱和位；解析唯一 MMIO8_SOURCE_WINDOW 与 CPU PASS，并核验 ASIC/boot/source 模式标记。完整周期严格为 end-start，无 +1，时间差与 6.666666ns 周期一致，CPU 诊断跨度须包住总线跨度。
- 输出逐例 `*_result.json`、`case_progress.json`，异常写独立 `*_failure.json` 并立即停止；汇总给总周期、平均周期、task/s、MMAC/s。活动可选，沿用完整 VCD 审计。功能模拟通过也不标记 STA、门级、系统功耗或官方精度通过。

## 字节与事务统计

从 monitor 的实际成功 ACK 字段要求源读 11744、初写 11744、共享输入读 23488、输出半字写 25344。本轮旧驱动仍每半字 LHU/SH，不能套 DMA 的共享读/输出写事务数。

报告分别保存：

- `successful_data_region_icb_transactions`：四段观察到的事务数。
- `data_region_transaction_count`：以上四段之和；完整正常任务为 72320。
- `data_region_bus_slot_bytes`：每个 32 位接口事务按 4 B 槽容量计算；正常任务为 289280 B。这是槽容量，不能叫有效输出数据量。
- `useful_bytes_by_phase`：按实际访问有效宽度 4/4/2/2 B 从各段 ACK 推导，再求有效字节合计；不沿用 DMA 的硬编码总量。
- `total_system_transactions=None`：明确四段统计不含 MMIO 状态轮询/寄存器、邮箱和指令交通。不得把上述四段之和标成整个 SoC 全部事务。

monitor 只有在 CPU 数据口、arbiter/router 排空后发布 WINDOW，CPU 完成邮箱出现后才 PASS。结束时间仍是最后输出写响应的时间，不延长到后续邮箱。

## 本地测试与哈希

实际执行 12 项单测全部通过：首源到最终响应边界、时钟和非有限时间拒绝、模式缺失/重复、输出/饱和/CPU跨度、把 DMA 事务数套到旧半字路径的负例、重复/缺失/负数字段、Fatal/FAIL、固件模式和缺失源身份、编译文件列表无 DMA16/linear16、Python3.6 语法。

另实际调用独立 `verify_firmware` 核对既有 `local_runs/mmio8_source_firmware_20261109_v1`，7 项当前源码及 shift11/12 镜像通过。没有构造伪 ASIC 编译/运行结果。

证据目录 `local_runs/mmio8_soc_contract_checks_20261109_v1`：

| 对象 | SHA256 |
|---|---|
| mmio8_soc.py | `4ea1218658508c43c418f9208caa44e26a266c3ef0bf559b8e420d1935b48055` |
| test_mmio8_soc.py | `58e754ada8239f7f3bf7b89e10f3b90710a7716dae87cd159644e17f88856f30` |
| receipt.json | `f55b12e66c4c78bcdb6b30e58f89aa4f66db1a840aa49ea57d276eee19d22052` |
| 被核验固件 manifest.json | `0e5ddd6be7a632cab585f1cce119395520e6be23e186172ca62802c956dcc49e` |

本地回执明确 `asic_compiled=false`、`cpu_executed=false`、`rtl_simulated=false`、`timing_verified=false`、`system_power_verified=false`。测试中的合成日志只用于解析器负例，不是性能数据。

## 尚未完成与下一步

主代理接入 server_run stage、冻结新包并在现有服务器路径运行。须实际验证：ASIC VCS 编译、固定平台新 8 路安装、原 E203 的 LHU/SH 实际总线地址/字节使能与监视器契约、物理启动、首源等待计时、最终写响应排空、14 例完整输出，以及可选活动覆盖。只在这些通过之后才能用结果与同源 DMA16 版本比较。

没有执行 1200 任务参考批；该入口按本次授权只做同条件 14 例。没有把旧 3890080 周期或本地解析夹具作为新性能结果。若真实总线地址/响应语义与当前监视器假设不同，应保留失败产物并按实际平台修订，不能仅改期望计数来掩盖访问遗漏。
