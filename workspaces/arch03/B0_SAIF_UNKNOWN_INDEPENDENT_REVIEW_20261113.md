# B0 SAIF未知清单工具独立只读审查

2026-11-13。审查对象为`b0_saif_unknown_inventory.py`及其实际调用的`native_saif_activity.py`、`saif_syntax.py`、`dma16_unknown_netlist.py`和`dma16_structural_audit.py`。本次没有修改这些文件，没有重复测试，没有扫描服务器SAIF，也没有启动EDA。原N1综合由根代理继续管理。

本轮审查最终看到的工具SHA256为`c57ed783754a6411bc3d43139dcf90a420d7c5a2f87ca050b12b98e75b20056d`。负责实现的代理报告15项本地检查通过；本审查没有把该消息或合成夹具当作真实B0活动/功耗验收。

## 结论与已纠正范围

未发现当前版本会把连接未知自动豁免为零影响。所有记录均`is_no_load_waiver=false`；全局alias连接、未知功耗影响和系统功耗审核保持false。

本次指出的范围问题是：原工具仅统计COND/IOPATH子记录数，未展开其中驻留内容；顶层TX/TZ为0但子条件含未知时，不会进入顶层unknown JSONL。实现代理已修正标记：`top_level_unknown_declarations_listed=true`，但存在条件子记录时`full_unknown_declarations_listed=false`、总状态为`top_level_unknown_inventory_conditional_expansion_required`。实际没有条件子记录时才声明顶层未知清单完整。未改变原native统计等式或伪造条件内容。

## 完整性与保守分类

- 原SAIF一边流式解析一边计算SHA，完成后要求字节数、时间单位、完整窗口、所有统计、各组件统计/原前12例名、模块路径、106个SysMem位及SHA组成的整个activity对象与原冻结回执完全相等。每个顶层TX+TZ>0声明都emit一次，并要求分类计数总和等于原unknown_declarations。
- 每条记录保留声明ordinal、完整SAIF名称、PORT/NET位置、T0/T1、原TX/TZ语义、TC/IG、全窗口未知和条件记录数。VCS缺单独TZ时继续标为合并X或Z，不能把占位0读成“已知Z为0”。
- SAIF统计是声明数量，可能包括同一物理网的端口/别名；组件计数也交叠。工具没有把这些数字改称独立未知网络数量或功耗误差比例。
- 实际mapped模块中局部没有表达式使用的位，被改标为`mapped_local_declaration_only_global_alias_review_required`。模块端口可在父层仍有别名/负载，这个分类没有授予无负载豁免。
- 存在表达式使用的位保持`mapped_expression_requires_time_review`。该计数也包括赋值左侧等保守使用，因此不能由数量推算实际电容或功耗，但不会因此漏掉待审连接。
- 外部标准单元/SRAM层级统一为`external_cell_port_or_model_internal_requires_review`。没有查真实Liberty pin清单前，Q/D/CEN等cell端口与模型私有变量不能区分，不能按名称自动排除。
- 未解析层级/信号保持明确review状态。向量位先检查是否存在完全同名的转义scalar，再把`data[n]`转成向量选择；防止把真实名为`data[31]`的scalar误归到另一个向量。
- 映射parser对结构声明/实例、未知格式和递归/歧义层次采取失败或待审方式。层次通过点拼接，若转义实例名与真实层次发生同名冲突会被歧义检查拒绝，而不是静默选择一个。

这些属性支持“原活动完整未知声明清单的收集与保守分类”，不支持物理功耗上下界或全局零负载结论。未知发生与valid/CEN的时间关系仍不在SAIF累计统计中。

## L01实际结果出来后的最小查询

1. 先读取新L01 JSON而非重扫整份SAIF：核原activity对象、SAIF SHA、mapped.v SHA、窗口、`unknown_rows`、分类计数总和、条件记录数、`full_unknown_declarations_listed`和输出gzip SHA。历史曾观察41406个未知声明，只作核对线索；必须以本次绑定原回执为准，不硬改计数。
2. 用新小型JSONL.gz输出取得所有分类计数，并各选少量具体对象：局部declaration-only、mapped expression、外部cell/model、unresolved。选样只用于确定下一种解析方法，不能据此关闭同类别剩余对象。JSONL完整清单保留，不能只带回前12项。
3. 先看已有`watched_committed_path`：实际`committed_data[31:0]`、valid和ready的驻留/未知及映射分类。检查有哪些实际声明、是否有PORT/NET重复、哪些位尚未匹配。即使valid本身全已知，不能从累计驻留推出数据X与valid=0同时发生。
4. 通过现有原B0 DRC06 mapped.v，只读列出上述实际信号所在模块的赋值别名、父子端口连接和消费者；对局部未用端口继续追到上层实际连接，不将零局部表达式数直接变为零叶负载。先使用Python/文本查询，不占用第二个EDA会话。
5. 对外部宏/标准单元未知，先用已经绑定的Liberty/model pin信息区分库pin与模型私有变量；尤其检查CLK/CEN/GWEN/WEN/RET1N及数据/地址是否包含在实际功耗条件中。名字看起来像内部变量也必须绑定具体ref和pin证据。
6. 只有少量连接仍无法解释时，再由根代理等原综合和协作锁释放后安排一次具名只读DDC/PT连接查询。不得与当前N1综合并发启动第二个EDA，也不重跑B0门级、1200或功耗12层来替代静态连接问题。

如果L01发现非零条件子记录、未识别名称或未知控制条件，先保留该明确缺口；是否展开条件或增加最小逐周期knownness观察由根代理根据实际证据决定。本工具的完成状态不批准N1相对B0的功耗准入，也不触发N2开发。
