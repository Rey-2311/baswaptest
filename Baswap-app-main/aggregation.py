import streamlit as st
import pandas as pd

def filter_data(df, date_from, date_to):
    filtered_df = df[(df["Timestamp (GMT+7)"].dt.date >= date_from) & 
                     (df["Timestamp (GMT+7)"].dt.date <= date_to)].copy()
    return filtered_df

def apply_aggregation(df, selected_cols, target_col, resample_freq, agg_functions):
    if resample_freq == "None":
        return df

    rule_map = {"Hour": "h", "Day": "d"}
    agg_map = {"Min": "min", "Max": "max", "Median": "median"}

    if not set(agg_functions).issubset(agg_map.keys()):
        st.error("Invalid aggregation functions selected.")
        return df

    df_resampled = df.set_index("Timestamp (GMT+7)")
    agg_results = []

    for agg_function in agg_functions:
        if agg_function in ["Min", "Max"]:
            idx_func = "idxmin" if agg_function == "Min" else "idxmax"
            grouped = df_resampled.groupby(pd.Grouper(freq=rule_map[resample_freq]))[target_col]
            idx = grouped.apply(lambda x: getattr(x, idx_func)() if not x.empty else None).dropna()
            agg_df = df_resampled.loc[idx].reset_index()
        elif agg_function == "Median":
            agg_series = df_resampled[target_col].resample(rule_map[resample_freq]).median()
            agg_df = agg_series.reset_index()

        agg_df["Aggregation"] = agg_function
        agg_results.append(agg_df)

    return pd.concat(agg_results, ignore_index=True)
