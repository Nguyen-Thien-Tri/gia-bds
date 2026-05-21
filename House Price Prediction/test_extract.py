import pandas as pd
import re

def extract_alley_width(text):
    text = str(text).lower()
    # Match patterns like "ngõ 3m", "ngõ 3.5m", "ngõ rộng 4m"
    match = re.search(r'ngõ (?:rộng )?(\d+(?:\.\d+)?)m', text)
    if match:
        return float(match.group(1))
    
    # Keyword based
    if 'ô tô tránh' in text or 'ô tô đỗ cửa' in text or 'ô tô vào nhà' in text:
        return 4.0
    if 'xe hơi' in text or 'xe tải' in text:
        return 4.0
    if 'xe máy tránh' in text:
        return 2.0
    if 'ngõ ba gác' in text:
        return 2.5
    
    return 2.0 # Default narrow alley for private houses

# Test on sample
sample_desc = "Nhà đẹp ngõ 3.5m Láng Hạ, ô tô đỗ cửa."
print(f"Test: {extract_alley_width(sample_desc)}")
