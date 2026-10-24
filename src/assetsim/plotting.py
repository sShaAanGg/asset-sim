"""matplotlib 中文字型設定：WSL 裡沒有中文字型，直接借用 Windows 的字型。"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

CANDIDATES = [
    Path("/mnt/c/Windows/Fonts/msjh.ttc"),  # 微軟正黑體
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
]


def setup_cjk_font() -> str | None:
    """註冊第一個找得到的中文字型並設為預設，回傳字型名稱 (找不到則回傳 None)。"""
    for path in CANDIDATES:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            name = font_manager.FontProperties(fname=str(path)).get_name()
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name
    return None
