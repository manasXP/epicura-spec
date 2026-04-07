---
name: stm32-firmware
description: Expert STM32 firmware development with MISRA C compliance, FreeRTOS integration, TouchGFX GUI development, and STM32CubeMX configuration. Use when creating production-ready STM32 embedded firmware requiring (1) MISRA C:2012 compliant code with static analysis, (2) FreeRTOS task management and IPC, (3) TouchGFX GUI applications, (4) STM32CubeMX/CubeIDE project setup, (5) HAL/LL driver integration, (6) Peripheral configuration (UART, SPI, I2C, ADC, timers, DMA), (7) Memory-safe embedded C patterns, or (8) Production firmware with comprehensive error handling and diagnostics.
---

# STM32 Firmware Expert

Production-grade STM32 firmware development following automotive and industrial standards with MISRA C compliance, real-time operating systems, and professional GUI frameworks.

## Core Architecture

### MISRA C:2012 Compliance

Follow these mandatory rules for production firmware:

**Rule 8.4**: Function declarations visible at point of use
- Declare all functions in headers before use
- Use `static` for file-scope functions

**Rule 8.13**: Pointer parameters should be `const` when not modified
```c
void ProcessData(const uint8_t* pData, uint16_t length);
```

**Rule 10.x**: Explicit casting for all type conversions
```c
uint16_t value = (uint16_t)ADC1->DR;  // Explicit cast
```

**Rule 11.x**: Pointer conversions must be explicit
```c
uint8_t* pBuffer = (uint8_t*)&dataStruct;
```

**Rule 14.4**: No unconditional control flow (no bare `for(;;)`)
```c
while(1U) { /* Main loop */ }  // Use while(1) instead
```

**Rule 15.6**: All `if`/`else` must use braces
```c
if (condition) {
    DoSomething();
}
```

**Rule 17.7**: Return values must be checked or explicitly cast to `(void)`
```c
(void)HAL_UART_Transmit(&huart1, data, len, timeout);
```

**Rule 21.x**: Avoid standard library functions with undefined behavior
- Use bounded string functions: `strncpy`, `snprintf`
- Validate all memory allocations

### Memory Management

**Stack usage**: Calculate worst-case per task
```c
#define TASK_STACK_SIZE_WORDS  512U
#define TASK_PRIORITY          (tskIDLE_PRIORITY + 2U)
```

**Heap management**: Use FreeRTOS heap_4 or heap_5 for deterministic allocation
```c
configTOTAL_HEAP_SIZE = 20480U  // 20KB heap
configMINIMAL_STACK_SIZE = 128U
```

**Static allocation**: Preferred for safety-critical systems
```c
static StaticTask_t xTaskBuffer;
static StackType_t xStack[TASK_STACK_SIZE_WORDS];
TaskHandle_t xHandle = xTaskCreateStatic(TaskFunction, "TaskName",
    TASK_STACK_SIZE_WORDS, NULL, TASK_PRIORITY, xStack, &xTaskBuffer);
```

### Error Handling

Implement comprehensive error handling at all layers:

```c
typedef enum {
    STATUS_OK = 0U,
    STATUS_ERROR = 1U,
    STATUS_BUSY = 2U,
    STATUS_TIMEOUT = 3U,
    STATUS_INVALID_PARAM = 4U
} StatusCode_t;

StatusCode_t FunctionName(void) {
    StatusCode_t status = STATUS_OK;
    
    if (inputValidation) {
        /* Process */
    } else {
        status = STATUS_INVALID_PARAM;
        ErrorHandler(__FILE__, __LINE__);
    }
    
    return status;
}
```

## FreeRTOS Integration

### Task Creation Pattern

```c
/* Task function prototype */
void vTaskFunction(void* pvParameters);

/* Create task in main or initialization */
BaseType_t xReturned = xTaskCreate(
    vTaskFunction,          // Task function
    "TaskName",            // Task name (debug)
    TASK_STACK_SIZE,       // Stack size in words
    NULL,                  // Task parameter
    TASK_PRIORITY,         // Priority
    &xTaskHandle           // Task handle (optional)
);

if (xReturned != pdPASS) {
    ErrorHandler(__FILE__, __LINE__);
}
```

### Inter-Task Communication

**Queues** for data passing:
```c
QueueHandle_t xQueue = xQueueCreate(10U, sizeof(uint32_t));

/* Sender task */
uint32_t dataToSend = 42U;
if (xQueueSend(xQueue, &dataToSend, pdMS_TO_TICKS(100U)) != pdPASS) {
    /* Handle timeout */
}

/* Receiver task */
uint32_t receivedData;
if (xQueueReceive(xQueue, &receivedData, portMAX_DELAY) == pdPASS) {
    /* Process data */
}
```

