"""
数据工厂Service层
处理数据工厂的业务逻辑
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete, or_
from datetime import datetime

from app.corelibs.logger import logger
from .model import DataFactoryRecord
from .schema import (
    DataFactoryRecordCreate,
    DataFactoryRecordUpdate,
    DataFactoryRecordOut,
    ToolExecuteRequest,
    BatchGenerateRequest
)
from .tool_list import get_tool_list, get_categories

# 工具显示名称映射
TOOL_DISPLAY_MAP = {
    # 测试数据工具
    'generate_chinese_name': '生成中文姓名',
    'generate_chinese_phone': '生成手机号',
    'generate_chinese_email': '生成邮箱',
    'generate_chinese_address': '生成中文地址',
    'generate_id_card': '生成身份证号',
    'generate_company_name': '生成公司名称',
    'generate_bank_card': '生成银行卡号',
    'generate_hk_id_card': '生成香港身份证',
    'generate_business_license': '生成营业执照号',
    'generate_coordinates': '生成经纬度',
    'generate_user_profile': '生成用户档案',
    
    # JSON工具
    'format_json': 'JSON格式化',
    'validate_json': 'JSON校验',
    'json_diff_enhanced': 'JSON对比',
    'jsonpath_query': 'JSONPath查询',
    'json_flatten': 'JSON扁平化',
    'json_path_list': 'JSON路径列表',
    'json_to_xml': 'JSON转XML',
    'xml_to_json': 'XML转JSON',
    'json_to_yaml': 'JSON转YAML',
    'yaml_to_json': 'YAML转JSON',
    
    # 字符工具
    'text_diff': '文本对比',
    'regex_test': '正则测试',
    'remove_whitespace': '去除空格换行',
    'replace_string': '字符串替换',
    'escape_string': '字符串转义',
    'unescape_string': '字符串反转义',
    'word_count': '字数统计',
    'case_convert': '大小写转换',
    'string_format': '字符串格式化',
    
    # 编码工具
    'generate_barcode': '生成条形码',
    'generate_qrcode': '生成二维码',
    'decode_qrcode': '二维码解析',
    'timestamp_convert': '时间戳转换',
    'base_convert': '进制转换',
    'unicode_convert': 'Unicode转换',
    'ascii_convert': 'ASCII转换',
    'color_convert': '颜色值转换',
    'url_encode': 'URL编码',
    'url_decode': 'URL解码',
    'jwt_decode': 'JWT解码',
    'image_to_base64': '图片转Base64',
    'base64_to_image': 'Base64转图片',
    'base64_encode': 'Base64编码',
    'base64_decode': 'Base64解码',
    
    # 随机工具
    'random_int': '随机整数',
    'random_float': '随机浮点数',
    'random_string': '随机字符串',
    'random_uuid': '随机UUID',
    'random_boolean': '随机布尔值',
    'random_mac_address': '随机MAC地址',
    'random_ip_address': '随机IP地址',
    'random_date': '随机日期',
    'random_password': '随机密码',
    'random_color': '随机颜色',
    'random_sequence': '随机序列数据',
    
    # 加密工具
    'md5_hash': 'MD5加密',
    'sha1_hash': 'SHA1加密',
    'sha256_hash': 'SHA256加密',
    'sha512_hash': 'SHA512加密',
    'hash_comparison': '哈希值比对',
    'aes_encrypt': 'AES加密',
    'aes_decrypt': 'AES解密',
    'password_strength': '密码强度分析',
    'generate_salt': '随机盐值',
    
    # Crontab工具
    'generate_expression': '生成Crontab表达式',
    'parse_expression': '解析Crontab表达式',
    'get_next_runs': '获取下次执行时间',
    'validate_expression': '验证Crontab表达式',
}

# 创建反向映射：从显示名称到内部名称
DISPLAY_TO_TOOL_MAP = {v: k for k, v in TOOL_DISPLAY_MAP.items()}


class DataFactoryService:
    """数据工厂服务类"""
    
    # 工具分类显示名称映射
    CATEGORY_DISPLAY_MAP = {
        'test_data': '测试数据',
        'json': 'JSON工具',
        'string': '字符工具',
        'encoding': '编码工具',
        'random': '随机工具',
        'encryption': '加密工具',
        'crontab': 'Crontab工具'
    }
    
    @classmethod
    async def get_categories_with_tools(cls) -> Dict[str, Any]:
        """
        获取所有工具分类和工具列表
        
        Returns:
            包含分类和工具的字典
        """
        try:
            categories = get_categories()
            tool_list = get_tool_list()
            
            # 为每个分类添加工具列表
            for category in categories:
                category['tools'] = [
                    tool for tool in tool_list 
                    if tool['scenario'] == category['scenario']
                ]
            
            return {
                'categories': categories,
                'total_tools': len(tool_list)
            }
        except Exception as e:
            logger.error(f"[数据工厂] 获取工具分类失败: {str(e)}")
            raise
    
    @classmethod
    async def execute_tool(
        cls,
        tool_name: str,
        tool_category: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            tool_category: 工具分类
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        try:
            logger.info(f"[数据工厂] 执行工具: {tool_name}, 分类: {tool_category}")
            
            # 根据分类调用对应的工具
            if tool_category == 'test_data':
                from .tools.test_data_tools import TestDataTools
                return await cls._execute_test_data_tool(tool_name, input_data)
            elif tool_category == 'json':
                from .tools.json_tools import JsonTools
                return await cls._execute_json_tool(tool_name, input_data)
            elif tool_category == 'string':
                from .tools.string_tools import StringTools
                return await cls._execute_string_tool(tool_name, input_data)
            elif tool_category == 'encoding':
                from .tools.encoding_tools import EncodingTools
                return await cls._execute_encoding_tool(tool_name, input_data)
            elif tool_category == 'random':
                from .tools.random_tools import RandomTools
                return await cls._execute_random_tool(tool_name, input_data)
            elif tool_category == 'encryption':
                from .tools.encryption_tools import EncryptionTools
                return await cls._execute_encryption_tool(tool_name, input_data)
            elif tool_category == 'crontab':
                from .tools.crontab_tools import CrontabTools
                return await cls._execute_crontab_tool(tool_name, input_data)
            else:
                return {'error': f'不支持的工具分类: {tool_category}'}
                
        except Exception as e:
            logger.error(f"[数据工厂] 工具执行失败: {str(e)}")
            return {'error': f'工具执行失败: {str(e)}'}
    
    @classmethod
    async def _execute_test_data_tool(cls, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试数据工具"""
        from .tools.test_data_tools import TestDataTools
        
        tool_mapping = {
            'generate_chinese_name': TestDataTools.generate_chinese_name,
            'generate_chinese_phone': TestDataTools.generate_chinese_phone,
            'generate_chinese_email': TestDataTools.generate_chinese_email,
            'generate_chinese_address': TestDataTools.generate_chinese_address,
            'generate_id_card': TestDataTools.generate_id_card,
            'generate_company_name': TestDataTools.generate_company_name,
            'generate_bank_card': TestDataTools.generate_bank_card,
            'generate_hk_id_card': TestDataTools.generate_hk_id_card,
            'generate_business_license': TestDataTools.generate_business_license,
            'generate_coordinates': TestDataTools.generate_coordinates,
            'generate_user_profile': TestDataTools.generate_user_profile
        }
        
        if tool_name not in tool_mapping:
            return {'error': f'不支持的测试数据工具: {tool_name}'}
        
        return tool_mapping[tool_name](**input_data)
    
    @classmethod
    async def _execute_json_tool(cls, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行JSON工具"""
        from .tools.json_tools import JsonTools
        
        try:
            if tool_name == 'format_json':
                return JsonTools.format_json(
                    json_str=input_data.get('json_str', ''),
                    indent=input_data.get('indent', 2),
                    sort_keys=input_data.get('sort_keys', False),
                    compress=input_data.get('compress', False)
                )
            elif tool_name == 'validate_json':
                return JsonTools.validate_json(
                    json_str=input_data.get('json_str', '')
                )
            elif tool_name == 'json_diff_enhanced':
                return JsonTools.json_diff_enhanced(
                    json_str1=input_data.get('json_str1', ''),
                    json_str2=input_data.get('json_str2', ''),
                    ignore_whitespace=input_data.get('ignore_whitespace', True)
                )
            elif tool_name == 'jsonpath_query':
                return JsonTools.jsonpath_query(
                    json_str=input_data.get('json_str', ''),
                    jsonpath_expr=input_data.get('jsonpath', '')
                )
            elif tool_name == 'json_flatten':
                return JsonTools.json_flatten(
                    json_str=input_data.get('json_str', ''),
                    separator=input_data.get('separator', '.')
                )
            elif tool_name == 'json_path_list':
                return JsonTools.json_path_list(
                    json_str=input_data.get('json_str', '')
                )
            elif tool_name == 'json_to_xml':
                return JsonTools.json_to_xml(
                    json_str=input_data.get('json_str', ''),
                    root_tag=input_data.get('root_tag', 'root')
                )
            elif tool_name == 'xml_to_json':
                return JsonTools.xml_to_json(
                    xml_str=input_data.get('xml_str', '')
                )
            elif tool_name == 'json_to_yaml':
                return JsonTools.json_to_yaml(
                    json_str=input_data.get('json_str', '')
                )
            elif tool_name == 'yaml_to_json':
                return JsonTools.yaml_to_json(
                    yaml_str=input_data.get('yaml_str', '')
                )
            else:
                return {'error': f'不支持的JSON工具: {tool_name}'}
        except Exception as e:
            return {'error': f'JSON工具执行失败: {str(e)}'}
    
    @classmethod
    async def _execute_string_tool(cls, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行字符工具"""
        from .tools.string_tools import StringTools
        
        try:
            if tool_name == 'text_diff':
                return StringTools.text_diff(
                    text1=input_data.get('text1', ''),
                    text2=input_data.get('text2', '')
                )
            elif tool_name == 'regex_test':
                return StringTools.regex_test(
                    pattern=input_data.get('pattern', ''),
                    text=input_data.get('text', ''),
                    flags=input_data.get('flags', '')
                )
            elif tool_name == 'remove_whitespace':
                return StringTools.remove_whitespace(
                    text=input_data.get('text', '')
                )
            elif tool_name == 'replace_string':
                return StringTools.replace_string(
                    text=input_data.get('text', ''),
                    old_str=input_data.get('old_str', ''),
                    new_str=input_data.get('new_str', ''),
                    is_regex=input_data.get('is_regex', False)
                )
            elif tool_name == 'escape_string':
                return StringTools.escape_string(
                    text=input_data.get('text', ''),
                    escape_type=input_data.get('escape_type', 'json')
                )
            elif tool_name == 'unescape_string':
                return StringTools.unescape_string(
                    text=input_data.get('text', ''),
                    unescape_type=input_data.get('unescape_type', 'json')
                )
            elif tool_name == 'word_count':
                return StringTools.word_count(
                    text=input_data.get('text', '')
                )
            elif tool_name == 'case_convert':
                return StringTools.case_convert(
                    text=input_data.get('text', ''),
                    convert_type=input_data.get('case_type', 'upper')
                )
            elif tool_name == 'string_format':
                return StringTools.string_format(
                    text=input_data.get('text', ''),
                    format_type=input_data.get('format_type', 'trim')
                )
            else:
                return {'error': f'不支持的字符工具: {tool_name}'}
        except Exception as e:
            return {'error': f'字符工具执行失败: {str(e)}'}
    
    @classmethod
    async def _execute_encoding_tool(cls, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行编码工具"""
        from .tools.encoding_tools import EncodingTools
        
        try:
            if tool_name == 'generate_barcode':
                return EncodingTools.generate_barcode(
                    data=input_data.get('text', ''),
                    barcode_type=input_data.get('barcode_type', 'code128'),
                    save_to_static=input_data.get('save_to_static', True)
                )
            elif tool_name == 'generate_qrcode':
                return EncodingTools.generate_qrcode(
                    data=input_data.get('text', ''),
                    image_size=input_data.get('size', 300),
                    border=input_data.get('border', 4),
                    save_to_static=input_data.get('save_to_static', True)
                )
            elif tool_name == 'decode_qrcode':
                return EncodingTools.decode_qrcode(
                    image_data=input_data.get('image_path', ''),
                    image_format=input_data.get('image_format', 'png')
                )
            elif tool_name == 'timestamp_convert':
                return EncodingTools.timestamp_convert(
                    timestamp=input_data.get('timestamp', 0),
                    convert_type=input_data.get('format_type', 'to_datetime'),
                    timestamp_unit=input_data.get('timestamp_unit', 'auto')
                )
            elif tool_name == 'base_convert':
                return EncodingTools.base_convert(
                    number=input_data.get('num_str', ''),
                    from_base=input_data.get('from_base', 10),
                    to_base=input_data.get('to_base', 16)
                )
            elif tool_name == 'unicode_convert':
                return EncodingTools.unicode_convert(
                    text=input_data.get('text', ''),
                    convert_type=input_data.get('convert_type', 'to_unicode')
                )
            elif tool_name == 'ascii_convert':
                return EncodingTools.ascii_convert(
                    text=input_data.get('text', ''),
                    convert_type=input_data.get('convert_type', 'to_ascii')
                )
            elif tool_name == 'color_convert':
                return EncodingTools.color_convert(
                    color=input_data.get('color_value', ''),
                    from_type=input_data.get('from_format', 'hex'),
                    to_type=input_data.get('to_format', 'rgb')
                )
            elif tool_name == 'url_encode':
                return EncodingTools.url_encode(
                    text=input_data.get('text', ''),
                    encoding=input_data.get('encoding', 'utf-8')
                )
            elif tool_name == 'url_decode':
                return EncodingTools.url_decode(
                    encoded_text=input_data.get('encoded_text', ''),
                    encoding=input_data.get('encoding', 'utf-8')
                )
            elif tool_name == 'jwt_decode':
                return EncodingTools.jwt_decode(
                    token=input_data.get('token', ''),
                    verify=input_data.get('verify', False)
                )
            elif tool_name == 'image_to_base64':
                return EncodingTools.image_to_base64(
                    image_data=input_data.get('image_path', ''),
                    image_format=input_data.get('image_format', 'png')
                )
            elif tool_name == 'base64_to_image':
                return EncodingTools.base64_to_image(
                    base64_data=input_data.get('base64_str', ''),
                    output_format=input_data.get('output_format', 'png')
                )
            elif tool_name == 'base64_encode':
                return EncodingTools.base64_encode(
                    text=input_data.get('text', ''),
                    encoding=input_data.get('encoding', 'utf-8')
                )
            elif tool_name == 'base64_decode':
                return EncodingTools.base64_decode(
                    encoded_text=input_data.get('encoded_text', ''),
                    encoding=input_data.get('encoding', 'utf-8')
                )
            else:
                return {'error': f'不支持的编码工具: {tool_name}'}
        except Exception as e:
            return {'error': f'编码工具执行失败: {str(e)}'}
    
    @classmethod
    async def _execute_random_tool(cls, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行随机工具"""
        from .tools.random_tools import RandomTools
        
        try:
            if tool_name == 'random_int':
                return RandomTools.random_int(
                    min_val=input_data.get('min_val', 0),
                    max_val=input_data.get('max_val', 100),
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_float':
                return RandomTools.random_float(
                    min_val=input_data.get('min_val', 0.0),
                    max_val=input_data.get('max_val', 1.0),
                    precision=input_data.get('precision', 2),
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_string':
                # 转换参数格式
                char_type = 'all'
                if input_data.get('include_letters') and input_data.get('include_numbers'):
                    char_type = 'all'
                elif input_data.get('include_letters'):
                    char_type = 'letters'
                elif input_data.get('include_numbers'):
                    char_type = 'numbers'
                
                return RandomTools.random_string(
                    length=input_data.get('length', 10),
                    char_type=char_type,
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_uuid':
                return RandomTools.random_uuid(
                    version=input_data.get('version', 4),
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_boolean':
                return RandomTools.random_boolean(
                    count=input_data.get('count', 1),
                    true_probability=input_data.get('true_probability', 0.5)
                )
            elif tool_name == 'random_mac_address':
                return RandomTools.random_mac_address(
                    separator=input_data.get('format_type', ':'),
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_ip_address':
                return RandomTools.random_ip_address(
                    ip_version=4 if input_data.get('ip_type', 'ipv4') == 'ipv4' else 6,
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_date':
                return RandomTools.random_date(
                    start_date=input_data.get('start_date', '2020-01-01'),
                    end_date=input_data.get('end_date', '2030-12-31'),
                    count=input_data.get('count', 1),
                    date_format=input_data.get('format_str', '%Y-%m-%d')
                )
            elif tool_name == 'random_password':
                return RandomTools.random_password(
                    length=input_data.get('length', 12),
                    include_uppercase=input_data.get('include_uppercase', True),
                    include_lowercase=input_data.get('include_lowercase', True),
                    include_digits=input_data.get('include_numbers', True),
                    include_special=input_data.get('include_symbols', True),
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_color':
                return RandomTools.random_color(
                    color_format=input_data.get('format_type', 'hex'),
                    count=input_data.get('count', 1)
                )
            elif tool_name == 'random_sequence':
                # 为random_sequence生成一个默认序列
                sequence_type = input_data.get('sequence_type', 'list')
                length = input_data.get('length', 10)
                min_val = input_data.get('min_val', 1)
                max_val = input_data.get('max_val', 100)
                
                if sequence_type == 'list':
                    sequence = list(range(min_val, min_val + length))
                else:
                    sequence = list(range(min_val, max_val + 1))
                
                return RandomTools.random_sequence(
                    sequence=sequence,
                    count=input_data.get('count', 1),
                    unique=input_data.get('unique', False)
                )
            else:
                return {'error': f'不支持的随机工具: {tool_name}'}
        except Exception as e:
            return {'error': f'随机工具执行失败: {str(e)}'}
    
    @classmethod
    async def _execute_encryption_tool(cls, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行加密工具"""
        from .tools.encryption_tools import EncryptionTools
        
        try:
            if tool_name == 'md5_hash':
                return EncryptionTools.md5_hash(
                    text=input_data.get('text', '')
                )
            elif tool_name == 'sha1_hash':
                return EncryptionTools.sha1_hash(
                    text=input_data.get('text', '')
                )
            elif tool_name == 'sha256_hash':
                return EncryptionTools.sha256_hash(
                    text=input_data.get('text', '')
                )
            elif tool_name == 'sha512_hash':
                return EncryptionTools.sha512_hash(
                    text=input_data.get('text', '')
                )
            elif tool_name == 'hash_comparison':
                return EncryptionTools.hash_comparison(
                    text=input_data.get('text', ''),
                    hash_value=input_data.get('hash1', ''),
                    algorithm=input_data.get('hash_type', 'auto')
                )
            elif tool_name == 'aes_encrypt':
                return EncryptionTools.aes_encrypt(
                    text=input_data.get('text', ''),
                    password=input_data.get('key', ''),
                    mode=input_data.get('mode', 'CBC')
                )
            elif tool_name == 'aes_decrypt':
                return EncryptionTools.aes_decrypt(
                    encrypted_text=input_data.get('encrypted_text', ''),
                    password=input_data.get('key', ''),
                    mode=input_data.get('mode', 'CBC')
                )
            elif tool_name == 'password_strength':
                return EncryptionTools.password_strength(
                    password=input_data.get('password', '')
                )
            elif tool_name == 'generate_salt':
                return EncryptionTools.generate_salt(
                    length=input_data.get('length', 16),
                    encoding=input_data.get('encoding', 'hex')
                )
            else:
                return {'error': f'不支持的加密工具: {tool_name}'}
        except Exception as e:
            return {'error': f'加密工具执行失败: {str(e)}'}
    
    @classmethod
    async def _execute_crontab_tool(cls, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行Crontab工具"""
        from .tools.crontab_tools import CrontabTools
        
        tool_mapping = {
            'generate_expression': CrontabTools.generate_expression,
            'parse_expression': CrontabTools.parse_expression,
            'get_next_runs': CrontabTools.get_next_runs,
            'validate_expression': CrontabTools.validate_expression
        }
        
        if tool_name not in tool_mapping:
            return {'error': f'不支持的Crontab工具: {tool_name}'}
        
        return tool_mapping[tool_name](**input_data)
    
    @classmethod
    async def save_record(
        cls,
        db: AsyncSession,
        user_id: int,
        tool_name: str,
        tool_category: str,
        tool_scenario: str,
        input_data: Optional[Dict[str, Any]],
        output_data: Dict[str, Any],
        is_saved: bool = True,
        tags: Optional[List[str]] = None
    ) -> DataFactoryRecord:
        """
        保存工具使用记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            tool_name: 工具名称
            tool_category: 工具分类
            tool_scenario: 使用场景
            input_data: 输入数据
            output_data: 输出数据
            is_saved: 是否保存
            tags: 标签列表
            
        Returns:
            保存的记录
        """
        try:
            # 处理标签：去除空格并过滤空标签
            processed_tags = None
            if tags:
                processed_tags = [tag.strip() for tag in tags if tag and tag.strip()]
                if not processed_tags:
                    processed_tags = None
            
            record = DataFactoryRecord(
                user_id=user_id,
                tool_name=tool_name,
                tool_category=tool_category,
                tool_scenario=tool_scenario,
                input_data=input_data,
                output_data=output_data,
                is_saved=is_saved,
                tags=processed_tags,
                created_by=user_id,
                updated_by=user_id
            )
            
            db.add(record)
            await db.commit()
            await db.refresh(record)
            
            logger.info(f"[数据工厂] 保存记录成功: ID={record.id}, 工具={tool_name}")
            return record
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[数据工厂] 保存记录失败: {str(e)}")
            raise
    
    @classmethod
    async def get_records(
        cls,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        tool_category: Optional[str] = None,
        tool_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> tuple[List[DataFactoryRecord], int]:
        """
        获取用户的工具使用记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            tool_category: 工具分类过滤
            tool_name: 工具名称过滤
            tags: 标签过滤列表
            
        Returns:
            (记录列表, 总数)
        """
        try:
            # 构建查询
            query = select(DataFactoryRecord).where(
                DataFactoryRecord.user_id == user_id,
                DataFactoryRecord.enabled_flag == True
            )
            
            # 添加过滤条件
            if tool_category:
                query = query.where(DataFactoryRecord.tool_category == tool_category)
            if tool_name:
                # 工具名称搜索：支持内部名称和显示名称搜索
                tool_name_conditions = []
                
                # 1. 搜索内部工具名称
                tool_name_conditions.append(DataFactoryRecord.tool_name.like(f'%{tool_name}%'))
                
                # 2. 如果输入的是中文显示名称，转换为内部名称进行搜索
                matching_internal_names = []
                for internal_name, display_name in TOOL_DISPLAY_MAP.items():
                    if tool_name.lower() in display_name.lower() or tool_name in display_name:
                        matching_internal_names.append(internal_name)
                
                # 3. 添加匹配的内部名称条件
                for internal_name in matching_internal_names:
                    tool_name_conditions.append(DataFactoryRecord.tool_name == internal_name)
                
                # 4. 使用OR条件组合所有搜索条件
                if tool_name_conditions:
                    query = query.where(or_(*tool_name_conditions))
            if tags:
                # 标签筛选：记录的标签列表中包含任一指定标签
                tag_conditions = []
                for tag in tags:
                    # 使用模糊匹配来处理可能的空格和格式差异
                    # 同时匹配带引号和不带引号的格式
                    condition1 = DataFactoryRecord.tags.like(f'%"{tag.strip()}"%')
                    condition2 = DataFactoryRecord.tags.like(f'%{tag.strip()}%')
                    tag_conditions.append(or_(condition1, condition2))
                
                if tag_conditions:
                    # 使用OR条件，只要包含任一标签即可
                    query = query.where(or_(*tag_conditions))
            
            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # 分页查询
            query = query.order_by(desc(DataFactoryRecord.creation_date))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(query)
            records = result.scalars().all()
            
            return list(records), total
            
        except Exception as e:
            logger.error(f"[数据工厂] 获取记录列表失败: {str(e)}")
            raise
    
    @classmethod
    async def delete_record(
        cls,
        db: AsyncSession,
        record_id: int,
        user_id: int
    ) -> bool:
        """
        软删除记录
        
        Args:
            db: 数据库会话
            record_id: 记录ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            query = select(DataFactoryRecord).where(
                DataFactoryRecord.id == record_id,
                DataFactoryRecord.user_id == user_id
            )
            result = await db.execute(query)
            record = result.scalar_one_or_none()
            
            if not record:
                return False
            
            # 软删除
            record.enabled_flag = False
            record.updated_by = user_id
            record.updation_date = datetime.now()
            
            await db.commit()
            logger.info(f"[数据工厂] 软删除记录成功: ID={record_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[数据工厂] 软删除记录失败: {str(e)}")
            raise
    
    @classmethod
    async def hard_delete_record(
        cls,
        db: AsyncSession,
        record_id: int,
        user_id: int
    ) -> bool:
        """
        硬删除记录
        
        Args:
            db: 数据库会话
            record_id: 记录ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            query = select(DataFactoryRecord).where(
                DataFactoryRecord.id == record_id,
                DataFactoryRecord.user_id == user_id
            )
            result = await db.execute(query)
            record = result.scalar_one_or_none()
            
            if not record:
                return False
            
            # 硬删除
            delete_query = delete(DataFactoryRecord).where(
                DataFactoryRecord.id == record_id,
                DataFactoryRecord.user_id == user_id
            )
            await db.execute(delete_query)
            await db.commit()
            
            logger.info(f"[数据工厂] 硬删除记录成功: ID={record_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[数据工厂] 硬删除记录失败: {str(e)}")
            raise
    
    @classmethod
    async def batch_hard_delete_records(
        cls,
        db: AsyncSession,
        record_ids: List[int],
        user_id: int
    ) -> int:
        """
        批量硬删除记录
        
        Args:
            db: 数据库会话
            record_ids: 记录ID列表
            user_id: 用户ID
            
        Returns:
            成功删除的记录数量
        """
        try:
            # 先查询用户拥有的记录数量
            query = select(func.count()).where(
                DataFactoryRecord.id.in_(record_ids),
                DataFactoryRecord.user_id == user_id
            )
            result = await db.execute(query)
            count = result.scalar()
            
            if count == 0:
                return 0
            
            # 批量硬删除
            delete_query = delete(DataFactoryRecord).where(
                DataFactoryRecord.id.in_(record_ids),
                DataFactoryRecord.user_id == user_id
            )
            await db.execute(delete_query)
            await db.commit()
            
            logger.info(f"[数据工厂] 批量硬删除记录成功: 删除数量={count}")
            return count
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[数据工厂] 批量硬删除记录失败: {str(e)}")
            raise
    
    @classmethod
    async def get_statistics(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取使用统计
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            # 获取用户的所有记录
            query = select(DataFactoryRecord).where(
                DataFactoryRecord.user_id == user_id,
                DataFactoryRecord.enabled_flag == True
            )
            result = await db.execute(query)
            records = result.scalars().all()
            
            # 总记录数
            total_records = len(records)
            
            # 按分类统计
            category_stats = {}
            for category_key, category_name in cls.CATEGORY_DISPLAY_MAP.items():
                count = sum(1 for r in records if r.tool_category == category_key)
                category_stats[category_name] = count
            
            # 按场景统计（与分类相同）
            scenario_stats = category_stats.copy()
            
            # 最近使用（前10条）
            recent_records = sorted(records, key=lambda x: x.creation_date, reverse=True)[:10]
            recent_tools = [
                {
                    'tool_name': r.tool_name,
                    'tool_category_display': cls.CATEGORY_DISPLAY_MAP.get(r.tool_category, r.tool_category),
                    'tool_scenario_display': cls.CATEGORY_DISPLAY_MAP.get(r.tool_scenario, r.tool_scenario),
                    'created_at': r.creation_date
                }
                for r in recent_records
            ]
            
            return {
                'total_records': total_records,
                'category_stats': category_stats,
                'scenario_stats': scenario_stats,
                'recent_tools': recent_tools
            }
            
        except Exception as e:
            logger.error(f"[数据工厂] 获取统计信息失败: {str(e)}")
            raise
    
    @classmethod
    async def get_tags(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> List[str]:
        """
        获取用户的所有标签
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            标签列表
        """
        try:
            query = select(DataFactoryRecord.tags).where(
                DataFactoryRecord.user_id == user_id,
                DataFactoryRecord.enabled_flag == True,
                DataFactoryRecord.tags.isnot(None)
            )
            result = await db.execute(query)
            all_tags = result.scalars().all()
            
            # 提取所有唯一标签
            tag_set = set()
            for tags in all_tags:
                if tags and isinstance(tags, list):
                    tag_set.update(tags)
            
            return sorted(list(tag_set))
            
        except Exception as e:
            logger.error(f"[数据工厂] 获取标签列表失败: {str(e)}")
            raise
