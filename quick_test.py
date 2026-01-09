#!/usr/bin/env python3
"""快速测试脚本 - 生成模拟收益曲线"""

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pandas as pd

def generate_simulation_results(start_date='2020-01-01', end_date='2025-12-31', initial_capital=100000):
    """生成模拟的回测结果"""
    
    # 生成模拟日期
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # 模拟基准收益（QQQ）
    np.random.seed(42)
    # 假设QQQ起始价格约为600 (2025/2026年水平)
    base_price = 600
    
    # 使用更真实的波动率 (年化约15-20%)
    daily_vol = 0.20 / np.sqrt(252)
    daily_drift = 0.10 / 252 # 假设年化10%上涨
    
    benchmark_returns = np.random.normal(daily_drift, daily_vol, len(dates))
    
    # 生成价格序列
    benchmark_prices = base_price * (1 + benchmark_returns).cumprod()
    
    # 将价格序列转换为资金曲线 (以初始资金为基准)
    benchmark_values = initial_capital * (benchmark_prices / benchmark_prices[0])
    
    # 模拟策略收益（略优于基准，Alpha）
    # 策略波动率通常略低于大盘 (因为有期权金缓冲)
    strategy_vol = 0.15 / np.sqrt(252)
    strategy_drift = 0.15 / 252 # 假设年化15%
    
    strategy_returns = np.random.normal(strategy_drift, strategy_vol, len(dates))
    strategy_values = initial_capital * (1 + strategy_returns).cumprod()
    
    return dates, strategy_values, benchmark_values, initial_capital

def plot_simulation():
    """绘制模拟收益曲线"""
    
    dates, strategy_values, benchmark_values, initial_capital = generate_simulation_results()
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 绘制策略收益曲线
    plt.plot(dates, strategy_values, label='期权策略', linewidth=2, color='blue')
    
    # 绘制基准收益曲线
    plt.plot(dates, benchmark_values, label='QQQ基准', linewidth=2, color='gray', alpha=0.7)
    
    # 计算性能指标
    total_return = (strategy_values[-1] / initial_capital - 1) * 100
    annualized_return = ((1 + total_return/100) ** (252/len(dates)) - 1) * 100
    
    # 格式化和标签
    plt.title('期权交易策略模拟表现 (2024年)')
    plt.xlabel('日期')
    plt.ylabel('投资组合价值 (元)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # 添加性能指标
    metrics_text = f"""年化收益率: {annualized_return:.1f}%
总收益率: {total_return:.1f}%
初始资金: {initial_capital:,}元
最终价值: {strategy_values[-1]:,.0f}元"""
    
    plt.annotate(metrics_text, xy=(0.02, 0.98), xycoords='axes fraction', 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('strategy_performance_2024.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 模拟图表已生成!")
    print("📍 图表保存为: strategy_performance_2024.png")

def show_strategy_details():
    """显示策略详情"""
    
    print("🎯 策略配置详情")
    print("=" * 50)
    print("标的配置:")
    print("  • NVDA: 25% - Delta 0.15-0.20")
    print("  • GOOGL: 25% - Delta 0.20-0.25") 
    print("  • TSLA: 20% - Delta 0.15-0.20")
    print("  • QQQ: 30% - Delta 0.20-0.25")
    print()
    print("交易规则:")
    print("  • 现金担保认沽期权: 60%仓位")
    print("  • 备兑认购期权: 40%仓位")
    print("  • DTE: 30-45天")
    print("  • 盈利70%时平仓")
    print("  • 每月首个交易日开仓")
    print()
    print("风险控制:")
    print("  • VIX > 35 时进入熊市模式")
    print("  • QQQ < 200日均线时调整策略")
    print("  • 熊市时只交易QQQ和GOOGL")

if __name__ == "__main__":
    print("📈 期权交易策略模拟器")
    print("=" * 60)
    
    show_strategy_details()
    print()
    
    # 生成模拟图表
    try:
        plot_simulation()
        print()
        print("✅ 系统功能正常!")
        print("💡 实际回测需要连接市场数据API")
        
    except Exception as e:
        print(f"❌ 生成图表时出错: {e}")