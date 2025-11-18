// 添加到浏览器控制台的调试工具
window.debugAuth = {
  // 检查当前认证状态
  checkAuth() {
    const accessToken = localStorage.getItem('access_token')
    const refreshToken = localStorage.getItem('refresh_token')
    
    console.log('🔍 认证状态检查:')
    console.log('Access Token:', accessToken ? `${accessToken.substring(0, 20)}...` : '未找到')
    console.log('Refresh Token:', refreshToken ? `${refreshToken.substring(0, 20)}...` : '未找到')
    
    if (accessToken) {
      try {
        // 解码JWT payload (不验证签名，仅查看内容)
        const payload = JSON.parse(atob(accessToken.split('.')[1]))
        const exp = new Date(payload.exp * 1000)
        const now = new Date()
        
        console.log('Token过期时间:', exp.toLocaleString())
        console.log('当前时间:', now.toLocaleString())
        console.log('Token是否过期:', now > exp)
        console.log('用户ID:', payload.user_id)
      } catch (e) {
        console.error('Token解析失败:', e)
      }
    }
  },
  
  // 手动测试API调用
  async testAPI() {
    try {
      const response = await fetch('/api/documents/stats/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      })
      
      console.log('API测试结果:')
      console.log('状态码:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('响应数据:', data)
      } else {
        console.error('API调用失败:', response.statusText)
      }
    } catch (error) {
      console.error('API测试失败:', error)
    }
  },
  
  // 清除认证信息
  clearAuth() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    console.log('认证信息已清除')
  }
}

console.log('🛠️ 认证调试工具已加载！使用以下命令:')
console.log('debugAuth.checkAuth() - 检查认证状态')
console.log('debugAuth.testAPI() - 测试API调用')
console.log('debugAuth.clearAuth() - 清除认证信息')