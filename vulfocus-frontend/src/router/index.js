import { createRouter, createWebHashHistory } from 'vue-router'

/* Layout */
import Layout from '@/layout/index.vue'

/**
 * constantRoutes - accessible by all roles
 */
export const constantRoutes = [
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    hidden: true,
  },
  {
    path: '/register',
    component: () => import('@/views/register/index.vue'),
    hidden: true,
  },
  {
    path: '/updatepwd',
    component: () => import('@/views/retrieve/update.vue'),
    hidden: true,
  },
  {
    path: '/activate',
    component: () => import('@/views/retrieve/activate.vue'),
    hidden: true,
  },
  {
    path: '/retrieve',
    component: () => import('@/views/retrieve/index.vue'),
    hidden: true,
  },
  {
    path: '/404',
    component: () => import('@/views/404.vue'),
    hidden: true,
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '首页', icon: 'dashboard', affix: true },
      },
    ],
  },
  {
    path: '/profile',
    component: Layout,
    redirect: '/profile/index',
    children: [
      {
        path: 'index',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: { title: '用户', icon: 'user' },
      },
    ],
  },
  {
    path: '/userrank',
    component: Layout,
    redirect: '/userrank/list',
    children: [
      {
        path: 'list',
        name: 'UserRank',
        component: () => import('@/views/rank/index.vue'),
        meta: { title: '积分总榜', icon: 'form' },
      },
    ],
  },
  {
    path: '/scene',
    component: Layout,
    redirect: '/scene/list',
    children: [
      {
        path: 'list',
        name: 'Scene',
        component: () => import('@/views/scene/list.vue'),
        meta: { title: '场景', icon: 'table' },
      },
      {
        path: 'index/:id',
        name: 'SceneDetail',
        component: () => import('@/views/scene/index.vue'),
        hidden: true,
        meta: { title: '场景详情' },
      },
      {
        path: 'timeindex/:id',
        name: 'TimeSceneDetail',
        component: () => import('@/views/scene/timeindex.vue'),
        hidden: true,
        meta: { title: '计时场景' },
      },
    ],
  },
  {
    path: '/notices',
    component: Layout,
    redirect: '/notices/all',
    children: [
      {
        path: 'all',
        name: 'Notice',
        component: () => import('@/views/notice/notices.vue'),
        meta: { title: '公告列表', icon: 'notice' },
      },
    ],
  },
]

const createRouterFn = () =>
  createRouter({
    history: createWebHashHistory(),
    scrollBehavior: () => ({ top: 0 }),
    routes: constantRoutes,
  })

const router = createRouterFn()

export function resetRouter() {
  const newRouter = createRouterFn()
  router.matcher = newRouter.matcher
}

export const asyncRoutes = [
  {
    path: '/image',
    component: Layout,
    redirect: '/image/image',
    meta: { role: ['admin'], title: '镜像管理', icon: 'docker' },
    children: [
      {
        path: 'image',
        name: 'ImageManage',
        component: () => import('@/views/image/index.vue'),
        meta: { title: '镜像管理', icon: 'docker', role: ['admin'] },
      },
      {
        path: 'images',
        name: 'TargetManage',
        component: () => import('@/views/manager/images.vue'),
        meta: { title: '靶场管理', icon: 'bug', role: ['admin'] },
      },
    ],
  },
  {
    path: '/layout',
    component: Layout,
    redirect: '/layout/network',
    meta: { role: ['admin'], title: '场景管理', icon: 'barrage_fill' },
    children: [
      {
        path: 'network',
        name: 'NetworkManage',
        component: () => import('@/views/network/index.vue'),
        meta: { title: '网卡管理', icon: 'tree', role: ['admin'] },
      },
      {
        path: 'manager',
        name: 'LayoutManage',
        component: () => import('@/views/layout/manager.vue'),
        meta: { title: '环境编排管理', icon: 'barrage_fill', role: ['admin'] },
      },
      {
        path: 'index',
        name: 'LayoutEditor',
        component: () => import('@/views/layout/index.vue'),
        hidden: true,
        meta: { title: '环境编排', role: ['admin'] },
      },
    ],
  },
  {
    path: '/manager',
    component: Layout,
    redirect: '/manager/user',
    meta: { role: ['admin'], title: '系统管理', icon: 'setting' },
    children: [
      {
        path: 'user',
        name: 'UserManage',
        component: () => import('@/views/manager/user.vue'),
        meta: { title: '用户管理', icon: 'user', role: ['admin'] },
      },
      {
        path: 'log',
        name: 'LogManage',
        component: () => import('@/views/manager/log.vue'),
        meta: { title: '日志管理', icon: 'log', role: ['admin'] },
      },
      {
        path: 'setting',
        name: 'SystemSetting',
        component: () => import('@/views/manager/setting.vue'),
        meta: { title: '系统配置', icon: 'setting', role: ['admin'] },
      },
      {
        path: 'notice',
        name: 'NoticeManage',
        component: () => import('@/views/notice/notice_index.vue'),
        meta: { title: '公告管理', icon: 'notice', role: ['admin'] },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/404', hidden: true },
]

export default router
