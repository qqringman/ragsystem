#!/bin/bash

echo "🔍 Docker DNS 深度診斷"
echo "======================"
echo "時間: $(date)"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 系統 DNS 檢查
echo "1. 🖥️  主機系統 DNS 設定"
echo "------------------------"
echo "📄 /etc/resolv.conf 內容:"
cat /etc/resolv.conf
echo ""

echo "🌐 主機 DNS 解析測試:"
for domain in "google.com" "deb.debian.org" "pypi.org"; do
    if nslookup $domain >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $domain 解析成功${NC}"
        nslookup $domain | grep -A1 "Address" | tail -1
    else
        echo -e "${RED}❌ $domain 解析失敗${NC}"
    fi
done
echo ""

# 2. Docker daemon 設定
echo "2. 🐋 Docker Daemon 設定"
echo "------------------------"
if [ -f /etc/docker/daemon.json ]; then
    echo "📄 /etc/docker/daemon.json 內容:"
    cat /etc/docker/daemon.json
else
    echo -e "${YELLOW}⚠️  /etc/docker/daemon.json 不存在${NC}"
fi
echo ""

echo "🔧 Docker 系統資訊:"
docker system info 2>/dev/null | grep -E "Server Version:|Storage Driver:|Docker Root Dir:|Registry:" || echo "無法取得 Docker 資訊"
echo ""

# 3. Docker 網路檢查
echo "3. 🌐 Docker 網路設定"
echo "----------------------"
echo "📋 Docker 網路列表:"
docker network ls
echo ""

echo "🔍 預設 bridge 網路詳情:"
docker network inspect bridge 2>/dev/null | grep -A5 "Config\|Options" || echo "無法檢查 bridge 網路"
echo ""

# 4. 容器內 DNS 測試
echo "4. 📦 容器內 DNS 測試"
echo "---------------------"

# 測試基本 DNS
echo "🧪 測試 1: 預設 DNS 設定"
docker run --rm alpine sh -c "cat /etc/resolv.conf && nslookup google.com" 2>&1 | head -10

echo ""
echo "🧪 測試 2: 使用 Google DNS"
docker run --rm --dns 8.8.8.8 --dns 8.8.4.4 alpine sh -c "cat /etc/resolv.conf && nslookup deb.debian.org" 2>&1 | head -10

echo ""
echo "🧪 測試 3: 使用 Cloudflare DNS"
docker run --rm --dns 1.1.1.1 --dns 1.0.0.1 alpine sh -c "nslookup deb.debian.org" 2>&1 | head -10

echo ""
echo "🧪 測試 4: 使用中華電信 DNS (台灣)"
docker run --rm --dns 168.95.1.1 --dns 168.95.192.1 alpine sh -c "nslookup deb.debian.org" 2>&1 | head -10

echo ""
echo "🧪 測試 5: 使用 host 網路模式"
docker run --rm --network host alpine sh -c "cat /etc/resolv.conf && nslookup deb.debian.org" 2>&1 | head -10

# 5. iptables 和防火牆檢查
echo ""
echo "5. 🔥 防火牆和 iptables 規則"
echo "-----------------------------"
echo "🛡️ iptables FORWARD 鏈規則:"
sudo iptables -L FORWARD -n -v | grep -E "DOCKER|policy" | head -5 || echo "需要 sudo 權限"

echo ""
echo "🛡️ Docker 相關的 iptables 規則:"
sudo iptables -L -n | grep -c DOCKER || echo "0"
echo ""

# 6. 系統代理檢查
echo "6. 🔐 系統代理設定"
echo "------------------"
env | grep -i proxy || echo "沒有設定代理"
echo ""

# 7. NetworkManager 檢查
echo "7. 📡 NetworkManager 狀態"
echo "-------------------------"
if systemctl is-active NetworkManager >/dev/null 2>&1; then
    echo -e "${GREEN}✅ NetworkManager 運行中${NC}"
    nmcli device status 2>/dev/null | head -5 || echo "無法取得裝置狀態"
else
    echo -e "${YELLOW}⚠️  NetworkManager 未運行${NC}"
fi
echo ""

# 8. 建議的解決方案
echo "8. 💡 診斷結果與建議"
echo "--------------------"

# 檢查是否可以解析
if docker run --rm alpine nslookup deb.debian.org >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker 容器可以解析 DNS${NC}"
else
    echo -e "${RED}❌ Docker 容器無法解析 DNS${NC}"
    echo ""
    echo "🔧 建議的解決方案:"
    echo ""
    echo "方案 1: 修改 Docker daemon 設定"
    echo "sudo tee /etc/docker/daemon.json << EOF"
    echo "{"
    echo '  "dns": ["8.8.8.8", "8.8.4.4", "168.95.1.1"],'
    echo '  "dns-opts": ["ndots:0"],'
    echo '  "bip": "172.26.0.1/16"'
    echo "}"
    echo "EOF"
    echo "sudo systemctl restart docker"
    echo ""
    echo "方案 2: 使用 host 網路模式構建"
    echo "docker build --network=host -t your-app ."
    echo ""
    echo "方案 3: 在 Dockerfile 中設定 DNS"
    echo 'RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \'
    echo '    echo "nameserver 1.1.1.1" >> /etc/resolv.conf && \'
    echo '    apt-get update'
    echo ""
    echo "方案 4: 檢查防火牆設定"
    echo "sudo iptables -P FORWARD ACCEPT"
    echo ""
fi

# 9. 快速測試
echo ""
echo "9. 🚀 快速修復測試"
echo "------------------"
echo "創建測試 Dockerfile..."
cat > /tmp/test-dns.dockerfile << 'EOF'
FROM debian:bookworm-slim
RUN echo "=== DNS 測試 ===" && \
    echo "1. 原始 resolv.conf:" && \
    cat /etc/resolv.conf && \
    echo "2. 設定 Google DNS..." && \
    echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf && \
    echo "3. 新的 resolv.conf:" && \
    cat /etc/resolv.conf && \
    echo "4. 測試 DNS 解析..." && \
    apt-get update && \
    echo "=== 成功! ==="
EOF

echo "測試不同的構建方式..."
echo ""

# 測試標準構建
echo "📦 測試 1: 標準構建"
if timeout 30 docker build -f /tmp/test-dns.dockerfile -t test:dns1 . >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 標準構建成功${NC}"
else
    echo -e "${RED}❌ 標準構建失敗${NC}"
fi

# 測試 host 網路構建
echo "📦 測試 2: Host 網路構建"  
if timeout 30 docker build --network=host -f /tmp/test-dns.dockerfile -t test:dns2 . >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Host 網路構建成功${NC}"
else
    echo -e "${RED}❌ Host 網路構建失敗${NC}"
fi

echo ""
echo "診斷完成！"
echo "=========="