import request from './index'

export const dashboardApi = {
  // 获取仪表盘统计数据
  getStatistics() {
    return request({
      url: '/dashboard/statistics',
      method: 'get'
    })
  },

  // 获取系统状态信息
  getSystemStatus() {
    return request({
      url: '/dashboard/system-status',
      method: 'get'
    })
  }
}

