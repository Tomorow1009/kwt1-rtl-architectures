# DMA16 搬运引擎交接

更新时间：2026-11-09 18:25（北京时间附近）。执行起点H0=2026-11-09T17:16:08+08:00。有效计划为 IMPLEMENTATION_PLAN_DMA16_20261109.md。

## 最新冻结候选（优先于以下过程记录）

- 生产RTL `arch03_dma16_accel.sv` SHA256：`4270345c39477220831ef4fda8227dc4f3c8d6df71f66234bfc0ec63b2df9f53`。含PREPARE、STATUS bit14、CLEAR新fault优先及提前响应守卫。主代理已收到并要求完成后保持冻结直到运行包验证。
- ABI SHA256：`6b1c53a46e8f490208adbd1d4734d2aead2bbe1ebf0df93cf0e294c7eba87c90`。
- 同版15协议通过：`local_runs/dma16_protocol_20261109_182449_665683/summary.json`，SHA256 `3f06b1d523dfc9c37057be5b492f7065589a4fba24773a07db5abffba7e83f2b`。exec65370已退出0。
- 同版实际局部fabric无额外等待6任务通过：`local_runs/dma16_datapath_20261109_182450_930510/summary.json`，SHA256 `50af9cb1f84ce8cc585ea5d31a806fb09adf7ae49a68f4bee97caa9baf793f17`。pf0=274010、pf1=225770；exec11676退出0。每例另有无复位下次首请求前清缓存、held-valid取消并经fabric排空probe。
- 同版标准14×prefetch两档反压实际局部fabric回归 **exec72618已退出0、整批PASS**：`local_runs/dma16_datapath_20261109_182450_311356/summary.json`，28任务、709632实际写回输出；每例pf0=347397、pf1=291159，全部含无复位下一次SOURCE请求前缓存清理/取消排空probe。摘要内engine SHA与上述当前冻结RTL一致。
- 实际总master传输47904个32位事务=191616B（额外源读46976B也计时），不是用户示例三段144640B总数；每任务11744源读＋11744共享装载写＋11744共享供core读＋12672结果写。
- 所有上述为本地pin_mock和/或协议stub；没有真实E203、厂商宏、服务器DC/STA/面积/功耗验证。root负责下一步不可变打包/SoC流程。本代理不提交Git、不操作服务器。
- 当前没有本代理仍在执行的仿真，所有exec均已退出。主代理新派任务为独立`dma16_synth.py`和离线契约/面积测试；不再修改本引擎生产RTL、TB、ABI，除非出现新的实际缺陷并先协调。

子代理 evidence_audit 当前获授权：只新增DMA16引擎、局部协议/集成测试和本模块ABI/交接；不改旧arch03_icb_accel、install_platform、sw、公共文档，不操作服务器、不提交Git。主代理负责平台原ICB仲裁/源路由；dma_feasibility代理负责arch03_linear16；contest_requirements代理负责tile16打包/批量。

## 已完成

