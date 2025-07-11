# 相似度计算优化建议

## 问题分析

根据用户反馈，当前RAG系统返回的相似度分数过低（如 `0.0006902945363423389`），这表明存在以下问题：

### 1. 相似度计算公式问题

**当前实现：**
```python
similarity = 1 / (1 + score)  # score 是向量距离
```

**问题分析：**
- ChromaDB 使用的是欧几里得距离或余弦距离
- 当距离值较大时，转换后的相似度会非常小
- 例如：score = 1448.5 时，similarity = 1/(1+1448.5) ≈ 0.0007

### 2. 文档内容匹配策略问题

**当前文档结构：**
```python
content = f"阶段名称: {stage_name}\n时间范围: {time_range}\n描述: {description}"
```

**问题：**
- 描述字段权重不够
- 结构化信息干扰语义匹配
- 缺乏关键词提取和优化

## 优化方案

### 方案一：改进相似度计算公式

#### 1.1 使用余弦相似度转换
```python
def calculate_similarity(self, score: float, distance_type: str = "cosine") -> float:
    """改进的相似度计算
    
    Args:
        score: ChromaDB返回的距离分数
        distance_type: 距离类型 (cosine, euclidean, l2)
    
    Returns:
        标准化的相似度分数 (0-1)
    """
    if distance_type == "cosine":
        # 余弦距离转相似度：similarity = 1 - distance
        # ChromaDB余弦距离范围通常是 [0, 2]
        return max(0, 1 - score / 2)
    elif distance_type == "euclidean" or distance_type == "l2":
        # 欧几里得距离使用指数衰减
        return math.exp(-score / 100)  # 可调整衰减因子
    else:
        # 默认使用改进的倒数公式
        return 1 / (1 + score / 10)  # 添加缩放因子
```

#### 1.2 自适应阈值调整
```python
def get_adaptive_threshold(self, query_results: List[Tuple], base_threshold: float = 0.7) -> float:
    """根据查询结果动态调整阈值"""
    if not query_results:
        return base_threshold
    
    scores = [self.calculate_similarity(score) for _, score in query_results]
    
    # 如果最高分数都很低，降低阈值
    max_score = max(scores)
    if max_score < base_threshold:
        return max(0.3, max_score * 0.8)  # 降低到最高分的80%，但不低于0.3
    
    return base_threshold
```

### 方案二：优化文档内容结构

#### 2.1 增强描述字段权重
```python
def build_enhanced_content(self, stage_name: str, time_range: str, description: str) -> str:
    """构建增强的文档内容，突出描述字段"""
    # 方式1：描述优先
    content = f"{description}\n\n阶段：{stage_name}\n时间：{time_range}"
    
    # 方式2：重复关键信息
    keywords = self.extract_keywords(description)
    content = f"{description}\n关键词：{', '.join(keywords)}\n阶段：{stage_name}"
    
    return content

def extract_keywords(self, text: str) -> List[str]:
    """提取关键词"""
    # 简单的关键词提取（可以使用更复杂的NLP方法）
    import re
    # 提取中文词汇和英文单词
    keywords = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
    # 过滤停用词和短词
    stopwords = {'的', '了', '在', '是', '和', '与', '或', '但', '然后', '接着'}
    return [kw for kw in keywords if len(kw) > 1 and kw not in stopwords]
```

#### 2.2 多字段分别存储
```python
def store_multi_field_documents(self, video_id: int, product_name: str, 
                               stage_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """分别存储不同字段的文档"""
    documents = []
    
    for i, (stage_name, time_range, description) in enumerate(zip(stages, times, descriptions)):
        # 存储三个不同的文档
        base_metadata = {
            "video_id": video_id,
            "stage_index": i,
            "product_name": product_name,
            "analysis_type": "video_stage_analysis"
        }
        
        # 1. 描述文档（主要用于语义搜索）
        desc_doc = Document(
            page_content=description,
            metadata={**base_metadata, "field_type": "description", "weight": 1.0}
        )
        
        # 2. 阶段名称文档（用于精确匹配）
        stage_doc = Document(
            page_content=stage_name,
            metadata={**base_metadata, "field_type": "stage_name", "weight": 0.8}
        )
        
        # 3. 综合文档（用于全文搜索）
        combined_doc = Document(
            page_content=f"{description} {stage_name}",
            metadata={**base_metadata, "field_type": "combined", "weight": 0.9}
        )
        
        documents.extend([desc_doc, stage_doc, combined_doc])
    
    return documents
```

