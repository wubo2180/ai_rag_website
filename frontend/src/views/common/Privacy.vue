<template>
  <div class="privacy-container">
    <div class="privacy-content">
      <div class="privacy-header">
        <h1 class="privacy-title">隐私协议</h1>
      </div>

      <div class="privacy-body">
        <section class="privacy-section">
          <h2>1. 信息收集</h2>
          <p>我们收集以下类型的信息：</p>
          <ul>
            <li><strong>账户信息：</strong>用户名、邮箱地址等注册时提供的基本信息</li>
            <li><strong>使用数据：</strong>对话记录、使用时间、功能使用情况等</li>
            <li><strong>技术信息：</strong>IP地址、浏览器类型、设备信息等</li>
            <li><strong>本地存储：</strong>为改善用户体验而存储在本地的数据</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>2. 信息使用</h2>
          <p>我们使用收集的信息用于：</p>
          <ul>
            <li>提供和维护服务功能</li>
            <li>改善用户体验和服务质量</li>
            <li>进行技术支持和故障排除</li>
            <li>分析服务使用情况以优化功能</li>
            <li>确保服务安全和防止滥用</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>3. 信息保护</h2>
          <p>我们采取以下措施保护您的个人信息：</p>
          <ul>
            <li>使用加密技术保护数据传输</li>
            <li>实施访问控制和权限管理</li>
            <li>定期进行安全审计和漏洞检测</li>
            <li>建立数据备份和恢复机制</li>
            <li>制定数据安全管理制度</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>4. 信息共享</h2>
          <p>我们承诺：</p>
          <ul>
            <li>不会向第三方出售您的个人信息</li>
            <li>不会与第三方交易您的个人信息</li>
            <li>不会未经授权转让您的个人信息</li>
            <li>仅在法律要求或紧急情况下可能共享必要信息</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>5. Cookie和本地存储</h2>
          <p>我们使用以下技术：</p>
          <ul>
            <li><strong>LocalStorage：</strong>保存您的登录状态和对话记录</li>
            <li><strong>SessionStorage：</strong>临时存储会话数据</li>
            <li><strong>Cookie：</strong>记住您的偏好设置</li>
          </ul>
          <p>您可以通过浏览器设置管理这些存储数据。</p>
        </section>

        <section class="privacy-section">
          <h2>6. 数据保留</h2>
          <p>我们的数据保留政策：</p>
          <ul>
            <li>账户信息：在账户存续期间保留</li>
            <li>对话记录：本地存储，用户可自行删除</li>
            <li>使用日志：保留30天用于技术分析</li>
            <li>已删除数据：30天内可恢复，之后永久删除</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>7. 用户权利</h2>
          <p>您享有以下权利：</p>
          <ul>
            <li>查看和更新您的个人信息</li>
            <li>删除您的账户和相关数据</li>
            <li>导出您的对话记录</li>
            <li>撤回对数据处理的同意</li>
            <li>对数据处理提出异议</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>8. 未成年人保护</h2>
          <p>我们特别关注未成年人的隐私保护：</p>
          <ul>
            <li>不会故意收集13岁以下儿童的个人信息</li>
            <li>如发现收集了儿童信息，将立即删除</li>
            <li>建议未成年人在监护人指导下使用服务</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>9. 隐私政策更新</h2>
          <p>我们可能会不时更新本隐私政策。重大变更时，我们会：</p>
          <ul>
            <li>在服务中显著位置发布通知</li>
            <li>通过邮件通知注册用户</li>
            <li>给予用户合理时间审查变更</li>
          </ul>
        </section>

        <section class="privacy-section">
          <h2>10. 联系我们</h2>
          <p>如您对本隐私政策有任何疑问或建议，请联系我们：</p>
          <p>邮箱：privacy@ai-chat-demo.com</p>
          <p>我们将在收到您的询问后7个工作日内回复。</p>
        </section>

        <div class="privacy-footer">
          <p>本隐私协议最后更新时间：2025年9月1日</p>
          <p>本协议自发布之日起生效。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 隐私协议页面 - 全屏显示
</script>

<style scoped>
.privacy-container {
  min-height: 100vh;
  width: 100vw;
  background: #f8fafc;
  padding: 0;
  position: absolute;
  top: 0;
  left: 0;
  overflow-y: auto;
}

.privacy-content {
  width: 100%;
  background: white;
  min-height: 100vh;
  padding-bottom: 60px;
}

.privacy-header {
  background: #059669;
  color: white;
  padding: 40px 32px;
  text-align: center;
}

.privacy-title {
  margin: 0;
  font-size: 36px;
  font-weight: 600;
}

.privacy-body {
  max-width: 900px;
  margin: 0 auto;
  padding: 60px 40px;
  line-height: 1.8;
  color: #374151;
  text-align: center;
}

.privacy-section {
  margin-bottom: 32px;
}

.privacy-section h2 {
  color: #1f2937;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.privacy-section p {
  margin-bottom: 12px;
  font-size: 16px;
}

.privacy-section ul {
  margin: 12px 0;
  padding-left: 24px;
}

.privacy-section li {
  margin-bottom: 8px;
  font-size: 16px;
}

.privacy-section strong {
  color: #1f2937;
  font-weight: 600;
}

.privacy-footer {
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
  text-align: center;
  color: #6b7280;
  font-size: 14px;
}

.privacy-footer p {
  margin: 4px 0;
}

@media (max-width: 768px) {
  .privacy-header {
    padding: 30px 20px;
  }
  
  .privacy-title {
    font-size: 28px;
  }
  
  .privacy-body {
    padding: 40px 20px;
  }
  
  .privacy-section h2 {
    font-size: 20px;
  }
  
  .privacy-section p,
  .privacy-section li {
    font-size: 16px;
  }
  
  .privacy-section ul {
    padding-left: 24px;
  }
}
</style>