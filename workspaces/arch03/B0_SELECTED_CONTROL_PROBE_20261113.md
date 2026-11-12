# B0 L01控制驻留补读工具

**05:55–05:56最新：**原报告最终SHA`677a1ae11042ffe6aab98fb1b0f124b29f604e6dc0d9bb29e96d9f04f4f6a81a`已八组join/实际HASH_MATCH=True/DIFF空确认，_v1/_v2/_v3均为手抄失败，原报告未变。L01 proof d894…和1253/1253/1253计数已读；未知gzip原SHA通过，41406总条/2234局部条/2234唯一名/重复0。后续只执行model/overlap_v4，尚无交集或模型结论；不重跑原报告身份。

2026-11-13，仅B0/N1证据审核。原unknown工具、受测硬件、活动及报告保持冻结；不实施N2或启动EDA。

## 已观察的原因与范围

根代理已完成L01完整未知清单。03:41截图确认shared顶层32组bank_data各32位全部窗口未知，另有160个N*组合节点；AON具名查询仍被大量生成网掩盖。后续03:44实际过滤结果为SYNOPSYS_UNCONNECTED 34组/34位、T_生成名47组/450位，其余1552组/1633位包含大量n*及Queue_1的index/mask、io_in_0的地址/数据/opcode/size/source。名称只帮助选择读数，不能作电气豁免。

现unknown清单不含原本完全已知控制的驻留。因此新增`scripts/b0_saif_control_probe.py`，将需补读的控制集中在**一次L01原SAIF读取**完成，避免按信号反复读110MB文件。工具冻结时真实服务器结果尚未取得；后续单层实跑见文末记录。

## 固定选择与缺项

- shared顶层：clk/rst_n、cmd_valid/ready/read、rsp_valid/ready/err、read_pending、fire/mapped、bank_q五位及cmd_addr32位。
- 64个bank半字适配器：clk、cs、we、wenable、mask；单独检查每bank/low/high。
- 64个实际宏：CLK、CEN、GWEN、RET1N及WEN[0:15]，共1280个必查身份逐个报告缺失；适配器mask[0:1]也列为必查。适配器信号不能自动替代未记录的宏引脚证据。
- AON子树：语义名称以valid、ready、clock/clk、reset/rst、enable/en结尾的控制，明确包含io_in_0和Queue_1的enq/deq控制。顶层clock/reset、io_in_0_valid/ready和Queue_1相关valid/ready作为明确必查名称，缺少则报告missing；改名或优化掉不能假定已知。

这是固定名称范围的补读，不声称涵盖所有控制锥。生成n*/T*仍需实际mapped连接追溯；SYNOPSYS_UNCONNECTED只在终端显示中过滤，未豁免。

## 完整性与边界

输入是已冻结L01未知清单summary及显式SHA，自动找到原B0 report、activity summary、passed state、原L01窗口及SAIF。原SAIF通过同一binary遍历同时SHA与解析；**全部native audit字段**必须与原回执相等，包括规模、SHA、单位、持续时间、106源口及模块/驻留统计。原文件开头/结尾stat一致，输入回执和实际导入依赖起止SHA一致。

记录工具、native_saif_activity、saif_syntax、icb32_power、soc_power、icb32_synth的来源/SHA。只需现有41b scripts提供依赖，不需要修改或导入冻结unknown工具。输出最多4096条、8MiB，输入SAIF上限256MiB，开始和结束保持2GiB空间余量；新目录不覆盖，失败保存request/failure及已捕获的未验partial。

每条保留真实完整层级名、PORT/NET、T0/T1/TX/TZ、TC/IG、精确ns、条件子记录及所选身份。combined TX仍是X或Z；存在COND/IOPATH时保留原子记录而不猜其语义。

**驻留只有边际统计。**不能据此证明cmd_valid、cmd_read与read_pending的联合关系或事件顺序，不能将14.666652ns未知放在假定的首两拍，不能凭valid全已知判数据无功耗影响。若cmd_read真实T1=0且无未知，这是该信号窗口内恒0的证据；若其有1驻留，则仍需真实握手或更细观测判断是否接受读。宏控制缺失时只列缺项，不输出完整控制已验。

