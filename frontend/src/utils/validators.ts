/**
 * Validates a GitHub repository URL.
 * Valid formats:
 * - https://github.com/username/repository
 * - https://github.com/username/repository.git
 * - git@github.com:username/repository.git
 */
export function isValidGithubUrl(url: string): boolean {
    if (!url) return false;
    // HTTP/HTTPS format
    const httpsRegex = /^https?:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+(\/.+)*(\.git)?$/;
    // SSH format
    const sshRegex = /^git@github\.com:[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+(\.git)?$/;
    return httpsRegex.test(url) || sshRegex.test(url);
}

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked.
 */
export function debounce<T extends unknown[], R>(func: (...args: T) => R, wait: number): (...args: T) => void {
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    return function (...args: T): void {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func(...args);
        }, wait);
    };
}
