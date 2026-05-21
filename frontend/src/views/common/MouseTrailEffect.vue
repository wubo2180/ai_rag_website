<template>
  <canvas ref="trailCanvas" class="mouse-trail-canvas"></canvas>
</template>

<script>
export default {
  name: 'MouseTrailEffect',
  props: {
    particleCount: {
      type: Number,
      default: 5
    },
    particleColor: {
      type: String,
      default: 'random' // 'random' 或特定颜色如 '#4f46e5'
    },
    particleSize: {
      type: Number,
      default: 5
    },
    particleLifespan: {
      type: Number,
      default: 40 // 粒子存在的帧数
    }
  },
  data() {
    return {
      particles: [],
      mouse: {
        x: null,
        y: null,
        lastX: null,
        lastY: null
      },
      animationId: null
    };
  },
  mounted() {
    this.initCanvas();
    window.addEventListener('mousemove', this.handleMouseMove);
    window.addEventListener('touchmove', this.handleTouchMove);
    this.animate();
  },
  beforeUnmount() {
    window.removeEventListener('mousemove', this.handleMouseMove);
    window.removeEventListener('touchmove', this.handleTouchMove);
    cancelAnimationFrame(this.animationId);
  },
  methods: {
    initCanvas() {
      const canvas = this.$refs.trailCanvas;
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      
      // 处理窗口大小变化
      window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
      });
    },
    
    handleMouseMove(event) {
      this.mouse.lastX = this.mouse.x;
      this.mouse.lastY = this.mouse.y;
      this.mouse.x = event.clientX;
      this.mouse.y = event.clientY;
      
      this.createParticles();
    },
    
    handleTouchMove(event) {
      event.preventDefault();
      this.mouse.lastX = this.mouse.x;
      this.mouse.lastY = this.mouse.y;
      this.mouse.x = event.touches[0].clientX;
      this.mouse.y = event.touches[0].clientY;
      
      this.createParticles();
    },
    
    createParticles() {
      // 只有当鼠标移动时才创建粒子
      if (this.mouse.x !== null && this.mouse.lastX !== null) {
        for (let i = 0; i < this.particleCount; i++) {
          // 在鼠标当前位置和上一个位置之间随机生成粒子
          const x = this.mouse.lastX + (this.mouse.x - this.mouse.lastX) * Math.random();
          const y = this.mouse.lastY + (this.mouse.y - this.mouse.lastY) * Math.random();
          
          this.particles.push({
            x,
            y,
            size: Math.random() * this.particleSize + 1,
            speedX: Math.random() * 3 - 1.5,
            speedY: Math.random() * 3 - 1.5,
            life: this.particleLifespan,
            color: this.getParticleColor()
          });
        }
      }
    },
    
    getParticleColor() {
      if (this.particleColor === 'random') {
        return `hsl(${Math.random() * 360}, 100%, 50%)`;
      }
      return this.particleColor;
    },
    
    animate() {
      const canvas = this.$refs.trailCanvas;
      const ctx = canvas.getContext('2d');
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      for (let i = 0; i < this.particles.length; i++) {
        const p = this.particles[i];
        
        // 更新粒子位置
        p.x += p.speedX;
        p.y += p.speedY;
        
        // 减小粒子大小和生命值
        p.size *= 0.95;
        p.life--;
        
        // 绘制粒子
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        
        // 移除生命值为0或尺寸过小的粒子
        if (p.life <= 0 || p.size < 0.3) {
          this.particles.splice(i, 1);
          i--;
        }
      }
      
      this.animationId = requestAnimationFrame(this.animate);
    }
  }
};
</script>

<style scoped>
.mouse-trail-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999; /* 确保在最上层但不影响交互 */
}
</style>