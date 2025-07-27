#!/bin/bash

echo "🔍 診斷 Docker 網路問題"
echo "====================="

# 1. 檢查 Docker 版本
echo "1. Docker 版本："
docker --version
docker-compose --version

# 2. 檢查 BuildKit 狀態
echo -e "\n2. BuildKit 狀態："
echo "DOCKER_BUILDKIT=$DOCKER_BUILDKIT"

# 3. 測試主機網路
echo -e "\n3. 主機網路測試："
ping -c 1 8.8.8.8 &>/dev/null && echo "✅ 可以 ping 8.8.8.8" || echo "❌ 無法 ping 8.8.8.8"
curl -s https://pypi.org &>/dev/null && echo "✅ 可以訪問 pypi.org" || echo "❌ 無法訪問 pypi.org"

# 4. 測試 Docker 網路
echo -e "\n4. Docker 容器網路測試："
docker run --rm alpine ping -c 1 8.8.8.8 &>/dev/null && echo "✅ 容器可以 ping" || echo "❌ 容器無法 ping"
docker run --rm --network host alpine ping -c 1 8.8.8.8 &>/dev/null && echo "✅ Host 模式可以 ping" || echo "❌ Host 模式無法 ping"

# 5. 測試 DNS
echo -e "\n5. DNS 測試："
docker run --rm alpine nslookup google.com 2>&1 | grep -q "Address" && echo "✅ 容器 DNS 正常" || echo "❌ 容器 DNS 異常"
docker run --rm --network host alpine nslookup google.com 2>&1 | grep -q "Address" && echo "✅ Host 模式 DNS 正常" || echo "❌ Host 模式 DNS 異常"

# 6. 檢查代理設定
echo -e "\n6. 代理設定："
echo "HTTP_PROXY=$HTTP_PROXY"
echo "HTTPS_PROXY=$HTTPS_PROXY"
echo "NO_PROXY=$NO_PROXY"

# 7. 建議
echo -e "\n💡 建議："
echo "1. 嘗試禁用 BuildKit: export DOCKER_BUILDKIT=0"
echo "2. 如果在公司網路，設定代理"
echo "3. 使用離線安裝方式"