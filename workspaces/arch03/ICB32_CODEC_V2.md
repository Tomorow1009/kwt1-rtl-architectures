# 无损传输格式v2

本格式仅改变原tile16的X/W传输表示；Q12与输出编码不变。所有多字节值小端，所有流与块按4B对齐；位载荷按元素顺序低位先放。压缩字必须真实写共享SRAM且成功ACK后才交给解码器。

32B总头为8个uint32：magic=0x3243574b（KWC2），version=0x00020000，layout=0x00100002，flags（0=分块，1=整流原始，其余非法），total_bytes（含头），decoded_halfwords=23488，raw_bytes=46976，reserved=0。长度必须匹配配置、4B对齐、<=47008。

分块模式依次99个X块，然后16个tile；每tile16个W块（k→lane）和96B原始bias。每块64个signed16，头uint32 bits4:0=有符号位宽1..16，bits10:5=元素数减1，bits31:11必须0。通用块函数支持1..64，但本任务X/W各块必须64。载荷占4*ceil(count*width/32)字节，元素是width位补码，高位填充必须0；符号扩展恢复16bit。bias每个三半字、第三半字仅低8bit有效，不作符号扩展填充。

整流原始模式头后为原46976B tile16流；压缩体>=原体时编码器自动选择该模式。因此合法输入最坏47008B，小于现输入至输出49152B间距。原始块本身由width=16表示。

拒绝magic/version/layout/flags/保留位错误、长度不符、非法位宽/元素数、非零填充、截断和多余载荷；不把错误流标为DONE。编码器只接受原始整数流，不改尺度、舍入或饱和。

软件入口scripts/icb32_codec.py：--raw-tile16 <load.bin> --output <新目录> [--force-raw]。输出load.bin、load32.hex及codec.json；只有前两者是硬件运行输入，不含参考输出。软件通过不代表RTL/E203或PPA通过。
