import { defineStore } from 'pinia'
import { asyncRoutes, constantRoutes } from '@/router/index.js'

function hasPermission(roles, route) {
  if (route.meta == undefined) {
    return true
  }
  if (route.meta.role && route.meta.role.length > 0) {
    return roles.some(role => route.meta.role.includes(role))
  } else {
    return true
  }
}

function filterAsyncRoutes(routes, roles) {
  const res = []
  routes.forEach(route => {
    const tmp = { ...route }
    let hasPer = hasPermission(roles, tmp)
    if (hasPer) {
      if (tmp.children) {
        tmp.children = filterAsyncRoutes(tmp.children, roles)
      }
      res.push(tmp)
    }
  })
  return res
}

export const usePermissionStore = defineStore('permission', {
  state: () => ({
    routes: [],
    addRoutes: [],
  }),
  getters: {
    permission_routes: (state) => state.routes,
  },
  actions: {
    generateRoutes(roles) {
      return new Promise(resolve => {
        let accessedRoutes
        if (roles.includes('admin')) {
          accessedRoutes = asyncRoutes || []
        } else {
          accessedRoutes = filterAsyncRoutes(asyncRoutes, roles)
        }
        this.addRoutes = accessedRoutes
        this.routes = constantRoutes.concat(accessedRoutes)
        resolve(accessedRoutes)
      })
    },
  },
})
