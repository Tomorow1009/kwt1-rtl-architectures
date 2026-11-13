# N1单条完整浮点恢复试验：仅准备，尚未执行

本入口只服务当前N1完整浮点来源缺口，不修改硬件、量化、模型或阶段顺序。
根代理尚未授权执行模型，本次没有运行`prepare`或`probe`，没有导入TensorFlow。
已完成9项合成工具测试；测试仅验证来源闸门及全零数组的NPZ保存/回读，不是语音推理结果。

## 已确认与未确认的原格式

原交付说明`转换脚本和语音导出数据说明.md:82–86`明确：

| 文件内字段 | 原声明形状 | 原声明dtype |
|---|---|---|
| X | (12,99,64) | float32 |
| Y | (12,99,256) | float32 |
| logits | (1,12) | float32 |

PR #9转换器`arrays()`实际读取X/Y，但没有写原浮点NPZ的代码，不能由该读取顺序证明归档键顺序。
本机完整提取器`full_matrix_eval.py:240`保存的是X/Y_float/logits/audio，不能把它的原NPZ直接当作目标格式。
目前未取得原最差100条导出器的键顺序、压缩模式、NPY头部、batch和threads记录。

候选明确采用`np.savez_compressed(handle, X=x, Y=y, logits=logits)`，不会改变数组数值或dtype。
本机NumPy1.19.5的`npyio.py:689–722`按关键字插入顺序写各`.npy`，使用ZIP_DEFLATED、force_zip64和
`format.write_array`；Python3.8的`ZipInfo(name)`默认日期为1980-01-01。以上只是当前候选保存规则，
不证明缺失的原文件使用同样规则。候选报告记录实际ZIP成员顺序/CRC/压缩/时间、数组原始字节SHA、
NumPy/zipfile代码SHA与zlib版本；原文件SHA不一致时，不将容器差异自行豁免。

## 独立入口及执行前条件

脚本：`workspaces/arch03/scripts/n1_float_single_probe.py`。

- 默认`--mode prepare`只核固定文件身份并输出计划记录，不导入NumPy或TensorFlow。
- `--mode probe`必须显式给出独立服务器WAV连接回执和sample_001原NPZ SHA；缺项直接拒绝。
- 只允许固定首条`down/90645155_nohash_0.wav`，完整12层；没有样本数/样本号或扩展100条的选项。
- 固定现有`full_matrix_eval.py`及`numeric.py`SHA、36个官方源/权重文件、原共享W/b、
  100条音频哈希清单和首条WAV字节身份。复用同一提取函数及有效flags，禁止训练和增强。
- 候选配置为CPU、batch1、threads4、现有提取器seed20261109；这是本次单条试验配置，
  不宣称已经确认原最差100条的运行配置。
- 使用全新输出目录；已有目录/候选文件拒绝覆盖。失败保留identity、候选和failure信息。

服务器回执须来自实际同一输入比对，最小字段如下；这不是可以直接提交的通过模板：

```text
schema = n1-wav-source-join-receipt-v1
passed = 实际通过布尔值
checked = 100
mismatches = 实际差异数量
inputs_stable = 实际前后输入稳定布尔值
wav_hashlist_sha256 = 5da67b0f6acc1cf89ca6d14166845606731c1442e00d6c083a2fc540c9541b3c
server_manifest_sha256 = 9900a9bd1addbdeb256020ba9a04f4615791fbd5a624abd411364098c382c97e
sample_001_float_npz_sha256 = 从该固定服务器manifest实际读取的原值
observed_server_time = 实际观察时间
evidence_sha256 = 实际服务器摘要或截图SHA
```

根代理确认来源通过后，显式试验命令应填入实际回执、原NPZ SHA及新的输出目录：

```text
E:/fpga_race-two/.venv-kwt/Scripts/python.exe -B workspaces/arch03/scripts/n1_float_single_probe.py --mode probe --model-root E:/fpga_race-two/keyword-transformer --data-root E:/fpga_race-two/data2/speech_commands_v0.02 --upstream-receipt E:/fpga_race-two/model_data/upstream_verification.json --shared-weights local_runs/d1_full_matrix_600_20261109/parameters.npz --wav-hashlist E:/fpga_race-two/takeover_local/n1_selected100_wav_hashes_20261113_0648.json --source-proof <实际来源回执.json> --expected-npz-sha256 <原sample001文件SHA> --output <全新本地目录>
```

## 试验记录与严格停止规则

正式试验会核共享W/b逐位等于已核原文件，重复完整capture逐位一致，对原模型logits及全部12层
X×W+b进行既有浮点方向检查，再保存X/Y/logits候选。输出逐数组SHA、各层方向检查误差、有效flags、
模型/源码/数据身份及整个候选NPZ SHA。

**唯有候选完整NPZ SHA与固定服务器原sample_001的SHA完全一致，才能认定本条原浮点文件已恢复。**
不一致返回状态`candidate_npz_mismatch_stop`及退出码2，不自动改batch、枚举序列化或扩到100条。
量化HEX相同不作为替代条件。匹配时也仅本条通过，`complete100_recovered`和`n1_precision_accepted`
仍为false，后续100条需另行形成完整身份链。

原`n1_precision.py`的固定ZIP和逐文件检查没有修改。没有把新候选重新打包冒充原ZIP，
没有使用旧Q12精度结果，尚未进入N2。
