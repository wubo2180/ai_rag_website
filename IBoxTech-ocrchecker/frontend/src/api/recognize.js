import request from './index'

/**
 * OCR识别相关API
 */
export const recognizeApi = {
  /**
   * 触发OCR识别（异步任务）
   * 立即返回任务ID
   */
  recognize(fileId) {
    return request({
      url: `/files/${fileId}/ocr/recognize`,
      method: 'post'
    })
  },

  /**
   * 获取任务状态
   * 用于轮询任务进度
   */
  getTaskStatus(taskId) {
    return request({
      url: `/files/ocr/task/${taskId}`,
      method: 'get'
    })
  },

  /**
   * 保存OCR识别结果到数据库
   */
  saveOcrResult(fileId, ocrResult) {
    return request({
      url: `/files/${fileId}/ocr/save`,
      method: 'post',
      data: {
        ocr_result: ocrResult
      }
    })
  }
}




