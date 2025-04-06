<template>
  <v-container class="fill-height">
    <v-responsive class="align-center py-0">
      <!-- Форма анализа -->
      <AnalysisForm
        @analysis-complete="handleAnalysisComplete"
        @analysis-error="handleAnalysisError"
      />

      <!-- Результаты анализа (показываются только когда есть данные) -->
      <AnalysisResults
        v-if="showResults"
        :metrics-data="metricsData"
        :task-id="taskId"
        :error-message="errorMessage"
        @reset="resetResults"
      />
    </v-responsive>
  </v-container>
</template>

<script lang="ts" setup>
    import { ref, computed } from "vue";
    import AnalysisForm from "@/components/AnalysisForm.vue";
    import AnalysisResults from "@/components/AnalysisResults.vue";
    import type { MetricsData } from "@/services/csvService";

    // Состояние
    const metricsData = ref<MetricsData[]>([]);
    const taskId = ref<string | undefined>(undefined);
    const errorMessage = ref<string | null>(null);

    // Вычисляемые свойства
    const showResults = computed(() => {
        return metricsData.value.length > 0 || errorMessage.value !== null;
    });

    // Методы
    function handleAnalysisComplete(data: { metricsData: MetricsData[]; taskId: string }) {
        metricsData.value = data.metricsData;
        taskId.value = data.taskId;
        errorMessage.value = null;
    }

    function handleAnalysisError(error: string) {
        errorMessage.value = error;
        metricsData.value = [];
        taskId.value = undefined;
    }

    function resetResults() {
        metricsData.value = [];
        taskId.value = undefined;
        errorMessage.value = null;
    }
</script>

<style scoped>
    .v-responsive {
        max-width: 1100px;
        margin: 0 auto;
        width: 100%;
        padding: 0 16px;
    }

    @media (max-width: 600px) {
        .v-responsive {
            padding: 0 8px;
        }

        :deep(.v-container) {
            padding: 8px !important;
        }
    }
</style>
