# N1辅助证据只归档入口

新增`scripts/n1_archive_auxiliary.py`和独立测试；没有修改冻结`n1_archive_runtime.py`、
runtime注册、生产RTL、N1阶段工具或服务器文件。本工具尚未部署、尚未执行生产归档。

现有主归档工具只接受完整N1 bundle及两个已知B0 inventory辅助run，无法通过纯配置覆盖
私有根下的控制probe、ZIP保留和锁恢复目录。新入口只处理这部分辅助证据，不替代三个
N1包的主归档，不把备份成功当作硬件验收或B0功耗批准。

## 固定范围与身份

源根固定为`/tmp/s4_21usr_n1_20261113_0210`，仅Linux账户`s4_21usr`拥有的0700目录。
可选择的直接子项固定为以下十一项；不接受通配符、父目录遍历、绝对entry、重复项或新增未知名称：

- `b0_control_l01_20261113_0403/`
- `n1_batch01_lock_recovery_0452/`
- `zip8_20261113_051340/`
- `retained_ops_upload_20261113_0428.zip`
- `duplicate_ops_zip_receipt_0428.json`
- `light-light126-n1-reviewops-20261113_0313-1f86fc70d41e/`
- `light-light126-n1-controlops-20261113_035653-3165fb3cab28/`
- `light-light126-n1-archiveops-20261113_033430-0f3a46d3f3fb/`
- `light-light126-n1-archiveops-3b5cf866b337/`
- `light-light126-n1-evidenceops-20261113_0640/`
- `b0_control_l02_l12_20261113_0640/`

每项必须明确选择，选择后保存其全部普通文件和空目录，不按后缀、PASS或体积排除文件。
目标固定为原项目`operations/n1-aux-archive-YYYYMMDD_HHMM[-标识]`的新目录，必须与/tmp
不同文件系统。已存在的目录拒绝；原工具和历史归档不能覆盖。

所有源symlink（包括悬空链接）、特殊文件、其他所有者、模糊成员名均拒绝，不跟随厂商目标。
普通文件内容用O_NOFOLLOW打开并核fd对应的inode/device后读取；读取前后stat必须一致。
目录owner/0700每轮重新核对。限制为总计10000项、2GiB普通文件、单文件512MiB、12层深度；
元数据遍历30秒、带内容身份遍历60秒。到上限就明确失败，不继续无界扫描，也不把部分和当完整身份。

依赖固定SHA：

- `n1_archive_runtime.py`：`6bfd21fbf42dbce160829f99c8eff2d3075c75857f2ccbe74fec67e141de09f9`。
- `n1_paths.py`：`fe301e1e5f87852103c537b8191c7064f1b8c44a8979f1977901bf26ed16e39d`。

复用这些已冻结的流式gzip、tar成员完整回读、fsync、空间守卫及/proc占用检查，运行前后都核依赖身份。
未扩大原bundle注册，未复用旧schema冒充新辅助终态。

## 三个模式

1. `--mode plan`：只做有界lstat/目录清点，不读取源文件内容，返回所选文件集合、字节数和
   当前共享空闲；不生成归档。`required_bytes=null`，明确实际压缩长度尚未测量。
2. `--mode identities`：只读全部所选文件，输出每文件SHA/大小/元数据和每个顶层项的
   `tree_sha256`，然后重核元数据与无占用。该树身份绑定确切成员集合、原路径、内容和源stat；
   由根代理审查后写入新的请求文件，不能把未审的自动计算值直接视为用户批准或阶段PASS。
3. `--mode archive`：每项必须携带已核对的64位tree SHA；重新测得的完整身份不一致即拒绝。
   只写新目的地，完整压缩、回读和源前后核对通过才发布verified回执。

三个模式只要原共享`.arch02_team_lock`存在就拒绝；plan/identities结束前也会复查锁。
archive从开始到结束持有这个唯一共享锁。初始owner写失败保留partial owner，不清理未知锁；
释放前核锁目录/owner文件inode、完整owner原始字节和目录成员。若owner被换，保留锁供人工复核。
工具没有Popen、网络、清理源目录或自动恢复旧锁的功能。

请求示例仅展示两个明确项，实际应按审阅选择所有必要项：

