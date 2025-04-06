import { type MetricStats, type StatsData } from "@/types/metrics";
import { type MetricsData } from "@/services/csvService";

/**
 * Рассчитывает статистические данные из массива чисел
 * @param data Массив числовых значений
 * @returns Объект со статистическими показателями
 */
export function calculateStats(data: number[]): MetricStats {
    // Сортируем массив для вычисления квантилей
    const sorted = [...data].sort((a, b) => a - b);
    const len = sorted.length;

    // Если данных нет, возвращаем нули
    if (len === 0) {
        return {
            min: 0,
            q1: 0,
            median: 0,
            q3: 0,
            max: 0,
            mean: 0,
            outliers: [],
        };
    }

    // Вычисляем квартили
    const q1Index = Math.floor(len * 0.25);
    const medianIndex = Math.floor(len * 0.5);
    const q3Index = Math.floor(len * 0.75);

    // Вычисляем среднее значение
    const mean = sorted.reduce((sum, val) => sum + val, 0) / len;

    return {
        min: sorted[0],
        q1: sorted[q1Index],
        median: sorted[medianIndex],
        q3: sorted[q3Index],
        max: sorted[len - 1],
        mean: mean,
        outliers: sorted,
    };
}

/**
 * Генерирует статистические данные из сырых метрик
 * @param metrics Сырые данные метрик
 * @returns Объект со статистикой по каждому инструменту
 */
export function generateMetricsStats(metrics: MetricsData[]): StatsData {
    if (!metrics.length) return {} as StatsData;

    const result: StatsData = {};
    const tools = new Set(metrics.map((m) => m.Tool));

    tools.forEach((tool) => {
        const toolMetrics = metrics.filter((m) => m.Tool === tool);

        result[tool] = {
            execution: calculateStats(toolMetrics.map((m) => m["Execution Time (s)"])),
            cpu: calculateStats(toolMetrics.map((m) => m["CPU Used (%)"])),
            memory: calculateStats(toolMetrics.map((m) => m["Memory Used (KB)"])),
        };
    });

    return result;
}
