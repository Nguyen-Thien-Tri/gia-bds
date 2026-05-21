import pandas as pd

def check_coords():
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    x_col = 'Tọa độ x'
    y_col = 'Tọa độ y'
    
    with open('coords_debug.txt', 'w', encoding='utf-8') as f:
        f.write("Sample Coordinates:\n")
        f.write(df[[x_col, y_col]].head(20).to_string())
        f.write("\n\nCoordinate Stats:\n")
        f.write(df[[x_col, y_col]].describe().to_string())

if __name__ == "__main__":
    check_coords()
