<template>
  <div class="particle-container" ref="particleContainer"></div>
</template>

<script>
export default {
  name: 'ParticleBackground',
  props: {
    color: {
      type: String,
      default: '#1a73e8'
    },
    particleCount: {
      type: Number,
      default: 80
    },
    speed: {
      type: Number,
      default: 1
    },
    connectParticles: {
      type: Boolean,
      default: true
    },
    minDistance: {
      type: Number,
      default: 120
    }
  },
  data() {
    return {
      particles: [],
      canvas: null,
      ctx: null,
      width: 0,
      height: 0,
      animationFrameId: null,
      mouse: {
        x: null,
        y: null,
        radius: 100 // 鼠标影响半径
      }
    }
  },
  mounted() {
    // 确保DOM已经渲染完成
    this.$nextTick(() => {
      this.initCanvas()
      window.addEventListener('resize', this.handleResize)
      
      // 添加鼠标移动事件监听
      this.canvas.addEventListener('mousemove', this.handleMouseMove)
      this.canvas.addEventListener('mouseleave', this.handleMouseLeave)
      
      // 触摸设备支持
      this.canvas.addEventListener('touchmove', this.handleTouchMove)
      this.canvas.addEventListener('touchend', this.handleMouseLeave)
    })
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    
    // 移除鼠标事件监听
    this.canvas.removeEventListener('mousemove', this.handleMouseMove)
    this.canvas.removeEventListener('mouseleave', this.handleMouseLeave)
    this.canvas.removeEventListener('touchmove', this.handleTouchMove)
    this.canvas.removeEventListener('touchend', this.handleMouseLeave)
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId)
    }
  },
  methods: {
    initCanvas() {
      const container = this.$refs.particleContainer
      this.canvas = document.createElement('canvas')
      this.ctx = this.canvas.getContext('2d')
      container.appendChild(this.canvas)
      
      this.handleResize()
      this.createParticles()
      this.animate()
    },
    handleResize() {
      const container = this.$refs.particleContainer
      this.width = container.offsetWidth
      this.height = container.offsetHeight
      this.canvas.width = this.width
      this.canvas.height = this.height
      
      // 重新创建粒子以适应新尺寸
      this.createParticles()
    },
    createParticles() {
      this.particles = []
      
      for (let i = 0; i < this.particleCount; i++) {
        this.particles.push({
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          vx: (Math.random() - 0.5) * this.speed,
          vy: (Math.random() - 0.5) * this.speed,
          radius: Math.random() * 2 + 1,
          opacity: Math.random() * 0.5 + 0.3
        })
      }
    },
    animate() {
      this.ctx.clearRect(0, 0, this.width, this.height)
      this.updateParticles()
      this.drawParticles()
      
      if (this.connectParticles) {
        this.connectNearbyParticles()
      }
      
      this.animationFrameId = requestAnimationFrame(this.animate)
    },
    updateParticles() {
      for (let i = 0; i < this.particles.length; i++) {
        const p = this.particles[i]
        
        // 移动粒子
        p.x += p.vx
        p.y += p.vy
        
        // 鼠标交互 - 当鼠标靠近时粒子被弹开
        if (this.mouse.x !== null && this.mouse.y !== null) {
          const dx = p.x - this.mouse.x
          const dy = p.y - this.mouse.y
          const distance = Math.sqrt(dx * dx + dy * dy)
          
          if (distance < this.mouse.radius) {
            // 计算弹开方向和力度
            const angle = Math.atan2(dy, dx)
            const force = (this.mouse.radius - distance) / this.mouse.radius
            
            // 应用弹开力
            p.vx += Math.cos(angle) * force * 2
            p.vy += Math.sin(angle) * force * 2
          }
        }
        
        // 限制最大速度
        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
        const maxSpeed = 3
        if (speed > maxSpeed) {
          p.vx = (p.vx / speed) * maxSpeed
          p.vy = (p.vy / speed) * maxSpeed
        }
        
        // 添加阻力，使粒子逐渐恢复正常速度
        p.vx *= 0.95
        p.vy *= 0.95
        
        // 边界检查
        if (p.x < 0) {
          p.x = this.width
        } else if (p.x > this.width) {
          p.x = 0
        }
        
        if (p.y < 0) {
          p.y = this.height
        } else if (p.y > this.height) {
          p.y = 0
        }
      }
    },
    drawParticles() {
      for (let i = 0; i < this.particles.length; i++) {
        const p = this.particles[i]
        
        this.ctx.beginPath()
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        this.ctx.closePath()
        
        // 设置粒子颜色和透明度
        const color = this.hexToRgb(this.color)
        this.ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${p.opacity})`
        this.ctx.fill()
      }
    },
    connectNearbyParticles() {
      for (let i = 0; i < this.particles.length; i++) {
        for (let j = i + 1; j < this.particles.length; j++) {
          const p1 = this.particles[i]
          const p2 = this.particles[j]
          
          const dx = p1.x - p2.x
          const dy = p1.y - p2.y
          const distance = Math.sqrt(dx * dx + dy * dy)
          
          if (distance < this.minDistance) {
            // 根据距离计算线条透明度
            const opacity = 1 - (distance / this.minDistance)
            
            this.ctx.beginPath()
            this.ctx.moveTo(p1.x, p1.y)
            this.ctx.lineTo(p2.x, p2.y)
            
            const color = this.hexToRgb(this.color)
            this.ctx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${opacity * 0.5})`
            this.ctx.lineWidth = 1
            this.ctx.stroke()
            this.ctx.closePath()
          }
        }
      }
    },
    hexToRgb(hex) {
      // 移除可能的 # 前缀
      hex = hex.replace(/^#/, '')
      
      // 解析十六进制颜色
      const bigint = parseInt(hex, 16)
      const r = (bigint >> 16) & 255
      const g = (bigint >> 8) & 255
      const b = bigint & 255
      
      return { r, g, b }
    },
    
    // 鼠标事件处理函数
    handleMouseMove(e) {
      const rect = this.canvas.getBoundingClientRect()
      this.mouse.x = e.clientX - rect.left
      this.mouse.y = e.clientY - rect.top
    },
    
    handleMouseLeave() {
      this.mouse.x = null
      this.mouse.y = null
    },
    
    handleTouchMove(e) {
      if (e.touches.length > 0) {
        const rect = this.canvas.getBoundingClientRect()
        this.mouse.x = e.touches[0].clientX - rect.left
        this.mouse.y = e.touches[0].clientY - rect.top
        
        // 防止触摸时页面滚动
        e.preventDefault()
      }
    }
  }
}
</script>

<style scoped>
.particle-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
  pointer-events: auto; /* 允许鼠标交互 */
}
</style>