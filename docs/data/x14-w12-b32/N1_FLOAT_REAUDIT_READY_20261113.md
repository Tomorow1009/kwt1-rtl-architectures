# 完整100条浮点源核查与重审工具就绪记录

本轮没有取得完整100条浮点包，没有完成该批新精度验收，也没有操作VNC或服务器。

唯一接受的生产源包为`KWT1_WORST100_ORIGINAL_FLOAT.zip`，SHA-256固定为
`edb98e1dcb02a9e142a62161b2769b54cffae1cf2ba143d0210c776b46ec36d9`。

本地按WORST100、ORIGINAL_FLOAT、shared_weights、hex_short检索了本项目、
E/C盘用户Downloads、E/D盘fpga_backups，以及项目相关competition/worktree_archives目录，
未找到该包或共享权重加100完整矩阵。现有固定12/validation_first浮点矩阵不足以替代100条；
`KWT1_ALL_SPEECH_ORIGINAL_FLOAT_20261106.zip`的单坐标范围也不能替代完整矩阵。
这些是已查目录的结论，不推断电脑其他位置或队友电脑不存在该包。

GitHub只读重查PR #9：仍为提交`50c1261f3f7fafe1531e05e023aadd926cefa24a`，
4个修改文件，无issue评论或新的下载链接。正文和DATA100仍指向队友的
`D:\转换脚本\KWT1_WORST100_20261109\KWT1_WORST100_ORIGINAL_FLOAT.zip`。
连接器按完整文件名检索也未提供新位置。本轮未发送任何消息给队友或管理员。

## 新增工具

`workspaces/arch03/scripts/n1_precision.py`只读完整FLOAT ZIP和既有100条HEX，只在不存在的
新输出目录写审计结果。生产CLI强制100条，不使用原转换器的30条`--archive`入口。

```text
python workspaces/arch03/scripts/n1_precision.py \
  --archive <完整FLOAT ZIP> \
  --dataset <hex_short_all目录> \
  --dataset-manifest-sha256 <实际manifest.json完整SHA> \
  --output <新的独立精度审核目录>
```

`SHA256_FILES.json`固定SHA仍为`ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997`；
它不是`manifest.json`的SHA，二者不能混用。工具检查全部4800个HEX及来源、样本编号、12层形状，
使用固定PR转换器API重新量化，并以独立原坐标解码核对每个X/W/b。再用逐k整数参考检查
累加范围及total/result/saturation，重建四种HEX并逐字节比对原文件。

每条必须有同批完整Y[12,99,256]，缺少Y时失败，不通过重新猜测Y补齐证据。NRMSE从新结果和
同批Y重新计算；先按层合并SSE和参考能量再开方，不平均百分比。每层阈值3%，保留逐任务
误差、截限/饱和、来源NPZ/ZIP/清单/转换器/审核工具哈希。结束后重新检查原输入身份。

## 报告与阶段衔接

报告schema为`arch03-n1-float-precision-v1`。真正完成100条后才可能出现`status=passed`和
`internal_precision_verified=true`；仍明确`cpu_executed=false`、`official_precision_verified=false`。
本工具只证明同批新参考的精度，必须与本轮实际ASIC/E203 1200批量的dataset manifest、
inventory、numeric/layout身份绑定，才能作为N1阶段硬件精度证据的一部分。

当前只通过7项合成数据测试：一条完整12层的只读重审、生产100条拒收一条样本、错误ZIP/manifest
拒绝、即使X全零也逐坐标核权重、重新计算浮点误差、SSE/能量聚合、signed33及舍入极值。
合成样本报告只能是`fixture_passed`，且`internal_precision_verified=false`，不能冒充100条。

```text
python -m unittest discover -s workspaces/arch03/scripts -p test_n1_precision.py -v
```

完整100条浮点包一旦以固定SHA到位，可按上述新入口继续；此前整数/RTL工作可以继续，但新100条
浮点精度门槛维持未完成，不借用PR旧软件说明或B0精度作为本轮PASS。

## 02:06报告工具整合（本地完成，生产100条仍未审核）

`n1_report.py`现在可在原请求中增加可选字段：

```json
"precision": {
  "run": "<n1_precision生成的独立目录>",
  "sha256": "<该目录summary.json的完整SHA256>"
}
```

如精度审核目录从本地迁移到服务器，可另外提供`archive`字段指向服务器上的同一原始ZIP；
其SHA仍须完全等于固定源包，不能用另一份浮点数据替代。没有`precision`字段时，报告仍可
导出已有证据，完整100条浮点精度保持pending，缺失数值保持null。提供了不完整或不匹配的
证据则报错，不静默忽略。

实际通过自己的ASIC/E203 1200任务、30,412,800个total/result/sat后，报告才允许连接上述
软件精度证明。连接重新核对batch身份、全部4800 HEX清单、manifest、1200逐项坐标/源布局/
HEX身份、100条原始浮点矩阵及speech来源、共享权重、原始ZIP、转换器和审核脚本SHA，
并重新按层合并SSE和参考能量，核对截限/饱和与真实批量一致。此处不借用B0误差，不把软件
`cpu_executed=false`改写成硬件执行；硬件整数证明与新浮点证明分别保留引用。

固定12个性能任务另列`fixed12_precision`。报告用标准库重读随包提供的同B0原始FLOAT NPZ，
独立核X/W/b量化坐标、result/4096对原始Y的SSE/NRMSE及饱和。本地重核最大NRMSE仍为
0.1425636423408142%；这不能代替完整100条，也不是新的ASIC执行结果。缺固定12浮点证据时
该范围单独保留未完成。

报告同时读取已冻结并核SHA的`constraints.rpt`，列出DRC违例记录、类型、未解析行和明确
无违例标记。即使精度或DRC清单通过，`stage_handoff.allowed`、严格时序/面积归属/系统功耗
与相对B0功耗准入仍不由本导出自动批准；门级total不可观察的范围也保持原样。

本地联合37项检查通过（报告22、原始精度7、DRC8）。报告导入与固定12读取无需NumPy；
生产100条重新量化工具本身仍需要NumPy。测试回执：
`workspaces/arch03/local_runs/n1_report_precision_toolcheck_20261113_020524/summary.json`，
SHA-256 `b9a83bbb5a19634791f04064dbed01bbc66f80a0bd277566128ea17ca5bae480`。
合成元数据测试明确mock了另行受测的HEX清单入口，不作为实际CPU或100条生产精度PASS。
