import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ResponseEvaluator:
    """
    响应评估器类，用于评估模型响应的质量
    """
    
    def __init__(self):
        """
        初始化评估器
        """
        pass

    def evaluate(self, response: str) -> Dict[str, Any]:
        """
        评估模型响应的质量
        
        Args:
            response: 模型的响应文本
            
        Returns:
            包含评估结果的字典
        """
        try:
            # 基本评估指标
            evaluation = {
                "length": len(response),
                "word_count": len(response.split()),
                "has_content": bool(response.strip()),
                "quality_score": self._calculate_quality_score(response)
            }
            
            return evaluation
        except Exception as e:
            logger.error(f"Failed to evaluate response: {str(e)}")
            return {
                "error": str(e),
                "length": 0,
                "word_count": 0,
                "has_content": False,
                "quality_score": 0
            }
    
    def _calculate_quality_score(self, response: str) -> float:
        """
        计算响应质量分数
        
        Args:
            response: 模型的响应文本
            
        Returns:
            质量分数（0-1之间的浮点数）
        """
        try:
            # 这里可以添加更复杂的质量评估逻辑
            # 目前使用一个简单的评分机制
            
            score = 0.0
            text = response.strip()
            
            # 检查是否有内容
            if not text:
                return 0.0
            
            # 基于长度的得分（假设合理长度在50-1000字之间）
            length = len(text)
            if 50 <= length <= 1000:
                score += 0.3
            elif length > 1000:
                score += 0.2
            else:
                score += 0.1
            
            # 检查是否包含完整句子
            if text[-1] in '.!?。！？':
                score += 0.2
            
            # 检查段落结构
            paragraphs = text.split('\n\n')
            if len(paragraphs) > 1:
                score += 0.2
            
            # 检查特殊字符比例
            special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
            char_ratio = special_chars / length
            if char_ratio <= 0.2:  # 特殊字符比例不超过20%
                score += 0.2
            
            # 检查是否包含代码块（如果有```标记）
            if '```' in text:
                score += 0.1
            
            return min(1.0, score)  # 确保分数不超过1.0
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {str(e)}")
            return 0.0 