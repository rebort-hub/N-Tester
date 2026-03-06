"""
随机工具
提供各种随机数据生成功能
"""
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List


class RandomTools:
    """随机工具类"""
    
    @staticmethod
    def random_int(min_val: int = 1, max_val: int = 100, count: int = 1) -> Dict[str, Any]:
        """
        生成随机整数
        
        Args:
            min_val: 最小值
            max_val: 最大值
            count: 生成数量
            
        Returns:
            随机整数
        """
        try:
            if min_val > max_val:
                return {'error': '最小值不能大于最大值'}
            
            if count == 1:
                result = random.randint(min_val, max_val)
                return {'result': result}
            else:
                result = [random.randint(min_val, max_val) for _ in range(count)]
                return {'result': result, 'count': len(result)}
        except Exception as e:
            return {'error': f'随机整数生成失败: {str(e)}'}
    
    @staticmethod
    def random_float(min_val: float = 0.0, max_val: float = 1.0, precision: int = 2, count: int = 1) -> Dict[str, Any]:
        """
        生成随机浮点数
        
        Args:
            min_val: 最小值
            max_val: 最大值
            precision: 精度
            count: 生成数量
            
        Returns:
            随机浮点数
        """
        try:
            if min_val > max_val:
                return {'error': '最小值不能大于最大值'}
            
            if count == 1:
                result = round(random.uniform(min_val, max_val), precision)
                return {'result': result}
            else:
                result = [round(random.uniform(min_val, max_val), precision) for _ in range(count)]
                return {'result': result, 'count': len(result)}
        except Exception as e:
            return {'error': f'随机浮点数生成失败: {str(e)}'}
    
    @staticmethod
    def random_string(length: int = 10, char_type: str = 'all', count: int = 1) -> Dict[str, Any]:
        """
        生成随机字符串
        
        Args:
            length: 字符串长度
            char_type: 字符类型
            count: 生成数量
            
        Returns:
            随机字符串
        """
        try:
            char_sets = {
                'all': string.ascii_letters + string.digits + string.punctuation,
                'letters': string.ascii_letters,
                'lowercase': string.ascii_lowercase,
                'uppercase': string.ascii_uppercase,
                'digits': string.digits,
                'alphanumeric': string.ascii_letters + string.digits,
                'hex': string.hexdigits.lower(),
                'special': string.punctuation
            }

            if char_type not in char_sets:
                return {'error': f'不支持的字符类型: {char_type}'}

            chars = char_sets[char_type]
            if count == 1:
                result = ''.join(random.choice(chars) for _ in range(length))
                return {'result': result, 'length': len(result)}
            else:
                result = [''.join(random.choice(chars) for _ in range(length)) for _ in range(count)]
                return {'result': result, 'count': len(result), 'string_length': length}
        except Exception as e:
            return {'error': f'随机字符串生成失败: {str(e)}'}
    
    @staticmethod
    def random_uuid(version: int = 4, count: int = 1) -> Dict[str, Any]:
        """
        生成随机UUID
        
        Args:
            version: UUID版本
            count: 生成数量
            
        Returns:
            随机UUID
        """
        try:
            if version == 1:
                uuid_gen = uuid.uuid1
            elif version == 4:
                uuid_gen = uuid.uuid4
            else:
                return {'error': f'不支持的UUID版本: {version}'}

            if count == 1:
                result = str(uuid_gen())
                return {
                    'result': result,
                    'version': version,
                    'format': 'string'
                }
            else:
                result = [str(uuid_gen()) for _ in range(count)]
                return {
                    'result': result,
                    'version': version,
                    'count': len(result)
                }
        except Exception as e:
            return {'error': f'UUID生成失败: {str(e)}'}
    
    @staticmethod
    def random_boolean(count: int = 1) -> Dict[str, Any]:
        """
        生成随机布尔值
        
        Args:
            count: 生成数量
            
        Returns:
            随机布尔值
        """
        try:
            if count == 1:
                result = random.choice([True, False])
                return {'result': result}
            else:
                result = [random.choice([True, False]) for _ in range(count)]
                return {'result': result, 'count': len(result)}
        except Exception as e:
            return {'error': f'随机布尔值生成失败: {str(e)}'}
    
    @staticmethod
    def random_mac_address(separator: str = ':', count: int = 1) -> Dict[str, Any]:
        """
        生成随机MAC地址
        
        Args:
            separator: 分隔符
            count: 生成数量
            
        Returns:
            随机MAC地址
        """
        try:
            def generate_mac():
                # 生成6个2位16进制数
                parts = [f'{random.randint(0x00, 0xff):02x}' for _ in range(6)]
                # 确保第一个字节的最低位为0（单播地址），次低位为0（本地管理）
                parts[0] = f'{int(parts[0], 16) & 0xfe:02x}'
                return separator.join(parts)

            if count == 1:
                result = generate_mac()
                return {'result': result}
            else:
                result = [generate_mac() for _ in range(count)]
                return {'result': result, 'count': len(result)}
        except Exception as e:
            return {'error': f'MAC地址生成失败: {str(e)}'}
    
    @staticmethod
    def random_ip_address(ip_version: int = 4, count: int = 1) -> Dict[str, Any]:
        """
        生成随机IP地址
        
        Args:
            ip_version: IP版本
            count: 生成数量
            
        Returns:
            随机IP地址
        """
        try:
            def generate_ipv4():
                return '.'.join(str(random.randint(0, 255)) for _ in range(4))

            def generate_ipv6():
                # 生成8个4位16进制数的IPv6地址
                parts = []
                for _ in range(8):
                    parts.append(f'{random.randint(0, 0xffff):04x}')
                return ':'.join(parts)

            if ip_version == 4:
                if count == 1:
                    result = generate_ipv4()
                    return {'result': result, 'version': 4}
                else:
                    result = [generate_ipv4() for _ in range(count)]
                    return {'result': result, 'version': 4, 'count': len(result)}
            elif ip_version == 6:
                if count == 1:
                    result = generate_ipv6()
                    return {'result': result, 'version': 6}
                else:
                    result = [generate_ipv6() for _ in range(count)]
                    return {'result': result, 'version': 6, 'count': len(result)}
            else:
                return {'error': f'不支持的IP版本: {ip_version}'}
        except Exception as e:
            return {'error': f'IP地址生成失败: {str(e)}'}
    
    @staticmethod
    def random_date(start_date: str, end_date: str, count: int = 1, date_format: str = '%Y-%m-%d') -> Dict[str, Any]:
        """
        生成随机日期
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            count: 生成数量
            date_format: 日期格式
            
        Returns:
            随机日期
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            delta = end_dt - start_dt
            random_seconds = random.randint(0, int(delta.total_seconds()))

            if count == 1:
                result = (start_dt + timedelta(seconds=random_seconds)).strftime(date_format)
                return {'result': result, 'format': date_format}
            else:
                result = []
                for _ in range(count):
                    random_seconds = random.randint(0, int(delta.total_seconds()))
                    result.append((start_dt + timedelta(seconds=random_seconds)).strftime(date_format))
                return {'result': result, 'count': len(result), 'format': date_format}
        except Exception as e:
            return {'error': f'随机日期生成失败: {str(e)}'}
    
    @staticmethod
    def random_password(length: int = 12, include_uppercase: bool = True, include_lowercase: bool = True,
                        include_digits: bool = True, include_special: bool = True, count: int = 1) -> Dict[str, Any]:
        """
        生成随机密码
        
        Args:
            length: 密码长度
            include_uppercase: 包含大写字母
            include_lowercase: 包含小写字母
            include_digits: 包含数字
            include_special: 包含特殊字符
            count: 生成数量
            
        Returns:
            随机密码
        """
        try:
            chars = ''
            if include_uppercase:
                chars += string.ascii_uppercase
            if include_lowercase:
                chars += string.ascii_lowercase
            if include_digits:
                chars += string.digits
            if include_special:
                chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'

            if not chars:
                return {'error': '至少选择一种字符类型'}

            def generate_password():
                password = ''.join(random.choice(chars) for _ in range(length))
                return password

            if count == 1:
                result = generate_password()
                return {
                    'result': result,
                    'length': len(result),
                    'contains': {
                        'uppercase': include_uppercase,
                        'lowercase': include_lowercase,
                        'digits': include_digits,
                        'special': include_special
                    }
                }
            else:
                result = [generate_password() for _ in range(count)]
                return {
                    'result': result,
                    'count': len(result),
                    'length': length,
                    'contains': {
                        'uppercase': include_uppercase,
                        'lowercase': include_lowercase,
                        'digits': include_digits,
                        'special': include_special
                    }
                }
        except Exception as e:
            return {'error': f'随机密码生成失败: {str(e)}'}
    
    @staticmethod
    def random_color(format: str = 'hex', count: int = 1) -> Dict[str, Any]:
        """
        生成随机颜色
        
        Args:
            format: 颜色格式
            count: 生成数量
            
        Returns:
            随机颜色
        """
        try:
            def generate():
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)

                if format == 'hex':
                    return f'#{r:02x}{g:02x}{b:02x}'
                elif format == 'rgb':
                    return f'rgb({r}, {g}, {b})'
                elif format == 'rgba':
                    a = round(random.random(), 2)
                    return f'rgba({r}, {g}, {b}, {a})'
                else:
                    raise ValueError(f'不支持的格式: {format}')

            if count == 1:
                result = generate()
                return {'result': result, 'format': format}
            else:
                result = [generate() for _ in range(count)]
                return {'result': result, 'count': len(result), 'format': format}
        except Exception as e:
            return {'error': f'随机颜色生成失败: {str(e)}'}
    
    @staticmethod
    def random_sequence(sequence: List, count: int = 1, unique: bool = False) -> Dict[str, Any]:
        """
        从序列中随机选择
        
        Args:
            sequence: 序列
            count: 选择数量
            unique: 是否唯一
            
        Returns:
            随机选择结果
        """
        try:
            if unique:
                if count > len(sequence):
                    return {'error': f'请求数量({count})大于序列长度({len(sequence)})'}
                result = random.sample(sequence, count)
            else:
                result = [random.choice(sequence) for _ in range(count)]

            return {
                'result': result[0] if count == 1 else result,
                'count': len(result) if count > 1 else 1
            }
        except Exception as e:
            return {'error': f'随机序列选择失败: {str(e)}'}
        """
        生成随机浮点数
        
        Args:
            min_val: 最小值
            max_val: 最大值
            precision: 小数位数
            count: 生成数量
            
        Returns:
            随机浮点数
        """
        try:
            if min_val > max_val:
                return {'error': '最小值不能大于最大值'}
            
            if count == 1:
                result = round(random.uniform(min_val, max_val), precision)
            else:
                result = [round(random.uniform(min_val, max_val), precision) for _ in range(count)]
            
            return {
                'success': True,
                'result': result,
                'min_val': min_val,
                'max_val': max_val,
                'precision': precision,
                'count': count,
                'type': 'float'
            }
        except Exception as e:
            return {'error': f'随机浮点数生成失败: {str(e)}'}
    
    @staticmethod
    def random_string(length: int = 8, char_type: str = 'all', count: int = 1) -> Dict[str, Any]:
        """
        生成随机字符串
        
        Args:
            length: 字符串长度
            char_type: 字符类型 ('letters', 'digits', 'alphanumeric', 'all', 'lowercase', 'uppercase')
            count: 生成数量
            
        Returns:
            随机字符串
        """
        try:
            if length <= 0:
                return {'error': '字符串长度必须大于0'}
            
            # 定义字符集
            char_sets = {
                'letters': string.ascii_letters,
                'digits': string.digits,
                'alphanumeric': string.ascii_letters + string.digits,
                'lowercase': string.ascii_lowercase,
                'uppercase': string.ascii_uppercase,
                'all': string.ascii_letters + string.digits + string.punctuation
            }
            
            if char_type not in char_sets:
                return {'error': f'不支持的字符类型: {char_type}'}
            
            chars = char_sets[char_type]
            
            if count == 1:
                result = ''.join(random.choices(chars, k=length))
            else:
                result = [''.join(random.choices(chars, k=length)) for _ in range(count)]
            
            return {
                'success': True,
                'result': result,
                'length': length,
                'char_type': char_type,
                'count': count,
                'charset_size': len(chars)
            }
        except Exception as e:
            return {'error': f'随机字符串生成失败: {str(e)}'}
    
    @staticmethod
    def random_uuid(version: int = 4, count: int = 1) -> Dict[str, Any]:
        """
        生成随机UUID
        
        Args:
            version: UUID版本 (1, 4)
            count: 生成数量
            
        Returns:
            随机UUID
        """
        try:
            if version not in [1, 4]:
                return {'error': 'UUID版本只支持1和4'}
            
            if count == 1:
                if version == 1:
                    result = str(uuid.uuid1())
                else:
                    result = str(uuid.uuid4())
            else:
                if version == 1:
                    result = [str(uuid.uuid1()) for _ in range(count)]
                else:
                    result = [str(uuid.uuid4()) for _ in range(count)]
            
            return {
                'success': True,
                'result': result,
                'version': version,
                'count': count,
                'format': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
            }
        except Exception as e:
            return {'error': f'随机UUID生成失败: {str(e)}'}
    
    @staticmethod
    def random_boolean(count: int = 1, true_probability: float = 0.5) -> Dict[str, Any]:
        """
        生成随机布尔值
        
        Args:
            count: 生成数量
            true_probability: True的概率
            
        Returns:
            随机布尔值
        """
        try:
            if not 0 <= true_probability <= 1:
                return {'error': 'True概率必须在0-1之间'}
            
            if count == 1:
                result = random.random() < true_probability
            else:
                result = [random.random() < true_probability for _ in range(count)]
            
            # 统计结果
            if count > 1:
                true_count = sum(result)
                false_count = count - true_count
                actual_probability = true_count / count
            else:
                true_count = 1 if result else 0
                false_count = 0 if result else 1
                actual_probability = true_probability
            
            return {
                'success': True,
                'result': result,
                'count': count,
                'true_probability': true_probability,
                'actual_probability': actual_probability,
                'true_count': true_count,
                'false_count': false_count
            }
        except Exception as e:
            return {'error': f'随机布尔值生成失败: {str(e)}'}
    
    @staticmethod
    def random_mac_address(separator: str = ':', uppercase: bool = True, count: int = 1) -> Dict[str, Any]:
        """
        生成随机MAC地址
        
        Args:
            separator: 分隔符 (':', '-', '')
            uppercase: 是否大写
            count: 生成数量
            
        Returns:
            随机MAC地址
        """
        try:
            def generate_one():
                # 生成6个字节的MAC地址
                mac_bytes = [random.randint(0, 255) for _ in range(6)]
                # 确保第一个字节是偶数（单播地址）
                mac_bytes[0] = mac_bytes[0] & 0xFE
                
                # 转换为十六进制
                hex_parts = [f'{byte:02x}' for byte in mac_bytes]
                if uppercase:
                    hex_parts = [part.upper() for part in hex_parts]
                
                return separator.join(hex_parts)
            
            if count == 1:
                result = generate_one()
            else:
                result = [generate_one() for _ in range(count)]
            
            return {
                'success': True,
                'result': result,
                'separator': separator,
                'uppercase': uppercase,
                'count': count,
                'format': 'XX:XX:XX:XX:XX:XX'
            }
        except Exception as e:
            return {'error': f'随机MAC地址生成失败: {str(e)}'}
    
    @staticmethod
    def random_ip_address(ip_version: int = 4, private: bool = False, count: int = 1) -> Dict[str, Any]:
        """
        生成随机IP地址
        
        Args:
            ip_version: IP版本 (4, 6)
            private: 是否生成私有IP
            count: 生成数量
            
        Returns:
            随机IP地址
        """
        try:
            def generate_ipv4():
                if private:
                    # 私有IP地址范围
                    ranges = [
                        (10, 0, 0, 0, 10, 255, 255, 255),      # 10.0.0.0/8
                        (172, 16, 0, 0, 172, 31, 255, 255),    # 172.16.0.0/12
                        (192, 168, 0, 0, 192, 168, 255, 255)   # 192.168.0.0/16
                    ]
                    range_choice = random.choice(ranges)
                    return f'{random.randint(range_choice[0], range_choice[4])}.' \
                           f'{random.randint(range_choice[1], range_choice[5])}.' \
                           f'{random.randint(range_choice[2], range_choice[6])}.' \
                           f'{random.randint(range_choice[3], range_choice[7])}'
                else:
                    # 公网IP（避免私有IP和特殊IP）
                    while True:
                        a = random.randint(1, 223)
                        if a in [10, 127] or (172 <= a <= 172) or (192 <= a <= 192):
                            continue
                        b = random.randint(0, 255)
                        if a == 172 and 16 <= b <= 31:
                            continue
                        if a == 192 and b == 168:
                            continue
                        c = random.randint(0, 255)
                        d = random.randint(1, 254)
                        return f'{a}.{b}.{c}.{d}'
            
            def generate_ipv6():
                # 生成IPv6地址
                groups = []
                for _ in range(8):
                    group = f'{random.randint(0, 65535):04x}'
                    groups.append(group)
                return ':'.join(groups)
            
            if ip_version == 4:
                if count == 1:
                    result = generate_ipv4()
                else:
                    result = [generate_ipv4() for _ in range(count)]
                format_str = 'xxx.xxx.xxx.xxx'
            elif ip_version == 6:
                if count == 1:
                    result = generate_ipv6()
                else:
                    result = [generate_ipv6() for _ in range(count)]
                format_str = 'xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx'
            else:
                return {'error': 'IP版本只支持4和6'}
            
            return {
                'success': True,
                'result': result,
                'ip_version': ip_version,
                'private': private,
                'count': count,
                'format': format_str
            }
        except Exception as e:
            return {'error': f'随机IP地址生成失败: {str(e)}'}
    
    @staticmethod
    def random_date(start_date: str = '2020-01-01', end_date: str = '2025-12-31', 
                   date_format: str = '%Y-%m-%d', count: int = 1) -> Dict[str, Any]:
        """
        生成随机日期
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            date_format: 日期格式
            count: 生成数量
            
        Returns:
            随机日期
        """
        try:
            # 解析日期
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt > end_dt:
                return {'error': '开始日期不能晚于结束日期'}
            
            days_between = (end_dt - start_dt).days
            
            def generate_one():
                random_days = random.randint(0, days_between)
                random_dt = start_dt + timedelta(days=random_days)
                return random_dt.strftime(date_format)
            
            if count == 1:
                result = generate_one()
            else:
                result = [generate_one() for _ in range(count)]
            
            return {
                'success': True,
                'result': result,
                'start_date': start_date,
                'end_date': end_date,
                'date_format': date_format,
                'count': count,
                'days_range': days_between
            }
        except ValueError as e:
            return {'error': f'日期格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'随机日期生成失败: {str(e)}'}
    
    @staticmethod
    def random_password(length: int = 12, include_uppercase: bool = True, 
                       include_lowercase: bool = True, include_digits: bool = True,
                       include_special: bool = True, exclude_ambiguous: bool = False,
                       count: int = 1) -> Dict[str, Any]:
        """
        生成随机密码
        
        Args:
            length: 密码长度
            include_uppercase: 包含大写字母
            include_lowercase: 包含小写字母
            include_digits: 包含数字
            include_special: 包含特殊字符
            exclude_ambiguous: 排除易混淆字符
            count: 生成数量
            
        Returns:
            随机密码
        """
        try:
            if length <= 0:
                return {'error': '密码长度必须大于0'}
            
            # 构建字符集
            chars = ''
            char_types = []
            
            if include_uppercase:
                uppercase = string.ascii_uppercase
                if exclude_ambiguous:
                    uppercase = uppercase.replace('O', '').replace('I', '')
                chars += uppercase
                char_types.append('uppercase')
            
            if include_lowercase:
                lowercase = string.ascii_lowercase
                if exclude_ambiguous:
                    lowercase = lowercase.replace('l', '').replace('o', '')
                chars += lowercase
                char_types.append('lowercase')
            
            if include_digits:
                digits = string.digits
                if exclude_ambiguous:
                    digits = digits.replace('0', '').replace('1')
                chars += digits
                char_types.append('digits')
            
            if include_special:
                special = '!@#$%^&*()_+-=[]{}|;:,.<>?'
                chars += special
                char_types.append('special')
            
            if not chars:
                return {'error': '至少需要选择一种字符类型'}
            
            def generate_one():
                password = ''.join(random.choices(chars, k=length))
                
                # 确保包含每种选择的字符类型
                if len(char_types) > 1 and length >= len(char_types):
                    password_list = list(password)
                    for i, char_type in enumerate(char_types):
                        if char_type == 'uppercase' and include_uppercase:
                            password_list[i] = random.choice(string.ascii_uppercase)
                        elif char_type == 'lowercase' and include_lowercase:
                            password_list[i] = random.choice(string.ascii_lowercase)
                        elif char_type == 'digits' and include_digits:
                            password_list[i] = random.choice(string.digits)
                        elif char_type == 'special' and include_special:
                            password_list[i] = random.choice('!@#$%^&*()_+-=[]{}|;:,.<>?')
                    
                    # 打乱顺序
                    random.shuffle(password_list)
                    password = ''.join(password_list)
                
                return password
            
            if count == 1:
                result = generate_one()
            else:
                result = [generate_one() for _ in range(count)]
            
            # 计算密码强度
            def calculate_strength(pwd):
                score = 0
                if any(c.isupper() for c in pwd):
                    score += 1
                if any(c.islower() for c in pwd):
                    score += 1
                if any(c.isdigit() for c in pwd):
                    score += 1
                if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in pwd):
                    score += 1
                if len(pwd) >= 8:
                    score += 1
                if len(pwd) >= 12:
                    score += 1
                
                if score <= 2:
                    return '弱'
                elif score <= 4:
                    return '中'
                else:
                    return '强'
            
            strength = calculate_strength(result if count == 1 else result[0])
            
            return {
                'success': True,
                'result': result,
                'length': length,
                'char_types': char_types,
                'count': count,
                'strength': strength,
                'charset_size': len(chars)
            }
        except Exception as e:
            return {'error': f'随机密码生成失败: {str(e)}'}
    
    @staticmethod
    def random_color(color_format: str = 'hex', count: int = 1) -> Dict[str, Any]:
        """
        生成随机颜色
        
        Args:
            color_format: 颜色格式 ('hex', 'rgb', 'hsl', 'all')
            count: 生成数量
            
        Returns:
            随机颜色
        """
        try:
            def generate_one():
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                
                # 转换为HSL
                r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
                max_val = max(r_norm, g_norm, b_norm)
                min_val = min(r_norm, g_norm, b_norm)
                h, s, l = 0, 0, (max_val + min_val) / 2
                
                if max_val != min_val:
                    d = max_val - min_val
                    s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
                    if max_val == r_norm:
                        h = (g_norm - b_norm) / d + (6 if g_norm < b_norm else 0)
                    elif max_val == g_norm:
                        h = (b_norm - r_norm) / d + 2
                    elif max_val == b_norm:
                        h = (r_norm - g_norm) / d + 4
                    h /= 6
                
                h = int(h * 360)
                s = int(s * 100)
                l = int(l * 100)
                
                color_data = {
                    'hex': f'#{r:02X}{g:02X}{b:02X}',
                    'rgb': f'rgb({r}, {g}, {b})',
                    'hsl': f'hsl({h}, {s}%, {l}%)',
                    'values': {
                        'r': r, 'g': g, 'b': b,
                        'h': h, 's': s, 'l': l
                    }
                }
                
                if color_format == 'hex':
                    return color_data['hex']
                elif color_format == 'rgb':
                    return color_data['rgb']
                elif color_format == 'hsl':
                    return color_data['hsl']
                else:
                    return color_data
            
            if count == 1:
                result = generate_one()
            else:
                result = [generate_one() for _ in range(count)]
            
            return {
                'success': True,
                'result': result,
                'color_format': color_format,
                'count': count
            }
        except Exception as e:
            return {'error': f'随机颜色生成失败: {str(e)}'}
    
    @staticmethod
    def random_sequence(sequence: List[Any], count: int = 1, unique: bool = False) -> Dict[str, Any]:
        """
        从序列中随机选择
        
        Args:
            sequence: 序列数据
            count: 选择数量
            unique: 是否唯一（不重复）
            
        Returns:
            随机选择结果
        """
        try:
            if not sequence:
                return {'error': '序列不能为空'}
            
            if unique and count > len(sequence):
                return {'error': '唯一选择的数量不能超过序列长度'}
            
            if count == 1:
                result = random.choice(sequence)
            else:
                if unique:
                    result = random.sample(sequence, count)
                else:
                    result = random.choices(sequence, k=count)
            
            return {
                'success': True,
                'result': result,
                'sequence_length': len(sequence),
                'count': count,
                'unique': unique,
                'sequence_type': type(sequence[0]).__name__ if sequence else 'unknown'
            }
        except Exception as e:
            return {'error': f'随机序列选择失败: {str(e)}'}