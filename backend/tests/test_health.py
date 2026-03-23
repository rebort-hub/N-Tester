# -*- coding: utf-8 -*-
# @author: rebort
"""健康检查接口测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查接口"""
    response = await client.get("/api/health/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == 0
    assert data["success"] is True
    assert "data" in data
    
    health_data = data["data"]
    assert "status" in health_data
    assert "timestamp" in health_data
    assert "version" in health_data
    assert "checks" in health_data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """测试就绪检查接口"""
    response = await client.get("/api/health/readiness")
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == 0
    assert data["success"] is True
    assert "data" in data
    
    readiness_data = data["data"]
    assert "ready" in readiness_data
    assert readiness_data["ready"] is True
    assert "timestamp" in readiness_data


@pytest.mark.asyncio
async def test_system_info(client: AsyncClient):
    """测试系统信息接口"""
    response = await client.get("/api/health/info")
    assert response.status_code == 200
    
    data = response.json()
    assert data["code"] == 0
    assert data["success"] is True
    assert "data" in data
    
    info_data = data["data"]
    assert "name" in info_data
    assert "version" in info_data
    assert "description" in info_data
    assert "base_url" in info_data
    assert "api_prefix" in info_data
    assert "timestamp" in info_data
    assert info_data["name"] == "fast-element-admin"


@pytest.mark.asyncio
async def test_swagger_docs(client: AsyncClient):
    """测试 Swagger 文档访问"""
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


@pytest.mark.asyncio
async def test_redoc_docs(client: AsyncClient):
    """测试 ReDoc 文档访问"""
    response = await client.get("/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()


@pytest.mark.asyncio
async def test_openapi_schema(client: AsyncClient):
    """测试 OpenAPI Schema"""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert schema["info"]["title"] == "Fast Element Admin API"
