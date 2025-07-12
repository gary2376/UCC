#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生豆名稱管理工具
使用預定義的list儲存生豆名稱，方便擴充和修改
"""
from typing import List

# 生豆名稱主列表 - 可以直接在這裡修改和擴充
GREEN_BEAN_NAMES = [
    # 台灣本土生豆
    "南投SL34 Typica生豆",
    "古坑SL34生豆", 
    "古坑Typica生豆",
    "古坑藝妓生豆",
    "阿里山(ILM)生豆",
    
    # 印尼生豆
    "印尼AP1生豆",
    "印尼WIB1(G1)生豆",
    "曼特寧MAN(G1)生豆",
    "黃金曼特寧-MANG(G1)生豆",
    
    # 越南生豆
    "越南APV(G1)生豆",
    
    # 哥倫比亞生豆
    "哥倫比亞COL(EX)生豆",
    "哥倫比亞烏伊拉COL(WIL)-(EX)生豆", 
    "哥倫比亞雨林認證COL(EX)RFA生豆",
    
    # 墨西哥生豆
    "墨西哥Mexico(woman)生豆",
    "墨西哥瑪雅Mexico Maya生豆",
    
    # 宏都拉斯生豆
    "宏都拉斯HON(HG)生豆",
    "宏都拉斯雨林認證HON(HG)RFA生豆",
    "宏都拉斯高地小農雨林認證HON(HIGH)RFA生豆",
    
    # 寮國生豆
    "寮國LAOS(G1)生豆",
    
    # 巴西生豆
    "巴西SAN(14/16)生豆",
    "巴西SAN(14/16)SW生豆", 
    "巴西SAN(17/18)生豆",
    "巴西雨林認證SAN(RFA)生豆",
    "SAN-ROSE(NO.4/5)",
    
    # 衣索比亞生豆
    "摩卡MOC(G4)生豆",
    "耶加雪夫YGCF(G1)生豆-日曬",
    "耶加雪夫YGCF(G1)生豆-水洗",
    "耶加雪夫YGCF(G2)生豆-水洗", 
    "耶加雪夫YGCF(G3)生豆-日曬",
    "衣索比亞阿拉比卡(水洗)藝妓生豆",
    "班奇瑪吉藝妓咖啡生豆(日曬豆)",
    
    # 瓜地馬拉生豆
    "瓜地馬拉GATM生豆(EPW/SHB)",
    "瓜地馬拉-薇薇特南果-法蒂瑪GATM(VVTN-SHB-FTM)生豆",
    
    # 祕魯生豆
    "祕魯PERU(RFA)生豆",
    
    # 其他新增生豆（補足至36個）
    "肯亞AA生豆",
    "牙買加藍山生豆",
]

def get_green_bean_names() -> List[str]:
    """
    獲取生豆名稱列表
    
    Returns:
        生豆名稱列表
    """
    return GREEN_BEAN_NAMES.copy()  # 返回副本避免意外修改

def add_green_bean_name(name: str) -> bool:
    """
    添加新的生豆名稱
    
    Args:
        name: 生豆名稱
        
    Returns:
        是否添加成功
    """
    if name and name not in GREEN_BEAN_NAMES:
        GREEN_BEAN_NAMES.append(name)
        GREEN_BEAN_NAMES.sort()  # 保持排序
        return True
    return False

def remove_green_bean_name(name: str) -> bool:
    """
    移除生豆名稱
    
    Args:
        name: 要移除的生豆名稱
        
    Returns:
        是否移除成功
    """
    if name in GREEN_BEAN_NAMES:
        GREEN_BEAN_NAMES.remove(name)
        return True
    return False

def get_green_bean_count() -> int:
    """
    獲取生豆名稱總數
    
    Returns:
        生豆名稱總數
    """
    return len(GREEN_BEAN_NAMES)

def search_green_bean_names(keyword: str) -> List[str]:
    """
    搜索生豆名稱
    
    Args:
        keyword: 搜索關鍵字
        
    Returns:
        符合條件的生豆名稱列表
    """
    if not keyword:
        return get_green_bean_names()
    
    keyword = keyword.lower()
    return [name for name in GREEN_BEAN_NAMES if keyword in name.lower()]

if __name__ == "__main__":
    # 測試函數
    names = get_green_bean_names()
    print(f"生豆名稱列表（共 {len(names)} 個）:")
    for i, name in enumerate(names, 1):
        print(f"{i:2d}. {name}")
    
    # 測試搜索功能
    print(f"\n搜索'巴西'相關生豆:")
    brazil_beans = search_green_bean_names("巴西")
    for name in brazil_beans:
        print(f"- {name}")