输出status只表示`selected_control_residence_collected_review_required`；`system_power_verified=false`、`full_control_cone_audited=false`、`joint_timing_proved=false`保持明确。该工具不赋活动值、不调用PT或仿真器。

## 运行入口与本地检查

根代理核验新工具包后运行一次；本代理没有远端操作：

```text
PYTHONPATH=<现41b包>/workspaces/arch03/scripts python3 -B <新独立ops>/b0_saif_control_probe.py --inventory <原项目>/operations/b0_unknown_l01_20261113_0319/summary.json --inventory-sha256 1a8c943829995ed0e42bdfe8801279065654f1e5314e771be8c726858376387f --scope-root <原项目scope根> --output <新的绝对路径>/b0_control_l01_01
```

本地9项fixture检查通过：完整原audit相等、源只读一次、实际1fs换算、已知/未知控制、selected条件子记录、嵌套与扁平bank路径、缺宏引脚不能由全部adapter顶替、WEN/mask缺项不得标完整、错误SHA/scope/截断、依赖变化与失败保留。独立只读审查提出的WEN/mask覆盖口径问题已修正；同时扩充io_reset_n/io_hfclk后缀选择。fixture不代表真实B0控制或功耗通过。

实际输出后的最小读取顺序：selected_count及missing分类 → shared cmd_read/read_pending/bank_q的T0/T1/TX/TC → 64macro与adapter分别覆盖/未知 → AON队列valid/ready与clock/reset → unresolved生成锥的映射关系。缺失或有未知的功耗相关范围继续明确记录。

## 04:05取得的实际单层结果

根代理的唯一probe已完成，输出为`/tmp/s4_21usr_n1_20261113_0210/b0_control_l01_20261113_0403`。本代理亲读`control_probe_status_0406.png`，终端查询时间04:04:54：status为`selected_control_residence_collected_review_required`，selected558、selected unknown0、COND0、重复身份0，完整原native审计相等。

缺项仍为macro1280（全部宏引脚未记录）、adapter64、shared_top7、AON顶层5。因此本结果只证明实际选到的558条边际驻留没有未知；不能称宏控制、整个控制锥或系统功耗通过。下一读只访问这份小summary，列出具体missing并读取shared读控制、握手和bank_q的驻留，再决定哪些缺项需要实际mapped直连/常量证据，不重复原SAIF扫描。工具及此前unknown工具继续冻结；本代理没有远端操作。

04:06–04:10补读：实际summary为570051B，SHA **`2c06372156a5f80e50e6c0634002f6686dc1768966d65bde32cc7a51b0060f7d`**，首8字符经逐字符截图核准，早前不完整/误抄串不得使用。本代理亲读`control_probe_shared_0407.png`：read_pending全窗口208926645774 ticks为0、TC0，cmd_ready全窗口为1；cmd_read的T1为65753326758 ticks、TC13286，因此不是恒0。缺失shared名称是fire、mapped、bank_q[0:4]；adapter缺wenable64；AON缺io_in_0_valid/ready、Queue_1_io_enq_valid/ready、Queue_1_io_deq_valid。缺名不能自动解释为常量0。

下一步使用原unknown summary绑定的mapped.v及实际index_netlist依赖，核shared真实reference、bank_q声明/assign和实际适配模块的宏控制pin表达式。read_pending恒0可在实际mapped关联及clock/reset证据齐全后支持本窗口未接受shared读的推导；当前不从cmd_read边际统计或源码单独下结论。宏端口未记录时，应补实际直连/组合关系证明，不将adapter记录直接充当leaf活动。

04:12与04:18实际mapped补读（亲读`b0_shared_mapped_scope_result_0413.png`、`b0_macro_pins_result_0418.png`）：SHA相等后解析到shared reference `arch03_shared_sram_turnover`、64个适配子模块；没有名含bank_q的网声明或直接assign，这不证明bank选择状态为0。实际首个宏`u_arch03_shared.banks[0].high.memory`属于`arch03_sram_half_turnover_62`，其CLK→clk、CEN→n2、GWEN→n8、RET1N→1'b1、WEN[15:8]→n6、WEN[7:0]→n7。这里只记录一例实际表达式，未推广到64例，也未按单元名推断极性。

