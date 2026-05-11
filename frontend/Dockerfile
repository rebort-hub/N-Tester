# 构建阶段
FROM node:20.0-alpine as build-stage

WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN yarn install --registry=https://registry.npmmirror.com

# 复制项目文件
COPY . .

# 构建生产版本
RUN yarn run build

# 生产阶段
FROM nginx:alpine as production-stage

# 复制构建产物到 nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
