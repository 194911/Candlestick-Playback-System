"""
数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class OrderType(Enum):
    """订单类型"""
    BUY = 1
    SELL = 2


class OrderStatus(Enum):
    """订单状态"""
    PENDING = 1
    FILLED = 2
    CLOSED = 3


@dataclass(slots=True)
class Tick:
    """Tick数据"""
    timestamp: datetime
    price: float
    volume: int
    bid: float
    ask: float
    bid_volume: int = 0
    ask_volume: int = 0


@dataclass(slots=True)
class KLine:
    """K线数据"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    real_volume: int
    spread: int
    ticks: List['Tick'] = field(default_factory=list)


@dataclass(slots=True)
class Order:
    """订单"""
    order_id: int
    order_type: OrderType
    entry_price: float
    volume: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    status: OrderStatus = OrderStatus.FILLED
    profit: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0


@dataclass
class Account:
    """账户"""
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    free_margin: float = 10000.0
    margin_level: float = 0.0
    positions: List[Order] = field(default_factory=list)
    history: List[Order] = field(default_factory=list)
    order_counter: int = 0
    leverage: float = 200.0
    margin_call_level: float = 100.0
    stop_out_level: float = 0.0
