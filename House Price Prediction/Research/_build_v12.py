import os

out_path = os.path.join(os.path.dirname(__file__), 'train_master.py')

code = []
code.append('"""')
code.append('Single-file V12 training script. This file is the new, consolidated ML model training entrypoint.')
code.append('"""')
code.append('')

# imports
code += [
'import os',
'import json',
'import warnings',
'import numpy as np',
'import pandas as pd',
'from sklearn.model_selection import train_test_split, KFold',
'from sklearn.metrics import mean_absolute_percentage_error, r2_score',
'from sklearn.linear_model import Ridge',
'from sklearn.ensemble import IsolationForest',
'from sklearn.preprocessing import OneHotEncoder',
'import optuna',
'optuna.logging.set_verbosity(optuna.logging.WARNING)',
'import xgboost as xgb',
'import lightgbm as lgb',
'import catboost as cb',
'import category_encoders as ce',
'import joblib',
'from sklearn.cluster import MiniBatchKMeans',
'from underthesea import text_normalize',
'warnings.filterwarnings("ignore")',
'',
]

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(code) + '\n')

print('Wrote', out_path)
