// 登录调试脚本
console.log('开始登录调试...')

// 测试API代理是否工作
fetch('/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'test',
    password: 'test',
  }),
})
  .then((response) => {
    console.log('登录API响应状态:', response.status)
    console.log('响应头:', response.headers)
    return response.json()
  })
  .then((data) => {
    console.log('登录API响应数据:', data)
  })
  .catch((error) => {
    console.error('登录API错误:', error)
  })

// 测试直接连接到后端
fetch('http://172.20.46.18:8002/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'test',
    password: 'test',
  }),
})
  .then((response) => {
    console.log('直接后端API响应状态:', response.status)
    return response.json()
  })
  .then((data) => {
    console.log('直接后端API响应数据:', data)
  })
  .catch((error) => {
    console.error('直接后端API错误 (可能是CORS问题):', error)
  })
