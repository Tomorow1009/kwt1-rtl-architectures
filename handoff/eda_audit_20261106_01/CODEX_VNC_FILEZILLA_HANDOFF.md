# Codex 操作 VNC Viewer 与 FileZilla：队友交接文档

交接日期：2026-11-06。本文依据本次实际操作与同目录 `AUDIT_REPORT.txt` 整理；描述的是当时的状态，接手时应重新观察当前窗口和任务状态。

## 1. 先了解工作方式

本项目的操作链路为：

```text
Windows 本地准备检查脚本
    ↓ FileZilla 仅上传指定文件
Linux 独立盘点目录
    ↓ 通过 Windows 上的 VNC Viewer 操作远程终端
Linux 执行 Shell / Python / Tcl
    ↓ 在远程终端或文本编辑器显示简短摘要
Codex 通过屏幕阅读并整理必要结论
```

本次验证了这条链路可以工作。Codex 控制的是 Windows 上的应用窗口，再通过 VNC 操作 Linux；没有通过 SSH 直接连接服务器。

本文用于传递工作上下文，**不会自动同步三个人的 Codex 对话或工程文件**。队友需要把本文及必要的本地脚本放入自己的工作目录，并让新对话先阅读。换电脑后，本地盘符、文件路径、窗口标识及控制工具可用性都要重新确认。

### 操作边界

- Windows 使用独立 **VNC Viewer** 和 **FileZilla**。Linux 内允许执行自己上传的 Python、Shell、Tcl 脚本。
- 不使用 SSH，不下载服务器文件，不建立绕过平台限制的回传通道。完整日志留在服务器，本地只整理允许通过界面查看的必要结论。
- VNC 和 Linux 密码已经更换。由本人完成登录，不向新对话提供密码，不使用附件或手册中的旧密码。
- 同一时刻只由一人控制这台 Windows 及共享 VNC 桌面的键鼠。其他队友可独立准备本地代码，但不要同时向同一桌面输入。
- 本阶段只盘点环境：不修改设计、不执行综合或布局布线、不生成 SRAM、不转换库，不改全局 `.cshrc`。
- 检索限于已发现的相关目录，不扫描整台服务器，不分析工具内部编码内容。

## 2. 接手前准备

1. 阅读本文、`AUDIT_REPORT.txt` 及即将执行的脚本。
2. 确认自己的 Codex 会话提供电脑控制工具，并读取当前安装的 `computer-use` 技能及其要求的说明。另一台电脑不一定具备相同工具；无法控制时应明确说明缺失能力，不能声称已执行。
3. 本次使用的控制实现为 `node_repl` 加 `@oai/sky`。这是历史实现记录，实际接手以当前技能和工具说明为准，不直接照搬旧会话中的变量、窗口 ID、坐标或元素索引。
4. 用户登录 VNC Viewer、FileZilla，打开目标会话；需要新密码时由用户操作。
5. 协调控制权，确认没有队友正在使用鼠标键盘。读取当前窗口，确认不是 VNC 启动器、认证窗口或其他连接。
6. 检查已有任务和日志，优先阅读本次已完成结果，不立即重跑盘点。

## 3. 已验证的路径与环境

以下均为 **现场验证**，账号及路径属于本次队伍环境，换账号后应重新确认。

| 项目 | 实际值 |
| --- | --- |
| Linux HOME | `/storage2/2026contest/server4/s4_21usr` |
| Linux 桌面 | `/storage2/2026contest/server4/s4_21usr/Desktop` |
| 登录 Shell | `/bin/tcsh` |
| Python | Python 3.6.8 |
| FileZilla 远程路径 | `/iccompetition` |
| 上述 FTP 路径对应的 Linux 路径 | `~/Desktop/iccompetition`，已验证可写 |
| Linux 绝对路径 `/iccompetition` | 不存在，不能直接作为运行目录 |
| 公共资源入口 | `/storage1/admin_public_dir` |

**资料记录：**平台手册说明 FTP 根映射到桌面；上表路径另外做过现场验证。`.cshrc` 可读，并引用 `/eda/synopsys/admin_snps_env` 下的环境脚本，本次未修改。

## 4. 标准操作步骤

### 4.1 本地准备脚本

- 使用英文文件名、UTF-8、LF 换行，不携带密码。
- 创建独立、带编号的目录；后续任务使用新的编号，避免覆盖已有脚本和结果。
- 先确认远端解释器版本，再选相容语法。本次 Python 为 3.6.8，不直接使用只在更高版本支持的语法或 API。
- 把复杂命令放进上传的脚本，减少远程终端输入长度。
- 脚本输出简短分段摘要、退出状态和明确结束标记；详细输出写入服务器日志。
- 对启动探测设置超时，只终止自己启动的探测进程；正常完成后退出工具，避免占用许可证。

