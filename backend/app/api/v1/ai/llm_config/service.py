# -*- coding: utf-8 -*-
"""
LLM 配置服务
"""
import time
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.ai.llm_config import LLMConfigModel
from app.api.v1.ai.llm_config.schema import (
    LLMConfigCreateSchema,
    LLMConfigUpdateSchema,
    LLMConfigTestSchema
)

logger = logging.getLogger(__name__)


class LLMConfigService:
    """LLM 配置服务"""
    
    @classmethod
    async def get_list(
        cls,
        db: AsyncSession,
        provider: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[LLMConfigModel]:
        """获取配置列表"""
        query = select(LLMConfigModel).where(LLMConfigModel.enabled_flag == 1)
        
        if provider:
            query = query.where(LLMConfigModel.provider == provider)
        
        if is_active is not None:
            query = query.where(LLMConfigModel.is_active == is_active)
        
        query = query.order_by(LLMConfigModel.is_default.desc(), LLMConfigModel.id.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, config_id: int) -> Optional[LLMConfigModel]:
        """根据ID获取配置"""
        query = select(LLMConfigModel).where(
            LLMConfigModel.id == config_id,
            LLMConfigModel.enabled_flag == 1
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_default(cls, db: AsyncSession) -> Optional[LLMConfigModel]:
        """获取默认配置"""
        query = select(LLMConfigModel).where(
            LLMConfigModel.is_default == True,
            LLMConfigModel.is_active == True,
            LLMConfigModel.enabled_flag == 1
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        data: LLMConfigCreateSchema,
        user_id: Optional[int] = None
    ) -> LLMConfigModel:
        """创建配置"""
        # 如果设置为默认配置，先取消其他默认配置
        if data.is_default:
            await cls._unset_all_defaults(db)
        
        # 创建新配置
        config = LLMConfigModel(
            config_name=data.config_name,
            name=data.name,
            provider=data.provider,
            model_name=data.model_name,
            api_key=data.api_key,
            base_url=data.base_url,
            system_prompt=data.system_prompt,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            supports_vision=data.supports_vision,
            context_limit=data.context_limit,
            is_default=data.is_default,
            is_active=data.is_active,
            created_by=user_id,
            updated_by=user_id
        )
        
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
        return config
    
    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        config_id: int,
        data: LLMConfigUpdateSchema,
        user_id: Optional[int] = None
    ) -> LLMConfigModel:
        """更新配置"""
        # 检查配置是否存在
        config = await cls.get_by_id(db, config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        # 如果设置为默认配置，先取消其他默认配置
        if data.is_default:
            await cls._unset_all_defaults(db)
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        update_data['updated_by'] = user_id
        
        # 检查API Key是否是脱敏值（包含****），如果是则保留数据库中的原值
        if 'api_key' in update_data and update_data['api_key'] and '****' in update_data['api_key']:
            logger.warning(f"检测到脱敏的API Key: {update_data['api_key']}, 将保留数据库中的原值")
            # 保留数据库中的原值
            update_data['api_key'] = config.api_key
            logger.info(f"保留原API Key: {config.api_key[:10]}...")
        
        stmt = (
            update(LLMConfigModel)
            .where(LLMConfigModel.id == config_id)
            .values(**update_data)
        )
        
        await db.execute(stmt)
        await db.commit()
        
        # 重新获取更新后的配置
        return await cls.get_by_id(db, config_id)
    
    @classmethod
    async def delete(cls, db: AsyncSession, config_id: int) -> bool:
        """删除配置（硬删除）"""
        config = await cls.get_by_id(db, config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        # 检查是否有AI模型配置在使用此LLM配置
        try:
            from sqlalchemy import select
            # 尝试导入AI模型配置模型
            try:
                from app.api.v1.ai_intelligence.model import AIModelConfigModel
                
                # 检查是否有AI模型配置关联此LLM配置
                check_stmt = select(AIModelConfigModel).where(
                    AIModelConfigModel.llm_config_id == config_id,
                    AIModelConfigModel.enabled_flag == 1
                )
                check_result = await db.execute(check_stmt)
                related_configs = check_result.scalars().all()
                
                if related_configs:
                    config_names = [c.name for c in related_configs]
                    raise HTTPException(
                        status_code=400, 
                        detail=f"无法删除，以下AI模型配置正在使用此LLM配置: {', '.join(config_names)}"
                    )
            except ImportError:
                # 如果AI模型配置模型不存在，跳过检查
                pass
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            # 其他异常记录日志但不阻止删除
            logger.warning(f"检查AI模型配置关联时出错: {e}")
        
        # 硬删除
        stmt = (
            delete(LLMConfigModel)
            .where(LLMConfigModel.id == config_id)
        )
        
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"硬删除LLM配置成功: ID={config_id}, Name={config.config_name}")
        return True
    
    @classmethod
    async def set_default(cls, db: AsyncSession, config_id: int) -> LLMConfigModel:
        """设置为默认配置"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 先检查配置是否存在
        config = await cls.get_by_id(db, config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        logger.info(f"[set_default] 开始设置默认配置: config_id={config_id}, config_name={config.config_name}")
        
        # 取消所有默认配置
        logger.info("[set_default] 取消所有默认配置...")
        await cls._unset_all_defaults(db)
        
        # 验证是否成功取消
        check_stmt = select(LLMConfigModel).where(
            LLMConfigModel.is_default == True,
            LLMConfigModel.enabled_flag == 1
        )
        check_result = await db.execute(check_stmt)
        remaining_defaults = check_result.scalars().all()
        if remaining_defaults:
            logger.warning(f"[set_default] 仍有 {len(remaining_defaults)} 个配置标记为默认")
            for rd in remaining_defaults:
                logger.warning(f"  - ID={rd.id}, name={rd.config_name}")
        else:
            logger.info("[set_default] 所有默认配置已取消")
        
        # 设置当前配置为默认
        logger.info(f"[set_default] 设置 config_id={config_id} 为默认...")
        stmt = (
            update(LLMConfigModel)
            .where(LLMConfigModel.id == config_id)
            .values(is_default=True)
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info("[set_default] 提交完成，重新查询配置...")
        
        # 重新获取更新后的配置
        updated_config = await cls.get_by_id(db, config_id)
        logger.info(f"[set_default] 更新后的配置: ID={updated_config.id}, is_default={updated_config.is_default}")
        
        # 验证数据库中的状态
        verify_stmt = select(LLMConfigModel).where(LLMConfigModel.enabled_flag == 1)
        verify_result = await db.execute(verify_stmt)
        all_configs = verify_result.scalars().all()
        logger.info(f"[set_default] 所有配置状态:")
        for c in all_configs:
            logger.info(f"  - ID={c.id}, name={c.config_name}, is_default={c.is_default}, is_active={c.is_active}")
        
        return updated_config
    
    @classmethod
    async def test_config(
        cls,
        db: AsyncSession,
        data: LLMConfigTestSchema
    ) -> Dict[str, Any]:
        """测试配置"""
        import httpx
        
        # 如果提供了 config_id，从数据库加载配置
        if data.config_id:
            config = await cls.get_by_id(db, data.config_id)
            if not config:
                return {
                    "success": False,
                    "message": "配置不存在",
                    "error": "配置ID无效"
                }
            
            provider = config.provider
            api_key = config.api_key
            base_url = config.base_url
            model_name = config.name
        else:
            # 使用提供的临时配置
            provider = data.provider
            api_key = data.api_key
            base_url = data.base_url
            model_name = data.name
        
        # 测试连接
        start_time = time.time()
        
        try:
            # 构建请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": data.test_message}
                ],
                "max_tokens": 100
            }
            
            # 确定端点
            if provider in ["openai", "custom"]:
                endpoint = f"{base_url}/chat/completions" if base_url else "https://api.openai.com/v1/chat/completions"
            else:
                endpoint = f"{base_url}/chat/completions"
            
            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return {
                        "success": True,
                        "message": "测试成功",
                        "response": content,
                        "latency": round(latency, 2)
                    }
                else:
                    return {
                        "success": False,
                        "message": "测试失败",
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "latency": round(latency, 2)
                    }
        
        except Exception as e:
            latency = time.time() - start_time
            return {
                "success": False,
                "message": "测试失败",
                "error": str(e),
                "latency": round(latency, 2)
            }
    
    @classmethod
    async def _unset_all_defaults(cls, db: AsyncSession):
        """取消所有默认配置"""
        stmt = (
            update(LLMConfigModel)
            .where(LLMConfigModel.is_default == True)
            .values(is_default=False)
        )
        await db.execute(stmt)
