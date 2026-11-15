# P80受测身份、运行入口与接续

本说明针对当前S1 P80，更新于2026年11月16日。阶段尚未冻结：自己的ASIC RTL/E203功能证据已完成，新网表综合及后继验收仍在原队列中。实时状态以根交接、最新检查点及服务器原始回执为准，本文不授权重复启动。

## 固定配置

- 硬件源码：`142fae28545759e33fa38de514eabf752cb8c43a`。
- 暂选事务元信息队列深度2；深度2/4/8各自十四例通过，固定12完整周期完全相同。最终选择仍须满足本版面积及时序。
- 五行×16列、80 PE；X14/W12、累加和偏置32位、total33位、SHIFT10；布局`0x00100004`。
- 原32位ICB、原平台缓冲/在途参数；源额度3，源/读回FIFO各16、输出FIFO32、原描述符队列8不变。
- 输入执行真实源读、共享写成功ACK、原总线读回后才解码。完成等待输出写ACK和全部事务排空。
- SS、0.99V、125°C、6.666666ns及原负载；项目面积按保守口径≤1.00mm²。
- 正式批量仅前20条、240任务；固定12性能组单独统计。桌面T80交付和全部旧八路数据保持原样。

## 当前服务器目录与身份

以下相对路径均位于`/tmp/s4_21usr_p80_20261116_0315`，该目录是当前运行位置，不冒充持久交付归档。

| 包或结果 | 相对位置 | 身份/用途 |
|---|---|---|
| 三深度固定十四例包 | `light-light126-p80-142fae2` | manifest SHA `7017da04075aea98b7a9dfe414e41621d3974fb43709d542d42ac6b0f43920fc` |
| 深度2功能包 | `light-light126-p80-e139032` | manifest SHA `c5429439f979357154736a30a2024a8c84fd615b545a2d8974b7ead52ecc52c8` |
| 新综合及后继工具包 | `light-light126-p80-1023646` | manifest SHA `402c08165610ed18bdd772cddd3d527570fd62bdaa6ff820e0ad19b5d7082bcd`；947文件 |
| 固定深度2十四例 | `light-light126-p80-142fae2/runs/p80_fixed_d2_05/p80_soc` | 已完成；summary SHA `43e9ec58048d24ab8ab7d505723f7360b1e7e1e6eeaf5d76c81134cef34222c8` |
| 深度2恢复 | `light-light126-p80-e139032/runs/p80_d2_sequence_02/p80_sequence` | 十阶段、无复位交替、真实CPU恢复 |
| 深度2竞争 | `light-light126-p80-e139032/runs/p80_d2_contention_02/p80_contention` | 真实CPU与DMA共享存储竞争 |
| 深度2批量 | `light-light126-p80-e139032/runs/p80_d2_batch20_02/p80_batch20` | 240任务、6,082,560输出及total零差异；summary SHA `36953e487c757a9980c4ac33760b7a8f65c6f61209e6b2582a8342b582d7e687` |
| 当前新综合 | `light-light126-p80-1023646/runs/p80_synth_d2_06/p80_synth` | 全新链接及三个块映射；没有复用旧硬件DDC |
| 当前正式后继队列 | `light-light126-p80-1023646/runs/p80_finish05/state.json` | 精度连接＋17项最终网表检查；成功结束不自动等于独立验收 |
| 当前报告收集状态 | `p80_export_review05/state.json` | 等待上述队列自然成功退出，再收集自己的报告和模型事实 |

1023646是工具提交，不是新的RTL功能提交。它修复DC导出的`set_local_link_library`旧路径歧义：旧/新标准DB同名且完整SHA相同才统一路径，其余边界时序预算不变。共享块已实际映射通过，不能据此提前授予整机时序通过。

## 入口及使用顺序

先阅读根`AGENTS.md`、`CONTEXT_HANDOFF.md`和`CONTEXT_CHECKPOINT_20261116_P80_LIBRARY_FIX.md`。检查原队列、PID、协作锁及空间；已有作业继续原入口，不重新运行本说明中的验证入口。所有新尝试必须使用独立session，原失败目录保留。

| 本地/服务器入口 | 用途与必要输入 |
|---|---|
| `scripts/build_p80_firmware.py` | 按指定深度构建任务固件，记录源码/配置哈希；恢复及竞争分别用`build_p80_sequence.py`、`build_p80_contention.py` |
| `scripts/make_p80_overlay.py` | 从已提交源码及已核验五套固件生成传输资料；该原始入口默认构建深度4主包，不能误用它替代当前深度2快照 |
| `scripts/p80_prepare_bundle.py` | 在新的私有目录，从固定S0输入＋核验overlay生成新包；核验前后源身份，不修改原包 |
| `scripts/p80_server.py` | `soc/build/sequence/contention/batch20/status`；显式指定runtime root和manifest，批量还需dataset，必要时指定固件目录 |
| `scripts/p80_eda_server.py` | `synth/gate/structure/timing_audit/drc_audit/saif/power/precision/status`；每阶段显式绑定前置run及SHA，不继承旧网表PASS |
| `scripts/p80_finish.py` | 对已完成且核验的新综合统一持原协作锁，执行结构、gate14、SAIF12、时序/DRC及逐层PT；不能用它重开当前combined05 |
| `scripts/p80_report.py` | 从自己的不可变回执导出JSON、CSV及中文报告，精度/完整12功耗缺项不得填零 |
| `scripts/p80_model_review_snapshot.py` | 连接同网表时序、未知活动及库模型事实，保留人工独立结论边界 |
| `scripts/p80_archive_runtime.py` | 完成后的复制归档、逐成员回读核验；不删除源，空间不足保持未归档 |

当前combined05实际控制器为`handoff/team/evidence/P80_FINAL_COMBINED05_20261116.py`，服务器副本位于根运行目录。它固定已有输入身份及独立运行目录，不是可任意改路径复用的通用批处理入口。`P80_PRECISION_HELPER02_20261116.py`只导入`precision_stage`及已核验常量；其继承的旧`main`不是当前接续入口，不直接执行。

只读查看当前队列可使用已部署入口（不启动EDA）：

```bash
python3 -B /tmp/s4_21usr_p80_20261116_0315/light-light126-p80-1023646/workspaces/arch03/scripts/p80_eda_server.py status \
  --session p80_finish05 \
  --runtime-root /tmp/s4_21usr_p80_20261116_0315 \
  --runtime-manifest-sha256 402c08165610ed18bdd772cddd3d527570fd62bdaa6ff820e0ad19b5d7082bcd
```

## 验收与数据边界

每个输出按`row*256+column`核对total/result/saturated与完整共享SRAM结果。ASIC RTL检查内部signed33 total；无SDF门级检查真实坐标/result/saturated和总线/IRQ，不能伪造被综合优化掉的内部total可观察性。

固定12平均77,545.3333333周期，按150MHz折算1934.3523788task/s；240平均77,545.1583333周期。功耗必须使用同一最终网表的12个完整窗口，按总能量/总时长计算平均功耗、总能量/12计算J/task。

浮点连接使用已核验完整NPZ成员的恢复容器，不能声称得到原始ZIP容器哈希。PR数据目录`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all`只取前20条；不能把内部精度称为官方600条验收。

新网表的面积、时序、门级、活动、功耗、模型审核和持久归档尚待当前队列完成。全部阶段报告/冻结完成后才进入C80；本说明本身不授予验收，也未修改任何受测包。
