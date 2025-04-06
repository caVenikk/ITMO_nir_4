/**
 * plugins/index.ts
 *
 * Automatically included in `./src/main.ts`
 */

// Plugins
import vuetify from "./vuetify";
import router from "../router";
import pinia from "./pinia";
import { registerApexCharts } from "./apexcharts";

// Types
import type { App } from "vue";

export function registerPlugins(app: App) {
    app.use(vuetify).use(router).use(pinia);

    // Регистрируем ApexCharts
    registerApexCharts(app);
}
