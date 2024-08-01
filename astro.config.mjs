import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	favicon: '/favicon.ico',
	site: 'https://github.com/binarycoder777',
	base: 'personal-weekly',
	integrations: [
		starlight({
			customCss: [
				// 你的自定义 CSS 文件的相对路径
				'./src/styles/custom.css',
				'@fontsource-variable/dancing-script',
			],
			title: {
				'zh-CN': 'BinaryCoder777的周刊',
				en: 'BinaryCoder777 Weekly',
			},
			logo: {
				src: './src/assets/favicon.webp'
			},
			// 为此网站设置英语为默认语言。
			defaultLocale: 'zh-cn',
			locales: {
				// 英文文档在 `src/content/docs/en/` 中。
				en: {
					label: 'English',
				},
				// 简体中文文档在 `src/content/docs/zh-cn/` 中。
				'zh-cn': {
					label: '简体中文',
					lang: 'zh-CN',
				},
			},
			social: {
				github: 'https://github.com/binarycoder777',
			}
		}),
	],
});
