# P80前20条完成，空间恢复与单锁接续

记录时间：2026-11-16 06:29，北京时间。恢复先读本文件、根交接、AGENTS和当前计划`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`。不要根据旧running记录重新派发。

## 当前有效目标及保护范围

- S0→P80→C80→C32-A/可选B→G32；最终32PE、150MHz/6.666666ns、SS/.99V/125°C、项目面积≤1.00mm²。S0已验收归档，当前P80尚未验收，C80/C32/G32没有开始。
- **服务器Desktop/T80_Delivery_20261113及所有旧八路文件不写、不移、不删。**本轮未改变它们。
- 四段真实搬运、原32位ICB和平台参数、源额度3、FIFO、SHIFT10数值保持。正式只跑前20条240任务，不扩100条。

## 唯一当前输入：先收完，勿并发

**exec 96487** 正在执行`local_runs/p80_combined02_recovery09_transfer_20261116/transfer.ps1`，35行。先等此输入结束并查看`E:/fpga_race-two/takeover_local/p80_combined02_recovery09_transfer_20261116.png`，不得并发键入、重复传输。

- 源提交`1e4f0bf`，payload SHA `132023d5f3675271ad7127ceae74235aa80859842f280d4a7cc9df584a9b1e6e`。
- 它只向当前P80临时根写入3个新脚本。随后运行cache09归档；归档成功才启动combined02。export02只部署，不启动。
- **归档结果、新队列PID及综合启动尚未观察**；不能先写成功。当前最后检查全部旧EDA/等待器已退出、原锁不存在。
- 脚本若失败，保留现场；先看回执和真实PID，不重跑35行。
- VNC18874435/workspace3，workspace4未操作、FileZilla关闭。当前无其他输入；恢复仍fresh windows/screenshot。

## 正式完成：P80自己的ASIC240

06:19:14原功能02父42584自然完成、退出。恢复十阶段和CPU竞争已过；前20条240任务最终重新核对原始输出后通过。

- `e139bundle/runs/p80_d2_batch20_02/p80_batch20`。
- summary SHA `36953e487c757a9980c4ac33760b7a8f65c6f61209e6b2582a8342b582d7e687`。
- 240任务、6,082,560输出及total、零失败。
- 批量均值77,545.15833333334周期，最小73,695，最大87,111；宿主1911.5024437289685秒。批量均值不能代替固定12性能均值。
- 精确本地摘要`handoff/team/evidence/P80_ASIC240_COMPLETE_20261116.json`。新FLOAT20连接仍未执行。
- 原142包三深度2/4/8各14例均已通过，每版354816输出；固定12均值77,545.3333333周期、1934.352378824 task/s（150MHz折算）。最小深度2暂选，PPA资格未通过。不要重跑这些14或240。

## 新失败及空间

- 06:19:20原综合等待47889在mkdir原共享锁时遇`ENOSPC`，**尚未进入综合02**。原选择记录与日志保留，不能当驱动库修复失败。
- 原67274 followup于06:19:28因前驱失败退出；原69883 export于06:19:41正确停止。06:26:03确认42584/47889/67274/69883全部不存在，原锁不存在，本账号没有EDA。
- 更早综合01是驱动库限定符错误，146错误/exit0被拒，旧mapped不复用；7430已修工具但实际重测仍待。
- 06:16共享盘剩1,048,576B，tmp剩90,484,076,544B；共享空间不够创建锁，而新结果本身都写在tmp。

cache09仅处理已核验的**旧B0 gate02普通编译缓存**，与旧八路及T80桌面无关：

- 由已固定SHA的`root/b0_cache_candidates01.json`索引3取路径，不手写长目录。
- bundle为`light-light126-systolic-b-v3-20261112_114355-ced0e139a01e`，运行`systolic_b_v3_drc06_gate02/systolic_b_gate/csrc`；38普通文件、65,967,651B。
- 06:26:03确认对应门级14通过，无SDF，原日志/输入/结果/可执行文件保留。
- 先在tmp压缩、全量逐成员SHA和字节数回读；再次核对无人使用/文件身份后仅移除重复普通缓存，再持久复制压缩文件回原stage，核对源结果全部不变。用户此前授权清理已验证且不用的大文件；不删除验证证据。
- 新tmp归档`b0_gate02_csrc_20261116.tar.gz`及`.receipt.json`；持久`STAGE/csrc_regular_files_20261116_p80.tar.gz`。**尚未观察完成**。之前四份N1/B0缓存归档均已做过，不重复。

## 新单锁接续设计（已本地演练，实际未观察）

`P80_FINAL_COMBINED02_20261116.py` SHA `f9566e5f768ddd6977022a835a7e3f5e899d9a8600a4ce90c7645efb4ab0b21a`。

