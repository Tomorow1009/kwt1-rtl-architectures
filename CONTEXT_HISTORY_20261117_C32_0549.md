# 05:49检查点：活动8/12，完整R4临时副本核验在进行

恢复先读AGENTS、有效计划 `workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`、本检查点及STATUS。本节覆盖下方旧观察，C32-A仍未冻结，不开始C32-B/G32硬件。

- 2026-11-17 05:47:51.011287：唯一正式父101802，c32_finish_repair04为running/saif。新门级14通过，活动L01–L08完成，L09子129728自05:44:13.599662运行。共享盘1048576B、/tmp63789752320B，原锁owner存活。等待器110729仍按原依赖在整队列成功退出后导出新报告；不重启。严格时序、DRC及PT12会由同一原队列继续。
- 修复03新网表4f6e416402f2a178ec0ae0494fab1cddc53d7cf9113ac19990e108580b47c1dc，约束无违反，保守面积0.7224077335mm²。自己的最终活动/功耗/模型审核未完。STATUS已把原坏网表结果移入unqualified_original_netlist_evidence，当前功耗字段为null；不能将旧48.9738mW当新结果。
- 共享盘容量只读调查：B0包占85291913216B，主要是r4_waves_lossless_archive02（75660296192B）及r4_l02_lossless_archive01（7669493760B）的已压缩波形，不是编译缓存。回执记录11月12日完整归档后原VCD移除。不能按无用缓存删除这些唯一归档。旧N1大csrc候选为0。HOME和共享盘同一设备45，/tmp设备2051，没有新增可用共享存储。

## 只读存储准备（未删除任何新文件）

R4 L03路径为PROJECT/bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/r4_waves_lossless_archive02/layer_03.vcd.gz，PROJECT仍是共享IC/light-light126-undergrad-d2-20261109。其gzip7662823694B，对应原VCD12584787471B。

1. 固定三段64MiB样本的gzip6/XZ3逐字节往返检查已完成，原文件只读。入口/tmp/s4_21usr_c32_storageprobe_20261117.py，SHA7420c0d16aefb8ab3926e89c536725a1c3a3945010535102c5fde4c92cb8573c。结果/tmp/s4_21usr_c32_storageprobe_20261117/result.json，SHA1177460e4694be4852dd7c13d48c41a1ad0c8445a019bf178d095d2eee596c1由后续stager机器校验。样本不构成删除许可或全量归档证明。
2. 单核nice+15的完整只读stager父128419已启动，源码/tmp/s4_21usr_r4_l03_xzstage_20261117.py，SHA1ab445bf8f621c84f40adb0db4e4fa43fbb5f18e660e13cd720a820b0c286f04；日志同前缀.log、启动回执同前缀_launch.json。控制/文件目录/tmp/s4_21usr_r4_l03_xzstage_20261117。原gzip完整拷贝及独立SHA回读已通过，仍保留共享原文件；目前只在/tmp压缩XZ。05:48:25.626113已处理2147483648原始字节/374.5098s，XZ文件478309001B。最终还必须完成全VCD原始哈希和独立XZ完整解压核对；未完成前不迁移、不删原gzip。脚本有12GiB/tmp余量检查，失败保留所有产物。
3. C32复制归档工具已部署并核验54个冻结依赖，但未启动归档：/tmp/s4_21usr_c32_archiveops01_20261117。tools.json SHA c53a4c486c5003341c7610f2e3706a9c99fe00b6ad6190829177eed8b2fb95ca，launcher.py SHA6ad68a9ee39c0ef6f4e29af23ef8a11ec3a39b3ce0abbed62252222d09d4f976。已测试的新等价修复合同保留旧严格合同；复制只在队列、exporter、等待器均结束后操作，完整回读，源不删除，20%+512MiB余量。运行命令须等完整新报告和空间条件满足再调用launcher.py --tools-sha256上述值。
4. 尚未编写或启动R4 gzip→XZ的持久迁移/删除入口。若考虑它，必须以完整stager终态、原gzip临时副本及XZ全量证明为前提，明确原路径恢复方式，持原协作锁并确认无人使用；保留唯一原始VCD字节及所有回执，不碰旧八路、桌面T80或冻结S0/P80/C80。不能把本次只读副本制作记录成已释放空间。

## 下一步与恢复入口

继续原101802队列剩余活动与PT12，待110729自动完成新报告/未知活动/模型snapshot。并行只读跟进128419；它不会启动EDA、修改源或删除文件。随后解决持久归档空间，完成新网表审阅和C32-A冻结，再按计划进入后续。旧清理32/33/34均终态，禁止重复。

Git7d5c877已推个人分支，最新检查点/部署观察随后同步。仅历史S0_SYNTH05_FINISH_LAUNCH_20261115.py未跟踪，勿提交/执行。VNC18874435/workspace3，无待输入GUI会话；不使用workspace4。重要旧状态保留CONTEXT_HISTORY_20261117_C32_0523.md及0508/0455等历史。

---

