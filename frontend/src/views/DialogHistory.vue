<template>
  <div class="dialog-history-container" :class="{ disabled }">
    <h4>对话历史</h4>
    <div class="history-list">
      <div v-for="(group, gIndex) in groups" :key="gIndex" class="history-group">
        <p class="date">{{ group.label }}</p>
        <ul>
          <li
            v-for="item in group.items"
            :key="item.id"
            class="history-item"
            @contextmenu.prevent="showContextMenu($event, item)"
          >
            <a
              href="#"
              class="history-link"
              :title="disabled ? 'AI正在回复，无法切换对话' : new Date(item.timestamp).toLocaleString()"
              :class="{ 'not-allowed': disabled }"
              @click.prevent="handleSelect(item.index)"
            >
              <img src="@/assets/talk page/talk@3X_52.png" alt="历史图标" class="history-icon" />
              {{ item.title }}
            </a>
          </li>
        </ul>
      </div>
    </div>
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ top: contextMenu.top + 'px', left: contextMenu.left + 'px' }"
    >
      <ul>
        <li @click="deleteHistory">删除</li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DialogHistory',
  emits: ['select', 'delete'],
  props: {
    groups: {
      type: Array,
      default: () => []
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      contextMenu: {
        visible: false,
        top: 0,
        left: 0,
        item: null
      }
    };
  },
  mounted() {
    document.addEventListener('click', this.closeContextMenu);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeContextMenu);
  },
  methods: {
    handleSelect(index) {
      if (this.disabled) return; // 禁用态下不触发切换
      this.$emit('select', index);
    },
    showContextMenu(event, item) {
      if (this.disabled) return; // 禁用态下不展示右键菜单
      this.contextMenu.visible = true;
      this.contextMenu.top = event.clientY;
      this.contextMenu.left = event.clientX;
      this.contextMenu.item = item;
    },
    closeContextMenu() {
      this.contextMenu.visible = false;
      this.contextMenu.item = null;
    },
    deleteHistory() {
      if (this.contextMenu.item) {
        this.$emit('delete', this.contextMenu.item.index);
      }
      this.closeContextMenu();
    }
  }
};
</script>

<style scoped>
.dialog-history-container {
  width: 280px;
  padding: 30px;
  background-color: #f7f8fa;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  max-height: 100vh; /* 限制为视口高度，超出由内部滚动 */
  overflow: hidden; /* 由内部列表处理滚动 */
}

h4 {
  font-size: 16px; /* 与聊天区域顶部标签一致 */
  font-weight: 400; /* 与聊天顶部标签字重一致 */
  margin: 0 0 16px 0; /* 去掉顶部外边距，保持更靠上 */
  text-align: center; /* 居中显示“对话历史”标题 */
}

.history-list .date {
  font-size: 14px;
  color: #888;
  margin-bottom: 10px;
}

.history-list {
  flex: 1; /* 占满容器剩余空间 */
  overflow-y: auto; /* 内容超出时显示滚动条 */
}

.history-list ul {
  list-style: none;
  padding: 0;
  position: relative;
  overflow: visible; /* 允许子元素溢出显示（如右侧删除按钮） */
}

.history-list li {
  margin-bottom: 10px;
}

.history-item {
  position: relative;
  display: block;
}
.history-link {
  text-decoration: none;
  color: #333;
  display: block;
  padding: 10px;
  border-radius: 5px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.history-icon {
  width: 18px;
  height: 18px;
  margin-right: 8px;
  vertical-align: middle;
}

.dialog-history-container.disabled .history-link,
.history-link.not-allowed {
  cursor: not-allowed;
  opacity: 0.6;
}

.history-list li.active a {
  background-color: #e6f7ff;
  color: #007bff;
}

.context-menu {
  position: fixed;
  background-color: white;
  border: 1px solid #ccc;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
  z-index: 10000;
  border-radius: 5px;
}

.context-menu ul {
  list-style: none;
  padding: 5px 0;
  margin: 0;
}

.context-menu li {
  padding: 8px 15px;
  cursor: pointer;
}

.context-menu li:hover {
  background-color: #f0f0f0;
}
</style>