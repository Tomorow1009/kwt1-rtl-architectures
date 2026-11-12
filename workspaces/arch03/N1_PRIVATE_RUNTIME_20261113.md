# N1受限临时运行目录：完整包与证据包分离

本改动只为N1增加已经明确核验的私有临时运行根，不更改生产RTL、旧B0入口、SoC、综合准备逻辑、
工艺库路径或共享团队锁。`/tmp`不是长期交付位置。原9305包及其已启动作业保持不变；新工具必须
部署为独立完整OPS包，不能覆写运行中的BASE包文件或重写其manifest。

## 固定边界

- Linux账户必须为`s4_21usr`，目录owner须与运行进程uid一致。
- runtime根只能是`/tmp/s4_21usr_n1_YYYYMMDD_HHMM`，必须是当前用户所有、权限0700、逐级无symlink。
- OPS和每个BASE证据包必须是该根直接子目录，名字以`light-light126-n1-`开头。
- 每个包显式提供完整manifest SHA；入口核对全部已列文件的SHA、所有者和无symlink。OPS还必须列出新`n1_paths.py`。
- 证据路径只能是已登记包的`runs/<独立session>/n1_<stage>`目录。未登记兄弟目录、任意/tmp、路径穿越及其他用户文件均拒绝。
- 同一cfg仍以`/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock`统一排队；不创建私有锁替代它，不清除已有锁。
- config文件不能注入`runtime_roots`。只有命令行明确身份核验后才在内存建立此列表；原配置、模型和工具位置必须完全一致。
- 进入和退出阶段均复核包文件、目录dev/inode及owner。每个新临时阶段记录`runtime_storage_receipt.json`，其SHA进入阶段summary。

## 调用方式

实际manifest SHA取解包后已独立核验的manifest；以下占位符不能直接运行。当前OPS可读取同一
runtime根内原9305 BASE综合证据，无需重新综合。原`verify_synthesis`继续比较必要准备脚本、
生产RTL、库和网表身份；新目录准入不代替这些检查。

```text
python3 <OPS>/workspaces/arch03/scripts/n1_server.py gate
  --session n1_gate_tmp01
  --synth-run <BASE>/runs/<原综合session>/n1_synth
  --synth-summary-sha256 <原综合summary完整SHA>
  --runtime-root /tmp/s4_21usr_n1_20261113_0210
  --runtime-manifest-sha256 <OPS manifest完整SHA>
  --runtime-evidence <BASE> <BASE manifest完整SHA>
```

`--runtime-evidence`可重复，只增加逐个明确指定并核验的兄弟包。跨包读原始证据不修改BASE。
不提供runtime参数时，原共享目录运行方式保持不变；新入口在共享根外必须显式给出runtime身份。
旧9305入口不做就地升级，因此此前由根代理启动的旧入口临时综合不受本次代码修改影响。

gate、saif、power、timing_audit与drc_audit均使用同一N1边界检查。server增加`drc_audit`和
`structure`串行阶段，两者均需`--synth-run`和对应SHA。原standalone结构审核仍为显式文件哈希的
只读工具，本次没有放宽其权限。R4原生SAIF资格证据仍按原共享根引用；旧native_saif系列入口
未改为任意/tmp访问。新工具不复制厂商库，仍使用原配置及已有映射记录。

## 归档义务

正式交付前必须把临时包和实测证据完整归档到可持续保存的团队共享位置，并核验目的地全部SHA。
至少包括源码/固件/数据身份、manifest、运行state与summary、功能capture及回执、错误和停止日志、
网表/约束/面积/时序报告、活动/功耗和本runtime身份记录。不能只保存最终数值表。

旧回执中的绝对路径和哈希不改写。后续复核必须能访问原引用，或提供独立审核的路径迁移映射与
复现入口；不能因为复制目录成功就声称路径依赖已经处理。归档核验完成前不删除临时证据，也不
把服务器/tmp的空闲容量视为永久备份。共享盘暂不可写时，归档状态必须明确保持未完成。

## 本地验证范围

55项联合检查通过（路径11、server4、gate7、PPA22、DRC8、structure3），未调用EDA或访问服务器。
Windows测试明确模拟Linux uid/权限，生产Linux实际身份检查仍需部署时运行。
回执`local_runs/n1_runtime_toolcheck_20261113_021839/summary.json`，
SHA `4fa7b9a64429429ffaa96ce3391d42365e5d549191965db6ac92e4c94409f604`。