- 新增 rtl/arch03_dma16_accel.sv：单MMIO应答、单master在途；SOURCE→共享写ACK完整装载后START core；共享读供core与成对结果写公平交替；16×32bit结果FIFO及地址；全部最终成功写ACK、core.done与缓冲/总线排空才DMA DONE。
- CANCEL禁止新请求，但保留已valid未接受命令，握手及响应排空后才core.cancel；首错/已提交计数保留，CLEAR恢复；IRQ完成/错误/取消，W1C；地址/长度/布局范围检查；MODE0真正16路MMIO debug，MODE1 DMA下LOAD/OUTPUT拒绝。
- 新增 DMA16_ABI.md，主代理已接受ABI。默认SOURCE=b0000000、shared=a0000000、output=a000c000；布局00100001；70额外SAT_COUNT。
- 主代理已核验官方平台O4 SysMem覆盖b0000000；将原已有SysMem ICB接口引出加载仿真边界，不是专用SRAM绕行口。SOURCE默认可冻结。
- 新增 tb/tb_arch03_dma16_protocol.sv 与 scripts/local_dma16_protocol_verify.py。明确使用非算术core stub、不是E203/真实算术/服务器证据。
- 协议9用例全部通过：完整47904笔DMA事务、所有25344输出地址/值、FIFO到达16、最终写ACK等待、MMIO应答反压稳定、取消held-valid/在途写、4类DMA读写错误及首错保持、地址重叠/非法地址、真正MMIO debug全输入输出。
- 通过运行：local_runs/dma16_protocol_20261109_173322_633523/summary.json；exec session40851已退出0。
- 扩展协议12用例通过：local_runs/dma16_protocol_20261109_175111_759406/summary.json。新增输出在途取消、错误坐标拒绝、长度/布局/overflow/掩码/地址全组守卫、完整47904事务同周期命令/响应。随后把零延迟TB计数器更新改为nonblocking以消除测试调度竞争，需针对当前TB再验；生产RTL未变。
- 新增 tb/tb_arch03_dma16_datapath.sv 与 scripts/local_dma16_datapath_verify.py，实际DMA+linear16+shared_sram RTL、pin_mock、真实输入装载/最终ACK，逐25344输出与饱和。正式打包器数据直接使用 layout_manifest.json。
- layer01/extremes/rounding×pf0/pf1共6真实局部任务152064输出通过：local_runs/dma16_datapath_20261109_174722_900143/summary.json。pf0=347392、pf1=291154周期，带源延迟及命令/响应反压、最后ACK31拍等待；不是E203/原平台仲裁/厂商宏/STA证据，不能据此宣称正式500达标。
- 原局部完整14×pf0/pf1共28任务709632输出通过：local_runs/dma16_datapath_20261109_175143_655455/summary.json。该版本计时在下一拍采样首valid，少计首个offer周期；旧数值保留其边界。
- 修正CLEAR与新fault同拍优先级：`error_q==0 || clear_request`时锁存新fault。原逻辑旧error非0、同拍CLEAR和孤立响应可能清掉新fault；这是代码审阅发现，不是算术失败。新增定向通过。
- 改为首dma_cmd_valid发送沿采样start，末输出ACK同步采样end，并用独立realtime交叉核对。完整14×两档再验通过：local_runs/dma16_datapath_20261109_180037_183235/summary.json，严格pf0=347393/pf1=291155。
- STATUS bit14已暴露core.start_ready，主代理同意驱动等待busy=0、start_ready=1；ABI已更新。
- 进一步局部TB接入实际新增arch03_icb_arb2、arch03_icb_memory_router、真实shared_sram，CPU主设备输入闲置。无故意额外等待的源为请求接收时寄存响应、下拍可消费，符合主代理SoC加载模型。layer01/extremes/rounding×两档6任务通过：local_runs/dma16_datapath_20261109_180639_844294/summary.json；pf0=274010、pf1=225770周期。只能作局部预算，不是E203/真实宏/STA成绩。
- 最终当前RTL协议14项通过：local_runs/dma16_protocol_20261109_180735_623557/summary.json，新增START_READY软件可见检查、共同reset在途事务和新完整任务恢复；含所有前述取消、错误、反压、完整zero-latency响应检查。exec95076已退出0。
- 上一条RTL为PREPARE前版本。带实际arb/router的完整14×两档已通过：local_runs/dma16_datapath_20261109_180736_176583/summary.json（exec64619已退出0）；仍不能外推到后续PREPARE版本。
- 严格缓存清理补充：旧引擎初始装载后才core.START，虽然未复用旧数据，上一任务的X valid可保留到新任务初始加载期间。现新增PREPARE state=6，DMA START先core.cancel并等待flush/start_ready，之后才生成首SOURCE请求；计时不含纯有效位清理，实际输入传输仍全包含。SVH既有内部绑定名没有改变。
- PREPARE版协议14项通过：local_runs/dma16_protocol_20261109_181656_195423/summary.json（exec13147退出0）。
- 实际路径TB新增无复位第二START：上一任务X valid=1，独立首SOURCE valid事件断言X/bank全0；hold该新请求后CANCEL，经过实际arb/router接收唯一源响应，要求不产生共享写且全部排空。先前第一轮完整layer01算术通过，但probe读started与posedge-valid更新同delta竞态失败，保留local_runs/dma16_datapath_20261109_181656_791722/layer_01_pf0.log。修复仅TB：held-valid保持到下一negedge再读probe结果，独立发送沿缓存断言仍保留。

