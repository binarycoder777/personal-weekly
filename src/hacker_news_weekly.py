import requests
from bs4 import BeautifulSoup
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hacker_news.log'),
        logging.StreamHandler()
    ]
)

# 目标网站 URL
url = "https://hckrnews.com/?utm_source=gold_browser_extension"

# 添加请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    # 发送 HTTP 请求
    logging.info("开始发送 HTTP 请求...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    logging.info("HTTP 请求成功")

    # 打印页面源代码预览
    logging.info("页面源代码预览:")
    logging.info(response.text[:1000])
    
    # 解析 HTML 内容
    logging.info("开始解析 HTML 内容...")
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 尝试打印所有的 tr 标签
    logging.info("所有 tr 标签预览:")
    trs = soup.find_all('tr')
    logging.info(f"找到 {len(trs)} 个 tr 标签")
    if trs:
        logging.info(str(trs[0])[:500])

    # 提取文章信息
    logging.info("开始提取文章信息...")
    articles = []
    for item in soup.find_all('li'):
        # 提取评论数和点数
        text = item.text.strip().split()
        if len(text) >= 2 and text[1].isdigit():  # 格式为: "comments points title"
            points = text[1]  # 第二个数字是点数
            
            # 获取链接和标题
            link_element = item.find('a')
            if link_element:
                title = ' '.join(text[2:])  # 标题在点数之后
                link = link_element.get('href')
                if link and title:
                    articles.append({
                        "title": title,
                        "link": link,
                        "heat": points
                    })
    logging.info(f"成功提取 {len(articles)} 篇文章信息")

    # 按热度排序并选择前 30 篇
    logging.info("开始排序文章...")
    articles_sorted = sorted(articles, key=lambda x: int(x["heat"]) if x["heat"].isdigit() else 0, reverse=True)[:30]
    logging.info("文章排序完成")

    # 生成 Markdown 格式周刊
    logging.info("开始生成 Markdown 内容...")
    markdown_content = "# 本周 Hacker News 热度最高文章\n\n"
    for idx, article in enumerate(articles_sorted, start=1):
        markdown_content += f"{idx}. **[{article['title']}]({article['link']})**  \n"
        markdown_content += f"   热度: {article['heat']}  \n\n"
    logging.info("Markdown 内容生成完成")

    # 保存为 Markdown 文件
    logging.info("开始保存 Markdown 文件...")
    with open("hacker_news_weekly.md", "w", encoding="utf-8") as file:
        file.write(markdown_content)
    logging.info("Markdown 文件保存成功")

    print("周刊已生成并保存为 hacker_news_weekly.md")

except requests.RequestException as e:
    logging.error(f"HTTP 请求失败: {str(e)}")
except Exception as e:
    logging.error(f"程序执行出错: {str(e)}")

