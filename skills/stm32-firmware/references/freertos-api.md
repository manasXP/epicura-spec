# FreeRTOS API Reference

Complete reference for FreeRTOS in STM32 applications.

## Task Management

### xTaskCreate()
```c
BaseType_t xTaskCreate(
    TaskFunction_t pvTaskCode,
    const char * const pcName,
    uint16_t usStackDepth,
    void *pvParameters,
    UBaseType_t uxPriority,
    TaskHandle_t *pxCreatedTask
);
```
**Parameters:**
- `pvTaskCode`: Pointer to task function
- `pcName`: Descriptive name (debugging only)
- `usStackDepth`: Stack size in **words** (not bytes)
- `pvParameters`: Pointer passed to task
- `uxPriority`: Task priority (0 = lowest)
- `pxCreatedTask`: Handle to created task (can be NULL)

**Returns:** `pdPASS` if successful, `errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY` if failed

**Example:**
```c
void vTaskFunction(void *pvParameters) {
    for(;;) {
        // Task code
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

TaskHandle_t xHandle;
BaseType_t result = xTaskCreate(
    vTaskFunction,
    "TaskName",
    512,  // 512 words = 2KB stack
    NULL,
    tskIDLE_PRIORITY + 1,
    &xHandle
);
```

### xTaskCreateStatic()
```c
TaskHandle_t xTaskCreateStatic(
    TaskFunction_t pxTaskCode,
    const char * const pcName,
    uint32_t ulStackDepth,
    void *pvParameters,
    UBaseType_t uxPriority,
    StackType_t * const puxStackBuffer,
    StaticTask_t * const pxTaskBuffer
);
```
**Use:** Static allocation (no heap usage)

**Example:**
```c
static StaticTask_t xTaskBuffer;
static StackType_t xStack[512];

TaskHandle_t xHandle = xTaskCreateStatic(
    vTaskFunction,
    "TaskName",
    512,
    NULL,
    tskIDLE_PRIORITY + 1,
    xStack,
    &xTaskBuffer
);
```

### vTaskDelete()
```c
void vTaskDelete(TaskHandle_t xTask);
```
**Parameters:**
- `xTask`: Handle of task to delete (NULL = calling task)

**Example:**
```c
vTaskDelete(NULL);  // Delete current task
vTaskDelete(xHandle);  // Delete specific task
```

### vTaskDelay()
```c
void vTaskDelay(const TickType_t xTicksToDelay);
```
**Delay relative to time called**

**Example:**
```c
vTaskDelay(pdMS_TO_TICKS(100));  // Delay 100ms
```

### vTaskDelayUntil()
```c
void vTaskDelayUntil(
    TickType_t * const pxPreviousWakeTime,
    const TickType_t xTimeIncrement
);
```
**Delay absolute for periodic tasks**

**Example:**
```c
TickType_t xLastWakeTime = xTaskGetTickCount();
for(;;) {
    // Do periodic work
    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(100));
}
```

### uxTaskPriorityGet()
```c
UBaseType_t uxTaskPriorityGet(TaskHandle_t xTask);
```
**Returns:** Current task priority

### vTaskPrioritySet()
```c
void vTaskPrioritySet(
    TaskHandle_t xTask,
    UBaseType_t uxNewPriority
);
```
**Change task priority at runtime**

### vTaskSuspend() / vTaskResume()
```c
void vTaskSuspend(TaskHandle_t xTaskToSuspend);
void vTaskResume(TaskHandle_t xTaskToResume);
BaseType_t xTaskResumeFromISR(TaskHandle_t xTaskToResume);
```
**Suspend/resume task execution**

## Queue Management

### xQueueCreate()
```c
QueueHandle_t xQueueCreate(
    UBaseType_t uxQueueLength,
    UBaseType_t uxItemSize
);
```
**Parameters:**
- `uxQueueLength`: Maximum number of items
- `uxItemSize`: Size of each item in bytes

