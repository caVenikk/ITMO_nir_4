<template>
    <div class="metric-charts">
        <h3 class="metric-charts-title">Диаграммы размаха метрик по анализаторам</h3>

        <div class="charts-container">
            <div class="chart-box">
                <VueApexCharts
                    type="boxPlot"
                    height="350"
                    :options="chartOptions.execution"
                    :series="boxplotSeries.execution"
                />
            </div>

            <div class="chart-box">
                <VueApexCharts type="boxPlot" height="350" :options="chartOptions.cpu" :series="boxplotSeries.cpu" />
            </div>

            <div class="chart-box">
                <VueApexCharts
                    type="boxPlot"
                    height="350"
                    :options="chartOptions.memory"
                    :series="boxplotSeries.memory"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import VueApexCharts from "vue3-apexcharts";
import type { StatsData, MetricKey } from "@/types/metrics";
import { CHART_COLORS } from "@/constants/chartConstants";

const props = defineProps<{
    statsData: StatsData;
}>();

const analyzerColors = CHART_COLORS;

const chartTitles: Record<MetricKey, string> = {
    execution: "Распределение времени выполнения (с)",
    cpu: "Распределение использования ЦП (%)",
    memory: "Распределение использования памяти (КБ)",
};

const chartOptions = computed(() => {
    const categories = Object.keys(props.statsData);

    const metricMinMax: Record<MetricKey, { min: number; max: number }> = {
        execution: { min: Infinity, max: -Infinity },
        cpu: { min: Infinity, max: -Infinity },
        memory: { min: Infinity, max: -Infinity },
    };

    Object.values(props.statsData).forEach((toolData) => {
        Object.entries(metricMinMax).forEach(([metric, value]) => {
            const metricKey = metric as MetricKey;
            metricMinMax[metricKey].min = Math.min(metricMinMax[metricKey].min, toolData[metricKey].min);
            metricMinMax[metricKey].max = Math.max(metricMinMax[metricKey].max, toolData[metricKey].max);
        });
    });

    Object.keys(metricMinMax).forEach((metric) => {
        const metricKey = metric as MetricKey;
        const range = metricMinMax[metricKey].max - metricMinMax[metricKey].min;
        const gap = range * 0.1;

        if (metricMinMax[metricKey].min !== Infinity) {
            metricMinMax[metricKey].min = Math.max(0, metricMinMax[metricKey].min - gap);
        } else {
            metricMinMax[metricKey].min = 0;
        }

        if (metricMinMax[metricKey].max !== -Infinity) {
            metricMinMax[metricKey].max = metricMinMax[metricKey].max + gap;
        } else {
            metricMinMax[metricKey].max = 100;
        }
    });

    const baseOptions = {
        chart: {
            type: "boxPlot",
            fontFamily: "Roboto, sans-serif",
            foreColor: "var(--v-theme-on-surface)",
            toolbar: {
                show: false,
            },
            zoom: {
                enabled: false,
            },
            animations: {
                enabled: true,
            },
        },
        colors: analyzerColors.slice(0, categories.length),
        plotOptions: {
            boxPlot: {
                colors: {
                    upper: analyzerColors[0],
                    lower: analyzerColors[0],
                },
                fillColors: {
                    upper: analyzerColors[0],
                    lower: analyzerColors[0],
                },
                distributed: true,
            },
        },
        stroke: {
            width: 2,
            colors: ["#000"],
        },
        xaxis: {
            categories,
            title: {
                text: "Анализаторы",
                style: {
                    fontSize: "14px",
                    fontWeight: "bold",
                    fontFamily: "Roboto, sans-serif",
                    color: "var(--v-theme-on-surface)",
                },
            },
            labels: {
                style: {
                    fontSize: "12px",
                    fontFamily: "Roboto, sans-serif",
                    colors: "var(--v-theme-on-surface)",
                },
            },
        },
        yaxis: {
            title: {
                style: {
                    fontSize: "14px",
                    fontWeight: "bold",
                    fontFamily: "Roboto, sans-serif",
                    color: "var(--v-theme-on-surface)",
                },
            },
            min: undefined,
            max: undefined,
            labels: {
                style: {
                    fontSize: "12px",
                    fontFamily: "Roboto, sans-serif",
                    colors: "var(--v-theme-on-surface)",
                },
                formatter: (val: number) => val.toFixed(2),
            },
        },
        tooltip: {
            shared: false,
            intersect: true,
            theme: "dark",
            custom: function ({
                seriesIndex,
                dataPointIndex,
                w,
            }: {
                seriesIndex: number;
                dataPointIndex: number;
                w: {
                    config: { series: { data: { y: number[] }[] }[]; title: { text: string } };
                    globals: { categoryLabels: string[] };
                };
            }) {
                const data = w.config.series[seriesIndex].data[dataPointIndex];
                const chartTitle = w.config.title.text;

                // Determine metric based on chart title instead of seriesIndex
                let metric: MetricKey = "execution";

                if (chartTitle.includes("ЦП")) {
                    metric = "cpu";
                } else if (chartTitle.includes("памяти")) {
                    metric = "memory";
                }

                const metricLabels = {
                    execution: "Время выполнения (с)",
                    cpu: "Использование ЦП (%)",
                    memory: "Использование памяти (КБ)",
                };

                const toolName = w.globals.categoryLabels[dataPointIndex];

                return `
          <div class="apexcharts-tooltip-box">
            <div class="apexcharts-tooltip-title" style="font-weight: bold; margin-bottom: 5px; font-family: Roboto, sans-serif;">
              ${toolName} - ${metricLabels[metric]}
            </div>
            <div style="font-family: Roboto, sans-serif;">
              <span><strong>Минимум:</strong> ${data.y[0].toFixed(2)}</span><br/>
              <span><strong>Q1:</strong> ${data.y[1].toFixed(2)}</span><br/>
              <span><strong>Медиана:</strong> ${data.y[2].toFixed(2)}</span><br/>
              <span><strong>Q3:</strong> ${data.y[3].toFixed(2)}</span><br/>
              <span><strong>Максимум:</strong> ${data.y[4].toFixed(2)}</span><br/>
              <span><strong>Среднее:</strong> ${
                  props.statsData[toolName] ? props.statsData[toolName][metric].mean.toFixed(2) : "0.00"
              }</span>
            </div>
          </div>
        `;
            },
        },
        legend: {
            labels: {
                colors: "var(--v-theme-on-surface)",
                useSeriesColors: false,
                fontFamily: "Roboto, sans-serif",
            },
        },
        title: {
            style: {
                fontSize: "16px",
                fontWeight: "bold",
                fontFamily: "Roboto, sans-serif",
                color: "var(--v-theme-on-surface)",
            },
        },
        responsive: [
            {
                breakpoint: 480,
                options: {
                    chart: {
                        height: 300,
                    },
                },
            },
        ],
        dataLabels: {
            enabled: false,
        },
        states: {
            hover: {
                filter: { type: "none" },
            },
            active: {
                filter: { type: "none" },
            },
        },
    };

    return {
        execution: {
            ...baseOptions,
            title: {
                text: chartTitles.execution,
                align: "center",
                style: {
                    fontSize: "16px",
                    fontWeight: "bold",
                    fontFamily: "Roboto, sans-serif",
                },
            },
            yaxis: {
                ...baseOptions.yaxis,
                min: metricMinMax.execution.min,
                max: metricMinMax.execution.max,
                title: {
                    text: "Секунды",
                    ...baseOptions.yaxis.title,
                },
            },
        },
        cpu: {
            ...baseOptions,
            title: {
                text: chartTitles.cpu,
                align: "center",
                style: {
                    fontSize: "16px",
                    fontWeight: "bold",
                    fontFamily: "Roboto, sans-serif",
                },
            },
            yaxis: {
                ...baseOptions.yaxis,
                min: metricMinMax.cpu.min,
                max: metricMinMax.cpu.max,
                title: {
                    text: "Проценты (%)",
                    ...baseOptions.yaxis.title,
                },
            },
        },
        memory: {
            ...baseOptions,
            title: {
                text: chartTitles.memory,
                align: "center",
                style: {
                    fontSize: "16px",
                    fontWeight: "bold",
                    fontFamily: "Roboto, sans-serif",
                },
            },
            yaxis: {
                ...baseOptions.yaxis,
                min: metricMinMax.memory.min,
                max: metricMinMax.memory.max,
                title: {
                    text: "Килобайты (КБ)",
                    ...baseOptions.yaxis.title,
                },
                forceNiceScale: true,
            },
        },
    };
});

