"""
数据加载器模块
"""

import os
from datetime import datetime
from typing import List, Optional

from .models import KLine


class DataLoader:
    """CSV数据加载器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.klines: List[KLine] = []
    
    def load_csv(self, filename: str) -> List[KLine]:
        """加载单个CSV文件"""
        filepath = os.path.join(self.data_dir, filename)
        klines = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return klines
        except Exception:
            return klines
        
        lines = content.split('\n')
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) < 8:
                continue
            
            try:
                dt_parts = parts[0].split(' ')
                if len(dt_parts) < 2:
                    continue
                    
                date_parts = dt_parts[0].split('.')
                time_parts = dt_parts[1].split(':')
                
                if len(date_parts) < 3 or len(time_parts) < 2:
                    continue
                
                dt = datetime(
                    int(date_parts[0]), 
                    int(date_parts[1]), 
                    int(date_parts[2]),
                    int(time_parts[0]), 
                    int(time_parts[1])
                )
                
                kline = KLine(
                    timestamp=dt,
                    open=float(parts[1]),
                    high=float(parts[2]),
                    low=float(parts[3]),
                    close=float(parts[4]),
                    tick_volume=int(parts[5]),
                    real_volume=int(parts[6]),
                    spread=int(parts[7]),
                    ticks=[]
                )
                klines.append(kline)
            except (ValueError, IndexError):
                continue
        
        return klines
    
    def load_all(self) -> List[KLine]:
        """加载目录下所有CSV文件"""
        all_klines = []
        
        try:
            csv_files = sorted([
                f for f in os.listdir(self.data_dir) 
                if f.endswith('.csv')
            ])
        except FileNotFoundError:
            print(f"目录不存在: {self.data_dir}")
            return all_klines
        
        for filename in csv_files:
            klines = self.load_csv(filename)
            all_klines.extend(klines)
            print(f"加载 {filename}: {len(klines)} 条K线")
        
        all_klines.sort(key=lambda x: x.timestamp)
        self.klines = all_klines
        print(f"总计加载: {len(all_klines)} 条K线")
        return all_klines
