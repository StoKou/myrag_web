#!/usr/bin/env python
"""
测试运行脚本
运行所有测试并生成报告
"""
import unittest
import os
import sys
import datetime
from unittest import TestLoader, TextTestRunner, TestSuite
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_logger_utils import test_logger, TestLoggerAdapter

def run_all_tests():
    """运行所有测试"""
    test_adapter = TestLoggerAdapter(test_logger, "TestRunner")
    test_adapter.info("=" * 60)
    test_adapter.info(f"开始测试运行: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    test_adapter.info("=" * 60)
    
    # 检查测试文件夹
    test_dir = os.path.dirname(__file__)
    
    # 创建测试加载器
    loader = TestLoader()
    
    # 从当前目录发现所有测试用例
    all_tests = loader.discover(test_dir, pattern="test_*.py")
    
    # 创建测试套件
    test_suite = TestSuite(all_tests)
    
    # 运行测试
    test_adapter.info(f"发现 {all_tests.countTestCases()} 个测试用例")
    
    # 记录开始时间
    start_time = datetime.datetime.now()
    
    # 运行测试
    runner = TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 计算运行时间
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 记录测试结果
    test_adapter.info("=" * 60)
    test_adapter.info(f"测试运行完成: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    test_adapter.info(f"运行时间: {duration:.2f} 秒")
    test_adapter.info(f"运行: {result.testsRun} | 成功: {result.testsRun - len(result.errors) - len(result.failures)} | 失败: {len(result.failures)} | 错误: {len(result.errors)}")
    
    if result.failures:
        test_adapter.error("失败的测试:")
        for failure in result.failures:
            test_adapter.error(f" - {failure[0]}")
    
    if result.errors:
        test_adapter.error("错误的测试:")
        for error in result.errors:
            test_adapter.error(f" - {error[0]}")
    
    test_adapter.info("=" * 60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 