# 《乡巴佬》血染钟楼剧本单（非官方）

基于剧本 JSON 生成的最终版自定义剧本单。角色名称与能力文字严格取自 JSON，未改写。

## 成品文件

| 文件 | 说明 |
|------|------|
| `output/乡巴佬_剧本单.png` | A4 @ 300DPI 高清 PNG |
| `output/乡巴佬_剧本单_HD.png` | 同尺寸高清导出 |
| `output/乡巴佬_剧本单_A4.pdf` | 适合 A4 打印的 PDF |

## 版面说明

- 真实角色图标（自 JSON `image` URL 拉取；卡住的 CDN 会跳过并使用备用源）
- 左侧纵向阵营色条
- 羊皮纸纹理背景
- 古典奇幻风《乡巴佬》标题
- 镇民 / 外来者：蓝色系；爪牙 / 恶魔：红色系；传奇角色：金色系
- 双栏紧凑排版（左镇民，右外来者→爪牙→恶魔→传奇）
- 页眉注明「非官方自定义剧本」

## 重新生成

```bash
pip install pillow reportlab
mkdir -p fonts
# 推荐字体（古典标题 + 正文）
# Noto Serif CJK SC Bold/SemiBold → fonts/
# LXGW WenKai Regular → fonts/LXGWWenKai.ttf
python3 generate_script_sheet.py download-icons
python3 generate_script_sheet.py
```
