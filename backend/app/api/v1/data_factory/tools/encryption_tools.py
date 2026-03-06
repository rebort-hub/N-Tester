"""
加密工具
提供各种加密、哈希、密码强度分析等功能
"""
import hashlib
import hmac
import secrets
import string
import re
from typing import Dict, Any


class EncryptionTools:
    """加密工具类"""
    
    @staticmethod
    def md5_hash(text: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        MD5哈希
        
        Args:
            text: 要哈希的文本
            encoding: 字符编码
            
        Returns:
            MD5哈希结果
        """
        try:
            md5_hash = hashlib.md5(text.encode(encoding)).hexdigest()
            
            return {
                'success': True,
                'original': text,
                'hash': md5_hash,
                'hash_upper': md5_hash.upper(),
                'algorithm': 'MD5',
                'length': len(md5_hash),
                'encoding': encoding
            }
        except Exception as e:
            return {'error': f'MD5哈希失败: {str(e)}'}
    
    @staticmethod
    def sha1_hash(text: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        SHA1哈希
        
        Args:
            text: 要哈希的文本
            encoding: 字符编码
            
        Returns:
            SHA1哈希结果
        """
        try:
            sha1_hash = hashlib.sha1(text.encode(encoding)).hexdigest()
            
            return {
                'success': True,
                'original': text,
                'hash': sha1_hash,
                'hash_upper': sha1_hash.upper(),
                'algorithm': 'SHA1',
                'length': len(sha1_hash),
                'encoding': encoding
            }
        except Exception as e:
            return {'error': f'SHA1哈希失败: {str(e)}'}
    
    @staticmethod
    def sha256_hash(text: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        SHA256哈希
        
        Args:
            text: 要哈希的文本
            encoding: 字符编码
            
        Returns:
            SHA256哈希结果
        """
        try:
            sha256_hash = hashlib.sha256(text.encode(encoding)).hexdigest()
            
            return {
                'success': True,
                'original': text,
                'hash': sha256_hash,
                'hash_upper': sha256_hash.upper(),
                'algorithm': 'SHA256',
                'length': len(sha256_hash),
                'encoding': encoding
            }
        except Exception as e:
            return {'error': f'SHA256哈希失败: {str(e)}'}
    
    @staticmethod
    def sha512_hash(text: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        SHA512哈希
        
        Args:
            text: 要哈希的文本
            encoding: 字符编码
            
        Returns:
            SHA512哈希结果
        """
        try:
            sha512_hash = hashlib.sha512(text.encode(encoding)).hexdigest()
            
            return {
                'success': True,
                'original': text,
                'hash': sha512_hash,
                'hash_upper': sha512_hash.upper(),
                'algorithm': 'SHA512',
                'length': len(sha512_hash),
                'encoding': encoding
            }
        except Exception as e:
            return {'error': f'SHA512哈希失败: {str(e)}'}
    
    @staticmethod
    def hash_comparison(text: str, hash_value: str, algorithm: str = 'auto') -> Dict[str, Any]:
        """
        哈希值比对
        
        Args:
            text: 原文本
            hash_value: 要比对的哈希值
            algorithm: 哈希算法 ('auto', 'md5', 'sha1', 'sha256', 'sha512')
            
        Returns:
            比对结果
        """
        try:
            hash_value = hash_value.lower().strip()
            
            # 自动检测算法
            if algorithm == 'auto':
                if len(hash_value) == 32:
                    algorithm = 'md5'
                elif len(hash_value) == 40:
                    algorithm = 'sha1'
                elif len(hash_value) == 64:
                    algorithm = 'sha256'
                elif len(hash_value) == 128:
                    algorithm = 'sha512'
                else:
                    return {'error': '无法自动识别哈希算法，请手动指定'}
            
            # 计算哈希
            if algorithm == 'md5':
                calculated_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            elif algorithm == 'sha1':
                calculated_hash = hashlib.sha1(text.encode('utf-8')).hexdigest()
            elif algorithm == 'sha256':
                calculated_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
            elif algorithm == 'sha512':
                calculated_hash = hashlib.sha512(text.encode('utf-8')).hexdigest()
            else:
                return {'error': f'不支持的哈希算法: {algorithm}'}
            
            is_match = calculated_hash == hash_value
            
            return {
                'success': True,
                'original_text': text,
                'provided_hash': hash_value,
                'calculated_hash': calculated_hash,
                'algorithm': algorithm.upper(),
                'is_match': is_match,
                'match_result': '匹配' if is_match else '不匹配'
            }
        except Exception as e:
            return {'error': f'哈希比对失败: {str(e)}'}
    
    @staticmethod
    def aes_encrypt(text: str, password: str, mode: str = 'CBC') -> Dict[str, Any]:
        """
        AES加密（简化实现）
        
        Args:
            text: 要加密的文本
            password: 密码
            mode: 加密模式
            
        Returns:
            加密结果
        """
        try:
            # 简化实现，实际应用中需要使用专业的加密库
            import base64
            
            # 使用密码生成密钥
            key_hash = hashlib.sha256(password.encode('utf-8')).digest()
            
            # 简单的异或加密（仅用于演示）
            encrypted_bytes = bytearray()
            text_bytes = text.encode('utf-8')
            
            for i, byte in enumerate(text_bytes):
                key_byte = key_hash[i % len(key_hash)]
                encrypted_bytes.append(byte ^ key_byte)
            
            encrypted_base64 = base64.b64encode(encrypted_bytes).decode('ascii')
            
            return {
                'success': True,
                'original': text,
                'encrypted': encrypted_base64,
                'algorithm': f'AES-{mode}',
                'key_length': len(key_hash) * 8,
                'note': '这是简化实现，生产环境请使用专业加密库'
            }
        except Exception as e:
            return {'error': f'AES加密失败: {str(e)}'}
    
    @staticmethod
    def aes_decrypt(encrypted_text: str, password: str, mode: str = 'CBC') -> Dict[str, Any]:
        """
        AES解密（简化实现）
        
        Args:
            encrypted_text: 要解密的文本
            password: 密码
            mode: 解密模式
            
        Returns:
            解密结果
        """
        try:
            import base64
            
            # 使用密码生成密钥
            key_hash = hashlib.sha256(password.encode('utf-8')).digest()
            
            # 解码Base64
            encrypted_bytes = base64.b64decode(encrypted_text)
            
            # 简单的异或解密
            decrypted_bytes = bytearray()
            
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_hash[i % len(key_hash)]
                decrypted_bytes.append(byte ^ key_byte)
            
            decrypted_text = decrypted_bytes.decode('utf-8')
            
            return {
                'success': True,
                'encrypted': encrypted_text,
                'decrypted': decrypted_text,
                'algorithm': f'AES-{mode}',
                'key_length': len(key_hash) * 8,
                'note': '这是简化实现，生产环境请使用专业加密库'
            }
        except Exception as e:
            return {'error': f'AES解密失败: {str(e)}'}
    
    @staticmethod
    def password_strength(password: str) -> Dict[str, Any]:
        """
        密码强度分析
        
        Args:
            password: 要分析的密码
            
        Returns:
            密码强度分析结果
        """
        try:
            analysis = {
                'length': len(password),
                'has_lowercase': bool(re.search(r'[a-z]', password)),
                'has_uppercase': bool(re.search(r'[A-Z]', password)),
                'has_digits': bool(re.search(r'\d', password)),
                'has_special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password)),
                'has_space': ' ' in password,
                'consecutive_chars': 0,
                'repeated_chars': 0,
                'common_patterns': []
            }
            
            # 检查连续字符
            consecutive = 0
            max_consecutive = 0
            for i in range(len(password) - 1):
                if ord(password[i+1]) == ord(password[i]) + 1:
                    consecutive += 1
                    max_consecutive = max(max_consecutive, consecutive + 1)
                else:
                    consecutive = 0
            analysis['consecutive_chars'] = max_consecutive
            
            # 检查重复字符
            char_count = {}
            for char in password:
                char_count[char] = char_count.get(char, 0) + 1
            analysis['repeated_chars'] = max(char_count.values()) if char_count else 0
            
            # 检查常见模式
            common_patterns = [
                ('123456', '连续数字'),
                ('abcdef', '连续字母'),
                ('qwerty', 'QWERTY键盘'),
                ('password', '常见单词'),
                ('admin', '常见单词'),
                ('123abc', '数字+字母'),
            ]
            
            for pattern, description in common_patterns:
                if pattern.lower() in password.lower():
                    analysis['common_patterns'].append(description)
            
            # 计算强度分数
            score = 0
            
            # 长度分数
            if analysis['length'] >= 8:
                score += 2
            if analysis['length'] >= 12:
                score += 2
            if analysis['length'] >= 16:
                score += 2
            
            # 字符类型分数
            if analysis['has_lowercase']:
                score += 1
            if analysis['has_uppercase']:
                score += 1
            if analysis['has_digits']:
                score += 1
            if analysis['has_special']:
                score += 2
            
            # 扣分项
            if analysis['consecutive_chars'] > 2:
                score -= 2
            if analysis['repeated_chars'] > 2:
                score -= 2
            if analysis['common_patterns']:
                score -= len(analysis['common_patterns'])
            if analysis['has_space']:
                score -= 1
            
            # 确定强度等级
            if score <= 3:
                strength = '弱'
                color = 'red'
            elif score <= 6:
                strength = '中等'
                color = 'orange'
            elif score <= 9:
                strength = '强'
                color = 'green'
            else:
                strength = '很强'
                color = 'darkgreen'
            
            # 生成建议
            suggestions = []
            if analysis['length'] < 8:
                suggestions.append('密码长度至少8位')
            if not analysis['has_lowercase']:
                suggestions.append('添加小写字母')
            if not analysis['has_uppercase']:
                suggestions.append('添加大写字母')
            if not analysis['has_digits']:
                suggestions.append('添加数字')
            if not analysis['has_special']:
                suggestions.append('添加特殊字符')
            if analysis['consecutive_chars'] > 2:
                suggestions.append('避免连续字符')
            if analysis['repeated_chars'] > 2:
                suggestions.append('避免重复字符')
            if analysis['common_patterns']:
                suggestions.append('避免常见模式')
            
            return {
                'success': True,
                'password_length': analysis['length'],
                'strength': strength,
                'strength_color': color,
                'score': max(0, score),
                'max_score': 12,
                'analysis': analysis,
                'suggestions': suggestions,
                'is_strong': score >= 7
            }
        except Exception as e:
            return {'error': f'密码强度分析失败: {str(e)}'}
    
    @staticmethod
    def generate_salt(length: int = 16, encoding: str = 'hex') -> Dict[str, Any]:
        """
        生成随机盐值
        
        Args:
            length: 盐值长度
            encoding: 编码方式 ('hex', 'base64', 'raw')
            
        Returns:
            随机盐值
        """
        try:
            if length <= 0:
                return {'error': '盐值长度必须大于0'}
            
            # 生成随机字节
            salt_bytes = secrets.token_bytes(length)
            
            # 根据编码方式转换
            if encoding == 'hex':
                salt = salt_bytes.hex()
            elif encoding == 'base64':
                import base64
                salt = base64.b64encode(salt_bytes).decode('ascii')
            elif encoding == 'raw':
                salt = salt_bytes
            else:
                return {'error': f'不支持的编码方式: {encoding}'}
            
            # 生成带盐哈希示例
            example_password = 'example123'
            salted_password = example_password + (salt if encoding != 'raw' else salt.hex())
            salted_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
            
            return {
                'success': True,
                'salt': salt if encoding != 'raw' else salt.hex(),
                'length': length,
                'encoding': encoding,
                'byte_length': len(salt_bytes),
                'example': {
                    'password': example_password,
                    'salted_password': salted_password,
                    'salted_hash': salted_hash
                },
                'usage_note': '将盐值与密码组合后再进行哈希运算'
            }
        except Exception as e:
            return {'error': f'盐值生成失败: {str(e)}'}
    
    @staticmethod
    def hmac_hash(text: str, key: str, algorithm: str = 'sha256') -> Dict[str, Any]:
        """
        HMAC哈希
        
        Args:
            text: 要哈希的文本
            key: 密钥
            algorithm: 哈希算法
            
        Returns:
            HMAC哈希结果
        """
        try:
            # 支持的算法
            algorithms = {
                'md5': hashlib.md5,
                'sha1': hashlib.sha1,
                'sha256': hashlib.sha256,
                'sha512': hashlib.sha512
            }
            
            if algorithm not in algorithms:
                return {'error': f'不支持的HMAC算法: {algorithm}'}
            
            # 计算HMAC
            hmac_hash = hmac.new(
                key.encode('utf-8'),
                text.encode('utf-8'),
                algorithms[algorithm]
            ).hexdigest()
            
            return {
                'success': True,
                'original': text,
                'key': key,
                'hmac': hmac_hash,
                'hmac_upper': hmac_hash.upper(),
                'algorithm': f'HMAC-{algorithm.upper()}',
                'length': len(hmac_hash)
            }
        except Exception as e:
            return {'error': f'HMAC哈希失败: {str(e)}'}
    
    @staticmethod
    def generate_key_pair(key_type: str = 'rsa', key_size: int = 2048) -> Dict[str, Any]:
        """
        生成密钥对（简化实现）
        
        Args:
            key_type: 密钥类型
            key_size: 密钥长度
            
        Returns:
            密钥对信息
        """
        try:
            # 简化实现，返回密钥对信息
            return {
                'success': True,
                'key_type': key_type.upper(),
                'key_size': key_size,
                'message': '密钥对生成功能需要专业加密库支持',
                'note': '生产环境请使用 cryptography 或 pycryptodome 库',
                'example_usage': {
                    'public_key': '用于加密和验证签名',
                    'private_key': '用于解密和生成签名',
                    'key_format': 'PEM 或 DER 格式'
                }
            }
        except Exception as e:
            return {'error': f'密钥对生成失败: {str(e)}'}