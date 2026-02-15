#!/usr/bin/env python3
"""
Stock Advisor v3.0 端到端测试脚本

测试范围:
1. 智能缓存功能
2. 批量加载 API  
3. AI 股票问答
4. v2.0 功能回归测试

测试环境:
- Backend: https://stock-advisor-api-6vtb.onrender.com
- Frontend: https://my-stock-advisor.netlify.app
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# 配置
BASE_URL = "https://stock-advisor-api-6vtb.onrender.com/api/v1"
TIMEOUT = 90  # Render 冷启动可能需要 60s

# 测试用股票代码
TEST_STOCK_CODES = ["000001", "600519", "512930"]  # 平安银行、贵州茅台、中证500ETF
TEST_USER_ID = "test_e2e_v3"


class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []
    
    def add_result(self, category: str, name: str, status: str, 
                   message: str = "", response_time: float = 0):
        """添加测试结果"""
        self.total += 1
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1
        
        self.results.append({
            "category": category,
            "name": name,
            "status": status,
            "message": message,
            "response_time": f"{response_time:.2f}s" if response_time > 0 else "N/A",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("Stock Advisor v3.0 E2E Test Summary")
        print("="*80)
        print(f"\nTotal Tests: {self.total}")
        print(f"✅ Passed: {self.passed} ({self.passed/self.total*100:.1f}%)")
        print(f"❌ Failed: {self.failed} ({self.failed/self.total*100:.1f}%)")
        print(f"⚠️  Warnings: {self.warnings} ({self.warnings/self.total*100:.1f}%)")
        
        # 按类别分组显示
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            categories[cat][result["status"]] += 1
        
        print("\n" + "-"*80)
        print("Results by Category:")
        print("-"*80)
        for cat, counts in categories.items():
            total_cat = sum(counts.values())
            pass_rate = counts["PASS"] / total_cat * 100
            print(f"\n{cat}: {counts['PASS']}/{total_cat} ({pass_rate:.1f}%)")
            print(f"  ✅ Pass: {counts['PASS']}  ❌ Fail: {counts['FAIL']}  ⚠️  Warn: {counts['WARN']}")
        
        # 详细结果
        print("\n" + "="*80)
        print("Detailed Test Results:")
        print("="*80)
        for result in self.results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}[result["status"]]
            print(f"\n{status_icon} [{result['category']}] {result['name']}")
            print(f"   Status: {result['status']} | Time: {result['response_time']}")
            if result["message"]:
                print(f"   Message: {result['message']}")


# 全局测试结果
test_result = TestResult()


def test_cache_single_stock():
    """测试1: 单股缓存功能"""
    print("\n" + "="*80)
    print("Test 1: 单股缓存功能测试")
    print("="*80)
    
    code = TEST_STOCK_CODES[0]
    
    # 1.1 首次查询 (应该从 L3 数据源获取)
    print(f"\n1.1 首次查询股票 {code} (预期: 从数据源获取)...")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/stock/{code}?refresh=true", timeout=TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查 cache_info 字段
            if "cache_info" in data:
                cache_info = data["cache_info"]
                print(f"   ✅ 返回 cache_info: {cache_info}")
                
                # 验证字段
                required_fields = ["hit", "level", "age_seconds"]
                missing = [f for f in required_fields if f not in cache_info]
                
                if not missing:
                    test_result.add_result(
                        "缓存功能", 
                        "单股查询返回 cache_info", 
                        "PASS",
                        f"cache_info 完整: {cache_info}",
                        elapsed
                    )
                else:
                    test_result.add_result(
                        "缓存功能",
                        "单股查询返回 cache_info",
                        "FAIL", 
                        f"cache_info 缺少字段: {missing}",
                        elapsed
                    )
            else:
                test_result.add_result(
                    "缓存功能",
                    "单股查询返回 cache_info",
                    "FAIL",
                    "响应中没有 cache_info 字段",
                    elapsed
                )
        else:
            test_result.add_result(
                "缓存功能",
                "单股查询返回 cache_info",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "缓存功能",
            "单股查询返回 cache_info",
            "FAIL",
            f"请求异常: {str(e)}"
        )
    
    # 1.2 立即再次查询 (应该从 L1 内存缓存命中)
    print(f"\n1.2 立即再次查询 {code} (预期: L1 内存缓存命中)...")
    time.sleep(1)
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/stock/{code}", timeout=TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            cache_info = data.get("cache_info", {})
            
            if cache_info.get("hit") and cache_info.get("level") == "L1":
                test_result.add_result(
                    "缓存功能",
                    "L1 内存缓存命中",
                    "PASS",
                    f"age_seconds: {cache_info.get('age_seconds')}",
                    elapsed
                )
            else:
                test_result.add_result(
                    "缓存功能",
                    "L1 内存缓存命中",
                    "WARN",
                    f"预期 L1 命中,实际: {cache_info}",
                    elapsed
                )
        else:
            test_result.add_result(
                "缓存功能",
                "L1 内存缓存命中",
                "FAIL",
                f"HTTP {response.status_code}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "缓存功能",
            "L1 内存缓存命中",
            "FAIL",
            f"请求异常: {str(e)}"
        )


def test_batch_loading():
    """测试2: 批量加载 API"""
    print("\n" + "="*80)
    print("Test 2: 批量加载 API 测试")
    print("="*80)
    
    codes = ",".join(TEST_STOCK_CODES)
    
    print(f"\n2.1 批量查询 {len(TEST_STOCK_CODES)} 只股票...")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/stocks/batch?codes={codes}", timeout=TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查返回结构
            if "stocks" in data and isinstance(data["stocks"], list):
                returned_count = len(data["stocks"])
                expected_count = len(TEST_STOCK_CODES)
                
                if returned_count == expected_count:
                    test_result.add_result(
                        "批量加载",
                        "批量查询返回正确数量",
                        "PASS",
                        f"返回 {returned_count}/{expected_count} 只股票",
                        elapsed
                    )
                    
                    # 检查每只股票是否有 cache_info
                    stocks_with_cache = sum(1 for s in data["stocks"] if "cache_info" in s)
                    if stocks_with_cache == returned_count:
                        test_result.add_result(
                            "批量加载",
                            "批量查询返回 cache_info",
                            "PASS",
                            f"{stocks_with_cache}/{returned_count} 股票含 cache_info",
                            0
                        )
                    else:
                        test_result.add_result(
                            "批量加载",
                            "批量查询返回 cache_info",
                            "WARN",
                            f"仅 {stocks_with_cache}/{returned_count} 股票含 cache_info",
                            0
                        )
                else:
                    test_result.add_result(
                        "批量加载",
                        "批量查询返回正确数量",
                        "FAIL",
                        f"预期 {expected_count} 只,实际 {returned_count} 只",
                        elapsed
                    )
            else:
                test_result.add_result(
                    "批量加载",
                    "批量查询返回正确数量",
                    "FAIL",
                    "响应缺少 stocks 数组",
                    elapsed
                )
        else:
            test_result.add_result(
                "批量加载",
                "批量查询返回正确数量",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "批量加载",
            "批量查询返回正确数量",
            "FAIL",
            f"请求异常: {str(e)}"
        )


def test_ai_chat():
    """测试3: AI 股票问答"""
    print("\n" + "="*80)
    print("Test 3: AI 股票问答功能测试")
    print("="*80)
    
    code = TEST_STOCK_CODES[1]  # 使用贵州茅台测试
    
    # 3.1 发起问答
    print(f"\n3.1 向股票 {code} 发起问答...")
    start_time = time.time()
    try:
        payload = {
            "question": "这只股票的近期表现如何?",
            "user_id": TEST_USER_ID
        }
        response = requests.post(
            f"{BASE_URL}/stock/{code}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查必需字段
            required_fields = ["answer", "tokens_used", "remaining_quota"]
            missing = [f for f in required_fields if f not in data]
            
            if not missing:
                answer = data["answer"]
                tokens = data["tokens_used"]
                remaining = data["remaining_quota"]
                
                # 检查答案不为空
                if answer and len(answer) > 10:
                    test_result.add_result(
                        "AI 问答",
                        "问答接口返回有效答案",
                        "PASS",
                        f"答案长度: {len(answer)} 字符, tokens: {tokens}, 剩余: {remaining}",
                        elapsed
                    )
                else:
                    test_result.add_result(
                        "AI 问答",
                        "问答接口返回有效答案",
                        "FAIL",
                        f"答案过短或为空: {answer}",
                        elapsed
                    )
            else:
                test_result.add_result(
                    "AI 问答",
                    "问答接口返回有效答案",
                    "FAIL",
                    f"响应缺少字段: {missing}",
                    elapsed
                )
        elif response.status_code == 429:
            test_result.add_result(
                "AI 问答",
                "问答接口返回有效答案",
                "WARN",
                f"已达每日额度限制 (HTTP 429)",
                elapsed
            )
        else:
            test_result.add_result(
                "AI 问答",
                "问答接口返回有效答案",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "AI 问答",
            "问答接口返回有效答案",
            "FAIL",
            f"请求异常: {str(e)}"
        )
    
    # 3.2 查询问答历史
    print(f"\n3.2 查询股票 {code} 的问答历史...")
    time.sleep(1)
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/stock/{code}/chat/history?user_id={TEST_USER_ID}",
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查必需字段
            if "history" in data and "remaining_quota" in data:
                history = data["history"]
                
                # 如果之前的问答成功,历史中应该至少有 1 条记录
                if isinstance(history, list):
                    test_result.add_result(
                        "AI 问答",
                        "问答历史查询",
                        "PASS",
                        f"返回 {len(history)} 条历史记录",
                        elapsed
                    )
                else:
                    test_result.add_result(
                        "AI 问答",
                        "问答历史查询",
                        "FAIL",
                        f"history 不是数组: {type(history)}",
                        elapsed
                    )
            else:
                test_result.add_result(
                    "AI 问答",
                    "问答历史查询",
                    "FAIL",
                    "响应缺少 history 或 remaining_quota",
                    elapsed
                )
        else:
            test_result.add_result(
                "AI 问答",
                "问答历史查询",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "AI 问答",
            "问答历史查询",
            "FAIL",
            f"请求异常: {str(e)}"
        )


def test_v2_regression():
    """测试4: v2.0 功能回归测试"""
    print("\n" + "="*80)
    print("Test 4: v2.0 功能回归测试")
    print("="*80)
    
    # 4.1 推荐列表
    print("\n4.1 测试推荐列表 API...")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/recommendations", timeout=TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if "recommendations" in data:
                count = len(data["recommendations"])
                test_result.add_result(
                    "v2.0 回归",
                    "推荐列表 API",
                    "PASS",
                    f"返回 {count} 只推荐股票",
                    elapsed
                )
            else:
                test_result.add_result(
                    "v2.0 回归",
                    "推荐列表 API",
                    "FAIL",
                    "响应缺少 recommendations 字段",
                    elapsed
                )
        else:
            test_result.add_result(
                "v2.0 回归",
                "推荐列表 API",
                "FAIL",
                f"HTTP {response.status_code}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "v2.0 回归",
            "推荐列表 API",
            "FAIL",
            f"请求异常: {str(e)}"
        )
    
    # 4.2 自选股列表
    print("\n4.2 测试自选股列表 API...")
    start_time = time.time()
    try:
        response = requests.get(
            f"{BASE_URL}/watchlist/list?user_id=default_user",
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if "watchlist" in data:
                count = len(data["watchlist"])
                test_result.add_result(
                    "v2.0 回归",
                    "自选股列表 API",
                    "PASS",
                    f"返回 {count} 只自选股",
                    elapsed
                )
            else:
                test_result.add_result(
                    "v2.0 回归",
                    "自选股列表 API",
                    "FAIL",
                    "响应缺少 watchlist 字段",
                    elapsed
                )
        else:
            test_result.add_result(
                "v2.0 回归",
                "自选股列表 API",
                "FAIL",
                f"HTTP {response.status_code}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "v2.0 回归",
            "自选股列表 API",
            "FAIL",
            f"请求异常: {str(e)}"
        )
    
    # 4.3 搜索功能
    print("\n4.3 测试股票搜索 API...")
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/stocks/search?q=平安", timeout=TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if "results" in data:
                count = len(data["results"])
                test_result.add_result(
                    "v2.0 回归",
                    "股票搜索 API",
                    "PASS",
                    f"搜索'平安'返回 {count} 个结果",
                    elapsed
                )
            else:
                test_result.add_result(
                    "v2.0 回归",
                    "股票搜索 API",
                    "FAIL",
                    "响应缺少 results 字段",
                    elapsed
                )
        else:
            test_result.add_result(
                "v2.0 回归",
                "股票搜索 API",
                "FAIL",
                f"HTTP {response.status_code}",
                elapsed
            )
    except Exception as e:
        test_result.add_result(
            "v2.0 回归",
            "股票搜索 API",
            "FAIL",
            f"请求异常: {str(e)}"
        )


def main():
    """主测试入口"""
    print("\n" + "="*80)
    print("Stock Advisor v3.0 端到端测试")
    print("="*80)
    print(f"\n测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试环境: {BASE_URL}")
    print(f"超时设置: {TIMEOUT}s (考虑 Render 冷启动)")
    
    # 执行测试套件
    test_cache_single_stock()
    test_batch_loading()
    test_ai_chat()
    test_v2_regression()
    
    # 打印测试摘要
    test_result.print_summary()
    
    # 生成测试报告文件
    print("\n" + "="*80)
    print("生成测试报告...")
    
    report_filename = f"V3_E2E_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump({
            "test_time": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "summary": {
                "total": test_result.total,
                "passed": test_result.passed,
                "failed": test_result.failed,
                "warnings": test_result.warnings,
                "pass_rate": f"{test_result.passed/test_result.total*100:.1f}%"
            },
            "results": test_result.results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 测试报告已保存: {report_filename}")
    
    # 返回退出码
    return 0 if test_result.failed == 0 else 1


if __name__ == "__main__":
    exit(main())
