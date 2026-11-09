# DMA16 离线布局交接

更新时间：2026-11-09（已追加 start_ready 固件修订和 boot_by_shift 批量入口）。子任务执行者：contest_requirements。
最新固件：polling=`dma16_firmware_poll_20261109_startready_v2`，IRQ=`dma16_firmware_irq_20261109_mapping_v1`（仅编译通过）。最新批量映射夹具为 `dma16_batch_fixture14_20261109_bootmap_v4`。早期产物保留，仅作历史证据。
有效主计划：`IMPLEMENTATION_PLAN_DMA16_20261109.md`；用户已批准 IMPLEMENT，H0=2026-11-09T17:16:08+08:00。
本文件只记录布局工具和数据准备，不替代主 `CONTEXT_HANDOFF.md` 或硬件验收。

## 已完成

- 新增 `scripts/dma16_layout.py`：复用现有 `numeric.py` 的 Q12/40bit bias/移位/舍入/饱和语义；将已冻结的 8 lane 输入转换为 tile16。
- 新增 `scripts/test_dma16_layout.py`：14 项单测全部通过，包括原坐标、负数/40bit 极值、tile/lane 置换、字节序、偏置高填充、长度、源哈希、输出坐标和 HEX 与 binary 一致性。不会把 pack/unpack 往返当作独立验证。
- 导出 `local_runs/dma16_layout_14case_20261109_h0/`，包含 layer_01..12、extremes、rounding；每例 22,976 个原始 X/W/b 坐标及 25,344 个输出核验，共 354,816 个输出。`total/result/saturated` 均与原冻结 `expected.npz` 逐位一致。
- 原数据源：`local_runs/light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386/validated_data/`，未改动。每例源文件先校验已有 layout/codec 哈希；实模型 case 还核对原 `input_integer.npz`。
- 独立坐标验证：按照原矩阵坐标 (row,k)/(k,column)/column 直接计算字节地址，不调用 tile16 解码逆函数或重用打包遍历；随后对传输所得整数运行既有数值参考，核对原结果。
- `E:/fpga_race-two/model_data/upstream_verification.json` 的 36 项文件在 `E:/fpga_race-two/keyword-transformer` 下实际重新计算 SHA256，全部与已核验 upstream receipt 一致。没有重新运行 TensorFlow、重新量化或修改模型。
- 生成器 SHA256：`c034f438c7a901c5ec3c6a4e75cf203873aee9f79e292546fa728467d11d2a1d`。
- 测试 SHA256：`183e01a55522afb238b2117fbdb8321280949e8ec4dbe90fad7ec2ca8dbfdf22`。
- 14case 根 manifest SHA256：`f134118ac38b5bd01406b76a282d13d7df677428a3ceb7f0bc313a0fce8a717e`。

## 协议及文件

- X：99×64 行主序，6,336 half，12,672 B。
- 16 个 tile：每 tile 包含 W[64][16]，按 k→lane 顺序 1,024 half；随后 16 个 bias，每个 low16/mid16/high8+zero8 共 3 half。每 tile 1,072 half = 2,144 B。
- 总输入 23,488 half = 11,744 个 32bit word = 46,976 B；基址要求 4B 对齐。输出 99×256 行主序，50,688 B。
- W 字节地址：`12672 + (column//16)*2144 + k*32 + (column%16)*2`。
- bias 字节地址：`12672 + (column//16)*2144 + 2048 + (column%16)*6`。
- 输出字节地址：`2*(row*256+column)`。
- 运行输入只包括 `load.bin`、`load.hex`（16bit 行）、`load32.hex`（32bit 行）。32bit word 的低 half 是先出现元素，little endian。
- `expected.npz`、`total.hex`、`result.hex`、`saturated.hex`、`result.bin` 仅供验证，不能作为硬件输入或预计算答案。
- `layout_manifest.json` 记录 shape、地址公式、tile 偏移、对齐、编码、量化、原始输入/模型/生成器哈希。明确 `rtl_verified=false`、`official_precision_verified=false`；离线转换不构成省略硬件装载时间的依据。

## 已尝试及结果

