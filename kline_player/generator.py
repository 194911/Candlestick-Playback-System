"""
Tick生成器模块
"""

import random
from datetime import timedelta
from typing import List

from .models import Tick, KLine


class TickGenerator:
    """基于K线生成模拟Tick数据"""
    
    __slots__ = ['tick_count', '_random']
    
    def __init__(self, tick_count: int = 5, seed: int = 42):
        if tick_count < 2:
            tick_count = 2
        self.tick_count = tick_count
        self._random = random.Random(seed)
    
    def generate(self, kline: KLine) -> List[Tick]:
        """为一根K线生成Tick序列"""
        ticks = []
        n = self.tick_count
        
        if n < 2:
            n = 2
        
        time_step = 60000.0 / n
        spread = kline.spread / 1000.0
        
        prices = self._generate_price_path(kline)
        base_volume = max(1, kline.tick_volume // n) if kline.tick_volume > 0 else 1
        
        for i in range(n):
            timestamp = kline.timestamp + timedelta(milliseconds=int(i * time_step))
            price = prices[i]
            
            tick = Tick(
                timestamp=timestamp,
                price=price,
                volume=base_volume,
                bid=price - spread / 2,
                ask=price + spread / 2
            )
            ticks.append(tick)
        
        return ticks
    
    def _generate_price_path(self, kline: KLine) -> List[float]:
        """生成符合OHLC约束的价格路径"""
        n = self.tick_count
        prices = [0.0] * n
        prices[0] = kline.open
        prices[-1] = kline.close
        
        price_range = kline.high - kline.low
        
        for i in range(1, n - 1):
            if price_range > 0:
                noise = self._random.uniform(-0.3, 0.3) * price_range
                price = kline.close + noise
                prices[i] = max(kline.low, min(kline.high, price))
            else:
                prices[i] = kline.close
        
        if n > 1:
            high_idx = self._random.randint(0, max(0, n // 2 - 1))
            low_idx = self._random.randint(max(0, n // 2), n - 1)
            prices[high_idx] = kline.high
            prices[low_idx] = kline.low
        
        return prices
