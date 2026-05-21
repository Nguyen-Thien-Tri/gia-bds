import pandas as pd

def compare_addresses():
    df = pd.read_csv('filtered_hanoi_data.csv', nrows=50, encoding='utf-8')
    with open('addr_comparison.txt', 'w', encoding='utf-8') as f:
        f.write("Comparing Address 1 and Address 2:\n")
        for i, row in df.iterrows():
            f.write(f"Row {i}:\n")
            f.write(f"  Addr 1: {row['Địa chỉ 1']}\n")
            f.write(f"  Addr 2: {row['Địa chỉ 2']}\n")
            f.write("-" * 20 + "\n")

if __name__ == "__main__":
    compare_addresses()
