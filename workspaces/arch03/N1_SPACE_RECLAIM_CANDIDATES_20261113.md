# N1空间紧急补充：仅旧非R4/B0编译中间物候选

2026-11-13 02:05，本地历史证据核对。根代理最近报告共享可用空间由10.9GB降至约6GB，R4 L01低优先级单worker压缩仍进行；本文没有远端操作，不将该最后观察当实时空间。

结论：目前本地**没有可证明仍存在且有确定可释放字节数的额外大文件**。六批旧VCD和8,745,588,450B旧gateprobe波形均已删除，不再计入候选。R4/B0、当前N1及其源码、网表、日志、输出、输入哈希不动。现有R4 L01的归档/验证由原作业继续，不创建第二作业。

最小下一步是对以下6个已知旧运行目录，只读检查其`csrc`编译中间目录。目录及历史身份由已有清理回执确认；`csrc`是否存在、大小和是否含运行依赖**尚未确认**。VCS命令在各run执行，源码中没有指定`-Mdir`，因此这是生成中间物的候选位置，而不是已核验删除目标。

路径均相对：
`/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/bundles/`

| 优先级 | 精确旧运行目录（后接`/csrc`检查） | 已知历史依据 |
|---|---|---|
| 1 | `light-light126-gateprobe-dma16-20261109_235343-51bc8d1fc7cb/runs/dma16_gate02/dma16_gate` | 旧source-width活动失败，25344功能输出独立重核；其raw已在01:25删除，日志/输出保留 |
| 2 | `light-light126-vcd-bits-dma16-20261110_003213-a53e4186a13a/runs/dma16_gate03/dma16_gate` | 旧16DMA gate14/活动通过；12个旧raw已第五批删除，summary `9ba06d90...` |
| 3 | `light-light126-mmio-timing-dma16-20261110_111311-ecf3cd4afb3c/runs/mmio8_source_gate_full01/mmio8_gate` | 原8路完整门级通过；12个旧raw已前三批删除，summary `06e388e1...` |
| 4 | `light-light126-power-sumchain-dma16-20261110_081342-a2e2bc682696/runs/mmio8_source_gate01/mmio8_gate` | 原8路首层通过；raw第四批删除，summary `b1321614...` |
| 5 | `light-light126-d3-portcheck-arch03-20261109_110751-5946c5426386/runs/d3_gate07_h0/gate_soc` | 旧D3首层通过；raw第四批删除，summary `4e735f46...` |
| 6 | `light-light126-d3-reports-arch03-20261109_071327-4c8803e509a0/runs/d3_activity01/gate_soc` | 原活动缺summary，但d3_activity02独立完整重审通过；raw第六批删除，两边证据仍保留 |

证据来源为`handoff/team/evidence/N1_SERVER_SPACE_RECOVERY_20261113.json`和`SERVER_WAVE_CLEANUP_{FIRST/SECOND/THIRD/FOURTH/FIFTH/SIXTH}`系列（第一份实际名`SERVER_WAVE_CLEANUP_20261112.json`）；门级生成命令见`scripts/dma16_gate.py`和`gate_soc.py`。

## 只读检查及保留边界

1. 对6个精确路径resolve，确认属于自己的bundles、不是符号链接，且路径不含R4/B0/N1；检查实际compile_command.json或compile.log的工作目录与编译输出。仅对存在的`csrc`做`du -s -B1 -- <绝对路径>`，不递归扫描全部bundles。
2. 若某目录足够大，读取该目录直接子文件名、大小、owner、mtime，分别统计`.o`、`.a`、生成C/头文件和`.so`。`.o/.a`只是优先核验的编译中间物候选，不凭后缀自动删除。
3. 保留`simv`、`simv.daidir`及`.so`运行依赖；不可盲删整个csrc。先检查原编译/链接命令、source_inputs.json、运行合同/制品清单是否引用候选，及进程/fuser/打开句柄。若与受测输入、当前作业或共享动态库有关，排除。
4. 真正清理前形成逐文件精确清单及字节数、哈希/归属和复现影响，保留所有源码、网表、日志、结果、固件、模型和原哈希记录。编译中间缓存没有替代历史输出证据，但仍需明确以后增量编译须重建。

本地尚未读取这6个远端csrc，**不能承诺能回收多少空间，也没有删除清单或删除动作**。若检查后它们很小，应如实停止此方向，不能为凑空间转而删除R4/B0资料。

## 已排除的方向

- 旧DMA16 1200任务不是每任务复制一套boot。`dma16_soc.py`先生成`boot_shift_%02d`，batch按SHIFT共用；删boot既不能据此预期数GB，又破坏冻结输入，故不建议。
- `source_inputs.json`和实际运行合同会引用simv、boot、平台/模型；这些不能当普通缓存无条件删除。
- 旧B失败synth01整目录历史观测仅257MiB，而且属于被保护B谱系，不纳入本次候选。
- 已压缩R4大波形、正在生成的R4 L01压缩临时文件、B0备份目录和归档都不纳入额外回收。
- 所有旧VCD清理已完成记录均为历史，不能重复统计其原始数百GB体积。

根代理可利用上述有限名单继续读取；本代理未使用VNC/FileZilla、未启动作业、未改冻结工具、未删文件、未提交Git。

## 根代理实际检查后的结论（覆盖上方候选待查状态）

根代理随后完成固定层级非B0/R4的csrc目录只读du：前14项大多仅约9MB，回收价值低，因此**不清理、不实现额外cleanup、不再重复搜索这些路径**。此处仅转述根代理实查，不伪造各文件精确字节数。原R4 L01归档约2GB临时文件、可用约6GB是该消息的最后观察，继续保留2GiB保护阈值；受保护的R4既有gzip不删。

这条编译缓存路径已探索并关闭。根代理将另查自己IC层级的空间统计，本代理停止此项搜索，未发现确定可回收的额外大文件。
