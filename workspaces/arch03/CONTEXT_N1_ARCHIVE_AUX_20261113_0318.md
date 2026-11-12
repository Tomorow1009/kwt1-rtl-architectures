# N1只归档辅助回执修订检查点

有效路线仍为N1→N2→D1→D2。已在压缩后重读实施计划与03:13归档检查点。
本子任务仅修独立归档工具，不操作VNC/服务器，不修改运行中OPS、n1_paths、RTL或root文件。

发现41b OPS的b0_inventory01/02已完成只读收集，但没有N1 state，旧终态检查会阻止完整归档。
已新增请求auxiliary_runs显式绑定每个绝对run路径与inventory.json SHA。仅接受已知B0只读
schema与inventory_rejected/read_only_inventory_collected_review_required两个终态，核false功耗验收
与对应error/只读标记；不能覆盖N1 state。未知缺state仍拒绝；全部文件保留归档，不排除任何内容。

本地19项测试通过（9.846秒，exit 0）。工具SHA：
e8664a5f9ff537b67ea99d2611e0c3786b938217d8b55a2c3e59b7039d85c141。
测试SHA：c9c24eacb676fe86a36a1d90fb3a3a19611bec23bad0c44fc646303b9ad08423。
回执：local_runs/n1_archive_runtime_toolcheck_20261113_031850/summary.json。

未做：真实Linux归档、迁移验证、删除/tmp、硬件或功耗验收。root须提供01/02原回执实测SHA，
待全部指定源终态、团队锁空闲及无进程占用后再启动。源仍运行时不得归档。
无提交、上传或服务器操作；原路径、原回执及原阶段闸门保持不变。
