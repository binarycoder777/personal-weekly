import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import react from "@astrojs/react";

const docsDirectory = new URL('./src/content/docs/', import.meta.url);

function numericPrefix(name) {
  return Number.parseInt(name, 10);
}

function pageTitle(file) {
  const content = readFileSync(file, 'utf8');
  const title = content.match(/^title:\s*(.+)$/m)?.[1].trim();

  return title?.replace(/^(['"])(.*)\1$/, '$2');
}

function weeklySidebar() {
  const years = readdirSync(docsDirectory, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^\d{4}年$/.test(entry.name))
    .sort((a, b) => numericPrefix(b.name) - numericPrefix(a.name));

  return [
    { label: '关于科技奇闻汇', link: '/介绍/' },
    ...years.map((year) => {
      const yearDirectory = join(fileURLToPath(docsDirectory), year.name);
      const months = readdirSync(yearDirectory, { withFileTypes: true })
        .filter((entry) => entry.isDirectory() && /^\d{1,2}月$/.test(entry.name))
        .sort((a, b) => numericPrefix(b.name) - numericPrefix(a.name));

      return {
        label: year.name,
        collapsed: year.name !== years[0]?.name,
        items: months.map((month) => {
          const monthDirectory = join(yearDirectory, month.name);
          const issues = readdirSync(monthDirectory, { withFileTypes: true })
            .filter((entry) => entry.isFile() && /\.mdx?$/.test(entry.name))
            .sort((a, b) => numericPrefix(b.name) - numericPrefix(a.name));

          return {
            label: month.name,
            collapsed: month.name !== months[0]?.name,
            items: issues.map((issue) => ({
              label: pageTitle(join(monthDirectory, issue.name)) ?? issue.name.replace(/\.mdx?$/, ''),
              link: `/${year.name}/${month.name}/${issue.name.replace(/\.mdx?$/, '')}/`,
            })),
          };
        }),
      };
    }),
  ];
}

// https://astro.build/config
export default defineConfig({
  favicon: 'https://raw.githubusercontent.com/binarycoder777/personal-pic/main/pic/favicon.ico',
  site: 'https://weekly.binarycoder.org',
  integrations: [starlight({
    customCss: [
    // 你的自定义 CSS 文件的相对路径
    './src/styles/custom.css', '@fontsource-variable/dancing-script'],
    title: {
      'zh-CN': '科技奇闻汇',
      en: 'TechWeekly'
    },
    sidebar: weeklySidebar(),
    // 为此网站设置中文为默认语言。
    locales: {
      'root': {
        label: '简体中文',
        lang: 'zh-CN'
      }
    },
    social: {
      github: 'https://github.com/binarycoder777/personal-weekly',
      twitter: 'https://x.com/binarycoder777',
      discord: 'https://discord.gg/7k3fsuas',
    },
    components: {
      Header: './src/components/SiteHeader.astro',
      PageTitle: './src/components/SitePageTitle.astro',
      Footer: './src/components/SiteFooter.astro',
    },
  }), react()]
});
