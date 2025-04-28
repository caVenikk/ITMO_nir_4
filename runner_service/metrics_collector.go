package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Определение инструмента статического анализа
type Tool struct {
	Name      string
	Command   []string
	Weight    int // Относительная "тяжесть" инструмента (используется только для логирования)
	TargetArg int // Индекс аргумента, в который нужно подставить путь к целевой директории
}

// Результат запуска инструмента
type ToolResult struct {
	Name       string
	ExecTime   float64
	CPUPercent float64
	MemoryKB   int64
	Timestamp  string
	Error      error
}

// Определение стандартных инструментов - все с одинаковым весом
var standardTools = []Tool{
	{Name: "flake8", Command: []string{"flake8"}, Weight: 1, TargetArg: 1},
	{Name: "ruff", Command: []string{"ruff", "check"}, Weight: 1, TargetArg: 2},
	{Name: "mypy", Command: []string{"mypy"}, Weight: 1, TargetArg: 1},
}

// Регулярные выражения для извлечения метрик
var (
	timeRegex   = regexp.MustCompile(`Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([0-9:.]+)`)
	cpuRegex    = regexp.MustCompile(`Percent of CPU this job got: ([0-9.]+)%`)
	memoryRegex = regexp.MustCompile(`Maximum resident set size \(kbytes\): ([0-9]+)`)
)

// Запуск инструмента с использованием пользовательского шаблона команды
func runToolWithTemplate(tool Tool, targetDir string, commandTemplate string) ToolResult {
	// Получаем команду анализатора как строку
	analyzerCmd := strings.Join(tool.Command, " ")
	
	// Заменяем плейсхолдеры в шаблоне
	cmd := strings.Replace(commandTemplate, "{analyzer_cmd}", analyzerCmd, -1)
	cmd = strings.Replace(cmd, "{path}", targetDir, -1)
	
	// Разбиваем команду на аргументы
	cmdParts := strings.Fields(cmd)
	
	// Если команда пуста, используем стандартный подход
	if len(cmdParts) == 0 {
		return runTool(tool, targetDir)
	}
	
	// Подготавливаем команду time
	timeCmd := exec.Command("/usr/bin/time", append([]string{"-v"}, cmdParts...)...)
	
	// Перенаправляем вывод - игнорируем ошибку выполнения
	output, _ := timeCmd.CombinedOutput()
	
	// Извлекаем метрики из вывода time
	timeStr := extractRegex(timeRegex, string(output), "0")
	cpuStr := extractRegex(cpuRegex, string(output), "0")
	memoryStr := extractRegex(memoryRegex, string(output), "0")
	
	// Преобразуем строки в числа
	execTime := parseTime(timeStr)
	cpuPercent, _ := strconv.ParseFloat(cpuStr, 64)
	memoryKB, _ := strconv.ParseInt(memoryStr, 10, 64)
	
	return ToolResult{
		Name:       tool.Name,
		ExecTime:   execTime,
		CPUPercent: cpuPercent,
		MemoryKB:   memoryKB,
		Timestamp:  time.Now().Format(time.RFC3339),
		Error:      nil, // Всегда игнорируем ошибки от анализаторов
	}
}

// Запуск инструмента и сбор метрик (стандартный метод)
func runTool(tool Tool, targetDir string) ToolResult {
	// Копируем команду и подставляем путь к целевой директории
	cmd := make([]string, len(tool.Command))
	copy(cmd, tool.Command)
	
	// Расширяем команду до необходимой длины
	for len(cmd) <= tool.TargetArg {
		cmd = append(cmd, "")
	}
	cmd[tool.TargetArg] = targetDir
	
	// Подготавливаем команду time
	timeCmd := exec.Command("/usr/bin/time", append([]string{"-v"}, cmd...)...)
	
	// Перенаправляем вывод - игнорируем ошибку выполнения
	output, _ := timeCmd.CombinedOutput()
	
	// Не выводим предупреждение о завершении с ошибкой - это нормально для анализаторов
	
	// Извлекаем метрики из вывода time
	timeStr := extractRegex(timeRegex, string(output), "0")
	cpuStr := extractRegex(cpuRegex, string(output), "0")
	memoryStr := extractRegex(memoryRegex, string(output), "0")
	
	// Преобразуем строки в числа
	execTime := parseTime(timeStr)
	cpuPercent, _ := strconv.ParseFloat(cpuStr, 64)
	memoryKB, _ := strconv.ParseInt(memoryStr, 10, 64)
	
	return ToolResult{
		Name:       tool.Name,
		ExecTime:   execTime,
		CPUPercent: cpuPercent,
		MemoryKB:   memoryKB,
		Timestamp:  time.Now().Format(time.RFC3339),
		Error:      nil, // Всегда игнорируем ошибки от анализаторов
	}
}

// Извлекает значение из текста по регулярному выражению
func extractRegex(re *regexp.Regexp, text, defaultValue string) string {
	matches := re.FindStringSubmatch(text)
	if len(matches) > 1 {
		return matches[1]
	}
	return defaultValue
}

// Преобразует строку времени в секунды
func parseTime(timeStr string) float64 {
	parts := strings.Split(timeStr, ":")
	if len(parts) == 2 {
		// Формат m:ss
		minutes, _ := strconv.ParseFloat(parts[0], 64)
		seconds, _ := strconv.ParseFloat(parts[1], 64)
		return minutes*60 + seconds
	} else if len(parts) == 3 {
		// Формат h:mm:ss
		hours, _ := strconv.ParseFloat(parts[0], 64)
		minutes, _ := strconv.ParseFloat(parts[1], 64)
		seconds, _ := strconv.ParseFloat(parts[2], 64)
		return hours*3600 + minutes*60 + seconds
	}
	// Если не удалось распарсить, пробуем просто как число
	result, _ := strconv.ParseFloat(timeStr, 64)
	return result
}

