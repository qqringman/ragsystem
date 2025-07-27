#!/usr/bin/env python3
"""
測試執行腳本

使用方式：
    python run_tests.py              # 執行所有測試
    python run_tests.py --unit       # 只執行單元測試
    python run_tests.py --integration # 只執行整合測試
    python run_tests.py --coverage   # 生成覆蓋率報告
    python run_tests.py --module llm # 只測試特定模組
"""

import sys
import argparse
import subprocess
import os
from pathlib import Path


def setup_test_environment():
    """設定測試環境"""
    # 設定測試環境變數
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # 如果沒有設定 API 金鑰，使用測試金鑰
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
    
    print("✅ 測試環境已設定")


def run_tests(args):
    """執行測試"""
    # 基本的 pytest 命令
    cmd = ["pytest"]
    
    # 添加選項
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # 單元測試或整合測試
    if args.unit:
        cmd.extend(["-m", "unit"])
        print("🧪 執行單元測試...")
    elif args.integration:
        cmd.extend(["-m", "integration"])
        print("🔗 執行整合測試...")
    else:
        print("🚀 執行所有測試...")
    
    # 特定模組
    if args.module:
        test_file = f"tests/test_{args.module}.py"
        if Path(test_file).exists():
            cmd.append(test_file)
            print(f"📦 測試模組: {args.module}")
        else:
            print(f"❌ 找不到測試檔案: {test_file}")
            return 1
    
    # 覆蓋率
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
        print("📊 生成覆蓋率報告...")
    
    # 快速失敗
    if args.fail_fast:
        cmd.append("-x")
    
    # 顯示輸出
    if args.show_output:
        cmd.append("-s")
    
    # 執行測試
    print(f"執行命令: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd)
    
    # 如果生成了覆蓋率報告，顯示路徑
    if args.coverage and result.returncode == 0:
        print("\n📊 覆蓋率報告已生成:")
        print(f"   HTML 報告: {Path('htmlcov/index.html').absolute()}")
    
    return result.returncode


def run_specific_test(test_name):
    """執行特定的測試函數"""
    cmd = ["pytest", "-v", "-k", test_name]
    print(f"🎯 執行測試: {test_name}")
    return subprocess.run(cmd).returncode


def list_tests():
    """列出所有可用的測試"""
    cmd = ["pytest", "--collect-only", "-q"]
    print("📋 可用的測試:")
    print("-" * 50)
    subprocess.run(cmd)


def clean_test_artifacts():
    """清理測試產生的檔案"""
    artifacts = [
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "coverage.xml",
        "test-results",
        "vector_db/test_*",
    ]
    
    print("🧹 清理測試檔案...")
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            if path.is_dir():
                import shutil
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            print(f"   ✓ 已刪除: {artifact}")
    print("✅ 清理完成")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="RAG 系統測試執行器")
    
    # 測試類型
    test_type = parser.add_mutually_exclusive_group()
    test_type.add_argument("--unit", action="store_true", help="只執行單元測試")
    test_type.add_argument("--integration", action="store_true", help="只執行整合測試")
    
    # 測試選項
    parser.add_argument("--module", "-m", help="只測試特定模組 (llm, loader, vectorstore, db)")
    parser.add_argument("--test", "-t", help="執行特定的測試函數")
    parser.add_argument("--coverage", "-c", action="store_true", help="生成覆蓋率報告")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    parser.add_argument("--fail-fast", "-x", action="store_true", help="第一個失敗就停止")
    parser.add_argument("--show-output", "-s", action="store_true", help="顯示 print 輸出")
    
    # 其他命令
    parser.add_argument("--list", "-l", action="store_true", help="列出所有測試")
    parser.add_argument("--clean", action="store_true", help="清理測試檔案")
    
    args = parser.parse_args()
    
    # 清理命令
    if args.clean:
        clean_test_artifacts()
        return 0
    
    # 列出測試
    if args.list:
        list_tests()
        return 0
    
    # 設定測試環境
    setup_test_environment()
    
    # 執行特定測試
    if args.test:
        return run_specific_test(args.test)
    
    # 執行測試
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())