import Papa from "papaparse";

export interface MetricsData {
    Tool: string;
    "Execution Time (s)": number;
    "CPU Used (%)": number;
    "Memory Used (KB)": number;
}

/**
 * Parses CSV data from a blob
 * @param blob The CSV data as a blob
 * @returns Promise resolving to the parsed data
 */
export function parseCSVBlob(blob: Blob): Promise<MetricsData[]> {
    return new Promise((resolve, reject) => {
        // First convert the blob to text, then parse the text
        blob.text()
            .then((csvString) => {
                const results = Papa.parse<Record<string, string | number>>(csvString, {
                    header: true,
                    dynamicTyping: true,
                    skipEmptyLines: true,
                });

                // Convert string values to numbers for metrics
                const data = results.data.map((row: Record<string, string | number>) => ({
                    Tool: row.Tool,
                    "Execution Time (s)": parseFloat(String(row["Execution Time (s)"] || 0)),
                    "CPU Used (%)": parseFloat(String(row["CPU Used (%)"] || 0)),
                    "Memory Used (KB)": parseInt(String(row["Memory Used (KB)"] || 0), 10),
                }));

                resolve(data as MetricsData[]);
            })
            .catch((error) => {
                reject(error);
            });
    });
}

/**
 * Aggregates metrics data by tool name
 * @param data The raw metrics data
 * @returns Object with aggregated metrics by tool
 */
export function aggregateMetricsByTool(data: MetricsData[]): Record<
    string,
    {
        avgExecutionTime: number;
        avgCpuUsage: number;
        avgMemoryUsage: number;
        count: number;
    }
> {
    const result: Record<
        string,
        {
            totalExecutionTime: number;
            totalCpuUsage: number;
            totalMemoryUsage: number;
            count: number;
            avgExecutionTime: number;
            avgCpuUsage: number;
            avgMemoryUsage: number;
        }
    > = {};

    // Calculate totals
    for (const row of data) {
        const tool = row.Tool;

        if (!result[tool]) {
            result[tool] = {
                totalExecutionTime: 0,
                totalCpuUsage: 0,
                totalMemoryUsage: 0,
                count: 0,
                avgExecutionTime: 0,
                avgCpuUsage: 0,
                avgMemoryUsage: 0,
            };
        }

        result[tool].totalExecutionTime += row["Execution Time (s)"];
        result[tool].totalCpuUsage += row["CPU Used (%)"];
        result[tool].totalMemoryUsage += row["Memory Used (KB)"];
        result[tool].count += 1;
    }

    // Calculate averages
    for (const tool in result) {
        const toolData = result[tool];
        toolData.avgExecutionTime = toolData.totalExecutionTime / toolData.count;
        toolData.avgCpuUsage = toolData.totalCpuUsage / toolData.count;
        toolData.avgMemoryUsage = toolData.totalMemoryUsage / toolData.count;
    }

    return result;
}

/**
 * Get statistics for a specific metric
 * @param data The raw metrics data
 * @param metricName The name of the metric to analyze
 * @returns Object with min, max, avg values for the metric
 */
export function getMetricStatistics(
    data: MetricsData[],
    metricName: keyof MetricsData
): {
    min: number;
    max: number;
    avg: number;
} {
    if (data.length === 0) {
        return { min: 0, max: 0, avg: 0 };
    }

    const values = data.map((row) => {
        const value = row[metricName];
        return typeof value === "number" ? value : 0;
    });

    const min = Math.min(...values);
    const max = Math.max(...values);
    const sum = values.reduce((acc, val) => acc + val, 0);
    const avg = sum / values.length;

    return { min, max, avg };
}
