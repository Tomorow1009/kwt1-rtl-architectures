# 原版 Q12 / SHIFT=12 转换脚本说明

配套数据：[100条原版语音数据说明](Q12_DATA100.md)。本工具保留旧数值协议，不使用校准后的W F16 / SHIFT=16，也不做tile16重排。

## 使用哪份工具

Git仓库已归档完整原版工具：[tools/kwt-q12-baseline](../../../tools/kwt-q12-baseline/)。统一入口为`kwt_to_hex.py`，原始转换实现为`_support/convert_hex.py`；随附完整依赖及原始README.txt。不要只下载一个py文件。

推荐完整工具包：`KWT_TO_HEX_TOOL_20261108.zip`，位于原工作区 `outputs/`，约43 KB。
SHA-256：`fc218e6fe8a858047a892806cd59c9a2c8ee013a995640c0ea803835e3ff2f27`。

已展开工具目录：
`C:\Users\Lucien\Documents\Codex\2026-10-23\https-mp-weixin-qq-com-s\work\kwt-to-hex-tool`

| 文件 | 作用 |
|---|---|
| kwt_to_hex.py | Python统一入口，原始WAV或已有完整浮点目录均可 |
| run_kwt_to_hex.ps1 | Windows便捷入口 |
| _support/convert_hex.py | 原版Q12转换实现 |
| _support/ | 提取、独立检查、锁定协议源码等依赖，必须完整保留 |
| samples_100.txt | 最初100条的固定样本名单 |
| requirements-lock.txt、README.txt | 环境与原始操作说明 |
| verification.json、SHA256_FILES.json | 工具历史测试及完整性记录 |

**不要只复制convert_hex.py一个文件。**它依赖check_hex.py、rtl_protocol.json、protocol_source及精确量化参考模块。
完整数据包根目录也有当时实际生成100条数据的convert_hex.py及依赖，可原样复现。

工具锁定提交 `8aa230695668458673b370bf85f8a397fc507a34`；历史工具记录说明相对数据包的9dcde6b仅交接资料变更，数值协议一致。
这不是自动适配任意最新RTL的工具。接手时先比较新RTL接口和数据布局。

## 已有浮点数据：推荐命令

在解压后的工具目录运行：
```powershell
python kwt_to_hex.py --from-float "D:\FPGA芯片赛道\KWT1_FULL100_FLOAT_HEX_ARCH02_9dcde6b_20261108\float" --output "D:\转换脚本\Q12_BASELINE_REGENERATED"
```

- --from-float：完整float目录，不是单个NPZ，也不是HEX目录；里面有manifest.json、shared_weights.npz、各sample目录。
- --output：新的输出根目录；输出HEX位于其hex子目录。目录必须不存在，避免覆盖已有数据。
- 此模式无需TensorFlow，但需要兼容的Python及NumPy，建议原Python3.8环境。

若使用完整数据包原始脚本，在该数据包根目录运行：
```powershell
python convert_hex.py --input ".\float" --out "D:\转换脚本\Q12_BASELINE_HEX_ONLY"
```
--input同样指完整float目录；--out直接是新的HEX目录。与统一入口的输出层级不同。

## 从原始WAV重新提取

在完整工具目录运行：
```powershell
python kwt_to_hex.py --model "<官方模型仓库根目录>" --audio "<speech_commands_v0.02目录>" --sample-list ".\samples_100.txt" --output "<不存在的新目录>"
```

--model需要官方源码及相匹配的checkpoint；--audio是WAV数据根目录；--sample-list固定原始100条及编号。
不是重新训练；运行官方模型，捕获各层FFN1的完整X/Y及共享W/b，再量化、编码和独立回读。
原始WAV模式使用Python3.8、TensorFlow2.4.0、tensorflow-addons0.12.1、NumPy1.19.5等；见requirements-lock.txt。
官方原依赖TF2.4.0rc1无法取得时曾使用2.4.0正式版，此差异已记入历史manifest。

## 生成内容与检查

X/W为signed16 F12，b为signed40 F24，total为signed41 F24，result为signed16 F12。
SHIFT=12，半值远离零舍入、signed16饱和。按原版8列分组生成load.hex；三种参考HEX为total/result/saturated。

独立检查单层（从完整数据包根目录）：
```powershell
python check_hex.py ".\hex\sample_000001\layer_01" --layer 1
```
需要该层完整文件，检查格式、哈希、布局，并从load.hex独立重算参考结果。

工具历史测试：一条WAV的12层；浮点目录模式48个HEX与原始模式逐字节一致；同样与原100条包首条一致。
本轮未重新执行模型导出或RTL仿真。原100条包的软件全量历史证据见reports/AUDIT.json。

## 若官方只给一条语音的一层

原版入口要求12层完整目录协议，**不能直接输入任意单层NPZ**。
单层完整X[99,64]、W[64,256]、b[256]已经足够生成该层load及整数参考；不需要其他层。
届时新增明确的单层适配入口、冻结量化规则并验证即可，不能补零/复制伪造12层。
只有局部点积或Y[0,0]的数据不足以恢复完整矩阵。

## 交给服务器的内容

已有HEX用于RTL仿真时，上传每层四种HEX和必要的layout/清单即可；无需重新运行官方模型。
要在服务器从浮点重转HEX，则上传完整工具及float目录，并准备NumPy环境。
厂商SRAM、RTL/testbench、SoC驱动属于另一个工程交付范围，不包含在这个转换工具包内。
