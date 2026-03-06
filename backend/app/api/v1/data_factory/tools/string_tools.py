# -*- coding: utf-8 -*-
"""
字符处理工具
提供字符串处理、文本对比、正则测试等功能
"""
import re
import json
import difflib
import urllib.parse
from typing import Dict, List, Any


class StringTools:
    """字符工具类"""

    @staticmethod
    def remove_whitespace(text: str) -> Dict[str, Any]:
        """去除空格和换行"""
        try:
            result = re.sub(r'\s+', '', text)
            return {
                'result': result,
                'original_length': len(text),
                'new_length': len(result)
            }
        except Exception as e:
            return {'error': f'去除空格失败: {str(e)}'}

    @staticmethod
    def replace_string(text: str, old_str: str, new_str: str, is_regex: bool = False) -> Dict[str, Any]:
        """字符串替换"""
        try:
            if is_regex:
                try:
                    result = re.sub(old_str, new_str, text)
                    # 计算替换次数
                    matches = re.findall(old_str, text)
                    replacements = len(matches)
                    return {
                        'result': result,
                        'replacements': replacements
                    }
                except re.error as e:
                    return {'error': f'正则表达式错误: {str(e)}'}
            else:
                result = text.replace(old_str, new_str)
                return {
                    'result': result,
                    'replacements': text.count(old_str)
                }
        except Exception as e:
            return {'error': f'字符串替换失败: {str(e)}'}

    @staticmethod
    def escape_string(text: str, escape_type: str = 'json') -> Dict[str, Any]:
        """字符串转义"""
        try:
            if escape_type == 'json':
                result = json.dumps(text, ensure_ascii=False)
                return {'result': result}
            elif escape_type == 'html':
                result = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
                return {'result': result}
            elif escape_type == 'url':
                result = urllib.parse.quote(text, safe='')
                return {'result': result}
            elif escape_type == 'xml':
                result = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
                return {'result': result}
            else:
                return {'error': f'不支持的转义类型: {escape_type}'}
        except Exception as e:
            return {'error': f'字符串转义失败: {str(e)}'}

    @staticmethod
    def unescape_string(text: str, unescape_type: str = 'json') -> Dict[str, Any]:
        """字符串反转义"""
        try:
            if unescape_type == 'json':
                try:
                    result = json.loads(text)
                    return {'result': result}
                except json.JSONDecodeError as e:
                    return {'error': f'JSON解析错误: {str(e)}'}
            elif unescape_type == 'html':
                html_unescape = {
                    '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&nbsp;': ' ', '&#x27;': "'", '&apos;': "'"
                }
                result = text
                for key, value in html_unescape.items():
                    result = result.replace(key, value)
                return {'result': result}
            elif unescape_type == 'url':
                result = urllib.parse.unquote(text)
                return {'result': result}
            elif unescape_type == 'xml':
                xml_unescape = {
                    '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'"
                }
                result = text
                for key, value in xml_unescape.items():
                    result = result.replace(key, value)
                return {'result': result}
            else:
                return {'error': f'不支持的反转义类型: {unescape_type}'}
        except Exception as e:
            return {'error': f'字符串反转义失败: {str(e)}'}

    @staticmethod
    def word_count(text: str) -> Dict[str, Any]:
        """字数统计"""
        try:
            # 统计中文字符
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            # 统计英文单词
            english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
            # 统计数字
            numbers = len(re.findall(r'\d+', text))
            # 统计标点符号
            punctuation = len(re.findall(r'[^\w\s\u4e00-\u9fff]', text))

            return {
                'total_length': len(text),
                'chinese_chars': chinese_chars,
                'english_words': english_words,
                'numbers': numbers,
                'punctuation': punctuation,
                'lines': len(text.split('\n')),
                'paragraphs': len([p for p in text.split('\n') if p.strip()])
            }
        except Exception as e:
            return {'error': f'字数统计失败: {str(e)}'}

    @staticmethod
    def text_diff(text1: str, text2: str) -> Dict[str, Any]:
        """文本对比"""
        try:
            if text1 is None:
                text1 = ""
            if text2 is None:
                text2 = ""

            lines1 = text1.splitlines()
            lines2 = text2.splitlines()

            differ = difflib.Differ()
            diff = list(differ.compare(lines1, lines2))

            added = 0
            removed = 0
            unchanged = 0

            for line in diff:
                if line.startswith('+ '):
                    added += 1
                elif line.startswith('- '):
                    removed += 1
                elif line.startswith('  '):
                    unchanged += 1

            return {
                'diff': diff,
                'added': added,
                'removed': removed,
                'unchanged': unchanged,
                'total_changes': added + removed
            }
        except Exception as e:
            return {'error': f'文本对比失败: {str(e)}'}

    @staticmethod
    def regex_test(pattern: str, text: str, flags: str = '') -> Dict[str, Any]:
        """正则表达式测试"""
        try:
            # 解析正则标志
            flag_mapping = {
                'i': re.IGNORECASE,
                'm': re.MULTILINE,
                's': re.DOTALL,
                'u': re.UNICODE,
                'x': re.VERBOSE
            }
            regex_flags = 0
            for flag in flags:
                if flag in flag_mapping:
                    regex_flags |= flag_mapping[flag]

            # 编译正则表达式
            regex = re.compile(pattern, regex_flags)

            # 查找所有匹配
            matches = regex.findall(text)
            # 查找第一个匹配的位置
            match = regex.search(text)
            groups = match.groups() if match else []
            groupdict = match.groupdict() if match else {}

            return {
                'matches': matches,
                'match_count': len(matches),
                'groups': groups,
                'groupdict': groupdict,
                'is_valid': True
            }
        except re.error as e:
            return {
                'error': f'正则表达式错误: {str(e)}',
                'is_valid': False
            }
        except Exception as e:
            return {'error': f'正则测试失败: {str(e)}'}

    @staticmethod
    def case_convert(text: str, convert_type: str) -> Dict[str, Any]:
        """大小写转换"""
        try:
            convert_functions = {
                'upper': str.upper,
                'lower': str.lower,
                'capitalize': str.capitalize,
                'title': str.title,
                'swapcase': str.swapcase
            }

            if convert_type not in convert_functions:
                return {'error': f'不支持的转换类型: {convert_type}'}

            return {
                'result': convert_functions[convert_type](text),
                'original': text
            }
        except Exception as e:
            return {'error': f'大小写转换失败: {str(e)}'}

    @staticmethod
    def string_format(text: str, format_type: str) -> Dict[str, Any]:
        """字符串格式化"""
        try:
            if format_type == 'trim':
                return {'result': text.strip()}
            elif format_type == 'reverse':
                return {'result': text[::-1]}
            elif format_type == 'split':
                return {'result': text.split()}
            elif format_type == 'join':
                return {'result': ''.join(text.split())}
            else:
                return {'error': f'不支持的格式化类型: {format_type}'}
        except Exception as e:
            return {'error': f'字符串格式化失败: {str(e)}'}