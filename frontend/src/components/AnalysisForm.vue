<template>
    <v-card class="mx-auto" max-width="700" elevation="5">
        <!-- <span class="text-h5 text-center card-title">Метрики анализаторов Python-кода</span> -->

        <span class="text-center card-title">Измерить производительность статического анализатора Python</span>

        <span class="text-center card-subtitle"
            >Выбранный анализатор будет сравниваться с ruff, mypy и flake8. Можно также выбрать один из них</span
        >

        <v-divider />

        <v-card-text>
            <v-form ref="form" @submit.prevent="submitForm">
                <v-autocomplete
                    v-model="formData.analyzerName"
                    v-model:search="searchQuery"
                    :items="packages"
                    :loading="isSearching"
                    item-title="name"
                    item-value="name"
                    label="Пакет Python"
                    placeholder="Начните вводить для поиска пакетов"
                    return-object
                    :rules="[(v) => !!v?.name || 'Пакет обязателен к выбору']"
                    hide-no-data
                    hide-selected
                    prepend-inner-icon="mdi-magnify"
                    required
                />

                <v-text-field
                    v-model="formData.repositoryUrl"
                    label="URL репозитория GitHub"
                    placeholder="https://github.com/username/repository"
                    :rules="[
                        (v) => !!v || 'URL репозитория обязателен',
                        (v) => isValidGithubUrl(v) || 'Неверный URL GitHub репозитория',
                    ]"
                    prepend-inner-icon="mdi-github"
                    required
                />

                <v-text-field
                    v-model="formData.commandTemplate"
                    label="Шаблон команды (необязательно)"
                    placeholder="например, ruff check src"
                    hint="Команда для запуска анализатора. По умолчанию '{tool} {path}'. Пример: 'ruff .'"
                    persistent-hint
                    prepend-inner-icon="mdi-console"
                />
            </v-form>
        </v-card-text>

        <v-card-actions class="justify-center pb-4">
            <v-btn
                color="primary"
                size="large"
                :disabled="!canSubmit || isLoading"
                :loading="isLoading && !isTaskRunning"
                @click="submitForm"
            >
                <v-icon start> mdi-play-circle </v-icon>
                Запустить анализ
            </v-btn>
        </v-card-actions>
    </v-card>

    <!-- Диалог статуса выполнения -->
    <analysis-status-dialog
        v-model:model-value="showStatusDialog"
        :status="taskStatus"
        :task-id="currentTask?.task_id"
        :is-downloading="isDownloading"
        :download-error="downloadError"
        @close="closeDialog"
        @cancel="cancelAnalysis"
        @retry="retryDownload"
    />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useAnalyzerStore } from "@/store/analyzerStore";
import { isValidGithubUrl, debounce } from "@/utils/validators";
import { type PyPIPackage } from "@/types";
import { parseCSVBlob, type MetricsData } from "@/services/csvService";
import AnalysisStatusDialog from "./AnalysisStatusDialog.vue";

const emit = defineEmits<{
    (e: "analysis-complete", data: { metricsData: MetricsData[]; taskId: string }): void;
    (e: "analysis-error", error: string): void;
}>();

// Store
const store = useAnalyzerStore();

// Refs
const form = ref<any>(null);
const searchQuery = ref("");
const showStatusDialog = ref(false);
const isDownloading = ref(false);
const downloadError = ref<string | null>(null);

// Form data
const formData = ref({
    analyzerName: null as PyPIPackage | null,
    repositoryUrl: "",
    commandTemplate: "",
});

// Computed properties
const canSubmit = computed(() => {
    return !!(
        formData.value.analyzerName?.name &&
        formData.value.repositoryUrl &&
        isValidGithubUrl(formData.value.repositoryUrl)
    );
});

const packages = computed(() => store.packages);
const isSearching = computed(() => store.isSearching);
const currentTask = computed(() => store.currentTask);
const taskStatus = computed(() => store.taskStatus);
const isTaskRunning = computed(() => store.isTaskRunning);
const isLoading = computed(() => store.isLoading);

// Watch for search query changes and debounce API calls
watch(
    searchQuery,
    debounce((query: string) => {
        if (query && query.length > 1) {
            store.searchPackages(query);
        }
    }, 300),
);

// Watch for task status changes
watch(taskStatus, async (newStatus, oldStatus) => {
    // Если задача только что завершилась успешно
    if (newStatus === "completed" && oldStatus !== "completed" && currentTask.value?.task_id) {
        await downloadMetrics(currentTask.value.task_id);
    }

    // Если задача завершилась с ошибкой
    if (newStatus === "failed" && currentTask.value?.error_message) {
        emit("analysis-error", currentTask.value.error_message);
        // Закрываем диалог после короткой задержки
        setTimeout(() => {
            showStatusDialog.value = false;
        }, 1500);
    }

    // Если задача отменена
    if (newStatus === "cancelled") {
        // Оставляем диалог открытым с сообщением об отмене
        // Пользователь закроет его сам
    }
});

// Methods
async function submitForm() {
    if (!canSubmit.value) return;

    const taskData = {
        analyzer_name: formData.value.analyzerName!.name,
        repository_url: formData.value.repositoryUrl,
    } as { analyzer_name: string; repository_url: string; command_template?: string };

    // Only add commandTemplate if it's not empty
    if (formData.value.commandTemplate) {
        taskData.command_template = formData.value.commandTemplate;
    }

    // Reset state
    downloadError.value = null;

    // Show status dialog
    showStatusDialog.value = true;

    // Start analysis
    await store.startAnalysis(taskData);
}

async function downloadMetrics(taskId: string) {
    downloadError.value = null;
    isDownloading.value = true;

    try {
        const blob = await store.downloadMetrics(taskId);

        if (blob) {
            try {
                const data = await parseCSVBlob(blob);

                // Emit event with results
                emit("analysis-complete", {
                    metricsData: data,
                    taskId: taskId,
                });

                // Close dialog after short delay
                setTimeout(() => {
                    showStatusDialog.value = false;
                }, 500);
            } catch (error) {
                console.error("Failed to parse metrics data:", error);
                downloadError.value = "Ошибка при обработке данных метрик";
            }
        } else {
            downloadError.value = "Не удалось получить данные метрик";
        }
    } catch (error) {
        console.error("Failed to download metrics:", error);
        downloadError.value = error instanceof Error ? error.message : "Ошибка при загрузке метрик";
    } finally {
        isDownloading.value = false;
    }
}

async function retryDownload() {
    if (currentTask.value?.task_id) {
        await downloadMetrics(currentTask.value.task_id);
    }
}

function cancelAnalysis() {
    store.cancelCurrentTask();
}

function closeDialog() {
    showStatusDialog.value = false;
}

// При монтировании компонента сбрасываем состояние хранилища
onMounted(() => {
    store.resetState();
});
</script>

<style lang="scss" scoped>
.v-form {
    padding: 16px;
}
</style>
