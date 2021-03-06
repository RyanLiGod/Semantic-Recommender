# Semantic-Recommender

基于语义的专家推荐系统的HNSW版本。使用HNSW近似最近邻搜索推荐出最匹配的论文、专利、项目。同时使用以上数据按正态分布评分推荐出最匹配的专家。

查看演示：https://www.itech4u.cn/homeSemanticSearch

切换分支有近似最近邻算法Annoy、远程方法调用RMI、后端框架flask、索引切分等其他方式的实现。

## 如何运行

词向量训练和HNSW索引构建，需要事先准备语料

```bash
python job.py
```

运行推荐服务器

```bash
python server.py
```

## 语义推荐步骤

1. word2vec词向量并构建论文等文档向量
2. HNSW索引构建
3. 准备特征文件实现推荐时筛选（可改为使用不需要特征文件且支持多属性查询的MA-NSW: https://github.com/RyanLiGod/MA-NSW）
4. 将目标查询短句分词并生成其句向量
5. 使用近似最近邻算法HNSW查询出最接近目标向量的论文、专利、项目
6. 使用以上数据按正态分布评分推荐出最匹配的专家
