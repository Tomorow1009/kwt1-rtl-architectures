# 原8路同源对照的门级及功耗入口

2026-11-10 02:47：本地工具已实现并验证；**尚未打包上传、尚未执行新MMIO8综合、门级或功耗**。当前服务器仍由DMA16 `dma16_gate03`占用，最后02:44:21.900607已完整通过前八层，正在第九层全波形扫描，不启动并发EDA。

原8路是保底与同条件对照，没有开发8路DMA。生产16路RTL、正式IRQ固件、已有网表及活动包均不改变。

## 本次新增

- `scripts/mmio8_gate.py`：只接受新`mmio8_synth`的138宏网表及明确摘要SHA，核对实际生产RTL、平台准备和库身份；不接受旧synth07或16路网表。只读DC探测原加速器、仲裁器、路由器、共享SRAM的真实模块边界和精确端口位宽/方向，绑定原MMIO8观察器，不依赖可能被综合删除的内部别名。
- 监视器保留首源VALID时刻、其相对时钟沿的相位、成功共享入库先于读取、全部输出坐标和饱和、最后写响应及排空。程序-only ITCM物理宏加载沿用已有验证工具，参数仍来自原SysMem响应源。
- 全活动仍使用原C++逐记录扫描、全文件SHA及完整106位源接口检查。共享的源/仲裁/路由声明审计适用于两版；MMIO8回执改为自己的明确scope，不把它称作DMA16。
- `scripts/mmio8_power.py`：同库、同SDC、同零延迟门级活动及相同PT命令，保留138宏归属、互斥模块清单、verbose时钟和禁用弧、X设置、映射及边界网络报告。功耗窗口采用实际首VALID至末ACK的实数时间，不能把小于一周期的保守周期取整追加到能量窗口。
- `server_run.py`新增`mmio8_gate`、`mmio8_power`独立阶段，继续使用原共享锁、独立session和错误即停。数值报告审核仍待真实PT运行；DMA16数值提取器不能直接作为MMIO8模块/宏数量提取器。

## 已完成的本地验证

相关58项Python/Tcl/原生扫描契约检查通过；4个运行脚本通过Python3.6语法检查。新门级监视器实际XSim RTL夹具在首请求相位1ns和0ns各跑2个完整任务，共101376输出全部一致，并各跑6类清除/复位拒绝测试。夹具使用pin_mock和过程总线发起器，没有E203或综合网表，不能称CPU/门级验收。

| 夹具 | 用例 | 输出 | 原始摘要SHA256 |
|---|---|---:|---|
| `local_runs/mmio8_source_fixture_20261110_024213_217021` | 1ns相位：layer_01、rounding；6反例 | 50688 | `3af832ec42a603071d127626f168f87c761ed304ca2e4d85e42ad3742a77fde1` |
| `local_runs/mmio8_source_fixture_20261110_024422_850433` | 0ns相位：layer_01、extremes；6反例 | 50688 | `1cfdf7710087d7db60d7c477e4a0aeddad449711135c4ac7b0e7e1d68a3b9d46` |

夹具733131周期仅用于观察器一致性，不用于实际E203吞吐。实际MMIO8 ASIC14例周期仍为3843121，见`mmio8_source02`；其新PPA尚未取得。

## 后续独立运行

先完成当前DMA16全14/12活动，首层实际功耗审查和冻结版本优先任务。共享锁空闲且原作业结束后，执行`mmio8_synth`新session；先读取新综合摘要和约束，再安排：

```text
python3 workspaces/arch03/scripts/server_run.py mmio8_gate --session <唯一名称> --synth-run <新mmio8_synth目录> --synth-summary-sha256 <核验SHA> --cases layer_01 --activity-cases layer_01
python3 workspaces/arch03/scripts/server_run.py mmio8_power --session <另一唯一名称> --gate-run <已通过mmio8_gate目录> --gate-summary-sha256 <核验SHA> --cases layer_01
```

先确认真实映射端口和第一份功耗报告，再按同条件对照需要完成14例及12层活动/功耗。不能把只跑一层或只收集到报告称完整PPA，不能因原8路耗时长而缩短应计入的窗口。若实际映射优化掉端口或模块，现有严格探测会失败；先读真实网表，再修观察器，不能通过保留无功能逻辑或任意默认别名掩盖问题。

最终报告还需统一比较新源窗口、声明布局差异及逻辑综合/布局前估算边界。没有模型、活动或数值审核通过的项保留未验证；原8路旧BEGIN功耗不能拼接本次源加载周期。
