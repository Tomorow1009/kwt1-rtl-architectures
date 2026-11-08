# 服务器操作入口

所有命令在VNC里的Linux终端运行。不要把Linux命令输入Windows终端UI；本机自动化遵守当前computer-use技能。

## 路径与环境

|资源|路径|
|---|---|
|FTP根|`/IC`|
|Linux根|`/storage2/2026contest/server4/s4_21usr/Desktop/IC`|
|旧通过基线|Linux根下`arch02_server_r03`，只读参考|
|SRAM|`/storage1/admin_public_dir/SRAM_Lib_2025`|
|工艺|`/storage1/admin_public_dir/SMIC40_2025/S40.tar.gz`|
|VCS|`/eda/synopsys/vcs/vcs_2020.03-SP2-6/bin/vcs`|
|DC|`/eda/synopsys/dc/dc_2022.03-SP5-5/bin/dc_shell`|
|LC|`/eda/synopsys/lib_compiler/lib_compiler_2022.03-SP5/bin/lc_shell`|
|Verdi|`/eda/synopsys/verdi/verdi_2020.03-SP2-6/bin/verdi`|

登录Shell为tcsh，已有.cshrc引用 `/eda/synopsys/admin_snps_env` 环境脚本。本入口继承登录环境并按server_config.json将工具bin加入PATH，不设置/输出许可证秘密，不修改.cshrc。工具启动失败时检查桌面command.log及本机环境说明；不能只凭可执行文件存在判断许可证有效。

预检校验两个实际底层模型的固定SHA256及匹配SS库；变化会失败，不自动沿用旧引脚结论。宏CEN/GWEN/WEN低有效，EMA=2、EMAW=0、RET1N=1。功能仿真显式选ARM_UD_MODEL。DC读取匹配RVT SS 0.99V125°C库，6.667ns、理想时钟、暂定IO预算；不代表物理签核。

## 分阶段命令

将生成ZIP和本目录unpack.py上传到/IC，按本地回执指定SHA256：

```sh
python3 unpack.py <本次包.zip> --destination team_runs/<成员> --sha256 <回执中的64位SHA256>
```

该入口检查路径越界、重复条目、manifest及每个文件哈希，目标存在时拒绝覆盖。随后进入打印的UNPACK_HASH_PASS目录。

进入解包后的本次包根目录（存在manifest.json、server.py、rtl和arch02），先确认没有队友操作或运行：

```sh
python3 server.py status --session acceptance01
python3 server.py all --session acceptance01
```

也可依次用 `preflight`、`software`、`unit`、`vcs`、`synth`、`hold`、`audit` 替换all，使用相同session。每阶段只允许执行一次；结果写入team_sessions/<session>/state.json和阶段日志。

软件校验重算12层304128输出；unit宏单测；vcs完整真实矩阵、定向和失败检查；synth首次综合；hold读取本次synth的DDC修复；audit重读本次VCS输出及最终DDC。只有最后输出 `TEAM_FLOW_PASS outputs=304128 physical_signoff=false` 且各阶段passed，才是本流程完成。

## 看结果与波形

state.json中的run字段是实际目录，不能照抄旧时间戳。VCS summary保存模型、源码哈希与实际输出数；各层CSV按索引重建矩阵。rounding作业的arch02.vcd可在Verdi波形窗口打开。完整12层不保存全量信号波形。

DC日志和qor/constraints/timing/area报告、网表/DDC/SDC留在dc_runs；审计结果在audits。先读错误和阶段退出码，再看PASS。没有完整跑完，状态只能是失败或未完成。

当前移植入口的服务器实测状态以STATUS为准。[2026-11-08新入口验收](evidence/SERVER_ACCEPTANCE_20261108.md)已完成全部阶段，最终输出TEAM_FLOW_PASS；这是独立于旧r03的新运行证据。后续修改仍需重新验证。
