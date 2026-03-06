"""
JSON工具
提供JSON格式化、校验、转换、对比、查询等功能
"""
import json
import yaml
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from difflib import SequenceMatcher, unified_diff


class JsonTools:
    """JSON工具类"""
    
    @staticmethod
    def format_json(json_str: str, indent: int = 2, sort_keys: bool = False, compress: bool = False) -> Dict[str, Any]:
        """
        JSON格式化/压缩
        
        Args:
            json_str: JSON字符串
            indent: 缩进空格数
            sort_keys: 是否排序键
            compress: 是否压缩
            
        Returns:
            格式化结果
        """
        try:
            data = json.loads(json_str)
            
            original_chars = len(json_str)
            original_lines = json_str.count('\n') + 1
            
            if compress:
                result = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
                compressed_chars = len(result)
                compressed_lines = result.count('\n') + 1
                
                return {
                    'success': True,
                    'result': result,
                    'mode': 'compress',
                    'original_length': original_chars,
                    'compressed_length': compressed_chars,
                    'original_lines': original_lines,
                    'compressed_lines': compressed_lines,
                    'compression_ratio': f"{(1 - compressed_chars / original_chars) * 100:.2f}%"
                }
            else:
                result = json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=sort_keys)
                formatted_chars = len(result)
                formatted_lines = result.count('\n') + 1
                
                return {
                    'success': True,
                    'result': result,
                    'mode': 'format',
                    'indent': indent,
                    'sort_keys': sort_keys,
                    'original_length': original_chars,
                    'formatted_length': formatted_chars,
                    'original_lines': original_lines,
                    'formatted_lines': formatted_lines
                }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'JSON格式错误: {str(e)}',
                'line': getattr(e, 'lineno', None),
                'column': getattr(e, 'colno', None)
            }
        except Exception as e:
            return {'error': f'JSON格式化失败: {str(e)}'}
    
    @staticmethod
    def validate_json(json_str: str) -> Dict[str, Any]:
        """
        JSON校验
        
        Args:
            json_str: JSON字符串
            
        Returns:
            校验结果
        """
        try:
            data = json.loads(json_str)
            
            # 分析JSON结构
            def analyze_structure(obj, depth=0):
                if isinstance(obj, dict):
                    return {
                        'type': 'object',
                        'keys': len(obj),
                        'depth': depth,
                        'children': {k: analyze_structure(v, depth + 1) for k, v in obj.items()}
                    }
                elif isinstance(obj, list):
                    return {
                        'type': 'array',
                        'length': len(obj),
                        'depth': depth,
                        'items': [analyze_structure(item, depth + 1) for item in obj[:3]]  # 只分析前3个
                    }
                else:
                    return {
                        'type': type(obj).__name__,
                        'value': str(obj)[:50] + ('...' if len(str(obj)) > 50 else ''),
                        'depth': depth
                    }
            
            structure = analyze_structure(data)
            
            return {
                'success': True,
                'valid': True,
                'message': 'JSON格式正确',
                'data_type': type(data).__name__,
                'size': len(json_str),
                'structure': structure
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'valid': False,
                'error': f'JSON格式错误: {str(e)}',
                'line': getattr(e, 'lineno', None),
                'column': getattr(e, 'colno', None),
                'position': getattr(e, 'pos', None)
            }
        except Exception as e:
            return {'error': f'JSON校验失败: {str(e)}'}
    
    @staticmethod
    def json_diff_enhanced(json_str1: str, json_str2: str, ignore_whitespace: bool = True) -> Dict[str, Any]:
        """
        JSON对比
        
        Args:
            json_str1: 第一个JSON字符串
            json_str2: 第二个JSON字符串
            ignore_whitespace: 是否忽略空白字符
            
        Returns:
            对比结果
        """
        try:
            data1 = json.loads(json_str1)
            data2 = json.loads(json_str2)
            
            str1 = json.dumps(data1, ensure_ascii=False, sort_keys=True, indent=2)
            str2 = json.dumps(data2, ensure_ascii=False, sort_keys=True, indent=2)
            
            if ignore_whitespace:
                str1_clean = ''.join(str1.split())
                str2_clean = ''.join(str2.split())
                similarity = SequenceMatcher(None, str1_clean, str2_clean).ratio()
            else:
                similarity = SequenceMatcher(None, str1, str2).ratio()
            
            diff_lines = list(unified_diff(
                str1.splitlines(keepends=True),
                str2.splitlines(keepends=True),
                fromfile='JSON 1',
                tofile='JSON 2',
                lineterm=''
            ))
            
            diff_result = ''.join(diff_lines) if diff_lines else '无差异'
            
            # 详细差异分析
            key_diffs = []
            
            def compare_objects(obj1, obj2, path=''):
                if isinstance(obj1, dict) and isinstance(obj2, dict):
                    keys1 = set(obj1.keys())
                    keys2 = set(obj2.keys())
                    
                    for key in keys1 | keys2:
                        current_path = f"{path}.{key}" if path else key
                        if key in keys1 and key in keys2:
                            if obj1[key] != obj2[key]:
                                key_diffs.append({
                                    'path': current_path,
                                    'key': key,
                                    'value1': obj1[key],
                                    'value2': obj2[key],
                                    'type': 'value_diff'
                                })
                                compare_objects(obj1[key], obj2[key], current_path)
                        elif key in keys1:
                            key_diffs.append({
                                'path': current_path,
                                'key': key,
                                'value1': obj1[key],
                                'value2': None,
                                'type': 'key_only_in_1'
                            })
                        elif key in keys2:
                            key_diffs.append({
                                'path': current_path,
                                'key': key,
                                'value1': None,
                                'value2': obj2[key],
                                'type': 'key_only_in_2'
                            })
                elif isinstance(obj1, list) and isinstance(obj2, list):
                    min_len = min(len(obj1), len(obj2))
                    for i in range(min_len):
                        if obj1[i] != obj2[i]:
                            current_path = f"{path}[{i}]"
                            key_diffs.append({
                                'path': current_path,
                                'index': i,
                                'value1': obj1[i],
                                'value2': obj2[i],
                                'type': 'array_diff'
                            })
                    
                    # 检查数组长度差异
                    if len(obj1) != len(obj2):
                        key_diffs.append({
                            'path': path,
                            'type': 'array_length_diff',
                            'length1': len(obj1),
                            'length2': len(obj2)
                        })
            
            compare_objects(data1, data2)
            
            return {
                'success': True,
                'similarity': f"{similarity * 100:.2f}%",
                'identical': similarity == 1.0,
                'diff': diff_result,
                'detailed_diffs': key_diffs,
                'diff_count': len(key_diffs),
                'size1': len(json_str1),
                'size2': len(json_str2)
            }
        except json.JSONDecodeError as e:
            return {'error': f'JSON格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'JSON对比失败: {str(e)}'}
    
    @staticmethod
    def jsonpath_query(json_str: str, jsonpath_expr: str) -> Dict[str, Any]:
        """
        JSONPath查询
        
        Args:
            json_str: JSON字符串
            jsonpath_expr: JSONPath表达式
            
        Returns:
            查询结果
        """
        try:
            # 简单的JSONPath实现
            data = json.loads(json_str)
            
            # 支持基本的JSONPath语法
            if jsonpath_expr.startswith('$.'):
                # 特殊处理 $.users[*].name 这种格式
                if '[*]' in jsonpath_expr:
                    # 分解路径
                    parts = jsonpath_expr[2:].split('[*]')
                    if len(parts) == 2:
                        # 前半部分：到数组的路径
                        array_path = parts[0]
                        # 后半部分：数组元素的属性
                        element_path = parts[1].lstrip('.')
                        
                        # 获取数组
                        result = data
                        if array_path:
                            for key in array_path.split('.'):
                                if key:
                                    result = result[key]
                        
                        # 如果是数组，提取每个元素的指定属性
                        if isinstance(result, list):
                            if element_path:
                                result = [item.get(element_path) if isinstance(item, dict) else item for item in result]
                            # 如果没有后续路径，返回整个数组
                        
                        return {
                            'success': True,
                            'expression': jsonpath_expr,
                            'result': result,
                            'type': type(result).__name__,
                            'count': len(result) if isinstance(result, (list, dict)) else 1
                        }
                
                # 普通路径处理
                path_parts = jsonpath_expr[2:].split('.')
                result = data
                
                for part in path_parts:
                    if '[' in part and ']' in part:
                        # 处理数组索引
                        key = part.split('[')[0]
                        index_part = part.split('[')[1].split(']')[0]
                        
                        if key:
                            result = result[key]
                        
                        if index_part == '*':
                            # 通配符，返回所有元素
                            if isinstance(result, list):
                                result = result
                            else:
                                result = list(result.values()) if isinstance(result, dict) else [result]
                        else:
                            # 具体索引
                            index = int(index_part)
                            result = result[index]
                    elif part == '*':
                        # 通配符处理
                        if isinstance(result, list):
                            result = result
                        elif isinstance(result, dict):
                            result = list(result.values())
                        else:
                            result = [result]
                    else:
                        result = result[part]
                
                return {
                    'success': True,
                    'expression': jsonpath_expr,
                    'result': result,
                    'type': type(result).__name__,
                    'count': len(result) if isinstance(result, (list, dict)) else 1
                }
            else:
                return {'error': 'JSONPath表达式必须以 $. 开头'}
                
        except json.JSONDecodeError as e:
            return {'error': f'JSON格式错误: {str(e)}'}
        except (KeyError, IndexError, TypeError) as e:
            return {'error': f'JSONPath查询失败: 路径不存在或格式错误 - {str(e)}'}
        except Exception as e:
            return {'error': f'JSONPath查询失败: {str(e)}'}
    
    @staticmethod
    def json_flatten(json_str: str, separator: str = '.') -> Dict[str, Any]:
        """
        扁平化JSON
        
        Args:
            json_str: JSON字符串
            separator: 分隔符
            
        Returns:
            扁平化结果
        """
        try:
            data = json.loads(json_str)
            result = {}
            
            def flatten(obj, parent_key=''):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        new_key = f"{parent_key}{separator}{key}" if parent_key else key
                        flatten(value, new_key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        new_key = f"{parent_key}[{i}]"
                        flatten(item, new_key)
                else:
                    result[parent_key] = obj
            
            flatten(data)
            
            return {
                'success': True,
                'result': result,
                'count': len(result),
                'separator': separator
            }
        except json.JSONDecodeError as e:
            return {'error': f'JSON格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'JSON扁平化失败: {str(e)}'}
    
    @staticmethod
    def json_path_list(json_str: str) -> Dict[str, Any]:
        """
        列出JSON所有路径
        
        Args:
            json_str: JSON字符串
            
        Returns:
            路径列表
        """
        try:
            data = json.loads(json_str)
            paths = []
            
            def get_paths(obj, current_path=''):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        new_path = f"{current_path}.{key}" if current_path else key
                        paths.append({
                            'path': new_path,
                            'type': type(value).__name__,
                            'value': str(value)[:50] + ('...' if len(str(value)) > 50 else '')
                        })
                        get_paths(value, new_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        new_path = f"{current_path}[{i}]"
                        paths.append({
                            'path': new_path,
                            'type': type(item).__name__,
                            'value': str(item)[:50] + ('...' if len(str(item)) > 50 else '')
                        })
                        get_paths(item, new_path)
            
            get_paths(data)
            
            return {
                'success': True,
                'paths': paths,
                'count': len(paths)
            }
        except json.JSONDecodeError as e:
            return {'error': f'JSON格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'获取JSON路径失败: {str(e)}'}
    
    @staticmethod
    def json_to_xml(json_str: str, root_tag: str = 'root') -> Dict[str, Any]:
        """
        JSON转XML
        
        Args:
            json_str: JSON字符串
            root_tag: 根标签名
            
        Returns:
            XML字符串
        """
        try:
            data = json.loads(json_str)
            
            def dict_to_xml(d, parent):
                for key, value in d.items():
                    # 处理特殊字符
                    safe_key = str(key).replace(' ', '_').replace('-', '_')
                    if safe_key[0].isdigit():
                        safe_key = f'item_{safe_key}'
                    
                    if isinstance(value, dict):
                        elem = ET.SubElement(parent, safe_key)
                        dict_to_xml(value, elem)
                    elif isinstance(value, list):
                        for item in value:
                            elem = ET.SubElement(parent, safe_key)
                            if isinstance(item, dict):
                                dict_to_xml(item, elem)
                            else:
                                elem.text = str(item)
                    else:
                        elem = ET.SubElement(parent, safe_key)
                        elem.text = str(value)
            
            root = ET.Element(root_tag)
            if isinstance(data, dict):
                dict_to_xml(data, root)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    elem = ET.SubElement(root, f'item_{i}')
                    if isinstance(item, dict):
                        dict_to_xml(item, elem)
                    else:
                        elem.text = str(item)
            else:
                root.text = str(data)
            
            xml_str = ET.tostring(root, encoding='unicode', method='xml')
            
            # 格式化XML
            try:
                import xml.dom.minidom
                dom = xml.dom.minidom.parseString(xml_str)
                formatted_xml = dom.toprettyxml(indent='  ')
                # 移除空行
                formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
            except:
                formatted_xml = xml_str
            
            return {
                'success': True,
                'result': formatted_xml,
                'root_tag': root_tag
            }
        except json.JSONDecodeError as e:
            return {'error': f'JSON格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'JSON转XML失败: {str(e)}'}
    
    @staticmethod
    def xml_to_json(xml_str: str) -> Dict[str, Any]:
        """
        XML转JSON
        
        Args:
            xml_str: XML字符串
            
        Returns:
            JSON字符串
        """
        try:
            def xml_to_dict(element):
                result = {}
                
                # 处理属性
                if element.attrib:
                    result['@attributes'] = element.attrib
                
                # 处理子元素
                children = list(element)
                if children:
                    child_dict = {}
                    for child in children:
                        child_data = xml_to_dict(child)
                        if child.tag in child_dict:
                            # 如果已存在，转换为数组
                            if not isinstance(child_dict[child.tag], list):
                                child_dict[child.tag] = [child_dict[child.tag]]
                            child_dict[child.tag].append(child_data)
                        else:
                            child_dict[child.tag] = child_data
                    result.update(child_dict)
                
                # 处理文本内容
                if element.text and element.text.strip():
                    if result:
                        result['#text'] = element.text.strip()
                    else:
                        return element.text.strip()
                
                return result if result else None
            
            root = ET.fromstring(xml_str)
            data = {root.tag: xml_to_dict(root)}
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'result': json_str
            }
        except ET.ParseError as e:
            return {'error': f'XML格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'XML转JSON失败: {str(e)}'}
    
    @staticmethod
    def json_to_yaml(json_str: str) -> Dict[str, Any]:
        """
        JSON转YAML
        
        Args:
            json_str: JSON字符串
            
        Returns:
            YAML字符串
        """
        try:
            data = json.loads(json_str)
            yaml_str = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            return {
                'success': True,
                'result': yaml_str
            }
        except json.JSONDecodeError as e:
            return {'error': f'JSON格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'JSON转YAML失败: {str(e)}'}
    
    @staticmethod
    def yaml_to_json(yaml_str: str) -> Dict[str, Any]:
        """
        YAML转JSON
        
        Args:
            yaml_str: YAML字符串
            
        Returns:
            JSON字符串
        """
        try:
            data = yaml.safe_load(yaml_str)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'result': json_str
            }
        except yaml.YAMLError as e:
            return {'error': f'YAML格式错误: {str(e)}'}
        except Exception as e:
            return {'error': f'YAML转JSON失败: {str(e)}'}