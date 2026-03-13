"""
回测分析模块 - PNG图表输出
"""

import math
import os
import shutil
from datetime import datetime
from typing import List, Optional

from .models import Account, Order

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class BacktestStats:
    """回测统计"""
    
    def __init__(self, account: Account):
        self.account = account
        self.history: List[Order] = account.history if account.history else []
        
        self.total_trades: int = 0
        self.win_count: int = 0
        self.loss_count: int = 0
        self.win_rate: float = 0.0
        self.total_profit: float = 0.0
        self.total_commission: float = 0.0
        self.total_wins: float = 0.0
        self.total_losses: float = 0.0
        self.profit_factor: float = 0.0
        self.avg_profit: float = 0.0
        self.avg_loss: float = 0.0
        self.max_win: float = 0.0
        self.max_loss: float = 0.0
        self.max_drawdown: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.final_equity: float = 10000.0
        self.equity_curve: List[float] = [10000.0]
        self.timestamps: List[Optional[datetime]] = [None]
        
        self._calculate_metrics()
    
    def _calculate_metrics(self):
        """计算各项指标"""
        if not self.history:
            return
        
        profits = [o.profit for o in self.history]
        commissions = [o.commission for o in self.history]
        
        self.total_trades = len(self.history)
        self.total_profit = sum(profits)
        self.total_commission = sum(commissions)
        
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p <= 0]
        
        self.win_count = len(wins)
        self.loss_count = len(losses)
        
        if self.total_trades > 0:
            self.win_rate = self.win_count / self.total_trades * 100
        
        self.total_wins = sum(wins) if wins else 0.0
        self.total_losses = abs(sum(losses)) if losses else 0.0
        
        if self.total_losses > 0:
            self.profit_factor = self.total_wins / self.total_losses
        
        if self.win_count > 0:
            self.avg_profit = self.total_wins / self.win_count
        if self.loss_count > 0:
            self.avg_loss = self.total_losses / self.loss_count
        
        self.max_win = max(wins) if wins else 0.0
        self.max_loss = min(losses) if losses else 0.0
        
        equity = 10000.0
        self.equity_curve = [equity]
        self.timestamps = [self.history[0].entry_time if self.history else None]
        peak = equity
        max_dd = 0.0
        
        for order in self.history:
            equity += order.profit
            self.equity_curve.append(equity)
            self.timestamps.append(order.exit_time)
            if equity > peak:
                peak = equity
            if peak > 0:
                dd = (peak - equity) / peak * 100
                if dd > max_dd:
                    max_dd = dd
        
        self.max_drawdown = max_dd
        self.final_equity = equity
        
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                if self.equity_curve[i-1] > 0:
                    ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
                    returns.append(ret)
            
            if len(returns) > 1:
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                std_return = math.sqrt(variance)
                if std_return > 0:
                    self.sharpe_ratio = avg_return / std_return * math.sqrt(252)


