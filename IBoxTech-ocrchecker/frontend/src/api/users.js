/**
 * 用户管理相关API
 */
import request from './index'

export const usersApi = {
  /**
   * 获取用户列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.per_page - 每页数量
   * @param {string} params.search - 搜索关键词
   * @param {string} params.role - 角色筛选
   * @param {string} params.status - 状态筛选
   * @param {string} params.sort_by - 排序字段
   * @param {string} params.sort_order - 排序方向
   * @returns {Promise}
   */
  getUsers(params = {}) {
    return request({
      url: '/users',
      method: 'get',
      params
    })
  },

  /**
   * 创建新用户
   * @param {Object} data - 用户数据
   * @param {string} data.username - 用户名
   * @param {string} data.email - 邮箱
   * @param {string} data.password - 密码
   * @param {string} data.real_name - 真实姓名
   * @param {string} data.role - 角色
   * @param {boolean} data.is_active - 是否激活
   * @returns {Promise}
   */
  createUser(data) {
    return request({
      url: '/users',
      method: 'post',
      data
    })
  },

  /**
   * 更新用户信息
   * @param {number} userId - 用户ID
   * @param {Object} data - 更新的数据
   * @returns {Promise}
   */
  updateUser(userId, data) {
    return request({
      url: `/users/${userId}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除用户
   * @param {number} userId - 用户ID
   * @returns {Promise}
   */
  deleteUser(userId) {
    return request({
      url: `/users/${userId}`,
      method: 'delete'
    })
  },

  /**
   * 获取用户统计信息
   * @returns {Promise}
   */
  getUserStats() {
    return request({
      url: '/users/stats',
      method: 'get'
    })
  },

  /**
   * 重置用户密码
   * @param {number} userId - 用户ID
   * @param {Object} data - 密码数据
   * @returns {Promise}
   */
  resetPassword(userId, data) {
    return request({
      url: `/users/${userId}/reset-password`,
      method: 'post',
      data
    })
  }
}