后继已准备两条不足1000字符且本地Python3.6语法检查通过的只读查询：将全部64宏按五类控制pin表达式分组；将全部64adapter移除宏实例后的完整逻辑分组，作为控制锥的保守超集。只输出前八组及每组全文长度；显示截断不当完整证据。bank状态另需在实际cell实例/选择锥追溯，不修改RTL或启动EDA。

04:24:49全部64macro表达式分组已完成（亲读`b0_macro_groups_0425.png`）：63个为上述接线，1个GWEN=n3、WEN高8=n5/低8=n4；CEN=n2、CLK=clk、RET1N=1'b1均相同。网名差异尚不说明功能差异。该结果明确给出全部64 shared宏RET1N常量1、CLK直连各自adapter clk；结合已选adapter clk有记录且unknown0，可解释这两类引脚的已知性。CEN/GWEN/WEN仍待完整adapter逻辑及真实库function核对；1280宏引脚原本未记录这一事实不改写，也不因此批准系统功耗。

04:50:08 adapter完整逻辑查询完成（亲读`b0_adapter_logic_result_0451.png`）：全部64分成33/30/1三组，每组226字符全部显示，各只有5个INV2_12TR40/NAND2CV2_12TR40组合门。宏控制端口的已知性可在实际Liberty function确认后按已知cs/we/mask进行逻辑推导，但当前不凭单元名字认定取反/NAND语义。若实际function符合预期，三组的n编号或语句顺序不改变同一控制布尔关系；该条件式不作为已验结论。

已保存固定只读Liberty查询`E:/fpga_race-two/takeover_local/b0_adapter_liberty_query.txt`，970字符/971B，SHA f66a5994b64396bb40228e14fdc092ab68e83fdce33eac68cd9d81d9cbaefbd6。从原synthesis summary的link_report.library_inputs按已绑定标准库SHA 5d236b1571f5bc791895328fa3f6f94e3873e985ee7963b9ac5e3e849b48949f唯一定位并核完整文件，再只读两种cell的pin/direction/function。ASCII、shell引号、Python3.6语法及合成字段提取fixture已核；尚无该查询实际服务器结果，未运行PT/EDA。

## 04:55–04:57实际映射与Liberty补证

根代理执行后，本代理亲读`takeover_local/b0_bank_state_result_0456.png`及`b0_adapter_liberty_0457.png`。04:55:19实际网表共有8条含bank_q/read_pending的语句：5个`DRNQV2_12TR40 bank_q_reg[4:0]`保留，Q分别连接N9至N5，D分别n72至n76，CK=clk、RDN=n792；`read_pending_reg`同类触发器D=n1082、Q=read_pending、CK=clk、RDN=n792。其余为含read_pending的NOR2V2与AOI211V2逻辑。因此旧bank_q网名缺失是映射改名，不能说寄存器消失或恒0；N5至N9的实际驻留、状态选择/数据消费仍需追溯。

04:56:35实际标准Liberty完整SHA核对通过，仍为`5d236b1571f5bc791895328fa3f6f94e3873e985ee7963b9ac5e3e849b48949f`。实际pin定义为：INV2_12TR40的I=input、ZN=output、function=`(!I)`；NAND2CV2_12TR40的A1/A2=input、ZN=output、function=`(!(A1&A2))`。结合全部64适配器的完整五门逻辑及宏控制接线，三种文本组归为同一实际关系：

```text
CEN = !cs
GWEN = !(cs & we)
WEN[15:8] = !(mask[1] & cs & we)
WEN[7:0]  = !(mask[0] & cs & we)
CLK = adapter.clk
RET1N = 1'b1
```

