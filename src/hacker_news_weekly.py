import os
import json  # 添加 json 导入
import requests
import datetime
import frontmatter
from openai import OpenAI
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-a26f1f0761d8463e895df6bf24e7a71e"  # 在这里填入您的 API 密钥

def make_request_with_retry(url, timeout=10, max_retries=3, method='get', headers=None):
    """带有重试机制的请求函数
    
    Args:
        url: 请求的URL
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        method: 请求方法（get 或 head）
        headers: 请求头
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
    
    for retry in range(max_retries):
        try:
            if method == 'head':
                response = requests.head(url, timeout=timeout, headers=headers)
            else:
                response = requests.get(url, timeout=timeout, headers=headers)
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            if retry == max_retries - 1:  # 最后一次重试
                print(f"请求失败 {url}: {str(e)}")
                raise
            
            # 计算退避时间
            wait_time = (retry + 1) * 2
            print(f"请求失败，{wait_time} 秒后重试: {url}")
            time.sleep(wait_time)
    
    return None

def fetch_article_image(url):
    """尝试获取文章的主要图片URL"""
    try:
        response = make_request_with_retry(url, timeout=10)
        if not response:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        possible_images = []
        
        # 查找 Open Graph 图片
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            possible_images.append(og_image['content'])
            
        # 查找 Twitter 卡片图片
        twitter_image = soup.find('meta', property='twitter:image')
        if twitter_image and twitter_image.get('content'):
            possible_images.append(twitter_image['content'])
            
        # 查找文章中的第一张大图
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                img_url = urljoin(url, src)
                if 'icon' not in img_url.lower() and 'logo' not in img_url.lower():
                    possible_images.append(img_url)
        
        # 验证图片URL是否有效
        for img_url in possible_images:
            try:
                img_response = make_request_with_retry(img_url, timeout=5, method='head')
                if img_response and img_response.status_code == 200:
                    return img_url
            except:
                continue
                
    except Exception as e:
        print(f"获取图片失败: {url}, 错误: {str(e)}")
    
    return None

async def async_fetch(session, url, timeout=10):
    """异步请求函数"""
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"请求失败 {url}: {str(e)}")
    return None

async def fetch_article_batch(session, stories, target_count):
    """异步批量获取文章"""
    articles = []
    tasks = []
    
    for story in stories:
        if 'url' not in story or 'title' not in story:
            continue
            
        task = asyncio.create_task(async_fetch(session, story['url']))
        tasks.append((story, task))
        
        if len(tasks) >= target_count * 2:  # 获取两倍于目标数量的文章
            break
    
    for story, task in tasks:
        try:
            content = await task
            if content:
                articles.append({
                    "title": story["title"],
                    "url": story["url"],
                    "content": content[:2000],
                    "score": story.get('score', 0),
                    "time": story.get('time', 0)
                })
                print(f"✓ 已获取 {len(articles)}/{target_count}: {story['title']}")
                
                if len(articles) >= target_count:
                    break
        except Exception as e:
            print(f"处理文章失败: {story['url']}, 错误: {str(e)}")
    
    return articles

async def fetch_top_articles_async(target_count=30):
    """异步获取热门文章"""
    async with aiohttp.ClientSession() as session:
        # 获取文章列表
        try:
            SOURCE_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
            async with session.get(SOURCE_URL) as response:
                story_ids = await response.json()
        except Exception as e:
            print(f"获取文章列表失败: {str(e)}")
            return []

        # 获取文章详情
        stories = []
        for story_id in story_ids[:100]:  # 获取前100个故事
            try:
                url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                async with session.get(url) as response:
                    story = await response.json()
                    if story and 'url' in story:
                        stories.append(story)
            except Exception as e:
                print(f"获取文章详情失败: {story_id}, 错误: {str(e)}")

        # 批量获取文章内容
        articles = await fetch_article_batch(session, stories, target_count)
        
        # 按热度排序
        articles.sort(key=lambda x: (x.get('score', 0), x.get('time', 0)), reverse=True)
        
        return articles[:target_count]

def fetch_top_articles(target_count=30):
    """主函数入口"""
    try:
        # 设置超时
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(fetch_top_articles_async(target_count))
        articles = loop.run_until_complete(future)
        loop.close()
        return articles
    except Exception as e:
        print(f"获取文章失败: {str(e)}")
        return []

def get_ai_client():
    """获取 DeepSeek API 客户端"""
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,  # 直接使用全局变量
        base_url="https://api.deepseek.com"
    )

def filter_articles(articles):
    """使用 AI 过滤、分类和总结文章"""
    prompt = f"""
    你是一位资深科技编辑，以下是抓取的文章列表，每篇文章包含标题、URL和内容：
    {articles}
    
    你的任务：
    1. 过滤掉无关、广告、低质量的文章
    2. 只保留科技相关的高质量文章
    3. 对每篇文章进行分类，可选的分类包括：
       - 人工智能：AI、机器学习、深度学习等
       - 编程开发：编程语言、框架、开发工具等
       - 技术架构：系统设计、架构方案、最佳实践等
       - 产品创新：新产品发布、创新应用等
       - 技术趋势：行业动态、技术展望等
       - 开源社区：开源项目、社区动态等
       - 其他：不属于上述类别但值得关注的内容
    4. 基于文章实际内容生成摘要，字数不超过150字
    5. 确保摘要准确反映原文内容，不要添加未提及的信息
    6. 内容如果是英文请翻译成中文
    7. 需要返回30篇文章，按重要性和质量排序
    
    输出格式：
    [{{"title": "...", 
       "summary": "...", 
       "url": "...",
       "category": "..."  # 添加分类字段
    }}]
    """
    
    client = get_ai_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def enhance_markdown(markdown_text):
    """使用 AI 优化 Markdown 格式"""
    prompt = f"""
    你是一名专业的 Markdown 编辑，请优化以下 Markdown 文章的格式，使其：
    1. 标题更清晰
    2. 代码块更易读
    3. 适当添加 emoji 或分隔线
    4. 确保内容逻辑清晰
    
    输入：
    {markdown_text}
    """
    
    client = get_ai_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def categorize_articles(articles):
    """将文章按主题分类"""
    categories = {
        'AI与机器学习': [],
        '编程与开发': [],
        '科技新闻': [],
        '工具与资源': [],
        '其他': []
    }
    
    # 关键词映射
    category_keywords = {
        'AI与机器学习': ['ai', 'machine learning', 'deep learning', 'neural', 'gpt', 'llm'],
        '编程与开发': ['programming', 'python', 'javascript', 'code', 'github', 'dev'],
        '工具与资源': ['tool', 'resource', 'library', 'framework', 'platform'],
        '科技新闻': ['launch', 'announce', 'release', 'news', 'update']
    }
    
    for article in articles:
        title_lower = article['title'].lower()
        content_lower = article.get('content', '').lower()
        
        # 根据标题和内容判断分类
        categorized = False
        for category, keywords in category_keywords.items():
            if any(keyword in title_lower or keyword in content_lower for keyword in keywords):
                categories[category].append(article)
                categorized = True
                break
        
        # 未分类的放入其他
        if not categorized:
            categories['其他'].append(article)
    
    return categories

def generate_weekly_title():
    """生成周刊标题"""
    today = datetime.date.today()
    week_number = today.isocalendar()[1]
    return f"第{week_number}期 · {today.strftime('%Y.%m.%d')}"

def translate_to_english(content):
    """将内容翻译成英文"""
    prompt = f"""
    请将以下中文内容翻译成英文，保持专业性和可读性：
    {content}
    
    注意：
    1. 保持 Markdown 格式不变
    2. 保持链接和图片引用不变
    3. 技术术语使用通用的英文表达
    4. 保持专业性和流畅性
    """
    
    client = get_ai_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a professional translator"},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def get_save_paths(date):
    """根据日期生成保存路径"""
    year = date.year
    month = date.month
    
    # 中文版路径
    zh_path = os.path.join(
        "content", "docs", "zh-cn",
        f"{year}年", f"{month}月"
    )
    
    # 英文版路径
    en_path = os.path.join(
        "content", "docs", "en",
        f"{year}", f"{month}"
    )
    
    return zh_path, en_path

def save_markdown(articles):
    """生成 Markdown 文件"""
    today = datetime.date.today()
    
    # 获取保存路径
    zh_path, en_path = get_save_paths(today)
    os.makedirs(zh_path, exist_ok=True)
    os.makedirs(en_path, exist_ok=True)
    
    # 生成期号
    weekly_title = generate_weekly_title()
    
    # 生成中文内容
    zh_content = generate_markdown_content(articles, weekly_title, "zh")
    
    # 生成英文内容
    en_content = translate_to_english(zh_content)
    
    # 保存中文版本
    zh_filepath = os.path.join(zh_path, f"{today.strftime('%d')}期.mdx")
    with open(zh_filepath, "w", encoding="utf-8") as f:
        f.write(zh_content)
    print(f"✅ 生成中文版本：{zh_filepath}")
    
    # 保存英文版本
    en_filepath = os.path.join(en_path, f"issue-{today.strftime('%d')}.mdx")
    with open(en_filepath, "w", encoding="utf-8") as f:
        f.write(en_content)
    print(f"✅ 生成英文版本：{en_filepath}")

def generate_markdown_content(articles, weekly_title, lang="zh"):
    """生成 Markdown 内容"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # 从第一篇文章获取标题和描述
    first_article = articles[0] if articles else {
        'title': '本周科技精选',
        'summary': '本周值得关注的技术趋势和开源项目精选'
    }
    
    # 按分类组织文章
    categories = {}
    for article in articles:
        category = article.get('category', '其他')
        if category not in categories:
            categories[category] = []
        categories[category].append(article)
    
    # Markdown 头部
    header = f"""---
title: {first_article['title']}
description: {first_article['summary']}
---

<div align="center">

# 科技周刊 {weekly_title}

本期精选 {len(articles)} 篇高质量科技内容

</div>

"""
    
    # 生成文章内容
    content_parts = []
    for category, articles_in_category in categories.items():
        content_parts.append(f"## {category}")
        for article in articles_in_category:
            # 标题和链接
            content_parts.append(f"### [{article['title']}]({article['url']})")
            
            # 如果有图片，添加图片
            if article.get('image'):
                content_parts.append(f"\n![article image]({article['image']})")
            
            # 添加摘要
            content_parts.append(f"\n{article['summary']}\n")
    
    content = "\n".join(content_parts)
    
    return header + content

def clean_ai_response(response):
    """清理 AI 返回的响应，移除 Markdown 格式"""
    # 移除 ```json 和 ``` 标记
    response = response.replace('```json', '').replace('```', '').strip()
    return response

def main():
    """主函数"""
    try:
        print("开始获取文章...")
        articles = fetch_top_articles()
        print(f"获取到 {len(articles)} 篇文章")
        
        if not articles:
            print("未获取到任何文章，程序退出")
            return
        
        print("正在过滤文章...")
        filtered_response = filter_articles(articles)
        cleaned_response = clean_ai_response(filtered_response)
        
        try:
            articles = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"解析 AI 响应失败: {str(e)}")
            return
        
        print(f"过滤后剩余 {len(articles)} 篇文章")
        save_markdown(articles)
        print("✅ 全部处理完成")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
