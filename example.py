"""
K线回放系统测试
"""

import sys
sys.path.insert(0, r'f:\Desktop\100')

from kline_player import (
    DataLoader, TickGenerator, PlaybackEngine,
    StrategyBase, BacktestReport, clear_pycache
)
from kline_player.models import OrderType


class TestStrategy(StrategyBase):
    """测试策略 - 简单均线交叉"""
    
    def __init__(self, engine):
        super().__init__(engine)
        self.fast_ma = 5
        self.slow_ma = 20
        self.prices = []
        self.position_opened = False
    
    def on_tick(self, tick, kline):
        """每个Tick调用"""
        self.prices.append(tick.price)
        
        if len(self.prices) < self.slow_ma:
            return
        
        fast = sum(self.prices[-self.fast_ma:]) / self.fast_ma
        slow = sum(self.prices[-self.slow_ma:]) / self.slow_ma
        
        if fast > slow and not self.position_opened:
            order = self.buy(0.1, tick, tick.timestamp)
            if order:
                print(f"[{tick.timestamp}] 开多 @ {tick.price:.2f}")
                self.position_opened = True
        
        elif fast < slow and self.position_opened:
            positions = self.get_positions()
            for pos in positions:
                self.close(pos, tick, tick.timestamp)
                print(f"[{tick.timestamp}] 平仓 @ {tick.price:.2f}, 盈亏: {pos.profit:.2f}")
            self.position_opened = False
    
    def on_stop(self):
        """回放结束"""
        if self.get_position_count() > 0:
            print(f"\n回放结束，强制平仓 {self.get_position_count()} 个持仓")


def main():
    """主函数"""
    print("=" * 50)
    print("K线回放系统测试")
    print("=" * 50)
    
    # 初始化组件
    data_loader = DataLoader(r'f:\Desktop\100\data')
    tick_generator = TickGenerator(tick_count=5, seed=42)
    engine = PlaybackEngine(data_loader, tick_generator)
    
    # 创建策略
    strategy = TestStrategy(engine)
    
    # 绑定回调
    engine.on_tick = strategy.on_tick
    engine.on_stop = strategy.on_stop
    
    # 加载数据
    print("\n加载数据...")
    if not engine.load_data():
        print("数据加载失败，请检查数据目录")
        return
    
    # 运行回放
    print("\n开始回放...")
    engine.run()
    
    # 生成报告
    print("\n生成回测报告...")
    report = BacktestReport(engine.account)
    report.print_summary()
    
    # 生成图表
    output_path = r'f:\Desktop\100\backtest_report.png'
    if report.generate_image(output_path, title="K线回放测试报告"):
        print(f"\n图表已保存: {output_path}")
    
    # 清除缓存
    clear_pycache()
    print("\n测试完成!")


if __name__ == "__main__":
    main()
