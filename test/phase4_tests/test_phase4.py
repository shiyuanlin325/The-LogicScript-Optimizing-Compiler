import os
import sys

# 路径配置
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TEST_DIR))
sys.path.append(PROJECT_ROOT)

# 导入你的Phase4核心函数
from logic_compiler import run_execution_phase, ExecutionError

def run_test_case(filename: str) -> bool:
    filepath = os.path.join(TEST_DIR, filename)
    print(f"Test Case: {filename}")
    print("-" * 50)

    # 自动判断：文件名带_error = 负向用例（预期报错）
    is_negative_test = "_error" in filename

    try:
        # 读取AST输入
        with open(filepath, "r", encoding="utf-8") as f:
            ast_input = eval(f.read())

        # 运行你的Phase4
        output = run_execution_phase(ast_input)

        # 正向用例：不报错 = 成功
        if not is_negative_test:
            print("[STATUS] PASSED (正向用例：正常执行)")
            print(f"最终变量: {output['final_state_dictionary']}")
            print(f"打印记录: {output['printed_output']}")
            return True

        # 负向用例：没报错 = 失败
        else:
            print("[STATUS] FAILED (负向用例：应该报错但没报)")
            return False

    except ExecutionError as e:
        # 负向用例：抛对错 = 成功
        if is_negative_test:
            print("[STATUS] PASSED (负向用例：正确抛出ExecutionError)")
            print(f"错误信息: {str(e)}")
            return True

        # 正向用例：报错 = 失败
        else:
            print("[STATUS] FAILED (正向用例：不该报错却报错)")
            print(f"错误信息: {str(e)}")
            return False

    except Exception as e:
        # 任何崩溃 = 全失败
        print("[STATUS] FAILED (代码崩溃：Python原生错误)")
        print(f"异常: {str(e)}")
        return False

def batch_test():
    print("=" * 60)
    print("Phase4 万能测试（自动识别正向/负向用例）")
    print("=" * 60)

    # 读取所有txt测试文件
    test_files = sorted([f for f in os.listdir(TEST_DIR) if f.endswith(".txt")])
    if not test_files:
        print("未找到测试文件")
        return

    passed = 0
    failed = 0
    for file in test_files:
        if run_test_case(file):
            passed += 1
        else:
            failed += 1
        print("-" * 60 + "\n")

    print("=" * 60)
    print("测试报告")
    print(f"总用例: {len(test_files)} | 通过: {passed} | 失败: {failed}")
    print("=" * 60)

if __name__ == "__main__":
    batch_test()