**Semaphores** for synchronization:
```c
SemaphoreHandle_t xBinarySem = xSemaphoreCreateBinary();

/* ISR gives semaphore */
BaseType_t xHigherPriorityTaskWoken = pdFALSE;
xSemaphoreGiveFromISR(xBinarySem, &xHigherPriorityTaskWoken);
portYIELD_FROM_ISR(xHigherPriorityTaskWoken);

/* Task waits */
if (xSemaphoreTake(xBinarySem, portMAX_DELAY) == pdPASS) {
    /* Process event */
}
```

**Mutexes** for resource protection:
```c
SemaphoreHandle_t xMutex = xSemaphoreCreateMutex();

if (xSemaphoreTake(xMutex, pdMS_TO_TICKS(100U)) == pdPASS) {
    /* Critical section */
    xSemaphoreGive(xMutex);
}
```

### Software Timers

```c
TimerHandle_t xTimer = xTimerCreate(
    "Timer",                    // Name
    pdMS_TO_TICKS(1000U),      // Period (1 second)
    pdTRUE,                    // Auto-reload
    NULL,                      // Timer ID
    vTimerCallback             // Callback function
);

void vTimerCallback(TimerHandle_t xTimer) {
    /* Timer expired - execute periodic action */
}

xTimerStart(xTimer, 0U);
```

## STM32CubeMX Configuration

### Project Setup Workflow

1. **Select MCU** based on requirements:
   - STM32F4: General purpose, good peripherals
   - STM32F7: Higher performance, DSP
   - STM32H7: Dual-core, high-speed peripherals
   - STM32L4: Low power applications

2. **Clock Configuration**:
   - Set system clock to maximum safe frequency
   - Configure peripheral clocks appropriately
   - Enable CSS (Clock Security System) for reliability

3. **GPIO Configuration**:
   - Set pin functions and modes
   - Configure pull-ups/pull-downs
   - Set GPIO speed and output type

4. **Peripheral Initialization**:
   - Enable required peripherals
   - Configure in CubeMX, generate initialization code
   - Initialization happens in `MX_*_Init()` functions

5. **Middleware/FreeRTOS**:
   - Enable FreeRTOS in middleware section
   - Configure heap size and stack sizes
   - Set timer source (prefer SysTick or TIM for high resolution)

### CubeMX Code Integration

User code sections are preserved between regenerations:
```c
/* USER CODE BEGIN Includes */
#include "app_config.h"
/* USER CODE END Includes */

void SystemClock_Config(void) {
    /* CubeMX generated code */
    
    /* USER CODE BEGIN SystemClock_Config */
    /* Custom clock adjustments */
    /* USER CODE END SystemClock_Config */
}
```

Always place custom code in USER CODE sections to prevent overwriting.

## HAL/LL Driver Usage

### HAL Driver Pattern (Higher Level)

**Blocking Mode**:
```c
uint8_t txData[] = "Hello";
HAL_StatusTypeDef status = HAL_UART_Transmit(&huart1, txData, 
    sizeof(txData), HAL_MAX_DELAY);
if (status != HAL_OK) {
    ErrorHandler(__FILE__, __LINE__);
}
```

**Interrupt Mode**:
```c
HAL_UART_Transmit_IT(&huart1, txData, sizeof(txData));

/* Callback in user code */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef* huart) {
    if (huart == &huart1) {
        /* Transmission complete */
    }
}
```

**DMA Mode** (most efficient):
```c
HAL_UART_Transmit_DMA(&huart1, txData, sizeof(txData));

void HAL_UART_TxCpltCallback(UART_HandleTypeDef* huart) {
    /* DMA transfer complete */
}
```

### LL Driver Pattern (Lower Level, More Efficient)

```c
/* Check if TX register empty */
if (LL_USART_IsActiveFlag_TXE(USART1)) {
    LL_USART_TransmitData8(USART1, data);
}

/* Read received data */
if (LL_USART_IsActiveFlag_RXNE(USART1)) {
    uint8_t received = LL_USART_ReceiveData8(USART1);
}
```

## TouchGFX Development

### Project Structure

```
TouchGFX/
├── gui/
│   ├── include/gui/
│   │   └── screen_screen/
│   ├── src/
│   │   ├── screen_screen/
│   │   └── model/
│   └── generated/
├── simulator/
└── target/
```

### Screen Implementation Pattern

**View (GUI logic)**:
```cpp
// screen_screenView.hpp
class screenView : public screenViewBase {
public:
    screenView();
    virtual ~screenView() {}
    virtual void setupScreen();
    virtual void tearDownScreen();
    
    // Button callback
    void buttonClicked();
    
private:
    // Custom methods
};
```

