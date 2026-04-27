import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md(
        """
        # 0DTE SPX/SPXW Inventory Reference App

        Scope: scaffold-only marimo app for a professional reference document,
        deterministic inventory adjustment playbook, and session-specific prompt
        workflow. It does not provide live data, fabricated Greeks, bid/asks,
        fills, P/L, signals, or automated trade recommendations.
        """
    )
    return


if __name__ == "__main__":
    app.run()
