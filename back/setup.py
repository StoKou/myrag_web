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
    print(f"脚本使用的 Python 解释器: {sys.executable}")
    print(f"脚本的模块搜索路径 (sys.path): {sys.path}")
    if not os.path.exists(requirements_path):
        print(f"× 找不到依赖文件: {requirements_path}")
        print("请确保 requirements.txt 文件存在于脚本所在目录。")
        return False

    print(f"正在从 {requirements_path} 检查依赖...")
    missing_packages = []
    
    # Mapping from package name (in requirements.txt) to import name
    import_name_map = {
        "Flask": "flask",           # Import 'flask', not 'Flask'
        "Flask-Cors": "flask_cors", # Import 'flask_cors', not 'Flask_Cors'
        "pdfminer.six": "pdfminer",
        "python-dotenv": "dotenv",
        "python-magic": "magic",
        "requests": "requests",     # Add requests package mapping
        # Add other known mappings if needed
    }
    # Packages to potentially skip checking due to complex import structure (e.g., namespaces)
    # Alternatively, check the top-level namespace if sufficient
    check_base_namespace_prefixes = ("llama-index-",) # Check 'llama_index' for these

    checked_namespaces = set() # To avoid checking 'llama_index' multiple times

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
                import_name_to_try = None # Reset for each package

                # Determine the correct import name
                if package_name in import_name_map:
                    import_name_to_try = import_name_map[package_name]
                elif package_name.startswith(check_base_namespace_prefixes):
                     # Check the base namespace once
                     base_namespace = "llama_index" # Assuming this is the common base
                     if base_namespace not in checked_namespaces:
                         import_name_to_try = base_namespace
                         checked_namespaces.add(base_namespace)
                         # Store the original package name for potential error reporting
                         original_package_name_for_namespace = package_name 
                     else:
                         # Already checked the base namespace, skip redundant check for this specific sub-package
                         # print(f"ⓘ Skipping redundant namespace check for: {package_name}")
                         continue 
                else:
                    # Default: replace hyphen with underscore
                    import_name_to_try = package_name.replace('-', '_')

                # Try importing if we determined an import name
                if import_name_to_try:
                    try:
                        importlib.import_module(import_name_to_try)
                        # print(f"✓ 检查通过: {package_name} (using import {import_name_to_try})") 
                    except ImportError:
                        # If the base namespace check failed, report the original package name
                        if package_name.startswith(check_base_namespace_prefixes) and import_name_to_try == base_namespace:
                             missing_packages.append(f"{original_package_name_for_namespace} (无法导入基础模块 '{base_namespace}')")
                             # Prevent further checks for this namespace if base failed
                             checked_namespaces.add(base_namespace) 
                        else:
                             missing_packages.append(f"{package_name} (无法导入模块 '{import_name_to_try}')")
                    except Exception as import_err: # Catch other potential import errors
                        print(f"⚠ 检查 {package_name} (尝试导入 {import_name_to_try}) 时发生错误: {import_err}")
                        missing_packages.append(f"{package_name} (检查时出错)")
                else:
                    # This case should ideally not happen with the logic above, but as a safeguard:
                    print(f"⁇ 未能确定包 '{package_name}' 的导入名称，跳过检查。")


    except Exception as e:
        print(f"× 读取或解析 {requirements_path} 时出错: {e}")
        return False

    if not missing_packages:
        print("✓ 所有必要的依赖都已安装")
        return True
    else:
        print("× 检测到缺失的依赖或检查时出错:")
        for pkg_info in missing_packages:
            print(f"  - {pkg_info}")
        print(f"\n请再次确认这些依赖是否正确安装在以下环境中:")
        print(f"  解释器: {sys.executable}")
        print(f"如果确认已安装，可能是脚本检查逻辑仍需调整。或者尝试重新安装:")
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