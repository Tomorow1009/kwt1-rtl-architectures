# 12层功耗活动来源审核

09:05更新：db8包经672输入/197干净tests及FileZilla上传，08:55:22.524544解包。实际首轮审核被“Unreviewed activity-source columns”守卫拒绝，未生成通过输出；`runs/annotation_all12_v1_failure.json`保留诊断。逐字符比较发现首表头完全一致，真实文件另有静态概率来源表，二者共2个同名表头，4个“Nets ”开头行中包含2个“Nets Driven by”类别标题。首版误将整文件视作单表。

修正分别识别具名的Switching Activity和Static Probability两张总览，逐表严格核对列名/顺序/10列总计，排除精确的“Nets Driven by”标题；两表的默认、传播及未标注等来源均不能自动通过。新增真实双表格式、缺表/错表、静态概率不同来源拒绝测试，9项新工具测试＋数值/报告共33项通过；**修正版尚未打包或服务器执行**。不更改生产RTL、固件、原始功耗报告或波形，不把首轮拒绝改成通过。

`scripts/dma16_power_activity_review.py`读取已完成full02的同一请求，对12份实际报告分别复核全部工件哈希、数值、单位、普通/verbose一致、模块、162宏和窗口，再审核：

- 实际设置是averaged、X跃迁系数0.5、initial-X=false；其他设置不得混入冻结生产汇总。
- 活动来源表的完整10列及总数一致，exact/implied之外的来源不能自动通过。
- before/after均包含明确的空未标注对象清单，不能按文件存在或只看首层推断。
- 同一冻结综合、门级和固件身份，完整12层且无重复；额外告警代码必须审核。
- 每层未知记录、原始活动哈希和告警出现位置全部保留。

运行方式：

```text
python3 workspaces/arch03/scripts/dma16_power_activity_review.py --request <a2的runs/dma16_report_full02/request.json> --output <新运行目录/annotation.json>
```

该检查只读小型报告，不启动EDA或重扫大波形；可在服务器既有重任务期间执行。结果仍为`system_power_verified=false`。精确映射不代表未知值无影响，toggle激励比例也不是映射覆盖率。

后续仍须审查未知对象的有效使用时段和初始状态，以及X建模敏感性。敏感性诊断尚未实现，不能宣称已有误差界。工艺/负载、宏模型、无寄生/理想时钟边界沿用原报告，不能选择不同设置的最小功耗作为正式成绩。