### 4.2 FileZilla 上传

1. 观察当前窗口，确认左侧是正确的本地目录，右侧是正确的远程目录。
2. 本次上传目录为 `/iccompetition/eda_audit_20261106_01`。
3. 仅上传选中的检查脚本。遇到重名提示先确认原因，不直接覆盖旧文件。
4. 检查传输日志中的文件名、字节数和成功状态，再确认远端列表已出现文件。
5. 本次 `inventory.sh` 上传大小为 4,944 字节，`probe.sh` 为 4,734 字节；这两个数字仅适用于未修改的本次脚本。

**旧队列注意事项：**本次 FileZilla 曾有 **504 个旧排队任务**，盘点时没有执行它们。接手时要重新检查队列，不点击会启动整个队列的操作，也不要擅自清空旧任务。

### 4.3 VNC 终端执行

采用“**观察窗口 → 一次操作 → 刷新核对 → 再决定下一步**”的方式。切换窗口、改变窗口大小或出现对话框后，应重新获取界面，不能沿用旧坐标。

远端登录 Shell 是 tcsh，不能把 Bash 的变量赋值、重定向或复合语句直接粘贴给它。已有两个脚本以 `/bin/sh` 为入口，在内部调用 Python，应显式使用 `sh` 运行。

以下命令 **仅在确需重新盘点，且确认没有运行中任务时使用**。接手时应先阅读已有日志；不要默认连续运行两轮。

第一轮：

```sh
cd ~/Desktop
sh iccompetition/eda_audit_20261106_01/inventory.sh
```

第二轮：

```sh
cd ~/Desktop
sh iccompetition/eda_audit_20261106_01/probe.sh
```

`inventory.sh` 会创建新的 `run_时间戳_进程号` 目录，并更新用于定位结果的 `latest_run.txt`；`probe.sh` 会创建新的 `probe_时间戳_进程号` 目录。重复运行会再次启动探测并新增日志，不应把重跑当成刷新界面的方法。

### 4.4 查看与记录结果

- 在 Linux 的终端或 Pluma 文本编辑器查看摘要，必要时分页，避免一次输出大量文字。
- 等待完成标记，同时检查退出码、错误信息和超时状态。总脚本完成不代表其中每项检查都通过。
- 记录必要的版本、路径、状态与阻塞项；完整日志继续留在服务器。
- “目录存在”“命令可启动”“具体功能许可证可用”“工程流程通过”是不同结论，分别记录。

## 5. 本次遇到的问题与恢复方式

| 情况 | 本次现象与接手方法 |
| --- | --- |
| Windows → Linux 粘贴 | 用户报告 `Ctrl+Shift+V` 可用，但自动化粘贴未稳定成功。先确认终端焦点，粘贴后核对命令，再回车；失败时按键输入短命令并用 Tab 补全路径。 |
| Linux → Windows 复制 | 当前环境不允许，不尝试通过其他通道绕过。 |
| 屏幕刷新延迟 | 截图有时落后于刚刚执行的操作。先等待并重新观察，不盲目重复点击、输入或按回车。 |
| 人工输入与焦点冲突 | 工具曾检测到人工输入及 FileZilla/VNC 焦点切换。停止输入，协调队友停止操作，再重新识别目标窗口。 |
| 最小化窗口或旧控制状态 | FileZilla 曾因旧人工输入状态无法自行展开，最终由用户恢复到前台。遇到同类问题按当前工具恢复流程处理，必要时仅请用户展开窗口；不改服务器设置。 |
| 断线或操作中断 | 重连后先查看终端、已有结果目录、日志和相关进程状态。未确认原任务结束前不重跑，也不终止不属于自己的任务。 |
| 工具或索引超时 | 保存退出码和日志，记录检查范围及未完成内容。超时不自动等于缺许可证或文件损坏。 |
| OCR 与小字误读 | OCR 仅辅助阅读，关键路径、数字和错误码通过原图与服务器端检查交叉核对。本次“8 项访问错误”实际是误读，第二轮确认六个宏均为 `errors=0`。 |

不需要为本次已验证的操作链路另外安装 OCR。后续若使用 OCR，也不能仅凭识别结果生成并执行关键命令。

## 6. 已完成的工具盘点

以下为 **现场验证**。五个 Shell 的启动脚本仅执行 `puts "AUDIT_SHELL_READY"` 和 `exit`，没有读取设计或运行设计流程。

