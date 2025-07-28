"""
Android ANR (Application Not Responding) 解析器

專門處理 Android ANR traces 檔案
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_log_parser import BaseLogParser
from langchain.schema import Document


class AndroidANRParser(BaseLogParser):
    """Android ANR 解析器"""
    
    def get_log_type(self) -> str:
        return "android_anr"
    
    def can_parse(self, file_path: str, content_sample: str) -> bool:
        """檢查是否為 ANR trace 檔案"""
        # ANR 檔案特徵
        anr_indicators = [
            "----- pid",
            "Cmd line:",
            "ABI:",
            "Build fingerprint:",
            "*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***",
            "DALVIK THREADS",
            "suspend all histogram",
            "\"main\" prio=",
            "\"Signal Catcher\" daemon prio=",
            "Build.ID:",
            "Build.VERSION.SDK_INT:",
            "zygote"
        ]
        
        # 檢查多個指標
        matches = sum(1 for indicator in anr_indicators if indicator in content_sample)
        
        # 如果匹配超過3個指標，認為是 ANR
        return matches >= 3
    
    def get_patterns(self) -> Dict[str, str]:
        """返回 ANR 相關的正則表達式"""
        return {
            'pid_header': r'----- pid (\d+) at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) -----',
            'cmd_line': r'Cmd line: (.+)',
            'build_fingerprint': r'Build fingerprint: [\'"]?(.+?)[\'"]?$',
            'thread_info': r'^"([^"]+)".*?prio=(\d+).*?tid=(\d+)',
            'native_stack': r'^\s+#\d+\s+pc\s+[0-9a-fA-F]+\s+(.+)',
            'java_stack': r'^\s+at\s+([a-zA-Z_$][a-zA-Z\d_$]*(?:\.[a-zA-Z_$][a-zA-Z\d_$]*)*)',
            'held_mutexes': r'^\s+\| held mutexes=(.+)',
            'waiting_on': r'^\s+\| waiting (?:on|to lock) (.+)',
            'thread_state': r'^\s+\| state=([A-Z])',
            'dalvik_threads': r'^DALVIK THREADS \((\d+)\):',
            'anr_header': r'\*{3,}.*?\*{3,}',
        }
    
    def analyze_log_structure(self, content: str) -> Dict[str, Any]:
        """分析 ANR 結構"""
        patterns = self.get_patterns()
        lines = content.split('\n')
        
        # 提取基本資訊
        pid_match = re.search(patterns['pid_header'], content)
        pid = int(pid_match.group(1)) if pid_match else None
        timestamp = pid_match.group(2) if pid_match else None
        
        cmd_match = re.search(patterns['cmd_line'], content)
        cmd_line = cmd_match.group(1).strip() if cmd_match else None
        
        build_match = re.search(patterns['build_fingerprint'], content)
        build_fingerprint = build_match.group(1).strip() if build_match else None
        
        # 統計線程資訊
        thread_count = 0
        thread_states = {}
        blocked_threads = []
        main_thread_state = None
        
        current_thread = None
        for line in lines:
            # 檢測線程開始
            thread_match = re.match(patterns['thread_info'], line)
            if thread_match:
                thread_count += 1
                current_thread = thread_match.group(1)
                if current_thread == "main":
                    # 特別關注主線程
                    pass
            
            # 檢測線程狀態
            if current_thread:
                state_match = re.match(patterns['thread_state'], line)
                if state_match:
                    state = state_match.group(1)
                    thread_states[state] = thread_states.get(state, 0) + 1
                    if current_thread == "main":
                        main_thread_state = state
                
                # 檢測阻塞
                waiting_match = re.match(patterns['waiting_on'], line)
                if waiting_match:
                    blocked_threads.append({
                        'thread': current_thread,
                        'waiting_on': waiting_match.group(1).strip()
                    })
        
        # 檢測是否有死鎖跡象
        has_deadlock = len(blocked_threads) >= 2
        
        # 分析嚴重程度
        severity = self._calculate_anr_severity(
            main_thread_state,
            blocked_threads,
            thread_states
        )
        
        return {
            'log_type': 'android_anr',
            'pid': pid,
            'timestamp': timestamp,
            'package_name': cmd_line,
            'build_fingerprint': build_fingerprint,
            'total_threads': thread_count,
            'thread_states': thread_states,
            'blocked_threads': len(blocked_threads),
            'main_thread_state': main_thread_state,
            'has_deadlock_risk': has_deadlock,
            'severity': severity,
            'file_size_mb': len(content) / (1024 * 1024),
        }
    
    def _calculate_anr_severity(self, main_thread_state: Optional[str], 
                                blocked_threads: List[Dict], 
                                thread_states: Dict[str, int]) -> str:
        """計算 ANR 嚴重程度"""
        # 如果主線程被阻塞，嚴重程度高
        if main_thread_state in ['D', 'S'] or any(t['thread'] == 'main' for t in blocked_threads):
            return "critical"
        
        # 如果有多個線程被阻塞
        if len(blocked_threads) >= 3:
            return "high"
        
        # 如果有死鎖風險
        if len(blocked_threads) >= 2:
            return "medium"
        
        return "low"
    
    def parse_content(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """解析 ANR 內容"""
        documents = []
        patterns = self.get_patterns()
        
        # 1. 創建摘要文檔
        summary_content = self._create_anr_summary(log_info)
        summary_doc = self.create_document(
            summary_content,
            file_path,
            {
                'chunk_method': 'anr_summary',
                'chunk_type': 'summary',
                'severity': log_info.get('severity', 'unknown'),
                **log_info
            }
        )
        documents.append(summary_doc)
        
        # 2. 按線程分割
        thread_documents = self._parse_by_threads(content, file_path, log_info)
        documents.extend(thread_documents)
        
        # 3. 提取關鍵堆疊
        stack_documents = self._extract_key_stacks(content, file_path, log_info)
        documents.extend(stack_documents)
        
        return documents
    
    def _create_anr_summary(self, log_info: Dict[str, Any]) -> str:
        """創建 ANR 摘要"""
        summary = f"""Android ANR 分析摘要
