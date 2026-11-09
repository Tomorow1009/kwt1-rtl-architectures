# DMA16 真实 CPU 无复位序列验证交接

更新：2026-11-09；子代理 `/root/contest_requirements`。上下文压缩后先读主计划 `IMPLEMENTATION_PLAN_DMA16_20261109.md`，再读本记录。这里只记录本工作线；不是已完成真实 CPU 验证的证明。

## 已完成、未完成与范围

新增文件：`sw/main_dma16_sequence.c`、`sw/start_dma16_sequence.S`、`scripts/build_dma16_sequence.py`、`scripts/test_dma16_sequence.py`。未修改已冻结的 DMA16 驱动、单任务 startup/builder、ABI、单任务 source/monitor 或服务器入口；没有服务器操作或 git 提交。

固件实际以 Zig RV32IMAC/ILP32 编译通过，8 项元数据/故障指令边界/运行源身份契约测试通过。当前产物为 `local_runs/dma16_sequence_firmware_20261109_v3`；只编译，不宣称 E203 执行、真实异常恢复、IRQ、取消、超时、无复位 A/B/A、时序或功耗已经通过。

本版明确 polling-only。单任务 IRQ/WFI 另证，不把本序列当 IRQ 验证。原 `kwt_dma16.c` 直接链接，无改动。

`/root/dma_feasibility` 已接收下面的完整契约，正独立新增 sequence source/monitor 与真实 DMA/core/fabric 本地夹具；主代理后续接真实 ASIC E203。该夹具即使通过也不能替代真实 CPU 异常/程序执行。

## 固件行为与阶段

所有阶段共享一次 SoC 复位后的执行，不复位 CPU/SoC。每阶段先真实 CANCEL/CLEAR，等待 core.start_ready、master pending/FIFO 清零，再选择源并 arm。DMA START 内部 PREPARE 的 core.cancel 与后续 ready 仍由硬件 observer 检查，不凭软件声明冷缓存。

| phase | 行为 | 必须有的实际证据 |
|---|---|---|
| 1 | SOURCE_BASE=B0000002，非法 START | 配置拒绝，真实 store access fault，零 DMA 请求 |
| 2 | INPUT_BASE=A007F000，输入范围越界 | 同上 |
| 3 | OUTPUT_BASE=INPUT_BASE，输入输出重叠 | 同上 |
| 4 | INPUT_BYTES=46972 | 同上 |
| 5 | OUTPUT_BYTES=50684 | 同上 |
| 6 | 有效 START；读到 source ACK≥32 后 CANCEL | 仍在初始装载、部分源/初写 ACK，LOAD/输出为零，排空后 ready，不能假装 done |
| 7 | 原 kwt_dma16_run 使用短 timeout=8192 | 真实源 ACK>0 且<11744，返回 TIMEOUT=-1，primary_result=-1，取消已排空，输出为零 |
| 8 | A 完整任务 | 25344 真实输出及饱和位、四段 ACK、最终响应排空 |
| 9 | B 完整任务 | 换数据和 shift，独立完整计时/输出验证 |
| 10 | A 完整任务 | 无复位返回 A，独立完整计时/输出验证，检测旧缓存污染 |

阶段 1–5 的无效配置寄存器写本身合法；只有 START 被拒绝。RTL 首错必须 code=3、phase=2、addr=40000004。固件用专用 `sequence_guarded_start` 中的 **32 位 SW** 触发真实异常，只有 expected_fault 已置位、mcause=7、mepc 精确等于该 SW 标签、mtval=40000004 时才恢复到固定下一条指令；其余异常走原 fatal trap，不吞掉任意错误，也不软件伪造 trap 次数。

每次拒绝后实际 CANCEL 等待 ready/drain，保留 FIRST_ERROR/ACK 供回执审计。阶段 7 如果实际平台的配置开销导致 timeout 在首源访问前发生，将如实失败，而不是声称已经测试装载中超时。8192 是待 CPU 验证的首版参数，可通过新构建调整；任何变更均换新目录、冻结新 manifest。

## 元数据、数据身份与源切换

ITCM 只装程序和 0xfff0 起四个 uint32：