**Example:**
```c
typedef struct {
    uint32_t value;
    uint8_t status;
} QueueData_t;

QueueHandle_t xQueue = xQueueCreate(10, sizeof(QueueData_t));
```

### xQueueSend() / xQueueSendToBack()
```c
BaseType_t xQueueSend(
    QueueHandle_t xQueue,
    const void *pvItemToQueue,
    TickType_t xTicksToWait
);
```
**Send item to back of queue**

**Returns:** `pdPASS` if sent, `errQUEUE_FULL` if timeout

**Example:**
```c
QueueData_t data = {.value = 42, .status = 1};
if (xQueueSend(xQueue, &data, pdMS_TO_TICKS(100)) != pdPASS) {
    // Handle timeout
}
```

### xQueueSendToFront()
```c
BaseType_t xQueueSendToFront(
    QueueHandle_t xQueue,
    const void *pvItemToQueue,
    TickType_t xTicksToWait
);
```
**Send item to front of queue (priority)**

### xQueueReceive()
```c
BaseType_t xQueueReceive(
    QueueHandle_t xQueue,
    void *pvBuffer,
    TickType_t xTicksToWait
);
```
**Receive and remove item from queue**

**Example:**
```c
QueueData_t received;
if (xQueueReceive(xQueue, &received, portMAX_DELAY) == pdPASS) {
    // Process received data
}
```

### xQueuePeek()
```c
BaseType_t xQueuePeek(
    QueueHandle_t xQueue,
    void *pvBuffer,
    TickType_t xTicksToWait
);
```
**Receive but don't remove item**

### uxQueueMessagesWaiting()
```c
UBaseType_t uxQueueMessagesWaiting(QueueHandle_t xQueue);
```
**Returns:** Number of items in queue

### ISR-Safe Queue Functions
```c
BaseType_t xQueueSendFromISR(
    QueueHandle_t xQueue,
    const void *pvItemToQueue,
    BaseType_t *pxHigherPriorityTaskWoken
);

BaseType_t xQueueReceiveFromISR(
    QueueHandle_t xQueue,
    void *pvBuffer,
    BaseType_t *pxHigherPriorityTaskWoken
);
```

**Example:**
```c
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    
    uint8_t data = rxBuffer[0];
    xQueueSendFromISR(xQueue, &data, &xHigherPriorityTaskWoken);
    
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

## Semaphore Management

### Binary Semaphores

```c
SemaphoreHandle_t xSemaphoreCreateBinary(void);
```
**Use:** Synchronization between tasks/ISRs

**Example:**
```c
SemaphoreHandle_t xBinarySem = xSemaphoreCreateBinary();

// ISR gives semaphore
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xSemaphoreGiveFromISR(xBinarySem, &xHigherPriorityTaskWoken);
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}

// Task waits for semaphore
void vTaskFunction(void *pvParameters) {
    for(;;) {
        if (xSemaphoreTake(xBinarySem, portMAX_DELAY) == pdPASS) {
            // Process event
        }
    }
}
```

### Counting Semaphores

```c
SemaphoreHandle_t xSemaphoreCreateCounting(
    UBaseType_t uxMaxCount,
    UBaseType_t uxInitialCount
);
```
**Use:** Resource counting, multiple resources

**Example:**
```c
// 5 available buffers
SemaphoreHandle_t xCountingSem = xSemaphoreCreateCounting(5, 5);

// Acquire buffer
if (xSemaphoreTake(xCountingSem, pdMS_TO_TICKS(100)) == pdPASS) {
    // Use buffer
    // Release when done
    xSemaphoreGive(xCountingSem);
}
```

### Mutexes

```c
SemaphoreHandle_t xSemaphoreCreateMutex(void);
```
**Use:** Mutual exclusion with priority inheritance

**Example:**
```c
SemaphoreHandle_t xMutex = xSemaphoreCreateMutex();

