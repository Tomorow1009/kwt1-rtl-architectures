# P80三深度完成，深度2新综合运行

## 05:15最新：原综合已进入块映射，独立d2包正在传输

- **唯一VNC输入18873**：`local_runs/p80_d2_ops_transfer_e139032_20261116/transfer.ps1`共66行。先收完整输入及准备回执，禁止并发键入或重跑。
- 05:14:11实查：原父27509仍持锁，fresh link和characterization已结束；**DC子30930**正在`854包/runs/p80_synth_d2_01/p80_synth/blocks/shared_sram`，准备/启动时间05:14:08。不重启、不改当前854包。launcher中child000005对应共享块；尚无最终面积/时序。
- 最新GitHub已push **07dba32**（含e139032工具）。新的d2包源e139032a1892087869c41987acb0a8635e803c5a，仅部署、不启动新EDA；新包名`light-light126-p80-e139032`。
- 新包110个overlay文件，19文件变化；原854 payload保持。完整payload SHA **7db6c43046c4c7437e447526f325c2e47cded1b1542789d3b0f5080026001f4a**。
- 传输采用仅复制已知基底字节的无损差分，整包重建验证不变：23,916B XZ，SHA **b816d126a3e46896fec8b03f5a715b68cd4402f08fbf4aaa5a6449b26e74b18c**。实际66行传输脚本已在本地完整重演，目标payload SHA完全一致；不是估计或只验分段。
- 默认IRQ固件=原已验证的firmware_d2字节，恢复/竞争使用新编译的d2；所有固件source_sha256与包内源逐项一致。新prepare入口绑定三类固件的深度，3项工具测试通过。**尚无恢复/竞争的服务器CPU PASS，新的prepare回执也尚未观察。**
- 新包默认transaction_metadata_depth=2，并含p80_report工具。根`payload_e139032_d2.json`、`prepare_e139032_d2.py`由当前输入创建；不能重复执行旧完整raw差分/旧synth01启动器。
- 后续仍跟进原综合；新e139包在原锁自然释放后承担恢复/竞争/240/精度、同最终网表gate/SAIF/PT/报告。20样本限制、T80桌面/旧八路保护不变。


