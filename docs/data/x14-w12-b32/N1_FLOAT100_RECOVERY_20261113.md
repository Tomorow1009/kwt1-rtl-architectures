# N1完整浮点100条的精确恢复

2026年11月13日08:27:31，服务器将本机恢复的100个完整NPZ SHA-256与既有`hex_short_all/manifest.json`逐项比较：100条全部一致，排名、原WAV、split、WAV哈希及共享W/b也一致。原manifest SHA为`9900a9bd1addbdeb256020ba9a04f4615791fbd5a624abd411364098c382c97e`。证明见`handoff/team/evidence/N1_FLOAT100_SOURCE_RECOVERY_20261113.json`。

恢复严格使用已有官方模型、原始音频及固定推理环境，没有从HEX反推浮点、训练、改模型或重新排名。先验证sample001精确一致，再用同一profile恢复100条；每条完整X、Y、logits重复推理逐位一致，并核对全部162个模型变量及共享权重。所有100个NPZ共142,487,371字节。

**原`KWT1_WORST100_ORIGINAL_FLOAT.zip`容器仍未取得。** 不能将新的打包文件标成原ZIP，也不能复用原ZIP SHA。此次证明的是原始NPZ成员逐字节相同。新容器独立命名、独立SHA；原严格`n1_precision.py`入口不变。

新增`n1_recovered_precision.py`采用显式`exact_original_npz_members`来源：固定原manifest、100条顺序、101个成员集合、全部NPZ与W/b哈希；重新量化和独立整数参考，与实际四种HEX逐字节核对，再合并SSE/参考能量计算逐层NRMSE。不能以恢复身份本身宣告精度通过。

最终`n1_report.py`仅在显式选择该来源、给定新容器SHA、完整软件精度和本轮真实ASIC1200同时存在时连接精度证据。它重新核对原manifest及每个成员，保留`original_float_archive_verified=false`，不借用B0误差，也不授予时序、面积或功耗验收。

截至本记录：本地恢复与服务器身份比较完成；新入口的数值/错误路径fixture通过。实际100条新精度运行尚未启动。N1硬件生产提交9305c694不变，N2尚未开始。
