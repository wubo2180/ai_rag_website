import request, { uploadRequest } from './index'

export const filesApi = {
  // 单个文件上传
  uploadFile(formData, onProgress) {
    return uploadRequest({
      url: '/files/upload',
      method: 'post',
      data: formData,
      onUploadProgress: onProgress
    })
  },

  // 批量文件上传
  batchUploadFiles(formData, onProgress) {
    return uploadRequest({
      url: '/files/batch-upload',
      method: 'post',
      data: formData,
      onUploadProgress: onProgress
    })
  },

  // 获取文件列表
  getFiles(params = {}) {
    return request({
      url: '/files',
      method: 'get',
      params
    })
  },

  // 获取文件详情
  getFileDetail(fileId) {
    return request({
      url: `/files/${fileId}`,
      method: 'get'
    })
  },

  // 更新文件信息
  updateFile(fileId, data) {
    return request({
      url: `/files/${fileId}`,
      method: 'put',
      data
    })
  },

  // 删除文件
  deleteFile(fileId, hardDelete = false) {
    return request({
      url: `/files/${fileId}`,
      method: 'delete',
      params: { hard: hardDelete }
    })
  },

  // 恢复文件
  restoreFile(fileId) {
    return request({
      url: `/files/${fileId}/restore`,
      method: 'post'
    })
  },

  // 下载文件
  downloadFile(fileId, preview = false) {
    return request({
      url: `/files/${fileId}/download`,
      method: 'get',
      responseType: 'blob',
      params: preview ? { preview: 'true' } : {}
    })
  },

  // 获取文件预览URL
  getPreviewUrl(fileId, expires = 3600) {
    return request({
      url: `/files/${fileId}/preview`,
      method: 'get',
      params: { expires }
    })
  },

  // 开始OCR处理（旧版同步方式）
  // @deprecated: 建议使用 recognizeApi.recognize() 创建异步任务
  // 当前用于：文件列表页面的"开始处理"功能
  // 推荐替代：recognizeApi.recognize() + recognizeApi.getTaskStatus()
  // 迁移计划：待系统稳定后，将文件列表页面迁移到异步任务
  startProcessing(fileId, modelId = null) {
    return request({
      url: `/files/${fileId}/process`,
      method: 'post',
      data: modelId ? { model_id: modelId } : {}
    })
  },

  // 批量分配文件
  batchAssignFiles(data) {
    return request({
      url: '/files/batch-assign',
      method: 'post',
      data
    })
  },

  // 完成文件核对
  completeReview(fileId) {
    return request({
      url: `/files/${fileId}/complete-review`,
      method: 'post'
    })
  }
}
