import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.types import (
    VARCHAR, Date, Integer, Numeric, SmallInteger
)

# Force UTF-8 output so Unicode chars print correctly on Windows
sys.stdout.reconfigure(encoding='utf-8')

#------config------------------------------
DB_USER="postgres"
DB_PASSWORD="****"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="employee_performance"
CSV_PATH=r"J:\python\DA_project\SQL Projects\Employee Performance Dashboard_HR\data\employee_data.csv"
TABLE_NAME="employee_performance"

np.random.seed(42)    #reproducibe results

df=pd.read_csv(CSV_PATH)
print("Original Shape:",df.shape)
print("\nColumns:",df.columns.tolist())    #Columns names

# ── 1. Standardize column names ──────────────────────────
df.columns=(
    df.columns
    .str.strip()
    .str.replace(r'[^a-zA-Z0-9]', '_', regex=True)
    .str.lower()
    .str.strip('_')
)
print("\n Renamed Columns:",df.columns.tolist())

# ── 2. Parse dates ────────────────────────────────────────
df['start_date']=pd.to_datetime(df['startdate'],errors='coerce',format='mixed')
df['exit_date']=pd.to_datetime(df['exitdate'],errors='coerce',format='mixed')
df['dob']=pd.to_datetime(df['dob'],errors='coerce',format='mixed')

refrance_date=pd.Timestamp('2024-01-01')  #anchor date for calculations

# ── 3. Calculate tenure in months ────────────────────────
# Active employees: tenure to reference date
# Terminated employees: tenure to exit date
df['end_for_cal']=df['exit_date'].fillna(refrance_date)
df['tenure_months']=((df['end_for_cal']-df['start_date'])
.dt.days // 30
).clip(lower=0)
df['tenure_years']=(df['tenure_months']/12).round(2)

# ── 4. Calculate age ──────────────────────────────────────
df['age']=(
    (refrance_date-df['dob']).dt.days//365
).clip(lower=18,upper=80)

# ── 5. Map Pay Zone to Monthly Salary ────────────────────
# Zone D = senior/executive level (highest)
# Zone C = mid-senior
# Zone B = mid level
# Zone A = entry/junior level
pay_zone_salary_ranges={
    'Zone A':(30000,55000),
    'Zone B':(55000,90000),
    'Zone C':(90000,140000),
    'Zone D':(140000,220000)
}
# NOTE: After column standardisation 'PayZone' → 'payzone', 'Performance Score' → 'performance_score'
def assign_salary(row):
    zone = str(row.get('payzone','')).strip()
    if zone not in pay_zone_salary_ranges:
        return np.random.randint(30000,60000)   #fallback
    low,high=pay_zone_salary_ranges[zone]

    # Performance modifier: high performers earn toward upper end
    perf=str(row.get('performance_score','')).strip().lower()
    if perf == 'exceeds':
        modifier=0.75  #upper 25% range
    elif perf=='fully meets':
        modifier=0.50 #mid of range
    elif perf=='needs improvement':
        modifier=0.25 # lower 25% of range
    else: 
        modifier=0.50    #random for unknowns

    #Add randomness around he modifier
    noise  = np.random.uniform(-0.10,0.10)  #+/-10%
    factor=min(max(modifier + noise,0),1)
    salary=int(low + factor*(high-low))

    #run to nearest 50 
    return round(salary/50)*50
df['monthly_salary']=df.apply(assign_salary, axis=1)
#add annual salary
df['annual_salary']=df['monthly_salary']*12

# employeestatus values: 'Voluntarily Terminated', 'Terminated for Cause',
# 'Active', 'Future Start', 'Leave of Absence'
# Both terminated categories contain the word 'terminated' -> use 'in' not ==
df['is_terminated']=df['employeestatus'].apply(
    lambda x: 1 if 'terminated' in str(x).strip().lower() else 0
)

