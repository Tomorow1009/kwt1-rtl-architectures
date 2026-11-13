# T80十二层活动通过，功耗7/12 — 2026-11-13 22:20

当前有效计划仍 `workspaces/arch03/T80_PRIORITY_COMPLETION_PLAN_20261113.md`。G64取消，T64暂停，当前只完成T80。旧8路及所有历史文件禁止删除；不重跑已通过的ASIC240、综合或gate14。

最新实读22:18:25.100876：唯一队列t80_finish03仍running/t80_power，父183563、当时子297128，无错误。已完成15项＝原7项＋SAIF＋7层功耗。tmp剩151077998592B。尚缺P08–P12、20条FLOAT/ASIC精度关联，之后完整报告、独立时序/未知活动审核、持久归档。

十二层SAIF已全部通过；总回执SHA `2fee667759ed46e95e672716ef4ccea60c1155fa63c0bc27323d72be5f49a35d`，L12为126238周期、97750415B。完整窗口、输出和坐标由本次门级独立核对。截图 `takeover_local/t80_saif12_complete.png`。

前7层整机功耗W依次为0.0501254834、0.0502292328、0.0502437986、0.0502531491、0.0503219143、0.0503468513、0.0503912009，均为布局前原模型数值，尚未完成未知影响审核，不能称系统功耗验收通过。首层实读HF6.666666ns/LF66ns，189个no_clock全部位于静态JTAG调试模块；220宏＝ITCM32+DTCM32+shared64+accelerator92；活动exact374614、default1245、total375859，其他来源0。首层internal0.0381124578W、switching0.00484297518W、leakage0.00717004994W。截图 `takeover_local/t80_p01_review.png`。禁用弧细节查询已发，截图待读取。

活跃包仍 `/tmp/s4_21usr_t80_20261113_2012/light-light126-t80-activity-cef81d4`，manifest `181bb96b719363be5350e9e968ac2b2ad29555e2f4606e362721be3c42629b9b`。ops-cef81d4/request未变，自动继续P08–P12后precision。不要改活跃包或重启队列。

最终报告工具已更新并独立部署为 `ops-review-b80b171/scripts`，8文件manifest `b4cef85bf45ad4bfc49bf328cc10e9ca75072615e5063696e8c03d275085f884`。22:06:39实见IMPORT_PASS/READY。0391b09修复queue目录形状；b80b171进一步修复unknown_inventory对stage内具体文件的校验（不能把文件直接传给只接受stage目录的allowed_run）。5项本地测试通过。最终导出用此目录，不再用旧cfbca86/0391b09。全部21项完成后，以实际最终state SHA调用transport_report_stage.py；显式runtime-root/manifest、原delta01 ASIC14及--unknown-inventory。不自动授予验收。

仅复制归档工具也已部署 `ops-archive-66186a6`，2文件manifest `348023da60fa760f2e091237b035f11cd404dbbe5c26fa46af3f898ea5255d91`，22:01:43实见IMPORT_PASS/READY；尚未运行。包含t80_archive_runtime.py与复用tar读回模块n1_archive_runtime.py。需PYTHONPATH包括该ops、最新report ops/scripts和活跃包/scripts。最终所有任务和审核结束后，明确queue state SHA，用新shared backups/t80-runtime-DATE_TIME目录，完整runtime根复制、回读、不删原件。归档日志必须在runtime根之外；归档进程cwd也在源根之外。

本地活动工作树 `E:/fpga_race-two/kwt1-t80-t64-g64`，分支codex/light-light126/n1-t80-t64-g64-20261113。已push66186a6；339f7d7、b80b171及本检查点待同步。另一个同步操作的5360ad9已保留。原脏工作树不动。

VNC18874436/workspace3，FZ20972102断开。所有ops传输已结束。最后发出读取首层disabled_timing.rpt前23行的只读命令，执行session85670待取最终截图 `takeover_local/t80_disabled_timing_head.png`；不要误Up当成功耗查询。功耗通用查询文本在 `takeover_local/t80_power_watch_cmd.txt`。恢复先核对windows、完成待收输出，再明确键入功耗查询。本文不将22:18状态作为未来实时状态。
