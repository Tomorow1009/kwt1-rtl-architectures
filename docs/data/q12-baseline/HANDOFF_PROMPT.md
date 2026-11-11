# 原版Q12架构优化交接提示词

请接手私人仓库 https://github.com/Tomorow1009/kwt1-rtl-architectures 的架构优化工作。本阶段先固定原版数值格式，不优化小数位数，不继续上传SHIFT16最差100条。

先同步仓库并阅读：
1. docs/data/q12-baseline/Q12_DATA100.md
2. docs/data/q12-baseline/Q12_CONVERTER.md
3. 仓库当前团队交接文档及最新架构实现；文档中的历史workspaces/arch02路径必须先确认存在，不直接假定最新版兼容。

使用的数据是最初100条验证集语音，不是后来的误差最大100条：
- 本地根目录：D:\FPGA芯片赛道\KWT1_FULL100_FLOAT_HEX_ARCH02_9dcde6b_20261108
- 本地HEX：上述目录\hex\sample_000001\layer_01，至sample_000100/layer_12。
- 原版HEX服务器地址（用户2026-11-11截图确认，注意IC为大写）：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex`。
- 原版第1条第1层：`/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex/sample_000001/layer_01/`，读取其中load.hex、total.hex、result.hex、saturated.hex。截图确认的是目录地址；接手运行前仍核对文件清单和哈希。
- 完整原版转换工具：原Codex工作区outputs/KWT_TO_HEX_TOOL_20261108.zip；数据包根目录也包含convert_hex.py及完整依赖。不要拿D:\转换脚本\convert_kwt1_fixed16.py当原版Q12转换器。
- Git仓库原版工具目录：`tools/kwt-q12-baseline/`。统一入口为`kwt_to_hex.py`，实际转换实现为`_support/convert_hex.py`；完整保留`_support/`及其锁定协议源码，不单独拷贝转换文件。从已有完整浮点数据转换：`python tools/kwt-q12-baseline/kwt_to_hex.py --from-float "<完整float目录>" --output "<不存在的新输出目录>"`。工具输出HEX位于新目录的hex子目录。原版工具始终生成SHIFT=12数据。

冻结协议：X/W signed16 F12，b signed40 F24，total signed41 F24，result signed16 F12；SHIFT=12，半值远离零舍入后饱和。load.hex先6336个X字，再32个8列组，每组512个W字+24个偏置字，总23488个16位字。每层四种HEX必须保留；total/result/saturated只用于检查，不参与DUT计算。

每条12层，每层X[99,64]×W[64,256]+b[256]，输出25344个；100条共30412800个输出。各层输入来自完整官方模型，不将上一层FFN1的输出直接作为下一层FFN1的输入。参考结果按row*256+column匹配，不能直接reshape RTL输出流。

先检查现有RTL的位宽、SHIFT配置、装载顺序及输出坐标，建立可复现Q12基线，再优化调度、并行度、缓存和搬运。若新架构只支持tile16/ICB32，明确做保持原整数值的Q12布局适配并独立回读验证；不得调用SHIFT16工具重新量化W/b。ICB保持32位。

每次改变架构后，以原始参考验证total/result/saturated逐位一致，检查坐标无遗漏重复，再比较性能。保持历史版本不变，记录源码、输入、配置、工具版本和结果哈希。历史100条软件通过、首条12层Icarus通过不算本轮新架构通过。

后续切换新版HEX：架构优化完成后，使用与RTL装载布局相同的新版完整HEX及其配套参考文件，数值配置只需将启动时的输出右移量从SHIFT=12改为SHIFT=16。新版已经完成量化：X signed16 F12、W signed16 F16、b signed40 F28、total signed41 F28、result signed16 F12；不需要再次转换HEX，也不需要改变这些数据的硬件位宽。RTL须保留可配置shift，驱动/testbench在start握手时传入16，并保持半值远离零舍入和饱和规则。

这里的“只改SHIFT”以装载布局一致、现有RTL支持shift=16为前提：原版8列流式接口可配同布局的新版未重排HEX；tile16/ICB32重排包须配匹配的装载器，不能仅靠修改SHIFT兼容。切换时必须一起更换load.hex和total/result/saturated参考文件，不混用新旧参考；单纯对原版HEX设置SHIFT=16不能得到新版数值结果。新版目录与本次原版服务器目录分开记录，不覆盖原版基线。

SoC计时遵循赛题答复：从输入和参数开始实际装载至结果写回完成，包含搬运、等待、调度及计算，不计PC文件读取和一次性格式转换。不要用预装SRAM或省略总线传输获得不公平性能结果。

首先报告：当前工程分支/提交、实际数据位置、Q12协议兼容性及最小必要适配。然后在独立分支推进，不覆盖旧数据与历史结果。
