# B0 L01控制驻留补读工具

2026-11-13，仅B0/N1证据审核。原unknown工具、受测硬件、活动及报告保持冻结；不实施N2或启动EDA。

## 已观察的原因与范围

根代理已完成L01完整未知清单。03:41截图确认shared顶层32组bank_data各32位全部窗口未知，另有160个N*组合节点；AON具名查询仍被大量生成网掩盖。后续03:44实际过滤结果为SYNOPSYS_UNCONNECTED 34组/34位、T_生成名47组/450位，其余1552组/1633位包含大量n*及Queue_1的index/mask、io_in_0的地址/数据/opcode/size/source。名称只帮助选择读数，不能作电气豁免。

现unknown清单不含原本完全已知控制的驻留。因此新增`scripts/b0_saif_control_probe.py`，将需补读的控制集中在**一次L01原SAIF读取**完成，避免按信号反复读110MB文件。工具本地准备完成，真实服务器结果尚未取得。

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
