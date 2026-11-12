# N1临时运行根工具交接（子任务，2026-11-13 02:21）

根代理因共享盘被其他写入占满，安排从已核验9305 ZIP在私有/tmp根运行原综合；本代理没有
操作VNC、服务器、旧运行包或Git。实时作业身份以根检查点为准，不能由本地工具PASS推断远端完成。

已完成`n1_paths.py`和`test_n1_paths.py`；修改N1 server/gate/saif/power/timing_audit/drc_audit
的必要边界与工具哈希。OPS完整包和9305 BASE可作同一私有根的兄弟目录，分别显式绑定manifest，
所有包文件校验、uid/0700/无symlink与原共享锁仍严格执行。未修改n1_synth/n1_soc/安装器或RTL，
不强迫重跑原综合。新server还接入DRC和结构审核串行阶段。

55项本地联合检查通过，回执`local_runs/n1_runtime_toolcheck_20261113_021839/summary.json`，
SHA `4fa7b9a64429429ffaa96ce3391d42365e5d549191965db6ac92e4c94409f604`。Linux所有权在本地
Windows测试中模拟，尚未由本代理验证生产Linux。说明与归档义务见`N1_PRIVATE_RUNTIME_20261113.md`。

下一步由根代理冻结新工具并导出完整独立OPS包，原9305 BASE不改。调用新入口要提供
`--runtime-root`、`--runtime-manifest-sha256`和每个兄弟BASE的`--runtime-evidence BUNDLE SHA`。
先执行status/身份核验，再在既有统一锁下串行运行后续阶段；不要重复当前综合。

完整100浮点源尚未由本代理取得，精度report整合已另行冻结，见02:06检查点。新增路径入口不
授予任何功能/时序/PPA PASS；N2仍必须等待N1全阶段通过。临时运行的最终完整归档仍是交付必需项。
