# gunicorn.conf.py
import multiprocessing

# 绑定地址和端口
bind = "0.0.0.0:8004"

# 工作进程数
workers = 4

# 工作进程类型（流式响应必须用 sync）
worker_class = "sync"

# 每个工作进程的线程数
threads = 1

# 请求超时时间（秒）
timeout = 300

# 优雅关闭超时时间（秒）
graceful_timeout = 30

# Keep-alive 连接时间（秒）
keepalive = 5

# 每个工作进程处理的最大请求数
max_requests = 1000

# 最大请求数的随机抖动范围
max_requests_jitter = 50

# 访问日志文件路径
accesslog = "/www/wwwlogs/gunicorn_access.log"

# 错误日志文件路径
errorlog = "/www/wwwlogs/gunicorn_error.log"

# 日志级别
loglevel = "info"

# 启用标准输入输出继承（注意：某些版本可能不支持）
# 如果不支持，可以注释掉这行
enable_stdio_inheritance = True

# 进程名称
proc_name = "ai_rag_website"

# 后台运行（设为 True 则后台运行，False 则前台运行）
daemon = False

# 工作进程类型额外配置
worker_connections = 1000

# 最大挂起的连接数
backlog = 2048

# 日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 在启动时打印配置信息
check_config = False

# 预加载应用（可以节省内存，但重载代码需要重启）
preload_app = False

# 重启前睡眠时间
reload = False
reload_extra_files = []