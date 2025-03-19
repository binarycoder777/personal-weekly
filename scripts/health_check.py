import os
import sys
from datetime import datetime

def check_weekly_generation():
    """检查周刊是否正常生成"""
    today = datetime.now()
    year = today.year
    month = today.month
    
    # 检查目录是否存在
    base_path = f"content/docs/zh-cn/{year}年/{month}月"
    if not os.path.exists(base_path):
        print(f"错误: 目录不存在 {base_path}")
        return False
    
    # 检查是否有最新的文件
    files = os.listdir(base_path)
    mdx_files = [f for f in files if f.endswith('.mdx')]
    
    if not mdx_files:
        print(f"错误: 未找到 MDX 文件在 {base_path}")
        return False
    
    print("健康检查通过")
    return True

if __name__ == "__main__":
    success = check_weekly_generation()
    sys.exit(0 if success else 1) 