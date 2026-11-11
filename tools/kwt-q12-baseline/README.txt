KWT-1 原始语音/完整浮点数据 -> arch02 HEX，一条命令入口

功能
读取官方预训练模型和原始WAV，执行官方推理，捕获12层FFN1完整浮点X/Y，
保存共享W/b，量化并生成现有RTL协议HEX，独立回读HEX并核对全部矩阵结果。
另一模式可直接读取已经导出的完整浮点数据，无需再次运行模型。
不训练模型，不修改官方数据、RTL或旧导出目录，不进行RTL/SoC仿真。

当前支持的RTL
私人仓库 Tomorow1009/kwt1-rtl-architectures
main提交 8aa230695668458673b370bf85f8a397fc507a34，开发目录 workspaces/arch02。
相对此前9dcde6b仅交接记录更新，RTL及数据协议未变。
这是固定且验证过的协议版本，不会悄悄追踪未来Git变更。
可加 -RtlRepo <本地完整私人仓库根目录> 核对RTL/协议源文件；不匹配会在生成数据前停止。
HEX对应arch02_linear的16位流式装载接口，不是尚未定义的E203内存映射。

本机使用（PowerShell）
进入本工具目录，执行：
  .\run_kwt_to_hex.ps1 -Count 100
默认从 D:\FPGA芯片赛道 自动查找模型根目录（支持ZIP双层目录）和语音目录，
输出到本工具目录下runs/新时间戳目录，不覆盖之前100条数据。
默认选验证集，约90%为十个目标词，10%为其他词；优先不同说话人，不生成静音。
Count=100与此前100条导出使用相同确定性选样规则。

明确指定输入、输出：
  .\run_kwt_to_hex.ps1 -DataRoot 'D:\FPGA芯片赛道' -Count 100 -Output 'D:\FPGA芯片赛道\新HEX结果目录'
  .\run_kwt_to_hex.ps1 -Model '<官方仓库根目录>' -Audio '<speech_commands_v0.02目录>' -Count 10
输出目录必须不存在。请选择有写权限、磁盘空间足够的位置。

指定之前同一批100条样本：
  .\run_kwt_to_hex.ps1 -SampleList '.\samples_100.txt'
指定训练集样本用于后续标定输入准备：
  .\run_kwt_to_hex.ps1 -Split training -Count 100
当前脚本始终使用现有Q12配置，不会利用所选样本调整量化参数。
正式评估按组委会样本/静音规则另行组织，本工具的默认选样不是官方600条名单。

已有完整浮点数据 -> HEX（不用TensorFlow，只需NumPy）
  .\run_kwt_to_hex.ps1 -FromFloat '<完整数据包里的float目录>' -Output '<新的输出目录>'
该模式转换所给目录的全部样本，不重复复制浮点文件，并在status.json记录原浮点路径和哈希。
支持我们新导出的kwt1-full-ffn1-float-v1格式，不能把旧的仅Y[0,0]数据包补成完整矩阵。
不支持直接把任意NPZ/WAV ZIP当作已知浮点协议，需先解压并使用正确目录。

直接使用Python入口（Windows/Linux）
  python kwt_to_hex.py --model <官方仓库根目录> --audio <语音目录> --count 100 --output <新目录>
  python kwt_to_hex.py --from-float <完整float目录> --output <新目录>
  python kwt_to_hex.py --help

环境
原始WAV模式：Python3.8、TensorFlow2.4.0、tensorflow-addons0.12.1、NumPy1.19.5、protobuf3.20.3。
首次在新电脑安装：用Python3.8创建本目录.venv，再在其中安装requirements-lock.txt。
  <Python3.8解释器> -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
也可用 -Python '<已安装环境的python.exe>' 指定解释器。
本机脚本会优先寻找本工具.venv或已有的相邻kwt-export/.venv。
官方requirements指定2.4.0rc1当前无法从包源获取；本流程使用2.4.0正式版，差异写入manifest。
工具包不包含官方模型、全量语音数据、Python环境、厂商库。

输出
status.json：总状态、受核对RTL版本、运行配置、文件哈希和数值误差；成功时status=passed。
logs/：原始提取和转换日志；出错保留部分结果并返回非零，不用旧PASS掩盖失败。
selection/：样本清单及身份；仅原始WAV模式生成。
float/shared_weights.npz：W[12,64,256]、b[12,256]。
float/sample_000001/float_tensors.npz：X[12,99,64]、Y[12,99,256]、logits，依次到所选样本数。
hex/sample_000001/layer_01/：每条语音12个完整FFN1任务。
完整X/Y来自对应编码模块内部FFN1入口/出口，不是整个编码器入口/出口。

每层HEX
load.hex：输入X、权重W、偏置b，共23488个16位字，交给DUT。
total.hex、result.hex、saturated.hex：完整参考结果，每种25344个，仅用于检查。
expected.npz、layout.json、hex_check.json：参考矩阵、协议/哈希和独立回读验收。
先行优先发送X的6336个字；随后每个8列权重组发送512个W字及24个偏置字，共32组。
偏置以低16位、中16位、高8位发送，最后一字上8位必须填0。
start握手时shift=12；装载必须遵守load_valid/load_ready。
X/W为signed16 Q12，b为signed40 Q24，total为signed41 Q24；半值远离零舍入并饱和为signed16。
result实际数值=result/4096。RTL输出按group->row->lane；参考矩阵按行排列，必须按row/column比对。

保留完整_support目录：里面是提取/转换模块和Git锁定的协议源文件，入口依赖这些文件。
一条语音的数据规模约10MB；100条结果约1GB，视语音与压缩效果略有变化。
