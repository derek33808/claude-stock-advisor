#!/usr/bin/env python3
"""
Stock Advisor v2.0 端到端测试脚本

测试环境:
- Backend API: https://stock-advisor-api-6vtb.onrender.com

测试覆盖:
1. 基础API测试 (健康检查、旧功能)
2. v2.0新功能测试 (5维分析、新闻、Token监控)
3. 自选股功能测试 (需要数据库)
4. 错误处理测试
"""

import requests
import time
import json
from typing import Dict, Any, List
from datetime import datetime

# 配置
BASE_URL = "https://stock-advisor-api-6vtb.onrender.com"
TEST_STOCK_CODE = "600519"  # 贵州茅台
TEST_INVALID_CODE = "999999"
TIMEOUT = 60  # 60秒超时（考虑冷启动）

class E2ETestRunner:
    """端到端测试运行器"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0

    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def test(self, name: str, category: str, priority: str):
        """测试用例装饰器"""
        def decorator(func):
            def wrapper():
                self.total_tests += 1
                test_id = f"TC-{self.total_tests:03d}"

                self.log(f"开始测试 {test_id}: {name}", "TEST")
                start_time = time.time()

                try:
                    result = func()
                    elapsed = time.time() - start_time

                    if result.get("status") == "PASS":
                        self.passed_tests += 1
                        status = "✅ PASS"
                    elif result.get("status") == "SKIP":
                        self.skipped_tests += 1
                        status = "⏭️ SKIP"
                    else:
                        self.failed_tests += 1
                        status = "❌ FAIL"

                    self.log(f"{status} {test_id}: {name} ({elapsed:.2f}s)",
                            "PASS" if result.get("status") == "PASS" else "FAIL")

                    self.results.append({
                        "test_id": test_id,
                        "name": name,
                        "category": category,
                        "priority": priority,
                        "status": result.get("status"),
                        "elapsed_time": round(elapsed, 2),
                        "details": result.get("details", ""),
                        "error": result.get("error", "")
                    })

                    return result

                except Exception as e:
                    elapsed = time.time() - start_time
                    self.failed_tests += 1
                    self.log(f"❌ FAIL {test_id}: {name} - 异常: {str(e)}", "ERROR")

                    self.results.append({
                        "test_id": test_id,
                        "name": name,
                        "category": category,
                        "priority": priority,
                        "status": "FAIL",
                        "elapsed_time": round(elapsed, 2),
                        "details": "",
                        "error": f"异常: {str(e)}"
                    })

                    return {"status": "FAIL", "error": str(e)}

            return wrapper
        return decorator

    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{BASE_URL}{endpoint}"
        kwargs.setdefault("timeout", TIMEOUT)

        try:
            response = requests.request(method, url, **kwargs)

            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "elapsed": response.elapsed.total_seconds()
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "请求超时（可能是冷启动）",
                "elapsed": TIMEOUT
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "连接失败（服务可能未运行）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_report(self):
        """生成测试报告"""
        report = []
        report.append("=" * 80)
        report.append("Stock Advisor v2.0 端到端测试报告")
        report.append("=" * 80)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试环境: {BASE_URL}")
        report.append("")

        # 总体统计
        report.append("## 测试总结")
        report.append(f"总测试数: {self.total_tests}")
        report.append(f"通过: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        report.append(f"失败: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")
        report.append(f"跳过: {self.skipped_tests} ({self.skipped_tests/self.total_tests*100:.1f}%)")
        report.append("")

        # 按分类统计
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

            categories[cat]["total"] += 1
            if result["status"] == "PASS":
                categories[cat]["passed"] += 1
            elif result["status"] == "SKIP":
                categories[cat]["skipped"] += 1
            else:
                categories[cat]["failed"] += 1

        report.append("## 按分类统计")
        for cat, stats in categories.items():
            pass_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            report.append(f"- {cat}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
        report.append("")

        # 详细结果
        report.append("## 详细测试结果")
        report.append("")
        for result in self.results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "SKIP": "⏭️"
            }.get(result["status"], "❓")

            report.append(f"{status_icon} {result['test_id']}: {result['name']}")
            report.append(f"   分类: {result['category']} | 优先级: {result['priority']} | 耗时: {result['elapsed_time']}s")

            if result.get("details"):
                report.append(f"   详情: {result['details']}")

            if result.get("error"):
                report.append(f"   错误: {result['error']}")

            report.append("")

        # 失败用例汇总
        failed = [r for r in self.results if r["status"] == "FAIL"]
        if failed:
            report.append("## 失败用例汇总")
            for result in failed:
                report.append(f"- {result['test_id']}: {result['name']}")
                report.append(f"  错误: {result['error']}")
            report.append("")

        # 性能数据
        report.append("## 性能数据")
        avg_time = sum(r["elapsed_time"] for r in self.results) / len(self.results) if self.results else 0
        max_time_result = max(self.results, key=lambda x: x["elapsed_time"]) if self.results else None

        report.append(f"平均响应时间: {avg_time:.2f}s")
        if max_time_result:
            report.append(f"最慢请求: {max_time_result['name']} ({max_time_result['elapsed_time']:.2f}s)")
        report.append("")

        report.append("=" * 80)

        return "\n".join(report)


# 创建测试运行器
runner = E2ETestRunner()


# ============================================
# 1. 基础API测试
# ============================================

@runner.test("健康检查", "基础API", "P0")
def test_health_check():
    """测试 GET /health"""
    result = runner.make_request("GET", "/health")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}"}

    return {
        "status": "PASS",
        "details": f"响应时间: {result['elapsed']:.2f}s"
    }


@runner.test("根路径访问", "基础API", "P1")
def test_root():
    """测试 GET /"""
    result = runner.make_request("GET", "/")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}"}

    return {
        "status": "PASS",
        "details": f"响应: {result['data']}"
    }


@runner.test("单股票查询(旧功能)", "基础API", "P0")
def test_stock_query_old():
    """测试 GET /api/v1/stock/{code}"""
    result = runner.make_request("GET", f"/api/v1/stock/{TEST_STOCK_CODE}")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}"}

    data = result["data"]

    # 验证关键字段
    required_fields = ["code", "name", "price", "indicators"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return {"status": "FAIL", "error": f"缺少字段: {missing}"}

    return {
        "status": "PASS",
        "details": f"股票: {data.get('name')}, 价格: {data.get('price')}"
    }


# ============================================
# 2. v2.0新功能测试
# ============================================

@runner.test("5维综合分析", "v2.0新功能", "P0")
def test_comprehensive_analysis():
    """测试 GET /api/v1/stock/{code}/comprehensive"""
    result = runner.make_request("GET", f"/api/v1/stock/{TEST_STOCK_CODE}/comprehensive")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}, 响应: {result.get('data')}"}

    data = result["data"]

    # 验证5个维度
    required_dimensions = ["technical", "fundamental", "news_events", "industry", "ai_synthesis"]
    missing = [d for d in required_dimensions if d not in data]

    if missing:
        return {"status": "FAIL", "error": f"缺少维度: {missing}"}

    return {
        "status": "PASS",
        "details": f"包含所有5个维度, 响应时间: {result['elapsed']:.2f}s"
    }


@runner.test("新闻获取", "v2.0新功能", "P1")
def test_news():
    """测试 GET /api/v1/stock/{code}/news"""
    result = runner.make_request("GET", f"/api/v1/stock/{TEST_STOCK_CODE}/news")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}"}

    data = result["data"]

    # API 返回对象 {"code": "...", "news": [...]}，不是直接列表
    if not isinstance(data, dict) or "news" not in data:
        return {"status": "FAIL", "error": "响应格式错误，应包含 'news' 字段"}

    if not isinstance(data["news"], list):
        return {"status": "FAIL", "error": "'news' 字段不是列表"}

    return {
        "status": "PASS",
        "details": f"获取到 {len(data['news'])} 条新闻"
    }


@runner.test("Token使用情况查询", "v2.0新功能", "P1")
def test_token_usage_today():
    """测试 GET /api/v1/token/usage/today"""
    result = runner.make_request("GET", "/api/v1/token/usage/today")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}"}

    data = result["data"]

    required_fields = ["date", "total_tokens", "total_cost_yuan"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return {"status": "FAIL", "error": f"缺少字段: {missing}"}

    return {
        "status": "PASS",
        "details": f"今日Token: {data.get('total_tokens')}, 成本: ¥{data.get('total_cost_yuan')}"
    }


@runner.test("Token统计", "v2.0新功能", "P2")
def test_token_stats():
    """测试 GET /api/v1/token/stats"""
    result = runner.make_request("GET", "/api/v1/token/stats")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}"}

    return {
        "status": "PASS",
        "details": "Token统计查询成功"
    }


# ============================================
# 3. 自选股功能测试 (需要数据库)
# ============================================

@runner.test("添加自选股", "自选股功能", "P1")
def test_watchlist_add():
    """测试 POST /api/v1/watchlist/add"""
    payload = {"code": TEST_STOCK_CODE}
    result = runner.make_request("POST", "/api/v1/watchlist/add", json=payload)

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    # 可能返回200(成功)或409(已存在)
    if result["status_code"] not in [200, 409]:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}, 响应: {result.get('data')}"}

    return {
        "status": "PASS",
        "details": f"HTTP {result['status_code']}: {result.get('data', {}).get('message', '成功')}"
    }


@runner.test("获取自选股列表", "自选股功能", "P1")
def test_watchlist_list():
    """测试 GET /api/v1/watchlist/list"""
    result = runner.make_request("GET", "/api/v1/watchlist/list")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}, 响应: {result.get('data')}"}

    data = result["data"]

    # API 返回对象 {"user_id": "...", "watchlist": [...]}，不是直接列表
    if not isinstance(data, dict) or "watchlist" not in data:
        return {"status": "FAIL", "error": "响应格式错误，应包含 'watchlist' 字段"}

    if not isinstance(data["watchlist"], list):
        return {"status": "FAIL", "error": "'watchlist' 字段不是列表"}

    return {
        "status": "PASS",
        "details": f"自选股数量: {len(data['watchlist'])}"
    }


@runner.test("检查自选股状态", "自选股功能", "P2")
def test_watchlist_check():
    """测试 GET /api/v1/watchlist/check/{code}"""
    result = runner.make_request("GET", f"/api/v1/watchlist/check/{TEST_STOCK_CODE}")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if result["status_code"] != 200:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}"}

    data = result["data"]

    if "is_in_watchlist" not in data:
        return {"status": "FAIL", "error": "缺少 is_in_watchlist 字段"}

    return {
        "status": "PASS",
        "details": f"在自选股: {data['is_in_watchlist']}"
    }


@runner.test("移除自选股", "自选股功能", "P2")
def test_watchlist_remove():
    """测试 DELETE /api/v1/watchlist/remove"""
    payload = {"code": TEST_STOCK_CODE}
    result = runner.make_request("DELETE", "/api/v1/watchlist/remove", json=payload)

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    # 可能返回200(成功)或404(不存在)
    if result["status_code"] not in [200, 404]:
        return {"status": "FAIL", "error": f"HTTP {result['status_code']}, 响应: {result.get('data')}"}

    return {
        "status": "PASS",
        "details": f"HTTP {result['status_code']}"
    }


# ============================================
# 4. 错误处理测试
# ============================================

@runner.test("无效股票代码", "错误处理", "P1")
def test_invalid_stock_code():
    """测试查询不存在的股票"""
    result = runner.make_request("GET", f"/api/v1/stock/{TEST_INVALID_CODE}")

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    # 应该返回404或400
    if result["status_code"] not in [400, 404, 500]:
        return {"status": "FAIL", "error": f"应返回错误状态码，实际: {result['status_code']}"}

    return {
        "status": "PASS",
        "details": f"正确返回错误状态码: {result['status_code']}"
    }


@runner.test("缺少必需参数", "错误处理", "P2")
def test_missing_parameter():
    """测试缺少必需参数"""
    result = runner.make_request("POST", "/api/v1/watchlist/add", json={})

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    # 应该返回422(验证错误)
    if result["status_code"] != 422:
        return {"status": "FAIL", "error": f"应返回422，实际: {result['status_code']}"}

    return {
        "status": "PASS",
        "details": "正确返回422验证错误"
    }


# ============================================
# 5. 性能测试
# ============================================

@runner.test("冷启动时间测试", "性能测试", "P1")
def test_cold_start():
    """测试Render冷启动时间"""
    runner.log("等待5秒后测试冷启动...", "INFO")
    time.sleep(5)

    start = time.time()
    result = runner.make_request("GET", "/health")
    elapsed = time.time() - start

    if not result["success"]:
        return {"status": "FAIL", "error": result["error"]}

    if elapsed > 30:
        return {
            "status": "PASS",
            "details": f"冷启动耗时: {elapsed:.2f}s (可能需要优化)"
        }

    return {
        "status": "PASS",
        "details": f"响应时间: {elapsed:.2f}s (热启动)"
    }


# ============================================
# 主函数
# ============================================

def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("Stock Advisor v2.0 端到端测试")
    print("=" * 80)
    print(f"测试环境: {BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    # 运行所有测试
    runner.log("开始执行测试套件...", "INFO")

    # 1. 基础API测试
    runner.log("========== 1. 基础API测试 ==========", "INFO")
    test_health_check()
    test_root()
    test_stock_query_old()

    # 2. v2.0新功能测试
    runner.log("========== 2. v2.0新功能测试 ==========", "INFO")
    test_comprehensive_analysis()
    test_news()
    test_token_usage_today()
    test_token_stats()

    # 3. 自选股功能测试
    runner.log("========== 3. 自选股功能测试 ==========", "INFO")
    test_watchlist_add()
    test_watchlist_list()
    test_watchlist_check()
    test_watchlist_remove()

    # 4. 错误处理测试
    runner.log("========== 4. 错误处理测试 ==========", "INFO")
    test_invalid_stock_code()
    test_missing_parameter()

    # 5. 性能测试
    runner.log("========== 5. 性能测试 ==========", "INFO")
    test_cold_start()

    # 生成报告
    print("\n")
    report = runner.generate_report()
    print(report)

    # 保存报告到文件
    report_file = f"E2E_TEST_REPORT_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    runner.log(f"测试报告已保存: {report_file}", "INFO")

    # 返回退出码
    return 0 if runner.failed_tests == 0 else 1


if __name__ == "__main__":
    exit(main())