记录时间：2026-11-16 05:09（北京时间）。恢复先读AGENTS、根交接、本文件、STATUS本轮段和有效计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`。

## 约束及当前位置

- 服务器`Desktop/T80_Delivery_20261113`及全部旧八路数据不写、不移、不删。
- 当前只做P80；S0已冻结并持久归档，不重跑。C80、C32-A/可选B、G32均未开始。
- 最终32PE、≤1.00mm²、150MHz。P80当前仍80PE，原32位ICB及平台缓冲参数不变；源读→共享写ACK→原总线真实读回→解码→最终输出写ACK/排空。
- X14/W12/acc32/total33/SHIFT10不变；正式仅前20条/240任务/6,082,560输出，固定12性能任务单列。

## 已取得的实际服务器结果

运行根`/tmp/s4_21usr_p80_20261116_0315`。

1. 功能包`light-light126-p80-142fae2`，源码142fae28545759e33fa38de514eabf752cb8c43a，917输入，manifest **7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc**。
2. `p80_pilot_d4_02/p80_soc`首层真实ASIC/E203通过：25,344输出，80,471完整周期，31,428编码B，host4.6802235秒。此项单层不充当12层均值。
3. **sweep05已完整完成**，04:58:41实读status completed/current=None/error=None，原父324565自然释放锁。深度4、2、8各自14例全部通过，每版354,816输出及total/result/saturated、坐标、原总线路由和IRQ/WFI核对。
4. 三版固定12层周期完全相同：`80471,78357,77223,77503,76061,74997,73765,74101,73793,76537,80625,87111`。合计930,544，平均77,545.333333，150MHz折算**1934.352378824 task/s**。
5. 因三深度性能相同，**深度2作为最小性能候选进入新综合**，面积和时序尚不预判。不是P80阶段已验收。
6. 854工具包04:58:06准备通过：938输入、原源保持。包`light-light126-p80-8543440`，manifest **42ff74ed50d2da1b348bf69c7750ac231da5a83166519d2c700d43260e681850**，payload SHA **5915a15ab41d6601684684ecce16272316fa303e645f8732740dc04c3ffd0e89**。

功能目录：142包`runs/p80_fixed_d4_05/p80_soc`、`p80_fixed_d2_05/p80_soc`、`p80_fixed_d8_05/p80_soc`。原完整summary SHA保存在根`p80_sweep05.json`，不得手抄不清楚的哈希或改回执。

## 当前作业身份：05:08:18实际观察

- **父27509**，`root/p80_selected_synth01.json` status running、selected_depth2、session `p80_synth_d2_01`、error=None。
- 原共享锁`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock` owner27509，bundle指向854，child_ledger为`854包/runs/p80_synth_d2_01/process_ledger`。
- 输出`854包/runs/p80_synth_d2_01/p80_synth`；顶层launcher日志`root/p80_selected_synth01.launcher.log`。子工具日志在各stage目录，launcher空尾不代表无进程。
- 启动器`root/p80_selected_synth01_controller.py` SHA **0114a53c16a87afda1fff2342e096989d6b4f8314c14dfb1e89c0271ae055e3a**（本地93行LF）。先核三深度全部回执和同数据同硬件，再调用原新综合入口。S0只作为已测接口预算；新P80三块全部重新映射。
- **不重启综合、不改854运行包、不释放/换锁。**先读原process_ledger、state及日志终态。尚未看到DC最终面积/时序。
- 全部本地VNC输入会话30194、76006、52045、76592、11349、63322等已结束。VNC18874435/workspace3最后为Bash空闲。恢复仍须fresh windows/screenshot，不复用旧前台判断。workspace4未操作，FileZilla保持关闭。

## 已完成空间恢复及保留的失败

共享盘会被其他任务持续耗尽，df上一读数不是实时。所有新运行在私有/tmp，最终仍需持久归档；不是自动放弃备份。

本轮只无损归档**已通过的N1/B0普通csrc编译缓存**：逐文件size/SHA回读一致、原结果/输入不变、无活跃使用后删除重复普通缓存，保留目录、符号链接、源码、simv、日志、波形及结果。

| 缓存 | 文件数/原字节 | 归档SHA |
|---|---:|---|
| N1 ASIC14 | 35 / 10,643,394 | 2aa12ed47a2c7abbe76da8e382aece92d298cd27ab6ebeb93c0febd24ef538c4 |
| N1 sequence | 35 / 7,193,225 | aebb47bf12cc63bde45408a3671c16078733f027e10814b4a94e99cb22045269 |
| B0 SAIF12 | 40 / 80,788,435 | 8dcedc469f4325a79f246bedea03a6b043ac6ee5b5e3a3e4effe7b98c735db78 |
| B0 gate14 | 38 / 65,971,564 | fa4ee769a8689c877147b5bf59130173b36ba0cde7d684ba55426bd6cb4c8236 |

四份完整receipt和临时tar在P80根；各原stage另有`csrc_regular_files_20261116_p80.tar.gz`持久副本，已回读核验。最后两份receipt分别`b0_saif_csrc_20261116.receipt.json`、`b0_gate14_csrc_20261116.receipt.json`。**都不能再次归档/清理**。原B0实际路径从固定哈希机器清单取得，不沿用旧检查点手工转录的包名。

- B0清单`root/b0_cache_candidates01.json` SHA c5d5e6b4069637e5d720eebaa09ba684e53604a8e6da2a0ebf176a68f5a68cd5。SAIF索引0，gate14索引2，均已执行完。
- gate08脚本SHA **f0d722f0f672ed017c54c7a7d0e3cf22688eb81281b2b956d95b06414b5e45ba**；持久归档完成后立即启动上述父27509。05:07:39 free56,623,104B，之后须重查。
- sweep01、sweep02的固定14后继、sweep04均在建共享锁时ENOSPC，未启相应EDA；sweep02首层PASS仍有效。
- sweep03因手工manifest多一字符在预检失败，原包没变。sweep04 JSON残留starting是入口异常记录缺陷，实际已退出；不要当live。
- cache03/04、cache07在手工路径检查处退出，未删除文件；cache05传输因CRLF/LF SHA不一致，在创建/运行前停止。cache06（SAIF）和cache08（gate）才是真实成功入口。失败脚本保持。
- 05:00尝试创建128KiB新锁空间预留文件遭ENOSPC，05:01明确exists=False，**没有可释放的reserve文件**。不要据旧计划去删不存在/未核验文件。

## 本地后继准备

- 当前个人分支仍`codex/light-light126/t80-pipeline-c32-g32-20261115`，最新已push6b18024；后续7a5f011/a5e985f/e139032尚待同步。
- 深度2恢复固件`local_runs/p80_sequence_firmware_d2_20261116`已编译，十阶段；竞争固件`local_runs/p80_contention_firmware_d2_20261116`已编译。**均尚未CPU执行**。
- 两者使用与旧深度4固件逐项SHA相同的A/B逻辑数据：只读来源`E:/fpga_race-two/kwt1-rtl-architectures/local_runs/light-light126-n1-v4-20261113_045945-0f62e4120790/validated_data`，first layer_01、second rounding。
- Zig `E:/fpga_race-two/takeover_local/tools/zig-windows-x86_64-0.13.0/zig.exe`；本地Python `.venv-kwt/Scripts/python.exe -B`。
- e139032更新**本地下一包**的p80_prepare_bundle：支持2/4/8默认深度并绑定IRQ/sequence/contention固件的实际深度，新增/更新3项测试全部通过。不修改服务器142或854包。
- 下一步准备新独立深度2工具/固件包：以本地`local_runs/p80_overlay_8543440_20261116/payload.json`为基底，默认IRQ替换为现有p80_firmware_d2，sequence/contention替换为刚编好的d2，payload.transaction_metadata_depth=2，加入e139032的prepare工具及p80_report。打包前核验每份固件source_sha256与payload实际字节，不假设工作树换行等于Git/服务器字节。**新包尚未生成/部署。**
- 854已经含新综合/gate/SAIF/PT/精度入口；p80_report后于854加入，仍需新包部署。report工具本地两测试此前通过。
- 旧15行`p80_selected_synth01_transfer_20261116`未执行且现在**不能执行**：controller已经由cache07/08传入并启动，重复会冲突。旧S0_SYNTH05_FINISH_LAUNCH未跟踪文件不提交、不执行。

## 未完成与接续顺序

1. 跟进27509原综合至最终面积、setup/hold、宏与结构；不重复跑三深度ASIC14。
2. 部署新独立深度2诊断/报告包，在原综合释放锁后，完成自己的恢复/CPU竞争、240任务、浮点重算连接；按原队列规则串行。
3. 同最终网表gate14、SAIF12/PT12及独立时序/面积/活动审核、同配置报告、持久归档；P80通过后才进入C80。
4. 浮点有效容器是恢复原NPZ成员的`n1-recovered-float100-20261113.zip`，SHA5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2；原edb98e容器仍不是已取得的包。历史private源和NumPy路径见P80_FIRST_CPU顶部，使用前只读核实，不重新上传/替代原数据。
5. 重要进展/暂停/压缩前继续更新根交接和检查点；随后同步私人GitHub。不能把综合启动、编译固件或中间性能值当作阶段验收。
