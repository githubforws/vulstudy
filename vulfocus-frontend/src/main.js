import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from '@/stores/index.js'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import locale from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import SvgIcon from '@/components/SvgIcon/index.vue'

import 'normalize.css/normalize.css'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

import '@/styles/index.scss'
import '@/permission'

// svg icons
import 'virtual:svg-icons-register'

const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(ElementPlus, { locale })

// register all Element Plus icons globally
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.component('svg-icon', SvgIcon)

NProgress.configure({ showSpinner: false })

// Provide a $t fallback for Element Plus internal components
// that expect vue-i18n to be installed
app.config.globalProperties.$t = key => key

app.mount('#app')
