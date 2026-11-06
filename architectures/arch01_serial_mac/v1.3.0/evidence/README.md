# v1.3.0 验收证据

原运行：`D:/IC_compeyition/Fast_coding/sim/full_matrix_kwt1/20261106_202300_448dcc0e`。只归档最终通过运行；此前中断试运行不计入验收。

- acceptance.json：综合验收。
- summary.json：逐作业结果及受测源码哈希。
- software.json：完整软件结果、源 NPZ 与生成 HEX 哈希。
- iverilog/、xsim/：逐层原始 CSV、实际 NPZ、主作业与波形作业文本日志。
- compatibility/：原向量、单样本及批量抽样回归证据。
- negative_tests/：故障检测摘要与文本日志，不含故障数据副本。
- package_sha256.json：此次发布文件的 SHA-256。

JSON 内容保留原始路径与运行编号。原 `.log` 文件仅改名为 `.txt`，字节内容未改；JSON 中相应路径映射到本目录同名 `.txt`。生成的 HEX 和波形未上传，其哈希/运行记录保留，代码可重新生成。发布时已核对随附输入 NPZ 与本轮受测数据身份一致。
