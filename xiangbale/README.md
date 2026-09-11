# 《乡巴佬》血染钟楼剧本单（非官方）

按官方 Trouble Brewing 版式生成的自定义成品。角色名称、能力、夜晚顺序与说书人提示均严格取自 `script.json`。

## 成品

| 文件 | 说明 |
|------|------|
| `output/乡巴佬_剧本单.png` | 角色表 A4 @ 300DPI（大字铺满） |
| `output/乡巴佬_剧本单_HD.png` | 角色表高清导出 |
| `output/乡巴佬_剧本单_A4.pdf` | 角色表 A4 打印 PDF |
| `output/乡巴佬_夜晚顺序.png` | 夜晚顺序横版 A4 @ 300DPI |
| `output/乡巴佬_夜晚顺序_HD.png` | 夜晚顺序高清导出 |
| `output/乡巴佬_夜晚顺序_A4.pdf` | 夜晚顺序横向 A4 PDF |

## 重新生成

```bash
pip install pillow reportlab
python3 generate_script_sheet.py download-icons
python3 generate_script_sheet.py
python3 generate_night_order.py
```