1. magic `0x53313631`；
2. A descriptor=`(source_id<<16)|shift`，默认 `0x0000000c`，A 为 layer_01/source_id0/shift12；
3. B descriptor 默认 `0x0001000b`，B 为 rounding/source_id1/shift11；
4. 短 timeout，默认8192（0x2000）。

0x10000 之后全部为零。builder 读取原 14 例只获取 shift、原 layout/hash，并在 PC 上重排计算 source payload 身份；没有把任何输入、权重、bias、expected 放入 ELF 或 ITCM。

外部源保持 B0000000，同原 ICB SysMem 接口。sequence source 的约定 plusargs：`FIRST_LOAD32`、`SECOND_LOAD32`；observer 使用 `DATA_DIR`、`SECOND_DIR`、`CAPTURE_PREFIX`。这些文件可在 PC/TB 预读，但只有实际 source 请求才允许响应硬件输入，不能提前写入共享 SRAM。

CPU 邮箱基址 A001F000，`mail[33]` 的成功写响应锁存 descriptor/源 bank；要求当时无 DMA held/accepted 事务、source 无未响应，core.start_ready 且不忙。该 selector 写本身是 CPU 的共享事务，不误判为残留 DMA。之后 `mail[32]=phase` 的成功响应 arm 阶段。真正首个 source VALID 才是本任务计时起点；选择源不是计时起点，也不构成输入传输。

两份 payload 必须不同。当前已有 tile16 文件是 CRLF；builder 因此明确分别记录 `load32_canonical_lf_sha256` 与 `load_payload_sha256`，不把规范 LF hash 误标为实际文件字节 hash。`build_dma16_sequence.verify_runtime_sources(manifest, first_path, second_path)` 校验 11744 个实际 32 位 token 的规范化 hash/二进制 payload，再返回实际路径及 `file_sha256`，供运行器冻结原文件。

已对 `local_runs/dma16_layout_14case_20261109_h0/layer_01/load32.hex` 与 `rounding/load32.hex` 实际调用通过。A payload SHA=`322ed19382c77c2ebab1223f55059739dc54b10b69db48ec95aec1c4e3fb7013`；B payload SHA=`b2a0842719415a285ed51a8a88e7ebaefa3c7419fe9d219046d296a24c56fb98`。

## 阶段回执与最终邮箱

每段记录位于 `A0020000+(phase-1)*0x100`，输入/输出/邮箱之外、仍在512KiB共享 SRAM 内。写完并 fence 后 `mail[34]=phase` 提交。记录的各 snapshot 值由真实 MMIO 读取得，monitor 应与实际 MMIO 响应和总线计数交叉核对：

| record word | 内容 |
|---|---|
| 0、1、2 | phase；kind（1配置拒绝、2取消、3超时、4成功）；返回码 |
| 3、4、5 | STATUS、COMPLETION、PENDING |
| 6、7、8 | FIRST_ERROR、error_addr、error_phase |
| 9–12 | source/stage/shared-load/output ACK |
| 13、14 | load/output committed bytes |
| 15、16、17 | input/output halves、sat |
| 18、19 | 诊断 CPU cycles 低/高字 |
| 20 | cancel_drained |
| 21–24 | 累计真实 guarded trap 数、最近 cause/epc/mtval |
| 25 | 当前 descriptor |
| 26、27 | 故意改写的配置 offset/value，非配置阶段为0 |
| 28 | 短 timeout 参数 |
| 29–31 | phase6 CANCEL 请求前最近读到的 source ACK、stage ACK、STATUS；其他阶段0 |
| 32 | stats.primary_result，timeout应为-1 |

配置拒绝的 record rc=0 表示实际 trap+硬件拒绝+排空证据均满足，不是“非法 START 执行成功”。timeout 阶段的 record rc=-1 是预期成功条件，其他异常返回值仍失败。所有完整任务正确性由真实输出捕获验证，CPU 不读取 expected 来伪造结果。

最终 `mail[1]=overall rc`、2=完成阶段数、3=当前phase、4=真实trap总数、5=53313631、6=IRQ0、7/8=A/B descriptors、9=短timeout；fence 后 mail0=53313650 为序列成功，bad00032 为普通失败。未预期异常仍使用原 bad00001。只有序列最终 mailbox 才结束仿真，不能在 phase8 第一次任务成功就 finish。最终必须10阶段、5次真实 guarded trap。

