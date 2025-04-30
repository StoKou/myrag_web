#!/usr/bin/env python
"""
初始化脚本，用于设置必要的目录结构和检查环境。
"""
import os
import sys
import unittest
import importlib
import time
from datetime import datetime
import re # 添加 re 模块用于解析 requirements.txt

def create_directory_structure():
    """创建必要的目录结构"""
    directories = [
        "files/upload",
        "files/load",
        "log",
        "tests"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def check_environment():
    """检查环境配置，从 requirements.txt 读取依赖"""
    requirements_path = "requirements.txt"
    if not os.path.exists(requirements_path):
        print(f"× 找不到依赖文件: {requirements_path}")
        print("请确保 requirements.txt 文件存在于脚本所在目录。")
        return False

    print(f"正在从 {requirements_path} 检查依赖...")
    missing_packages = []
    try:
        with open(requirements_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 解析包名，移除版本号、注释等
                # 使用正则表达式查找第一个版本限定符或特殊符号
                match = re.match(r'^\s*([a-zA-Z0-9_.-]+)', line)
                if not match:
                    continue # 跳过无法解析的行

                package_name = match.group(1)
                # 处理一些特殊情况，例如包名包含连字符，但导入时用下划线
                import_name = package_name.replace('-', '_')

                try:
                    importlib.import_module(import_name)
                    # print(f"✓ 检查通过: {package_name}") # 可以取消注释以显示每个包的检查结果
                except ImportError:
                    missing_packages.append(package_name)

    except Exception as e:
        print(f"× 读取或解析 {requirements_path} 时出错: {e}")
        return False

    if not missing_packages:
        print("✓ 所有必要的依赖都已安装")
        return True
    else:
        print("× 检测到缺失的依赖:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print(f"\n请运行以下命令安装缺失的依赖:")
        print(f"pip install -r {requirements_path}")
        return False

def run_tests():
    """运行服务的测试代码，并记录结果到日志文件"""
    try:
        # 动态导入测试日志工具
        from tests.test_logger_utils import test_logger, TestLoggerAdapter
    except ImportError:
        print("× 找不到测试日志工具，请确保 tests/test_logger_utils.py 文件存在")
        return False
    
    overall_logger = TestLoggerAdapter(test_logger, "整体测试")
    
    test_start_time = datetime.now()
    overall_logger.info("="*50)
    overall_logger.info(f"开始测试运行 - 时间: {test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    overall_logger.info("="*50)
    
    # 自动加载和运行所有测试
    test_dir = "tests"
    if not os.path.exists(test_dir):
        overall_logger.error(f"找不到测试目录: {test_dir}")
        return False
    
    # 获取所有测试文件
    test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py") and f != "test_logger_utils.py"]
    
    if not test_files:
        overall_logger.warning("没有找到测试文件")
        return False
    
    overall_logger.info(f"找到 {len(test_files)} 个测试文件:")
    for i, test_file in enumerate(test_files, 1):
        overall_logger.info(f"{i}. {test_file}")
    
    # 测试结果统计
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    error_tests = 0
    
    # 逐个运行测试模块
    for test_file in sorted(test_files):
        module_name = f"tests.{test_file[:-3]}"  # 移除 .py 扩展名
        module_logger = TestLoggerAdapter(test_logger, module_name)
        
        try:
            # 模块测试开始时间
            module_start_time = time.time()
            module_logger.log_test_start()
            
            # 动态导入测试模块
            module = importlib.import_module(module_name)
            
            # 创建测试加载器和套件
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # 自定义测试结果类，记录日志
            class LoggingTestResult(unittest.TextTestResult):
                def startTest(self, test):
                    super().startTest(test)
                    test_name = test._testMethodName
                    module_logger.debug(f"开始执行测试用例: {test_name}")
                
                def addSuccess(self, test):
                    super().addSuccess(test)
                    test_name = test._testMethodName
                    module_logger.log_test_result(test_name, success=True)
                    nonlocal passed_tests
                    passed_tests += 1
                
                def addFailure(self, test, err):
                    super().addFailure(test, err)
                    test_name = test._testMethodName
                    error_message = self._exc_info_to_string(err, test)
                    module_logger.log_test_result(test_name, success=False, error=error_message)
                    nonlocal failed_tests
                    failed_tests += 1
                
                def addError(self, test, err):
                    super().addError(test, err)
                    test_name = test._testMethodName
                    error_message = self._exc_info_to_string(err, test)
                    module_logger.log_test_result(test_name, success=False, error=error_message)
                    nonlocal error_tests
                    error_tests += 1
            
            # 运行测试
            runner = unittest.TextTestRunner(resultclass=LoggingTestResult, verbosity=2)
            result = runner.run(suite)
            
            # 计算模块测试时间
            module_duration = time.time() - module_start_time
            
            # 记录模块测试结果
            total_tests += result.testsRun
            module_logger.log_test_end(
                success=len(result.failures) == 0 and len(result.errors) == 0,
                duration=module_duration
            )
            module_logger.info("-"*50)
            
        except Exception as e:
            module_logger.error(f"测试模块 {module_name} 运行失败: {str(e)}")
            error_tests += 1
    
    # 测试结束时间和总耗时
    test_end_time = datetime.now()
    test_duration = (test_end_time - test_start_time).total_seconds()
    
    # 记录总体测试结果
    overall_logger.info("="*50)
    overall_logger.info("测试结果统计:")
    overall_logger.info(f"运行: {total_tests} 个测试用例")
    overall_logger.info(f"通过: {passed_tests} 个测试用例")
    overall_logger.info(f"失败: {failed_tests} 个测试用例")
    overall_logger.info(f"错误: {error_tests} 个测试用例")
    overall_logger.info(f"总时长: {test_duration:.2f} 秒")
    overall_logger.info(f"结束时间: {test_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    overall_logger.info("="*50)
    
    return failed_tests == 0 and error_tests == 0

if __name__ == "__main__":
    print("初始化后端环境...")
    
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 创建目录结构
    create_directory_structure()
    
    # 检查环境
    env_ok = check_environment()
    
    if not env_ok:
        print("\n初始化未完成，请解决上述问题后重试。")
        sys.exit(1)
    
    print("\n初始化完成！")
    
    # 询问用户是否运行测试
    user_input = input("\n是否运行测试代码? (y/n): ")
    if user_input.lower() in ['y', 'yes']:
        print("\n正在运行测试，测试结果将输出到 log/test_result.log 文件中...")
        tests_passed = run_tests()
        
        if tests_passed:
            print("\n所有测试均已通过! 详细结果请查看日志文件。")
        else:
            print("\n测试未全部通过，请查看日志文件获取详细信息。")
    
    print("\n您可以通过运行以下命令启动应用:")
    print("python app.py") 