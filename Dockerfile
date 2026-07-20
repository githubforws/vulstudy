# ============ 第一阶段：构建前端（Debian slim） ============
FROM node:18-bullseye-slim AS frontend-builder

WORKDIR /app

# ① 源和系统依赖：几乎不变，永久缓存
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends git python3 make g++ && \
    npm config set registry https://registry.npmmirror.com && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

# ② 仅先复制依赖声明文件 → npm install 层被缓存
#    只有 package.json / lock 文件变动时才重新安装依赖
COPY vulfocus-frontend/package.json vulfocus-frontend/package-lock.json* ./

RUN npm install && \
    chmod -R +x node_modules/.bin

# ③ 最后再复制全部源码 → 改代码不会触发 npm install
COPY vulfocus-frontend/ ./

RUN npm run build:prod


# ============ 第二阶段：最终镜像 ============
FROM python:3.12
LABEL maintainer="Prometheus <2835064365@qq.com>" version="0.4.7" description="Vulfocus for Docker"
EXPOSE 80

# ④ 系统依赖：几乎不变，永久缓存
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo 'deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list && \
    echo 'deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    apt update && \
    apt install -y redis-server nginx && \
    rm -rf /var/lib/apt/lists/* /var/www/html/*

# ⑤ 先复制 Nginx 配置和依赖声明 → 这些文件很少变动
COPY vulfocus-api/nginx.conf /etc/nginx/nginx.conf
COPY vulfocus-api/default /etc/nginx/sites-available/default
COPY vulfocus-api/default /etc/nginx/sites-enabled/default
COPY vulfocus-api/requirements.txt /tmp/requirements.txt

# ⑥ pip install 单独一层：requirements.txt 不变就不会重装
RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# ⑦ 最后复制全部后端代码
WORKDIR /vulfocus-api/
COPY vulfocus-api/ ./

RUN chmod u+x run.sh && \
    sed -i 's/\r$//' run.sh && \
    python3 -c "import site, os; p=site.getsitepackages()[0]; d=os.path.join(p, 'distutils'); os.makedirs(d, exist_ok=True); open(os.path.join(d, 'version.py'), 'w').write('from packaging.version import Version as StrictVersion, Version')"

# ⑧ 从前端阶段复制构建产物（仅影响最终镜像，不影响构建速度）
COPY --from=frontend-builder /app/dist/ /var/www/html/
#通过Docker run启动需要必须要设置VUL_IP为本机地址，否则无法正常出现访问地址
ENV VUL_IP="192.168.1.47" EMAIL_HOST="" EMAIL_HOST_USER="" EMAIL_HOST_PASSWORD="" DOCKER_URL="unix://var/run/docker.sock"

CMD ["sh", "/vulfocus-api/run.sh"]