## 构建记录与当前哈希

- v1：Zig 实际编译成功，但默认剥离符号表，构建后无法核验 fault labels，构建器拒绝产生 PASS。目录保留。
- v2：仅新 builder 增加 `-g` 保留符号；实际 SW 编码/恢复地址核验通过。其 source hash 字段后来明确区分 canonical LF，故保留但不作为最终包。
- v3：当前冻结候选；代码3788 B、9项源码依赖哈希逐项复核、ELF/segment/metadata/boot逐字节核对、实际 A/B 源 payload 交叉核对通过。

| 对象 | SHA256 |
|---|---|
| v3 manifest.json | `c04056ff804ae88660be2fcdc723aadbb0a53d92af7d2b49fc5220cb20e895cd` |
| driver.elf | `5f751362ad33a01f0b4237c84ef36b809708e23f6913741451c19eb0a80b9acd` |
| sequence.verilog | `f3c9e02cf9ba0c36b616dbfc6243f48a2ee84774c73da5d9f5f40db77f79029f` |
| main_dma16_sequence.c | `3134f4f3399119e499b451c33828a46fa28b757e7ffed3466f0d4654e05e9fbb` |
| start_dma16_sequence.S | `0fc68194f7fedc47483d3910affdb61c2667837abaf0e74e152ab1ba66ef383d` |
| build_dma16_sequence.py | `a91b0567b95205a7170887748284e51ade863246cd6fb17641b9610adae03831` |
| test_dma16_sequence.py | `af369e558be50625ba746ea25d1fa2749a514b03a9fda4ed9f93f4ea3a243ac8` |

当前真实 ELF：guarded store=80000100，resume=80000104，trap_entry=8000004c，C handler=800007c0；SW 指令实际为0062a023。新 monitor 可用 `+EXPECTED_FAULT_EPC=80000100` 绑定该冻结镜像，不猜测“程序区内任意 epc”。地址会随将来的程序构建变化，须从对应 manifest 取值。

8项测试涵盖 program-only四词元数据、非法输入区/元数据预置、source ID/shift/descriptor错误、短timeout范围、实际32位故障指令和恢复标签、缺失符号拒绝、运行源身份变化拒绝、Python3.6语法。测试只证软件契约。

## 下一步缺口

待 sibling 完成新 source/monitor 的实际数据切换、各阶段真实 MMIO/ACK 观测、PREPARE冷失效、真实结果捕获和无全局复位守卫；本地真实 DMA夹具用于先验这些机制。随后 root 新建独立 ASIC CPU sequence 入口与完整冻结包，验证 E203 实际 store fault 的 cause/epc/mtval、恢复 mret、程序每段回执、取消/timeout排空后恢复及A/B/A数值。

不将原功能 TCM sequence、旧序列PASS、软件夹具或本次编译成功复制为新 ASIC CPU 证明。未实测前不调整计时起点、吞掉异常或把输入换bank直接当成完成硬件加载。

## 接续任务：独立真实 ASIC sequence runner（进行中）

root 已继续授权本子代理新增 `scripts/dma16_sequence_soc.py` 与契约测试；尚未创建 runner。不得修改 server_run/package，由 root 统一接 stage。默认 `ROOT/firmware_sequence`；一次真实 CPU 启动执行10阶段。复用 install_dma16 到新 run/platform 后只替换 monitor include，编译真实标准单元/宏/物理boot，不使用旧功能TCM路径。冻结全部9项固件sources、新sequence source/monitor、既有task_window16、布局、boot、向量和实际源文件；明确 polling，不宣称IRQ。

sibling 当前开发接口已定（其文件未完成本地验证，不作为冻结通过）：

