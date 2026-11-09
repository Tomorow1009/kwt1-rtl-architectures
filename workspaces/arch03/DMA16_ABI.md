# DMA16 最小寄存器 ABI（开发中，2026-11-09）

模块 `arch03_dma16_accel`，MMIO 基址默认 `0x40000000`，4 KiB 窗口，所有寄存器为对齐 32 位；写必须 `wmask=0xf`。单笔 MMIO 应答在反压期间保持。只读项写入、未知地址、未对齐或不完整写返回 ICB error，并保留首错。配置仅任务空闲时可改。IRQ_ENABLE/IRQ_STATUS 可在忙时访问。

| 偏移 | 名称 | 语义／复位值 |
|---|---|---|
| 00 | ID | `0x4b575416`，16-lane 版本，不是旧8路布局 |
| 04 | CONTROL | 写1 START；写2 CANCEL；写4 CLEAR。不是可组合位掩码 |
| 08 | STATUS | bit0 busy；1 core.load_ready；2 core.out_valid；3 sticky done；4 error；5 cancel_pending；6 aborted；7 master响应在途；8 master命令待接受；9初始装载全部写ACK；10 core.done已见；11半个输出待配对；12输入32位缓冲有效；13 core.busy；14 core.start_ready |
| 0c | SHIFT | 0–31，默认12 |
| 10 | LOAD | 仅 MODE bit0=0：低16位流输入，高16位须0；仅core.ready时合法 |
| 14 | OUTPUT | 仅 MODE bit0=0：读并消费 `{sat,column[7:0],row[6:0],result[15:0]}`；仅out_valid时合法 |
| 18 | LOAD_COUNT | core实际接受的16位元素数，完整23488 |
| 1c | OUTPUT_COUNT | core实际交付的16位输出数，完整25344 |
| 20 | FIRST_ERROR | 首错码，见下；CLEAR后归零 |
| 24 | MODE | bit0 DMA（1）/MMIO debug（0）；bit1权重预取；默认3 |
| 28 | SOURCE_BASE | 默认`0xb0000000`，加载源地址由SoC路由实现，须在原平台核验 |
| 2c | INPUT_BASE | 默认`0xa0000000` |
| 30 | OUTPUT_BASE | 默认`0xa000c000` |
| 34 | INPUT_BYTES | 默认46976；本版只接受此长度 |
| 38 | OUTPUT_BYTES | 默认50688；本版只接受此长度 |
| 3c | LAYOUT | `0x00100001`：tile16，布局版本1，本版只接受此值 |
| 40 | IRQ_ENABLE | bit0完成、1错误、2取消排空完成；默认0 |
| 44 | IRQ_STATUS | 同上sticky，写1清对应位；硬件当拍新事件优先 |
| 48 | FIRST_ERROR_ADDR | DMA错误为对应命令地址，MMIO/配置错误为拒绝的MMIO地址；core错误为诊断地址 |
| 4c | FIRST_ERROR_PHASE | 1 MMIO，2配置，3源读，4初始共享写，5共享读供core，6 core，7结果写，8总线协议 |
| 50 | LOAD_COMMITTED_BYTES | 初始源→共享搬运的成功写应答字节数 |
| 54 | OUTPUT_COMMITTED_BYTES | 成功输出写应答字节数 |
| 58 | PENDING | bit0待接受命令；1在途响应；2初始copy数据；3输入word缓冲；4半输出；12:8结果FIFO个数；19:16命令kind；27:24引擎state |
| 5c | COMPLETION | bit0初始全部写ACK；1全部core输入；2core.done已见；3全部输出写ACK；4master总线排空；5取消完成 |
| 60/64/68/6c | ACK_COUNTS | 源读／初始共享写／共享读／结果写成功响应数 |
| 70 | SAT_COUNT | core交付输出中的饱和个数 |

首错码：1 MMIO访问；2 core格式／状态；3启动配置无效；4源读错误；5初始共享写错误；6共享输入读错误；7结果写错误；8输出坐标／计数；9无已接受命令的总线响应（含命令仍被ready阻塞时提前响应）。合法命令同拍接受及响应允许。错误使当前任务停止发新请求，保留尚未接受的valid命令，接收所有已有请求的响应后取消core。中途错误不得计为完成。

START需要idle、core.start_ready且无错误；驱动在CANCEL/CLEAR后须等待STATUS bit0=0、bit14=1，避免core取消/flush流水尚未完成。START清上次done/aborted/IRQ和任务计数，不隐式清错误。CANCEL停止产生新请求，但不撤回已经valid的请求；该请求握手及响应结束后，才脉冲core.cancel、清内部FIFO和有效位，置aborted及IRQ bit2。CANCEL保留已提交字节与首错供诊断。CLEAR仅idle且master排空时允许，清首错/done/aborted/IRQ并再次使core失效；不清历史计数，下一次START清计数。同拍新错误优先于CLEAR。

DMA：START先进入PREPARE（state=6），使core.cancel失效旧X/权重valid并等待flush/start_ready，然后才发出首个源请求；纯有效位清理在输入传输计时前。全部源数据经过实际源读响应→共享写响应（11744个32位字），然后从共享读取、每word低半字先送core；计算期间共享输入读取和结果写出公平交替，单在途，允许与core计算及独立权重bank装载重叠。输出按core的tile→row→lane顺序核验，相邻两列打包为一个全字，硬件生成行主序目标地址，16×32位结果FIFO另存地址。DONE只在全部输出写成功响应、core完成、缓冲和总线排空后置位。

MMIO debug：START/LOAD/OUTPUT语义沿旧接口，但输入为16-lane布局；无DMA命令。若CPU先装载共享SRAM再START core，驱动必须在首个输入源请求前CANCEL并等busy=0、start_ready=1，保证旧缓存valid先失效。DONE沿旧语义在最后OUTPUT被读取后置位，CPU的最终共享写响应仍须由系统计时观察器确认，不能用此DONE替代完整任务结束。

布局：X为6336个16位元素，随后16个tile；每tile有1024个W元素（k→lane）、16个40位bias（每bias低16、中16、高8且高字其余8位为0），共23488 halfwords。使用little-endian 32位打包。DMA地址均4字节对齐；输入/输出必须完整落在512 KiB共享区且互不重叠；源范围不得溢出或与输入/输出重叠。本模块不假定源实际存在，源总线error必须被传播。

`rst_n` 是整个互连共同复位，必须同时取消外部总线事务；软件中途取消必须使用CONTROL=2，不能仅单独复位DMA模块而保留外部事务。外部响应缺失时取消也不能假装排空完成，系统超时处理须报告真实未完成状态。
