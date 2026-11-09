# DMA16 门级入口交接

更新时间：2026-11-09 19:39:56+08:00。子代理evidence_audit。有效计划IMPLEMENTATION_PLAN_DMA16_20261109.md；H0=17:16:08+08:00。root负责服务器/共享锁/包；本代理只新增入口和离线测试，不修改已冻结RTL/synth/firmware、不改server_run、不提交Git。

## 最新来源范围修正（优先于下方初版回执）

root指出初版比较两包全部arch03/sw字典会误拒绝后续新增mmio8/sequence测试固件。已改为由原综合source_inputs.json和synthesis_inputs.json实际追溯的生产RTL/生产头文件匹配当前包，并严格核对安装器、工艺/存储元数据与相关准备文件。原运行所有输入仍逐hash核验；两receipt冲突拒绝。新增未参与综合的软件或RTL文件可存在，不代表它们获硬件验收。

- 所选门级固件继续独立verify_firmware验证源/ELF/镜像/program-only和IRQ配置，并冻结在本次gate source_inputs中；不要求它与旧包里所有测试软件目录完全一致。
- 实际生产include `arch02_sram_config.vh`是每run生成，新增verify_gate_memory_config在vendor生成门级配置后，对照原综合receipt唯一真实header SHA；时序/宏模式变化仍会拒绝。
- 复核soc_power.power_databases与dma16_synth兼容：后者source_inputs实际包含run/libs/标准DB及两份LC生成SRAM DB的绝对路径，前者按basename校验恰好3份DB和原SHA。增加实际路径样式的成功、DB变更、同名冲突拒绝测试。无需修改旧soc_power或冻结synth。
- 新gate SHA256 `034dd7bad091e5fafc5928301910b4b9c42847a5bc4096ae7b33083797842cc6`。
- 新test SHA256 `1f693f1a2cef706bfaee0ac670e8699a7f6caaa71c91f67ef08a9cb726a4283d`。
- gate现10项，含独立后续包新增mmio8/sequence/uncompiled fixture允许、实际综合core变化拒绝；与power10/旧power4合计24项通过。命令 `python -m unittest test_dma16_gate test_dma16_power test_soc_power -v`，19:39:56前exec退出0。未运行服务器、未改RTL/synth/firmware或旧power。

下面初版hash/测试数仅保留历史，当前打包以上述新hash为准。

## 已完成与可交付

- 新增 `scripts/dma16_gate.py`，SHA256 `d6423fd10494e8a57f1f0cbdfa84611bcb54d408c15915baa96ddffdf325e07a`。
- 新增 `scripts/test_dma16_gate.py`，SHA256 `2b9812a5b0962af7b2d9c57425e9f4a73945ad2559d6b7b57b72d32e8c903ae2`。
- `python -m unittest test_dma16_gate -v` 新8项通过。连同新power10项/synth14项，共32项通过；最终命令 `python -m unittest test_dma16_gate test_dma16_power test_dma16_synth -v`，exec退出0。Python3.6语法通过。未执行DC/VCS新映射仿真；离线fixture不作为门级证据。
- root已接server_run阶段，调用签名：`verify(cfg, run, synthesis, expected_sha, cases, call, activity_cases=(), firmware=None)`，firmware最后可选；power依赖的`verify_synthesis(synthesis, expected_sha, cfg)`已实现。
- scope固定 `dma16_whole_soc_mapped_functional_without_SDF`；summary包含firmware_sha256/source_inputs_sha256、synthesis SHA、binding receipt SHA。每case含outputs=25344/layout_sha256/task_window/实际capture/result/IRQ证据，以及选中时的activity。timing/system_power/physical_signoff仍false。

## 实际映射探测方式

冻结dma16_synth的mapped_probe_inventory.tsv只列DMA/core接口和5类内部别名，没有shared/arb/router边界。因此root明确批准在新gate目录补独立只读DC probe；没有改冻结综合脚本。