## 尝试路径与失败

- 首次RTL编译/展开直接通过。首轮协议前8用例通过，最后MMIO debug失败：stub的load_ready每7拍任意抖动，软件式先观察ready后发MMIO写可能遇到ready变低，硬件正确返回访问错误。并非DMA丢数。
- 首轮保留：local_runs/dma16_protocol_20261109_173144_124118/simulation.log。修正仅stub：DMA streaming仍随机ready，MMIO debug阶段ready在CPU读状态至写之间稳定。新独立运行9用例通过。

## 尚未完成

1. PREPARE+无复位缓存清理/取消probe的标准14×两档反压回归exec95619已退出0：local_runs/dma16_datapath_20261109_181810_632897/summary.json。同配置layer01/extremes/rounding×两档无额外wait预算回归exec81802也已退出0。以下旧活动记录保留，当前新运行见后。
   - 81802已退出0，目录local_runs/dma16_datapath_20261109_181810_072020，6任务及无复位probe全通过；无额外wait仍pf0=274010、pf1=225770。
   - 95619最近layer10 pf0通过，有反压当前phase为pf0=347397、pf1=291159，因PREPARE使固定周期抖动相位改变，不是少计计时。
   - core代理只读review发现协议守卫：提前rsp_valid在cmd_valid=1但cmd_ready=0时，旧 `!pending_q && !dma_cmd_valid` 未拒绝。已先用定向复现实际失败，保留local_runs/dma16_protocol_20261109_182308_344276/simulation.log（前两个用例过、提前响应未拒绝而fatal）。待95619结束后已改 `!pending_q && !dma_fire`，仍允许合法同拍接受/响应。
   - **当前生产RTL已是提前响应修复版**。正在最终同配置运行：15协议exec **65370**；14×两档有反压exec **72618**；3用例×两档无额外等待exec **11676**。data=local_runs/dma16_layout_14case_20261109_h0。用write_stdin读最终，不重启，不改RTL/TB/runner/两个fabric模块。
2. 协议扩展/同周期响应/共同复位恢复均通过。实际DMA A/B不同输入无复位连续完整任务尚未测；当前新增probe证明旧X有效状态在下一首请求前失效并能取消排空，第二任务没有完成算术。core代理已有core范围A/B证据，不能替代引擎完整A/B集成。
3. 服务器厂商宏、原SoC仲裁、真实E203固件、综合、严格150MHz、面积、完整窗口功耗和最终1200均未验。
4. 引擎初始装载全完成后才core计算，这计入真实装载，不预装共享区；500 task/s仍目标。实际单在途请求间隔待集成实测，不能套NICE测量。

## 恢复入口

先读AGENTS.md、CONTEXT_HANDOFF.md、有效计划、本文件和DMA16_ABI.md。勿改其他代理正在回归的core文件。真实core端口：start_valid/start_ready、shift、load_valid/load_ready/load_data、out_valid/out_ready/out_row/out_column/result/saturated、busy/done/error，新增cancel与prefetch_enable；cancel后一拍flush，等start_ready。core.done为最后输出握手后一拍脉冲；error至cancel粘滞。

Vivado D:/Xilinx/Vivado/2018.3/bin；Python E:/fpga_race-two/.venv-kwt/Scripts/python.exe。协议复现：`python workspaces/arch03/scripts/local_dma16_protocol_verify.py --vivado-bin D:/Xilinx/Vivado/2018.3/bin`。每次新目录，保留旧失败，不重用摘要。
