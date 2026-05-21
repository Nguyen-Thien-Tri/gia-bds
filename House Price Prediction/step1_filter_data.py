import pandas as pd
import numpy as np

def filter_data():
    file_path = 'ads_data_2026_03.csv'
    chunk_size = 50000
    
    # Target values - case insensitive or matching the dataset's style
    target_province = 'Hà Nội'
    target_types = ['căn hộ chung cư', 'nhà mặt phố', 'nhà riêng', 'đất']
    
    filtered_chunks = []
    
    print(f"Starting filtering...")
    
    try:
        # Index 6 is 'Loại BĐS', Index 7 is 'Tỉnh thành phố'
        reader = pd.read_csv(file_path, chunksize=chunk_size, encoding='utf-8', encoding_errors='replace', low_memory=False)
        
        for i, chunk in enumerate(reader):
            # Identifying columns by index to be absolutely sure
            col_type = chunk.columns[6]
            col_province = chunk.columns[7]

            # Filter
            mask = (chunk[col_province].str.contains(target_province, na=False)) & \
                   (chunk[col_type].str.lower().isin(target_types))
            
            filtered_chunk = chunk[mask]
            filtered_chunks.append(filtered_chunk)
            
            if (i+1) % 10 == 0:
                print(f"Processed {i+1} chunks...")
                
        if not filtered_chunks:
            print("No data found.")
            return

        full_df = pd.concat(filtered_chunks)
        print(f"Total rows after filtering: {len(full_df)}")
        
        # Save to CSV
        full_df.to_csv('filtered_hanoi_data.csv', index=False, encoding='utf-8')
        print("Saved to filtered_hanoi_data.csv")
        
    except Exception as e:
        print(f"Error during processing: {e}")

if __name__ == "__main__":
    filter_data()
