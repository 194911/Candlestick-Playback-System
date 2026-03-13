"""
回放引擎模块
"""

import time
from typing import Callable, List, Optional

from .models import Account, KLine, Tick
from .loader import DataLoader
from .generator import TickGenerator
from .trading import TradingInterface


class PlaybackEngine:
    """K线回放引擎"""
    
    def __init__(self, data_loader: DataLoader, tick_generator: TickGenerator):
        self.data_loader = data_loader
        self.tick_generator = tick_generator
        self.klines: List[KLine] = []
        self.current_index: int = 0
        self.account = Account()
        self.trading = TradingInterface(self.account)
        
        self.on_tick: Optional[Callable[[Tick, KLine], None]] = None
        self.on_kline: Optional[Callable[[KLine], None]] = None
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[], None]] = None
    
    def load_data(self) -> bool:
        """加载数据"""
        self.klines = self.data_loader.load_all()
        return len(self.klines) > 0
    
    def reset(self):
        """重置到开始"""
        self.current_index = 0
        self.account = Account()
        self.trading = TradingInterface(self.account)
    
    def run(self, max_klines: Optional[int] = None, enable_stop_out: bool = True):
        """
        运行回放
        
        Args:
            max_klines: 最大回放K线数
            enable_stop_out: 是否启用强平检查
        """
        if not self.klines:
            if not self.load_data():
                return
        
        if self.on_start:
            self.on_start()
        
        total = len(self.klines)
        end_index = min(max_klines or total, total)
        
        if end_index <= 0:
            return
        
        start_time = time.time()
        
        while self.current_index < end_index:
            kline = self.klines[self.current_index]
            
            if not kline.ticks:
                kline.ticks = self.tick_generator.generate(kline)
            
            if self.on_kline:
                self.on_kline(kline)
            
            if self.on_tick:
                for tick in kline.ticks:
                    self.on_tick(tick, kline)
                    
                    if enable_stop_out and self.trading.get_position_count() > 0:
                        stopped = self.trading.check_stop_out(tick, tick.timestamp)
                        if stopped:
                            print(f"\n[{tick.timestamp}] 强平 {len(stopped)} 个持仓!")
            
            self.current_index += 1
            
            if self.current_index % 1000 == 0:
                elapsed = time.time() - start_time
                speed = self.current_index / elapsed if elapsed > 0 else 0
                print(f"\r进度: {self.current_index}/{end_index} ({self.current_index/end_index*100:.1f}%) "
                      f"速度: {speed:.0f} K线/秒", end='', flush=True)
        
        elapsed = time.time() - start_time
        print(f"\n回放完成: {self.current_index} 根K线，耗时 {elapsed:.2f} 秒")
        
        if self.on_stop:
            self.on_stop()
