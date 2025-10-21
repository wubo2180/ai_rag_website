<template>
  <div id="app">
    <Navigation />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
  import Navigation from '@/components/Navigation.vue'

  export default {
    name: 'App',
    components: {
      Navigation,
    },
  }
</script>

<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html,
  body {
    height: 100%;
    width: 100%;
    overflow: hidden; /* 防止页面级别的滚动 */
  }

  #app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    color: #2c3e50;
    height: 100vh; /* 使用视口高度 */
    width: 100vw; /* 使用视口宽度 */
    display: flex;
    flex-direction: column;
    overflow: hidden; /* 防止应用级别的滚动 */
  }

  .main-content {
    flex: 1; /* 占用剩余空间 */
    overflow: auto; /* 允许滚动 */
    width: 100%;
    height: 100%;
  }
</style>