```json
{
  "schema": "arch03-n1-auxiliary-archive-request-v1",
  "runtime_root": "/tmp/s4_21usr_n1_20261113_0210",
  "destination": "/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109/operations/n1-aux-archive-20261113_1700",
  "entries": [
    {"name": "b0_control_l01_20261113_0403", "tree_sha256": null},
    {"name": "zip8_20261113_051340", "tree_sha256": null}
  ]
}
```

null只用于plan/identities。archive必须替换为对应实际tree SHA，不允许占位值。
CLI还必须传`--request-sha256`，对输入请求原始字节核验；请求限1MiB。
归档manifest另保存完整请求及其规范JSON哈希，明确命名`request_canonical_sha256`，
避免把它误认为原文件字节哈希。CLI完整返回中含`request_file_sha256`。

```text
python3 -B <新独立入口>/n1_archive_auxiliary.py --mode plan --request <新请求.json> --request-sha256 <实际请求SHA>
python3 -B <新独立入口>/n1_archive_auxiliary.py --mode identities --request <新请求.json> --request-sha256 <实际请求SHA>
python3 -B <新独立入口>/n1_archive_auxiliary.py --mode archive --request <已审身份请求.json> --request-sha256 <新请求SHA>
```

完整输出应保存到所选源目录以外的新审计日志。启动cwd、请求文件、工具和driver日志也应
位于所选源之外，避免归档自己正在打开的文件。原锁活动时不运行这些命令，不建立自动队列。

## 空间、回读与失败

复用gzip1不落盘计数流得到准确压缩长度C，要求共享空闲≥`ceil(1.2×C)+2GiB`。
写入每约4MiB继续检查2GiB余量；元数据字节数或压缩采样比例不能代替该前置条件。
所有tar成员的类型、SHA、字节数、权限/时间等核对，并读到gzip EOF核CRC/长度。
结束时再次全量核源、无占用、依赖和锁归属，然后才将本次partial改为最终新文件。

空间不足、CRC损坏、源变化、外来owner或其他异常时，源与已产生的partial都保留，
能写时记录failed状态，不生成通过回执。唯一允许移除的是本次确证拥有的协作锁元数据。
恢复索引只保存原路径→成员，不重写原回执，不解包覆盖，不宣称迁移后验证/干净复现通过，
也不授权删除/tmp。本地ZIP和历史服务器记录不会因本工具被清理。

## 本地验证与未测范围

首轮冻结16项测试通过，耗时2.783秒，根代理另重跑16项通过/2.854秒。使用真实小文件与tar/gzip回读、实际NTFS正常/悬空链接，
覆盖路径/所有者/目的文件系统、原锁占用、输入及依赖SHA、成员集合变化、数量/时间/大小边界、
空间不足与写途中不足、CRC破坏、源变化、owner被换、初始owner fsync ENOSPC。
Linux账户、/proc、目录fsync和不同设备事实使用明确fixture，不宣称在服务器完成这些检查。

首次15项测试中一项fixture在坏归档保留后误用已存在目的目录，生产guard按设计拒绝；
修正fixture为另一个全新目的目录，没有放宽guard。加入初始owner失败测试后16项通过；
补每轮root检查和成员名检查后再次16项通过。未重复旧主归档全套测试。
两份代码在Python3.8.20上通过`ast.parse(..., feature_version=(3,6))`；不是实际Python3.6运行声明。
源码SHA、命令和结果记录见`handoff/team/evidence/N1_AUXILIARY_ARCHIVE_TOOL_20261113.json`。

下一步为独立代码审查、冻结/部署新小工具、源全终态后有界清点与真实身份审阅。
目前没有实际辅助归档、没有新硬件PASS，N1阶段不因此解锁N2。

根代理随后已静态复核本入口、原helper的流式回读/CRC及锁逻辑，未发现当前阻断。
只读审查不替代服务器实际归档。根代理随后明确固定本轮合并OPS及11层控制probe的两个目录名，
授权仅将上述最后两项加入ALLOW；没有自动扩大匹配规则。新增路径同样必须实际存在、属于本账号、
不是链接、具有已审树身份，并在原锁空闲时才可归档。新增定向测试核两名字只能是目录，近似名称拒绝。
更新后的17项相关测试通过，耗时2.828秒；原16项记录保留。提交冻结及最终合并部署仍由根代理统一处理。