func isStandardAnalyzer(name string) bool {
    for _, tool := range standardTools {
        if tool.Name == name {
            return true
        }
    }
    return false
}

// Собирает метрики для всех инструментов
func collectMetrics(targetDir string, iterations int, outputFile string, parallelism int, smartScheduling bool, commandTemplate string, customAnalyzer string) {
    var wg sync.WaitGroup
    var tools []Tool
    
    // Используем стандартные инструменты
    tools = make([]Tool, len(standardTools))
    copy(tools, standardTools)
    
    // Добавляем пользовательский анализатор, если указан
    if customAnalyzer != "" && !isStandardAnalyzer(customAnalyzer) {
        customTool := Tool{
            Name:      customAnalyzer,
            Command:   []string{customAnalyzer},
            Weight:    1,
            TargetArg: 1, // Предполагаем, что путь - первый аргумент
        }
        tools = append(tools, customTool)
    }
	
	resultChan := make(chan ToolResult, iterations*len(tools))
	
	// Ограничиваем количество одновременно выполняющихся горутин
	if parallelism <= 0 {
		parallelism = runtime.NumCPU() - 1
		if parallelism <= 0 {
			parallelism = 1
		}
	}
	sem := make(chan struct{}, parallelism)
	
	// Планируем задачи
	taskCount := 0
	
	// Вычисляем количество итераций для каждого инструмента
	// Всегда используем точно указанное количество итераций для каждого инструмента
	toolIterations := iterations
	
	for _, tool := range tools {
		for i := 0; i < toolIterations; i++ {
			wg.Add(1)
			taskCount++
			
			go func(t Tool) {
				defer wg.Done()
				
				// Получаем "разрешение" на выполнение
				sem <- struct{}{}
				defer func() { <-sem }()
				
				// Запускаем инструмент с указанным шаблоном команды
				var result ToolResult
				if commandTemplate != "" {
					result = runToolWithTemplate(t, targetDir, commandTemplate)
				} else {
					result = runTool(t, targetDir)
				}
				resultChan <- result
			}(tool)
		}
	}
	
	// Ожидаем завершения всех горутин в отдельной горутине
	go func() {
		wg.Wait()
		close(resultChan)
	}()
	
	// Собираем результаты
	results := make([]ToolResult, 0, taskCount)
	for result := range resultChan {
		results = append(results, result)
	}
	
	// Записываем результаты в CSV
	writeResultsToCSV(results, outputFile)
	
	fmt.Printf("Собрано %d измерений в %s (по %d для каждого из %d инструментов)\n", len(results), outputFile, toolIterations, len(tools))
}

// Записывает результаты в CSV-файл
func writeResultsToCSV(results []ToolResult, outputFile string) {
	// Проверяем существование файла
	fileExists := false
	if _, err := os.Stat(outputFile); err == nil {
		fileExists = true
	}
	
	// Открываем файл для записи (создаем, если не существует)
	file, err := os.OpenFile(outputFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Ошибка открытия файла %s: %v\n", outputFile, err)
		return
	}
	defer file.Close()
	
	// Создаем writer для CSV
	writer := csv.NewWriter(file)
	defer writer.Flush()
	
	// Записываем заголовок, если файл новый
	if !fileExists {
		writer.Write([]string{"Tool", "Execution Time (s)", "CPU Used (%)", "Memory Used (KB)"})
	}
	
	// Записываем результаты
	for _, result := range results {
		writer.Write([]string{
			result.Name,
			fmt.Sprintf("%.2f", result.ExecTime),
			fmt.Sprintf("%.2f", result.CPUPercent),
			fmt.Sprintf("%d", result.MemoryKB),
		})
	}
}

func main() {
    // Разбор аргументов командной строки
    targetDirPtr := flag.String("target", ".", "Директория для анализа")
    iterationsPtr := flag.Int("iterations", 10, "Количество итераций")
    outputFilePtr := flag.String("output", "metrics_data.csv", "Выходной CSV-файл")
    parallelismPtr := flag.Int("parallel", 0, "Количество параллельных процессов (0 = авто)")
    smartPtr := flag.Bool("smart", true, "Использовать умное планирование (не влияет на количество итераций)")
    commandTemplatePtr := flag.String("command-template", "{analyzer_cmd} {path}", "Шаблон команды для запуска анализатора")
    customAnalyzerPtr := flag.String("custom-analyzer", "", "Пользовательский анализатор для запуска вместе со стандартными")
    flag.Parse()
    
    // Преобразуем относительный путь в абсолютный
    targetDir, err := filepath.Abs(*targetDirPtr)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Ошибка определения пути: %v\n", err)
        os.Exit(1)
    }
    
    startTime := time.Now()
    fmt.Printf("Начинаем сбор метрик: %d итераций для каждого из %d инструментов\n", *iterationsPtr, len(standardTools))
    fmt.Printf("Шаблон команды: %s\n", *commandTemplatePtr)
    
    // Если указан пользовательский анализатор, выводим информацию
    if *customAnalyzerPtr != "" {
        fmt.Printf("Включен пользовательский анализатор: %s\n", *customAnalyzerPtr)
    }
    
    collectMetrics(targetDir, *iterationsPtr, *outputFilePtr, *parallelismPtr, *smartPtr, *commandTemplatePtr, *customAnalyzerPtr)
    
    elapsed := time.Since(startTime)
    fmt.Printf("Сбор метрик завершен за %.2f секунд\n", elapsed.Seconds())
}