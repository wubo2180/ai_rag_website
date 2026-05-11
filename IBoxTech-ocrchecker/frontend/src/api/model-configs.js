/**
 * 模型配置API
 */
import request from './index'

export const modelConfigsApi = {
  // 获取模型配置列表
  getAll(params) {
    return request({
      url: '/model-configs',
      method: 'get',
      params
    })
  },

  // 获取单个模型配置
  getById(id) {
    return request({
      url: `/model-configs/${id}`,
      method: 'get'
    })
  },

  // 创建模型配置
  create(data) {
    return request({
      url: '/model-configs',
      method: 'post',
      data
    })
  },

  // 更新模型配置
  update(id, data) {
    return request({
      url: `/model-configs/${id}`,
      method: 'put',
      data
    })
  },

  // 删除模型配置
  delete(id) {
    return request({
      url: `/model-configs/${id}`,
      method: 'delete'
    })
  },

  // 获取适用于文件的模型配置
  getForFile(fileType) {
    return request({
      url: '/model-configs/get-for-file',
      method: 'get',
      params: { file_type: fileType }
    })
  }
}

