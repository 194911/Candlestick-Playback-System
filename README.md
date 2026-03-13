# K线回放系统

基于Python的K线回放回测框架，支持Tick级数据模拟、交易接口、风险管理和回测报告生成。


## 功能特性

- 零外部依赖：仅使用Python标准库
- Tick级回放：基于K线生成模拟Tick数据
- 完整交易接口：支持开平仓、持仓管理、保证金计算
- 风险管理：强平机制、点差模拟、滑点模拟
- 回测报告：余额曲线、回撤分析、夏普比率等指标
- 可视化输出：自动生成PNG图表报告


## 系统架构

    kline_player/
    ├── __init__.py      # 包导出
    ├── models.py        # 数据模型（K线、Tick、订单、账户）
    ├── loader.py        # CSV数据加载器
    ├── generator.py     # Tick数据生成器
    ├── trading.py       # 交易接口
    ├── engine.py        # 回放引擎
    ├── strategy.py      # 策略基类
    └── analytics.py     # 回测分析和图表生成


## 核心模块说明

### 1. 数据模型 (models.py)

| 类 | 说明 |
|----|------|
| KLine | K线数据（时间、开高低收、成交量、点差） |
| Tick | Tick数据（时间、价格、买卖价、成交量） |
| Order | 订单（类型、价格、数量、盈亏、状态） |
| Account | 账户（余额、净值、保证金、持仓、历史） |
| OrderType | 订单类型枚举（BUY/SELL） |
| OrderStatus | 订单状态枚举（PENDING/FILLED/CLOSED） |

账户默认参数：
- 初始资金：10,000
- 杠杆：1:200
- 强平水平：保证金水平 小于等于 0%


### 2. 数据加载器 (loader.py)

    from kline_player import DataLoader

    loader = DataLoader(r'f:\Desktop\100\data')
    klines = loader.load_all()  # 加载目录下所有CSV

CSV格式要求：

    时间,开盘,最高,最低,收盘,Tick成交量,实际成交量,点差
    2018.01.02,00:00,1302.36,1302.68,1302.08,1302.36,54,0,90


### 3. Tick生成器 (generator.py)

基于K线OHLC生成模拟Tick序列：

    from kline_player import TickGenerator

    generator = TickGenerator(tick_count=5, seed=42)
    ticks = generator.generate(kline)  # 为单根K线生成5个Tick

生成逻辑：
- 价格路径符合OHLC约束
- 时间均匀分布在1分钟内
- 买卖价基于K线点差计算


### 4. 交易接口 (trading.py)

    from kline_player import TradingInterface
    from kline_player.models import Account

    account = Account()
    trading = TradingInterface(account, commission_rate=0.0)

    # 开仓
    order = trading.open_position(
        order_type=OrderType.BUY,
        volume=0.1,
        tick=tick,
        timestamp=tick.timestamp,
        slippage_ticks=0
    )

    # 平仓
    trading.close_position(order, tick, tick.timestamp)

    # 平所有持仓
    trading.close_all_positions(tick, tick.timestamp)

交易规则：
- 买入以Ask价成交，卖出以Bid价成交
- 1点 = 0.001
- 强平额外滑点：5点


### 5. 回放引擎 (engine.py)

    from kline_player import PlaybackEngine

    engine = PlaybackEngine(loader, generator)

    # 绑定回调
    engine.on_tick = lambda tick, kline: print(tick.price)
    engine.on_kline = lambda kline: print(kline.close)
    engine.on_start = lambda: print("开始")
    engine.on_stop = lambda: print("结束")

    # 运行回放
    engine.run(max_klines=10000)  # 限制最大K线数，None表示全部


### 6. 策略基类 (strategy.py)

    from kline_player import StrategyBase

    class MyStrategy(StrategyBase):
        def __init__(self, engine):
            super().__init__(engine)
            # 初始化参数

        def on_tick(self, tick, kline):
            # 每个Tick调用
            pass

        def on_kline(self, kline):
            # 每根K线完成时调用
            pass

        def on_start(self):
            # 回放开始时调用
            pass

        def on_stop(self):
            # 回放结束时调用
            pass

策略内置方法：
- buy(volume, tick, timestamp, slippage) - 开多单
- sell(volume, tick, timestamp, slippage) - 开空单
- close(order, tick, timestamp) - 平仓指定订单
- close_all(tick, timestamp) - 平所有持仓
- get_positions() - 获取当前持仓列表
- get_position_count() - 获取持仓数量


### 7. 回测分析 (analytics.py)

    from kline_player import BacktestReport

    report = BacktestReport(engine.account)
    report.print_summary()  # 打印文本报告
    report.generate_image('report.png', title='回测报告')  # 生成PNG图表

统计指标：
- 收益率、总盈亏、总手续费
- 总交易次数、胜率、盈亏比
- 盈利因子、最大回撤、夏普比率
- 最大/平均盈利、最大/平均亏损

