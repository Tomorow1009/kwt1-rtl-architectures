# S0设计容器修复检查点 — 2026-11-15 21:45

**21:53更新：synth06父135293在短链接探针失败，DC135510运行67秒，没有进入新块映射。`-single_file`未消除同名设计，两个块current_design仍报ambiguous；旧目录保留。修复9ffb2a9改为读取前保存设计对象集合、读取后按同名对象明确移除旧内存设计并检查唯一性；seed只移除-designs，保留库。21项本地检查通过，此修复尚未部署。前台watcher135824已自行退出，Bash空闲，无未完输入；74512/56532/60151均结束。**

有效计划仍为`workspaces/arch03/IMPLEMENTATION_PLAN_T80_P80_C32_G32_20261115.md`；S0→P80→C80→C32→G32。桌面T80和全部旧八路禁止修改。S1–S4尚未开始。

## 实际终态

- a5ce90a包`s0_synth05`父126260于21:33:17结束failed；DC127319用时185秒。两条错误：`arch03_t80_accel doesn't specify a unique design`（compile.log第106和857行）。旧unmapped linked.ddc与mapped seed同时驻留，设计名称重复。不是数值验证失败，也不能把其输出记为PASS。
- 21:38只读查询原锁False；watcher127118已自行退出，VNC18874435/workspace3显示Bash空闲。没有未完输入。板端转发91027保持；FileZilla未连接。必须重新核对当前状态，不能把此记录当实时。
- 所有05c、a5失败产物和T80桌面均未修改；前一次N1编译缓存归档已完成，不重复。

## 本地修复

- 已读取实际安装DC官方`doc/syn/man/cat2/read_file.2`：`-single_file`可将不同格式设计读入指定内部容器。
- seed恢复在原RTL完成缺失单元检查后`remove_design -all`，再读mapped seed，避免同名数据库残留。
- CPU与最终顶层将三个DDC读入同一`s0_designs`容器，再link。新增不映射的短探针，在新综合开始前按完整module tokens核对两个子块与seed输出完全一致，检查220宏；探针不赋予硬件PASS。
- 最终报告保留incremental_recovery来源与失败seed工具耗时，避免把恢复时间冒充完整从零综合耗时。
- 本地21项相关检查通过。旧default block脚本保持，用于严格验证synth03失败seed来源。当前修复尚未部署/服务器验证。
- 未提交的`S0_SYNTH05_FINISH_LAUNCH_20261115.py`已过时，禁止执行（synth05失败）。后续必须针对实际成功session另建收尾请求。

## 接续

1. 提交修复、部署独立包，在原共享锁下新session synth06；复用未验收seed仅作增量起点，短DDC链接探针必须先通过。
2. 再执行共享块/加速器增量/CPU/最终顶层，确认同最终网表面积、setup/hold、220宏、子块身份和结构。
3. 合格后同原锁收尾gate14/SAIF12/时序DRC/PT12并独立报告。S0完成之前不进入S1。
4. 如短探针失败先修新工具，不继续长综合。运行中包不修改，历史失败不覆盖。

更早输入/运行/归档身份见S0_RECOVERY_RUNNING及S0_RECOVERY_TRANSFER检查点。
