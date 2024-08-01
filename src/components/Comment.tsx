import * as React from 'react'
import Giscus from '@giscus/react'

const id = 'inject-comments'

const getSavedTheme = () => {
    if (typeof window !== 'undefined' && localStorage.getItem('starlight-theme')) {
        return localStorage.getItem('starlight-theme') || 'light';
    }
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

const Comments = () => {
  const [mounted, setMounted] = React.useState(false)
  const [theme, setTheme] = React.useState('light')

  React.useEffect(() => {
    // 仅在客户端执行的代码
    const theme = getSavedTheme()
    setTheme(theme)

    const observer = new MutationObserver(() => {
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
          repo="binarycoder777/personal-weekly"
          repoId="R_kgDOMRwFCQ"
          category="Announcements"
          categoryId="DIC_kwDOMRwFCc4ChU84"
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
