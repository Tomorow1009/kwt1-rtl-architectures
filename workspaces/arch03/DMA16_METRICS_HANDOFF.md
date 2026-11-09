# DMA16 被动总线测量交接

更新时间：2026-11-09 20:10:35+08:00。以下“最新完成”优先于后面的实施中草案。当前有效计划IMPLEMENTATION_PLAN_DMA16_20261109.md；本代理无仍运行任务。

## 最新完成与冻结回执

- 新被动模块 `tb/arch03_dma16_bus_metrics.sv`，SHA256 `9709c7585824ec8ed66e1910c87412c29abab9436e8bb98ffe703ba01f1ac154`。
- 协议夹具 `tb/tb_arch03_dma16_bus_metrics.sv`，SHA256 `24ca0f285a988ddaa1456146baa15e81c84d4a1870d7b876bf9a9a39358a8853`。
- 解析/绑定生成 `scripts/dma16_bus_metrics.py`，SHA256 `1885fc53dc09d1f196074fb5bc947bffa636051d86631032907e83aaad08830f`。
- 本地runner `scripts/local_dma16_bus_metrics_verify.py`，SHA256 `ade9604ce69a6381a1ca9918616ea6690876e9cd509c953ea423e5f1926cca05`。
- 解析契约测试 `scripts/test_dma16_bus_metrics.py`，SHA256 `91d1cb099b6e654b3f6ac9f8c44096da47190c3ef56e61c22feacc8232f96266`；5项通过，含部分取消不能冒充完整任务、遗漏/重复/错误字节/直方图拒绝、实际路径被动绑定、Python3.6语法。
- XSim最终7个mode全部通过：1取消held请求排空、2错误ACK不计有效bytes、6无复位两个取消窗口/旧finished同arm边界、0完整47904事务、3 held payload变更拒绝code15、4第二在途接受拒绝code3、5孤立响应拒绝code18。
- 最终目录 `local_runs/dma16_bus_metrics_20261109_200900_766574/summary.json`，SHA256 `daff51a565bf6663f1f1348344e926355cbf84bcd034fdc1be3026d9d1482812`；session2298退出0。
- 每个正例均用独立offer/accept/ACK的实际时间日志重算四phase全部12项stats、4类读写切换和全部直方图，逐项一致。CPU占有总线导致的DMA等待另由CPU accept/ACK与DMA offer/accept时间区间交集复算一致；不借用测量器自身owner/counters自证。

完整47904例只是**真实arbiter＋人工服务/反压模型的协议夹具**，无E203、无MAC、无真实SRAM，不是新ASIC性能。该夹具首offer3/末ACK485344/发布485348，窗口485341周期；47904成功ACK、191616B。CPU grants44121、争用16807周期（CPU获准12187、DMA获准4200、都等待420）；CPU占有导致DMA等待172704周期、响应反压4204周期均有覆盖。禁止把这些数字当实际DMA16吞吐或服务器性能。

## 接入方式与计量语义

1. 模块全部端口为input，没有反压/等待输出。只加入仿真observer列表，**不加入生产RTL或综合source_list**。原engine/source/window/monitor/gate/server均未修改。
2. Python `binding_include(bindings)`接受至少accel/arb实际路径，生成实例文本；在原monitor信号声明之后include。ASIC RTL可用已核验模块路径；门级必须传 `dma16_gate` 实测probe receipt的bindings，不猜内部别名。
3. 连接clk/rst_n到a3_mon_clk/a3_mon_rst_n；task_arm=a3_task_arm，task_cancel=a3_task_cancel，task_end=a3_window_finished。DMA九个观测信号取accel.dma_cmd/rsp边界；CPU cmd_valid/ready与arb主cmd/rsp握手取arb模块边界。只读取现有端口。
4. 完整任务以首次source VALID发送沿起始，成功第12672个output写ACK冻结统计，晚到task_end仅发布。其23行块用 `parse_metrics(log, expected_window=原read_window结果)` 解析，实际集成应强制与独立完整窗口逐cycle交叉比对。
5. 每phase offer_wait=发出到接受的边沿间隔，READY预先为1仍可能1周期；ready_wait_cycles另计VALID&&!READY采样周期。accept_gap是同phase相邻接受间隔，包含其它事务/计算空档，不冒充纯存储服务能力。response_latency是接受到消费ACK，包含slave延迟及响应反压，不是裸宏延迟。
6. hist九bin：0、1、2、3、4—7、8—15、16—31、32—63、≥64；保留min/max/sum/count，不丢长等待。响应latency样本包括成功与错误ACK，错误数另列；只有成功ACK贡献4B有效DMA传输。CPU其他流量只计grants，不假定全字有效bytes。
7. RR/RW/WR/WW针对相邻DMA接受请求，非将phase跨度相加。CPU竞争同时报告双VALID、双方获准/都等待，以及CPU在途占有导致DMA等ready的周期；这两类观测可重叠，不能相加当总时间。
8. 默认解析要求标准几何四phase11744/11744/11744/12672、总47904/191616B及排空；`require_complete=False`可保留错误/取消分析，但full_task_counts_verified=false，不能通过性能验收。统计不替代结果、饱和、地址覆盖、cache清理或最终全局排空证明。
9. 当前仅本地协议验证；真实E203/ASIC/gate接入后的服务间隔/竞争实测仍待root运行。源/库/计时/配置不同的测量不得拼接。

