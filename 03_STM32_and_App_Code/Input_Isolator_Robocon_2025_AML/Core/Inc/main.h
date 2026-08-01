/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */
void uart_printf(const char *format, ...);
/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define IN_1_Pin GPIO_PIN_0
#define IN_1_GPIO_Port GPIOA
#define IN_2_Pin GPIO_PIN_1
#define IN_2_GPIO_Port GPIOA
#define IN_3_Pin GPIO_PIN_2
#define IN_3_GPIO_Port GPIOA
#define IN_4_Pin GPIO_PIN_3
#define IN_4_GPIO_Port GPIOA
#define IN_5_Pin GPIO_PIN_4
#define IN_5_GPIO_Port GPIOA
#define IN_6_Pin GPIO_PIN_5
#define IN_6_GPIO_Port GPIOA
#define IN_7_Pin GPIO_PIN_6
#define IN_7_GPIO_Port GPIOA
#define IN_8_Pin GPIO_PIN_7
#define IN_8_GPIO_Port GPIOA
#define IN_9_Pin GPIO_PIN_0
#define IN_9_GPIO_Port GPIOB
#define IN_10_Pin GPIO_PIN_1
#define IN_10_GPIO_Port GPIOB
#define IN_11_Pin GPIO_PIN_2
#define IN_11_GPIO_Port GPIOB
#define IN_12_Pin GPIO_PIN_10
#define IN_12_GPIO_Port GPIOB
#define IN_13_Pin GPIO_PIN_11
#define IN_13_GPIO_Port GPIOB
#define IN_14_Pin GPIO_PIN_12
#define IN_14_GPIO_Port GPIOB
#define IN_15_Pin GPIO_PIN_13
#define IN_15_GPIO_Port GPIOB
#define IN_16_Pin GPIO_PIN_14
#define IN_16_GPIO_Port GPIOB
#define STT_LED_Pin GPIO_PIN_10
#define STT_LED_GPIO_Port GPIOA

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
