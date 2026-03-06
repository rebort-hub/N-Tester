"""
UI自动化测试变量解析器
支持在测试步骤的输入值中使用动态函数表达式
语法：${function_name(args)}
"""
import re
import random
import string
import uuid
import hashlib
import base64
from datetime import datetime, timedelta


class VariableResolver:
    """UI自动化测试变量解析器"""
    
    def __init__(self):
        # 注册所有内置函数
        self.functions = {
            # 随机数函数
            'random_int': self._random_int,
            'random_float': self._random_float,
            'random_digits': self._random_digits,
            
            # 随机字符串函数
            'random_string': self._random_string,
            'random_letters': self._random_letters,
            'random_chinese': self._random_chinese,
            
            # 业务数据函数
            'random_phone': self._random_phone,
            'random_email': self._random_email,
            'random_id_card': self._random_id_card,
            'random_name': self._random_name,
            'random_company': self._random_company,
            'random_address': self._random_address,
            
            # 时间日期函数
            'timestamp': self._timestamp,
            'timestamp_sec': self._timestamp_sec,
            'datetime': self._datetime,
            'date': self._date,
            'time': self._time,
            'date_offset': self._date_offset,
            
            # 其他工具函数
            'uuid': self._uuid,
            'guid': self._guid,
            'base64': self._base64,
            'md5': self._md5,
            'sha1': self._sha1,
            'sha256': self._sha256,
            'random_mac': self._random_mac,
            'random_ip': self._random_ip,
            'random_password': self._random_password,
        }
    
    def resolve(self, text):
        """解析文本中的所有变量表达式
        
        Args:
            text: 包含变量表达式的文本，如 "user_${random_string(6)}@test.com"
            
        Returns:
            解析后的文本，如 "user_abc123@test.com"
        """
        if not text or not isinstance(text, str):
            return text
        
        # 匹配 ${function_name(args)} 模式
        pattern = r'\$\{([^}]+)\}'
        
        def replace_func(match):
            expression = match.group(1)
            try:
                return str(self._evaluate_expression(expression))
            except Exception as e:
                # 如果解析失败，保留原始表达式
                print(f"⚠️  变量解析失败: ${{{expression}}} - {str(e)}")
                return match.group(0)
        
        return re.sub(pattern, replace_func, text)
    
    def _evaluate_expression(self, expression):
        """评估单个表达式
        
        Args:
            expression: 函数表达式，如 "random_int(100, 200)" 或 "timestamp()"
            
        Returns:
            函数执行结果
        """
        # 解析函数名和参数
        match = re.match(r'(\w+)\((.*)\)', expression.strip())
        if not match:
            # 无参数函数
            func_name = expression.strip()
            args = []
        else:
            func_name = match.group(1)
            args_str = match.group(2)
            args = self._parse_args(args_str)
        
        # 调用对应函数
        if func_name in self.functions:
            return self.functions[func_name](*args)
        else:
            raise ValueError(f"未知函数: {func_name}")
    
    def _parse_args(self, args_str):
        """解析函数参数
        
        Args:
            args_str: 参数字符串，如 "100, 200" 或 "YYYY-MM-DD"
            
        Returns:
            参数列表
        """
        if not args_str.strip():
            return []
        
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            # 尝试转换为数字
            try:
                if '.' in arg:
                    args.append(float(arg))
                else:
                    args.append(int(arg))
            except ValueError:
                # 移除引号
                args.append(arg.strip('\'"'))
        return args
    
    # ========== 随机数函数 ==========
    
    def _random_int(self, min_val=0, max_val=100):
        """生成随机整数"""
        return random.randint(int(min_val), int(max_val))
    
    def _random_float(self, min_val=0.0, max_val=1.0, decimals=2):
        """生成随机浮点数"""
        value = random.uniform(float(min_val), float(max_val))
        return round(value, int(decimals))
    
    def _random_digits(self, length=6):
        """生成随机数字字符串"""
        return ''.join(random.choices(string.digits, k=int(length)))
    
    # ========== 随机字符串函数 ==========
    
    def _random_string(self, length=8):
        """生成随机字母数字字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=int(length)))
    
    def _random_letters(self, length=8):
        """生成随机字母字符串"""
        return ''.join(random.choices(string.ascii_letters, k=int(length)))
    
    def _random_chinese(self, length=2):
        """生成随机中文字符"""
        chinese_chars = []
        for _ in range(int(length)):
            chinese_chars.append(chr(random.randint(0x4e00, 0x9fa5)))
        return ''.join(chinese_chars)
    
    # ========== 业务数据函数 ==========
    
    def _random_phone(self):
        """生成随机手机号（中国大陆）"""
        prefixes = [
            '130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
            '150', '151', '152', '153', '155', '156', '157', '158', '159',
            '180', '181', '182', '183', '184', '185', '186', '187', '188', '189',
            '170', '171', '176', '177', '178'
        ]
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.digits, k=8))
        return prefix + suffix
    
    def _random_email(self):
        """生成随机邮箱地址"""
        username = self._random_string(8).lower()
        domains = ['test.com', 'example.com', 'demo.com', 'mail.com', 'qq.com', '163.com']
        domain = random.choice(domains)
        return f"{username}@{domain}"
    
    def _random_id_card(self):
        """生成随机身份证号（18位）"""
        area_codes = ['110101', '310101', '440101', '500101', '320101', '330101']
        area_code = random.choice(area_codes)
        
        birth_year = random.randint(1970, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = f"{birth_year}{birth_month:02d}{birth_day:02d}"
        
        sequence = f"{random.randint(0, 999):03d}"
        
        check_digits = string.digits + 'X'
        check_digit = random.choice(check_digits)
        
        return area_code + birth_date + sequence + check_digit
    
    def _random_name(self):
        """生成随机中文姓名"""
        surnames = [
            '王', '李', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴',
            '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '罗', '高'
        ]
        
        name_chars = [
            '伟', '芳', '娜', '秀', '敏', '静', '丽', '强', '磊', '军',
            '洋', '勇', '艳', '杰', '涛', '明', '超', '秀', '英', '华',
            '文', '玉', '建', '国', '春', '梅', '兰', '红', '霞', '鹏'
        ]
        
        surname = random.choice(surnames)
        name_length = random.randint(1, 2)
        given_name = ''.join(random.choices(name_chars, k=name_length))
        
        return surname + given_name
    
    def _random_company(self):
        """生成随机公司名称"""
        cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安']
        types = ['科技', '网络', '信息', '软件', '电子', '智能', '数据', '云计算']
        suffixes = ['有限公司', '股份有限公司', '技术有限公司', '集团有限公司']
        
        city = random.choice(cities)
        type_name = random.choice(types)
        suffix = random.choice(suffixes)
        
        return f"{city}{type_name}{suffix}"
    
    def _random_address(self):
        """生成随机地址"""
        cities = ['北京市', '上海市', '广州市', '深圳市', '杭州市', '成都市']
        districts = ['朝阳区', '海淀区', '浦东新区', '天河区', '南山区', '西湖区']
        streets = ['建国路', '中山路', '人民路', '解放路', '和平路', '胜利路']
        
        city = random.choice(cities)
        district = random.choice(districts)
        street = random.choice(streets)
        number = random.randint(1, 999)
        
        return f"{city}{district}{street}{number}号"
    
    # ========== 时间日期函数 ==========
    
    def _timestamp(self):
        """获取当前时间戳（毫秒）"""
        return int(datetime.now().timestamp() * 1000)
    
    def _timestamp_sec(self):
        """获取当前时间戳（秒）"""
        return int(datetime.now().timestamp())
    
    def _datetime(self, format_str='YYYY-MM-DD HH:mm:ss'):
        """格式化当前日期时间"""
        format_str = format_str.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
        format_str = format_str.replace('HH', '%H').replace('mm', '%M').replace('ss', '%S')
        return datetime.now().strftime(format_str)
    
    def _date(self, format_str='YYYY-MM-DD'):
        """格式化当前日期"""
        format_str = format_str.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
        return datetime.now().strftime(format_str)
    
    def _time(self, format_str='HH:mm:ss'):
        """格式化当前时间"""
        format_str = format_str.replace('HH', '%H').replace('mm', '%M').replace('ss', '%S')
        return datetime.now().strftime(format_str)
    
    def _date_offset(self, days=0, format_str='YYYY-MM-DD'):
        """获取偏移日期"""
        target_date = datetime.now() + timedelta(days=int(days))
        format_str = format_str.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
        return target_date.strftime(format_str)
    
    # ========== 其他工具函数 ==========
    
    def _uuid(self):
        """生成UUID"""
        return str(uuid.uuid4())
    
    def _guid(self):
        """生成GUID（同UUID）"""
        return str(uuid.uuid4())
    
    def _base64(self, text):
        """Base64编码"""
        return base64.b64encode(str(text).encode()).decode()
    
    def _md5(self, text):
        """MD5哈希"""
        return hashlib.md5(str(text).encode()).hexdigest()

    def _sha1(self, text):
        """SHA1哈希"""
        return hashlib.sha1(str(text).encode()).hexdigest()

    def _sha256(self, text):
        """SHA256哈希"""
        return hashlib.sha256(str(text).encode()).hexdigest()

    def _random_mac(self):
        """生成随机MAC地址"""
        mac = [random.randint(0x00, 0xff) for _ in range(6)]
        mac[0] = mac[0] & 0xfe
        return ':'.join(f'{x:02x}' for x in mac)

    def _random_ip(self, version=4):
        """生成随机IP地址"""
        if version == 4:
            return '.'.join(str(random.randint(0, 255)) for _ in range(4))
        elif version == 6:
            parts = []
            for i in range(8):
                parts.append(f'{random.randint(0, 0xffff):04x}')
            return ':'.join(parts)
        else:
            return '.'.join(str(random.randint(0, 255)) for _ in range(4))

    def _random_password(self, length=12):
        """生成随机密码"""
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(random.choices(chars, k=int(length)))


# 全局单例
_resolver = VariableResolver()


def resolve_variables(text):
    """便捷函数：解析文本中的变量表达式
    
    Args:
        text: 包含变量表达式的文本
        
    Returns:
        解析后的文本
    """
    return _resolver.resolve(text)
