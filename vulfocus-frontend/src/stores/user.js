import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi, getInfo, register as registerApi } from '@/api/user'
import { getToken, setToken, removeToken } from '@/utils/auth'
import { resetRouter } from '@/router/index.js'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    name: '',
    avatar: '',
    rank: '',
    email: '',
    roles: [],
    greenhand: false,
    licence: '',
  }),
  getters: {
    rolesList: (state) => state.roles,
  },
  actions: {
    login(userInfo) {
      const { username, password } = userInfo
      return new Promise((resolve, reject) => {
        loginApi({ username: username.trim(), password })
          .then(response => {
            const { data } = response
            this.token = data.token
            setToken(data.token)
            resolve()
          })
          .catch(error => {
            reject(error)
          })
      })
    },
    register(userInfo) {
      const { name, pass, checkpass, captcha_code, hashkey } = userInfo
      return new Promise((resolve, reject) => {
        registerApi({
          username: name.trim(),
          password: pass,
          checkpass,
          captcha_code,
          hashkey,
        })
          .then(response => {
            resolve(response)
          })
          .catch(error => {
            reject(error)
          })
      })
    },
    getInfo() {
      return new Promise((resolve, reject) => {
        getInfo(this.token)
          .then(response => {
            const { data } = response
            if (!data) {
              reject('Verification failed, please Login again.')
            }
            const { name, avatar, rank, roles, email, greenhand, licence } = data
            this.name = name
            this.avatar = avatar
            this.rank = rank
            this.roles = roles
            this.email = email
            this.greenhand = greenhand
            this.licence = licence
            resolve(data)
          })
          .catch(error => {
            reject(error)
          })
      })
    },
    logout() {
      return new Promise((resolve, reject) => {
        logoutApi(this.token)
          .then(() => {
            this.token = ''
            this.roles = []
            removeToken()
            resetRouter()
            resolve()
          })
          .catch(error => {
            reject(error)
          })
      })
    },
    resetToken() {
      return new Promise(resolve => {
        this.token = ''
        this.roles = []
        removeToken()
        resolve()
      })
    },
  },
})
