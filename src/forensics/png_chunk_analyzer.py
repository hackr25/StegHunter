import struct
from typing import Dict, Any, List


class PNGChunkAnalyzer:
    """
    PNG hidden chunk forensic detector.
    Inspects PNG chunk structure for ancillary payload hiding,
    metadata abuse, malformed chunks, and appended binary data.
    """

    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

    def __init__(self):
        self.suspicious_chunks = {"tEXt", "zTXt", "iTXt", "sTER", "vpAg"}

    def analyze(self, image_path: str) -> Dict[str, Any]:
        try:
            with open(image_path, "rb") as f:
                data = f.read()

            if not data.startswith(self.PNG_SIGNATURE):
                return {
                    "error": "Not a valid PNG file",
                    "suspicion_score": 0.0
                }

            offset = 8
            chunks: List[Dict[str, Any]] = []
            suspicious_score = 0.0
            suspicious_found = []
            iend_end = None

            while offset < len(data):
                if offset + 8 > len(data):
                    break

                length = struct.unpack(">I", data[offset:offset+4])[0]
                chunk_type = data[offset+4:offset+8].decode("latin1", errors="ignore")

                chunk_start = offset
                chunk_end = offset + 12 + length

                if chunk_end > len(data):
                    suspicious_score += 20
                    suspicious_found.append(f"Malformed chunk length in {chunk_type}")
                    break

                chunk_payload = data[offset+8:offset+8+length]

                chunks.append({
                    "type": chunk_type,
                    "length": length
                })

                # suspicious ancillary textual chunks
                if chunk_type in self.suspicious_chunks:
                    suspicious_score += min(15, length / 20)
                    suspicious_found.append(f"Ancillary chunk present: {chunk_type}")

                # unusually large unknown ancillary chunk
                if chunk_type[0].islower() and length > 512:
                    suspicious_score += 18
                    suspicious_found.append(f"Large ancillary chunk: {chunk_type}")

                if chunk_type == "IEND":
                    iend_end = chunk_end
                    break

                offset = chunk_end

            # Appended binary after IEND
            if iend_end is not None and iend_end < len(data):
                extra = len(data) - iend_end
                suspicious_score += min(30, extra / 10)
                suspicious_found.append(f"Appended data after IEND ({extra} bytes)")

            suspicion_score = min(100.0, suspicious_score)

            return {
                "chunk_count": len(chunks),
                "chunks": chunks[:15],
                "suspicious_indicators": suspicious_found,
                "suspicion_score": round(float(suspicion_score), 2),
                "method": "PNG Structural Chunk Forensics"
            }

        except Exception as e:
            return {
                "error": str(e),
                "suspicion_score": 0.0
            }