图表内容：
- 余额曲线
- 回撤曲线
- 盈亏分布
- 统计数据表格


## 使用方法

### 快速开始

    from kline_player import (
        DataLoader, TickGenerator, PlaybackEngine,
        StrategyBase, BacktestReport, clear_pycache
    )

    # 1. 定义策略
    class MyStrategy(StrategyBase):
        def __init__(self, engine):
            super().__init__(engine)
            self.prices = []

        def on_tick(self, tick, kline):
            self.prices.append(tick.price)

            if len(self.prices) > 20:
                ma20 = sum(self.prices[-20:]) / 20

                if tick.price > ma20 and self.get_position_count() == 0:
                    self.buy(0.1, tick, tick.timestamp)

                elif tick.price < ma20 and self.get_position_count() > 0:
                    self.close_all(tick, tick.timestamp)

    # 2. 运行回测
    def main():
        # 初始化
        loader = DataLoader(r'f:\Desktop\100\data')
        generator = TickGenerator(tick_count=5, seed=42)
        engine = PlaybackEngine(loader, generator)

        # 绑定策略
        strategy = MyStrategy(engine)
        engine.on_tick = strategy.on_tick

        # 加载并运行
        engine.load_data()
        engine.run()

        # 生成报告
        report = BacktestReport(engine.account)
        report.print_summary()
        report.generate_image('report.png')

        # 清除缓存
        clear_pycache()

    if __name__ == '__main__':
        main()


### 完整示例

参见 example.py - 均线交叉策略示例


## 配置参数

### 账户参数 (models.py)

    Account(
        balance=10000.0,           # 初始余额
        leverage=200.0,            # 杠杆倍数
        stop_out_level=0.0         # 强平水平（%）
    )


### Tick生成参数 (generator.py)

    TickGenerator(
        tick_count=5,              # 每根K线生成Tick数
        seed=42                    # 随机种子
    )


### 交易参数 (trading.py)

    TradingInterface(
        account=account,
        commission_rate=0.0        # 佣金率（Standard账户为0）
    )


## 数据格式

### CSV文件格式

文件名：XAUUSDm_M1_201801.csv

内容：

    时间,开盘,最高,最低,收盘,Tick成交量,实际成交量,点差
    2018.01.02,00:00,1302.36,1302.68,1302.08,1302.36,54,0,90
    2018.01.02,00:01,1302.36,1302.65,1302.36,1302.65,51,0,100

字段说明：
- 时间：格式 YYYY.MM.DD,HH:MM
- 开盘/最高/最低/收盘：价格
- Tick成交量：该分钟内的Tick数量
- 实际成交量：实际交易手数
- 点差：买入卖出价差（通常以点数表示）


## 性能优化

- 使用 __slots__ 减少内存占用
- 批量读取CSV文件
- 手动解析时间字符串（避免strptime）
- 按需生成Tick数据

典型性能：
- 处理速度：60,000+ K线/秒
- 280万根K线约45秒完成


## 注意事项

1. 数据路径：确保数据目录存在且包含CSV文件
2. matplotlib：生成图表需要安装 pip install matplotlib
3. 内存使用：大量K线数据会占用内存，可分批处理
4. 随机种子：Tick生成使用固定种子保证可重复性
5. 强平机制：保证金水平小于等于0%时触发强平


## 扩展开发

### 自定义指标

    class Indicator:
        def __init__(self, period):
            self.period = period
            self.values = []

        def update(self, price):
            self.values.append(price)
            if len(self.values) > self.period:
                self.values.pop(0)

        def ma(self):
            return sum(self.values) / len(self.values) if self.values else 0


### 多品种支持

    # 为每个品种创建独立的引擎实例
    engine_gold = PlaybackEngine(loader_gold, generator)
    engine_silver = PlaybackEngine(loader_silver, generator)


### 参数优化

    # 遍历参数组合
    for fast in [5, 10, 15]:
        for slow in [20, 30, 40]:
            engine.reset()
            strategy = MyStrategy(engine, fast, slow)
            # 运行回测...


## API参考

### StrategyBase 方法

| 方法 | 参数 | 返回值 | 说明 |
|-----|------|-------|------|
| buy | volume, tick, timestamp, slippage=0 | Order/None | 开多单 |
| sell | volume, tick, timestamp, slippage=0 | Order/None | 开空单 |
| close | order, tick, timestamp | bool | 平仓 |
| close_all | tick, timestamp | int | 平所有持仓 |
| get_positions | - | List[Order] | 获取持仓 |
| get_position_count | - | int | 持仓数量 |


### PlaybackEngine 方法

| 方法 | 参数 | 返回值 | 说明 |
|-----|------|-------|------|
| load_data | - | bool | 加载数据 |
| reset | - | - | 重置引擎 |
| run | max_klines=None, enable_stop_out=True | - | 运行回放 |


## 许可证

MIT License
