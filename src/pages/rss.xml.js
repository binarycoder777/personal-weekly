import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const blog = await getCollection('blog');
  return rss({
    title: '科技奇闻汇',
    description: '一个记录互联网上实时发生的科技新闻和奇闻趣事的站点，项目保持每周六或周日更新。',
    site: context.site,
    items: blog.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      customData: post.data.customData,
      // 从 `slug` 属性计算出 RSS 链接
      // 这个例子假设所有的文章都被渲染为 `/blog/[slug]` 路由
      link: `/zh-cn/${post.slug}/`,
    })),
  });
}