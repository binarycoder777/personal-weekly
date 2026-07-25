<p align="center">
    <img width="200" src="https://raw.githubusercontent.com/binarycoder777/binarycoder777.github.io/main/public/favicon.ico">
</p>


<p align="center">
    <a target="_blank">
        <img src="https://img.icons8.com/?size=100&id=lckHFUP7nJhG&format=png&color=000000" style="width: 50px; height: 50px;"/>
    </a>
    <a target="_blank">
        <img src="https://github.com/withastro/starlight/assets/357379/494fcd83-42aa-4891-87e0-87402fa0b6f3" style="width: 50px; height: 50px;"/>
    </a>
    <a target="_blank">
        <img src="https://img.icons8.com/?size=100&id=13841&format=png&color=000000" style="width: 50px; height: 50px;"/>
    </a>
    <a target="_blank">
        <img src="https://img.icons8.com/?size=100&id=yauDoZYEux9L&format=png&color=000000" style="width: 50px; height: 50px;"/>
    </a>
    <a target="_blank">
        <img src="https://img.icons8.com/?size=100&id=12192&format=png&color=000000" style="width: 50px; height: 50px;"/>
    </a>
    <a target="_blank">
        <img src="https://img.icons8.com/?size=100&id=76thz6hgYpSk&format=png&color=000000" style="width: 50px; height: 50px;"/>
    </a>
</p>


<h1 align="center">《科技奇闻汇》· 关注每周新鲜事~ </h1>

<div align="center">



<p>基于Astro，支持RSS订阅、Giscus评论、中英双语阅读、明暗主题等</p>

```
🕙 一个记录互联网上实时发生的科技新闻和奇闻趣事的站点，项目保持每周六或周日更新，喜欢的朋友可以免费订阅，不错过每周发生的科技奇闻趣事～
```

</div>


## 关于站点

站点通过[starlight主题](https://starlight.astro.build/getting-started/)进行搭建（一个建立在 [Astro](https://astro.build/) 框架之上的全功能文档主题），站点内容遵循MIT 授权许可，详情可参阅[LICENSE](https://github.com/binarycoder777/binarycoder777.github.io?tab=MIT-1-ov-file)。


![](https://raw.githubusercontent.com/binarycoder777/personal-pic/main/pic/20250301193555.png)

## 快速上手

**步骤**
```
1. clone the repo
2. npm install
3. npm run dev
4. change astro.config.mjs config
5. more info refer to https://astro.build/ or https://starlight.astro.build/
```

## 自动生成周刊

GitHub Actions 会在每周五北京时间 22:00 自动运行
`src/hacker_news_weekly.py`，生成新一期 MDX、提交到 `main`，随后触发现有的
GitHub Pages 部署流程。

首次启用时，需要在仓库的 **Settings → Secrets and variables → Actions**
中添加名为 `DEEPSEEK_API_KEY` 的 Repository secret。配置完成后，可以到
**Actions → Auto Fetch Weekly Articles → Run workflow** 手动运行一次进行验证。
默认使用 `deepseek-v4-flash`；如果更看重生成质量，可以在 workflow 中将
`DEEPSEEK_MODEL` 改为 `deepseek-v4-pro`。

GitHub Actions 的定时任务使用 UTC，因此 workflow 中的
`0 14 * * 5` 对应北京时间周五 22:00。GitHub 的调度可能有数分钟延迟。

## 订阅

喜欢科技奇闻汇的朋友可以通过 [这里](https://weekly.binarycoder.org/rss.xml) 免费订阅我的更新。 感谢您的关注和支持！

## 投稿分享

如果你有任何建议、想法或者想要投稿，欢迎通过电子邮件联系我：atao67276@gmail.com。

## 期刊目录

- [001期：Microsoft CrowdStrike 事件的技术故障](https://weekly.binarycoder.org/2024年/7月/001期)
- [002期：英特尔将裁员15,000人](https://weekly.binarycoder.org/2024年/7月/002期)
- [003期：1 万亿美元市值蒸发：市场暴跌重创大型科技公司](https://weekly.binarycoder.org/2024年/8月/003期)
- [004期：年轻人癌症发病率不断上升](https://weekly.binarycoder.org/2024年/8月/009期)
- [005期：程序员不读书——但你应该读书](https://weekly.binarycoder.org/2024年/8月/005期)
- [006期：等待时间悖论，或者为什么我的公交车总是晚点？](https://weekly.binarycoder.org/2024年/8月/006期)
- [007期：电动汽车电池起火——需要了解的知识和应对方法](https://weekly.binarycoder.org/2024年/8月/007期)
- [008期：开发人员讨厌他们的工作，但喜欢在工作之外编写代码](https://weekly.binarycoder.org/2024年/8月/008期)
- [009期：价值 15 亿美元的 Bybit 黑客事件：运营安全失败的时代已经到来](https://weekly.binarycoder.org/2024年/8月/009期)
- [010期：继承变得几乎和工作一样重要](https://weekly.binarycoder.org/2024年/8月/010期)