void AccessSharedResource(void) {
    if (xSemaphoreTake(xMutex, pdMS_TO_TICKS(100)) == pdPASS) {
        // Critical section
        // Access shared resource
        
        xSemaphoreGive(xMutex);
    }
}
```

### Recursive Mutexes

```c
SemaphoreHandle_t xSemaphoreCreateRecursiveMutex(void);
BaseType_t xSemaphoreTakeRecursive(
    SemaphoreHandle_t xMutex,
    TickType_t xTicksToWait
);
BaseType_t xSemaphoreGiveRecursive(SemaphoreHandle_t xMutex);
```
**Use:** When same task needs to take mutex multiple times

## Software Timers

### xTimerCreate()
```c
TimerHandle_t xTimerCreate(
    const char * const pcTimerName,
    const TickType_t xTimerPeriodInTicks,
    const UBaseType_t uxAutoReload,
    void * const pvTimerID,
    TimerCallbackFunction_t pxCallbackFunction
);
```

**Parameters:**
- `pcTimerName`: Descriptive name
- `xTimerPeriodInTicks`: Timer period
- `uxAutoReload`: `pdTRUE` = auto-reload, `pdFALSE` = one-shot
- `pvTimerID`: Timer ID (passed to callback)
- `pxCallbackFunction`: Callback function

**Example:**
```c
void vTimerCallback(TimerHandle_t xTimer) {
    // Timer expired
    uint32_t id = (uint32_t)pvTimerGetTimerID(xTimer);
}

TimerHandle_t xTimer = xTimerCreate(
    "Timer",
    pdMS_TO_TICKS(1000),  // 1 second
    pdTRUE,               // Auto-reload
    (void*)0,             // Timer ID
    vTimerCallback
);
```

### Timer Control Functions
```c
BaseType_t xTimerStart(TimerHandle_t xTimer, TickType_t xTicksToWait);
BaseType_t xTimerStop(TimerHandle_t xTimer, TickType_t xTicksToWait);
BaseType_t xTimerReset(TimerHandle_t xTimer, TickType_t xTicksToWait);
BaseType_t xTimerChangePeriod(
    TimerHandle_t xTimer,
    TickType_t xNewPeriod,
    TickType_t xTicksToWait
);
```

**Example:**
```c
// Start timer
xTimerStart(xTimer, 0);

// Change period to 2 seconds
xTimerChangePeriod(xTimer, pdMS_TO_TICKS(2000), 0);

// Stop timer
xTimerStop(xTimer, 0);
```

### Timer ISR Functions
```c
BaseType_t xTimerStartFromISR(
    TimerHandle_t xTimer,
    BaseType_t *pxHigherPriorityTaskWoken
);
BaseType_t xTimerStopFromISR(
    TimerHandle_t xTimer,
    BaseType_t *pxHigherPriorityTaskWoken
);
```

## Event Groups

### xEventGroupCreate()
```c
EventGroupHandle_t xEventGroupCreate(void);
```
**Use:** Synchronize multiple tasks, signal multiple events

**Example:**
```c
#define BIT_0  (1 << 0)
#define BIT_1  (1 << 1)
#define BIT_2  (1 << 2)

EventGroupHandle_t xEventGroup = xEventGroupCreate();
```

### xEventGroupSetBits()
```c
EventBits_t xEventGroupSetBits(
    EventGroupHandle_t xEventGroup,
    const EventBits_t uxBitsToSet
);
```
**Set one or more event bits**

**Example:**
```c
xEventGroupSetBits(xEventGroup, BIT_0 | BIT_1);
```

### xEventGroupWaitBits()
```c
EventBits_t xEventGroupWaitBits(
    EventGroupHandle_t xEventGroup,
    const EventBits_t uxBitsToWaitFor,
    const BaseType_t xClearOnExit,
    const BaseType_t xWaitForAllBits,
    TickType_t xTicksToWait
);
```

**Parameters:**
- `uxBitsToWaitFor`: Bits to wait for
- `xClearOnExit`: Clear bits on exit if `pdTRUE`
- `xWaitForAllBits`: Wait for all bits if `pdTRUE`, any if `pdFALSE`
- `xTicksToWait`: Timeout

**Example:**
```c
// Wait for BIT_0 OR BIT_1
EventBits_t uxBits = xEventGroupWaitBits(
    xEventGroup,
    BIT_0 | BIT_1,
    pdTRUE,        // Clear on exit
    pdFALSE,       // Wait for any bit
    portMAX_DELAY
);

