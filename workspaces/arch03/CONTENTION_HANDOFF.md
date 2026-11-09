# CPU／DMA共享总线竞争验证交接

2026-11-10 00:45：本地实现及编译完成，**真实ASIC/E203尚未执行**。独立固件不替代正式IRQ性能版本，也不改变生产RTL。

- 新主程序`sw/main_dma16_contention.c`沿用已有寄存器契约和未修改的`kwt_dma16.c`，启动DMA后反复在共享SRAM独立128字节区域写／读／比较，至少16轮；错误或timeout走取消排空并报告失败。
- scratch=`0xa0040000..0xa004007f`，与输入、输出和邮箱不重叠；没有任务输入预填、源旁路或预取下一任务。
- 新构建器`build_dma16_contention.py`产出程序-only shift11/12镜像。固件目录`local_runs/dma16_contention_firmware_20261110_v1`，manifest SHA `6f4445ec285319279c45d6381ca83172e19f29cd76ce2cc223a236aa528a5447`，ELF SHA `6933ae865bee90f67770e7eecf8c0407f764c423923a2a918586b44363ffcbfb`。打包时去掉宿主command字段后manifest SHA会不同，以服务器实际回执为准。
- 构建第一遍因一个辅助源路径没有resolve而在创建输出目录之前失败；已修复，第二遍编译与程序-only边界核验通过，未覆盖已生成的旧固件。
- `dma16_contention`复用实际ASIC编译／观察器／四段事务检查，额外要求同时请求、双方各自竞争获准计数均大于0。原WFI性能任务这些计数为0，必须被该验证拒绝。
- 80项相关工具测试通过，包括5项新竞争证据拒绝测试；不将合成Python报告作为CPU证据。

恢复入口：用`--contention-firmware`打包至`firmware_contention`，新包通过FileZilla上传／SHA与全部输入核验后，在共享锁空闲时新session执行`server_run.py dma16_contention --session <唯一名称> --cases layer_01 rounding`。当前先等原8路14例结束，再用a53包运行gate03；竞争包上传与运行另排队，不改运行中快照。

待完成：真实两例CPU执行、四段统计及竞争双方服务证据；必要时根据真实失败修测试环境，保留失败目录。完整功耗、严格STA、最终1200和正式报告另看根交接。