## 保留的失败与修复

- 首次单独xvlog在local_runs根目录编译语法通过，产生工具临时log/xsim目录；后续每次均新独立子目录，未删除旧产物。
- `195729_961913`：Windows XSim .bat将命令行CASE=1拆错，未跑DUT；改用.options文件。
- `195805_661126`：RTL小取消例完成，fixture PASS标记误用了DMA16_BUS_解析命名空间；改fixture marker为BUS_METRICS_FIXTURE_PASS。
- 后续六例逐例通过，但runner写summary时相对__file__.relative_to(ROOT)失败；统一resolve后`200113_948735`完整六例summary通过。
- 主动新增无复位边界先复现真实测量器bug：`200345_869551/case_6.log`第一取消窗口通过，第二ARM拍旧finished=1导致code17空任务发布。修为task_end&&!task_arm，`200438_410929`七例通过。
- 补CPU在途占有等待计数及独立CPU/DMA时间交集oracle后，最终`200900_766574`七例再次全过；这是当前哈希对应配置。

## 当前未做与恢复

root需将新observer、生成include及解析接入后续ASIC/gate包，并记录实际服务模型和case参数。未改已冻结主包，不会出现在旧包的已有结果中。没有服务器操作或Git提交；无本代理运行任务。压缩后读AGENTS、CONTEXT_HANDOFF、当前计划和本文件，再读root实时回执。

## 早期实施草案（历史，不是当前状态）

当前任务由root分派：新增独立被动总线测量器、Python解析、短协议夹具和负测；不得修改首包engine/source/window/monitor、已有gate/server。四phase source read/shared stage write/shared load read/output write，记录offer→accept、phase接受间隔、accept→ACK的min/max/sum/count/hist，以及RR/RW/WR/WW切换间隔、CPU争用/仲裁接受/响应/反压计数。仅成功ACK记有效bytes，错误/取消另列。默认完整任务47904事务/191616B，不把阶段跨度相加当总耗时。

目前只新增了 `tb/arch03_dma16_bus_metrics.sv`，**还未编译/仿真，不能标通过**。端口为clk/rst_n/task_arm/task_cancel/task_end；DMA cmd_valid/ready/addr/read/wdata/wmask+rsp_valid/ready/err；CPU cmd_valid/ready；arb cmd_valid/ready/rsp_valid/ready。全为input，不驱动DUT。

实现草案：四phase固定合法地址/长度，首次offer在实际valid/payload发送事件捕获cycle（连续同payload valid由negedge补捕获）；每phase3项stats＋9hist bins=[0],[1],[2],[3],[4..7],[8..15],[16..31],[32..63],[64+]。成功末outputACK冻结测量，晚task_end只发布；CANCEL保留已发未接受请求的测量到排空，error ACK单列并停止新请求。会检查held payload、单outstanding、孤立响应、DMA/CPU与arb所有权。支持命令同拍响应和前一响应同拍后一接受的ledger。输出HEADER/4PHASE/12STAT/4SWITCH/CONTENTION/END行。

已自行审查并在首次测试前修正：global ledger ACK+新CMD同时拍更新用old_global_pending，不能清零后再判断；无效rsp时不要求rsp_err已知，仅有效payload检查。所有RTL仍未验。

接下来必须完成：
1. 新 `scripts/dma16_bus_metrics.py` 严格解析以上行、直方图/和/计数一致性、默认47904/191616；可显式allow_partial验证取消/错误，不冒充完整任务。
2. 新tb协议夹具建议实例真实arch03_icb_arb2＋可控延迟响应模型，DMA驱动和CPU竞争。独立记录offer/accept/ACK时间oracle供Python复算，避免只用实现自身统计自证。
3. 小取消反压、错误ACK例；1个无MAC的47904全事务例（不用全14）；heldpayload变更、接受第二在途、孤立响应负测。仅本地XSim，保留失败日志新目录，不改DUT。
4. 接口/绑定生成器：RTL使用现有DMA/CPU/arb信号，gate使用已实测probe的accel.dma_*与arb.cpu_*、arb.cmd/rsp边界；taskarm/end跟原独立window。同出入前后配置的测量不拼接。
5. 完成后更新本交接、给root文件hash/测试回执/计量定义和限制。压缩后先读AGENTS、CONTEXT_HANDOFF、当前计划及本文件，再核对已有门级/功耗交接；当前无本代理运行任务。
