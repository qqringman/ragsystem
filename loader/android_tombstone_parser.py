"""
Android Tombstone 解析器

專門處理 Android 崩潰的 tombstone 檔案
"""

import re
from typing import List, Dict, Any, Optional
from .base_log_parser import BaseLogParser
from langchain.schema import Document


class AndroidTombstoneParser(BaseLogParser):
    """Android Tombstone 解析器"""
    
    def get_log_type(self) -> str:
        return "android_tombstone"
    
    def can_parse(self, file_path: str, content_sample: str) -> bool:
        """檢查是否為 Tombstone 檔案"""
        # Tombstone 檔案特徵
        tombstone_indicators = [
            "*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***",
            "Build fingerprint:",
            "Revision:",
            "ABI:",
            "Timestamp:",
            "Process uptime:",
            "Cmdline:",
            "pid:",
            "tid:",
            "signal",
            "fault addr",
            "backtrace:",
            "stack:",
            "memory map:",
            "registers:",
            "SIGSEGV",
            "SIGABRT",
            "Abort message:",
            "#00 pc"
        ]
        
        # 檢查多個指標
        matches = sum(1 for indicator in tombstone_indicators if indicator in content_sample)
        
        # 如果匹配超過4個指標，認為是 Tombstone
        return matches >= 4 or "tombstone" in file_path.lower()
    
    def get_patterns(self) -> Dict[str, str]:
        """返回 Tombstone 相關的正則表達式"""
        return {
            'header': r'\*{3,}.*?\*{3,}',
            'build_fingerprint': r'Build fingerprint: [\'"]?(.+?)[\'"]?$',
            'revision': r'Revision: [\'"]?(.+?)[\'"]?$',
            'abi': r'ABI: [\'"]?(.+?)[\'"]?$',
            'timestamp': r'Timestamp: (.+)',
            'process_uptime': r'Process uptime: (.+)',
            'cmdline': r'Cmdline: (.+)',
            'pid_tid': r'pid: (\d+), tid: (\d+), name: (.+?)(?:\s+>>>(.+?)<<<)?',
            'signal_info': r'signal (\d+) \(([A-Z]+)\)',
            'fault_addr': r'fault addr ([0-9a-fA-Fx]+)',
            'abort_message': r'Abort message: [\'"]?(.+?)[\'"]?$',
            'backtrace_line': r'^\s*#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+(.+?)(?:\s+\((.+?)\))?$',
            'register': r'^\s*([a-z0-9]+)\s+([0-9a-fA-F]+)',
            'memory_map': r'^\s*([0-9a-fA-F]+)-([0-9a-fA-F]+)\s+([rwxp-]+)\s+([0-9a-fA-F]+)\s+',
            'cause_line': r'Cause: (.+)',
            'java_stacktrace': r'^\s+at\s+([a-zA-Z_$][a-zA-Z\d_$]*(?:\.[a-zA-Z_$][a-zA-Z\d_$]*)*)',
        }
    
    def analyze_log_structure(self, content: str) -> Dict[str, Any]:
        """分析 Tombstone 結構"""
        patterns = self.get_patterns()
        
        # 提取基本資訊
        build_match = re.search(patterns['build_fingerprint'], content)
        build_fingerprint = build_match.group(1).strip() if build_match else None
        
        timestamp_match = re.search(patterns['timestamp'], content)
        timestamp = timestamp_match.group(1).strip() if timestamp_match else None
        
        cmdline_match = re.search(patterns['cmdline'], content)
        cmdline = cmdline_match.group(1).strip() if cmdline_match else None
        
        # PID/TID 資訊
        pid_tid_match = re.search(patterns['pid_tid'], content)
        if pid_tid_match:
            pid = int(pid_tid_match.group(1))
            tid = int(pid_tid_match.group(2))
            thread_name = pid_tid_match.group(3).strip()
            process_name = pid_tid_match.group(4).strip() if pid_tid_match.group(4) else cmdline
        else:
            pid = tid = None
            thread_name = process_name = None
        
        # 信號資訊
        signal_match = re.search(patterns['signal_info'], content)
        if signal_match:
            signal_num = int(signal_match.group(1))
            signal_name = signal_match.group(2)
        else:
            signal_num = signal_name = None
        
        # 錯誤地址
        fault_match = re.search(patterns['fault_addr'], content)
        fault_addr = fault_match.group(1) if fault_match else None
        
        # Abort 訊息
        abort_match = re.search(patterns['abort_message'], content)
        abort_message = abort_match.group(1).strip() if abort_match else None
        
        # 分析崩潰類型和嚴重程度
        crash_type = self._determine_crash_type(signal_name, abort_message, content)
        severity = self._calculate_crash_severity(crash_type, signal_name, fault_addr)
        
        # 統計 backtrace 深度
        backtrace_count = len(re.findall(patterns['backtrace_line'], content, re.MULTILINE))
        
        return {
            'log_type': 'android_tombstone',
            'build_fingerprint': build_fingerprint,
            'timestamp': timestamp,
            'pid': pid,
            'tid': tid,
            'thread_name': thread_name,
            'process_name': process_name or cmdline,
            'signal_num': signal_num,
            'signal_name': signal_name,
            'fault_addr': fault_addr,
            'abort_message': abort_message,
            'crash_type': crash_type,
            'severity': severity,
            'backtrace_depth': backtrace_count,
            'file_size_mb': len(content) / (1024 * 1024),
        }
    
    def _determine_crash_type(self, signal_name: Optional[str], 
                             abort_message: Optional[str], 
                             content: str) -> str:
        """判斷崩潰類型"""
        if signal_name == "SIGSEGV":
            if "null pointer" in content.lower():
                return "null_pointer_dereference"
            return "segmentation_fault"
        elif signal_name == "SIGABRT":
            if abort_message:
                if "assertion" in abort_message.lower():
                    return "assertion_failure"
                elif "check" in abort_message.lower():
                    return "check_failure"
            return "abort"
        elif signal_name == "SIGBUS":
            return "bus_error"
        elif signal_name == "SIGILL":
            return "illegal_instruction"
        elif signal_name == "SIGFPE":
            return "arithmetic_exception"
        elif "stack corruption" in content.lower():
            return "stack_corruption"
        elif "heap corruption" in content.lower():
            return "heap_corruption"
        else:
            return "unknown_crash"
    
    def _calculate_crash_severity(self, crash_type: str, 
                                 signal_name: Optional[str], 
                                 fault_addr: Optional[str]) -> str:
        """計算崩潰嚴重程度"""
        # 關鍵崩潰類型
        critical_types = [
            "heap_corruption",
            "stack_corruption",
            "segmentation_fault",
        ]
        
        # 高嚴重度崩潰
        high_types = [
            "null_pointer_dereference",
            "abort",
            "assertion_failure",
        ]
        
        if crash_type in critical_types:
            return "critical"
        elif crash_type in high_types:
            return "high"
        elif signal_name in ["SIGKILL", "SIGSTOP"]:
            return "medium"
        else:
            return "low"
    
    def parse_content(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """解析 Tombstone 內容"""
        documents = []
        
        # 1. 創建崩潰摘要
        summary_content = self._create_crash_summary(log_info)
        summary_doc = self.create_document(
            summary_content,
            file_path,
            {
                'chunk_method': 'tombstone_summary',
                'chunk_type': 'crash_summary',
                'crash_type': log_info.get('crash_type', 'unknown'),
                'severity': log_info.get('severity', 'unknown'),
                **log_info
            }
        )
        documents.append(summary_doc)
        
        # 2. 提取崩潰上下文
        crash_context_doc = self._extract_crash_context(content, file_path, log_info)
        if crash_context_doc:
            documents.append(crash_context_doc)
        
        # 3. 提取 backtrace
        backtrace_docs = self._extract_backtrace(content, file_path, log_info)
        documents.extend(backtrace_docs)
        
        # 4. 提取寄存器和記憶體資訊（用於深度分析）
        technical_doc = self._extract_technical_details(content, file_path, log_info)
        if technical_doc:
            documents.append(technical_doc)
        
        return documents
    
    def _create_crash_summary(self, log_info: Dict[str, Any]) -> str:
        """創建崩潰摘要"""
        summary = f"""Android Tombstone 崩潰分析
==============================
進程: {log_info.get('process_name', 'Unknown')}
PID/TID: {log_info.get('pid', '?')}/{log_info.get('tid', '?')}
線程名: {log_info.get('thread_name', 'Unknown')}
時間: {log_info.get('timestamp', 'Unknown')}

崩潰資訊:
- 信號: {log_info.get('signal_name', 'Unknown')} ({log_info.get('signal_num', '?')})
- 崩潰類型: {log_info.get('crash_type', 'Unknown').replace('_', ' ').title()}
- 嚴重程度: {log_info.get('severity', 'Unknown').upper()}
- 錯誤地址: {log_info.get('fault_addr', 'N/A')}
"""
        
        if log_info.get('abort_message'):
            summary += f"- Abort 訊息: {log_info['abort_message']}\n"
        
        summary += f"""
堆疊資訊:
- Backtrace 深度: {log_info.get('backtrace_depth', 0)} 層

Build: {log_info.get('build_fingerprint', 'Unknown')}
"""
        
        return summary
    
    def _extract_crash_context(self, content: str, file_path: str, log_info: Dict[str, Any]) -> Optional[Document]:
        """提取崩潰上下文"""
        patterns = self.get_patterns()
        
        # 找到崩潰的核心部分
        context_lines = []
        lines = content.split('\n')
        
        # 標記關鍵部分
        in_key_section = False
        section_start_patterns = [
            r'signal \d+',
            r'Abort message:',
            r'Cause:',
            r'backtrace:',
        ]
        
        for i, line in enumerate(lines):
            # 檢查是否進入關鍵部分
            if any(re.search(pattern, line) for pattern in section_start_patterns):
                in_key_section = True
                # 包含前面幾行上下文
                start = max(0, i - 3)
                context_lines.extend(lines[start:i])
            
            if in_key_section:
                context_lines.append(line)
                
                # 如果遇到 backtrace 結束或記憶體映射開始，停止
                if re.match(r'^(stack:|memory map:|registers:)', line):
                    break
        
        if context_lines:
            context_content = '\n'.join(context_lines)
            return self.create_document(
                context_content,
                file_path,
                {
                    'chunk_method': 'tombstone_context',
                    'chunk_type': 'crash_context',
                    'crash_type': log_info.get('crash_type', 'unknown'),
                    'severity': log_info.get('severity', 'unknown'),
                }
            )
        
        return None
    
    def _extract_backtrace(self, content: str, file_path: str, log_info: Dict[str, Any]) -> List[Document]:
        """提取 backtrace"""
        documents = []
        patterns = self.get_patterns()
        
        # 找到 backtrace 部分
        backtrace_start = content.find('backtrace:')
        if backtrace_start == -1:
            return documents
        
        # 找到 backtrace 結束位置
        backtrace_end_patterns = [
            '\nstack:',
            '\nmemory map:',
            '\nregisters:',
            '\n\n\n'
        ]
        
        backtrace_end = len(content)
        for pattern in backtrace_end_patterns:
            pos = content.find(pattern, backtrace_start)
            if pos != -1 and pos < backtrace_end:
                backtrace_end = pos
        
        backtrace_content = content[backtrace_start:backtrace_end]
        
        # 解析 backtrace 行
        backtrace_lines = []
        for line in backtrace_content.split('\n'):
            match = re.match(patterns['backtrace_line'], line)
            if match:
                frame_num = match.group(1)
                pc_addr = match.group(2)
                location = match.group(3)
                symbol = match.group(4) if match.group(4) else ""
                
                backtrace_lines.append({
                    'frame': int(frame_num),
                    'pc': pc_addr,
                    'location': location,
                    'symbol': symbol
                })
        
        if backtrace_lines:
            # 創建簡化的 backtrace（前10個最重要的幀）
            important_frames = backtrace_lines[:10]
            simplified_backtrace = "Backtrace (崩潰堆疊):\n"
            simplified_backtrace += "=" * 50 + "\n"
            
            for frame in important_frames:
                simplified_backtrace += f"#{frame['frame']:02d} {frame['location']}"
                if frame['symbol']:
                    simplified_backtrace += f" ({frame['symbol']})"
                simplified_backtrace += "\n"
            
            doc = self.create_document(
                simplified_backtrace,
                file_path,
                {
                    'chunk_method': 'tombstone_backtrace',
                    'chunk_type': 'backtrace',
                    'frame_count': len(backtrace_lines),
                    'crash_type': log_info.get('crash_type', 'unknown'),
                }
            )
            documents.append(doc)
        
        return documents
    
    def _extract_technical_details(self, content: str, file_path: str, log_info: Dict[str, Any]) -> Optional[Document]:
        """提取技術細節（寄存器、記憶體等）"""
        # 只在崩潰嚴重程度高時提取這些細節
        if log_info.get('severity') not in ['critical', 'high']:
            return None
        
        technical_sections = []
        
        # 提取寄存器資訊
        registers_start = content.find('registers:')
        if registers_start != -1:
            registers_end = content.find('\n\n', registers_start)
            if registers_end == -1:
                registers_end = len(content)
            
            registers_section = content[registers_start:registers_end]
            technical_sections.append("寄存器狀態:\n" + registers_section)
        
        # 提取關鍵記憶體映射（只取前幾行）
        memory_start = content.find('memory map:')
        if memory_start != -1:
            memory_lines = content[memory_start:].split('\n')[:20]
            technical_sections.append("記憶體映射（部分）:\n" + '\n'.join(memory_lines))
        
        if technical_sections:
            technical_content = '\n\n'.join(technical_sections)
            return self.create_document(
                technical_content,
                file_path,
                {
                    'chunk_method': 'tombstone_technical',
                    'chunk_type': 'technical_details',
                    'severity': log_info.get('severity', 'unknown'),
                }
            )
        
        return None