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
import logging
import sys
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('weekly_generation.log')
    ]
)

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
                # 获取文章图片
                image_url = fetch_article_image(story['url'])
                
                articles.append({
                    "title": story["title"],
                    "url": story["url"],
                    "content": content[:2000],
                    "score": story.get('score', 0),
                    "time": story.get('time', 0),
                    "image": image_url  # 添加图片URL
                })
                print(f"✓ 已获取 {len(articles)}/{target_count}: {story['title']}")
                
                if len(articles) >= target_count:
                    break
        except Exception as e:
            print(f"处理文章失败: {story['url']}, 错误: {str(e)}")
    
    return articles

async def fetch_top_articles_async(target_count=30):
    """异步获取热门文章"""
    # 设置更长的超时时间
    timeout = aiohttp.ClientTimeout(total=30)  # 30秒超时
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 获取文章列表
        SOURCE_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"  # 修正URL
        
        # 添加重试机制
        max_retries = 3
        for retry in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'  # 明确指定接受JSON响应
                }
                async with session.get(SOURCE_URL, headers=headers) as response:
                    if response.status == 200:
                        story_ids = await response.json()
                        if isinstance(story_ids, list):  # 验证返回的是列表
                            break
                        else:
                            print("返回的数据格式不正确")
                    else:
                        print(f"获取文章列表失败，状态码: {response.status}")
            except Exception as e:
                if retry == max_retries - 1:
                    print(f"获取文章列表失败: {str(e)}")
                    return []
                print(f"重试 {retry + 1}/{max_retries}")
                await asyncio.sleep(2 ** retry)  # 指数退避
        else:
            print("获取文章列表失败，已达到最大重试次数")
            return []

        # 获取文章详情
        stories = []
        for story_id in story_ids[:100]:  # 获取前100个故事
            try:
                url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        story = await response.json()
                        if story and 'url' in story:
                            stories.append(story)
            except Exception as e:
                print(f"获取文章详情失败: {story_id}, 错误: {str(e)}")
                continue  # 继续处理下一篇文章

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
    你是一位资深科技编辑，以下是抓取的文章列表，每篇文章包含标题、URL、图片和内容：
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
    4. 文章主题。（一个主题）
    5. 事件或观点。（判断文章是在讲新的事件还是发表观点，三至五个核心事件或观点，如果事件和观点都存在，可以放在一句话里）
    6. 事件详情或观点依据。（每个事件或观点提炼2-4个详情或依据）
    7. 重要金句或反常识的观点（1-4个）
    8. 整体总结。需要内容中看起来像是由AI生成的部分进行重写，可以从语气、视角、过渡词汇等角度进行修改。
    9. 对总结的内容中可能的语法错误大胆纠正，保证中文文章使用的是中文标点符号，使得文本看起来更像是人类自行创作的结果，改写前后要保持用户原本的文本风格。
    10. 内容限制在200字内。
    11. 所有内容必须翻译成中文，包括标题
    12. 需要返回30篇文章，按重要性和质量排序
    
    输出格式：
    [{{"title": "...", # 中文标题
       "summary": "...", # 中文摘要
       "url": "...",
       "category": "...",  # 添加分类字段
       "image": "..."  # 保持原有的图片URL
    }}]
    """
    
    client = get_ai_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Please ensure the response is in valid JSON format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7  # 降低温度以获得更一致的输出
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
    start_date = datetime.date(2024, 7, 1)  # 设置起始日期
    today = datetime.date.today()
    days_diff = (today - start_date).days
    issue_number = (days_diff // 7) + 1  # 从起始日期开始的第几周
    return f"第{issue_number}期 · {today.strftime('%Y.%m.%d')}"

def translate_to_english(content):
    """将内容翻译成英文"""
    # 将内容分块处理，避免超出token限制
    def split_content(text, max_length=4000):
        parts = []
        lines = text.split('\n')
        current_part = []
        current_length = 0
        
        for line in lines:
            if current_length + len(line) > max_length:
                parts.append('\n'.join(current_part))
                current_part = [line]
                current_length = len(line)
            else:
                current_part.append(line)
                current_length += len(line)
        
        if current_part:
            parts.append('\n'.join(current_part))
        return parts

    try:
        content_parts = split_content(content)
        translated_parts = []
        client = get_ai_client()

        for part in content_parts:
            prompt = f"""
请将以下中文内容翻译成英文，保持专业性和可读性：

{part}

