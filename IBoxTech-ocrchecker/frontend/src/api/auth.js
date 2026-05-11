import request from './index'

export const authApi = {
  // 用户登录
  login(data) {
    return request({
      url: '/auth/login',
      method: 'post',
      data
    })
  },

  // 用户注册
  register(data) {
    return request({
      url: '/auth/register',
      method: 'post',
      data
    })
  },

  // 刷新令牌
  refresh() {
    return request({
      url: '/auth/refresh',
      method: 'post'
    })
  },

  // 登出
  logout() {
    return request({
      url: '/auth/logout',
      method: 'post'
    })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request({
      url: '/auth/me',
      method: 'get'
    })
  },

  // 修改密码
  changePassword(data) {
    return request({
      url: '/auth/change-password',
      method: 'post',
      data
    })
  }
}
