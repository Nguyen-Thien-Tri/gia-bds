import pandas as pd

def check():
    with open('ads_data_2026_03.csv', 'rb') as f:
        line = f.readline()
        print(f"Raw first line: {line[:200]}")
        
    try:
        df = pd.read_csv('ads_data_2026_03.csv', nrows=1, encoding='utf-8')
        print("UTF-8 worked")
    except Exception as e:
        print(f"UTF-8 failed: {e}")

    try:
        df = pd.read_csv('ads_data_2026_03.csv', nrows=1, encoding='latin1')
        print("Latin1 worked")
        print(df.columns.tolist())
    except Exception as e:
        print(f"Latin1 failed: {e}")

if __name__ == "__main__":
    check()
