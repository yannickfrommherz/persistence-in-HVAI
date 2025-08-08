import pandas as pd
import sys
sys.path.append("../../../code/")
import annotation

alternating = "alternating_nonagentivity_nonprimed"

alternation_set = ["man", "werden"]

df = pd.read_csv("../../RBC.csv", sep=",", index_col=0, na_filter=False)

if not alternating in df.columns:
    df[alternating] = ""

df_updated = annotation.alternation_check(df, alternation_set, alternating)

df_updated.to_csv("../../RBC.csv")

