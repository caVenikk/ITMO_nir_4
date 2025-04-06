import { defineStore } from "pinia";
import { ref, computed } from "vue";
import * as api from "@/api";
import type { PyPIPackage, TaskCreate, TaskResponse, TaskStatus } from "@/types";

export const useAnalyzerStore = defineStore("analyzer", () => {
    // State
    const packages = ref<PyPIPackage[]>([]);
    const searchQuery = ref("");
    const isSearching = ref(false);
    const currentTask = ref<TaskResponse | null>(null);
    const taskStatus = ref<TaskStatus | null>(null);
    const isPolling = ref(false);
    const pollingInterval = ref<number | null>(null);
    const errorMessage = ref<string | null>(null);
    const isLoading = ref(false);

    // Computed properties
    const isTaskRunning = computed(() => {
        return taskStatus.value === "pending" || taskStatus.value === "running";
    });

    const canStartAnalysis = computed(() => {
        return !isLoading.value && !isTaskRunning.value;
    });

    // Actions
    async function searchPackages(query: string) {
        searchQuery.value = query;
        if (!query.trim()) {
            packages.value = [];
            return;
        }

        isSearching.value = true;
        errorMessage.value = null;

        try {
            const response = await api.searchPackages(query);
            packages.value = response.packages;
        } catch (error) {
            console.error("Failed to search packages:", error);
            errorMessage.value =
                error instanceof Error ? error.message : "Failed to search packages";
            packages.value = [];
        } finally {
            isSearching.value = false;
        }
    }

    async function startAnalysis(taskData: TaskCreate) {
        isLoading.value = true;
        errorMessage.value = null;

        try {
            const response = await api.startAnalysis(taskData);
            currentTask.value = response;
            taskStatus.value = response.status as TaskStatus;

            // Start polling for task status
            startPolling(response.task_id);
        } catch (error) {
            console.error("Failed to start analysis:", error);
            errorMessage.value =
                error instanceof Error ? error.message : "Failed to start analysis";
        } finally {
            isLoading.value = false;
        }
    }

    async function checkTaskStatus(taskId: string) {
        if (!taskId) return;

        try {
            const response = await api.getTaskStatus(taskId);
            taskStatus.value = response.status as TaskStatus;

            if (
                taskStatus.value === "completed" ||
                taskStatus.value === "failed" ||
                taskStatus.value === "cancelled" ||
                taskStatus.value === "data_already_retrieved"
            ) {
                stopPolling();
            }
        } catch (error) {
            console.error("Failed to check task status:", error);
            errorMessage.value =
                error instanceof Error ? error.message : "Failed to check task status";
            stopPolling();
        }
    }

    function startPolling(taskId: string) {
        if (isPolling.value) return;

        isPolling.value = true;
        pollingInterval.value = window.setInterval(() => {
            checkTaskStatus(taskId);
        }, 3000);
    }

    function stopPolling() {
        if (pollingInterval.value) {
            clearInterval(pollingInterval.value);
            pollingInterval.value = null;
        }
        isPolling.value = false;
    }

    async function downloadMetrics(taskId: string): Promise<Blob | null> {
        isLoading.value = true;
        errorMessage.value = null;

        try {
            const blob = await api.downloadMetrics(taskId);
            return blob;
        } catch (error) {
            console.error("Failed to download metrics:", error);
            errorMessage.value =
                error instanceof Error ? error.message : "Failed to download metrics";
            return null;
        } finally {
            isLoading.value = false;
        }
    }

    async function cancelCurrentTask() {
        if (!currentTask.value?.task_id) return;

        isLoading.value = true;
        errorMessage.value = null;

        try {
            await api.cancelTask(currentTask.value.task_id);
            taskStatus.value = "cancelled";
            stopPolling();
        } catch (error) {
            console.error("Failed to cancel task:", error);
            errorMessage.value = error instanceof Error ? error.message : "Failed to cancel task";
        } finally {
            isLoading.value = false;
        }
    }

    function resetState() {
        stopPolling();
        currentTask.value = null;
        taskStatus.value = null;
        errorMessage.value = null;
    }

    return {
        // State
        packages,
        searchQuery,
        isSearching,
        currentTask,
        taskStatus,
        isPolling,
        errorMessage,
        isLoading,

        // Computed
        isTaskRunning,
        canStartAnalysis,

        // Actions
        searchPackages,
        startAnalysis,
        checkTaskStatus,
        downloadMetrics,
        cancelCurrentTask,
        resetState,
    };
});