if (uxBits & BIT_0) {
    // BIT_0 was set
}
```

### xEventGroupClearBits()
```c
EventBits_t xEventGroupClearBits(
    EventGroupHandle_t xEventGroup,
    const EventBits_t uxBitsToClear
);
```

## Task Notifications

### xTaskNotifyGive() / ulTaskNotifyTake()
```c
BaseType_t xTaskNotifyGive(TaskHandle_t xTaskToNotify);

uint32_t ulTaskNotifyTake(
    BaseType_t xClearCountOnExit,
    TickType_t xTicksToWait
);
```
**Use:** Lightweight binary semaphore alternative**

Example:**
```c
// ISR notifies task
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    vTaskNotifyGiveFromISR(xTaskHandle, &xHigherPriorityTaskWoken);
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}

// Task waits
void vTask(void *pvParameters) {
    for(;;) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        // Process event
    }
}
```

### xTaskNotify() / xTaskNotifyWait()
```c
BaseType_t xTaskNotify(
    TaskHandle_t xTaskToNotify,
    uint32_t ulValue,
    eNotifyAction eAction
);

BaseType_t xTaskNotifyWait(
    uint32_t ulBitsToClearOnEntry,
    uint32_t ulBitsToClearOnExit,
    uint32_t *pulNotificationValue,
    TickType_t xTicksToWait
);
```
**Use:** Lightweight event group alternative

**Actions:**
- `eNoAction`: Notify without updating value
- `eSetBits`: Set bits in notification value
- `eIncrement`: Increment notification value
- `eSetValueWithOverwrite`: Overwrite value
- `eSetValueWithoutOverwrite`: Set if not already pending

**Example:**
```c
// Send notification with value
xTaskNotify(xTaskHandle, 0x01, eSetBits);

