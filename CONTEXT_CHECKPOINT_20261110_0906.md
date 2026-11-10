# 2026-11-10 09:06 接续检查点

**09:28最新：** 已重新读取AGENTS、计划和状态。实际未标注格式截图`takeover_local/d2_20261109/unannotated_exact_schema.png`核对完成；第三版解析修正与35相关测试通过，待提交/干净包/上传/真实annotation_all12_v3。要求自身两表均零未标注且file/implied覆盖、10列和总数严格一致，再接受独立行1或空尾部；保存标记，不删除原报告。新增加错设计大小与对象名1/非零数量反例。原8路gate46140/scan55423于09:25:37.990186仍running并持锁，不启动新重任务。fd54包已上传核验，三份JSON正在同步纠正旧状态。

**09:20最新，覆盖09:12传输中：** fd54修正版33相关tests/198干净tests包已FileZilla33秒上传成功并断开，09:14:59.391512安全解包，672输入核验通过。真实annotation_all12_v2通过双表解析后，在`empty_unannotated`因清单尾部非空被拒绝，没有通过输出；新诊断保存fd54 `runs/annotation_all12_v2_failure.json`。已只读核对全部24份before/after报告：均有两张统计表、每表零未标注，清单后均为独立行`1`，不是任意文字；需要把“空清单”的判定绑定其自身两张表零未标注计数，并单独保留这个已观察尾部标记。未标注报告不带include_mapping_types，列标题还打印两次SSA Force，须原样校验并分别要求对应值零，不猜语义。正在准备第三版修正，**尚未修改/测试/打包该尾部处理**，不能把第二次失败当PASS。服务器原8路重作业不变，最近09:09仍scan55423；先查当前状态再排任何重任务。FileZilla已断开，VNC第三页空闲，本地无挂起测试/上传会话。

**09:12增量优先：** 双表修正已提交并推送`fd54fd14267df093a991e9e07685462b6b414c44`，ls-remote独立确认。新包`light-light126-annotation-tables-dma16-20261110_090821-fd54fd14267d.zip`，16632892B，SHA=`d56631e998cfaf6ed34803d36e17ef4deaeca0f1789da7021760750c0cc566ce`；672输入/198干净tests/5固件/40生产不变。audit=`local_runs/dma16_annotation_tables_clean_audit_20261110_0910/receipt.json`，SHA=`a42ed561a50ffcecd110cee3ca2179ea75d80bcad222ac842b236f33ef7a9895`。已暂存板端`/home/root/undergrad-annotation-tables-20261110`并核对SHA，**FileZilla上传刚启动，尚未看到成功**；下一步先确认成功再解包/输入核验/运行新annotation_all12_v2。下文“修正版未提交/打包”仅为09:06历史状态。本地测试会话48068已结束。

原8路门级09:09:16.781222仍driver46140/child55423扫描layer_01_activity_scan.log，VCD30231391361B中读到12807816195B；首层功能25344输出/3843121周期通过，阶段尚未完成。只读查询终端空闲，不重复启动重作业。下一步其他未完成项保持。

用户要求继续实施三天直接16路MAC＋ICB DMA＋双缓冲计划；最新暂停已解除，开发板上电，FileZilla允许。本次及后续同范围源码/交接/小型证据向私人`Tomorow1009/kwt1-rtl-architectures`、分支`codex/light-light126/undergrad-d1-numerics`同步均已获明确授权；不重复询问，不改main。

压缩后先读AGENTS.md、`workspaces/arch03/IMPLEMENTATION_PLAN_DMA16_20261109.md`、本文件、根CONTEXT_HANDOFF与三份JSON状态。H28=11月10日21:16:08；H72=11月12日17:16:08；用户截止11月13日晚。不要把当前诊断改成新架构优化。

## 已完成

- 生产仍为fcd445f配置，ASIC/E20314、真实恢复/竞争、同网表门级14及完整活动12通过；每任务225770周期，标称150MHz换算664.392966task/s。生产RTL、正式IRQ固件和668最终批量runner/parser保持冻结。
- 668 `runs/dma16_final1200_v2`于06:22:56.909362完成1200任务/30412800输出/0失败。
- a2 `runs/dma16_report_full02`于08:38:53.904490成功，**全部1200回执再次独立重审**，12层原始功耗数值及统一JSON/CSV/中文报告已生成；08:41:17核对全部输出哈希，08:43:30独立确认receipt SHA `06c246af4de0914e1e304fc77cf1b61413e955a350c59d5d8d0df8c521e84e5c`。
- full02目录为`light-light126-power-sumchain-dma16-20261110_081342-a2e2bc682696/runs/dma16_report_full02/output`。请求SHA `a6f483701cff4fac27f03a11c8cc0f63b59bb318898991448826f938f860b105`独立确认。时序与0.434796781612mm²项目面积上界审定已绑定；系统功耗/官方精度/物理签核仍false。
- 12层实际数字提取a2 `runs/power_numbers_all12_sumchain01/numbers.json` SHA `06c867453c7225537188a8d32b815b4947383f4a05339210a3bb2c665126e17e`已独立确认。L06独立舍入的和校验已用11项原严格检查的可推导三角不等式界修正，未放宽任意相对容差；旧full01失败保留。
- 原8路MMIO同源新综合1aa `runs/mmio8_source_synth01/mmio8_synth`于08:30:15.335643完成；SHA `0e33c1d045d063829c34e97b7ba10109d446c381c95fa7003449d0bbc6159fc9`独立确认。6.666666ns，setup +0.00000905991ns、hold +0.00131008ns、0latch，130大/8小宏；保守预算0.2921861914119108mm²。约束审核未完成，不是8路DMA。
- GitHub最后独立确认`db8e2719b2a6030208925a8dc99856e20adb711c`；后续双表解析修正及文档更新尚未提交。

