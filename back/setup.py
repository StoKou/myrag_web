#!/usr/bin/env python
"""
初始化脚本，用于设置必要的目录结构和检查环境。
"""
import os
import sys

def create_directory_structure():
    """创建必要的目录结构"""
    directories = [
        "files/upload",
        "files/load",
        "log",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def check_environment():
    """检查环境配置"""
    try:
        import flask
        import unstructured
        import flask_cors
        print("✓ 所有必要的依赖都已安装")
    except ImportError as e:
        print(f"× 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

if __name__ == "__main__":
    print("初始化后端环境...")
    
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 创建目录结构
    create_directory_structure()
    
    # 检查环境
    if check_environment():
        print("\n初始化完成！您可以通过运行以下命令启动应用:")
        print("python app.py")
    else:
        print("\n初始化未完成，请解决上述问题后重试。")
        sys.exit(1) 