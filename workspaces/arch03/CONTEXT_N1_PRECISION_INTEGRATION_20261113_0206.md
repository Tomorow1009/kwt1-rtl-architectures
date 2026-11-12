# N1精度及报告整合检查点（子任务，2026-11-13 02:06）

继续遵守`IMPLEMENTATION_PLAN_N1_N2_D1_D2_20261113.md`的阶段闸门。这里只记录
requirements_plan_audit子任务；服务器、ASIC、归档进度以根检查点和实时回执为准。

## 已完成

- N1数据/编码/1200入口、PR固定转换器导入、33位total及5列capture、14组本地数据与独立工具检查已交接。
- 精确R4 L01无损归档工具及12项本地检查已交接；本代理没有执行服务器删除或归档。
- 按固定ZIP SHA寻找完整100条浮点源，本地已查相关目录和PR#9仍未取得；未联系外部人员。
- 新`n1_precision.py`可读完整100 FLOAT ZIP+原HEX，用固定PR转换器与独立整数模型重算，7项合成测试通过。
- 本轮独占修改`n1_report.py`/`test_n1_ppa_tools.py`：连接可选严格精度证据至已通过的自身ASIC1200，缺证据保持pending；固定12同B0浮点单独从原NPZ复核；新增冻结DRC报告清单。
- 本地联合37项工具检查通过，目录`local_runs/n1_report_precision_toolcheck_20261113_020524`。summary SHA为`b9a83bbb5a19634791f04064dbed01bbc66f80a0bd277566128ea17ca5bae480`。
- 固定12软件重新核得最大NRMSE 0.1425636423408142%，不是100条精度，不是新的CPU运行。
- Report仍禁止自动N2准入；严格时序、面积归属、未知活动功耗及B0功耗准入均独立。门级只核result/sat，不伪造total。

## 未完成与恢复入口

完整100浮点包尚未取得，因此生产float100审核未执行，不能宣布新100精度通过。根代理负责
当前ASIC/EDA实跑、工具打包部署及Git提交；本代理没有提交、上传、操作VNC或改变运行包。

浮点到位后按`docs/data/x14-w12-b32/N1_FLOAT_REAUDIT_READY_20261113.md`运行新的精度入口，
保留原始HEX。真正完成自己的ASIC1200后，报告请求增加`precision={run,sha256}`；迁移ZIP可
指定同SHA的`archive`路径。必须配合同一batch、manifest、inventory及逐任务源身份，不能
把旧B0或PR软件说明代替硬件PASS。

恢复后先重新读计划、本检查点和根最新检查点；检查上述两个工具文件是否已由根冻结，避免
修改已投入运行的工具身份。既有测试日志和数据不删除，不重启旧B0/8路/R1任务。
