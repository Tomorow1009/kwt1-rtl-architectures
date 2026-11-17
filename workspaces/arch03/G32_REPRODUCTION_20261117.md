# G32 源码、数据及复现入口

本轮采用16列×2行、32 PE，150 MHz，SS/0.99 V/125°C，工具周期6.666666 ns。正式批量范围为原榜单前20条×12层；固定12个性能任务单独统计。本文说明受测配置与运行入口，最终选择和持久备份身份以阶段结论、冻结回执为准。

## 身份及主要代码

生产硬件提交为`0e16994675bb15e53642017a88f6307da9af4a01`，运行包manifest为`3524e2726880684c1c5681ef90da3a1ca41d78daf20d0df5b648e633b6e42f4a`。正式网表SHA为`f02759430cff876497e7158a5b570a7543553f066a58197a5eeca0546c6e02bb`。

| 功能 | 工作区文件 |
|---|---|
| 32 PE脉动与数据门控 | `rtl/arch03_g32_systolic2x16.sv`、`rtl/arch03_g32_icg.sv` |
| 两行调度、缓存、偏置、结果 | `rtl/arch03_g32_linear16x2.sv` |
| 任务级DMA、提交与实际读回 | `rtl/arch03_g32_transport.sv` |
| MMIO、状态、IRQ接口 | `rtl/arch03_g32_accel.sv`、`G32_ABI.md` |
| 完整无损格式6解码 | `rtl/arch03_c80_decoder.sv`及对应C80编码工具 |
| 原总线仲裁与存储适配 | `rtl/arch03_icb_arb2_queued.sv`、`rtl/arch03_icb_memory_router_turnover.sv`、`rtl/arch03_shared_sram_turnover.sv` |
| 固定点转换 | `rtl/arch03_n1_requantize.sv` |

源读→真实共享写成功ACK→原ICB读回→解码→计算→最后输出写ACK排空，四段均保留。源信用3、事务元信息队列深度2、源/读回FIFO各16字、输出FIFO32字；原平台缓冲参数不变。X/W宏仍为60+32个128×16，23 KiB；有效数据为X14/F10、W12/F12、累加及偏置32/F22、total33/F22、结果16/F12、SHIFT10。

## 数据与参考

服务器输入目录是`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all`。原100条HEX库存清单SHA为`ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997`；正式任务只选其中既定前20条，未重新排名。原group8 HEX和运行编码文件各自保留哈希。

恢复的完整浮点容器为`/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip`，SHA为`5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2`。本轮核验同批成员身份，不声称它等于队友原ZIP的容器哈希。逐层NRMSE先合并平方误差及参考能量再开方，不平均百分比。

`total.hex`为signed33；软件和TB按坐标核对，不将脉动输出流直接reshape。真实ASIC/E203检查total/result/saturated；门级检查结果、饱和、全部坐标、IRQ/WFI、真实总线路径及完整窗口，内部total不可观测不计为门级证据。

## 执行顺序与工具修复

实际运行根为`/tmp/s4_21usr_g32_20261117_0810`，包名`light-light126-g32-0e16994`。每个阶段的request、进程账本、输入清单、日志和摘要均保留；不要在这些已完成目录重跑。

1. 本地`local_verify_g32_array.py`运行10000随机及32定向块，逐周期比较C32参考/G32门控/G32静态旁路。`local_g32_datapath_verify.py`、`local_verify_g32_sequence.py`及`local_verify_g32_transport.py`覆盖矩阵、1/2拍SRAM、连续任务、反压和取消。
2. `g32_qualification.py --request <新请求> --request-sha256 <请求SHA> --session <新名称>`负责真实ASIC14、恢复、竞争、三块综合、实际ICG时序、240任务与浮点连接。请求绑定新包、配置、数据、库和队列脚本身份。
3. `g32_finish.py`使用同样三个参数，执行新网表结构、门级14、SAIF12、时序/DRC和PT12。活动窗口从首源VALID到最后成功输出ACK并排空，包含首请求等待；不能用较晚的CPU finished事件替代。
4. `g32_report.py`输出逐任务/汇总CSV、JSON及中文说明；未知活动清单、实际网表连接、别名分类和任务模式时序另行审阅。原自动汇总的false标志不改写为人工结论，独立结论另存。

原首次ICG查询遇到PT2022不支持pin的`name`属性；失败状态保留。只将两处`name == E`及一处`name == TE`改为`full_name`末级匹配，修复源码SHA为`33c20a4c5a9d081a9d60e9ed9d57bda80da44081306630a9659499ed9bf1e57d`。实际恢复使用外部`g32_icg_timing_pt2022.py`；Git提交`1e0ef75`把完全相同字节同步到常规`g32_icg_timing.py`入口，便于今后新包复现，服务器原生产包未改。没有关闭门控检查、增加时序例外或重映射硬件。

现有证据链为`g32_initial01`的四个通过阶段＋`g32_recovery01`的ICG/240/精度＋`g32_finish01`的最终网表证据；`g32_export_review01`显式连接其终态哈希。旧失败状态不被改成PASS。第一次运行的新包使用已修正的普通入口，不需要故意重演旧失败。

## 备份及边界

持久归档须完整成员回读并保持源目录，位置及SHA记录在最终冻结回执。归档包含精确源文件、活动、结果、失败记录和外部修复工具；厂商库仍由服务器原授权路径提供。复制归档不等于已验证任意目录重定位，原路径或环境变更后应建立新配置与新运行目录。

同网表门级没有SDF；时序为声明的稳定任务模式，功耗为完整活动下的整机布局前库模型估算。官方600条、提取寄生后的时序/功耗和物理签核不在本轮通过范围。原桌面T80、旧八路和各已冻结阶段保持原样；完整100条不是本轮自动追加任务。
