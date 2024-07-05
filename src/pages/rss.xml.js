import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const docs = await getCollection('docs');
  return rss({
    title: '科技奇闻汇',
    description: '前沿科技，奇趣故事，一键开启你的探索之旅',
    site: context.site,
    items: docs.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      customData: post.data.customData,
      // 从 `slug` 属性计算出 RSS 链接
      // 这个例子假设所有的文章都被渲染为 `/docs/[slug]` 路由
      link: `/docs/${post.slug}/`,
    })),
  });
}