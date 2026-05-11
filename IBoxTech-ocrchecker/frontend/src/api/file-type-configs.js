/**
 * 文件类型配置 API
 */
import request from './index'

export const fileTypeConfigsApi = {
  // 获取文件类型配置列表
  getAll(params) {
    return request({
      url: '/file-type-configs',
      method: 'get',
      params
    })
  },

  // 获取单个文件类型配置
  getById(id) {
    return request({
      url: `/file-type-configs/${id}`,
      method: 'get'
    })
  },

  // 根据类型代码获取配置
  getByTypeCode(typeCode) {
    return request({
      url: `/file-type-configs/by-code/${typeCode}`,
      method: 'get'
    })
  },

  // 创建文件类型配置
  create(data) {
    return request({
      url: '/file-type-configs',
      method: 'post',
      data
    })
  },

  // 更新文件类型配置
  update(id, data) {
    return request({
      url: `/file-type-configs/${id}`,
      method: 'put',
      data
    })
  },

  // 删除文件类型配置
  delete(id) {
    return request({
      url: `/file-type-configs/${id}`,
      method: 'delete'
    })
  },

  // 切换启用状态
  toggleActive(id, isActive) {
    return request({
      url: `/file-type-configs/${id}/toggle-active`,
      method: 'patch',
      data: { is_active: isActive }
    })
  },

  // 获取所有模型配置（用于下拉选择）
  getModelConfigs() {
    return request({
      url: '/model-configs',
      method: 'get',
      params: { is_active: true }
    })
  },

  // 获取所有适配器列表
  getAdapters() {
    return request({
      url: '/file-type-configs/adapters',
      method: 'get'
    })
  },

  // 获取数据库表列表
  getDatabaseTables() {
    return request({
      url: '/file-type-configs/database-tables',
      method: 'get'
    })
  }
}

