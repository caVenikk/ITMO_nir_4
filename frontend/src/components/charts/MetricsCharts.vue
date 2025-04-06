<template>
  <div class="metrics-charts">
    <v-card
      elevation="1"
      class="mb-4 px-2 py-2"
    >
      <span class="text-center main-title card-title">Графики метрик производительности</span>
      <v-card-text>
        <MetricBarCharts :stats-data="statsData" />
        <v-divider class="my-4 my-sm-6" />
        <MetricBoxPlots :stats-data="statsData" />
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
    import { computed } from "vue";
    import { generateMetricsStats } from "@/utils/metricsCalculator";
    import { type MetricsData } from "@/services/csvService";
    import { type StatsData } from "@/types/metrics";
    import MetricBarCharts from "./MetricBarCharts.vue";
    import MetricBoxPlots from "./MetricBoxPlots.vue";

    const props = defineProps<{
        metricsData: MetricsData[];
    }>();

    // Вычисляем статистику для метрик
    const statsData = computed((): StatsData => {
        if (!props.metricsData.length) return {} as StatsData;
        return generateMetricsStats(props.metricsData);
    });
</script>

<style scoped lang="scss">
    .metrics-charts {
        width: 100%;
        margin-top: 2rem;

        .main-title {
            font-size: 1.5rem;
            padding: 0 16px;
            word-break: break-word;
            hyphens: auto;
        }
    }

    @media (max-width: 600px) {
        .metrics-charts {
            margin-top: 1rem;

            .main-title {
                font-size: 1.2rem;
                line-height: 1.4;
            }

            :deep(.v-card-text) {
                padding: 8px;
            }
        }
    }
</style>
