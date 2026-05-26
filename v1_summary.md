# V1 Summary

## 当前能力

- 支持读取汽车用户手册 PDF
- 支持按页抽取文本
- 支持 fixed-size chunk
- 支持本地 embedding
- 支持 Chroma 向量库
- 支持 Ollama 本地大模型回答
- 支持 citation 返回 page、chunk_id、quote、score、distance
- 支持 debug retrieval
- 支持日志文件输出

## 当前限制

- chunk 仍然偏粗，接近一页一个 chunk
- citation quote 有改善但仍不稳定
- 纯 dense retrieval 排序不稳定
- 尚未识别章节结构
- 尚未识别警告 / 注意 / 说明
- 尚未保护操作步骤块
- 尚未做 hybrid search / rerank
- 尚未建立系统化评估集

## 下一阶段

V2：汽车手册结构化解析与 chunk 策略优化。