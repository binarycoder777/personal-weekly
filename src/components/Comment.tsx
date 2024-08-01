import * as React from 'react'
import Giscus from '@giscus/react'

const id = 'inject-comments'

// 获取 localStorage 中 theme 的值
function getSavedTheme() {
    if (typeof localStorage !== 'undefined' && localStorage.getItem('starlight-theme')) {
        return localStorage.getItem('starlight-theme');
    }
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}


const Comments = () => {
  const [mounted, setMounted] = React.useState(false)
  const [theme, setTheme] = React.useState('light')

  React.useEffect(() => {
    const theme = getSavedTheme()
    setTheme(theme)
    // 监听主题变化
    const observer = new MutationObserver(() => {
      console.log(getSavedTheme())
      setTheme(getSavedTheme())
    })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })

    // 取消监听
    return () => {
      observer.disconnect()
    }
  }, [])

  React.useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div id={id} className="w-full">
      {mounted ? (
        <Giscus
          id={id}
          repo="binarycoder777/binarycoder777.github.io"
          repoId="R_kgDOKeudTw"
          category="Announcements"
          categoryId="DIC_kwDOKeudT84Cch4W"
          mapping="title"
          reactionsEnabled="1"
          emitMetadata="0"
          inputPosition="top"
          lang="zh-CN"
          loading="lazy"
          theme={theme}
        />
      ) : null}
    </div>
  )
}
export default Comments
