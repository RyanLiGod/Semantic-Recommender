# Semantic-Recommender-splited

基于语义的专家推荐系统。使用Annoy近似最近邻搜索推荐出最匹配的论文、专利、项目。同时使用以上数据按正态分布评分推荐出最匹配的专家。
索引根据属性进行切分，因此不需要特征文件进行筛选。但是更好的解决方案是MA-NSW: https://github.com/RyanLiGod/MA-NSW

## 如何运行

词向量训练和Annoy索引构建

```bash
python job.py

```

运行推荐服务器

```bash
python server.py

```

## 语义推荐步骤

1. word2vec词向量并构建论文等文档向量
2. Annoy索引构建
3. 准备特征文件实现推荐时筛选（可改为使用不需要特征文件且支持多属性查询的MA-NSW: https://github.com/RyanLiGod/MA-NSW）
4. 将目标查询短句分词并生成其句向量
5. 使用近似最近邻算法HNSW查询出最接近目标向量的论文、专利、项目
6. 使用以上数据按正态分布评分推荐出最匹配的专家