- `tb/arch03_dma16_sequence_source.sv`、`tb/arch03_dma16_sequence_monitor.svh`；编译既有 `arch03_task_window16.sv`。
- Plusargs：`FIRST_LOAD32`、`SECOND_LOAD32`、`DATA_DIR`、`SECOND_DIR`、`CAPTURE_PREFIX`、`EXPECTED_FAULT_EPC=%h`、`FIRST_DESCRIPTOR=%h`、`SECOND_DESCRIPTOR=%h`、`SHORT_TIMEOUT=%d`，另程序物理boot使用 `BOOT_DIR`。
- 三份成功 CSV：`<prefix>__task1.csv`、`__task2.csv`、`__task3.csv`，原 row,col,signedresult,sat，分别核对A/B/A。
- 源准备 marker：`DMA16_SEQUENCE_SOURCE_READY words_per_bank=11744 scope=PC_file_only no_ITCM_task_data=true`。
- 每次源选择 marker：`DMA16_SEQUENCE_SOURCE_SELECTED descriptor=%08h`。
- 每phase：`DMA16_SEQUENCE_PHASE_ARM phase=.. descriptor=..`；随后唯一原 `DMA16_TASK_WINDOW`；最后 `DMA16_SEQUENCE_PHASE_PASS phase kind rc source_acks stage_acks read_acks output_acks start_cycle end_cycle cycles window_failed saturated`（均key=value）。
- 前5个非法配置窗口没有源请求，start/end/cycles可能为0；它们的时间戳不作为性能。前7窗口均 failed=1/failure_code=11（预期失败阶段），phase6/7有真实部分传输，末3完整窗口 failed=0/failure_code=0。
- 最终真实 CPU marker：`DMA16_SEQUENCE_PASS phases=10 tasks=3 outputs=76032 cpu_executed=true guarded_faults=5 timeout_recovery=true`。
- 本地 `ARCH03_SEQUENCE_NO_CPU` 夹具的最终 marker 明确 cpu_executed=false、actual_CPU_traps_verified=false、actual_driver_timeout_verified=false；ASIC runner 必须拒绝这种日志，不可将夹具变成CPU证明。

解析计划：逐日志顺序将 ARM→WINDOW→PHASE_PASS 绑定10阶段，检查descriptor A×8/B/A、各kind/rc与部分/完整ACK，末3总线时间差严格cycles×6.666666ns且与76032实际CSV一致；最终必须真实CPU marker与5 guarded fault。每段日志、固件metadata/source身份均保留哈希；失败写回执并停止。还需 sibling 本地验证后的接口稳定确认，然后root实际ASIC集成。

### 最新状态：v4 固件与 runner 已实现，等最终夹具日志互验

以上“尚未创建 runner”已过时：已新增 `scripts/dma16_sequence_soc.py` 与 `scripts/test_dma16_sequence_soc.py`，11项契约测试通过。入口按 root 指示固定为 `verify(cfg,run,platform_source,cases,call,firmware=None)`，恰好两个不同case且顺序等于FW manifest A/B；默认 `ROOT/firmware_sequence`，不接受 activity，防止把三任务合并为一个功耗窗口。root 统一接 server_run/package，本子代理没有改这些文件。

为 root 打包新增 `build_dma16_sequence.verify_firmware(firmware,source_root=ROOT)`，返回 `(manifest, Path(sequence.verilog))`。它核验精确9项sources、真实ELF/故障指令与恢复标签、segment、4词metadata、程序镜像逐字节和10阶段契约。root 同时为 dma16_batch 增加宿主耗时记录，新batch SHA=`388468647b16d661d46926428f6f54bbb5dcf347e0a7077c44114180a52ff518`。因此保留v3，重建了**当前 v4**：

- `local_runs/dma16_sequence_firmware_20261109_v4/manifest.json` SHA=`2d921e2563d7dd70b51d7d29f36b802e208a18445b3c05df2c6a086f6203ff1b`。
- 当前 builder SHA=`1929e60be8976c657521e324dee43ff2541e4b9ae236d40aa6516b3f362ce90a`，已明确停止修改，供 sibling 和 root 冻结。
- v4 ELF、sequence.verilog、程序/metadata字节、EPC/store/resume与v3完全相同；只是source依赖身份及验证入口更新。实际调用新verify_firmware已PASS。
- 新runner先按原validated_data核对task_identity，再在新run现场prepare tile16，实际源文件用verify_runtime_sources核验；冻结9固件源、monitor/source/window、模型、平台修改、向量/布局、物理boot后真实VCS编译和一次simv启动。
- parser关联 ARM→WINDOW→完整33词RECEIPT→PHASE_PASS，最终要求真实CPU marker。新RECEIPT格式为 `DMA16_SEQUENCE_RECEIPT phase=N words=<33个逗号分隔8位hex>`；已要求 sibling 放在PHASE_PASS之前。
- **取消/超时失败window的byte计数会在failed置位后停止增加；独立phase ledger继续累计排空后的真实ACK。** 例如phase6 window source34而ledger35，phase7为1347/1348。因此失败window只要求不超过真实ledger，不要求相等；成功8..10严格四段全数一致。失败阶段不算性能任务。
- 11项测试覆盖完整10段/三capture、失败window与drain ledger差异、拒绝NO_CPU、缺失receipt、错误实际fault EPC、源/phase顺序、成功ACK不足、失败窗口计数超过ledger、capture饱和、周期边界/时钟、Fatal/缺final、Python3.6语法。

