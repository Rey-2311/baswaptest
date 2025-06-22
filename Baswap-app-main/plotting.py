import streamlit as st
import altair as alt
import pandas as pd
from model import LITModel, LSTMTimeseries
import pytorch_lightning as pl
import numpy as np
import torch
from model import make_predictions

def plot_line_chart(df, col, resample_freq="None"):
    if col not in df.columns:
        st.error(f"Column '{col}' not found in DataFrame.")
        return

    df_filtered = df.copy()

    color_scale = alt.Scale(
            domain=["Raw", "Max", "Min", "Median"],
            range=["orange", "red", "blue", "green"]
        )

    if resample_freq == "None":
        df_filtered["Aggregation"] = "Raw"
        chart = (
            alt.Chart(df_filtered)
            .mark_line(point=True)
            .encode(
                x=alt.X("Timestamp (GMT+7):T", title="Timestamp"),
                y=alt.Y(f"{col}:Q", title="Value"),
                color=alt.Color("Aggregation:N", title="Aggregation", scale=color_scale),
                tooltip=[
                    alt.Tooltip("Timestamp (GMT+7):T", title="Exact Time", format="%d/%m/%Y %H:%M:%S"),
                    alt.Tooltip(f"{col}:Q", title="Value")
                ],
            )
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        # Create a rounded timestamp based on resample frequency.
        if resample_freq == "Hour":
            df_filtered["Timestamp (Rounded)"] = df_filtered["Timestamp (GMT+7)"].dt.floor('h')
        elif resample_freq == "Day":
            df_filtered["Timestamp (Rounded)"] = df_filtered["Timestamp (GMT+7)"].dt.floor('d')
        else:
            df_filtered["Timestamp (Rounded)"] = df_filtered["Timestamp (GMT+7)"]

        df_filtered["Timestamp (Rounded Display)"] = df_filtered["Timestamp (Rounded)"].dt.strftime(
            r"%H:%M:%S" if resample_freq == "Hour" else "%d/%m/%Y"
        )

        # Build the main chart for all data.
        main_chart = (
            alt.Chart(df_filtered)
            .mark_line(point=True)
            .encode(
                x=alt.X("Timestamp (Rounded):T", title="Timestamp"),
                y=alt.Y(f"{col}:Q", title="Value"),
                color=alt.Color("Aggregation:N", title="Aggregation", scale=color_scale),
                tooltip=[
                    alt.Tooltip("Timestamp (Rounded Display):N", title="Rounded Time"),
                    alt.Tooltip("Timestamp (GMT+7):T", title="Exact Time", format="%d/%m/%Y %H:%M:%S"),
                    alt.Tooltip(f"{col}:Q", title="Value"),
                    alt.Tooltip("Aggregation:N", title="Aggregation")
                ]
            )
            .interactive()
        )

        if resample_freq == "Hour" and col in ["EC Value (us/cm)", "EC Value (g/l)"]:
            # Filter the "Max" aggregation points.
            max_data = df_filtered[df_filtered["Aggregation"] == "Max"]

            # Extract only the numeric values from the last 7 points.
            max_values_numeric = max_data[[col]].iloc[-7:]
            
            # Get the last timestamp and last value from the max data.
            last_timestamp = max_data["Timestamp (Rounded)"].iloc[-1]
            last_value = max_values_numeric.iloc[-1][col]

            if (col == "EC Value (g/l)"):
                max_values_numeric = max_values_numeric * 2000

            # Call your prediction function, which now returns a list of predicted values.
            predictions_list = make_predictions(max_values_numeric, mode="Max")

            if (col == "EC Value (g/l)"):
                predictions_list = [x/2000 for x in predictions_list]
            
            # Create new timestamps for each prediction by adding one hour for each prediction.
            prediction_timestamps = [
                last_timestamp + pd.Timedelta(hours=i+1) for i in range(len(predictions_list))
            ]
            
            # To connect the prediction line to the max graph, prepend the last max point.
            combined_timestamps = [last_timestamp] + prediction_timestamps
            combined_values = [last_value] + predictions_list
            
            # Create a DataFrame that includes the connecting point and the predictions.
            predictions_line_df = pd.DataFrame({
                "Timestamp": combined_timestamps,
                col: combined_values,
                "Aggregation": "Predicted"
            })
            
            # Create a dashed line chart for the prediction segment (which now starts at the last max point).
            predictions_chart = (
                alt.Chart(predictions_line_df)
                .mark_line(color='red', strokeDash=[5, 5], point=alt.OverlayMarkDef(color="red"))
                .encode(
                    x=alt.X("Timestamp:T", title="Timestamp"),
                    y=alt.Y(f"{col}:Q", title="Value"),
                    tooltip=[
                        alt.Tooltip("Timestamp:T", title="Predicted Time", format="%d/%m/%Y %H:%M:%S"),
                        alt.Tooltip(f"{col}:Q", title="Predicted Value"),
                        alt.Tooltip("Aggregation:N", title="Aggregation")
                    ]
                )
            )
            
            # Combine the main chart with the predictions chart.
            combined_chart = alt.layer(predictions_chart, main_chart).resolve_scale(
                color='independent'
            )
            st.altair_chart(combined_chart, use_container_width=True)
        else:
            st.altair_chart(main_chart, use_container_width=True)


def display_statistics(df, target_col):
    st.subheader("**📊 Overall Statistics (Raw Data)**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Maximum", value=f"{df[target_col].max():.2f}")
    col2.metric(label="Minimum", value=f"{df[target_col].min():.2f}")
    col3.metric(label="Average", value=f"{df[target_col].mean():.2f}")
    col4.metric(label="Std Dev", value=f"{df[target_col].std():.2f}")