| 工具 | 现场输出版本 | 检查结果 |
| --- | --- | --- |
| Design Compiler：`dc_shell` | T-2022.03-SP5-5 | 输出检查标记，exit=0 |
| PrimeTime：`pt_shell` | T-2022.03-SP5-1 | 输出检查标记，exit=0，但有 PT-063 和 1 项诊断错误 |
| Formality：`fm_shell` | R-2020.09-SP5 | 输出检查标记，exit=0 |
| ICC2：`icc2_shell` | T-2022.03-SP2-1 | 输出检查标记，exit=0 |
| Library Compiler：`lc_shell` | T-2022.03-SP5 | 输出检查标记，exit=0 |
| VCS：`vcs -ID` | VCS script version Q-2020.03 | 版本查询 exit=0，未验证编译仿真 |
| Verdi：`verdi -version` | 尚未确认 | 20 秒超时，返回124，脚本已终止自身启动的进程组 |

工具入口的完整路径见 `AUDIT_REPORT.txt`。`innovus`、`genus`、`xrun`、`virtuoso`、`spectre`、`calibre` 在当时 PATH 中未发现，不等于服务器没有安装。

**许可证范围：**本次没有针对具体 feature 做 checkout 审计。综合、形式验证、STA 分析、布局布线、库转换、VCS 编译仿真等功能许可证均尚未验证。启动横幅中的通用 license 文本也不是许可证有效的独立证据。

PrimeTime 的具体错误为：

```text
PT-063: Library Compiler executable path is not set.
Diagnostics summary: 1 error
```

因此不能把 PrimeTime 记录为“无错误可用”。Verdi 超时的原因也尚未诊断，不能直接认定是许可证不足。

## 7. 已发现的 SRAM 与工艺资源

### 7.1 SRAM：现场验证

入口：`/storage1/admin_public_dir/SRAM_Lib_2025`

已发现六个宏目录，抽查 Verilog 模块名称与目录名称一致：

- `RAMSP128X16`
- `RAMSP1024X16`
- `RAMSP2048X16`
- `RAMSP4096X16`
- `RAMTP128X16`
- `RAMTP1024X16`

每个宏的目录清单均包含：28 个 `.lib`、1 个 `.lef`、1 个 `.gds2`、2 个 `.v`、1 个 `.cdl`，另有其他配套文件。六个宏遍历错误数均为 **0**。抽查 Liberty 和 Verilog 可读，但未逐个验证所有文件，也未测试 GDS2/LEF 导入。

每宏抽查的库文件为 `lib/<宏名>_tt_1p00v_1p00v_125c.lib`，库头显示 `nom_process=1`、`nom_voltage=1.000`、`nom_temperature=125.000`、时间单位 `1ns`、电压单位 `1V`。这些仅是所抽查文件的信息，不能据此指定整个项目的工作条件。

**尚未确认：**实际深度、位宽、端口行为、读写时序、有效电平、供电接口、发行版本及与选定工艺的兼容性。不能只靠名称判断。当前扫描未发现 SRAM `.db`，也未确认 SRAM 生成器入口。

### 7.2 SMIC40：现场验证与限制

入口：`/storage1/admin_public_dir/SMIC40_2025`

| 资源 | 本次结果 | 结论边界 |
| --- | --- | --- |
| `S40.tar.gz` | `tar -tzf` 在60秒超时，exit=124 | 索引不完整，只能确认已看到的条目 |
| `techfile.tar.gz` | 索引 exit=0，共170条 | 尚未核对具体工艺内容、层叠与角配置 |
| 工艺相关 PDF | 已发现文件入口 | 最终批准的工艺版本仍待确认 |

大包的部分索引中出现 `S40/smic/SCC40NLL_VHSC40_HVT_V0.1/`，并发现 `.db`、`.lib`、`.lef`、`.tf`、`.tluplus`、`.gds`、`.v` 条目。该路径只是归档中的版本标识，不能视为已经批准用于本项目的工艺版本；索引也不能证明文件内容完整或可导入。

本次未解压、转换或复制这些库。公共目录还含 `Document`、`2025_Lab`、`SOC_RTL_2025`；旧截图中的工具内部 Tcl 文件不是芯片工艺库证据。

## 8. 文件与证据位置

### Windows 本地

```text
D:\IC_compeyition\Fast_coding\eda_audit_20261106_01\
    CODEX_VNC_FILEZILLA_HANDOFF.md   本交接文档
    AUDIT_REPORT.txt               详细环境盘点报告
    inventory.sh                   第一轮目录、环境与资源清单脚本
    probe.sh                       第二轮工具启动、库头与归档索引脚本
```

补充资料：平台手册位于 `D:\IC_compeyition\2026NICT EDA平台_用户登录及使用手册_V10.pdf`；历史截图位于 `D:\IC_compeyition\Fast_coding\eda_resource`，各文件夹内部按时间顺序阅读。历史资料不代替当前现场验证；附件中的旧密码不使用、不转录。

### Linux 服务器