sibling 当前已绑定v4启动最终真实RTL夹具回归（2026-11-09 session58783），含3个真实负测和完整10阶段，新增raw RECEIPT及unknown MMIO error/data拒绝；其source/monitor/TB/本地runner运行中不再改。尚待完成后给log/hash。本子代理接下来应：直接对真实夹具10段与3CSV调用分段解析校验，整体ASIC parser必须拒绝其NO_CPU/缺ASIC模式证据，不能把日志最终marker改为true来假装CPU；然后交root最终runner/hash/证据与CPU待验证缺口。

已向root提示：旧MMIO8 wrapper数据manifest绑定旧batch helper SHA，更新后不能当新源已验证；新8参考runner现场重新prepare不受影响。若打包复用旧wrapper，必须新目录重封装，不能改旧manifest。

### 最新完成：runner 与真实 RTL 夹具日志交叉核验

runner当前 SHA=`bb17959339f04c945653ee1da083a726fd165f5c18fe314e85860b0b6dd69057`；`test_dma16_sequence_soc.py` SHA=`52933f23bd740abe5d5e3d1519192e77db729dc5d815722289fd3418ff61fba6`。单测增至 **12项全部PASS**。

集成复核发现 asic_boot 在TB里注入的 clock guard仍引用旧 `a3_mon_clk/a3_mon_rst_n/a3_window_active/a3_window_finished`，而新sequence monitor没有这些别名。已**仅在新runner生成TB的sequence include后、原guard前**增加4个wire：clk/rst接s16；active为phase!=0且completed<10，finished为completed==10。因此监控全部阶段及间隔，避免未驱动implicit net，也没有修改冻结asic_boot/monitor。新增单测核对声明顺序与整个序列范围。

sibling 最终夹具已PASS：`local_runs/dma16_sequence_fixture_20261109_200001_072693`，实际DMA/core/fabric pin_mock、procedural MMIO、**无CPU**，有3个真实负测（提前换源、错EPC、缺receipt32）及10阶段/76032输出。冻结 source SHA=`60c2832c66c80ed3c8b67cc7dac1aee6ca43e853fcbbda1f6a966bfe20fd9820`；monitor SHA=`93259f9e028f092c7b612e5b87a3867fb9abf9314ee37f31d201cbc1ab5604f2`。

本子代理直接读取该**未修改原日志**，分别使用runner `check_phase`核对10条完整33词receipt与对应window/phase摘要，再用逐坐标checker核对三份CSV共76032值。全部通过。A/B/A饱和数分别0/4554/0，A两次capture完全同SHA。完整ASIC `parse_transcript` 对该原日志明确抛出 `NO_CPU fixture cannot establish real CPU sequence acceptance`，不补造ASIC模式marker、不改cpu_executed为true。

交叉核验回执：`local_runs/dma16_sequence_parser_crosscheck_20261109_v1/receipt.json`，SHA=`faa615855e617335140606b2b241bff7236038b910a9febe8fa4b36701e70416`。其cpu_executed/asic_CPU_sequence_verified/actual_CPU_traps_verified/actual_driver_timeout_verified全部false，保留真实fixture log/summary/source/monitor/fw/parser/capture各hash。

已向root交付API、v4固件目录、runner/hash与测试范围。现停止修改代码和builder；只待root接真实服务器ASIC stage。旧 `kwt_dma16.c`、`start_dma16.S`、`build_dma16_firmware.py` 对HEAD无diff。真实E203异常CSR、mret恢复、程序中的timeout、完整无复位sequence CPU执行、STA/功耗仍待验证；不能把此次真实硬件夹具结果当CPU通过。
