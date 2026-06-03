"""F8 ROR distribution / volcano plot."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import plotly.express as px
import streamlit as st

import data as D
import ui

ui.page_setup("Volcano")
st.title("ROR distribution & volcano plot")
st.caption("Signal strength (ROR) versus the amount of evidence (number of co-reports "
           "`a`). High-ROR / low-`a` points top-left are the fragile signals; "
           "high-ROR / high-`a` points top-right are the robust ones.")
ui.require_db()

df = D.ror_sample()
if df.empty:
    st.info("No signal data.")
    st.stop()

df = df.copy()
df["log_ror"] = np.log10(df["ror"].clip(lower=1e-9))
df["pair"] = df["drug_a_name"].fillna(df["drug_a"]) + " + " + \
    df["drug_b_name"].fillna(df["drug_b"])

tab1, tab2 = st.tabs(["Volcano (ROR vs evidence)", "ROR distribution"])

with tab1:
    fig = px.scatter(
        df, x="a", y="ror", log_x=True, log_y=True, opacity=0.45,
        color="log_ror", color_continuous_scale="Plasma",
        hover_data={"pair": True, "reaction": True, "a": True,
                    "ror": ":.1f", "log_ror": False},
        labels={"a": "Co-reports a (log)", "ror": "ROR (log)"},
    )
    fig.update_layout(height=620, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width='stretch')
    st.caption("Sampled top signals bucketed by evidence level so the plot is not "
               "swamped by the millions of minimum-evidence points.")

with tab2:
    # Histogram in log space (binning ROR linearly over a 2..22M range collapses
    # almost everything into one bar), then relabel ticks with real ROR values.
    fig2 = px.histogram(df, x="log_ror", nbins=60, labels={"log_ror": "ROR (log scale)"})
    lo = int(np.floor(df["log_ror"].min()))
    hi = int(np.ceil(df["log_ror"].max()))
    tickvals = list(range(lo, hi + 1))

    def _fmt(v: int) -> str:
        val = 10 ** v
        if val >= 1e6:
            return f"{val/1e6:g}M"
        if val >= 1e3:
            return f"{val/1e3:g}k"
        return f"{val:g}"

    fig2.update_xaxes(tickvals=tickvals, ticktext=[_fmt(v) for v in tickvals])
    fig2.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10),
                       yaxis_title="signals (sampled)")
    st.plotly_chart(fig2, width='stretch')

ui.download_df(df, "ror_sample.csv", "Download sampled points (CSV)")
