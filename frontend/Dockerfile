# === 階段一：建構階段 ===
FROM node:20-alpine AS builder

# 設定工作目錄
WORKDIR /app

# 複製 package 文件並安裝依賴
COPY package*.json ./
RUN npm install

# 複製源代碼並建構
COPY . .
RUN npm run build

# === 階段二：生產階段 ===
FROM nginx:alpine

# 安裝 curl 用於健康檢查
RUN apk add --no-cache curl

# 複製自定義 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 從建構階段複製打包後的檔案
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 啟動 nginx
CMD ["nginx", "-g", "daemon off;"]
