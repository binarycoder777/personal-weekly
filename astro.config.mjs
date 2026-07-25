import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

import react from "@astrojs/react";

// https://astro.build/config
export default defineConfig({
  favicon: 'https://raw.githubusercontent.com/binarycoder777/personal-pic/main/pic/favicon.ico',
  site: 'https://weekly.binarycoder.org',
  integrations: [starlight({
    customCss: [
    // 你的自定义 CSS 文件的相对路径
    './src/styles/custom.css', '@fontsource-variable/dancing-script'],
    title: {
      'zh-CN': 'BinaryCoder777 weekly',
      en: 'BinaryCoder777 Weekly'
    },
    logo: {
      src: './src/assets/favicon.webp'
    },
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
    }
  }), react()]
});
