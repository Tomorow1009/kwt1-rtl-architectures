# N1综合初步证据：2026-11-13 04:20

**N1原综合已结束并生成报告，尚未完成严格时序、结构及完整阶段验收。**
本记录只保存已观察结果，不修改总状态、根检查点或运行队列，也不据此进入N2。

配套机器记录为`handoff/team/evidence/N1_SYNTH_PRELIMINARY_20261113_0420.json`。
本代理已亲读`E:/fpga_race-two/takeover_local/n1_metrics_short_0421.png`；截图服务器时钟为
04:20:38，SHA-256为`e147a53ae4d6c157614ebf7fd5586eab36b3c7db95fe7925dc4c92ee4627e08b`。
原始综合summary未为本记录下载，正式审核仍以原服务器报告及其哈希为准。

## 受测身份与已生成结果

- 源提交：`9305c6948c764fed01fe86b20bb3db94170299ab`。
- 原driver PID 169157、DC PID 174746已结束；根代理读取的终态时间为
  `2026-11-13T04:15:04.006067`，保留服务器原显示时间。
- 运行目录：`/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-v4-20261113_013211-9305c6948c76/runs/n1_synth01/n1_synth`。
- summary SHA-256：`cc7f26115f3158fb69f4575f28b5dfde4dd8e5b3aeefda2a927928ad8418db31`。

| 项目 | 观察值 | 范围 |
|---|---:|---|
| HF周期 | 6.666666000000 ns | 对应声明的150 MHz约束 |
| LF周期 | 66 ns | 原平台低频域 |
| RAMSP128X16 | 92 | 实际报告总数 |
| RAMSP4096X16 | 128 | 实际报告总数，合计220个宏 |
| max路径最差slack | +0.0000510216 ns | 综合初步max报告，2个path groups |
| min路径最差slack | +0.00153732 ns | 综合初步min报告，2个path groups |
| latch数量 | 0 | 根代理另确认latch_inventory为0字节 |
| 整机面积 | 4,473,365.187497 µm²，即4.473365187497 mm² | 包含复用模块，不直接套用新增项目面积限额 |
| 项目保守预算面积 | 0.9511486879005002 mm² | 数值低于1.20 mm²；最终归属审核尚未完成 |

截图包含`constraints.rpt`的完整结论：`This design has no violated constraints.`
根代理另外确认最终映射loop check实际存在，未报告组合环。这些是积极的初步结果，但正slack、
零latch和该结论不能替代源锥、约束覆盖、例外及工具warning的完整审阅。

当前N1综合脚本的保守面积规则是“全部SoC标准单元＋加速器内部SRAM”，只排除64个共享SRAM
和64个TCM复用宏；该统计与整机面积分开记录。库单位及归属证据仍须在本次冻结配置下审核，
不将初步预算直接标为官方面积验收。

## 后续作业的最后观察

根代理记录：41b OPS的`n1_structure01`于04:21:37以唯一新作业PID 268159启动，随后因
手工抄录的BASE manifest SHA只有62字符，在configure前被身份检查拒绝，没有创建session
或团队锁。01 driver日志保留；这是启动参数错误，不是硬件或结构验证失败。

正确BASE manifest SHA为`73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d`。
后续`n1_structure02`（PID 269558）于04:25:31在创建原共享团队锁时遇到
`Errno 28: No space left on device`，进程已退。根代理确认NO_STATE、锁不存在、没有启动EDA，
输入未改变；这是共享空间阻塞，不能记为硬件或结构检查失败，结构验证仍待完成。

根代理随后按既有清理授权处理一份已解包的重复上传ZIP，不动R4/B0归档。本记录代理已核对
本地OPS41b保留包：8,891,173字节，实际SHA为
`17d2e972e0452daf70505a69613423979bc0f1c9f10a50d6fc6ba676dc0a65e3`；包内manifest SHA为
`0837b78df4867df055ecf4f115bcd2b8ec58d1e48acf698850de8c9eed58f64e`，与原OPS身份一致。
首次`fuser --`调用返回用法错误，空stderr守卫阻止继续；未复制或删除。修正调用后先复制到
私有/tmp，核完整SHA；删除前再次核两份ZIP的大小/SHA、fuser无占用，并fsync保留副本。
04:29:29.203111仅删除共享盘这一重复ZIP；本地ZIP、/tmp保留副本及解包目录仍在。
观察到共享盘free_after=1,558,183,936字节，不能把该总可用空间全部归因于8.89MB的清理。
独立回执见`handoff/team/evidence/N1_DUPLICATE_OPS_ZIP_CLEANUP_20261113_0429.json`。

`n1_structure03`于04:30:51.383600启动，PID 274281，04:31:04.708340完成。截图
`n1_structure03_status_0432.png`显示服务器stage状态passed、锁已释放，summary SHA为
`95a3bde42e44fe1aabcbb0b450a683acbfc3d5b298a423b4607daab0a7158652`。
这里只确认阶段报告生成完成；内部warning、位宽/source-cone及严格条件仍须根代理阅读，
不把stage状态直接转为完整结构或时序验收。

04:32:28唯一新作业`n1_batch100_01`以PID 275224启动，见`n1_batch100_launch_0432.png`。
本记录尚未读取真实编译状态或任务进度，不推断任何任务已经通过。本记录代理没有操作
服务器、删除文件或另启任务；上述增量来自亲读截图及根代理回传。

## 仍待完成

严格时序、source-cone/结构及check_timing/check_design warning审阅仍待完成；N1自有1200任务、
同网表门级14例、完整活动12层和系统功耗也仍待完成。完整100条浮点源缺口另见
`docs/data/x14-w12-b32/N1_FLOAT_SOURCE_SEARCH_20261113.md`，不因本次综合结束而解除。

本记录不补写吞吐、功耗或能耗数值，也不借用B0结果。阶段交接继续保持未获准；/tmp原始
运行产物还需最终持久化归档，不能将临时磁盘视为长期交付地点。
