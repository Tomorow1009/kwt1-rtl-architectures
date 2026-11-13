# T64独立包传输中、T80继续综合 — 2026-11-13T18:37:51.917520+08:00

有效计划：workspaces/arch03/N1_T80_T64_G64_IMPLEMENTATION_PLAN_20261113.md。每版只跑前20条/240任务/6082560输出；全100条未授权。G64必须等T64全项验收。

**最新保留要求：服务器旧8路所有数据、源码包、日志、波形、网表和报告不得删除或覆盖，也不能归档后删原件。本接续没有执行服务器删除。**

## 已完成与运行中
- GitHub个人分支codex/light-light126/n1-t80-t64-g64-20261113已成功推送至65d25073a1afcf4fc37da29c2d40ffc56f7e122a；T64生产RTL仍为e2e83ce，新增仅验收/报告工具及阶段标签修正。
- T80原ASIC14、240任务和真实CPU恢复/竞争通过，固定12平均112569周期，150MHz折算1332.5160568task/s。各summary哈希与目录见1826检查点，未重跑。
- **T80唯一队列t80_finish02，PID14008，18:22:51启动；18:35:25.095956实读running/t80_synth。** 日志正在处理N1数值核心层级，无新终态。可用空间34212937728B。当前bundle light-light126-t80-v4-9196556-delta03，不修改其文件，不重启。
- T64本地10000随机+32定向、14例、1/2拍/预取开关/ABA及恢复全部通过，详见1826检查点及T64_IMPLEMENTATION_REPORT.md；仍无真实ASIC/PPA PASS。
- 新完整T64包local_runs/light-light126-t64-v4-20261113_183328-65d25073a1af.zip，981文件，9597032B，SHA bbc52d95968ec51324b7af7e30600361cb5c2f4461c9f735a401ac7278320709。前包e2e仍保留。
- 新包的全部RTL、三套实际装载固件BIN/Verilog与前包完全一致。sequence ELF容器哈希变化，但装载字节及除elf_sha256外全部metadata一致；该差异已明确，不宣称所有ELF字节相同。
- FTP一次重试仍421，未上传包、未恢复旧上传队列。改用现有VNC工作区3在新目录重建精确运行子集；不碰工作区4。
- **VNC键盘传输中，本地exec会话60646。未完成前禁止发其他VNC输入。** 执行local_runs/transfer_t64_delta01.ps1，共141行；进度见local_runs/t64_delta01_65d2507_verified/transfer_state.json。只有代码传输，未启动T64作业。
- 重建目标bundle light-light126-t64-v4-65d2507-delta01，874文件，manifest SHA367eb3d21e0dcacc230f821be609805d9b1789bc3dd9ebca432e9f977f60c8ff；ops light-light126-t64-finishops-65d2507，SHA437a29f65ed61f1f389445ddd16fc457151b87f34fade3ca8548b44c338100f9。先在本机重建874文件与完整包逐字节核验通过，再发送。所有新目录使用exist_ok=False，不覆盖旧文件。
- 功耗未知活动收集器新增T80/T64身份绑定，18项本地测试通过；尚未部署、尚未拿到新功耗数据，不代表审核通过。

## 待办和失败路径
- 等60646结束，读取VNC回执并再次核对874文件、三套固件、源码和ops身份。先查看T80现有队列终态、锁、空间，再决定后续正式作业，不能重复启动。
- T80还缺综合/时序/面积、门级14、SAIF12、功耗12、同批20条浮点关联及独立审查。T64待实际ASIC14/240及完整PPA。G64尚未开始。
- 原t80_finish01因被动观察器把原O4混合端口视作CPU而失败，已9196556改到仲裁前mem_icb；新真实CPU恢复通过。旧失败目录保留。
- 首次T64本地delta检查把ELF容器也当作必须完全一致，因sequence ELF容器差异停止；local_runs/t64_delta01_65d2507保留。随后明确比较实际装载镜像、RTL和metadata，在*_verified新目录重新生成通过，未使用失败目录传输。
- 原工作树kwt1-rtl-architectures未提交修改保持不动；活动工作树kwt1-t80-t64-g64。
