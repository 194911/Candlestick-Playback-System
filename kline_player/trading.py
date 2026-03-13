"""
交易接口模块
"""

from datetime import datetime
from typing import Callable, List, Optional

from .models import Account, Order, OrderType, Tick


class TradingInterface:
    """交易接口"""
    
    __slots__ = ['account', 'commission_rate', 'on_order_filled', 'on_order_closed']
    
    def __init__(self, account: Account, commission_rate: float = 0.0):
        self.account = account
        self.commission_rate = max(0.0, commission_rate)
        self.on_order_filled: Optional[Callable[[Order], None]] = None
        self.on_order_closed: Optional[Callable[[Order], None]] = None
    
    def _calculate_margin(self, volume: float, price: float) -> float:
        """计算所需保证金"""
        if volume <= 0 or price <= 0:
            return 0.0
        contract_value = volume * price * 100
        return contract_value / max(1.0, self.account.leverage)
    
    def _update_account_metrics(self):
        """更新账户指标"""
        total_margin = 0.0
        
        for pos in self.account.positions:
            total_margin += self._calculate_margin(pos.volume, pos.entry_price)
        
        self.account.margin = total_margin
        self.account.equity = self.account.balance
        self.account.free_margin = self.account.equity - total_margin
        
        if total_margin > 0:
            self.account.margin_level = (self.account.equity / total_margin) * 100
        else:
            self.account.margin_level = 0.0
    
    def check_stop_out(self, tick: Tick, timestamp: datetime) -> List[Order]:
        """检查强平条件"""
        stopped_out = []
        
        if self.account.margin_level >= 0 and self.account.margin_level <= self.account.stop_out_level:
            for order in self.account.positions[:]:
                if self.close_position(order, tick, timestamp, forced=True):
                    stopped_out.append(order)
        
        return stopped_out
    
    def open_position(self, order_type: OrderType, volume: float, 
                      tick: Tick, timestamp: datetime, 
                      slippage_ticks: int = 0) -> Optional[Order]:
        """开仓"""
        if volume <= 0:
            return None
        
        if order_type == OrderType.BUY:
            base_price = tick.ask
            fill_price = base_price + slippage_ticks * 0.001
        else:
            base_price = tick.bid
            fill_price = base_price - slippage_ticks * 0.001
        
        if fill_price <= 0:
            return None
        
        required_margin = self._calculate_margin(volume, fill_price)
        
        if required_margin > self.account.free_margin:
            return None
        
        self.account.order_counter += 1
        
        commission = fill_price * volume * 100 * self.commission_rate
        self.account.balance -= commission
        
        order = Order(
            order_id=self.account.order_counter,
            order_type=order_type,
            entry_price=fill_price,
            volume=volume,
            entry_time=timestamp,
            slippage=abs(slippage_ticks) * 0.001,
            commission=commission
        )
        
        self.account.positions.append(order)
        self._update_account_metrics()
        
        if self.on_order_filled:
            self.on_order_filled(order)
        
        return order
    
    def close_position(self, order: Order, tick: Tick, 
                       timestamp: datetime, forced: bool = False) -> bool:
        """平仓"""
        if order not in self.account.positions:
            return False
        
        if order.order_type == OrderType.BUY:
            exit_price = tick.bid
        else:
            exit_price = tick.ask
        
        if forced:
            if order.order_type == OrderType.BUY:
                exit_price -= 0.005
            else:
                exit_price += 0.005
        
        order.exit_price = exit_price
        order.exit_time = timestamp
        
        if order.order_type == OrderType.BUY:
            gross_profit = (exit_price - order.entry_price) * order.volume * 100
        else:
            gross_profit = (order.entry_price - exit_price) * order.volume * 100
        
        exit_commission = exit_price * order.volume * 100 * self.commission_rate
        order.commission += exit_commission
        order.profit = gross_profit - order.commission
        
        self.account.balance += order.profit
        
        try:
            self.account.positions.remove(order)
        except ValueError:
            pass
        
        self.account.history.append(order)
        self._update_account_metrics()
        
        if self.on_order_closed:
            self.on_order_closed(order)
        
        return True
    
    def close_all_positions(self, tick: Tick, timestamp: datetime) -> int:
        """平掉所有持仓"""
        count = 0
        for order in self.account.positions[:]:
            if self.close_position(order, tick, timestamp):
                count += 1
        return count
    
    def get_position_count(self) -> int:
        """获取当前持仓数量"""
        return len(self.account.positions)
    
    def get_positions(self) -> List[Order]:
        """获取当前持仓列表"""
        return self.account.positions.copy()