这些是实际映射及实际库函数的组合推导，不再依据单元名称猜测。L01原控制probe已记录全部64适配器的clk/cs/we/mask且TX/TZ均0，故可确认这64个shared宏上述控制输入在该窗口的已知性。原SAIF未记录1280个宏leaf pin这一事实保持不变；本结论不是直接leaf活动注释证明，也不恢复联合时序、读写事件数或毛刺波形。未读取的其他11层控制驻留不能继承L01结论。

系统功耗仍未验收。N5至N9真实bank状态、未知bank_data/N*如何被实际read mux消费、AON与其余有负载未知锥，以及未知活动的功耗影响仍需独立闭合。下一最小查询优先从已有L01未知gzip按完整shared scope精确读取N5至N9及read_pending：清单包含者返回实际驻留，清单不含只能表述“未知清单无此声明”，不能冒充已得到T0/T1或宣布常量，不重扫原SAIF。

05:09:13该未知gzip查询已经执行，本代理亲读`b0_bank_knownness_0510.png`。原gzip完整SHA及41406行数均核通过，`UNKNOWN_MATCH=[]`，N5至N9及read_pending全部`ABSENT_FROM_UNKNOWN`。这与独立控制probe的read_pending全0不矛盾；前者只列未知，不能证明五个新名是否存在于原SAIF及其T0/T1。没有再次读取原SAIF。

下一步已准备两个独立只读短命令，尚无实际服务器结果：`takeover_local/b0_shared_control_drivers_query.txt`只列小写n9、n1082、n792的实际驱动与n9消费者（计数及前10条）；`b0_shared_model_identity_query.txt`从已核原report→gate summary→source_inputs定位4096厂商Verilog模型路径/SHA。只有读取实际模型后才解释写时Q保持或置X行为，本地behavioral不能替代厂商模型。即使读消费被禁用，也不能将全部bank_data及组合节点自动记为零功耗。

本地只读再次确认main_systolic_b.c、kwt_systolic_b.c、arch03_shared_sram_turnover.sv与B0生产63da的git diff为空。原正式B驱动明确要求load_acks=0、source_acks=stage_acks=encoded_bytes/4、output_acks=12672；主程序只写shared mailbox而不读结果。这支持正常性能任务预期无加速器shared再读的解释，不能替代实际mapped窗口的电气/活动证据；另外CPU竞争用例的scratch读不移用于本功耗窗口。

后续消费锥查询已运行但原截图上半driver部分未保留下可读结果。亲读`vnc_after_minimize_0525.png`（实际钟05:21:23）仅确认小写n9引用总数3：BUFV2RD_12TR40 U392的I=n9/Z=n779，U394的I=n9/Z=n780，以及NOR2V2_12TR40 U398的A1=read_pending/A2=n11/ZN=n9。当前没有证据补写其余driver或BUF/NOR的实际Liberty function。更短的`b0_shared_control_frontier_query.txt`只列n9/n11/n779/n780/n1082/n792实际驱动，待根在N1恢复后读；不扩大为新的SAIF扫描。

05:40:46该frontier已实际完成：除上述三条外，INV2 U39从n793驱动n792，INV2 U73从n13驱动n1082，NOR2BV2 U227的A1=n15/B1=n14/ZN=n11，共6条。只有INV2实际function已被此前读取，其他门函数仍待查。随后宏模型身份/no-load交集两个只读命令在首reportSHA断言停止；05:50逐行分组核对确认是本地手抄常量错误（05:46的_v2仍误抄后半并失败），原inventory pin与实际报告相等，报告没有改变。正确原报告SHA为`677a1ae11042ffe6aab98fb1b0f124b29f604e6dc0d9bb29e96d9f04f4f6a81a`；旧失败命令/截图保留，生成_v3命令但尚无实际结果，_v1/_v2失败文件均保留。完整恢复入口及新命令SHA见B0_REVIEW_CHECKPOINT_CONTROL_MAPPED_20261113.md。

## 06:00–06:05实际推进（优先于上述历史待办）

