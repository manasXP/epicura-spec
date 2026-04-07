# MISRA C:2012 Guidelines Reference

Complete reference for MISRA C:2012 compliance in STM32 firmware development.

## Mandatory Rules (Cannot be Violated)

### Rule 1.3: No undefined or critical unspecified behavior
- All code must have well-defined behavior
- Test all edge cases
- Document assumptions

### Rule 8.1: Types shall be explicitly specified
```c
// Bad
const x = 5;

// Good
const uint8_t x = 5U;
```

### Rule 8.4: Compatible declarations for external linkage
```c
// header.h
extern void MyFunction(uint16_t param);

// source.c
void MyFunction(uint16_t param) { /* ... */ }
```

### Rule 8.13: Const correctness for pointers
```c
// If pointer doesn't modify data, mark const
void ProcessBuffer(const uint8_t* pBuffer, uint16_t size);
```

### Rule 9.1: No use of uninitialized variables
```c
// Bad
uint32_t value;
if (value > 100) { /* ... */ }

// Good
uint32_t value = 0U;
if (value > 100) { /* ... */ }
```

## Type Conversion Rules

### Rule 10.1: Operands in appropriate context
```c
uint8_t a = 5U;
uint16_t b = (uint16_t)a * 2U;  // Explicit conversion
```

### Rule 10.3: Value of expression assigned to narrower type
```c
uint32_t large = 1000U;
uint8_t small = (uint8_t)large;  // Explicit cast required
```

### Rule 10.4: Both operands of operator shall have same type
```c
uint16_t a = 10U;
uint32_t b = 20U;
uint32_t result = (uint32_t)a + b;  // Cast to match types
```

### Rule 10.8: Composite expression cast
```c
uint16_t result = (uint16_t)(a + b);  // Cast entire expression
```

## Pointer Rules

### Rule 11.1: Conversions between function pointer and other types prohibited
```c
// Never cast function pointers to data pointers or vice versa
void (*pFunc)(void) = MyFunction;  // OK
void* pData = (void*)pFunc;        // VIOLATION
```

### Rule 11.2: Conversions between pointer to incomplete type prohibited
```c
struct MyStruct;  // Incomplete type
struct MyStruct* pStruct;  // OK - pointer to incomplete
void* pVoid = (void*)pStruct;  // OK - can cast to void*
```

### Rule 11.3: Cast between pointer to object and different pointer type
```c
// Requires explicit cast with careful consideration
uint8_t data[4];
uint32_t* pWord = (uint32_t*)data;  // Explicit cast required
```

### Rule 11.5: Cast from pointer to void to other pointer type
```c
void* pGeneric = malloc(sizeof(MyStruct_t));
MyStruct_t* pStruct = (MyStruct_t*)pGeneric;  // Explicit cast
```

### Rule 11.8: Removing const qualification
```c
const uint8_t* pConst = GetConstData();
uint8_t* pMutable = (uint8_t*)pConst;  // VIOLATION - don't remove const
```

### Rule 11.9: NULL pointer constant
```c
// Use NULL for pointer comparisons
uint8_t* ptr = NULL;
if (ptr != NULL) { /* ... */ }
```

## Expression Rules

### Rule 12.1: Precedence of operators
```c
// Use parentheses for clarity
uint32_t result = (a + b) * c;  // Clear precedence
```

### Rule 12.2: Right-hand operand of shift operator
```c
uint32_t value = 1U;
uint32_t shifted = value << 5U;  // Shift count < width of type
```

### Rule 13.1: Initializer list shall not have persistent side effects
```c
// Bad
uint8_t array[] = {getNextValue(), getNextValue()};  // Order undefined

// Good
uint8_t val1 = getNextValue();
uint8_t val2 = getNextValue();
uint8_t array[] = {val1, val2};
```

### Rule 13.2: Value of expression with side effects shall be used
```c
(void)HAL_UART_Transmit(&huart1, data, len, timeout);  // Void cast OK
```

### Rule 13.5: Right operand of && or || shall not contain side effects
```c
// Bad
if (flag && (counter++ < 10)) { /* ... */ }

// Good
counter++;
if (flag && (counter < 10)) { /* ... */ }
```

## Control Flow Rules

### Rule 14.1: No unreachable code
```c
// Bad
return value;
counter++;  // VIOLATION - unreachable

// Good
counter++;
return value;
```

### Rule 14.2: All non-null statements shall have an effect
```c
// Bad
if (condition) {
    a;  // VIOLATION - no effect
}

// Good
if (condition) {
    DoSomething(a);
}
```

### Rule 14.3: Controlling expressions shall not be invariant
```c
// Bad
while (1) { /* ... */ }  // VIOLATION - but commonly used

// Compliant
while (1U) { /* ... */ }  // Use 1U to show intent
// Or use break statements for exit conditions
```

### Rule 14.4: Controlling expression shall have Boolean type
```c
// Bad
uint8_t count = 10;
if (count) { /* ... */ }  // VIOLATION

// Good
if (count > 0U) { /* ... */ }
```

### Rule 15.1: goto statement shall not be used
```c
// Avoid goto in normal code
// Exception: Forward goto for error handling acceptable
```

### Rule 15.2: goto statement shall not jump backward
```c
// Never use goto to create loops
```

### Rule 15.3: All switch statements require default
```c
switch (value) {
    case 0U:
        /* Handle */
        break;
    case 1U:
        /* Handle */
        break;
    default:
        /* Handle unexpected values */
        break;
}
```

