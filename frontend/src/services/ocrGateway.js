import apiClient from '@/utils/api'

export const ocrGatewayAPI = {
  async health() {
    const response = await apiClient.get('/ocr/health')
    return response.data
  },

  async serviceHealth(service) {
    const response = await apiClient.get(`/ocr/${service}/health`)
    return response.data
  },

  async getTaskStatus(taskId, service = '') {
    const response = await apiClient.get(`/ocr/tasks/${encodeURIComponent(taskId)}`, {
      params: service ? { service } : {},
    })
    return response.data
  },

  async proxyRequest(service, path, method = 'GET', data = null, params = null, headers = null) {
    const response = await apiClient.request({
      url: `/ocr/${service}/${path}`,
      method,
      data,
      params,
      headers,
    })
    return response.data
  },
}

export default ocrGatewayAPI