class ChartGenerator:
    """图表生成器"""
    
    @staticmethod
    def generate_report_image(stats: BacktestStats, output_path: str, 
                               title: str = "回测报告") -> bool:
        """生成完整报告PNG图片"""
        if not HAS_MATPLOTLIB:
            print("需要安装matplotlib: pip install matplotlib")
            return False
        
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig = plt.figure(figsize=(14, 10))
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)
        
        ax_equity = fig.add_subplot(gs[0, :2])
        ChartGenerator._plot_equity_curve(ax_equity, stats)
        
        ax_dd = fig.add_subplot(gs[1, :2])
        ChartGenerator._plot_drawdown(ax_dd, stats)
        
        ax_dist = fig.add_subplot(gs[2, :2])
        ChartGenerator._plot_profit_distribution(ax_dist, stats)
        
        ax_stats = fig.add_subplot(gs[:, 2])
        ChartGenerator._plot_stats_table(ax_stats, stats)
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        
        return True
    
    @staticmethod
    def _plot_equity_curve(ax, stats: BacktestStats):
        """绘制余额曲线"""
        if len(stats.equity_curve) < 2:
            ax.text(0.5, 0.5, '数据不足', ha='center', va='center', transform=ax.transAxes)
            return
        
        x = list(range(len(stats.equity_curve)))
        ax.fill_between(x, stats.equity_curve, alpha=0.3, color='blue')
        ax.plot(x, stats.equity_curve, color='blue', linewidth=1.5)
        
        ax.axhline(y=10000, color='gray', linestyle='--', alpha=0.5, label='初始资金')
        
        ax.set_title('余额曲线', fontsize=12, fontweight='bold')
        ax.set_xlabel('交易次数')
        ax.set_ylabel('账户余额')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
        max_eq = max(stats.equity_curve)
        min_eq = min(stats.equity_curve)
        if max_eq > min_eq:
            ax.set_ylim(min_eq * 0.95, max_eq * 1.05)
    
    @staticmethod
    def _plot_drawdown(ax, stats: BacktestStats):
        """绘制回撤曲线"""
        if len(stats.equity_curve) < 2:
            ax.text(0.5, 0.5, '数据不足', ha='center', va='center', transform=ax.transAxes)
            return
        
        drawdowns = []
        peak = stats.equity_curve[0]
        
        for eq in stats.equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100 if peak > 0 else 0
            drawdowns.append(dd)
        
        x = list(range(len(drawdowns)))
        ax.fill_between(x, drawdowns, alpha=0.4, color='red')
        ax.plot(x, drawdowns, color='red', linewidth=1)
        
        max_dd = max(drawdowns) if drawdowns else 0
        ax.axhline(y=max_dd, color='darkred', linestyle='--', alpha=0.7, 
                   label=f'最大回撤: {max_dd:.2f}%')
        
        ax.set_title('回撤曲线', fontsize=12, fontweight='bold')
        ax.set_xlabel('交易次数')
        ax.set_ylabel('回撤 (%)')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        ax.invert_yaxis()
    
    @staticmethod
    def _plot_profit_distribution(ax, stats: BacktestStats):
        """绘制盈亏分布"""
        if not stats.history:
            ax.text(0.5, 0.5, '数据不足', ha='center', va='center', transform=ax.transAxes)
            return
        
        profits = [o.profit for o in stats.history]
        
        colors = ['green' if p >= 0 else 'red' for p in profits]
        
        ax.bar(range(len(profits)), profits, color=colors, alpha=0.7, width=1.0)
        ax.axhline(y=0, color='black', linewidth=0.5)
        
        ax.set_title('盈亏分布', fontsize=12, fontweight='bold')
        ax.set_xlabel('交易序号')
        ax.set_ylabel('盈亏金额')
        ax.grid(True, alpha=0.3, axis='y')
    
    @staticmethod
    def _plot_stats_table(ax, stats: BacktestStats):
        """绘制统计表格"""
        ax.axis('off')
        
        return_rate = ((stats.final_equity - 10000) / 10000 * 100) if stats.final_equity else 0
        profit_ratio = (stats.avg_profit / stats.avg_loss) if stats.avg_loss > 0 else 0
        
        table_data = [
            ['账户概览', ''],
            ['初始资金', f'{10000.0:,.2f}'],
            ['最终资金', f'{stats.final_equity:,.2f}'],
            ['总盈亏', f'{stats.total_profit:,.2f}'],
            ['收益率', f'{return_rate:.2f}%'],
            ['总手续费', f'{stats.total_commission:,.2f}'],
            ['', ''],
            ['交易统计', ''],
            ['总交易次数', f'{stats.total_trades}'],
            ['盈利次数', f'{stats.win_count}'],
            ['亏损次数', f'{stats.loss_count}'],
            ['胜率', f'{stats.win_rate:.2f}%'],
            ['盈亏比', f'{profit_ratio:.2f}'],
            ['盈利因子', f'{stats.profit_factor:.2f}'],
            ['', ''],
            ['风险指标', ''],
            ['最大回撤', f'{stats.max_drawdown:.2f}%'],
            ['夏普比率', f'{stats.sharpe_ratio:.2f}'],
            ['最大盈利', f'{stats.max_win:,.2f}'],
            ['最大亏损', f'{stats.max_loss:,.2f}'],
            ['平均盈利', f'{stats.avg_profit:,.2f}'],
            ['平均亏损', f'{stats.avg_loss:,.2f}'],
        ]
        
        table = ax.table(
            cellText=table_data,
            colWidths=[0.5, 0.5],
            cellLoc='left',
            loc='upper center'
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.4)
        
        for i, row in enumerate(table_data):
            if row[0] in ['账户概览', '交易统计', '风险指标']:
                for j in range(2):
                    cell = table[(i, j)]
                    cell.set_facecolor('#4472C4')
                    cell.set_text_props(color='white', fontweight='bold')
            elif row[0] == '':
                for j in range(2):
                    cell = table[(i, j)]
                    cell.set_facecolor('white')


class BacktestReport:
    """回测报告生成器"""
    
    def __init__(self, account: Account):
        self.stats = BacktestStats(account)
    
    def generate_image(self, output_path: str = "backtest_report.png", 
                       title: str = "回测报告") -> bool:
        """生成PNG图片报告"""
        return ChartGenerator.generate_report_image(self.stats, output_path, title)
    
    def print_summary(self) -> None:
        """打印简要报告"""
        return_rate = ((self.stats.final_equity - 10000) / 10000 * 100) if self.stats.final_equity else 0
        
        print("\n" + "=" * 50)
        print("回测报告".center(46))
        print("=" * 50)
        print(f"{'初始资金:':<20} {10000.0:>20,.2f}")
        print(f"{'最终资金:':<20} {self.stats.final_equity:>20,.2f}")
        print(f"{'收益率:':<20} {return_rate:>19.2f}%")
        print("-" * 50)
        print(f"{'总交易次数:':<20} {self.stats.total_trades:>20d}")
        print(f"{'胜率:':<20} {self.stats.win_rate:>19.2f}%")
        print(f"{'盈利因子:':<20} {self.stats.profit_factor:>19.2f}")
        print(f"{'最大回撤:':<20} {self.stats.max_drawdown:>19.2f}%")
        print(f"{'夏普比率:':<20} {self.stats.sharpe_ratio:>20.2f}")
        print("=" * 50)


def clear_pycache(package_dir: Optional[str] = None) -> bool:
    """清除__pycache__目录"""
    if package_dir is None:
        package_dir = os.path.dirname(os.path.abspath(__file__))
    
    pycache_dir = os.path.join(package_dir, "__pycache__")
    
    if os.path.exists(pycache_dir):
        try:
            shutil.rmtree(pycache_dir)
            return True
        except Exception:
            return False
    return True
