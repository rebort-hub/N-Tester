"""
Crontab工具
提供Crontab表达式生成、解析、验证等功能
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List


class CrontabTools:
    """Crontab工具类"""
    
    # Crontab字段说明
    FIELD_NAMES = ['分钟', '小时', '日', '月', '星期']
    FIELD_RANGES = {
        'minute': (0, 59),
        'hour': (0, 23),
        'day': (1, 31),
        'month': (1, 12),
        'weekday': (0, 7)  # 0和7都表示星期日
    }
    
    # 月份名称
    MONTH_NAMES = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # 星期名称
    WEEKDAY_NAMES = {
        'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6
    }
    
    @staticmethod
    def generate_expression(minute: str = '*', hour: str = '*', day: str = '*', 
                          month: str = '*', weekday: str = '*') -> Dict[str, Any]:
        """
        生成Crontab表达式
        
        Args:
            minute: 分钟 (0-59)
            hour: 小时 (0-23)
            day: 日 (1-31)
            month: 月 (1-12)
            weekday: 星期 (0-7, 0和7都表示星期日)
            
        Returns:
            Crontab表达式
        """
        try:
            # 验证各个字段
            fields = [minute, hour, day, month, weekday]
            field_names = ['minute', 'hour', 'day', 'month', 'weekday']
            
            for i, (field, field_name) in enumerate(zip(fields, field_names)):
                if not CrontabTools._validate_field(field, field_name):
                    return {'error': f'{CrontabTools.FIELD_NAMES[i]}字段格式错误: {field}'}
            
            expression = f'{minute} {hour} {day} {month} {weekday}'
            
            # 生成描述
            description = CrontabTools._generate_description(minute, hour, day, month, weekday)
            
            # 生成下次执行时间示例
            next_runs = CrontabTools.get_next_runs(expression, count=5)
            
            return {
                'success': True,
                'expression': expression,
                'description': description,
                'fields': {
                    'minute': minute,
                    'hour': hour,
                    'day': day,
                    'month': month,
                    'weekday': weekday
                },
                'next_runs': next_runs.get('next_runs', []) if isinstance(next_runs, dict) else []
            }
        except Exception as e:
            return {'error': f'Crontab表达式生成失败: {str(e)}'}
    
    @staticmethod
    def parse_expression(expression: str) -> Dict[str, Any]:
        """
        解析Crontab表达式
        
        Args:
            expression: Crontab表达式
            
        Returns:
            解析结果
        """
        try:
            # 清理表达式
            expression = expression.strip()
            parts = expression.split()
            
            if len(parts) != 5:
                return {'error': 'Crontab表达式必须包含5个字段（分 时 日 月 周）'}
            
            minute, hour, day, month, weekday = parts
            
            # 验证表达式
            validation = CrontabTools.validate_expression(expression)
            if not validation.get('success'):
                return validation
            
            # 解析各个字段
            parsed_fields = {}
            field_names = ['minute', 'hour', 'day', 'month', 'weekday']
            field_values = [minute, hour, day, month, weekday]
            
            for field_name, field_value in zip(field_names, field_values):
                parsed_fields[field_name] = CrontabTools._parse_field(field_value, field_name)
            
            # 生成描述
            description = CrontabTools._generate_description(minute, hour, day, month, weekday)
            
            # 生成执行时间示例
            next_runs = CrontabTools.get_next_runs(expression, count=10)
            
            return {
                'success': True,
                'expression': expression,
                'description': description,
                'fields': {
                    'minute': minute,
                    'hour': hour,
                    'day': day,
                    'month': month,
                    'weekday': weekday
                },
                'parsed_fields': parsed_fields,
                'next_runs': next_runs.get('next_runs', []) if isinstance(next_runs, dict) else []
            }
        except Exception as e:
            return {'error': f'Crontab表达式解析失败: {str(e)}'}
    
    @staticmethod
    def get_next_runs(expression: str, count: int = 10, start_time: str = None) -> Dict[str, Any]:
        """
        获取下次执行时间
        
        Args:
            expression: Crontab表达式
            count: 获取数量
            start_time: 开始时间（格式：YYYY-MM-DD HH:MM:SS）
            
        Returns:
            下次执行时间列表
        """
        try:
            # 验证表达式
            validation = CrontabTools.validate_expression(expression)
            if not validation.get('success'):
                return validation
            
            # 解析开始时间
            if start_time:
                try:
                    current_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return {'error': '开始时间格式错误，应为：YYYY-MM-DD HH:MM:SS'}
            else:
                current_time = datetime.now()
            
            # 解析表达式
            parts = expression.strip().split()
            minute, hour, day, month, weekday = parts
            
            next_runs = []
            check_time = current_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
            
            # 最多检查未来一年
            max_checks = 525600  # 一年的分钟数
            checks = 0
            
            while len(next_runs) < count and checks < max_checks:
                if CrontabTools._matches_cron(check_time, minute, hour, day, month, weekday):
                    next_runs.append({
                        'datetime': check_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': int(check_time.timestamp()),
                        'weekday': check_time.strftime('%A'),
                        'relative': CrontabTools._get_relative_time(current_time, check_time)
                    })
                
                check_time += timedelta(minutes=1)
                checks += 1
            
            return {
                'success': True,
                'expression': expression,
                'start_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'count': len(next_runs),
                'next_runs': next_runs
            }
        except Exception as e:
            return {'error': f'获取执行时间失败: {str(e)}'}
    
    @staticmethod
    def validate_expression(expression: str) -> Dict[str, Any]:
        """
        验证Crontab表达式
        
        Args:
            expression: Crontab表达式
            
        Returns:
            验证结果
        """
        try:
            # 清理表达式
            expression = expression.strip()
            
            if not expression:
                return {'success': False, 'error': 'Crontab表达式不能为空'}
            
            parts = expression.split()
            
            if len(parts) != 5:
                return {
                    'success': False,
                    'error': f'Crontab表达式必须包含5个字段，当前有{len(parts)}个字段',
                    'expected_format': '分钟 小时 日 月 星期'
                }
            
            minute, hour, day, month, weekday = parts
            field_names = ['minute', 'hour', 'day', 'month', 'weekday']
            field_values = [minute, hour, day, month, weekday]
            
            errors = []
            
            # 验证各个字段
            for i, (field_value, field_name) in enumerate(zip(field_values, field_names)):
                if not CrontabTools._validate_field(field_value, field_name):
                    errors.append(f'{CrontabTools.FIELD_NAMES[i]}字段格式错误: {field_value}')
            
            if errors:
                return {
                    'success': False,
                    'error': '表达式格式错误',
                    'errors': errors,
                    'expression': expression
                }
            
            # 生成描述以进一步验证
            description = CrontabTools._generate_description(minute, hour, day, month, weekday)
            
            return {
                'success': True,
                'valid': True,
                'expression': expression,
                'description': description,
                'message': 'Crontab表达式格式正确'
            }
        except Exception as e:
            return {'success': False, 'error': f'Crontab表达式验证失败: {str(e)}'}
    
    @staticmethod
    def _validate_field(field_value: str, field_name: str) -> bool:
        """验证单个字段"""
        try:
            if field_value == '*':
                return True
            
            # 获取字段范围
            min_val, max_val = CrontabTools.FIELD_RANGES[field_name]
            
            # 处理逗号分隔的值
            if ',' in field_value:
                values = field_value.split(',')
                for value in values:
                    if not CrontabTools._validate_single_value(value.strip(), min_val, max_val, field_name):
                        return False
                return True
            
            return CrontabTools._validate_single_value(field_value, min_val, max_val, field_name)
        except:
            return False
    
    @staticmethod
    def _validate_single_value(value: str, min_val: int, max_val: int, field_name: str) -> bool:
        """验证单个值"""
        try:
            # 处理范围 (例如: 1-5)
            if '-' in value:
                if value.count('-') != 1:
                    return False
                start, end = value.split('-')
                start_num = int(start)
                end_num = int(end)
                return (min_val <= start_num <= max_val and 
                       min_val <= end_num <= max_val and 
                       start_num <= end_num)
            
            # 处理步长 (例如: */5, 1-10/2)
            if '/' in value:
                if value.count('/') != 1:
                    return False
                base, step = value.split('/')
                step_num = int(step)
                if step_num <= 0:
                    return False
                
                if base == '*':
                    return True
                elif '-' in base:
                    return CrontabTools._validate_single_value(base, min_val, max_val, field_name)
                else:
                    base_num = int(base)
                    return min_val <= base_num <= max_val
            
            # 处理名称（月份和星期）
            if field_name == 'month' and value.lower() in CrontabTools.MONTH_NAMES:
                return True
            if field_name == 'weekday' and value.lower() in CrontabTools.WEEKDAY_NAMES:
                return True
            
            # 处理数字
            num = int(value)
            return min_val <= num <= max_val
        except:
            return False
    
    @staticmethod
    def _parse_field(field_value: str, field_name: str) -> Dict[str, Any]:
        """解析字段值"""
        if field_value == '*':
            return {'type': 'any', 'description': '任意值'}
        
        min_val, max_val = CrontabTools.FIELD_RANGES[field_name]
        
        # 处理逗号分隔
        if ',' in field_value:
            values = [v.strip() for v in field_value.split(',')]
            return {
                'type': 'list',
                'values': values,
                'description': f'指定值: {", ".join(values)}'
            }
        
        # 处理范围
        if '-' in field_value and '/' not in field_value:
            start, end = field_value.split('-')
            return {
                'type': 'range',
                'start': int(start),
                'end': int(end),
                'description': f'范围: {start}-{end}'
            }
        
        # 处理步长
        if '/' in field_value:
            base, step = field_value.split('/')
            if base == '*':
                return {
                    'type': 'step',
                    'base': 'any',
                    'step': int(step),
                    'description': f'每{step}个单位'
                }
            else:
                return {
                    'type': 'step',
                    'base': base,
                    'step': int(step),
                    'description': f'从{base}开始，每{step}个单位'
                }
        
        # 单个值
        return {
            'type': 'value',
            'value': field_value,
            'description': f'指定值: {field_value}'
        }
    
    @staticmethod
    def _generate_description(minute: str, hour: str, day: str, month: str, weekday: str) -> str:
        """生成Crontab表达式的中文描述"""
        desc_parts = []
        
        # 月份描述
        if month != '*':
            if ',' in month:
                desc_parts.append(f"在{month.replace(',', '、')}月")
            elif '-' in month:
                start, end = month.split('-')
                desc_parts.append(f"在{start}月到{end}月")
            else:
                desc_parts.append(f"在{month}月")
        
        # 日期和星期描述
        if day != '*' and weekday != '*':
            desc_parts.append(f"每月{day}日或每周{CrontabTools._weekday_desc(weekday)}")
        elif day != '*':
            desc_parts.append(f"每月{day}日")
        elif weekday != '*':
            desc_parts.append(f"每周{CrontabTools._weekday_desc(weekday)}")
        
        # 时间描述
        if hour == '*' and minute == '*':
            desc_parts.append("每分钟")
        elif hour == '*':
            if minute == '0':
                desc_parts.append("每小时整点")
            else:
                desc_parts.append(f"每小时的第{minute}分钟")
        elif minute == '*':
            desc_parts.append(f"在{hour}点的每分钟")
        else:
            desc_parts.append(f"在{hour}:{minute.zfill(2)}")
        
        if not desc_parts:
            return "每分钟执行"
        
        return "".join(desc_parts) + "执行"
    
    @staticmethod
    def _weekday_desc(weekday: str) -> str:
        """生成星期描述"""
        weekday_names = ['日', '一', '二', '三', '四', '五', '六']
        
        if weekday == '*':
            return "每天"
        elif ',' in weekday:
            days = []
            for day in weekday.split(','):
                day_num = int(day) % 7
                days.append(f"周{weekday_names[day_num]}")
            return "、".join(days)
        elif '-' in weekday:
            start, end = weekday.split('-')
            start_num = int(start) % 7
            end_num = int(end) % 7
            return f"周{weekday_names[start_num]}到周{weekday_names[end_num]}"
        else:
            day_num = int(weekday) % 7
            return f"周{weekday_names[day_num]}"
    
    @staticmethod
    def _matches_cron(dt: datetime, minute: str, hour: str, day: str, month: str, weekday: str) -> bool:
        """检查时间是否匹配Cron表达式"""
        return (CrontabTools._matches_field(dt.minute, minute, 'minute') and
                CrontabTools._matches_field(dt.hour, hour, 'hour') and
                CrontabTools._matches_field(dt.day, day, 'day') and
                CrontabTools._matches_field(dt.month, month, 'month') and
                CrontabTools._matches_field(dt.weekday(), weekday, 'weekday'))
    
    @staticmethod
    def _matches_field(value: int, pattern: str, field_name: str) -> bool:
        """检查值是否匹配字段模式"""
        if pattern == '*':
            return True
        
        # 处理星期特殊情况（0和7都表示星期日）
        if field_name == 'weekday':
            # Python的weekday(): 0=Monday, 6=Sunday
            # Cron的weekday: 0=Sunday, 6=Saturday
            cron_weekday = (value + 1) % 7
            if pattern == '7':
                pattern = '0'
        else:
            cron_weekday = value
        
        check_value = cron_weekday if field_name == 'weekday' else value
        
        # 处理逗号分隔
        if ',' in pattern:
            return str(check_value) in pattern.split(',')
        
        # 处理范围
        if '-' in pattern and '/' not in pattern:
            start, end = map(int, pattern.split('-'))
            return start <= check_value <= end
        
        # 处理步长
        if '/' in pattern:
            base, step = pattern.split('/')
            step = int(step)
            
            if base == '*':
                return check_value % step == 0
            elif '-' in base:
                start, end = map(int, base.split('-'))
                return start <= check_value <= end and (check_value - start) % step == 0
            else:
                base_val = int(base)
                return check_value >= base_val and (check_value - base_val) % step == 0
        
        # 单个值
        return check_value == int(pattern)
    
    @staticmethod
    def _get_relative_time(current: datetime, target: datetime) -> str:
        """获取相对时间描述"""
        diff = target - current
        
        if diff.days > 0:
            return f"{diff.days}天后"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}小时后"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}分钟后"
        else:
            return "即将执行"