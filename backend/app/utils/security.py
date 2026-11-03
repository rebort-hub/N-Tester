# -*- coding: utf-8 -*-
# @author: rebort
"""安全工具模块 - 密码加密、Token生成等"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.setting import config

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 配置
ALGORITHM = "HS256"


class PasswordHandler:
    """密码处理类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码
            
        Returns:
            密码是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        生成随机密码
        
        Args:
            length: 密码长度
            
        Returns:
            随机密码
        """
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class TokenHandler:
    """Token 处理类"""
    
    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量
            
        Returns:
            JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            config.SECRET_KEY,
            algorithm=ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def decode_access_token(token: str) -> Optional[dict]:
        """
        解码访问令牌
        
        Args:
            token: JWT token
            
        Returns:
            解码后的数据，如果失败返回 None
        """
        try:
            payload = jwt.decode(
                token,
                config.SECRET_KEY,
                algorithms=[ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """
        生成随机令牌
        
        Args:
            length: 令牌长度
            
        Returns:
            随机令牌
        """
        return secrets.token_urlsafe(length)


class DataMasking:
    """数据脱敏类"""
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        手机号脱敏
        
        Args:
            phone: 手机号
            
        Returns:
            脱敏后的手机号
        """
        if not phone or len(phone) < 11:
            return phone
        return f"{phone[:3]}****{phone[7:]}"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """
        邮箱脱敏
        
        Args:
            email: 邮箱地址
            
        Returns:
            脱敏后的邮箱
        """
        if not email or '@' not in email:
            return email
        
        parts = email.split('@')
        if len(parts) != 2:
            return email
        
        username = parts[0]
        domain = parts[1]
        
        if len(username) <= 2:
            masked_username = username[0] + '*'
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """
        身份证号脱敏
        
        Args:
            id_card: 身份证号
            
        Returns:
            脱敏后的身份证号
        """
        if not id_card or len(id_card) < 18:
            return id_card
        return f"{id_card[:6]}********{id_card[14:]}"
    
    @staticmethod
    def mask_bank_card(bank_card: str) -> str:
        """
        银行卡号脱敏
        
        Args:
            bank_card: 银行卡号
            
        Returns:
            脱敏后的银行卡号
        """
        if not bank_card or len(bank_card) < 16:
            return bank_card
        return f"{bank_card[:4]} **** **** {bank_card[-4:]}"
    
    @staticmethod
    def mask_name(name: str) -> str:
        """
        姓名脱敏
        
        Args:
            name: 姓名
            
        Returns:
            脱敏后的姓名
        """
        if not name:
            return name
        
        if len(name) == 2:
            return name[0] + '*'
        elif len(name) > 2:
            return name[0] + '*' * (len(name) - 2) + name[-1]
        else:
            return name


class InputValidator:
    """输入验证类"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """验证手机号格式（中国大陆）"""
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def is_valid_password(password: str, min_length: int = 8) -> tuple[bool, str]:
        """
        验证密码强度
        
        Args:
            password: 密码
            min_length: 最小长度
            
        Returns:
            (是否有效, 错误信息)
        """
        if len(password) < min_length:
            return False, f"密码长度至少为 {min_length} 位"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "密码必须包含大写字母、小写字母和数字"
        
        return True, ""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        清理输入，防止 XSS 攻击
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        import html
        return html.escape(text)


# 便捷函数
def hash_password(password: str) -> str:
    """加密密码"""
    return PasswordHandler.hash_password(password)


def get_password_hash(password: str) -> str:
    """加密密码"""
    return PasswordHandler.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return PasswordHandler.verify_password(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    return TokenHandler.create_access_token(data, expires_delta)


def decode_access_token(token: str) -> Optional[dict]:
    """解码访问令牌"""
    return TokenHandler.decode_access_token(token)
