"""
测试模块
包含所有后端服务的单元测试
"""
import os
import sys
import logging

# 确保可以从tests目录导入服务模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 禁用测试时的外部日志记录
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("unstructured").setLevel(logging.ERROR) 