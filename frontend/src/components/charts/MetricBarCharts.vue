<template>
  <div class="metric-charts">
    <h3 class="metric-charts-title">
      Средние значения метрик по анализаторам
    </h3>

    <div class="charts-container">
      <!-- Диаграмма времени выполнения -->
      <div class="chart-box">
        <VueApexCharts
          type="bar"
          height="350"
          :options="chartOptions.execution"
          :series="chartSeries.execution"
        />
      </div>

      <!-- Диаграмма использования CPU -->
      <div class="chart-box">
        <VueApexCharts
          type="bar"
          height="350"
          :options="chartOptions.cpu"
          :series="chartSeries.cpu"
        />
      </div>

      <!-- Диаграмма использования памяти -->
      <div class="chart-box">
        <VueApexCharts
          type="bar"
          height="350"
          :options="chartOptions.memory"
          :series="chartSeries.memory"
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

// Цвета для разных анализаторов (цветовая палитра)
const analyzerColors = CHART_COLORS;

// Названия графиков
const chartTitles: Record<MetricKey, string> = {
    execution: "Среднее время выполнения (с)",
    cpu: "Среднее использование ЦП (%)",
    memory: "Среднее использование памяти (КБ)",
};

// Конфигурация для графиков
const chartOptions = computed(() => {
    // Получаем названия инструментов для категорий на оси X
    const categories = Object.keys(props.statsData);

    const baseOptions = {
        chart: {
            type: "bar",
            fontFamily: "Roboto, sans-serif",
            foreColor: "var(--v-theme-on-surface)",
            toolbar: {
                show: false, // Полностью отключаем панель инструментов
            },
        },
        colors: analyzerColors.slice(0, categories.length), // Используем разные цвета для каждого анализатора
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: "60%",
                borderRadius: 4,
                distributed: true, // Важно: включаем режим распределенных цветов для столбцов
            },
        },
        dataLabels: {
            enabled: true,
            formatter: function (val: number) {
                return val.toFixed(2);
            },
            style: {
                fontSize: "13px",
                fontFamily: "Roboto, sans-serif",
                colors: ["var(--v-theme-on-surface)"],
            },
        },
        xaxis: {
            categories,
            title: {
                text: "Анализаторы",
                style: {
                    fontSize: "14px",
                    fontWeight: "bold",
                    fontFamily: "Roboto, sans-serif",
                },
            },
            labels: {
                style: {
                    fontSize: "13px",
                    fontFamily: "Roboto, sans-serif",
                },
            },
        },
        yaxis: {
            title: {
                style: {
                    fontSize: "14px",
                    fontWeight: "bold",
                    fontFamily: "Roboto, sans-serif",
                },
            },
            min: 0,
            labels: {
                style: {
                    fontSize: "13px",
                    fontFamily: "Roboto, sans-serif",
                },
                formatter: (val: number) => val.toFixed(2),
            },
        },
        tooltip: {
            theme: "dark",
            y: {
                formatter: (val: number) => val.toFixed(2),
            },
        },
        legend: {
            show: false, // Отключаем легенду, так как она не нужна при distributed: true
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
                title: {
                    text: "Килобайты (КБ)",
                    ...baseOptions.yaxis.title,
                },
            },
        },
    };
});

// Данные серий для графиков - заменяем на серии без name, так как используем distributed: true
const chartSeries = computed(() => {
    // Если данных нет - возвращаем пустые серии
    if (Object.keys(props.statsData).length === 0) {
        return {
            execution: [{ data: [] }],
            cpu: [{ data: [] }],
            memory: [{ data: [] }],
        };
    }

    return {
        execution: [
            {
                data: Object.values(props.statsData).map((tool) => tool.execution.mean),
            },
        ],
        cpu: [
            {
                data: Object.values(props.statsData).map((tool) => tool.cpu.mean),
            },
        ],
        memory: [
            {
                data: Object.values(props.statsData).map((tool) => tool.memory.mean),
            },
        ],
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
        }
    }
}

@media (max-width: 768px) {
    .metric-charts .charts-container .chart-box {
        padding: 1rem;
        overflow-x: auto;
    }
}

:deep(.apexcharts-toolbar) {
    z-index: 5;
}
</style>
