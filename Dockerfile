FROM python:3.12
LABEL maintainer="Prometheus <99234@qq.com>" version="0.3.2.11" description="Vulfocus for Docker"
EXPOSE 80

RUN mkdir /vulfocus-api/
WORKDIR /vulfocus-api/
ADD vulfocus-api/ /vulfocus-api/

ENV VUL_IP="" EMAIL_HOST="" EMAIL_HOST_USER="" EMAIL_HOST_PASSWORD="" DOCKER_URL="unix://var/run/docker.sock"

RUN rm -rf /etc/apt/sources.list.d/* && \
    echo 'deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list && \
    echo 'deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware' >> /etc/apt/sources.list && \
    apt update && \
    apt install -y redis-server nginx && \
    rm -rf /var/www/html/* && \
    cp /vulfocus-api/nginx.conf /etc/nginx/nginx.conf && \
    cp /vulfocus-api/default /etc/nginx/sites-available/default && \
    cp /vulfocus-api/default /etc/nginx/sites-enabled/default && \
    python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && \
    chmod u+x /vulfocus-api/run.sh && \
    python3 -c "import site, os; p=site.getsitepackages()[0]; d=os.path.join(p, 'distutils'); os.makedirs(d, exist_ok=True); open(os.path.join(d, 'version.py'), 'w').write('from packaging.version import Version as StrictVersion, Version')"

ADD dist/ /var/www/html/
CMD ["sh", "/vulfocus-api/run.sh"]