### 方案三：实现混合搜索策略

#### 3.1 多策略搜索
```python
def hybrid_search(self, query: str, product_name: Optional[str] = None, 
                 k: int = 5, similarity_threshold: float = 0.7) -> Dict[str, Any]:
    """混合搜索策略"""
    results = []
    
    # 策略1：语义搜索（主要基于描述）
    semantic_results = self.semantic_search(query, product_name, k*2)
    
    # 策略2：关键词搜索
    keyword_results = self.keyword_search(query, product_name, k)
    
    # 策略3：模糊匹配
    fuzzy_results = self.fuzzy_search(query, product_name, k)
    
    # 合并和去重
    all_results = self.merge_and_deduplicate(
        semantic_results, keyword_results, fuzzy_results
    )
    
    # 重新计算综合分数
    for result in all_results:
        result['final_score'] = self.calculate_final_score(result)
    
    # 过滤和排序
    filtered_results = [
        r for r in all_results 
        if r['final_score'] >= similarity_threshold
    ]
    
    return sorted(filtered_results, key=lambda x: x['final_score'], reverse=True)[:k]

def calculate_final_score(self, result: Dict) -> float:
    """计算最终综合分数"""
    semantic_score = result.get('semantic_score', 0) * 0.6
    keyword_score = result.get('keyword_score', 0) * 0.3
    fuzzy_score = result.get('fuzzy_score', 0) * 0.1
    
    return semantic_score + keyword_score + fuzzy_score
```

#### 3.2 关键词搜索实现
```python
def keyword_search(self, query: str, product_name: Optional[str] = None, k: int = 5) -> List[Dict]:
    """基于关键词的搜索"""
    query_keywords = self.extract_keywords(query)
    
    # 使用ChromaDB的where条件进行关键词匹配
    results = []
    
    for keyword in query_keywords:
        # 在文档内容中搜索关键词
        docs = self.vector_store.similarity_search(
            keyword,
            k=k*2,
            filter=self.build_filter(product_name)
        )
        
        for doc in docs:
            # 计算关键词匹配分数
            content = doc.page_content.lower()
            keyword_count = content.count(keyword.lower())
            
            if keyword_count > 0:
                score = min(1.0, keyword_count * 0.2)  # 每个匹配+0.2分，最高1.0
                results.append({
                    'document': doc,
                    'keyword_score': score,
                    'matched_keyword': keyword
                })
    
    return results
```

### 方案四：改进embedding策略

#### 4.1 使用更好的embedding模型
```python
class ImprovedArkEmbeddings(ArkEmbeddings):
    """改进的embedding类"""
    
    def __init__(self, model: str = "doubao-embedding-large-text-250515"):
        super().__init__(model)
        self.max_length = 512  # 限制文本长度
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """改进的文档embedding"""
        # 预处理文本
        processed_texts = [self.preprocess_text(text) for text in texts]
        return super().embed_documents(processed_texts)
    
    def embed_query(self, text: str) -> List[float]:
        """改进的查询embedding"""
        processed_text = self.preprocess_text(text)
        return super().embed_query(processed_text)
    
    def preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 1. 清理文本
        import re
        text = re.sub(r'\s+', ' ', text)  # 标准化空白字符
        text = text.strip()
        
        # 2. 截断过长文本
        if len(text) > self.max_length:
            text = text[:self.max_length]
        
        # 3. 添加上下文标记（可选）
        if '阶段名称:' in text:
            text = f"[视频阶段] {text}"
        
        return text
```