要求：
1. 保持 Markdown 格式不变
2. 保持链接和图片引用不变
3. 技术术语使用通用的英文表达
4. 保持专业性和流畅性
5. 保持原文的格式和结构
"""
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a professional translator"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                # 打印调试信息
                print(f"Translation API Response: {response}")
                
                if hasattr(response.choices[0], 'message'):
                    translated_text = response.choices[0].message.content
                    translated_parts.append(translated_text)
                else:
                    print(f"警告：响应格式异常: {response}")
                    return content  # 如果翻译失败，返回原文
                    
            except Exception as e:
                print(f"翻译部分内容时出错: {str(e)}")
                return content  # 如果翻译失败，返回原文
        
        return '\n'.join(translated_parts)
        
    except Exception as e:
        print(f"翻译过程出错: {str(e)}")
        return content  # 如果翻译失败，返回原文

def get_save_paths(date):
    """根据日期生成保存路径"""
    year = date.year
    month = date.month
    
    # 中文版路径
    zh_path = os.path.join(
       "src", "content", "docs",
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
    try:
        today = datetime.date.today()
        
        # 获取保存路径
        zh_path, _ = get_save_paths(today)
        os.makedirs(zh_path, exist_ok=True)
        
        # 生成期号
        weekly_title = generate_weekly_title()
        
        # 生成中文内容
        zh_content = generate_markdown_content(articles, weekly_title, "zh")
        
        # 保存中文版本
        zh_filepath = os.path.join(zh_path, f"{today.strftime('%d')}期.mdx")
        with open(zh_filepath, "w", encoding="utf-8") as f:
            f.write(zh_content)
        print(f"✅ 生成中文版本：{zh_filepath}")
            
    except Exception as e:
        print(f"保存 Markdown 文件时出错: {str(e)}")
        raise

def generate_markdown_content(articles, weekly_title, lang="zh"):
    """生成 Markdown 内容"""
    today = datetime.date.today()  # 保持为 datetime.date 对象，不要转换为字符串
    week_number = today.isocalendar()[1]
    
    # 从第一篇文章获取标题和描述
    first_article = articles[0] if articles else {
        'title': '本周科技精选',
        'summary': '本周值得关注的技术趋势和开源项目精选'
    }
    
    # Markdown 头部，添加期号到标题
    header = f"""---
title: 第{week_number}期 · {first_article['title']}
description: {first_article['summary']}
---

<div align="center">

# 科技周刊 {weekly_title}

本期精选 {len(articles)} 篇高质量科技内容

</div>

"""
    
    # 按分类组织文章
    categories = {}
    for article in articles:
        category = article.get('category', '其他')
        if category not in categories:
            categories[category] = []
        categories[category].append(article)
    
    # 生成文章内容
    content_parts = []
    for category, articles_in_category in categories.items():
        content_parts.append(f"## {category}")
        for article in articles_in_category:
            # 标题和链接
            content_parts.append(f"### [{article['title']}]({article['url']})")
            
            # 添加图片（如果有）
            if article.get('image'):
                content_parts.append(f"""
<div align="center">
<img src="{article['image']}" width="400" />
</div>
""")
            
            # 添加摘要
            content_parts.append(f"\n{article['summary']}\n")
            
            # 添加分隔线
            content_parts.append("---\n")
    
    content = "\n".join(content_parts)
    
    # 添加页脚
    footer = """
<div align="center">

如果觉得这些内容对你有帮助，欢迎[点个 Star ⭐](https://github.com/your-repo) 或[分享给朋友](https://twitter.com/intent/tweet)

</div>
"""
    
    return header + content + footer

def clean_ai_response(response):
    """清理 AI 返回的响应，移除 Markdown 格式并修复 JSON 格式"""
    try:
        # 移除 Markdown 格式标记
        cleaned = response.replace('```json', '').replace('```', '').strip()
        
        # 尝试解析 JSON 以验证格式
        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            # 如果解析失败，尝试修复常见问题
            # 1. 移除注释
            lines = [line for line in cleaned.split('\n') if not line.strip().startswith('#')]
            cleaned = '\n'.join(lines)
            
            # 2. 确保所有单引号变成双引号
            cleaned = cleaned.replace("'", '"')
            
            # 3. 移除末尾可能的多余逗号
            cleaned = cleaned.replace(',]', ']').replace(',}', '}')
            
            # 再次尝试解析
            try:
                json.loads(cleaned)
                return cleaned
            except json.JSONDecodeError as e:
                logging.error(f"JSON 格式修复失败: {str(e)}")
                logging.error(f"清理后的响应:\n{cleaned}")
                raise
                
    except Exception as e:
        logging.error(f"清理响应时出错: {str(e)}")
        raise

def main():
    """主函数"""
    try:
        logging.info("开始获取文章...")
        articles = fetch_top_articles()
        logging.info(f"获取到 {len(articles)} 篇文章")
        
        if not articles:
            logging.error("未获取到任何文章，程序退出")
            sys.exit(1)
        
        logging.info("正在过滤文章...")
        filtered_response = filter_articles(articles)
        cleaned_response = clean_ai_response(filtered_response)
        
        try:
            articles = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logging.error(f"解析 AI 响应失败: {str(e)}")
            logging.error(f"原始响应: {cleaned_response}")
            sys.exit(1)
        
        logging.info(f"过滤后剩余 {len(articles)} 篇文章")
        
        # 确保目录存在
        today = datetime.date.today()
        zh_path, _ = get_save_paths(today)
        os.makedirs(zh_path, exist_ok=True)
        
        save_markdown(articles)
        logging.info("✅ 全部处理完成")
        
    except Exception as e:
        logging.error(f"❌ 程序执行出错: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
