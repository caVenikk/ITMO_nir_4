export interface PyPIPackage {
    name: string;
    last_serial?: number;
}

export interface PyPISearchResponse {
    packages: PyPIPackage[];
}

export interface TaskCreate {
    analyzer_name: string;
    repository_url: string;
    command_template?: string;
}

export interface TaskResponse {
    task_id: string;
    analyzer_name: string;
    repository_url: string;
    command_template: string;
    status: string;
    created_at: string;
    completed_at?: string;
    error_message?: string;
}

export interface TaskStatusResponse {
    task_id: string;
    status: string;
}

export interface CancelTaskResponse {
    task_id: string;
    status: string;
    message: string;
}

export type TaskStatus =
    | "pending"
    | "running"
    | "completed"
    | "failed"
    | "cancelled"
    | "data_already_retrieved";