- 新包仍用已冻结4cf，未修改它。重新核验三个深度原14、自己的恢复/竞争/240、FLOAT与私有NumPy、原失败队列退出和空间。
- **只获取一次原共享锁**，统一ProcessLedger，先在`4cfbundle/runs/p80_synth_d2_03/p80_synth`执行全新三块综合；沿用7430驱动限定符修复及已验证S0接口环境，不能复用失败map。
- 父队列`4cfbundle/runs/p80_finish02`；综合注册为同一锁的独立兄弟stage。映射完成立即打印实际面积/setup/hold；≤1.00mm²且setup/hold通过后，自己的FLOAT连接及17项最终网表检查/门级14/SAIF12/PT12接续，仍持同一锁，不再反复建锁。
- 新control`root/p80_final_combined02.json`及`.launcher.log`。综合不放进18项最终stage列表，单独绑定`synthesis`，后续报告和归档可核对。
- 本地3项映射成功/失败/面积拒绝演练通过；没有额外获取/释放锁，不因映射工具exit0就提前通过时序/面积。
- 继续复用原helper的`precision_stage`，旧helper SHA `e25435bf74ff0a582a0956a6e1892a65163999af8dffbc177e501b2f83d257e7`；只调用函数，不重启旧main。

`P80_EXPORT_REVIEW02_20261116.py` SHA `2e15053973fdd32b07e621f1a7d33ee321eaf5ff7e526561d79f3e298b9b269b`：当前传输只部署。后续确认combined02运行后再独立启动；等待它成功自然释放锁，才导出`p80_report02`、`p80_unknown_inventory02`及`p80_unknown_connections02`和模型事实连接。固定14 bundle已在combined request注册，不能重复添加。

`P80_B0_GATE02_CACHE_RECOVERY09_20261116.py` SHA `1bc5403557f268892cc6b8ddadcbdb64e29cd53d84757da809869113f12c65e9`；其自身不会启动EDA。当前外层35行仅在其returncode0后启动combined02。

## 冻结包和精度身份

P80根`/tmp/s4_21usr_p80_20261116_0315`，bundle前缀`light-light126-p80-`：

| 包 | manifest SHA | 用途 |
|---|---|---|
|142fae2|7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc|三深度真实14|
|e139032|c5429439f979357154736a30a2024a8c84fd615b545a2d8974b7ead52ecc52c8|默认d2、自己的恢复/竞争/240已通过|
|7430bb6|f3406e930f048a73f344736f8b10c2c91651a4b1f43ad3e9b79ebdf785e5ad1a|综合工具修复；02建锁ENOSPC未启EDA|
|4cf35b6|b8981502f271542300ec6139553be939bffb0d7f14c2cd00d0fda616ba59c6d1|944文件，全部核验；当前03映射及最终工具包|

实际硬件实现142fae28545759e33fa38de514eabf752cb8c43a，后续包RTL及d2固件逐字节一致；新网表仍必须自身验收。其他历史包身份在旧P80_BATCH20/SYNTH_STARTED检查点。

- FLOAT：`/tmp/s4_21usr_n1_20261113_0210/n1_precision_inputs_20261113_0840/n1-recovered-float100-20261113.zip`，143258826B，SHA `5df11251821d2d36e85e07c8a171195d9d2ed2d4084a979519d23f6df7d683e2`。exact_original_npz_members，原edb容器未取得，不混淆。
- NumPy1.19.5：`/tmp/s4_21usr_n1_20261113_0210/n1_numpy1195_20261113_0905`，receipt SHA `c1fe14065d6919ff337f2cbf53551f94941acc35d04d3cadabca311fe742eacd`。显式sys.path，OPENBLAS/OMP=1，不改系统Python。
- 数据原`Desktop/IC/hex_short_all`，仅前20。SAIF方法qualification沿用原R4方法回执a0a9bc62…62d26，只复用方法，不复用硬件PASS，详细路径见旧检查点/helper常量。

## 本地工具及后续

- 当前分支`codex/light-light126/t80-pipeline-c32-g32-20261115`。最新本地1e4f0bf，最近push307baf5；14c6dab新增只复制P80归档工具尚未部署。`p80_archive_contract.py`/`p80_archive_runtime.py`及测试：P80/S0共4项通过，要求18项全部结束/同网表报告/同精度；不删除源。归档还需要实际共享空间，不能先宣称完成。
- 下一步收96487、看cache09回执及combined02 PID/状态。失败先定位，不覆盖目录。成功后部署已传好的export02等待入口，继续观察新综合；完成P80自己的PPA/审核/持久备份后再进C80。
- 原失败/停止记录全部保留，S0不重跑、旧100条不重跑。没有本地XSim或其他EDA在跑。唯一旧未跟踪`S0_SYNTH05_FINISH_LAUNCH_20261115.py`不提交、不执行。
- Python使用`E:/fpga_race-two/.venv-kwt/Scripts/python.exe`；默认WindowsApps别名不可用。板端现有`F:/linux_fpga_try/ac820.ps1`可见VNC输入，每行≤1000 ASCII，既有速度不改，禁止并发键入。
