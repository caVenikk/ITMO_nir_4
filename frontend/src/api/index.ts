import ky from "ky";
import type {
    PyPISearchResponse,
    TaskCreate,
    TaskResponse,
    TaskStatusResponse,
    CancelTaskResponse,
} from "@/types";

// Function to get API base URL from environment variables
function getApiBaseUrl(): string {
    // Try to access environment variables in different ways
    return (
        process.env.VITE_API_URL ||
        (typeof import.meta !== "undefined" ? import.meta.env.VITE_API_URL : null) ||
        "http://localhost:8000/api/v1"
    );
}

// Create a custom ky instance with base URL and default options
const api = ky.create({
    prefixUrl: getApiBaseUrl(),
    timeout: 30000,
    retry: 0,
    hooks: {
        beforeError: [
            async (error) => {
                const { response } = error;
                if (response && response.body) {
                    try {
                        const body = await response.json();
                        if (typeof body === "object" && body !== null && "detail" in body) {
                            error.message =
                                (body as { detail?: string; message?: string }).detail ||
                                (body as { detail?: string; message?: string }).message ||
                                "Unknown error";
                        } else {
                            error.message = "An error occurred";
                        }
                    } catch {
                        error.message = "An error occurred";
                    }
                }
                return error;
            },
        ],
    },
});

// Rest of the API functions remain unchanged
export const searchPackages = async (query = ""): Promise<PyPISearchResponse> => {
    const params = new URLSearchParams();
    if (query) {
        params.set("query", query);
    }

    return await api.get(`pypi/search?${params}`).json<PyPISearchResponse>();
};

export const startAnalysis = async (taskData: TaskCreate): Promise<TaskResponse> => {
    return await api.post("analyze", { json: taskData }).json<TaskResponse>();
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatusResponse> => {
    return await api.get(`tasks/${taskId}/status`).json<TaskStatusResponse>();
};

export const cancelTask = async (taskId: string): Promise<CancelTaskResponse> => {
    return await api.post(`tasks/${taskId}/cancel`).json<CancelTaskResponse>();
};

export const downloadMetrics = async (taskId: string): Promise<Blob> => {
    try {
        const blob = await api
            .get(`tasks/${taskId}/metrics`, {
                timeout: 60000,
                headers: {
                    Accept: "text/csv",
                },
            })
            .blob();
        return blob;
    } catch (error) {
        console.error("Error downloading metrics:", error);
        throw error;
    }
};