### Rule 15.4: No more than one break at end of switch clause
```c
// Only one break per case
case VALUE:
    DoSomething();
    break;  // Single break
```

### Rule 15.5: Function shall have single point of exit
```c
// Advisory - prefer single return
StatusCode_t MyFunction(void) {
    StatusCode_t status = STATUS_OK;
    
    if (condition1) {
        status = STATUS_ERROR;
        goto cleanup;
    }
    
    /* Processing */
    
cleanup:
    return status;
}
```

### Rule 15.6: All if/else if constructs shall use braces
```c
// Always use braces
if (condition) {
    DoSomething();
}

if (condition) {
    Action1();
} else {
    Action2();
}
```

### Rule 15.7: All if...else if shall have final else
```c
if (state == STATE_IDLE) {
    /* Handle */
} else if (state == STATE_BUSY) {
    /* Handle */
} else {
    /* Handle unexpected state */
}
```

## Pointer and Array Rules

### Rule 17.1: Features of <stdarg.h> shall not be used
```c
// Don't use varargs (va_list, va_start, etc.)
// Use fixed parameter functions instead
```

### Rule 17.2: Functions shall not call themselves
```c
// No recursive functions in embedded systems
// Use iteration instead
```

### Rule 17.3: Symbol shadowing not permitted
```c
// Bad
uint8_t value = 10U;
void Function(void) {
    uint8_t value = 20U;  // VIOLATION - shadows outer value
}

// Good - use different names
uint8_t globalValue = 10U;
void Function(void) {
    uint8_t localValue = 20U;
}
```

### Rule 17.4: All exit paths return a value
```c
StatusCode_t GetStatus(void) {
    if (condition) {
        return STATUS_OK;
    }
    // Must return in all paths
    return STATUS_ERROR;
}
```

### Rule 17.7: Return value shall be used
```c
// Check all return values
HAL_StatusTypeDef status = HAL_Init();
if (status != HAL_OK) {
    ErrorHandler(__FILE__, __LINE__);
}

// Or explicitly ignore
(void)HAL_UART_Transmit(&huart1, data, len, timeout);
```

### Rule 17.8: Function parameters shall not be modified
```c
// Bad
void Process(uint8_t value) {
    value++;  // VIOLATION - modifying parameter
}

// Good
void Process(uint8_t value) {
    uint8_t localValue = value;
    localValue++;  // Modify local copy
}
```

## Preprocessor Rules

### Rule 20.1: #include directives before other code
```c
// All includes at top of file
#include "stm32f4xx_hal.h"
#include "FreeRTOS.h"

// Then constants and code
```

### Rule 20.3: #include uses "" or <> consistently
```c
// Project files use ""
#include "app_config.h"

// System/library files use <>
#include <stdint.h>
#include <string.h>
```

### Rule 20.4: No use of malloc/free
```c
// In safety-critical code, use static allocation
// Or use FreeRTOS pvPortMalloc/vPortFree
```

### Rule 20.7: Macro parameters shall be enclosed in parentheses
```c
// Bad
#define SQUARE(x) x * x

// Good
#define SQUARE(x) ((x) * (x))
```

### Rule 20.10: # and ## operators shall not be used
```c
// Avoid stringification and token pasting
// Use regular functions instead
```

## Standard Library Rules

### Rule 21.1: #define and #undef shall not be used on reserved identifiers
```c
// Don't redefine standard library names
// Bad: #define errno myerrno
```

### Rule 21.2: Reserved identifier not to be used for macro name
```c
// Don't create macros with names like __FUNC or _Func
```

### Rule 21.3: Memory allocation functions not to be used
```c
// Don't use malloc, calloc, realloc, free
// Use FreeRTOS heap functions or static allocation
```

### Rule 21.4: setjmp and longjmp shall not be used
```c
// No non-local jumps
// Use structured error handling instead
```

### Rule 21.6: Use snprintf instead of sprintf
```c
// Bad
sprintf(buffer, "Value: %d", value);

// Good
snprintf(buffer, sizeof(buffer), "Value: %d", value);
```

## Common Patterns for Compliance

### Integer Literals
```c
// Always suffix integer constants
#define TIMEOUT_MS    1000U    // Unsigned
#define BUFFER_SIZE   256U
#define ERROR_CODE    -1       // Signed (no suffix for negative)
```

### Type Safety
```c
// Use sized types from stdint.h
uint8_t  byteValue = 0U;
uint16_t wordValue = 0U;
uint32_t dwordValue = 0UL;
int32_t  signedValue = 0;
```

### Enum Usage
```c
// Always specify underlying type
typedef enum {
    STATE_IDLE = 0U,
    STATE_BUSY = 1U,
    STATE_ERROR = 2U
} State_t;
```

### Boolean Expressions
```c
// Use explicit comparisons
if (counter > 0U) { /* ... */ }      // Good
if (counter) { /* ... */ }            // Bad - implicit

if (ptr != NULL) { /* ... */ }        // Good
if (ptr) { /* ... */ }                // Bad - implicit
```

### Loop Constructs
```c
// Prefer for loops with explicit bounds
for (uint8_t i = 0U; i < ARRAY_SIZE; i++) {
    array[i] = 0U;
}

// While loops need explicit conditions
while (status == STATUS_BUSY) {
    ProcessData();
}
```

### Function Return Checking
```c
// Always check critical function returns
HAL_StatusTypeDef status = HAL_SPI_Transmit(&hspi1, data, len, timeout);
if (status != HAL_OK) {
    // Handle error
}

// Or explicitly void non-critical returns
(void)HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);
```