```text
~/Desktop/iccompetition/eda_audit_20261106_01/
    inventory.sh
    probe.sh
    latest_run.txt
    run_20261106_225701_225097/
        summary.txt
        inventory.log
        config_references.txt
        resource_manifest.txt
        各资源目录的 examples.txt
    probe_20261106_230736_233687/
        probe_summary.txt
        driver.log
        各工具子目录中的 stdout.log
        各归档索引子目录中的 stdout.log
```

第一轮已观察到 `INVENTORY_EXIT=0`；第二轮已观察到 `AUDIT_PROBE_COMPLETE`。这些是历史完成记录，不代表接手时服务器上没有其他新任务。日志留在 Linux，本地报告是屏幕阅读后的整理，不是下载的服务器日志副本。

## 9. 接手后的下一步

以下均 **尚未执行**，应根据接手任务逐项推进：

1. 先阅读已有摘要及错误日志，确认现场当前状态和控制权，不默认重新盘点。
2. 根据设计需求核对 SRAM 模型和说明，确定深度、位宽、端口、时序及电源接口。
3. 确认平台批准的标准单元、IO、RC 角与 SRAM 版本组合，补充大压缩包完整索引与资源完整性检查。
4. 诊断 PrimeTime PT-063，优先采用独立工程级配置验证；保留全局 `.cshrc`。
5. 确定 SRAM Liberty 的使用方式或是否需要转换 `.db`；转换不属于已完成盘点。
6. 针对实际将用到的 EDA 功能验证许可证，再配置 link/target library、约束及物理资源。
7. 单独诊断 Verdi 超时。新增任务的脚本和结果使用新编号目录，保留本次证据。

本次交接不自动授权执行综合、布局布线、SRAM 生成、库转换或修改设计；开展这些工作前，应在新任务中明确目标和范围。

## 10. 可复制给新 Codex 对话的提示词

把下面内容发给队友的新对话，并将“本地资料目录”替换为其实际路径：

```text
请接手我们的 EDA 服务器环境工作。先阅读本地资料目录中的
CODEX_VNC_FILEZILLA_HANDOFF.md、AUDIT_REPORT.txt、inventory.sh 和 probe.sh。
本地资料目录：D:\IC_compeyition\Fast_coding\eda_audit_20261106_01
如果本机路径不同，先定位我们提供的交接资料，不假定旧路径存在。

操作方式：Windows 上的独立 VNC Viewer + FileZilla。
先确认本会话电脑控制工具可用，读取当前 computer-use 技能要求，
再识别当前窗口。用户自行完成登录，不需要向你提供密码。
操作前确认只有一人控制这台 Windows 和共享 VNC 桌面的键鼠。

无 SSH，不下载 Linux 文件，不建立其他回传通道。
只上传必要的本地脚本，通过 VNC 运行，在屏幕查看必要摘要；
完整日志保留服务器。不修改全局 .cshrc，不扫描整台服务器。
本阶段不执行综合、布局布线、SRAM 生成、库转换或修改设计。

FTP /iccompetition 对应 Linux ~/Desktop/iccompetition，
不是 Linux 绝对路径 /iccompetition。
本次验证 Shell=/bin/tcsh、Python=3.6.8。
执行脚本需明确解释器，不直接粘贴 Bash 语法给 tcsh。
Windows→Linux 的 Ctrl+Shift+V 自动化粘贴曾不稳定，
可用按键输入短命令并 Tab 补全；回车前核对整条命令。

先检查当前任务和既有日志，不默认重跑。
服务器已有日志目录：
~/Desktop/iccompetition/eda_audit_20261106_01/run_20261106_225701_225097/
~/Desktop/iccompetition/eda_audit_20261106_01/probe_20261106_230736_233687/
这两轮历史盘点已完成，但接手时可能有其他新任务。
FileZilla 当时有504个旧排队任务；请检查当前队列，
只上传本次指定文件，不启动整个旧队列、不擅自清空。

已知结论：五个 EDA Shell 完成最小启动，具体功能许可证未验证。
PrimeTime 有 PT-063（Library Compiler executable path is not set）。
Verdi 版本查询超时。S40.tar.gz 的索引超时且不完整。
六个 SRAM 宏有 Liberty/LEF/GDS2/Verilog，遍历错误数均为0；
此前“8项错误”为误读。实际接口及工艺兼容性尚未确认。
资源入口：/storage1/admin_public_dir/SRAM_Lib_2025
以及 /storage1/admin_public_dir/SMIC40_2025。

本次接手先核对现有记录与当前状态，列出阻塞项及下一步建议。
所有结论区分“现场验证”“资料记录”“尚未确认”。
遇到界面延迟先刷新观察，不重复提交；遇到人工输入冲突先停止输入。
后续任务范围由我们另行给出，不因阅读交接文档就重跑或改配置。
```
