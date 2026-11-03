#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.common.response import success_response
from app.api.v1.system.code_generator.schema import (
    GenerateCodeRequest,
    GenerateCodeResponse,
    GenerateModesResponse,
    GenerateModeItem,
    ResetRuleItem
)
from app.api.v1.system.code_generator.service import CodeGeneratorService

router = APIRouter(prefix="/code-generator", tags=["编码生成器"])


@router.post("/generate", summary="生成编码", response_model=dict)
async def generate_code(
    data: GenerateCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    生成唯一编码
    
    支持的生成方式:
    - datetime: 日期时间格式 (PREFIX20241222103000)
    - date_seq: 日期+序号格式 (PREFIX20241222-0001)
    - uuid: UUID片段格式 (PREFIX-a1b2c3d4)
    - snowflake: 雪花ID格式 (PREFIX1234567890123456)
    - random: 随机字符格式 (PREFIX-X7K9M2)
    - custom: 自定义模板格式
    
    序号重置规则:
    - daily: 每日重置
    - monthly: 每月重置
    - yearly: 每年重置
    - never: 不重置
    
    自定义模板变量:
    - {PREFIX}: 前缀
    - {YYYY}: 4位年份
    - {YY}: 2位年份
    - {MM}: 月份
    - {DD}: 日期
    - {HH}: 小时
    - {mm}: 分钟
    - {ss}: 秒
    - {SEQ}: 序号
    - {SEQ:N}: N位序号
    - {UUID}: UUID片段
    - {RANDOM}: 随机字符
    - {RANDOM:N}: N位随机字符
    """
    code = await CodeGeneratorService.generate(
        prefix=data.prefix,
        separator=data.separator,
        generate_mode=data.generate_mode,
        date_format=data.date_format,
        seq_length=data.seq_length,
        seq_reset_rule=data.seq_reset_rule,
        random_length=data.random_length,
        custom_template=data.custom_template,
        business_type=data.business_type,
        db=db
    )

    return success_response(data={'code': code}, message="生成成功")


@router.get("/modes", summary="获取生成方式列表", response_model=dict)
async def get_generate_modes():
    """获取支持的编码生成方式和重置规则"""
    modes = [
        GenerateModeItem(
            value='datetime',
            label='日期时间',
            example='PREFIX20241222103000'
        ),
        GenerateModeItem(
            value='date_seq',
            label='日期+序号',
            example='PREFIX20241222-0001'
        ),
        GenerateModeItem(
            value='uuid',
            label='UUID片段',
            example='PREFIX-a1b2c3d4'
        ),
        GenerateModeItem(
            value='snowflake',
            label='雪花ID',
            example='PREFIX1234567890123456'
        ),
        GenerateModeItem(
            value='random',
            label='随机字符',
            example='PREFIX-X7K9M2'
        ),
        GenerateModeItem(
            value='custom',
            label='自定义模板',
            example='{PREFIX}{YYYY}{MM}{DD}-{SEQ:4}'
        ),
    ]
    
    reset_rules = [
        ResetRuleItem(value='daily', label='每日重置'),
        ResetRuleItem(value='monthly', label='每月重置'),
        ResetRuleItem(value='yearly', label='每年重置'),
        ResetRuleItem(value='never', label='不重置'),
    ]
    
    return success_response(
        data={'modes': [m.model_dump() for m in modes], 'reset_rules': [r.model_dump() for r in reset_rules]},
        message="查询成功"
    )
