# 《乡巴佬》血染钟楼剧本单（非官方）

按官方 **Trouble Brewing** 剧本单版式生成的自定义成品：左侧纵向阵营色条（竖排阵营名）、镇民双栏铺开、阵营间横线分隔、羊皮纸星点底纹、暗红古典标题、单色阵营着色图标。

角色 **名称 / 能力** 严格取自 `script.json`，未改写。

## 成品

| 文件 | 说明 |
|------|------|
| `output/乡巴佬_剧本单.png` | A4 @ 300DPI 高清 PNG |
| `output/乡巴佬_剧本单_HD.png` | 同尺寸高清导出 |
| `output/乡巴佬_剧本单_A4.pdf` | A4 打印 PDF |

## 重新生成

```bash
pip install pillow reportlab
python3 generate_script_sheet.py download-icons
python3 generate_script_sheet.py
```

字体首次运行会自动下载到 `fonts/`（Noto Serif CJK + 霞鹜文楷）。
