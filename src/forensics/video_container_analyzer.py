"""
Video container analysis - detect MP4/MKV anomalies and appended payloads.
"""
from pathlib import Path
from typing import Dict, Any, List
import struct


class MP4Parser:
    """Parse MP4 file structure and detect anomalies."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_size = self.file_path.stat().st_size
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse MP4 file structure.
        
        Returns:
            Dict with structure analysis and anomalies
        """
        anomalies = []
        boxes = []
        
        try:
            with open(self.file_path, 'rb') as f:
                # Parse MP4 boxes
                boxes = self._parse_boxes(f)
                
                # Check for appended data
                last_box_end = 0
                for box in boxes:
                    last_box_end = max(last_box_end, box['end'])
                
                if last_box_end < self.file_size:
                    appended_size = self.file_size - last_box_end
                    anomalies.append({
                        'type': 'appended_data',
                        'size_bytes': appended_size,
                        'percentage': round(100 * appended_size / self.file_size, 2),
                        'suspicion_score': min(100.0, appended_size * 10 / self.file_size)
                    })
            
            # Check for missing moov box (video might be incomplete/corrupted)
            moov_found = any(box['type'] == 'moov' for box in boxes)
            if not moov_found:
                anomalies.append({
                    'type': 'missing_moov',
                    'description': 'MP4 missing critical moov (movie) box',
                    'suspicion_score': 30.0
                })
            
            # Check for multiple mdat boxes (unusual)
            mdat_count = sum(1 for box in boxes if box['type'] == 'mdat')
            if mdat_count > 1:
                anomalies.append({
                    'type': 'multiple_mdat',
                    'count': mdat_count,
                    'suspicion_score': 20.0
                })
        
        except Exception as e:
            anomalies.append({
                'type': 'parse_error',
                'error': str(e),
                'suspicion_score': 0.0
            })
        
        # Calculate overall score
        overall_score = sum(a.get('suspicion_score', 0) for a in anomalies)
        overall_score = min(100.0, overall_score)
        
        return {
            'format': 'MP4',
            'file_size': self.file_size,
            'boxes': boxes,
            'anomalies': anomalies,
            'suspicion_score': round(overall_score, 2),
            'is_suspicious': overall_score > 20.0
        }
    
    def _parse_boxes(self, f) -> List[Dict[str, Any]]:
        """Parse MP4 box hierarchy."""
        boxes = []
        offset = 0
        
        while offset < self.file_size:
            f.seek(offset)
            size_bytes = f.read(4)
            
            if len(size_bytes) < 4:
                break
            
            size = struct.unpack('>I', size_bytes)[0]
            box_type_bytes = f.read(4)
            
            if len(box_type_bytes) < 4:
                break
            
            box_type = box_type_bytes.decode('ascii', errors='ignore')
            
            boxes.append({
                'offset': offset,
                'size': size,
                'type': box_type,
                'end': offset + size
            })
            
            if size == 0:
                break
            
            offset += size
        
        return boxes


class MKVParser:
    """Parse MKV/WebM file structure (EBML format)."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_size = self.file_path.stat().st_size
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse MKV file structure.
        
        Returns:
            Dict with structure analysis
        """
        anomalies = []
        
        try:
            with open(self.file_path, 'rb') as f:
                # Check for EBML header
                header = f.read(4)
                if header != b'\x1a\x45\xdf\xa3':  # EBML magic
                    anomalies.append({
                        'type': 'invalid_ebml_header',
                        'suspicion_score': 50.0
                    })
                
                # Check for appended data (crude check)
                f.seek(0, 2)  # Seek to end
                end_pos = f.tell()
                
                # Try to find last EBML element
                # This is simplified; full EBML parsing is complex
                f.seek(max(0, end_pos - 1024))
                tail = f.read()
                
                # Check if there's random data at end (sign of appended payload)
                entropy = self._calculate_entropy(tail)
                if entropy > 7.5:  # High entropy suggests random data
                    anomalies.append({
                        'type': 'high_entropy_tail',
                        'entropy': round(entropy, 2),
                        'suspicion_score': 25.0
                    })
        
        except Exception as e:
            anomalies.append({
                'type': 'parse_error',
                'error': str(e),
                'suspicion_score': 0.0
            })
        
        overall_score = sum(a.get('suspicion_score', 0) for a in anomalies)
        overall_score = min(100.0, overall_score)
        
        return {
            'format': 'MKV',
            'file_size': self.file_size,
            'anomalies': anomalies,
            'suspicion_score': round(overall_score, 2),
            'is_suspicious': overall_score > 20.0
        }
    
    @staticmethod
    def _calculate_entropy(data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0.0
        
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1
        
        entropy = 0.0
        for count in freq.values():
            p = count / len(data)
            entropy -= p * (p and __import__('math').log2(p))
        
        return entropy


class VideoContainerAnalyzer:
    """Analyze video container formats for anomalies."""
    
    @staticmethod
    def analyze(file_path: str) -> Dict[str, Any]:
        """
        Analyze video container based on format.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Analysis result dict
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext in {'.mp4', '.m4a', '.m4v'}:
            parser = MP4Parser(file_path)
            return parser.parse()
        elif ext in {'.mkv', '.mka', '.mks', '.webm'}:
            parser = MKVParser(file_path)
            return parser.parse()
        else:
            return {
                'format': ext,
                'error': f'Unsupported container format: {ext}',
                'suspicion_score': 0.0
            }
