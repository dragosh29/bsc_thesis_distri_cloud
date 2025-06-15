import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_node_distribution_results(csv_path, output_prefix="execution_analysis"):
    try:
        df = pd.read_csv(csv_path, parse_dates=['assigned_at', 'completed_at'])
    except Exception as e:
        print(f"Error reading CSV file: {csv_path}\n{e}")
        return None

    scenario_starts = df.groupby(['N', 'M', 'algorithm'])['assigned_at'].min().reset_index()
    scenario_starts.rename(columns={'assigned_at': 'scenario_start'}, inplace=True)
    df = pd.merge(df, scenario_starts, on=['N', 'M', 'algorithm'], how='left')

    df['wait_time'] = (df['completed_at'] - df['scenario_start']).dt.total_seconds()
    grouped = df.groupby(['N', 'M', 'algorithm'])

    summary = grouped.agg(
        avg_wait_time=('wait_time', 'mean'),
        min_wait_time=('wait_time', 'min'),
        max_wait_time=('wait_time', 'max'),
        total_execution_time=('completed_at', lambda x: (x.max() - df.loc[x.index, 'scenario_start'].min()).total_seconds()),
        avg_work_duration=('work_duration', 'mean'),
        avg_stale_count=('stale_count', 'mean'),
        task_count=('task_id', 'nunique'),
    ).reset_index()

    summary_path = f"{output_prefix}_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"\nSaved summary to {summary_path}")

    melted = summary.melt(
        id_vars=['N', 'M', 'algorithm'],
        value_vars=['min_wait_time', 'avg_wait_time', 'max_wait_time'],
        var_name='wait_type',
        value_name='wait_time'
    )

    for (n_val, m_val), group in melted.groupby(['N', 'M']):
        plt.figure(figsize=(8, 5))
        pivot = group.pivot(index='algorithm', columns='wait_type', values='wait_time')
        pivot = pivot[['min_wait_time', 'avg_wait_time', 'max_wait_time']]
        ax = pivot.plot(kind='bar', ax=plt.gca(), rot=0)

        for container in ax.containers:
            for bar in container:
                height = bar.get_height()
                if not pd.isna(height):
                    ax.annotate(f'{height:.1f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9, color='black')

        plt.title(f"Min, Avg, Max Wait Times per Algorithm\nN={n_val} Nodes, M={m_val} Tasks")
        plt.ylabel("Wait Time (seconds)")
        plt.xlabel("Algorithm")
        plt.tight_layout()
        outname = f"{output_prefix}_wait_times_N{n_val}_M{m_val}.png"
        plt.savefig(outname)
        print(f"Saved plot: {outname}")
        plt.close()

    print("\nAll done!")
    return summary

if __name__ == "__main__":
    analyze_node_distribution_results("node_distribution_experiment_results_1.csv")