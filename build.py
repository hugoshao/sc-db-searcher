import PyInstaller.__main__
import os
import shutil

# ================= 配置区域 =================
main_script = "sc_searcher.py" 
data_file = "data.txt"
exe_name = "SC_DB_Searcher"
icon_file = None 
# ===========================================

def build():
    print("开始清理旧的构建文件...")
    for path in ['build', 'dist']:
        if os.path.exists(path):
            shutil.rmtree(path)
            
    print(f"正在打包 {exe_name} v1.1 ...")
    
    params = [
        main_script,
        '--onefile',            # 打包成单文件
        '--noconsole',          # 运行时不显示黑窗口
        f'--name={exe_name}',   # 指定程序名称
        f'--add-data={data_file}{os.pathsep}.', # 包含数据库文件
        '--clean',              # 打包前清理缓存
        '--uac-admin',          # !!! 核心：强制程序以管理员权限启动
    ]

    # 如果有图标，加入图标参数
    if icon_file and os.path.exists(icon_file):
        params.append(f'--icon={icon_file}')

    # 执行打包
    PyInstaller.__main__.run(params)

    print("\n" + "="*30)
    print(f"打包完成！程序位置: dist/{exe_name}.exe")
    print("注意：请确保 dist 目录下有 data.txt，或者程序已将其打包进内部。")
    print("="*30)

if __name__ == "__main__":
    build()