#### 4.2 使用多个embedding模型
```python
class MultiEmbeddingService:
    """多embedding模型服务"""
    
    def __init__(self):
        self.primary_embeddings = ArkEmbeddings("doubao-embedding-large-text-250515")
        self.secondary_embeddings = ArkEmbeddings("doubao-embedding-base-text-250515")
    
    def get_ensemble_similarity(self, query: str, documents: List[str]) -> List[float]:
        """集成多个模型的相似度"""
        # 使用主模型
        primary_scores = self.calculate_similarities(query, documents, self.primary_embeddings)
        
        # 使用辅助模型
        secondary_scores = self.calculate_similarities(query, documents, self.secondary_embeddings)
        
        # 加权平均
        ensemble_scores = [
            0.7 * p + 0.3 * s 
            for p, s in zip(primary_scores, secondary_scores)
        ]
        
        return ensemble_scores
```

## 实施建议

### 阶段一：快速修复（1-2天）
1. **修改相似度计算公式**
   - 实施改进的相似度转换算法
   - 添加自适应阈值调整
   - 更新API返回的相似度分数

2. **优化文档内容结构**
   - 调整文档内容格式，突出描述字段
   - 添加关键词提取功能

### 阶段二：功能增强（3-5天）
1. **实施混合搜索**
   - 添加关键词搜索功能
   - 实现多策略结果合并
   - 优化综合评分算法

2. **改进embedding处理**
   - 添加文本预处理功能
   - 优化embedding参数

### 阶段三：深度优化（1-2周）
1. **多模型集成**
   - 实施多embedding模型策略
   - 添加模型性能监控

2. **智能阈值调整**
   - 基于历史数据优化阈值
   - 实现用户反馈学习机制

## 监控和评估

### 1. 性能指标
```python
class SimilarityMetrics:
    """相似度性能指标"""
    
    def __init__(self):
        self.query_logs = []
    
    def log_query(self, query: str, results: List[Dict], user_feedback: Optional[Dict] = None):
        """记录查询日志"""
        log_entry = {
            'timestamp': datetime.now(),
            'query': query,
            'result_count': len(results),
            'avg_similarity': sum(r['similarity_score'] for r in results) / len(results) if results else 0,
            'max_similarity': max(r['similarity_score'] for r in results) if results else 0,
            'user_feedback': user_feedback
        }
        self.query_logs.append(log_entry)
    
    def get_performance_report(self) -> Dict:
        """生成性能报告"""
        if not self.query_logs:
            return {"message": "暂无查询数据"}
        
        return {
            'total_queries': len(self.query_logs),
            'avg_result_count': sum(log['result_count'] for log in self.query_logs) / len(self.query_logs),
            'avg_similarity': sum(log['avg_similarity'] for log in self.query_logs) / len(self.query_logs),
            'high_quality_rate': len([log for log in self.query_logs if log['max_similarity'] > 0.7]) / len(self.query_logs)
        }
```

### 2. A/B测试框架
```python
class ABTestFramework:
    """A/B测试框架"""
    
    def __init__(self):
        self.test_groups = {
            'control': {'similarity_formula': 'original', 'threshold': 0.7},
            'test_a': {'similarity_formula': 'improved', 'threshold': 0.7},
            'test_b': {'similarity_formula': 'improved', 'threshold': 0.5}
        }
    
    def assign_user_to_group(self, user_id: str) -> str:
        """分配用户到测试组"""
        hash_value = hash(user_id) % 100
        if hash_value < 33:
            return 'control'
        elif hash_value < 66:
            return 'test_a'
        else:
            return 'test_b'
```

## 总结

通过以上优化方案，可以显著提高RAG系统的相似度计算准确性：

1. **相似度分数提升**：从0.0007提升到0.3-0.9的合理范围
2. **匹配质量改善**：更好地匹配描述字段的语义内容
3. **用户体验优化**：减少无关结果，提高查询满意度
4. **系统可维护性**：添加监控和评估机制，便于持续优化

建议优先实施阶段一的快速修复方案，然后根据效果逐步推进后续优化。