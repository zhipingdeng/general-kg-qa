#!/bin/bash
# Clone general-kg-qa template to a new domain project
# Usage: ./clone_project.sh <project-name> <domain-title> <mysql-port> <neo4j-http> <neo4j-bolt> <milvus-port> <backend-port> <frontend-port>

set -e

PROJECT_NAME=$1
DOMAIN_TITLE=$2
MYSQL_PORT=$3
NEO4J_HTTP=$4
NEO4J_BOLT=$5
MILVUS_PORT=$6
BACKEND_PORT=$7
FRONTEND_PORT=$8
TEMPLATE="/mnt/e/hermes_code_workspace/general-kg-qa"
TARGET="/mnt/e/hermes_code_workspace/${PROJECT_NAME}"

if [ -z "$FRONTEND_PORT" ]; then
    echo "Usage: ./clone_project.sh <project-name> <domain-title> <mysql-port> <neo4j-http> <neo4j-bolt> <milvus-port> <backend-port> <frontend-port>"
    exit 1
fi

echo "==> Cloning ${PROJECT_NAME}..."

# Copy project
cp -r "$TEMPLATE" "$TARGET"
cd "$TARGET"

# Remove git history and old data
rm -rf .git data/* backend/scripts/eval_results.json

# Update docker-compose.yml
sed -i "s/container_name: neo4j-kgqa/container_name: neo4j-${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/container_name: mysql-kgqa/container_name: mysql-${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/container_name: etcd-kgqa/container_name: etcd-${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/container_name: minio-kgqa/container_name: minio-${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/container_name: milvus-kgqa/container_name: milvus-${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/container_name: backend-kgqa/container_name: backend-${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/container_name: frontend-kgqa/container_name: frontend-${PROJECT_NAME}/g" docker-compose.yml

# Update ports
sed -i "s/\"3307:3306\"/\"${MYSQL_PORT}:3306\"/g" docker-compose.yml
sed -i "s/\"7474:7474\"/\"${NEO4J_HTTP}:7474\"/g" docker-compose.yml
sed -i "s/\"7687:7687\"/\"${NEO4J_BOLT}:7687\"/g" docker-compose.yml
sed -i "s/\"19530:19530\"/\"${MILVUS_PORT}:19530\"/g" docker-compose.yml
sed -i "s/\"9091:9091\"/\"9091:9091\"/g" docker-compose.yml
sed -i "s/\"8000:8000\"/\"${BACKEND_PORT}:8000\"/g" docker-compose.yml
sed -i "s/\"80:80\"/\"${FRONTEND_PORT}:80\"/g" docker-compose.yml

# Update MySQL password for uniqueness
sed -i "s/NEO4J_PASSWORD: kgqa123/NEO4J_PASSWORD: ${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/NEO4J_AUTH: neo4j\/kgqa123/NEO4J_AUTH: neo4j\/${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/MYSQL_PASSWORD: kgqa123/MYSQL_PASSWORD: ${PROJECT_NAME}/g" docker-compose.yml
sed -i "s/NEO4J_PASSWORD=kgqa123/NEO4J_PASSWORD=${PROJECT_NAME}/g" docker-compose.yml

# Update .env
sed -i "s/MYSQL_PORT=3307/MYSQL_PORT=${MYSQL_PORT}/g" .env
sed -i "s/NEO4J_URI=bolt:\/\/localhost:7687/NEO4J_URI=bolt:\/\/localhost:${NEO4J_BOLT}/g" .env
sed -i "s/MILVUS_PORT=19530/MILVUS_PORT=${MILVUS_PORT}/g" .env
sed -i "s/NEO4J_PASSWORD=kgqa123/NEO4J_PASSWORD=${PROJECT_NAME}/g" .env
sed -i "s/MYSQL_PASSWORD=kgqa123/MYSQL_PASSWORD=${PROJECT_NAME}/g" .env
sed -i "s/API_PORT=8000/API_PORT=${BACKEND_PORT}/g" .env

# Update .env.example
sed -i "s/MYSQL_PORT=3307/MYSQL_PORT=${MYSQL_PORT}/g" .env.example
sed -i "s/NEO4J_URI=bolt:\/\/localhost:7687/NEO4J_URI=bolt:\/\/localhost:${NEO4J_BOLT}/g" .env.example
sed -i "s/MILVUS_PORT=19530/MILVUS_PORT=${MILVUS_PORT}/g" .env.example
sed -i "s/API_PORT=8000/API_PORT=${BACKEND_PORT}/g" .env.example

# Update frontend title
sed -i "s/通用百科知识问答/${DOMAIN_TITLE}/g" frontend/src/views/Login.vue
sed -i "s/通用百科知识问答/${DOMAIN_TITLE}/g" frontend/src/views/Home.vue
sed -i "s/通用百科知识问答/${DOMAIN_TITLE}/g" frontend/src/components/Header.vue
sed -i "s/知识问答/${DOMAIN_TITLE}/g" frontend/src/router/index.ts
sed -i "s/KG-QA/${PROJECT_NAME}/g" frontend/src/router/index.ts
sed -i "s/基于知识图谱的智能问答系统/基于知识图谱的${DOMAIN_TITLE}问答系统/g" frontend/src/views/Login.vue
sed -i "s/通用百科知识问答/${DOMAIN_TITLE}/g" frontend/index.html

# Update config.py default port
sed -i "s/mysql_port: int = 3307/mysql_port: int = ${MYSQL_PORT}/g" backend/app/config.py

# Update README
sed -i "s/通用百科知识图谱问答系统/${DOMAIN_TITLE}知识图谱问答系统/g" README.md
sed -i "s/General KG-QA/${PROJECT_NAME}/g" README.md
sed -i "s/general-kg-qa/${PROJECT_NAME}/g" README.md

# Init git
git init
git add -A
git commit -m "feat: initialize ${DOMAIN_TITLE} knowledge graph QA from template"

echo "==> Done! ${PROJECT_NAME} created at ${TARGET}"
echo "    MySQL: localhost:${MYSQL_PORT}"
echo "    Neo4j: localhost:${NEO4J_BOLT}"
echo "    Milvus: localhost:${MILVUS_PORT}"
echo "    Backend: localhost:${BACKEND_PORT}"
echo "    Frontend: localhost:${FRONTEND_PORT}"
