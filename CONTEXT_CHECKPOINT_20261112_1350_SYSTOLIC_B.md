# B 接续检查点：2026-11-12 13:50

任务 ACTIVE，继续直接B计划。源冻结63da6ba/v3/credits3，不增架构。R4保底。用户授权清理完成后继续；FTP421用户确认没有队友使用，不重复询问。工作区3，禁止工作区4。

## 已完成

- B ASIC14、CPU恢复/竞争及原synth02无SDF gate14通过。平均30502.3333周期、4917.6566task/s；自己的1200未运行。详见1320检查点。
- 两次旧MMIO8 L03–L12波形清理共279.506GiB，已完成不得重复；R4/B、小证据与重建输入保留。
- bf55a29fcc022e33dd3f78d3f3a5e0a83a24564a已推送核对。8工具部署operations/systolic_b_tools_bf55a29，manifest484ec4c551ed1a0adf16d10b4f4b9a2cef957d11eeca18789be75892ef094103。11条差分命令全已执行，禁止重复append。
- 实际VCS SAIF 1e-15采集60ns已重解析通过，支持注释和整数小数duration；VCS将X/Z合于TX，不称分离或零未知。PT资格未过。
- structure05原synth02报告SHA aa035114a16290563657af24f74c336c819954f7d7f77091a012af12486b09d0，13067声明端口/263无负载对象全部匹配；其它LINT1=4/LINT32=12054/LINT33=1186未完全审定。

## 新失败和待办

DRC03因同名库不同文件身份OPT106/128/100失败，已结束。bf改绑定原DB路径，保留新副本供报告。

**DRC04 13:42:34.753709报告完成，但仍不合格。** ced包runs/systolic_b_v3_drc04/systolic_b_synth，PID211052已结束。summary SHA dd960574b5ac119192055932b7fadcf7e245fa97446d4370d8b6a49d4e990ca4；面积上界1.0975813687mm²、整机4619797.868661µm²、220宏/0锁存、setup+0.0002141ns、hold+0.00249085ns。4项transition约1.37>1.35ns；decoder/add_129/A[1]及sub_67/A[1]新增multiport_net。不能批准最终队列。

精确核心mapped.v查询：n5271由BUFV2RD_12TR40 U32684驱动/109关联cell，n5320同型U32686/109，n5368同型U32433/109；n25600由AOI22V2_12TR40 U30602驱动/52。先查实际驱动约束和替代单元，不盲目重复only_design_rule，不放宽原规范；新映射必须新gate14。

SAIF probe02（ced runs/systolic_b_v3_saif_probe02/systolic_b_saif_probe，PID206692）VCS成功、PT拒绝ANSI端口，Expected ',' or ')' but found 'c' at line1，后继DES错误不是根因。本地native_saif_probe已改经典端口声明，尚未提交部署；新probe03待做。R4 L01 SAIF/VCD≤1%交叉核对未做。

## 恢复入口

13:28:55空间413.0088GiB；新EDA前重核进程/锁。当前无已知运行EDA，本地无持续session/待Return。VNC18874435 workspace3/ced空闲shell，FZ关闭，最后驱动查询截图已读。

ced=light-light126-systolic-b-v3-20261112_114355-ced0e139a01e；原synth02在8d包。旧62/2b完整ZIP仅板端暂存未FTP上传，且含后续工具修复，不执行。所有运行目录保留。

下一步DRC诊断/修复与结构审核、SAIF新probe03、R4交叉核对；通过时序/面积后自己的1200、干净ASIC14、新gate14、活动12/功耗12及最终报告。B无最终1200和功耗，不继承R4 PASS。

远端tcsh使用env PYTHONPATH；python外层双引号内避免美元符号。type每条<1000字符独立命令，等完成再Return。只使用已授权VNC/FTP；9351字符长行曾引号失败，不重试。所有旧launch/cleanup/deploy已执行，不重复。
