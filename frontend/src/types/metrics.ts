export interface MetricStats {
    min: number;
    q1: number;
    median: number;
    q3: number;
    max: number;
    mean: number;
    outliers: number[];
}

export interface ToolMetrics {
    execution: MetricStats;
    cpu: MetricStats;
    memory: MetricStats;
}

export type StatsData = Record<string, ToolMetrics>;

export type MetricKey = "execution" | "cpu" | "memory";
