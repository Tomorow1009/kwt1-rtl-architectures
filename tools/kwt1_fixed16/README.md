# KWT-1 固定16位转换工具与校准说明

本目录同步 2026-11-09 的三份本地交付文件，原文和源码保持不变。

- [105829条语音校准、位宽与小数位配置](KWT1_105829条语音校准_位宽与小数位配置说明.md)
- [转换脚本和语音导出数据说明](转换脚本和语音导出数据说明.md)
- [独立转换脚本](convert_kwt1_fixed16.py)

格式：X signed16/F12、W signed16/F16、b signed40/F28、Y signed16/F12，运行匹配的RTL测试平台时使用 `+SHIFT=16`。

转换器依赖 Python 3.6+ 与兼容版本的 NumPy。一次处理一条语音的完整12层浮点NPZ，当前没有单层命令行入口。

```sh
python convert_kwt1_fixed16.py --sample float_tensors.npz --weights shared_weights.npz --out NEW_HEX_DIRECTORY
```

## 同步范围与证据

本次仅同步脚本和文档，不修改RTL、历史版本或服务器。文档中的D盘路径是本机交付位置；对ZIP、JSON、榜单及其他配套文件的相对链接指向原本地数据目录，这些附件未随本次提交上传，因此并非GitHub下载链接。需要数据时按本地交付目录取得。

脚本源码SHA256：`444a0ca35175fc48aebe6a23069848fbc89a6d5baaaae0d95e0f1ece9a3f404d`。本次检查Python语法与命令行帮助；源码与已完成48个HEX文件逐字节对比的版本一致。文档记载的100条、30412800个输出属于此前完成的软件HEX回读核查，不代表本次新执行RTL验证；该100条的Icarus/VCS/E203验证仍未完成。

两份文档保留原文中的本地运行路径和日期，不将历史PASS视为当前服务器已更新。