- 普通 `python` 命令解析到 WindowsApps 占位程序，启动失败；已改用可用的 `E:/fpga_race-two/.venv-kwt/Scripts/python.exe`（Python 3.8 / NumPy 1.19.5）。后续不要反复尝试占位 `python.exe`。
- 14 项单测：PASS，1.660 s。
- 14case 原文件哈希、布局坐标、传输后算术及全部输出：PASS，软件路径；未运行 RTL 或服务器任务。

## 复现命令（仓库根 PowerShell）

```powershell
& 'E:/fpga_race-two/.venv-kwt/Scripts/python.exe' workspaces/arch03/scripts/test_dma16_layout.py
& 'E:/fpga_race-two/.venv-kwt/Scripts/python.exe' workspaces/arch03/scripts/dma16_layout.py --source local_runs/light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386/validated_data --output local_runs/dma16_layout_14case_20261109_h0 --verify-only
```

重新导出必须使用新的输出目录，并加入：
`--upstream-receipt E:/fpga_race-two/model_data/upstream_verification.json --model-root E:/fpga_race-two/keyword-transformer`。
脚本拒绝覆盖已有输出目录，不要删除旧结果来隐藏失败或改变受测配置。

## 100 样本入口与尚未完成事项

- 旧 100 样本/1,200 task 的确切已核验入口见 `handoff/team/evidence/ARCH03_BATCH100_20261108.json` 和 `scripts/batch_soc.py::dataset`。
- 旧数据在服务器 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`；`manifest.json` SHA256=`0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507`；schema=`kwt1-full-arch02-q12-v1`。各层含 layout.json/load.hex/expected.npz 等，可逐 case 调用 `export_case`。本子任务未访问服务器，也未发现这份完整 100 样本 manifest 的本地副本。
- 旧批次软件 1,200 case 核验、CPU 37 case 已通过，第 38 case 用户中断；这不是新版 DMA 验收，不能续跑旧可执行文件代替新版 1,200 case 回归。
- 本地已有完整 600 条开发集缓存：`local_runs/d1_full_matrix_600_20261109/`，包含 dev_000000..599.npz、parameters.npz、samples.json、environment.json、evaluation.json。将来若选择其固定 100 个样本，可复用缓存，完全无需重新执行 TF；但它和原服务器 100 样本不是同一清单，必须明确记录选择及新哈希，不能冒称复用原 100。
- 缓存 hashes：evaluation=`8832e338ecdf383a68266ca32da1b522b77c631df86db7291688dd4830b50934`；samples=`80e9ea7de8f0412ce222310f0e84f2c32022b440bbed5c61d7830fa0879c9b11`；parameters=`99a3f2d990203b2bd9f3bdf5dc98974d6a7102027f7d67b9abf19e72ee03a6ad`；environment=`0fd3cb704c56cdf133cdf8a2fecd3dbfe4ca3b57244cb0c6e7cea4632c4be7ad`。
- 待主代理安排：将新向量接入 16lane RTL/ICB DMA；真实加载到末写响应计时；仲裁/反压/错误/复位取消覆盖；全 SoC 仿真、综合/时序/功耗；最终新版 100×12 回归。当前没有这些 PASS。
- 本子任务不改 numeric.py/full_matrix_eval.py、共享报告、厂商目录或原始向量；没有 git commit、上传、服务器连接或进程操作。

压缩后先读本文件与有效主计划，核对已生成目录和源码哈希，再继续；主代理的其他文件可能同时变化，不覆盖。

## 后续完成：ASIC 批量 runner 的独立准备

主代理后续授权新增纯标准库批量组件，仍不修改 asic_soc.py/batch_soc.py/install_platform.py 或主报告；没有服务器操作。

新增 `scripts/dma16_batch.py` 和 `scripts/test_dma16_batch.py`：

- Python 3.6 标准库运行入口，不导入 NumPy、numeric.py、TensorFlow 或平台安装模块；Python 3.6 语法解析通过（实际测试解释器仍为本机 Python 3.8）。
- `index_legacy_dataset(root)` 固定核验旧 100 样本 manifest SHA256，100 个不同样本、每样本 12 层、全部 7,201 文件入口/哈希。实际本地仅运行结构性夹具测试，未访问服务器的这 100 样本。
- `prepare_case(source, destination)` 按旧 8lane 块复制重排；`verify_reorder` 另按原 row/k/column/bias-part 地址核对，检查高填充位；产生 tile16 load.bin/load.hex/load32.hex，原参考只读复制到 DATA_DIR，绝不放入 boot。
- `validate_contract(contract)` 校验所有冻结角色文件和哈希：executable、rtl、platform、firmware、boot、monitor、timing、layout、libraries、compile_receipt。代码和配置变化拒绝复用。
- `command_for` 只添加 `+LOAD32=... +DATA_DIR=... +CAPTURE=... +SHIFT=...`；boot 地址/层级/宏布局完全由主代理准备的 frozen command/extra_args 和文件承担，不猜 hierarchy，不调用旧 asic_soc 的输入镜像。
- `check_capture` 检查 CSV 为 `row,column,result,sat`，全部 25,344 坐标唯一、完整、数值和饱和一致。
- `run_tasks` 按顺序运行已编译产物；FAIL 立即停止，失败 attempt 永久保留。显式 resume 时核对身份和已完成 PASS 前缀的源码、输入、参考、捕获、日志及回执；未完成 case 建立新 attempt，不能覆盖旧失败。
- shared lock 目录由 contract 明确提供；只释放本次自己建立且 owner 完全一致的锁，不清除别人/残留锁。
- 状态和回执始终区分 `mode=hardware` 与 `mode=dry_run_fixture`；夹具永不宣称 ASIC 运行。硬件 mode 也不代表时序、功耗或官方精度通过。

### 已验证结果

- 15 项对抗单测 PASS，8.289 s：布局、源哈希、重复/缺失坐标、非整数 CSV、饱和、周期差一、未 drain、缺 marker、编译/固件/计时/命令/源码变化、篡改捕获、停止/恢复和他人锁。
- 最新准备数据：`local_runs/dma16_batch_prepare14_20261109_h0_v2/`，14case preparation-only PASS；与先前 NumPy 导出逐字节完全一致，共 328,832 half。回执 `numpy_crosscheck.json`。
- 最新 runner 夹具：`local_runs/dma16_batch_fixture14_20261109_h0_v2/`，14case、354,816 条模拟 capture 行通过整个 runner/receipt 检查。**capture_origin=copied_verification_reference，asic_executed=false，rtl_simulated=false，hardware_performance_measured=false**。这是控制流程夹具，绝非真实硬件输出。
- 初版同名 `_h0` 目录保留；最后加强完成计数类型检查、最终冻结文件复核后，用新的 `_h0_v2` 目录重跑，不能用初版回执核验最终脚本。
- 最终 batch 脚本 SHA256：`1520360adbf0ca27396a99cd655d5afddfc50995e041d82a01b54ce516a9d917`。
- 最终 batch 测试 SHA256：`de9c48a3afa4cda27bd13e0b5b940a3362c027f489d1b16b1cdce0d31ee1a1ca`。
- prepare smoke SHA256：`0c54170a15d33f7ac957a8813e25a0b15b6cea210523c3d659949e5a388d6208`。
- NumPy 交叉核对 SHA256：`cc4aa69a2f752b2ea60ff4f8316ca8ac1865d9516b884a7f083c08f1401830ab`。
- runner fixture 摘要 SHA256：`f08370fdd4614acb6a89a2121ce169f43c75542f00fc495926404625be8c5ae9`。

### 与主代理确认的 monitor 契约

主代理明确接受以下单行，`cycles = final_response_cycle - first_request_cycle`，不加 1。
起点由 source request valid 首次实际发出观察，而非 ready 握手；终点为末输出 ACK 且 pending=0。

```text
ARCH03_DMA16_BATCH_RESULT {"status":"passed","outputs":25344,"cpu_executed":true,"first_request_cycle":7,"final_response_cycle":100,"cycles":93,"saturated":0,"pending_transactions":0,"all_writes_responded":true}
```

以上数值仅为语法示例，不是测量值。结果必须唯一；ERROR/FATAL/FAIL、缺/重复必要 ASIC 模式 marker、饱和总数不符、未 drain 或周期不符一律拒绝。

### 实际编译入口集成前仍需提供的 contract

`schema=arch03-dma16-batch-contract-v1`，`mode=hardware`，scope 选择 `asic_rtl_functional` 或 `mapped_gate_functional_no_sdf`；`boot_scope=firmware_only_no_task_inputs`；提供正整数 timeout_seconds、shared lock_directory（绝对路径），command_prefix（argv 列表，不使用 shell），extra_args（例如绑定已准备物理 boot 的 `+BOOT_DIR`）。files 是绝对路径→SHA256，roles 是上述各角色→files 中路径列表，全部非空。

timing 必须等于：

```json
{"start":"first_load_request_issued","end":"last_output_write_response_drained","clock_period_fs":6666666,"cycle_convention":"end_minus_start","cold_cache_each_task":true,"cross_task_prefetch":false}
```

hardware build_assertions 必须由实际编译/boot 审核阶段支持并填写：

```json
{"actual_asic_models":true,"global_FPGA_defined":false,"firmware_only_physical_boot":true,"task_data_preloaded":false,"compile_inputs_complete":true}
```

required_log_markers 为主代理实际 boot/模式监视器应输出的完整固定行列表，硬件模式不能为空；runner 逐行要求唯一。contract 只能引用实际完成和审核的编译结果，不以填写这些声明代替 ASIC 验证。所有 contract 字段、本 runner 源码、每个 task 的原 layout 都进入 resume identity。

复现软件准备和夹具（输出用新目录）：

```powershell
& 'E:/fpga_race-two/.venv-kwt/Scripts/python.exe' workspaces/arch03/scripts/test_dma16_batch.py
& 'E:/fpga_race-two/.venv-kwt/Scripts/python.exe' workspaces/arch03/scripts/dma16_batch.py prepare-smoke --data <旧14case目录> --output <新准备目录>
& 'E:/fpga_race-two/.venv-kwt/Scripts/python.exe' workspaces/arch03/scripts/test_dma16_batch.py --smoke-source <旧14case目录> --smoke-output <新夹具目录>
```

服务器将来实际命令（尚未执行）：

```text
python3 workspaces/arch03/scripts/dma16_batch.py run --data /storage2/2026contest/server4/s4_21usr/Desktop/IC/hex --contract <已冻结实际编译contract.json> --output <独立运行目录>
```

恢复仅在完全相同配置时显式增加 `--resume`；已通过完整批次不可原地重跑。后续实际 compile/TB 集成、14case ASIC smoke 和最终 1,200case 仍由主代理安排，当前均未执行。

## 后续任务：DMA16 独立固件（进行中）

主代理授权只新增 `sw/kwt_dma16.h`、`sw/kwt_dma16.c`、`sw/main_dma16.c`、`sw/start_dma16.S` 和 `scripts/build_dma16_firmware.py`；以上已新增，不改旧固件、link.ld、旧构建脚本。不连接服务器，不提交 Git。

### 已完成及实际本地构建

- 读取 DMA16_ABI.md、原 kwt.c/main.c/start.S/link.ld/build_firmware.py，并对照实际 arch03_dma16_accel.sv。
- 配置 API 支持 DMA/MMIO debug、shift、prefetch、源/共享输入/输出地址；每任务先 CANCEL 排空、CLEAR 使 core 失效，再配置。默认地址 source=B0000000/input=A0000000/output=A000C000，ID=4b575416，layout=00100001。
- mcycle64 用 high/low/high 稳定读取；timeout 和 cancel timeout 各自有界。CANCEL 不撤销已有总线事务，只有 active/core.busy/pending 有效位都清空、COMPLETION aborted/drained 位确认后返回；未响应则 NOT_DRAINED。
- 特别注意 PENDING 的 kind/state 是诊断字段，可能保留旧值；检查工作有效位 mask=0x1f1f，不能要求整个寄存器为零。
- DMA成功核对 LOAD_COUNT=23488、OUTPUT_COUNT=25344、COMPLETION低5位全1、committed=46976/50688、源读/共享初写/共享回读/结果写 ACK=11744/11744/11744/12672。
- MMIO debug mode 做真实 source→shared 32bit copy，然后按16lane tile输出坐标写回；不从ITCM取任务数据。该路径不是DMA吞吐证据。
- 完整machine trap汇编保存全部整数寄存器及mepc/mstatus，C处理MEIP/MTIP；真实IRQ逻辑已写，尚待完整地址核验构建。
- IRQ路径采用关global MIE→重新检查完成/超时→WFI→恢复MIE；MTIE/MEIE局部使能保持，CLINT周期中断保证DMA不发IRQ时仍能检查mcycle超时。进入第一次WFI前，必须在有界轮询中观察到真实timer ISR执行，否则拒绝睡眠。
- 共享GPIOB源：claim后读取DMA IRQ_STATUS、W1C已观测事件、fence、complete；非DMA来源交weak hook处理；未处理IRQ记错并禁MEIE避免中断风暴，不能擅自清GPIOB外设。
- mail[0..6]保留旧成功/错误、rc、输入数、输出数、cycle low/high、sat格式；mail[7..31]扩展ABI/layout/status/completion/pending/首错/ACK/committed/IRQ/timer/WFI/cancel诊断。
- builder没有 `--data` 参数。ITCM镜像仅ELF代码和0xfff0处SHIFT元数据；0x10000之后所有196608字节为零。支持独立shift_11/shift_12镜像，byte HEX固定LF及binary双份，记录编译器/源文件/ELF/image哈希。
- `--self-test`：8项ELF/metadata/禁止输入区自检PASS；builder Python3.6语法解析PASS。
- Zig0.13.0真实RV32IMAC/ILP32编译，-Wall/-Wextra/-Werror：DMA polling构建PASS，MMIO debug polling构建PASS。只代表编译和镜像边界，**CPU/IRQ/RTL/时序/功耗都未验**。

默认DMA polling产物：`local_runs/dma16_firmware_poll_20261109_h0/`。
ELF SHA256=`bcae39dd55aa762a05f5ff38dcd43f877a7ce61d13c04b0db7888a009a8fdee9`；单代码段0x80000000、2014B。
manifest SHA256=`5f6e43237254e2c5d0b5d4a62dfbf2708d659aa8a9ddc6be4797d3cf23944115`。
shift12.verilog SHA256=`34964d6e99c195e03b1e17cf715bbef173ba918793ec667bf1d411b8b5c22968`。
MMIO debug产物：`local_runs/dma16_firmware_mmio_debug_20261109_h0/`（mode=0,prefetch=0）。

### IRQ寄存器核验进度

主代理已从fixed RTL实际核验（不是地址猜测）：

- PLIC_IRQ_NUM=17；16物理源拼接后bit0常零；GPIOB=io_devices_0_15 → claim ID16。新DMA IRQ与原gpioB_irq OR，保留原线。
- PLIC base=0x0c000000。
- priority16=0x0c000040；enable[0]=0x0c002000，mask=0x00010000；threshold=0x0c200000；claim/complete=0x0c200004。
- PLIC译码证据：`E:/fpga_race-two/takeover_local/d2_20261109/dma16_irq_decode.png`（由主代理实际读取）。
- CLINT base=0x02000000已核验，**mtime/mtimecmp具体offset仍待主代理读取；本子任务不得猜地址**。
- IRQ构建需要 `--irq-config`，包含mapping_verified=true、mapping_evidence字符串、irq_id/plic_priority_addr/plic_enable_addr/plic_enable_mask/plic_threshold_addr/plic_claim_addr/mtime_addr/mtimecmp_addr/timer_wake_ticks/timer_probe_cycles。地址可hex字符串。缺少核验配置会在构建前拒绝，不以默认16宏宣称CPU验证。

WFI global/individual enable处理参考RISC-V官方机器态规范：<https://docs.riscv.org/reference/isa/priv/machine.html>。规范支持global MIE=0且局部使能的中断唤醒WFI；**实际E203实现仍需真实CPU运行核验**。

接下来：取得主代理核验的CLINT offsets和合适timer tick/probe参数，构建IRQ版；检查编译后镜像无任务输入，并将明确“编译通过，CPU待验”的产物交主代理接入ASIC boot/TB。不要用polling编译或软件stub证明IRQ/WFI有效。

### 最新修订：STATUS.start_ready 与按 shift 选择物理 boot

最终当前ABI SHA256=`6b1c53a46e8f490208adbd1d4734d2aead2bbe1ebf0df93cf0e294c7eba87c90`。旧 h0 polling manifest绑定c9d9版本，不能用于新ABI打包，目录仍保留。

- `kwt_dma16_cancel` 现在还要求 STATUS bit14(core.start_ready)=1；busy、core_busy、总线有效位和COMPLETION仍一起检查。
- CLEAR后新增带mcycle64 timeout的 `wait_start_ready`，要求bit0=0、bit14=1，失败保留错误并尝试有界取消排空；该等待在MMIO debug首个source读取之前。
- START前再次同样检查bit14，避免取消/flush尚未完成时启动。
- 主代理确认DMA START内部另有PREPARE状态先使旧X/权重valid失效，再发首个源读；软件不以此省略自身启动前检查。
- 新polling目录：`local_runs/dma16_firmware_poll_20261109_startready_v2/`，ELF=`763911034c70e65433c289449ea4f1a5f3cc294387b3df743ae0d4f21f87dc20`，manifest=`a7e8647ebd6be2a325dcf04f7e9395c3018987a89e0596312a76751c8ab2f683`，绑定上述最终ABI。
- 新MMIO debug目录：`local_runs/dma16_firmware_mmio_debug_20261109_startready_v2/`，mode0/prefetch0。两种Zig编译通过，仍未CPU验证。
- 当前C SHA256=`9b7729814da24ea03784903e2bf0c3308daccc53f38dcc89aa03959d7844d991`。
- 核心子代理只读复核：取消/排空、ACK数量、COMPLETION、16lane输出坐标与core/engine语义一致。**MMIO debug的CPU copy在START之前，不适用只观察DMA端task_arm的新版DMA性能计时器，只作调试；不能直接拿来充当同口径8路对照。**

batch contract现在支持 `boot_by_shift={"11":"<绝对物理boot目录>","12":"<绝对物理boot目录>"}`：

- hardware模式强制该映射；run_tasks启动任何case前核对全部任务的shift均有合法目录。
- 每个目录必须存在且非空，全部文件必须进入contract.files和roles.boot；不同shift必须使用不同目录。
- command_for按当前case shift添加唯一 `+BOOT_DIR`；映射存在时，command_prefix/extra_args出现任何额外 `+BOOT_DIR`均拒绝。
- 物理boot内容/映射/哈希进入identity；即使人为更新文件hash，resume仍因配置变化拒绝复用。
- 旧dry_run_fixture不提供映射时仍可沿用单个额外BOOT_DIR，不能重复。
- 不修改server_run/install/monitor。实际批量将用独立命令自己持shared lock，主代理只编译产出contract，避免嵌套锁。

新增4类boot映射测试后共 **19项单测PASS**；旧14case fixture兼容回归通过（`dma16_batch_fixture14_20261109_bootmap_v3`）；新增完整14case按shift映射fixture通过（`dma16_batch_fixture14_20261109_bootmap_v4`），包括rounding shift11和12个真实层shift12，共354816行。夹具仍为参考复制，非ASIC结果。

当前batch脚本SHA256=`6328a1457b142dd8b5787ec50dd5de6cea76ea73128dde74ab1f34fa673081f5`；测试SHA256=`e39c1b1f338cb1baac38df910112d19e610e709e014aed9e371852301793866c`。
v4 state SHA256=`cc93cdd7c007586411b66548e32b3c2135fc226cf97a6b98d1a9d93f10dc9aab`。
新增复现选项：`test_dma16_batch.py --smoke-source <14case> --smoke-output <新目录> --smoke-boot-by-shift`。

尚待：CLINT mtime/mtimecmp精确地址、IRQ构建与真实E203/WFI/timer/共享GPIOB验证、真实ASIC批次。没有启动服务器任务。

### 最新完成：CLINT 地址核验与 IRQ 固件编译

2026-11-09 18:42 后主代理提供fixed RTL完整译码证据，已新增 `workspaces/arch03/irq_mapping.json`。以上“CLINT地址/IRQ构建待办”已完成；**CPU/IRQ/WFI/timer实际运行仍待办**。

- CLINT base=0x02000000，mtime=0x0200bff8/high=0x0200bffc，mtimecmp=0x02004000/high=0x02004004。
- 主代理核验sirv_clint.v链：T958=addr[25:2]，T940_bits_index=T958[13:0]，T1015_bits_index=T940_bits_index，T1600={index12,index1,index0}；offsets bff8/bffc/4000/4004分别选择2/3/4/5，对应time_0/time_1/timecmp_0_0/timecmp_0_1。写译码及全byte mask也已读核。
- 本子任务实际查看了 `takeover_local/d2_20261109/dma16_clint_verified.png`，保留该截图SHA256=`b71344f73b17d685f21debe646f684d3ff5c0d83d73ae56378c7c6da2e86ffb1`；PLIC截图SHA256=`ab16a1529f3b74671c5fb726ab5d2f3611373bbffb03980f7a66def2f6afd1bd`。
- timer_wake_ticks=1024、timer_probe_cycles=1000000 是主代理指定的首轮参数。没有推断或宣称实际tick频率，配置明确 `timer_frequency_hz=null`、CPU/唤醒未验。
- irq_mapping.json SHA256=`247d641e71b4e67092cfb212cb161f69f33f52bf7aa7d33e599af35cde334c8a`，包含全部PLIC地址/ID16/共享GPIOB说明、CLINT译码、固定platform baseline与截图hash。
- 实际Zig构建成功：`local_runs/dma16_firmware_irq_20261109_mapping_v1/`。代码段3152B，ELF中WFI/MRET指令编码各1处（只证明指令已编入，不证明执行）。shift11/12镜像各262144B，0x10000之后全零。
- IRQ manifest SHA256=`823456a56b4115e67f40a21988dc0b8e777accd3af626aab44765c922a01a7c2`。
- IRQ ELF SHA256=`ab1a3f2475f1e933fc2930a9b341a21bc9f0ff5687682c9045d2fbb313004640`。
- IRQ shift11.verilog SHA256=`a28ee039ee17b143997c363eee5754b047f47d4ae3ce375bca996ac9c1eda9ad`；shift12.verilog SHA256=`fedbe171dac4c51627cbf92679af7b8eb0542ab7608392c0e8b25c46829f5bab`。
- IRQ目录8个直接payload文件的canonical(name→SHA256) JSON（sort_keys=True,separators=(',',':')）SHA256=`f3c47d9effd8a22839531367188fb8195fd1d4398405a90ae6d557cba7480e45`。payload为build.log/build_command.json/driver.elf/manifest.json/shift_11.bin/shift_11.verilog/shift_12.bin/shift_12.verilog，不含compiler cache。
- IRQ manifest内输入mapping哈希与新JSON实测一致，ABI仍为6b1c53a46e8f490208adbd1d4734d2aead2bbe1ebf0df93cf0e294c7eba87c90。
- 本轮没有更改C/h/main/start/build脚本，IRQ与startready_v2 polling/debug保持同份源码，故未重复构建poll/debug。

复现IRQ构建需新目录：

```powershell
& 'E:/fpga_race-two/.venv-kwt/Scripts/python.exe' workspaces/arch03/scripts/build_dma16_firmware.py --zig E:/fpga_race-two/takeover_local/tools/zig-windows-x86_64-0.13.0/zig.exe --output <新目录> --irq-config workspaces/arch03/irq_mapping.json
```

下一步由主代理使用实际ASIC boot/TB核验：首次timer trap探针、外部claim/complete、WFI睡眠/唤醒、DMA与存储时钟持续、timeout/cancel drain、共享GPIOB非DMA中断处理和全矩阵输出。尚未运行服务器或改写旧产物。
