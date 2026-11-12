# N1同批语音来源：有界只读核对与恢复条件

记录日期：2026-11-13。本轮只核查现有文件、依赖安装元信息及提取源码，没有导入TensorFlow、
运行模型、重新量化、下载音频、训练或全盘寻找ZIP。N1完整100条浮点精度仍未验收。

## 当前可用条件

- 本机`E:/fpga_race-two/data2/speech_commands_v0.02`包含原语音目录。目标首条
  `down/90645155_nohash_0.wav`实际存在，17792字节，SHA见配套身份JSON；其余99条尚待映射核对。
- `E:/fpga_race-two/keyword-transformer`内官方模型源、flags及checkpoint存在；
  本轮对上游回执列出的36个文件逐项重哈希，均与固定上游身份相符。
- `.venv-kwt`安装元信息为Python3.8.20、TensorFlow2.4.0、tensorflow-addons0.12.1、
  NumPy1.19.5、protobuf3.20.3。仅查看安装元信息，不等于本轮推理或运行时健康检查通过。
- 本地旧完整600条的`parameters.npz`与新100条清单的共享W/b SHA相同。
  旧600条均来自validation，不能替代目标83条training、13条testing、4条validation的X/Y。

已有音频、模型和依赖使恢复尝试具备基础，但没有据此证明能生成与原100份浮点NPZ相同的字节。
原完整FLOAT ZIP仍未取得。FTP对其已有HEX清单下载返回550 Permission denied，本轮不修改权限，
也不启用另一下载通道。以下方法只上传本地路径索引，在服务器读取比对摘要。

## 小索引与只读脚本

现有`model_data/outputs/all_speech_dot00/samples.csv`含105829条路径、划分和文件大小，
固定SHA为`1aea9aa75107cde96e2adad290f2d8f8fafb78be89f009f8e6ae9f514fcba09d`。
它不含WAV内容哈希，也不是本次最差100条榜单。本轮仅从该既有CSV按原sample_id顺序提取
相对路径与split，得到`audio_index.json.gz`；索引号从0开始。

压缩索引403722字节，保留于本机ignored目录
`E:/fpga_race-two/takeover_local/n1_float_source_index_20261113_v1/audio_index.json.gz`，不加入Git。
其SHA、解压SHA、脚本及源回执身份记录于
[身份摘要](N1_AUDIO_SOURCE_INDEX_IDENTITY_20261113.json)。文件中没有音频、浮点数组或HEX。

工具为`workspaces/arch03/scripts/n1_audio_path_join.py`，只依赖Python3.6以上标准库。
原服务端清单固定为`hex_short_all/manifest.json`，SHA为
`9900a9bd1addbdeb256020ba9a04f4615791fbd5a624abd411364098c382c97e`。
脚本核对压缩及解压索引身份、100条编号/原排名/路径/split、重复和缺失、源哈希格式以及共享W/b身份；
在处理前后再次核两个输入的SHA。它不写文件、不读取WAV、不调用EDA或模型。

在根代理核验OPS包及实际解包路径后执行：

```text
python3 -B <OPS>/scripts/n1_audio_path_join.py --index <OPS>/audio_index.json.gz --manifest /storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_short_all/manifest.json
```

输出仅包括匹配摘要、按sample_001到sample_100排列的两行各50个索引号和来源哈希，
不打印完整原manifest。`passed=true`仅表示路径/排名/划分连接成功；
`wav_bytes_verified=false`、`float_source_recovered=false`始终明确保留。
9项本地合成夹具通过，不是实际服务器数据比对结果。本记录写入时尚未执行服务器脚本。

后续可据实际100个索引在本机只读取对应100个WAV，检查安全路径、PCM格式、文件SHA和官方划分；
将其小型哈希清单上传，在服务器与原manifest逐项比对，避免重新读全部105829份语音。
精确音频身份通过也仍不是完整浮点矩阵恢复通过。

## 提取入口和剩余真实性条件

- `model_data/scripts/extract_kwt.py`的CLI限制validation，且是逐条eager导出，不能原样覆盖本批100条。
- `model_data/scripts/batch_runtime.py`只捕获X[0,:]/Y[0,0]，不满足完整99×256矩阵要求。
- `workspaces/arch03/scripts/full_matrix_eval.py:90`的`build_runtime`可捕获12层完整X/Y；
  其CLI仍固定600条validation，不能直接作为目标100条入口。已有代码对不同batch大小只作allclose，
  对同配置重复单条才检查array_equal，不能保证换批量配置后浮点逐位相同。
- 原新100条manifest提供每份`float_tensors.npz`的`sample_sha256`和每个WAV的SHA，
  没有原提取batch/threads/有效flags/脚本哈希及独立X/Y数组哈希。不能由相同HEX反证相同float。
- 完整恢复应首先匹配原100份NPZ逐文件SHA；若仅NPZ容器不同，则需要取得原数组哈希及明确序列化依据，
  不能自行把哈希不符当成浮点等价。原共享权重文件已匹配，不解除逐语音X/Y来源条件。
- 当前`n1_precision.py`还严格绑定原ZIP完整SHA。即便以后恢复原NPZ，另打包ZIP也不能默默替代该输入；
  如采用独立恢复审计入口，须单独记录来源和完整逐文件身份，保留原检查不变。

截至本轮：未导出新浮点矩阵、未生成替代FLOAT ZIP、未执行100条浮点精度验收，
未改N1 RTL/量化/计时契约，未进入N2。原浮点源问题仍保留。
