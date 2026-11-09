# DMA16独立运行入口

执行状态以CONTEXT_HANDOFF及验收记录为准。以下命令是已实现入口；实际服务器通过项必须附新运行回执，不能把命令存在当成验证完成。

使用已提交干净源码、已独立核对的旧14用例及tile16目录、无任务输入的DMA固件打新包。`package_dma16.py`逐个重核坐标、整数输出和源码/固件哈希；可同时携带polling和IRQ固件。包不含固定平台原始源码、厂商库、凭据、聊天记录或大波形。

```text
python workspaces/arch03/scripts/package_dma16.py --member <成员/本次标识> --data <旧14case> --tile-data <对应tile16> --firmware <polling产物> --irq-firmware <已核验映射IRQ产物>
```

按已有授权经开发板Linux FileZilla上传独立目录，校验ZIP并用既有安全解包器核对每个文件。所有运行入口持同一个`.arch02_team_lock`；先读取现有锁和进程，不清除他人/历史锁，不同时启动多个EDA作业。

```text
python3 workspaces/arch03/scripts/server_run.py dma16_soc --session dma16_smoke01 --cases layer_01
python3 workspaces/arch03/scripts/server_run.py dma16_soc --session dma16_irq01 --cases layer_01 --firmware-root <本包绝对路径>/firmware_irq
python3 workspaces/arch03/scripts/server_run.py dma16_soc --session dma16_full01 --firmware-root <本包绝对路径>/firmware_irq
python3 workspaces/arch03/scripts/server_run.py dma16_synth --session dma16_synth01
```

每个stage都是新目录，错误也保留。首次固定平台安装/编译本身可能发现接口问题，必须修本地源码后生成新包，不能原地改正在验证的包。只有真实CPU14用例通过后才扩大回归。

`dma16_soc`一次编译后按case运行真实E203；`dma16_build`仅编译并生成`batch_contract.json`，不声明CPU已执行。contract冻结可执行文件、全部RTL/头文件、平台、宏和标准单元模型、程序-only物理启动文件、观察器、时钟、布局和编译回执。任务数据只有PC预读的`+LOAD32`，经原SysMem接口进入DMA，再依次共享写ACK/共享读/输出写ACK；ITCM不含输入。

最终批量在编译入口释放锁后独立执行，避免嵌套锁。`boot_by_shift`选择事先校核的程序镜像，任务间不改源代码或已编译配置。

```text
python3 workspaces/arch03/scripts/dma16_batch.py run --data /storage2/2026contest/server4/s4_21usr/Desktop/IC/hex --contract <合格冻结构建>/batch_contract.json --output <全新1200运行目录>
```

旧37组不续跑。只有完全一致配置且重新核验全部已完成回执时才能显式`--resume`新批次；失败尝试不覆盖。此入口不代替最终14门级及12完整活动/功耗任务。

完整时间从首源读VALID发出至最后输出ACK；排空可以稍晚证实但不额外计入末ACK周期。源模型边沿N接受后寄存response，最早N+1握手，单笔在途。VCD在首VALID开始、末ACK结束；现场必须核验文件实际区间。CPU mcycle只交叉核对，IRQ/WFI下不可假定其等于自由运行系统时间。

MMIO8参考安装暂明确拒绝，需另做旧8路加载器与观察器；16路MODE0仅调试，不当新计时口径的正式8路对照。门级观察点还须根据新网表实际层次适配，当前RTL监视器不能自动证明门级可用。
