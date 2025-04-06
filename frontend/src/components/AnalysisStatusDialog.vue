<template>
  <v-dialog
    :model-value="modelValue"
    persistent
    max-width="500"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title class="text-h5">
        Статус анализа
      </v-card-title>

      <v-card-text>
        <!-- Выполнение анализа -->
        <div
          v-if="isRunning"
          class="text-center py-4"
        >
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
          />
          <p class="mt-4">
            Анализ кода... Пожалуйста, подождите.
          </p>
          <p class="text-caption">
            ID задачи: {{ taskId }}
          </p>
        </div>

        <!-- Загрузка метрик -->
        <div
          v-else-if="isDownloading"
          class="text-center py-4"
        >
          <v-progress-circular
            indeterminate
            color="info"
            size="64"
          />
          <p class="mt-4">
            Загрузка данных метрик...
          </p>
        </div>

        <!-- Ошибка при загрузке метрик -->
        <div
          v-else-if="downloadError"
          class="text-center py-4"
        >
          <v-icon
            color="error"
            size="64"
          >
            mdi-alert-circle
          </v-icon>
          <p class="mt-4">
            Ошибка при загрузке метрик
          </p>
          <p class="text-caption text-error">
            {{ downloadError }}
          </p>
        </div>

        <!-- Анализ отменен -->
        <div
          v-else-if="status === 'cancelled'"
          class="text-center py-4"
        >
          <v-icon
            color="warning"
            size="64"
          >
            mdi-cancel
          </v-icon>
          <p class="mt-4">
            Анализ был отменен
          </p>
        </div>
      </v-card-text>

      <v-card-actions class="justify-center pb-4">
        <v-btn
          v-if="canCancel"
          color="error"
          @click="$emit('cancel')"
        >
          Отменить анализ
        </v-btn>

        <v-btn
          v-if="downloadError"
          color="primary"
          @click="$emit('retry')"
        >
          Повторить загрузку
        </v-btn>

        <v-btn
          color="secondary"
          :disabled="!canClose"
          @click="$emit('close')"
        >
          Закрыть
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
    import { computed } from "vue";

    const props = defineProps<{
        modelValue: boolean;
        status: string | null;
        taskId?: string;
        isDownloading: boolean;
        downloadError: string | null;
    }>();

    defineEmits<{
        (e: "update:modelValue", value: boolean): void;
        (e: "close"): void;
        (e: "cancel"): void;
        (e: "retry"): void;
    }>();

    // Вычисляемые свойства
    const isRunning = computed(() => {
        return props.status === "pending" || props.status === "running";
    });

    const canCancel = computed(() => {
        return isRunning.value;
    });

    const canClose = computed(() => {
        return !isRunning.value && !props.isDownloading;
    });
</script>
