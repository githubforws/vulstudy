import axios from 'axios'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// create an axios instance
const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API, // url = base url + request url
  // withCredentials: true, // send cookies when cross-domain requests
  timeout: 600000, // request timeout
})

// request interceptor
service.interceptors.request.use(
  config => {
    // do something before request is sent
    const userStore = useUserStore()
    if (userStore.token) {
      // let each request carry token
      // ['X-Token'] is a custom headers key
      // please modify it according to the actual situation
      config.headers['Authorization'] = 'BMH ' + userStore.token
    }
    return config
  },
  error => {
    // do something with request error
    return Promise.reject(error)
  }
)

// response interceptor
service.interceptors.response.use(
  response => {
    const res = response

    if (res.status > 300) {
      const data = res.data || {}
      const msg = data.msg || data.message || res.statusText || '请求失败'
      const userStore = useUserStore()

      if (res.status === 401) {
        ElMessageBox.confirm('登录已过期，请重新登录', '提示', {
          confirmButtonText: '重新登录', cancelButtonText: '取消', type: 'warning',
        }).then(() => {
          userStore.resetToken().then(() => location.reload())
        })
        return Promise.reject(new Error(msg))
      }
      if (res.status === 403) {
        ElMessage.error('权限不足')
        return Promise.reject(new Error(msg))
      }

      ElMessage.error(msg)
      return Promise.reject(new Error(msg))
    }
    return res
  },
  error => {
    let response = error.response
    let status = response?.status
    let data = response?.data || {}
    let msg = data.msg || data.message || error.message || '网络错误'

    if (status === 401) {
      const userStore = useUserStore()
      userStore.resetToken().then(() => location.reload())
      return Promise.reject(error)
    }
    if (status === 400) {
      if (data.non_field_errors) msg = data.non_field_errors[0]
      else if (data.username) msg = data.username[0]
      else if (data.email) msg = data.email[0]
    }

    ElMessage({ message: msg, type: 'error', duration: 5 * 1000 })
    return Promise.reject(error)
  }
)

export default service