- 现成no-load证明与局部未知精确交集已读：LOCAL2234、PROVEN1253、HIT0、REMAINING2234。两边名称同为u_e203_subsys_top起始层级，预览分别为dcsr_r位和子模块inspect_pc位；不增减前缀强造匹配，2234项仍无全局无负载豁免。
- 原report→gate summary→source_inputs身份链通过，唯一实际4096模型为`/storage1/admin_public_dir/SRAM_Lib_2025/RAMSP4096X16/verilog/RAMSP4096X16.v`。模型索引再按源输入清单的原SHA验证成功，1768行，47条Q赋值/task候选。没有复制整个厂商模型，候选索引不代表已经解释其全部行为。
- 固定5d236…库实际函数已读：BUFV2RD的Z=I；NOR2BV2的ZN=`!((!A1)|B1)`；NOR2V2的ZN=`!(A1|A2)`。结合实际端口，n11=n15&!n14，n779=n780=n9=!(read_pending|n11)。这只确定该消费控制片段，不证明整个bank_data路径无活动或功耗为零；没有按门名猜极性。
- 模型实际Q输出赋值含RET1N/pre_charge_st及Q_int，readWrite从258行开始。下一只读258–286与287–321的真实分支，并核原compile_command的实际定义；索引中出现Q_int=X不能推成所有写均输出X，也不能用本地behavioral代替真实模型。

## 06:12–06:18实际模型与声明分类补证

本代理亲读`b0_readwrite_a_zoom_0613.png`、`b0_readwrite_b_top_0615.png`和`b0_readwrite_b_0614.png`。原gate的compile_command按原source_inputs哈希通过，实际定义为`+define+ARM_UD_MODEL`及`+define+functional`。实际4096模型在有效保持/使能/地址条件下：GWEN已知为0的分支写入mem，不给Q_int赋值；GWEN已知为1的分支读出数据并更新Q_int。因此正常写保持Q，正常读更新Q。RET1N未知、相关模式/控制未知、地址异常、GWEN未知等独立异常分支仍可能产生X，不能将异常分支当成正常写行为，也不能遗漏这些条件。该结论来自原模型正文及原编译定义，不是本地behavioral推测。

L01的read_pending整窗为0、共享Q保持全X，与正常写期间未初始化Q保持的解释相容。但这不是其余11层的控制证据，也不自动说明所有共享读mux、未知状态相关泄漏或AON未知不影响功耗。现有L01 probe已覆盖cmd_addr全部32位且未知为0，后续最小边界是实际64宏A/EMA/EMAW接线分组及bank选择/输出消费控制；不扩展为无边界逐门查询。

06:17:48的局部声明候选分类为internal633、output821、input780，NO_GLOBAL_WAIVER=True。原查询仅对port表未命中的名称使用internal标签，因此633目前只是候选，不能先称真实wire/reg。新的`takeover_local/b0_local_decl_actual_query.txt`（999字符，SHA `148bc3a00f59f89d2de197992b0d234ff20e293130bef9a9c0a212da2125cb81`）绑定原index_netlist、网表及未知gzip身份，按resolve_alias相同规则区分独立位选和转义标识，再要求名称存在于实际nets声明；不存在者显式列MISSING，实际声明存在且不在ports者才列internal。本地仅验证ASCII、shell参数及Python3.6语法，尚无该新查询服务器结果。即使633候选全部证实，1601端口仍须跨层连接审核，633非port声明也尚未取得全局无负载豁免。

## 后续控制补证的限定方案（尚未执行）

冻结control工具的`scan()`可直接复用完整native/window/SHA比对，但`collect()`两处固定筛选L01，因此原CLI不能直接采其余11层。建议仅新增薄包装，读取已完成L02–L12未知inventory及原report/activity/state，精确限定这11层、每层对原SAIF单遍、独立新输出/失败保留、记录原工具及依赖哈希；完整原native对象仍必须逐字段相等。复用已完成L01回执，不再扫描L01、不重建任何unknown JSONL、不改原工具或SAIF、不启动仿真或PT。每层继续显式列缺失macro pin、已选控制未知、条件子记录及联合时序限制；任一层read_pending非零都需独立读路径审查，不能继承L01结论。该方案目前只有接口核对，没有新包装、新扫描或新功耗批准。

