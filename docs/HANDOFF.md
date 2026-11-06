# 队友协作与交接

## 加入私人仓库

队友先提供 GitHub 用户名或邮箱。所有者在仓库 Settings → Collaborators 中建立指定对象的邀请，队友登录对应账号接受后再 clone。不能只转发仓库 URL 就获得权限；没有供任意持有者加入的通用邀请码。

## 日常上传

```bash
git switch main
git pull --ff-only
git switch -c feature/your-topic
# 修改代码、同步文档、执行对应验证
git add <明确的文件或目录>
git commit -m "Describe the architecture change"
git push -u origin feature/your-topic
```

在 GitHub 创建 PR，说明修改内容、验证命令与结果，请队友 review。合并后再基于最新 main 开始下一项工作。不要强推共享 main。

## 交接资料

- 架构说明：计算范围、数据通路、状态机、端口及握手时序。
- 数值协议：位宽、小数位、偏置尺度、舍入和饱和定义。
- 测试数据：来源、层号、样本号、布局、整数参考生成方式。
- 验证：可复现命令、工具版本、最终 PASS/FAIL、未验证内容。
- 已知问题与后续工作：区分已实现、已验证、规划。

新版本使用 [架构说明模板](../templates/ARCHITECTURE.md)。大型 checkpoint、音频、波形由约定的资料存储位置交接，Git 中记录来源和校验信息；不要上传访问令牌、密码或个人配置。