**Presenter (Business logic)**:
```cpp
// screen_screenPresenter.hpp
class screenPresenter : public touchgfx::Presenter {
public:
    screenPresenter(screenView& v);
    virtual void activate();
    virtual void deactivate();
    
    // Model interaction
    void updateData(uint32_t value);
    
private:
    screenView& view;
};
```

**Model (Data and backend)**:
```cpp
// Model.hpp
class Model : public touchgfx::Model {
public:
    Model();
    void tick();
    
    // Data getters/setters
    void setSensorValue(uint32_t value);
    uint32_t getSensorValue() const;
    
private:
    uint32_t sensorValue;
};
```

### FreeRTOS Integration with TouchGFX

Create separate task for GUI updates:
```c
void TouchGFX_Task(void* argument) {
    touchgfx::HAL::getInstance()->taskEntry();
}

void Backend_Task(void* argument) {
    while(1) {
        /* Read sensors, process data */
        uint32_t value = ReadSensor();
        
        /* Update model (thread-safe) */
        model->setSensorValue(value);
        
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

### Custom Widgets

```cpp
class CustomWidget : public touchgfx::Container {
public:
    CustomWidget();
    virtual ~CustomWidget() {}
    
    virtual void handleTickEvent();
    virtual void handleClickEvent(const ClickEvent& evt);
    
    void setValue(int value);
    
private:
    touchgfx::TextArea textArea;
    touchgfx::Box background;
    int currentValue;
};
```

## Peripheral Configuration Examples

### UART with DMA and Circular Buffer

```c
#define RX_BUFFER_SIZE 256U

static uint8_t rxBuffer[RX_BUFFER_SIZE];
static uint8_t rxCircularBuffer[RX_BUFFER_SIZE];
static volatile uint16_t rxWriteIndex = 0U;

void UART_Init(void) {
    /* Start DMA reception in circular mode */
    HAL_UART_Receive_DMA(&huart1, rxBuffer, RX_BUFFER_SIZE);
}

void HAL_UART_RxHalfCpltCallback(UART_HandleTypeDef* huart) {
    /* First half of buffer filled */
    uint16_t len = RX_BUFFER_SIZE / 2U;
    (void)memcpy(&rxCircularBuffer[rxWriteIndex], rxBuffer, len);
    rxWriteIndex = (rxWriteIndex + len) % RX_BUFFER_SIZE;
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef* huart) {
    /* Second half of buffer filled */
    uint16_t len = RX_BUFFER_SIZE / 2U;
    (void)memcpy(&rxCircularBuffer[rxWriteIndex], 
                 &rxBuffer[RX_BUFFER_SIZE / 2U], len);
    rxWriteIndex = (rxWriteIndex + len) % RX_BUFFER_SIZE;
}
```

### SPI with DMA

```c
void SPI_WriteRead(const uint8_t* pTxData, uint8_t* pRxData, uint16_t size) {
    /* Pull CS low */
    HAL_GPIO_WritePin(SPI_CS_GPIO_Port, SPI_CS_Pin, GPIO_PIN_RESET);
    
    /* Transmit and receive simultaneously */
    HAL_StatusTypeDef status = HAL_SPI_TransmitReceive_DMA(&hspi1, 
        (uint8_t*)pTxData, pRxData, size);
    
    if (status != HAL_OK) {
        ErrorHandler(__FILE__, __LINE__);
    }
}

void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef* hspi) {
    /* Pull CS high */
    HAL_GPIO_WritePin(SPI_CS_GPIO_Port, SPI_CS_Pin, GPIO_PIN_SET);
    
    /* Signal completion to task */
    xSemaphoreGiveFromISR(xSpiSemaphore, NULL);
}
```

### I2C with Error Recovery

```c
StatusCode_t I2C_WriteRegister(uint8_t devAddr, uint8_t regAddr, 
                               uint8_t value) {
    StatusCode_t status = STATUS_OK;
    uint8_t data[2] = {regAddr, value};
    
    HAL_StatusTypeDef halStatus = HAL_I2C_Master_Transmit(&hi2c1, 
        devAddr << 1U, data, sizeof(data), HAL_MAX_DELAY);
    
    if (halStatus != HAL_OK) {
        /* Check error type */
        if (hi2c1.ErrorCode & HAL_I2C_ERROR_AF) {
            /* NACK received - device not responding */
            status = STATUS_ERROR;
        } else if (hi2c1.ErrorCode & HAL_I2C_ERROR_TIMEOUT) {
            /* Bus timeout */
            status = STATUS_TIMEOUT;
            /* Reset I2C peripheral */
            HAL_I2C_DeInit(&hi2c1);
            HAL_I2C_Init(&hi2c1);
        }
    }
    
    return status;
}
```

### ADC with DMA Multi-Channel

```c
#define ADC_CHANNELS 4U
static uint16_t adcBuffer[ADC_CHANNELS];

