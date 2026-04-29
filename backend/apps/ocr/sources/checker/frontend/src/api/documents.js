/**
 * 统一文档数据API接口
 * 
 * 支持自动识别文档类型（论文/委托单），无需前端判断
 * 
 * @author AI Assistant
 * @date 2025-11-17
 */
import request from './index'

/**
 * 统一文档数据API
 */
export const documentsApi = {
  /**
   * 获取文档数据（自动识别类型：论文/委托单）
   * 
   * @param {Number} fileId - 文件ID
   * @returns {Promise} 返回格式：
   * {
   *   success: true,
   *   data: {
   *     // 论文格式
   *     article_id: "...",
   *     article_name: "...",
   *     hierarchical_data: [...]
   *     
   *     // 或委托单格式
   *     basic_info: {...},
   *     test_items: [...],
   *     special_tests: [...]
   *   },
   *   document_type: "paper" | "commission"
   * }
   */
  getDocumentData(fileId) {
    return request({
      url: `/files/${fileId}/document-data`,
      method: 'get'
    })
  },

  /**
   * 保存/更新文档数据（自动识别类型：论文/委托单）
   * 
   * @param {Number} fileId - 文件ID
   * @param {Object} data - 文档数据
   * @returns {Promise} 返回格式：
   * {
   *   success: true,
   *   message: "保存成功",
   *   document_type: "paper" | "commission"
   * }
   */
  saveDocumentData(fileId, data) {
    return request({
      url: `/files/${fileId}/document-data`,
      method: 'put',
      data
    })
  },

  /**
   * 保存OCR识别结果（自动识别类型：论文/委托单）
   * 
   * 用于识别页面首次保存OCR结果
   * 
   * @param {Number} fileId - 文件ID
   * @param {Object} ocrResult - OCR识别结果
   * @returns {Promise} 返回格式：
   * {
   *   success: true,
   *   message: "OCR识别结果保存成功",
   *   document_type: "paper" | "commission"
   * }
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

export default documentsApi