// Wait and get value
uint32_t ulNotificationValue;
if (xTaskNotifyWait(0x00, 0xFFFFFFFF, &ulNotificationValue, portMAX_DELAY) == pdPASS) {
    // Check bits
    if (ulNotificationValue & 0x01) {
        // Handle event
    }
}
```

## Critical Sections

### taskENTER_CRITICAL() / taskEXIT_CRITICAL()
```c
taskENTER_CRITICAL();
// Critical section - interrupts disabled
taskEXIT_CRITICAL();
```
**Use:** Short critical sections in tasks

### taskENTER_CRITICAL_FROM_ISR() / taskEXIT_CRITICAL_FROM_ISR()
```c
UBaseType_t uxSavedInterruptStatus;
uxSavedInterruptStatus = taskENTER_CRITICAL_FROM_ISR();
// Critical section in ISR
taskEXIT_CRITICAL_FROM_ISR(uxSavedInterruptStatus);
```

### vTaskSuspendAll() / xTaskResumeAll()
```c
vTaskSuspendAll();
// Scheduler suspended - interrupts still enabled
// Faster than critical section for longer operations
xTaskResumeAll();
```

## Memory Management

### pvPortMalloc() / vPortFree()
```c
void *pvPortMalloc(size_t xWantedSize);
void vPortFree(void *pv);
```
**Use:** FreeRTOS heap allocation

**Example:**
```c
uint8_t *pBuffer = (uint8_t*)pvPortMalloc(256);
if (pBuffer != NULL) {
    // Use buffer
    vPortFree(pBuffer);
}
```

### xPortGetFreeHeapSize()
```c
size_t xPortGetFreeHeapSize(void);
```
**Returns:** Current free heap size in bytes

### xPortGetMinimumEverFreeHeapSize()
```c
size_t xPortGetMinimumEverFreeHeapSize(void);
```
**Returns:** Minimum free heap size since boot (heap high water mark)

## Utility Functions

### xTaskGetTickCount()
```c
TickType_t xTaskGetTickCount(void);
```
**Returns:** Current tick count

### pdMS_TO_TICKS()
```c
TickType_t ticks = pdMS_TO_TICKS(milliseconds);
```
**Convert milliseconds to ticks**

### portMAX_DELAY
```c
// Wait forever
xSemaphoreTake(xSem, portMAX_DELAY);
```

### vTaskGetRunTimeStats()
```c
void vTaskGetRunTimeStats(char *pcWriteBuffer);
```
**Get runtime statistics (requires config)**

**FreeRTOSConfig.h:**
```c
#define configGENERATE_RUN_TIME_STATS      1
#define configUSE_STATS_FORMATTING_FUNCTIONS 1
```

## Hook Functions

### vApplicationIdleHook()
```c
void vApplicationIdleHook(void) {
    // Called when idle task runs
    // Use for low-power modes
}
```

### vApplicationStackOverflowHook()
```c
void vApplicationStackOverflowHook(
    TaskHandle_t xTask,
    char *pcTaskName
) {
    // Stack overflow detected
}
```

### vApplicationMallocFailedHook()
```c
void vApplicationMallocFailedHook(void) {
    // Memory allocation failed
}
```

### vApplicationTickHook()
```c
void vApplicationTickHook(void) {
    // Called every tick (keep very short!)
}
```

## Configuration Constants

Common FreeRTOSConfig.h settings:

```c
#define configUSE_PREEMPTION              1
#define configUSE_TIME_SLICING            1
#define configUSE_IDLE_HOOK               0
#define configUSE_TICK_HOOK               0
#define configCPU_CLOCK_HZ                168000000
#define configTICK_RATE_HZ                1000
#define configMAX_PRIORITIES              5
#define configMINIMAL_STACK_SIZE          128
#define configTOTAL_HEAP_SIZE             20480
#define configMAX_TASK_NAME_LEN           16
#define configUSE_TRACE_FACILITY          1
#define configUSE_16_BIT_TICKS            0
#define configIDLE_SHOULD_YIELD           1
#define configUSE_MUTEXES                 1
#define configUSE_RECURSIVE_MUTEXES       1
#define configUSE_COUNTING_SEMAPHORES     1
#define configUSE_TASK_NOTIFICATIONS      1
#define configQUEUE_REGISTRY_SIZE         10

// Interrupt priorities (Cortex-M specific)
#define configPRIO_BITS                   4
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY      15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5
#define configKERNEL_INTERRUPT_PRIORITY 
    (configLIBRARY_LOWEST_INTERRUPT_PRIORITY << (8 - configPRIO_BITS))
#define configMAX_SYSCALL_INTERRUPT_PRIORITY
    (configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << (8 - configPRIO_BITS))
```

## Important Notes

1. **Interrupt Priorities**: ISRs calling FreeRTOS functions must have priority >= `configMAX_SYSCALL_INTERRUPT_PRIORITY`

2. **Stack Sizes**: Specified in **words**, not bytes (multiply by 4 for ARM Cortex-M)

3. **Task Priorities**: Higher number = higher priority

4. **Tick Rate**: Typically 1000 Hz (1ms tick) for general use

5. **Heap Schemes**:
   - heap_1: Simple, no free
   - heap_2: Best fit, no coalescence
   - heap_3: Wraps malloc/free
   - heap_4: Best fit with coalescence (recommended)
   - heap_5: Like heap_4, multiple non-contiguous regions

6. **Critical Section Duration**: Keep as short as possible (<10-20 instructions)

7. **ISR Context**: Always use FromISR variants in interrupt handlers

8. **portYIELD_FROM_ISR()**: Call after setting `xHigherPriorityTaskWoken` to force context switch