void ADC_Start(void) {
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adcBuffer, ADC_CHANNELS);
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
    /* All channels converted */
    uint16_t ch1Value = adcBuffer[0];
    uint16_t ch2Value = adcBuffer[1];
    /* Process ADC values */
}
```

### Timer PWM Generation

```c
void PWM_Init(void) {
    /* Start PWM on channel 1 */
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
}

void PWM_SetDutyCycle(uint8_t percentage) {
    /* Calculate CCR value (0-100% maps to 0-ARR) */
    uint32_t pulse = (htim3.Init.Period * percentage) / 100U;
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, pulse);
}
```

### Header File Pattern

```c
#ifndef SENSOR_INTERFACE_H
#define SENSOR_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes */
#include "stm32f4xx_hal.h"
#include <stdint.h>

/* Constants */
#define SENSOR_TIMEOUT_MS    1000U
#define SENSOR_MAX_RETRY     3U

/* Type definitions */
typedef struct {
    uint32_t temperature;
    uint32_t humidity;
    uint8_t isValid;
} SensorData_t;

/* Function prototypes */
StatusCode_t Sensor_Init(void);
StatusCode_t Sensor_Read(SensorData_t* pData);
StatusCode_t Sensor_PowerDown(void);

#ifdef __cplusplus
}
#endif

#endif /* SENSOR_INTERFACE_H */
```

## Static Analysis Integration

### Compiler Settings for MISRA

Add to project compiler flags:
```
-Wall -Wextra -Wpedantic
-Wconversion -Wsign-conversion
-Wcast-align -Wcast-qual
-Wshadow -Wstrict-overflow
```

### PC-Lint Configuration

Create `project.lnt` for MISRA checking:
```
// Enable MISRA C:2012
+misra(2012)

// Project includes
-i"Core/Inc"
-i"App/Inc"
-i"Drivers/CMSIS/Include"

// Suppress specific warnings as needed
-esym(765,SystemInit) // External references
```

### Cppcheck MISRA Addon

```bash
cppcheck --enable=all --addon=misra.json \
  --suppress=missingIncludeSystem \
  --inline-suppr \
  Core/Src/*.c App/Src/*.c
```

## Debugging and Diagnostics

### Runtime Statistics

Enable FreeRTOS runtime stats in `FreeRTOSConfig.h`:
```c
#define configGENERATE_RUN_TIME_STATS      1
#define configUSE_STATS_FORMATTING_FUNCTIONS 1
```

Print task statistics:
```c
void PrintTaskStats(void) {
    char buffer[512];
    vTaskGetRunTimeStats(buffer);
    printf("%s\r\n", buffer);
}
```

### Stack Overflow Detection

```c
void vApplicationStackOverflowHook(TaskHandle_t xTask, char* pcTaskName) {
    /* Stack overflow detected for pcTaskName */
    printf("Stack overflow in task: %s\r\n", pcTaskName);
    ErrorHandler(__FILE__, __LINE__);
}
```

### Assert Macros

```c
#ifdef DEBUG
#define ASSERT(expr) \
    do { \
        if (!(expr)) { \
            printf("Assertion failed: %s, file %s, line %d\r\n", \
                   #expr, __FILE__, __LINE__); \
            while(1); \
        } \
    } while(0)
#else
#define ASSERT(expr) ((void)0)
#endif
```

## Production Checklist

- [ ] All MISRA C rules followed (run static analysis)
- [ ] All HAL return values checked or explicitly voided
- [ ] Stack sizes verified via runtime stats
- [ ] Heap size sufficient with margin (check `xPortGetFreeHeapSize()`)
- [ ] All interrupts have appropriate priorities (<`configMAX_SYSCALL_INTERRUPT_PRIORITY`)
- [ ] Watchdog timer configured and fed
- [ ] Error handling and recovery implemented
- [ ] Critical sections protected with mutexes/semaphores
- [ ] Memory barriers for volatile shared data
- [ ] Brown-out reset configured
- [ ] Clock security system enabled
- [ ] All peripherals properly deinitialized in low-power modes
- [ ] Flash read/write protection configured
- [ ] Debug features disabled in production builds

## Reference Documentation

See `references/` for:
- `misra-guidelines.md` - Detailed MISRA C:2012 rule explanations
- `freertos-api.md` - Complete FreeRTOS API reference
- `touchgfx-patterns.md` - TouchGFX design patterns and examples
- `stm32-hal-reference.md` - HAL driver function reference
- `peripheral-cookbook.md` - Common peripheral configurations

## Bundled Scripts

- `scripts/generate_freertos_task.py` - Generate boilerplate FreeRTOS task code
- `scripts/calculate_stack_size.py` - Calculate worst-case stack usage
- `scripts/misra_checker.sh` - Run MISRA compliance checks
- `scripts/memory_map_analyzer.py` - Analyze linker map file for memory usage
