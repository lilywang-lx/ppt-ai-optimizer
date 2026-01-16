# Node.js 前端 Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# 复制package.json
COPY frontend/package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY frontend/ .

# 构建
RUN npm run build

# 生产环境
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
