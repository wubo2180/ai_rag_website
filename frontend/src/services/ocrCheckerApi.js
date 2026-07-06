import ocrGatewayAPI from '@/services/ocrGateway'
import apiClient from '@/utils/api'

const SERVICE = 'checker'

const ocrCheckerApi = {
  listFiles(params = {}) {
    return ocrGatewayAPI.proxyRequest(SERVICE, 'api/files', 'GET', null, params)
  },

  getFileDetail(fileId) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/${fileId}`, 'GET')
  },

  batchUpload(formData) {
    return ocrGatewayAPI.proxyRequest(SERVICE, 'api/files/batch-upload', 'POST', formData, null, {
      'Content-Type': 'multipart/form-data',
    })
  },

  deleteFile(fileId) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/${fileId}`, 'DELETE')
  },

  startRecognize(fileId) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/${fileId}/ocr/recognize`, 'POST')
  },

  saveOcrResult(fileId, ocrResult) {
    return ocrGatewayAPI.proxyRequest(
      SERVICE,
      `api/files/${fileId}/ocr/save`,
      'POST',
      { ocr_result: ocrResult },
    )
  },

  getTaskStatus(taskId) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/ocr/task/${taskId}`, 'GET')
  },

  getDocumentData(fileId, params = { refresh: 1 }) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/${fileId}/document-data`, 'GET', null, params)
  },

  updateDocumentData(fileId, payload) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/${fileId}/document-data`, 'PUT', payload)
  },

  completeReview(fileId) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/${fileId}/complete-review`, 'POST')
  },

  markAsUnreviewed(fileId) {
    return ocrGatewayAPI.proxyRequest(SERVICE, `api/files/${fileId}/mark-unreviewed`, 'POST')
  },

  getFilePreviewUrl(fileId, expires = 3600) {
    return apiClient.request({
      url: `/ocr/pdf/${fileId}/preview`,
      method: 'GET',
      params: { expires },
    }).then((response) => response.data)
  },

  async downloadFileBlob(fileId, preview = true) {
    const response = await apiClient.request({
      url: `/ocr/pdf/${fileId}/download`,
      method: 'GET',
      params: { preview: preview ? 'true' : 'false' },
      responseType: 'blob',
    })
    return response.data
  },
}

export default ocrCheckerApi