## 06:32独立包装已准备，真实扫描尚未运行

根代理批准后新增`b0_controls_remaining11.py`，原probe及unknown工具未修改。包装严格接受且仅接受L02–L12完整十一例，绑定原report/activity/state、各层完整native回执、已完成L01控制summary及其selector/依赖SHA；运行时调用原`scan()`逐层顺序单读。L01只读取既有小summary，不读取原SAIF。每层独立新目录、成功摘要、失败前缀及partial保留；总结果中的`full12_receipt_coverage`只表示旧L01与新11份控制回执齐全，`system_power_verified`、全控制锥和联合时间证明仍为false。

成本上限为11×256MiB源读取、初始空间要求2GiB＋120MiB，实际输出仍受每份8MiB限额；推荐私有/tmp、单worker及低优先级。宿主时间暂按原L01约两分钟级×11规划，不能在未实际运行前承诺精确时长。它不使用EDA许可证、不启动VCS/PT、不重新生成未知清单，也不回写旧报告。

新7项小fixture全部通过：各SAIF只读一次且不读L01、所有源不改；缺宏pin仍明确；错误层集合、L01合同/依赖不符拒绝；中途源SHA/统计不符保留前缀及partial；依赖变更、空间不足、错误inventory SHA留失败回执；旧输出不能覆盖。两个新Python文件通过3.6语法核验。测试只验证包装合同，不是实际B0控制或功耗通过，独立代码审阅正在进行。

```text
python3 -B b0_controls_remaining11.py
  --inventory <project>/operations/b0_unknown_l02_l12_20261113_0326/summary.json
  --inventory-sha256 ddf61c38beeed4261d9a87604d4870979d960072ae3b8713823b53fc328d5643
  --l01-control /tmp/s4_21usr_n1_20261113_0210/b0_control_l01_20261113_0403/summary.json
  --l01-control-sha256 2c06372156a5f80e50e6c0634002f6686dc1768966d65bde32cc7a51b0060f7d
  --scope-root <original project root>
  --output <new private absolute directory>
```

上述为参数说明，不是已经执行的命令。实际导入的原probe必须仍为SHA b1c6df556c7df0f2b8e13c1be6c2ba8babb4b994f50c2d99b5f78af24d7bc963；其余依赖逐SHA与L01原回执匹配，路径迁移不能掩盖文件变化。

06:31:49的实际声明查询结果已亲读`b0_actual_decl_and_pending_0633.png`：633 internal、821 output、780 input，无MISSING，所有原工具/网表/gzip身份和数量断言通过。因此633已证明是实际nets声明且不在ports，另外1601确为实际端口方向；此前候选分类没有因为名称匹配差异丢项。仍须区分本模块零表达式引用与全局电气无负载，不继承1253默认网的证明，也不据此批准功耗。图中另一个宏地址/模式查询当时只有输入行，尚无结果，不能记成已执行。

06:32:46该宏地址/模式查询实际完成，已亲读`b0_macro_address_mode_0634.png`：全部64宏只有一组，A连接各适配器addr，EMA固定010、EMAW固定00；三个pin的64实例覆盖及原网表/parser哈希断言均通过。结合此前CLK/RET1N及CEN/GWEN/WEN实际映射，已补齐这组宏接线和固定模式条件。A到addr是实际连接事实，不自动替代所有地址和控制的联合时间证明。自此停止新增手工逐门查询，下一有界动作仅为剩余11层selected-control及资源允许后的固定2234项实际全局连接查询；系统功耗未知影响仍未闭合。

独立只读审阅已完成，工具f12e89c6…及test d7088fad…未发现阻断，未重复运行fixture。低优先级由启动器设置，包装本身不设置nice。普通异常有failure回执；SIGKILL或KeyboardInterrupt可能只留下request和已完成前缀，不能将没有failure.json当成成功，必须核最终summary及完整11例身份。上述633/821/780均是声明/别名项分类，不是独立物理网络数量。
