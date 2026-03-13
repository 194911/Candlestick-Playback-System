"""
策略基类模块
"""

from datetime import datetime
from typing import List, Optional

from .models import KLine, Order, OrderType, Tick
from .engine import PlaybackEngine


class StrategyBase:
    """策略基类"""
    
    def __init__(self, engine: PlaybackEngine):
        self.engine = engine
        self.trading = engine.trading
        self.account = engine.account
    
    def on_init(self) -> None:
        """初始化时调用"""
        pass
    
    def on_tick(self, tick: Tick, kline: KLine) -> None:
        """每个Tick调用"""
        pass
    
    def on_kline(self, kline: KLine) -> None:
        """每根K线完成时调用"""
        pass
    
    def on_start(self) -> None:
        """回放开始时调用"""
        pass
    
    def on_stop(self) -> None:
        """回放结束时调用"""
        pass
    
    def buy(self, volume: float, tick: Tick, timestamp: datetime, 
            slippage: int = 0) -> Optional[Order]:
        """开多单"""
        return self.trading.open_position(OrderType.BUY, volume, tick, timestamp, slippage)
    
    def sell(self, volume: float, tick: Tick, timestamp: datetime,
             slippage: int = 0) -> Optional[Order]:
        """开空单"""
        return self.trading.open_position(OrderType.SELL, volume, tick, timestamp, slippage)
    
    def close(self, order: Order, tick: Tick, timestamp: datetime) -> bool:
        """平仓"""
        return self.trading.close_position(order, tick, timestamp)
    
    def close_all(self, tick: Tick, timestamp: datetime) -> int:
        """平掉所有持仓"""
        return self.trading.close_all_positions(tick, timestamp)
    
    def get_positions(self) -> List[Order]:
        """获取当前持仓"""
        return self.trading.get_positions()
    
    def get_position_count(self) -> int:
        """获取持仓数量"""
        return self.trading.get_position_count()
