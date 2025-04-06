import VueApexCharts from "vue3-apexcharts";
import type { App } from "vue";

export function registerApexCharts(app: App): void {
    app.use(VueApexCharts);
}