# ── 7. Map Performance Score to numeric ──────────────────
perf_map={
    'exceeds': 4,
    'fully meets': 3,
    'needs improvement':1,
    'pip': 1 #performance improvment plan
}
df['performance_score_num']=(
    df['performance_score'].str.strip().str.lower().map(perf_map)
    .fillna(3)  #default to 3 for fully meets
    .astype(int)
)

# ── 8. Drop helper columns ────────────────────────────────
df.drop(columns=['end_for_cal'],inplace=True,errors='ignore')

# ── 9. Validation ─────────────────────────────────────────
print("\n Salary By Pay Zone")
print(df.groupby('payzone')['monthly_salary'].agg(['min','max','mean']).round(0))  

print("\n Tenure Stats:")
print(df['tenure_months'].describe().round(1))

print("\n Age Stats:")
print(df['age'].describe().round(1))

print("\n Termination Count")
print(df['is_terminated'].value_counts())

print("\n Performance Distribution")
print(df['performance_score'].value_counts())

print("Final Columns:")
print(df.columns.tolist())
print(df.head(10))

# ── 10. Load to PostgreSQL ────────────────────────────────
print("\n--- Loading data into PostgreSQL ---")

# Explicit dtype mapping → controls the DDL that SQLAlchemy generates
DTYPE_MAP = {
    # ── original text columns ──────────────────────────────
    'empid'                     : VARCHAR(20),
    'firstname'                 : VARCHAR(100),
    'lastname'                  : VARCHAR(100),
    'startdate'                 : VARCHAR(30),   # raw string kept for reference
    'exitdate'                  : VARCHAR(30),   # raw string kept for reference
    'title'                     : VARCHAR(150),
    'supervisor'                : VARCHAR(150),
    'ademail'                   : VARCHAR(200),
    'businessunit'              : VARCHAR(100),
    'employeestatus'            : VARCHAR(50),
    'employeetype'              : VARCHAR(50),
    'payzone'                   : VARCHAR(20),
    'employeeclassificationtype': VARCHAR(100),
    'terminationtype'           : VARCHAR(100),
    'terminationdescription'    : VARCHAR(255),
    'departmenttype'            : VARCHAR(100),
    'division'                  : VARCHAR(100),
    'state'                     : VARCHAR(50),
    'jobfunctiondescription'    : VARCHAR(200),
    'gendercode'                : VARCHAR(20),
    'locationcode'              : VARCHAR(20),
    'racedesc'                  : VARCHAR(100),
    'maritaldesc'               : VARCHAR(50),
    'performance_score'         : VARCHAR(50),
    # ── parsed / derived columns ───────────────────────────
    'dob'                       : Date(),
    'start_date'                : Date(),
    'exit_date'                 : Date(),
    'tenure_months'             : Integer(),
    'tenure_years'              : Numeric(6, 2),
    'age'                       : SmallInteger(),
    'monthly_salary'            : Integer(),
    'annual_salary'             : Integer(),
    'current_employee_rating'   : SmallInteger(),
    'is_terminated'             : SmallInteger(),
    'performance_score_num'     : SmallInteger(),
}

# Build connection string and engine
CONN_STR = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
engine = create_engine(CONN_STR)

# Push DataFrame → PostgreSQL
# if_exists='replace' : drops & recreates the table on every run
# Change to 'append'  : to keep existing rows and just add new ones
df.to_sql(
    name      = TABLE_NAME,
    con       = engine,
    if_exists = 'replace',   # recreates table; use 'append' to add rows
    index     = False,
    dtype     = DTYPE_MAP,
    chunksize = 500,         # batch inserts for better performance
    method    = 'multi',
)

# ── 11. Verify upload ─────────────────────────────────────
with engine.connect() as conn:
    row_count = conn.execute(
        text(f'SELECT COUNT(*) FROM "{TABLE_NAME}"')
    ).scalar()

print(f"\n[OK] Table '{TABLE_NAME}' created successfully in '{DB_NAME}'.")
print(f"     Rows in DB  : {row_count:,}")
print(f"    Rows in df  : {len(df):,}")
print(f"    Columns     : {len(df.columns)}")
