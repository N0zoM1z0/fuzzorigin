FROM python:3.7-alpine

WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# 【加速 1】修改 Alpine 系统软件源为阿里云镜像
# 这一步必须在 apk add 之前执行
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 安装系统依赖
RUN apk add --no-cache gcc musl-dev linux-headers

COPY requirements.txt requirements.txt

# 【加速 2】升级 pip 并修改 Python 包源为清华源 (也可以用阿里云)
# --no-cache-dir 可以减小镜像体积
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

EXPOSE 7009
COPY . .
CMD ["flask", "run"]