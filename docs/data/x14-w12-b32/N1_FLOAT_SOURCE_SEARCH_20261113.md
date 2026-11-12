# N1完整100条浮点源排查记录

记录日期：2026-11-13。范围是现有本地资料、旧数据目录及根代理提供的服务器只读查询结果。
本轮没有重新生成浮点矩阵、重建ZIP、下载数据、修改HEX或调整精度验收条件。

## 结论

**完整100条原始浮点源仍未找到，N1完整100条浮点精度重审保持未完成。**

服务器HEX清单中的共享W/b文件SHA与本地旧完整矩阵批次的`parameters.npz`完全相同，
这解决了共享参数的身份对应；不能替代缺失的逐语音X/Y。目标100条含83条training、
13条testing和4条validation，而旧本地600条全部来自validation。因此旧批次不可能补齐
至少96条training/testing的X/Y；另外4条是否与旧600条重合尚未逐项核对，不能称已找齐。

仍需原始文件：`KWT1_WORST100_ORIGINAL_FLOAT.zip`。

固定SHA-256：
`edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9`。

## PR #9与原交付说明

PR #9固定提交为`50c1261f3f7fafe1531e05e023aadd926cefa24a`。本地
`DATA100_X14_W12_B32.md`与`CONVERTER_X14_W12_B32.md`记录原始ZIP位于队友电脑：

`D:/转换脚本/KWT1_WORST100_20261109/KWT1_WORST100_ORIGINAL_FLOAT.zip`。

它包含共享`shared_weights.npz`，以及sample_001至sample_100各自完整12层X/Y、source.json
和语音来源记录。HEX数据保持原SHIFT16最差100条的榜单顺序，并未按N1重新排名。

本机`E:/UserData/LENOVO/Downloads/转换脚本和语音导出数据说明.md`第34行明确给出
training 83、validation 4、testing 13；第176行说明重新导出的100条完整浮点数组与当时扫描
数组哈希一致。这是来源说明，不能代替取得实际浮点文件并核验。该说明引用的同目录
`KWT1_WORST100_20261109`子目录和`最差100条语音榜单.md`均未找到；本机
`D:/转换脚本`也不存在。

## 本地完整600条候选

实际存在目录：
`E:/fpga_race-two/kwt1-rtl-architectures/local_runs/d1_full_matrix_600_20261109`。

600个`dev_*.npz`文件均存在。抽查`dev_000000.npz`、`dev_000599.npz`确实含
float32的X[12,99,64]、Y_float[12,99,256]，以及logits/audio；`parameters.npz`
含float32的W[12,64,256]和b[12,256]。这是真实完整矩阵来源候选，不是单坐标点积档案。

但`samples.json`表明其抽样是seed 20261109、validation内每个目标词50条、99条unknown，
再加1条规范零静音。这与目标100条的全语音最差榜单不同，不能直接沿用编号或误差结果。

| 已检查文件 | SHA-256 |
|---|---|
| samples.json | `80e9ea7de8f0412ce222310f0e84f2c32022b440bbed5c61d7830fa0879c9b11` |
| parameters.npz | `99a3f2d990203b2bd9f3bdf5dc98974d6a7102027f7d67b9abf19e72ee03a6ad` |
| dev_000000.npz | `78eee931c58df79e24b9a8a3c730c73e2f431e7c8e8287c8a0d3320f1110c2d3` |
| dev_000599.npz | `e606b3a1d17a4061867e9b0fa93fdb76025dc3537d016db9c56a4658225e389b` |
| evaluation.json | `8832e338ecdf383a68266ca32da1b522b77c631df86db7291688dd4830b50934` |

上述参数和两个抽查样本的实际文件SHA与旧evaluation记录一致。本轮未对600个NPZ逐一重哈希，
也未重新执行旧600条计算；旧Q12 SSE/NRMSE不用于N1精度验收。

## 服务器HEX清单只读核对

根代理于03:50:29读取服务器`hex_short_all/manifest.json`，证据截图名为
`n1_data100_manifest_identity_0352.png`，随后将结果回传本记录代理：

- 样本划分：training 83、testing 13、validation 4。
- `weights_sha256`：`99a3f2d990203b2bd9f3bdf5dc98974d6a7102027f7d67b9abf19e72ee03a6ad`。
- sample_001来源：`down/90645155_nohash_0.wav`，划分training。

这与本地参数文件SHA及原交付说明的划分一致，但尚未提供完整100条原始X/Y或固定原ZIP。
本记录代理没有另外操作VNC、读取服务器或重复该查询。

## 其他路径及排除依据

- 固定`real_sample_001`和`validation_first`保留少量完整12层矩阵；抽查同层NPZ哈希相同，
  不能把目录副本数当成不同语音数量，也不构成目标100条。
- `d1_precision_cases_20261109`是旧开发批次的固定12层与少量极值选例，不是新100条。
- `d1_decoded_worst_20261109.npz`只有旧RTL结果解码的Y_decoded、result_int、saturated，
  不含原始X/W/b/Y；不能从已量化输出恢复完整浮点源。
- `model_data/outputs/all_speech_float_original`及ALL_SPEECH说明明确仅保存每层Y[0,0]
  对应的X[0,:]、W[:,0]、b[0]。batch_smoke抽查形状也只有每语音每层64输入和单个输出，
  无法替代99×256完整输出矩阵。
- 在既定项目输入目录、已知本地运行目录和Downloads的窄范围检索中，没有找到原ZIP或
  可补齐目标100条的原始矩阵集合；本结论不声称扫描过整台电脑的全部磁盘。

## 恢复入口

后续应取得上述固定ZIP的实际本地或服务器路径，再核完整SHA、100条样本身份、共享参数、
每条原始X/Y与现有HEX清单。已准备的`workspaces/arch03/scripts/n1_precision.py`负责
从原浮点重新量化、核对全部HEX与独立整数参考、重算逐任务及逐层误差；不能仅抄manifest
现有分数。`n1_report.py`只有在实际N1自有1200任务与严格精度证据身份一致时才合并结果。

本次没有改动这些脚本或放宽固定ZIP检查。完整100条浮点精度未验之前，继续保留该缺口；
固定12任务的已有浮点检查、整数回归及旧B0结果分别按自己的范围报告，不转移为新100条PASS。
