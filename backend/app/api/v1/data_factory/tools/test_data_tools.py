"""
测试数据生成工具
生成各种测试数据，包括姓名、手机号、邮箱、地址、身份证号等
"""
import random
import string
from typing import Dict, Any
from datetime import datetime, timedelta


class TestDataTools:
    """测试数据工具类"""
    
    # 中文姓氏
    SURNAMES = [
        '王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
        '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
        '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧',
        '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕',
        '苏', '卢', '蒋', '蔡', '贾', '丁', '魏', '薛', '叶', '阎'
    ]
    
    # 中文名字
    MALE_NAMES = [
        '伟', '强', '磊', '军', '勇', '涛', '明', '超', '俊', '华',
        '建', '国', '峰', '学', '永', '杰', '松', '波', '民', '友',
        '志', '清', '坚', '庆', '东', '海', '安', '举', '旭', '雷',
        '振', '宁', '福', '生', '龙', '元', '全', '国', '胜', '学',
        '祥', '才', '发', '武', '新', '利', '飞', '鹏', '万', '忠'
    ]
    
    FEMALE_NAMES = [
        '芳', '娜', '敏', '静', '丽', '强', '洁', '美', '娟', '艳',
        '秀', '红', '霞', '燕', '玲', '梅', '莹', '雪', '琳', '佳',
        '慧', '巧', '雅', '素', '真', '环', '雨', '想', '妍', '叶',
        '璐', '萍', '荣', '爱', '妮', '娅', '莉', '兰', '凤', '洋',
        '露', '倩', '馨', '蕊', '薇', '菁', '梦', '岚', '苑', '婕'
    ]
    
    # 手机号前缀
    PHONE_PREFIXES = [
        '130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
        '147', '150', '151', '152', '153', '155', '156', '157', '158', '159',
        '180', '181', '182', '183', '184', '185', '186', '187', '188', '189',
        '170', '171', '172', '173', '174', '175', '176', '177', '178', '179'
    ]
    
    # 邮箱域名
    EMAIL_DOMAINS = [
        'qq.com', '163.com', '126.com', 'gmail.com', 'sina.com',
        'sohu.com', 'yahoo.com', 'hotmail.com', '139.com', 'foxmail.com'
    ]
    
    # 省份
    PROVINCES = [
        '北京市', '天津市', '上海市', '重庆市', '河北省', '山西省', '辽宁省',
        '吉林省', '黑龙江省', '江苏省', '浙江省', '安徽省', '福建省', '江西省',
        '山东省', '河南省', '湖北省', '湖南省', '广东省', '海南省', '四川省',
        '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省', '内蒙古自治区',
        '广西壮族自治区', '西藏自治区', '宁夏回族自治区', '新疆维吾尔自治区',
        '香港特别行政区', '澳门特别行政区'
    ]
    
    # 城市
    CITIES = [
        '北京市', '上海市', '广州市', '深圳市', '杭州市', '南京市', '武汉市',
        '成都市', '西安市', '郑州市', '青岛市', '大连市', '宁波市', '厦门市',
        '福州市', '沈阳市', '长沙市', '哈尔滨市', '济南市', '昆明市', '兰州市',
        '石家庄市', '太原市', '合肥市', '南昌市', '贵阳市', '南宁市', '银川市',
        '西宁市', '呼和浩特市', '乌鲁木齐市', '拉萨市', '海口市', '三亚市'
    ]
    
    # 公司类型
    COMPANY_TYPES = [
        '有限公司', '股份有限公司', '有限责任公司', '集团有限公司',
        '科技有限公司', '贸易有限公司', '实业有限公司', '投资有限公司'
    ]
    
    # 公司名称前缀
    COMPANY_PREFIXES = [
        '华为', '腾讯', '阿里巴巴', '百度', '京东', '美团', '字节跳动', '滴滴',
        '小米', '网易', '新浪', '搜狐', '360', '携程', '去哪儿', '苏宁',
        '国美', '海尔', '格力', '美的', '联想', '华硕', '戴尔', '惠普',
        '中兴', '大疆', '比亚迪', '吉利', '长城', '奇瑞', '上汽', '一汽'
    ]
    
    @staticmethod
    def generate_chinese_name(gender: str = 'random', count: int = 1) -> Dict[str, Any]:
        """
        生成中文姓名
        
        Args:
            gender: 性别 ('male', 'female', 'random')
            count: 生成数量
            
        Returns:
            生成的姓名
        """
        try:
            def generate_one():
                surname = random.choice(TestDataTools.SURNAMES)
                
                if gender == 'male':
                    given_name = random.choice(TestDataTools.MALE_NAMES)
                elif gender == 'female':
                    given_name = random.choice(TestDataTools.FEMALE_NAMES)
                else:
                    # 随机选择性别
                    names = TestDataTools.MALE_NAMES + TestDataTools.FEMALE_NAMES
                    given_name = random.choice(names)
                
                # 有30%概率生成双字名
                if random.random() < 0.3:
                    if gender == 'male':
                        given_name += random.choice(TestDataTools.MALE_NAMES)
                    elif gender == 'female':
                        given_name += random.choice(TestDataTools.FEMALE_NAMES)
                    else:
                        names = TestDataTools.MALE_NAMES + TestDataTools.FEMALE_NAMES
                        given_name += random.choice(names)
                
                return surname + given_name
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'中文姓名生成失败: {str(e)}'}
    
    @staticmethod
    def generate_chinese_phone(region: str = 'all', count: int = 1) -> Dict[str, Any]:
        """
        生成中国手机号
        
        Args:
            region: 地区 ('all', 'mobile', 'unicom', 'telecom')
            count: 生成数量
            
        Returns:
            生成的手机号
        """
        try:
            def generate_one():
                if region == 'mobile':
                    # 移动号段
                    prefixes = ['134', '135', '136', '137', '138', '139', '147', '150', '151', '152', '157', '158', '159', '182', '183', '184', '187', '188']
                elif region == 'unicom':
                    # 联通号段
                    prefixes = ['130', '131', '132', '155', '156', '185', '186', '176']
                elif region == 'telecom':
                    # 电信号段
                    prefixes = ['133', '153', '180', '181', '189', '177']
                else:
                    # 所有号段
                    prefixes = TestDataTools.PHONE_PREFIXES
                
                prefix = random.choice(prefixes)
                suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
                return prefix + suffix
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'手机号生成失败: {str(e)}'}
    
    @staticmethod
    def generate_chinese_email(domain: str = 'random', count: int = 1) -> Dict[str, Any]:
        """
        生成邮箱地址
        
        Args:
            domain: 域名 ('random' 或指定域名)
            count: 生成数量
            
        Returns:
            生成的邮箱
        """
        try:
            def generate_one():
                # 生成用户名
                username_length = random.randint(5, 12)
                username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
                
                # 选择域名
                if domain == 'random':
                    email_domain = random.choice(TestDataTools.EMAIL_DOMAINS)
                else:
                    email_domain = domain
                
                return f'{username}@{email_domain}'
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'邮箱生成失败: {str(e)}'}
    
    @staticmethod
    def generate_chinese_address(full_address: bool = True, count: int = 1) -> Dict[str, Any]:
        """
        生成中文地址
        
        Args:
            full_address: 是否生成完整地址
            count: 生成数量
            
        Returns:
            生成的地址
        """
        try:
            def generate_one():
                province = random.choice(TestDataTools.PROVINCES)
                city = random.choice(TestDataTools.CITIES)
                
                if not full_address:
                    return f'{province} {city}'
                
                # 生成完整地址
                district = f'{random.choice(["东", "西", "南", "北", "中"])}区'
                street = f'{random.choice(["建设", "人民", "解放", "中山", "和平", "友谊", "胜利", "光明"])}路'
                number = random.randint(1, 999)
                unit = random.randint(1, 20)
                room = random.randint(101, 2999)
                
                return f'{province}{city}{district}{street}{number}号{unit}单元{room}室'
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'地址生成失败: {str(e)}'}
    
    @staticmethod
    def generate_id_card(count: int = 1) -> Dict[str, Any]:
        """
        生成身份证号
        
        Args:
            count: 生成数量
            
        Returns:
            生成的身份证号
        """
        try:
            def generate_one():
                # 地区代码（前6位）
                area_codes = [
                    '110101', '110102', '110105', '110106', '110107', '110108',  # 北京
                    '310101', '310104', '310105', '310106', '310107', '310109',  # 上海
                    '440101', '440103', '440104', '440105', '440106', '440111',  # 广州
                    '440301', '440303', '440304', '440305', '440306', '440307',  # 深圳
                ]
                area_code = random.choice(area_codes)
                
                # 出生日期（8位）
                start_date = datetime(1950, 1, 1)
                end_date = datetime(2005, 12, 31)
                random_date = start_date + timedelta(
                    days=random.randint(0, (end_date - start_date).days)
                )
                birth_date = random_date.strftime('%Y%m%d')
                
                # 顺序码（3位）
                sequence = f'{random.randint(1, 999):03d}'
                
                # 前17位
                id_17 = area_code + birth_date + sequence
                
                # 计算校验码
                weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
                check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
                
                sum_value = sum(int(id_17[i]) * weights[i] for i in range(17))
                check_code = check_codes[sum_value % 11]
                
                return id_17 + check_code
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'身份证号生成失败: {str(e)}'}
    
    @staticmethod
    def generate_company_name(company_type: str = 'all', count: int = 1) -> Dict[str, Any]:
        """
        生成公司名称
        
        Args:
            company_type: 公司类型
            count: 生成数量
            
        Returns:
            生成的公司名称
        """
        try:
            def generate_one():
                prefix = random.choice(TestDataTools.COMPANY_PREFIXES)
                
                if company_type == 'all':
                    suffix = random.choice(TestDataTools.COMPANY_TYPES)
                else:
                    suffix = company_type
                
                # 有50%概率添加地区前缀
                if random.random() < 0.5:
                    city = random.choice(['北京', '上海', '深圳', '广州', '杭州', '南京'])
                    return f'{city}{prefix}{suffix}'
                else:
                    return f'{prefix}{suffix}'
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'公司名称生成失败: {str(e)}'}
    
    @staticmethod
    def generate_bank_card(count: int = 1) -> Dict[str, Any]:
        """
        生成银行卡号
        
        Args:
            count: 生成数量
            
        Returns:
            生成的银行卡号
        """
        try:
            def generate_one():
                # 银行卡前缀（BIN码）
                bank_prefixes = [
                    '6225', '6227', '6228', '6229',  # 招商银行
                    '6214', '6215', '6216', '6217',  # 工商银行
                    '6222', '6223', '6224',          # 建设银行
                    '6230', '6231', '6232',          # 农业银行
                    '6236', '6237', '6238',          # 中国银行
                    '6250', '6251', '6252',          # 交通银行
                ]
                
                prefix = random.choice(bank_prefixes)
                
                # 生成剩余位数（总长度19位）
                remaining_length = 19 - len(prefix) - 1  # 减去校验位
                remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(remaining_length)])
                
                # 计算Luhn校验码
                card_without_check = prefix + remaining_digits
                check_digit = TestDataTools._calculate_luhn_check_digit(card_without_check)
                
                return card_without_check + str(check_digit)
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'银行卡号生成失败: {str(e)}'}
    
    @staticmethod
    def generate_hk_id_card(count: int = 1) -> Dict[str, Any]:
        """
        生成香港身份证号
        
        Args:
            count: 生成数量
            
        Returns:
            生成的香港身份证号
        """
        try:
            def generate_one():
                # 生成字母前缀（1-2个字母）
                letters = random.choice([
                    random.choice(string.ascii_uppercase),
                    ''.join(random.choices(string.ascii_uppercase, k=2))
                ])
                
                # 生成6位数字
                numbers = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                
                # 计算校验码
                letter_values = sum((ord(letter) - ord('A') + 1) * (8 - i) for i, letter in enumerate(letters))
                number_values = sum(int(num) * (7 - i) for i, num in enumerate(numbers))
                total = letter_values + number_values
                remainder = total % 11
                
                if remainder == 0:
                    check_code = '0'
                elif remainder == 1:
                    check_code = 'A'
                else:
                    check_code = str(11 - remainder)
                
                return f'{letters}{numbers}({check_code})'
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'香港身份证号生成失败: {str(e)}'}
    
    @staticmethod
    def generate_business_license(count: int = 1) -> Dict[str, Any]:
        """
        生成营业执照号（统一社会信用代码）
        
        Args:
            count: 生成数量
            
        Returns:
            生成的营业执照号
        """
        try:
            def generate_one():
                # 统一社会信用代码18位
                # 第1位：登记管理部门代码（9-其他）
                first_digit = '9'
                
                # 第2位：机构类别代码（1-企业）
                second_digit = '1'
                
                # 第3-8位：登记管理机关行政区划码
                area_codes = ['110000', '310000', '440000', '320000', '330000', '500000']
                area_code = random.choice(area_codes)
                
                # 第9-17位：主体标识码（组织机构代码）
                org_code = ''.join([random.choice('0123456789ABCDEFGHJKLMNPQRTUWXY') for _ in range(8)])
                
                # 前17位
                code_17 = first_digit + second_digit + area_code + org_code
                
                # 计算校验码
                check_digit = TestDataTools._calculate_credit_code_check_digit(code_17)
                
                return code_17 + check_digit
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'营业执照号生成失败: {str(e)}'}
    
    @staticmethod
    def generate_coordinates(count: int = 1) -> Dict[str, Any]:
        """
        生成经纬度坐标
        
        Args:
            count: 生成数量
            
        Returns:
            生成的经纬度
        """
        try:
            def generate_one():
                # 中国范围: 经度 73-135, 纬度 18-54
                longitude = round(random.uniform(73.0, 135.0), 6)
                latitude = round(random.uniform(18.0, 54.0), 6)
                
                return {
                    'longitude': longitude,
                    'latitude': latitude,
                    'longitude_formatted': f'{longitude:.6f}°E',
                    'latitude_formatted': f'{latitude:.6f}°N',
                    'coordinate_string': f'{latitude:.6f},{longitude:.6f}'
                }
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'经纬度生成失败: {str(e)}'}
    
    @staticmethod
    def generate_user_profile(count: int = 1) -> Dict[str, Any]:
        """
        生成完整用户档案
        
        Args:
            count: 生成数量
            
        Returns:
            生成的用户档案
        """
        try:
            def generate_one():
                # 随机性别
                gender = random.choice(['male', 'female'])
                gender_cn = '男' if gender == 'male' else '女'
                
                # 生成姓名
                name_result = TestDataTools.generate_chinese_name(gender=gender, count=1)
                name = name_result['result']
                
                # 生成手机号
                phone_result = TestDataTools.generate_chinese_phone(count=1)
                phone = phone_result['result']
                
                # 生成邮箱
                email_result = TestDataTools.generate_chinese_email(count=1)
                email = email_result['result']
                
                # 生成地址
                address_result = TestDataTools.generate_chinese_address(count=1)
                address = address_result['result']
                
                # 生成身份证号
                id_card_result = TestDataTools.generate_id_card(count=1)
                id_card = id_card_result['result']
                
                # 生成公司名称
                company_result = TestDataTools.generate_company_name(count=1)
                company = company_result['result']
                
                # 生成年龄和生日
                age = random.randint(18, 65)
                birth_year = datetime.now().year - age
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)  # 避免日期问题
                birthday = f'{birth_year}-{birth_month:02d}-{birth_day:02d}'
                
                # 职业
                jobs = [
                    '软件工程师', '产品经理', '设计师', '销售经理', '市场专员',
                    '财务分析师', '人力资源', '运营专员', '数据分析师', '项目经理',
                    '客服专员', '行政助理', '法务专员', '采购经理', '质量工程师'
                ]
                job = random.choice(jobs)
                
                return {
                    'name': name,
                    'gender': gender_cn,
                    'age': age,
                    'birthday': birthday,
                    'phone': phone,
                    'email': email,
                    'address': address,
                    'id_card': id_card,
                    'company': company,
                    'job': job
                }
            
            if count == 1:
                return {'result': generate_one()}
            else:
                result = [generate_one() for _ in range(count)]
                return {'result': result, 'count': len(result)}
                
        except Exception as e:
            return {'error': f'用户档案生成失败: {str(e)}'}
    
    @staticmethod
    def _calculate_luhn_check_digit(card_number: str) -> int:
        """计算Luhn算法校验位"""
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10
        
        return (10 - luhn_checksum(card_number)) % 10
    
    @staticmethod
    def _calculate_credit_code_check_digit(code_17: str) -> str:
        """计算统一社会信用代码校验位"""
        code_chars = '0123456789ABCDEFGHJKLMNPQRTUWXY'
        weights = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]
        
        sum_value = 0
        for i, char in enumerate(code_17):
            sum_value += code_chars.index(char) * weights[i]
        
        remainder = sum_value % 31
        check_index = (31 - remainder) % 31
        return code_chars[check_index]