const boxplotSeries = computed(() => {
    if (Object.keys(props.statsData).length === 0) {
        return {
            execution: [],
            cpu: [],
            memory: [],
        };
    }

    const getSeriesForMetric = (metricKey: MetricKey) => {
        return [
            {
                name: "Analyzers",
                data: Object.entries(props.statsData).map(([toolName, toolData], index) => {
                    return {
                        x: toolName,
                        y: [
                            toolData[metricKey].min,
                            toolData[metricKey].q1,
                            toolData[metricKey].median,
                            toolData[metricKey].q3,
                            toolData[metricKey].max,
                        ],
                        fillColor: analyzerColors[index % analyzerColors.length],
                        color: analyzerColors[index % analyzerColors.length],
                    };
                }),
            },
        ];
    };

    return {
        execution: getSeriesForMetric("execution"),
        cpu: getSeriesForMetric("cpu"),
        memory: getSeriesForMetric("memory"),
    };
});
</script>

<style scoped lang="scss">
.metric-charts {
    width: 100%;
    margin-bottom: 3rem;

    &-title {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .charts-container {
        display: flex;
        flex-direction: column;
        gap: 3rem;
        width: 100%;

        .chart-box {
            border-radius: 8px;
            padding: 1.5rem;
            background-color: rgba(var(--v-theme-surface-variant), 0.2);
            border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);

            h4 {
                text-align: center;
                margin-bottom: 1rem;
                font-size: 1.2rem;
                font-weight: 500;
            }
        }
    }
}

@media (max-width: 768px) {
    .metric-charts .charts-container .chart-box {
        padding: 1rem;
        overflow-x: auto;
    }
}

:deep(.apexcharts-tooltip-box) {
    padding: 8px 12px;
    font-size: 0.85rem;
    line-height: 1.4;
}

:deep(.apexcharts-toolbar) {
    z-index: 5;
    .apexcharts-menu {
        background-color: var(--v-theme-surface);
        border-color: var(--v-theme-outline);
        border-radius: 4px;
        font-family: "Roboto, sans-serif";

        .apexcharts-menu-item {
            font-family: "Roboto, sans-serif";
        }
    }
}

:deep(.apexcharts-boxPlot-series) {
    stroke-width: 2px;
    .apexcharts-boxPlot-whisker {
        stroke-width: 2px;
    }
    .apexcharts-boxPlot-box {
        stroke-width: 1.5px;
    }
}
</style>