## 当前唯一重作业

a2 `runs/mmio8_source_gate01/mmio8_gate`，driver **46140**，launcher08:42:24.188768、stage08:42:24.710930。09:05看到首层VCS已于08:54:12完成25344输出、3843121周期、无饱和；完整VCD **30231391361B**，仍执行`activity_scan.log`，阶段最终通过尚未观察。首VALID在此门级运行相位0ns，保留实际窗口。不要重复启动、清锁、并发EDA或大波形扫描。

下一次先读state和owner（输出简短字段，避免日志挤掉状态），等完整活动扫描自然完成；核对摘要/哈希后再排原8路首层PT。原8路后续完整14门级/12活动与功耗尚未完成。

## 正在修复的轻量审核工具

- `dma16_power_activity_review.py`逐层核对实际settings、映射、显式未标注清单、告警、工件哈希和相同冻结配置；不扫描VCD，不自动批准功耗。
- 首版db8包672输入/197干净tests，通过FileZilla33秒上传，08:55:22.524544安全解包，服务器672输入已核验。首轮真实审核在表头守卫失败，没有通过输出；诊断在db8 `runs/annotation_all12_v1_failure.json`。
- **真实原因：** 同一报告含Switching Activity与Static Probability两张总览，完全相同的表头出现2次；4个“Nets ”开头行含2个“Nets Driven by”分类标题。首表头与本地预期逐字符相同，不是空格或列名差异。不能简单允许任意重复表头。
- 本地已改为分别识别两张具名表、每表独立严格核对列名/顺序/10列/合计、排除精确分类标题；静态概率和翻转来源都检查。9个工具测试，连同数值/完整报告共33tests通过。
- **修正版未提交/打包/上传/服务器执行**。下一步先提交当前明确改动，新包干净检查应198tests，672文件预期不变；上传后用新的`annotation_all12_v2`，保留首轮失败。不要修改服务器旧包工具。
- db8包ZIP SHA `7935ce6d3788c896525f6bd1723f294aa8a632586f649bfbe63e241bf9ab23e6`，16629994B；旧干净audit `local_runs/dma16_annotation_clean_audit_20261110_0850/receipt.json` SHA `f9cd6de76edd25346f76cc117ae86033718c6790c8f17a720fe9a2e36f99a441`，这是首版而非修正版。

## 仍未完成

1. 新双表解析器实际12层复验。
2. 未知活动有效使用/初始状态与全部层审核。1aa全34742对象网表审计只有1775项全别名仅声明；32967项有表达式需时段审核。有引用MAC 19733标识未知累计中位/最大约92694.0045周期，不能说都是小毛刺；结束已知也不等于无功耗影响。
3. X敏感性诊断尚未实现/启动。安装手册明确X系数控制X跃迁功耗比例，initial-X决定首次X→0/1是否计入；冻结报告采用0.5/false。后续诊断不能替代默认正式条件、不能把未知强制0或宣称绝对误差界。
4. 原8路完整同条件PPA、干净服务器复现、最终提交包和答辩材料。现有验收/索引/答辩已更新完整1200及报告完成，仍保留功耗未验。

## 操作约束与恢复

- 仅经开发板Linux VNC操作服务器、FileZilla传文件；不直接SSH/下载/旁路。现FileZilla已断开最小化。先刷新窗口清单，最近VNC18874435、FileZilla20972102、panel10485764；VNC现5个终端页，第三页空闲用于查询，门级在后台持锁。
- 已有板端工具`F:/linux_fpga_try/ac820.ps1`；上传前创建新`/home/root/...`目录，GUI路径为`/home/board/...`。远端单行Python命令<1000字符，先长度检查；stdout用8位SHA逐行编号并独立断言，避免长串截图误抄。
- 服务器base `/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109`；包在`bundles`；共享锁在父IC的`.arch02_team_lock`。
- 当前没有本地测试/上传会话挂起；首次长度超1000命令在本地被拒绝未执行。所有失败与旧输出保留。
- 复用`local_runs/audit_dma16_delivery_bundle.py`，模块清单已包括unknown_netlist和power_activity_review；检查5固件/40生产文件/规范LF审定及全部tests。打包仍用sequence v7（字节与v6相同，只更新来源manifest），不能用旧37任务批量入口。
- 08:39:42文件系统空余2745875562496B；`quota -s`无输出不能证明无限个人配额。大型波形不删除，下一批前复查空间。
