# N1 数据接入与当前软件证据

本目录的原始 DATA100、DATA30、CONVERTER 说明及
`tools/kwt-x14-w12-b32/convert_kwt1_x14_w12_b32.py`按 PR #9 提交
`50c1261f3f7fafe1531e05e023aadd926cefa24a`逐字节导入，未修改转换器的30条CLI入口。
转换器 SHA-256：`c99301b68185f599b95e4b4b3cbe5e62db27128dcf3cf04e4725bdb9a5620c35`。
原说明中“未上传”的文字属于该固定提交的历史状态；项目新计划记录的
`hex_short_all`到位情况需依实际服务器回执核验，不能据本导入文档推断实时服务器状态。

## 新入口和数值身份

`workspaces/arch03/scripts/n1_data.py`独立读取原group8文件，不经过旧Q12批量入口。
`source_case`核文件哈希、X14/W12符号扩展、三半字b32、严格9字符33位total。
`inspect_case`使用Python不定长整数逐k累加，检查全部前缀累加范围及每个坐标的
total/result/saturated；不复用旧Q12参考或浮点误差。

`prepare_case(source,destination)`只写新目录：保留原group8来源哈希，独立坐标核对
tile16排列，再通过`n1_codec.py`生成新身份的无损v3载荷。布局为`0x00100004`，
数值身份`0x000e0c20`，SHIFT=10。全局头仍32字节，仅第2/7字与B0不同；原算法、
W0/b→X→W1/b…顺序、16位传输容器、三半字偏置均保持。源数据非法符号扩展会拒绝，
不会截断后继续。解码端也再次检查缩位范围。

生成的`load.bin/load.hex/load32.hex`是规范tile16数据；`codec.bin/codec32.hex`是实际
源端运行载荷。`total.hex/result.hex/saturated.hex/expected.npz`只用于验证，不能进入
硬件运算。`verify_prepared`重新检查来源、全部运行文件、排列、参考副本及编码依赖哈希。

实际写回捕获必须为五列十进制`row,col,result,saturated,total`。允许输出乱序，但严格
要求25344个唯一合法坐标，并逐坐标核对signed33 total、signed16结果及饱和标志；拒绝旧4列格式。

## 100条数据身份

`ae052bc1e543930abece8202a5b1439dcbd50dd4f5d7d09fb8f049eb30eeb997`
是`SHA256_FILES.json`的SHA，不是`manifest.json`的SHA。
`n1_data.index_dataset`绑定该清单，核准100×12×4精确文件集合、每个大小/哈希、格式与层号；
同时记录实际根manifest和每层layout的SHA。原样本命名是`sample_001`至`sample_100`。

`n1_batch.py`是独立的一次编译1200任务ASIC/E203入口，限定layout4/SHIFT10/真实IRQ，
正式运行前检查空间20%余量，结束后重新审查源数据、原始捕获和回执。该工具尚未执行服务器
1200任务；它的存在不构成硬件验收。完整浮点100源目前未由本软件工作线取得，100条新精度
审核仍未完成；原PR软件误差只作为来源信息。

## 本地已执行

固定12性能任务取自B0同一组完整浮点张量：
`architectures/arch01_serial_mac/v1.3.0/KWT1/model_data/outputs/real_sample_001/layer_01..12/float_tensors.npz`。
调用原PR转换器重新量化，加极值、舍入两例，共14任务/354816个输出逐位软件核对通过。
输出目录是`workspaces/arch03/local_runs/n1_data14_20261113_02`；其中source保持group8，
prepared供本轮本地DMA验证。01目录保留为首次准备记录，因工具API增加后哈希改变，不用作正式输入。

12真实层的X/W/b裁剪和最终饱和均为0，最大NRMSE为0.1425636423408142%。每例保存新SSE、
参考能量、原float文件哈希和转换器身份。它不代表完整100条、官方600条或RTL通过。
新编码长度依次为31428、30220、29572、29732、28908、28300、27596、27788、27612、
29180、31516、35220字节，平均29756字节。编码算法未变，数据重新量化仍会改变压缩长度，
不能把完整吞吐变化全部归因乘法器缩位。

两定向例检查total范围-3221094400至3220570175，确认超signed32但仍在signed33内；
分别覆盖10197与6732个饱和输出。14项单元测试覆盖新旧身份拒绝、原payload保持、坏头、
截断、符号扩展、33位读入、篡改哈希、坐标乱序/重复/缺漏、精确文件集合及空间不足先于编译。

```text
python -m unittest discover -s workspaces/arch03/scripts -p test_n1_data.py -v
python workspaces/arch03/scripts/n1_data.py local14 <固定12浮点根> <不存在的新目录>
python workspaces/arch03/scripts/n1_data.py check <一个group8层目录>
python workspaces/arch03/scripts/n1_data.py verify <group8源> <新准备目录>
```

本记录仅是软件接入证据。N1 ASIC/E203、1200、门级、PPA和同批完整100浮点精度门槛
必须分别取得新证据，不能继承B0的PASS。

## 独立整合审查补充

`test_n1_integration.py`另有10项检查通过：实际已编译IRQ固件的ELF/来源/身份、
SHIFT10与旧布局拒绝、无任务预填边界、从生产C直接抽取的配置校验函数、
批量正式身份建立路径、SysMem106位约束、N1专属活动计数格式/有效位、SoC监视器。
审查修复了新`n1_batch.py`中`server_run.sha`参数须为Path的问题；修复发生在任何服务器
批量执行之前，未改数据、codec或本地02用例身份。

监视器测试通过真实Vivado编译、展开和7种fixture执行，将-3221094400与3220570175
两个实际signed33总和值保留到对应共享写ACK，并核对五列CSV。错误total、重复total、
过期结果区标签、末组无效第五行、写ACK前缺少total、重复写ACK均被拒绝。
fixture只模拟层次端点，不执行E203或算术核心，不代表ASIC/SoC通过。

回执见`N1_INTEGRATION_CHECK_20261113.json`；对应保存目录
`local_runs/n1_monitor_fixture_20261113_011657_478498`。
