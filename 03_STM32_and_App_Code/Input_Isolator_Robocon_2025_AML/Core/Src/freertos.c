/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "main.h"
#include "gpio.h"
#include "usart.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
typedef struct State_IO {
  uint8_t in1;
  uint8_t in2;
  uint8_t in3;
  uint8_t in4;
  uint8_t in5;
  uint8_t in6;
  uint8_t in7;
  uint8_t in8;
  uint8_t in9;
  uint8_t in10;
  uint8_t in11;
  uint8_t in12;
  uint8_t in13;
  uint8_t in14;
  uint8_t in15;
  uint8_t in16;
} State_IO;
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */

/* USER CODE END Variables */
osThreadId ReadIOTaskHandle;
osThreadId SendUartTaskHandle;
osMessageQId BitMapQueue01Handle;

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */
static uint16_t Read_GPIO_Bitmap(void);
void ReadIOTask(void const * argument);
void SendUartTask(void const * argument);
/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void const * argument);
void StartTask02(void const * argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/* GetIdleTaskMemory prototype (linked to static allocation support) */
void vApplicationGetIdleTaskMemory( StaticTask_t **ppxIdleTaskTCBBuffer, StackType_t **ppxIdleTaskStackBuffer, uint32_t *pulIdleTaskStackSize );

/* USER CODE BEGIN GET_IDLE_TASK_MEMORY */
static StaticTask_t xIdleTaskTCBBuffer;
static StackType_t xIdleStack[configMINIMAL_STACK_SIZE];

void vApplicationGetIdleTaskMemory( StaticTask_t **ppxIdleTaskTCBBuffer, StackType_t **ppxIdleTaskStackBuffer, uint32_t *pulIdleTaskStackSize )
{
  *ppxIdleTaskTCBBuffer = &xIdleTaskTCBBuffer;
  *ppxIdleTaskStackBuffer = &xIdleStack[0];
  *pulIdleTaskStackSize = configMINIMAL_STACK_SIZE;
  /* place for user code */
}
/* USER CODE END GET_IDLE_TASK_MEMORY */

/* Helper Functions */
static uint16_t Read_GPIO_Bitmap(void)
{
    uint16_t bitmap = 0;
    bitmap |= (HAL_GPIO_ReadPin(IN_1_GPIO_Port, IN_1_Pin) << 0);
    bitmap |= (HAL_GPIO_ReadPin(IN_2_GPIO_Port, IN_2_Pin) << 1);
    bitmap |= (HAL_GPIO_ReadPin(IN_3_GPIO_Port, IN_3_Pin) << 2);
    bitmap |= (HAL_GPIO_ReadPin(IN_4_GPIO_Port, IN_4_Pin) << 3);
    bitmap |= (HAL_GPIO_ReadPin(IN_5_GPIO_Port, IN_5_Pin) << 4);
    bitmap |= (HAL_GPIO_ReadPin(IN_6_GPIO_Port, IN_6_Pin) << 5);
    bitmap |= (HAL_GPIO_ReadPin(IN_7_GPIO_Port, IN_7_Pin) << 6);
    bitmap |= (HAL_GPIO_ReadPin(IN_8_GPIO_Port, IN_8_Pin) << 7);
    bitmap |= (HAL_GPIO_ReadPin(IN_9_GPIO_Port, IN_9_Pin) << 8);
    bitmap |= (HAL_GPIO_ReadPin(IN_10_GPIO_Port, IN_10_Pin) << 9);
    bitmap |= (HAL_GPIO_ReadPin(IN_11_GPIO_Port, IN_11_Pin) << 10);
    bitmap |= (HAL_GPIO_ReadPin(IN_12_GPIO_Port, IN_12_Pin) << 11);
    bitmap |= (HAL_GPIO_ReadPin(IN_13_GPIO_Port, IN_13_Pin) << 12);
    bitmap |= (HAL_GPIO_ReadPin(IN_14_GPIO_Port, IN_14_Pin) << 13);
    bitmap |= (HAL_GPIO_ReadPin(IN_15_GPIO_Port, IN_15_Pin) << 14);
    bitmap |= (HAL_GPIO_ReadPin(IN_16_GPIO_Port, IN_16_Pin) << 15);
    return bitmap;
}

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */

  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* definition and creation of BitMapQueue01 */
  osMessageQDef(BitMapQueue01, 128, uint32_t);
  BitMapQueue01Handle = osMessageCreate(osMessageQ(BitMapQueue01), NULL);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* definition and creation of ReadIOTask */
  osThreadDef(ReadIOTask, StartDefaultTask, osPriorityNormal, 0, 128);
  ReadIOTaskHandle = osThreadCreate(osThread(ReadIOTask), NULL);

  /* definition and creation of SendUartTask */
  osThreadDef(SendUartTask, StartTask02, osPriorityBelowNormal, 0, 128);
  SendUartTaskHandle = osThreadCreate(osThread(SendUartTask), NULL);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

}

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the ReadIOTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void const * argument)
{
  /* USER CODE BEGIN StartInputReadTask */
  uint16_t io_bitmap;
  static int read_count = 0;

  for(;;)
  {
    // Đọc trạng thái 16 GPIO pins thành bitmap
    io_bitmap = Read_GPIO_Bitmap();

    // Gửi vào queue (non-blocking)
    osMessagePut(BitMapQueue01Handle, io_bitmap, 10);
    
    // Debug: Print mỗi 100 lần đọc
    read_count++;
    if (read_count >= 100) {
      read_count = 0;
      uart_printf("[READ] bitmap=0x%04X\r\n", io_bitmap);
    }

    // đang đoc bao nhiều hz =
    osDelay(1);
  }
  /* USER CODE END StartDefaultTask */
}

/* USER CODE BEGIN Header_StartTask02 */
/**
* @brief Function implementing the SendUartTask thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTask02 */
void StartTask02(void const * argument)
{
  /* USER CODE BEGIN StartInputSendTask */
  osEvent event;
  uint16_t io_bitmap;
  static int send_count = 0;
  static int queue_empty_count = 0;

  for(;;)
  {
    // Nhận dữ liệu từ queue (chờ tối đa 50ms)
    event = osMessageGet(BitMapQueue01Handle, 50);

    if(event.status == osEventMessage)
    {
      io_bitmap = event.value.v;  // Lấy giá trị từ queue

      // Bảo vệ UART


      // Gửi định dạng: "IN:0xABCD"
      uart_printf("IN:0x%04X\r\n", io_bitmap);
  

      
      send_count++;
    }
    else
3    {
      queue_empty_count++;
      
      // Debug mỗi 20 lần queue trống
      if (queue_empty_count >= 20) {
        queue_empty_count = 0;

        uart_printf("[SEND] Queue empty, sent=%d\r\n", send_count);

      }
    }

    osDelay(10);
  }
  /* USER CODE END StartTask02 */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

/* USER CODE END Application */

