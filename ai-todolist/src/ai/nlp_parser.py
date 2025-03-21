import re
import datetime
import jieba
import jieba.posseg as pseg

class NLPTaskParser:
    """自然语言任务解析器"""
    
    def __init__(self):
        # 添加自定义词典
        self.time_keywords = {
            "今天": 0,
            "明天": 1,
            "后天": 2,
            "大后天": 3,
            "下周": 7,
            "下个月": 30,
        }
        
        self.category_keywords = {
            "工作": ["会议", "报告", "项目", "客户", "演讲", "提案", "工作", "办公", "文档", "邮件"],
            "学习": ["学习", "课程", "作业", "考试", "阅读", "书籍", "笔记", "研究", "论文", "复习"],
            "生活": ["购物", "买菜", "打扫", "健身", "约会", "聚餐", "吃饭", "休息", "电影", "旅行"],
            "其他": []
        }
        
        # 初始化自定义词典
        for word in self.time_keywords.keys():
            jieba.add_word(word)
        for category, keywords in self.category_keywords.items():
            for word in keywords:
                jieba.add_word(word)
    
    def parse(self, text):
        """解析任务文本
        
        Args:
            text: 用户输入的自然语言任务描述
            
        Returns:
            dict: 包含解析后的任务信息
                {
                    "text": 任务内容,
                    "category": 任务分类,
                    "due_date": 截止日期 (可选),
                    "due_time": 截止时间 (可选),
                    "priority": 优先级 (可选)
                }
        """
        result = {
            "text": text,
            "category": "工作",  # 默认分类
            "due_date": None,
            "due_time": None,
            "priority": "正常"
        }
        
        # 提取日期和时间
        result.update(self._extract_datetime(text))
        
        # 提取分类
        result["category"] = self._extract_category(text)
        
        # 提取优先级
        result["priority"] = self._extract_priority(text)
        
        # 清理任务内容 (去除已识别的时间、优先级等信息)
        result["text"] = self._clean_task_text(text, result)
        
        return result
    
    def _extract_datetime(self, text):
        """提取日期和时间信息"""
        result = {"due_date": None, "due_time": None}
        today = datetime.datetime.now().date()
        
        # 识别相对日期 (今天、明天、下周等)
        for keyword, days in self.time_keywords.items():
            if keyword in text:
                result["due_date"] = today + datetime.timedelta(days=days)
                break
                
        # 识别具体日期 (如MM月DD日)
        date_pattern = re.compile(r'(\d+)月(\d+)日')
        date_match = date_pattern.search(text)
        if date_match:
            month, day = int(date_match.group(1)), int(date_match.group(2))
            year = today.year
            # 如果月份已过，假设是明年的日期
            if month < today.month or (month == today.month and day < today.day):
                year += 1
            try:
                result["due_date"] = datetime.date(year, month, day)
            except ValueError:
                # 处理无效日期
                pass
        
        # 识别时间 (如3点、下午2:30等)
        time_pattern = re.compile(r'(上午|下午|早上|晚上)?(\d+)(?:[:：](\d+))?(?:点|时)')
        time_match = time_pattern.search(text)
        if time_match:
            period, hour, minute = time_match.groups()
            hour = int(hour)
            minute = int(minute) if minute else 0
            
            # 处理12小时制
            if period in ["下午", "晚上"] and hour < 12:
                hour += 12
            elif period in ["上午", "早上"] and hour == 12:
                hour = 0
                
            try:
                result["due_time"] = datetime.time(hour, minute)
            except ValueError:
                # 处理无效时间
                pass
        
        return result
    
    def _extract_category(self, text):
        """从文本中提取任务分类"""
        # 对文本分词
        words = jieba.lcut(text)
        
        # 统计每个分类的关键词出现次数
        category_scores = {"工作": 0, "学习": 0, "生活": 0, "其他": 0}
        
        for word in words:
            for category, keywords in self.category_keywords.items():
                if word in keywords:
                    category_scores[category] += 1
        
        # 选择得分最高的分类，如果都是0则返回"其他"
        max_score = 0
        selected_category = "其他"
        
        for category, score in category_scores.items():
            if score > max_score:
                max_score = score
                selected_category = category
        
        return selected_category
    
    def _extract_priority(self, text):
        """提取优先级信息"""
        high_priority = ["紧急", "重要", "优先", "尽快", "立即"]
        low_priority = ["不急", "低优先级", "有空", "闲时"]
        
        for word in high_priority:
            if word in text:
                return "高"
                
        for word in low_priority:
            if word in text:
                return "低"
                
        return "正常"
    
    def _clean_task_text(self, text, parsed_info):
        """清理任务文本，去除已识别的时间、优先级等信息"""
        # 这里简单实现，实际应用中可以更复杂
        clean_text = text
        
        # 替换日期相关词汇
        for keyword in self.time_keywords.keys():
            clean_text = clean_text.replace(keyword, "")
        
        # 替换时间模式
        time_pattern = re.compile(r'(上午|下午|早上|晚上)?(\d+)(?:[:：](\d+))?(?:点|时)')
        clean_text = time_pattern.sub("", clean_text)
        
        # 替换日期模式
        date_pattern = re.compile(r'(\d+)月(\d+)日')
        clean_text = date_pattern.sub("", clean_text)
        
        # 替换优先级词汇
        priority_words = ["紧急", "重要", "优先", "尽快", "立即", "不急", "低优先级", "有空", "闲时"]
        for word in priority_words:
            clean_text = clean_text.replace(word, "")
        
        # 去除多余空格并修剪
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text if clean_text else "未指定任务内容"