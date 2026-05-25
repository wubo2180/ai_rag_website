<template>
  <div class="terms-container">
    <div class="terms-content">
      <div class="terms-header">
        <h1 class="terms-title">用户服务条款</h1>
      </div>

      <div class="terms-body">
        <section class="terms-section">
          <h2>1. 服务说明</h2>
          <p>本服务为AI智能对话演示系统，旨在为用户提供人工智能对话体验。本系统仅供学习、研究和演示使用，不用于商业用途。</p>
        </section>

        <section class="terms-section">
          <h2>2. 用户责任</h2>
          <p>用户在使用本服务时应当：</p>
          <ul>
            <li>遵守相关法律法规，不得进行违法或有害活动</li>
            <li>不得发布违法、有害、威胁、辱骂、骚扰、侵权或其他不当内容</li>
            <li>不得恶意攻击系统或干扰其他用户的正常使用</li>
            <li>保护自己的账户信息，不得与他人共享账户</li>
          </ul>
        </section>

        <section class="terms-section">
          <h2>3. 服务内容</h2>
          <p>本服务提供以下功能：</p>
          <ul>
            <li>AI智能对话功能</li>
            <li>对话历史记录保存</li>
            <li>相关问题推荐</li>
            <li>用户账户管理</li>
          </ul>
        </section>

        <section class="terms-section">
          <h2>4. 免责声明</h2>
          <p>本服务按"现状"提供，我们不保证：</p>
          <ul>
            <li>服务的准确性、可靠性或完整性</li>
            <li>服务不会中断或无错误</li>
            <li>通过服务获得的信息的准确性</li>
          </ul>
          <p>用户使用本服务的风险由用户自行承担。</p>
        </section>

        <section class="terms-section">
          <h2>5. 知识产权</h2>
          <p>本服务的所有内容，包括但不限于文本、图片、代码、设计等，均受知识产权法保护。未经授权，用户不得复制、修改、分发或以其他方式使用这些内容。</p>
        </section>

        <section class="terms-section">
          <h2>6. 服务变更与终止</h2>
          <p>我们保留随时修改、暂停或终止服务的权利，无需事先通知。我们也可能因为技术、法律或其他原因对服务条款进行修改。</p>
        </section>

        <section class="terms-section">
          <h2>7. 争议解决</h2>
          <p>因使用本服务产生的争议，应通过友好协商解决。如协商不成，可向有管辖权的人民法院提起诉讼。</p>
        </section>

        <section class="terms-section">
          <h2>8. 隐私保护</h2>
          <p>我们重视用户隐私保护：</p>
          <ul>
            <li>严格按照隐私协议处理用户信息</li>
            <li>不会未经授权收集或使用个人信息</li>
            <li>采用行业标准的安全措施保护数据</li>
            <li>定期审查和更新隐私保护措施</li>
          </ul>
        </section>

        <section class="terms-section">
          <h2>9. 服务费用</h2>
          <p>关于服务费用的说明：</p>
          <ul>
            <li>当前版本为免费演示版本</li>
            <li>未来可能推出付费功能或服务</li>
            <li>任何收费变更将提前30天通知用户</li>
            <li>用户有权在收费前停止使用服务</li>
          </ul>
        </section>

        <section class="terms-section">
          <h2>10. 技术支持</h2>
          <p>我们提供以下技术支持：</p>
          <ul>
            <li>在线帮助文档和常见问题解答</li>
            <li>邮件技术支持服务</li>
            <li>定期的系统维护和更新</li>
            <li>用户反馈收集和处理机制</li>
          </ul>
        </section>

        <section class="terms-section">
          <h2>11. 适用法律</h2>
          <p>本服务条款受中华人民共和国法律管辖。如本条款的任何条款被认定为无效或不可执行，其余条款仍然有效。</p>
        </section>

        <section class="terms-section">
          <h2>12. 条款生效</h2>
          <p>本服务条款自用户同意之日起生效，直至用户停止使用服务或我们终止服务为止。即使服务终止，涉及用户责任、免责声明、争议解决等条款仍然有效。</p>
        </section>

        <section class="terms-section">
          <h2>13. 联系方式</h2>
          <p>如您对本服务条款有任何疑问或建议，请通过以下方式联系我们：</p>
          <p><strong>邮箱：</strong>support@ai-chat-demo.com</p>
          <p><strong>客服时间：</strong>工作日 9:00-18:00</p>
          <p>我们将在收到您的询问后3个工作日内回复。</p>
        </section>

        <div class="terms-footer">
          <p>本服务条款最后更新时间：2025年9月1日</p>
          <p>本条款自发布之日起生效。</p>
          <p>感谢您使用我们的AI智能对话服务！</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 用户服务条款页面 - 全屏显示
</script>

<style scoped>
.terms-container {
  min-height: 100vh;
  width: 100vw;
  background: #f8fafc;
  padding: 0;
  position: absolute;
  top: 0;
  left: 0;
  overflow-y: auto;
}

.terms-content {
  width: 100%;
  background: white;
  min-height: 100vh;
  padding-bottom: 60px;
}

.terms-header {
  background: #4f46e5;
  color: white;
  padding: 40px 32px;
  text-align: center;
}

.terms-title {
  margin: 0;
  font-size: 36px;
  font-weight: 600;
}

.terms-body {
  max-width: 900px;
  margin: 0 auto;
  padding: 60px 40px;
  line-height: 1.8;
  color: #374151;
  text-align: center;
}

.terms-section {
  margin-bottom: 48px;
  text-align: left;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.terms-section h2 {
  color: #1f2937;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 3px solid #4f46e5;
  text-align: center;
}

.terms-section p {
  margin-bottom: 16px;
  font-size: 18px;
  text-align: justify;
  line-height: 1.8;
}

.terms-section ul {
  margin: 16px 0;
  padding-left: 32px;
  text-align: left;
}

.terms-section li {
  margin-bottom: 12px;
  font-size: 18px;
  line-height: 1.7;
}

.terms-footer {
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
  text-align: center;
  color: #6b7280;
  font-size: 14px;
}

.terms-footer p {
  margin: 4px 0;
}

@media (max-width: 768px) {
  .terms-header {
    padding: 30px 20px;
  }
  
  .terms-title {
    font-size: 28px;
  }
  
  .terms-body {
    padding: 40px 20px;
  }
  
  .terms-section h2 {
    font-size: 20px;
  }
  
  .terms-section p,
  .terms-section li {
    font-size: 16px;
  }
  
  .terms-section ul {
    padding-left: 24px;
  }
}
</style>