1. 验证`dma16_synth` stage与summary SHA、mapped.v/ddc/sdc、source_inputs/synthesis_inputs、面积和已冻probe等artifact SHA；拒绝旧asic_synth/138宏scope。校验同源RTL/软件/平台安装器/工艺配置和三份实际库DB。
2. 新gate生成mapped_probe.tcl，读同SHA mapped.ddc并link，按实际唯一hierarchical reference查找accel/core/shared/arb/router，输出每个实际cell路径、reference、边界每一bit的名称和方向。无compile、无网表写入、无dont_touch。
3. 解析器独立完整核对五接口所有方向/位宽/bit。core必须是实际accel/core，shared/arb/router为其同级fabric；拒绝缺失、重复、误绑、非简单层次路径。默认RTL路径不用于运行。
4. 与冻结mapped_probe_inventory中的DMA全部pin及core全部边界pin交叉核对；缺失/不符即失败，不从旧别名猜测。
5. 同时probe实际clock test_mode/pllbypass/plloutdivby1及bootrom_deglitch/io_q边界pin，生成top的clock-mode guard连接，不依赖猜测内部寄存器名。
6. 保存probe_command.json、mapped_probe.tcl、mapped_probe.log、mapped_port_probe.tsv、mapped_binding_receipt.json；receipt记录输入DDC、netlist、冻结probe、DB哈希和完整命令/日志/端口清单哈希。探测前后输入一致。

## 实际运行链（尚未执行）

- 使用 `dma16_gate_monitor.generate` 和上述五个真实映射绑定生成被动MMIO完成证明monitor，使用 `arch03_dma16_gate_proof.sv`。未读fifo_count/core_done等内部别名。缺映射接口会在仿真前拒绝。
- 顶层non-ANSI mapped.v输入完整清单与固定平台+新增4组SysMem输入核对；SysMem10组方向/宽度另由综合守卫核验，全部连接到原同步加载源。
- 复用真实厂商模型提取/vendor核验及gate_soc.mapped_loader。只将验证过的program-only固件转换为真实32 ITCM宏物理行；不预装input/shared/core/expected到硬件。
- 每任务从原validated_data独立prepare/verify tile16，`LOAD32`交实际source；期望结果只给被动monitor检查实际writeback，25344坐标/数值/饱和逐项验。复用严格四段191616B首valid→末ACK窗口；最终MMIO排空证明可以更晚，不改变end。
- 实际IRQ/WFI模式必须与固件一致并由CPU mailbox证明；polling CPU周期包住任务；所有模式记录真实CPU周期。
- compile只含mapped.v、四个新observer/source模块、生成TB、真实标准单元/SRAM库，不加入生产RTL旁路。源文件/准备脚本/boot/layout/firmware/映射probe、编译命令/日志、simv均hash冻结，每任务后复验。
- 活动走新dma16_activity全文件native扫描+SHA、头部SysMem/新增fabric核验。case activity范围仍首valid—末ACK；12层都需独立真实VCD才能功耗汇总。

## 测试覆盖与边界

8项包括：自定义实际fixture路径而非默认根生成monitor；缺bit/重复pin/错方向/缺router/冻结probe不一致拒绝；顶层全部SysMem连接及额外未知input拒绝；只读probe无compile/write/donttouch；Tcl模块缺失立刻停止；旧stage/改平台来源拒绝；真实32 ITCM宏路径loader只初始化ITCM；Python3.6语法。

当前只是入口与离线契约通过，没有实际DMA16综合产物可观察，不能声明门级功能/时序/功耗完成。DC collection/ref_name格式、模块接口是否被优化、clock/boot pins是否保留都需实际probe确认；格式或层级不足会停止，不能通过添加猜测别名或大范围donttouch绕过。

当前无本代理运行任务。root将实际ASIC smoke/综合完成后按同SHA运行此新gate入口；首包是否含后续gate代码需以其manifest为准，不能假定已有上传。压缩后先读AGENTS、CONTEXT_HANDOFF、计划、本文件和DMA16_POWER_HANDOFF，再核对root实际回执；旧任务运行状态不视为实时。
