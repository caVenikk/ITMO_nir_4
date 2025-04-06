<template>
  <div
    v-if="metricsData.length > 0 || errorMessage"
    class="analysis-results mt-8"
  >
    <v-card elevation="3">
      <v-card-title class="text-h5">
        <v-icon
          v-if="!errorMessage"
          color="success"
          class="mr-2"
        >
          mdi-check-circle
        </v-icon>
        <v-icon
          v-else
          color="error"
          class="mr-2"
        >
          mdi-alert-circle
        </v-icon>
        {{ errorMessage ? "Ошибка анализа" : "Результаты анализа" }}
      </v-card-title>

      <v-divider />

      <!-- Отображение ошибки, если она есть -->
      <v-card-text
        v-if="errorMessage"
        class="error-container"
      >
        <v-alert
          type="error"
          class="mb-4"
        >
          {{ errorMessage }}
        </v-alert>
      </v-card-text>

      <!-- Отображение результатов анализа, если нет ошибки -->
      <v-card-text v-else>
        <v-tabs v-model="activeTab">
          <v-tab value="summary">
            Сводка
          </v-tab>
          <v-tab value="graphs">
            Графики
          </v-tab>
          <v-tab value="details">
            Детальные данные
          </v-tab>
        </v-tabs>

        <v-window
          v-model="activeTab"
          class="mt-4"
        >
          <v-window-item value="summary">
            <v-alert
              type="success"
              variant="tonal"
              class="mb-4"
            >
              Анализ успешно завершен с {{ metricsData.length }} точками данных.
            </v-alert>

            <v-table density="compact">
              <thead>
                <tr>
                  <th>Инструмент</th>
                  <th>Ср. время выполнения (с)</th>
                  <th>Ср. загрузка ЦП (%)</th>
                  <th>Ср. использование памяти (КБ)</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(data, tool) in aggregatedData"
                  :key="tool"
                >
                  <td>
                    <strong>{{ tool }}</strong>
                  </td>
                  <td>{{ data.avgExecutionTime.toFixed(2) }}с</td>
                  <td>{{ data.avgCpuUsage.toFixed(2) }}%</td>
                  <td>{{ Math.round(data.avgMemoryUsage).toLocaleString() }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-window-item>

          <v-window-item value="graphs">
            <MetricsCharts :metrics-data="metricsData" />
          </v-window-item>

          <v-window-item value="details">
            <v-alert
              type="info"
              variant="tonal"
              class="mb-4"
            >
              Исходные данные метрик для всех инструментов и итераций
            </v-alert>

            <v-data-table
              :items="metricsData"
              :headers="tableHeaders"
              density="compact"
              class="elevation-1"
            />
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          v-if="metricsData.length > 0"
          color="primary"
          prepend-icon="mdi-download"
          @click="downloadCSV"
        >
          Скачать CSV
        </v-btn>
        <v-btn
          color="secondary"
          @click="resetResults"
        >
          Новый анализ
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import Papa from "papaparse";
import { aggregateMetricsByTool, type MetricsData } from "@/services/csvService";
import MetricsCharts from "@/components/charts/MetricsCharts.vue";

const props = defineProps<{
    metricsData: MetricsData[];
    taskId?: string;
    errorMessage?: string | null;
}>();

const emit = defineEmits<{
    (e: "reset"): void;
}>();

// Локальное состояние
const activeTab = ref("summary");

// Заголовки таблицы
const tableHeaders = [
    { title: "Инструмент", key: "Tool" },
    { title: "Время выполнения (с)", key: "Execution Time (s)" },
    { title: "Использование ЦП (%)", key: "CPU Used (%)" },
    { title: "Использование памяти (КБ)", key: "Memory Used (KB)" },
];

// Вычисляемые свойства
const aggregatedData = computed(() => {
    if (props.metricsData.length === 0) {
        return {};
    }
    return aggregateMetricsByTool(props.metricsData);
});

// Методы
function downloadCSV() {
    if (!props.taskId || props.metricsData.length === 0) return;

    const csvData = props.metricsData;
    const csv = Papa.unparse(csvData);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `metrics_${props.taskId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}

function resetResults() {
    emit("reset");
}
</script>

<style lang="scss" scoped>
.analysis-results {
    margin-bottom: 2rem;
}

.error-container {
    min-height: 100px;
    display: flex;
    align-items: center;
}
</style>
