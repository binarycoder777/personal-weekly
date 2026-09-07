import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { issueDate, sortWeeklyIssues } from '../utils/issues';

export async function GET(context) {
  const issues = sortWeeklyIssues(await getCollection('docs'));
  return rss({
    title: '科技奇闻汇',
    description: '一个记录互联网上实时发生的科技新闻和奇闻趣事的站点，项目保持每周六或周日更新。',
    site: context.site,
    items: issues.map((post) => ({
      title: post.data.title,
      pubDate: issueDate(post),
      description: post.data.description,
      link: `/${post.slug}/`,
    })),
  });
}