========================
包名: {log_info.get('package_name', 'Unknown')}
PID: {log_info.get('pid', 'Unknown')}
時間: {log_info.get('timestamp', 'Unknown')}
嚴重程度: {log_info.get('severity', 'Unknown').upper()}

線程統計:
- 總線程數: {log_info.get('total_threads', 0)}
- 阻塞線程數: {log_info.get('blocked_threads', 0)}
- 主線程狀態: {log_info.get('main_thread_state', 'Unknown')}
- 死鎖風險: {'是' if log_info.get('has_deadlock_risk') else '否'}

線程狀態分布:
"""
        
        thread_states = log_info.get('thread_states', {})
        for state, count in thread_states.items():
            state_name = self._get_thread_state_name(state)
            summary += f"- {state_name}: {count} 個線程\n"
        
        summary += f"\nBuild: {log_info.get('build_fingerprint', 'Unknown')}"
        
        return summary
    
    def _get_thread_state_name(self, state: str) -> str:
        """獲取線程狀態的可讀名稱"""
        state_names = {
            'R': 'Running (執行中)',
            'S': 'Sleeping (休眠)',
            'D': 'Waiting in uninterruptible sleep (不可中斷等待)',
            'Z': 'Zombie (殭屍)',
            'T': 'Stopped (停止)',
            't': 'Tracing stop (追蹤停止)',
            'X': 'Dead (死亡)',
            'x': 'Dead (死亡)',
            'K': 'Wakekill (喚醒終止)',
            'W': 'Waking (喚醒中)',
        }
        return state_names.get(state, f'Unknown ({state})')
    
    def _parse_by_threads(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """按線程解析"""
        documents = []
        patterns = self.get_patterns()
        
        # 分割成線程塊
        thread_blocks = []
        current_block = []
        current_thread_name = None
        
        lines = content.split('\n')
        for line in lines:
            # 檢測新線程開始
            thread_match = re.match(patterns['thread_info'], line)
            if thread_match:
                # 保存前一個線程塊
                if current_block and current_thread_name:
                    thread_blocks.append({
                        'name': current_thread_name,
                        'content': '\n'.join(current_block)
                    })
                
                # 開始新線程
                current_thread_name = thread_match.group(1)
                current_block = [line]
            elif current_thread_name:
                current_block.append(line)
        
        # 保存最後一個線程
        if current_block and current_thread_name:
            thread_blocks.append({
                'name': current_thread_name,
                'content': '\n'.join(current_block)
            })
        
        # 只保存重要的線程（主線程、阻塞的線程等）
        important_threads = ['main', 'Signal Catcher', 'FinalizerDaemon']
        
        for thread_block in thread_blocks:
            thread_name = thread_block['name']
            thread_content = thread_block['content']
            
            # 判斷是否為重要線程
            is_important = (
                thread_name in important_threads or
                'waiting on' in thread_content or
                'held mutexes' in thread_content or
                thread_name == 'main'
            )
            
            if is_important:
                # 分析線程狀態
                is_blocked = 'waiting on' in thread_content or 'waiting to lock' in thread_content
                has_stack = '  at ' in thread_content or '  pc ' in thread_content
                
                doc = self.create_document(
                    thread_content,
                    file_path,
                    {
                        'chunk_method': 'anr_thread',
                        'chunk_type': 'thread',
                        'thread_name': thread_name,
                        'is_main_thread': thread_name == 'main',
                        'is_blocked': is_blocked,
                        'has_stack_trace': has_stack,
                        'severity': log_info.get('severity', 'unknown'),
                    }
                )
                documents.append(doc)
        
        return documents
    
    def _extract_key_stacks(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """提取關鍵堆疊追蹤"""
        documents = []
        
        # 查找主線程的堆疊
        main_thread_pattern = r'"main".*?(?=^"|\Z)'
        main_match = re.search(main_thread_pattern, content, re.MULTILINE | re.DOTALL)
        
        if main_match:
            main_stack = main_match.group(0)
            
            # 如果主線程有明顯的阻塞或異常
            if any(keyword in main_stack for keyword in ['waiting', 'blocked', 'lock', 'ANR']):
                doc = self.create_document(
                    main_stack,
                    file_path,
                    {
                        'chunk_method': 'anr_main_stack',
                        'chunk_type': 'critical_stack',
                        'thread_name': 'main',
                        'severity': 'critical',
                    }
                )
                documents.append(doc)
        
        return documents