import PyInstaller.__main__
import os
import shutil

# --- 配置区域 ---
SCRIPT_NAME = "sc_searcher.py" 
EXE_NAME = "SC_DB_Searcher"
DATA_FILE = "data.txt"
ICON_FILE = "app_icon.ico" 
# --- 配置区域 ---

def build():
    if not os.path.exists(DATA_FILE):
        print(f"错误: 找不到 {DATA_FILE}，请确保它在当前目录下。")
        return

    args = [
        SCRIPT_NAME,
        f"--name={EXE_NAME}",
        "--onefile",              # 打包成单个独立文件
        "--noconsole",            # 运行时不显示黑色的控制台窗口
        f"--add-data={DATA_FILE};.", # 关键：将数据库文件打包进 EXE (Windows 使用 ;)
        "--clean",                # 打包前清理临时文件
        "--uac-admin",            # 重点：强制要求管理员权限启动，防止热键在游戏中失效
        # "--icon=" + ICON_FILE,  # 如果你有 .ico 图标，取消本行注释
    ]

    print(f"正在开始打包 {EXE_NAME}...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*30)
        print(f"打包成功！可执行文件位于: dist/{EXE_NAME}.exe")
        print("="*30)
    except Exception as e:
        print(f"打包过程中出现错误: {e}")

if __name__ == "__main__":
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except:
                pass
                
    build()