<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1 class="error-title">页面不存在</h1>
      <p class="error-description">
        抱歉，您访问的页面不存在或已被移动。
      </p>
      <div class="error-actions">
        <el-button type="primary" @click="goHome">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回上页
        </el-button>
      </div>
    </div>
    
    <div class="error-illustration">
      <el-icon class="illustration-icon"><WarningFilled /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>

.not-found-container {
  @include flex-center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: $spacing-lg;
}

.not-found-content {
  text-align: center;
  color: white;
  max-width: 500px;
  
  .error-code {
    font-size: 120px;
    font-weight: bold;
    line-height: 1;
    margin-bottom: $spacing-lg;
    text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  }
  
  .error-title {
    font-size: 32px;
    margin-bottom: $spacing-md;
    font-weight: 600;
  }
  
  .error-description {
    font-size: 16px;
    margin-bottom: $spacing-xl;
    opacity: 0.9;
    line-height: 1.6;
  }
  
  .error-actions {
    display: flex;
    gap: $spacing-md;
    justify-content: center;
    
    @include respond-to(sm) {
      flex-direction: column;
      
      .el-button {
        width: 100%;
      }
    }
  }
}

.error-illustration {
  margin-top: $spacing-xl;
  
  .illustration-icon {
    font-size: 200px;
    color: rgba(255, 255, 255, 0.3);
  }
}

@include respond-to(sm) {
  .not-found-content {
    .error-code {
      font-size: 80px;
    }
    
    .error-title {
      font-size: 24px;
    }
  }
  
  .error-illustration {
    .illustration-icon {
      font-size: 120px;
    }
  }
}
</style>
