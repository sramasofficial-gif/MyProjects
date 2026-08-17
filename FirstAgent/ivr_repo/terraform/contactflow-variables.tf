############     Variables for Contact flow deployment    ################################

##############     Lambdas variable    #########################


variable "GetSsmParamsLambdaArn" {
  type = string
}

variable "AccountMemosLambdaArn" {
  type = string
}

variable "GetAccountStatusLambdaArn" {
  type = string
}

variable "GetAccountSummaryInfoLambdaArn" {
  type = string
}

variable "GetCardDetailsLambdaArn" {
  type = string
}

variable "TemporaryblockCardLambdaArn" {
  type = string
}

variable "VerifyPinLambdaArn" {
  type = string
}

variable "changepinLambdaArn" {
  type = string
}

variable "GetRewardsPointsLambdaArn" {
  type        = string
}

variable "GetPrimaryCardDetailsLambdaArn" {
  type        = string
}

variable "ActivateCardLambdaArn" {
  type        = string
}

variable "GetHolidayParamsLambdaArn" {
  type        = string
}

variable "SecureCallLambdaArn" {
  type        = string
}

variable "AgentDetailsLambdaArn" {
  type        = string
  description = "ARN of the Agent Details Lambda"
}

variable "CreateInteractionLambdaArn" {
  type        = string
}

variable "ValidatePhoneNumberLambdaARN" {
  type        = string
}

variable "GetDOBLambdaArn" {
  type        = string
}

variable "validateDOBLambdaArn" {
  type        = string
}


################################   contact flows variable    ############################

variable "cfQueueConfigContactFlowArn" {
  type = string
}

variable "cfErrorHandlingArn" {
  type = string
}

variable "cfActivateCardArn" {
  type = string
}

variable "cfPreMenuArn" {
  type = string
}

variable "cfMainMenuArn" {
  type = string
}

variable "cfAgentUIArn" {
  type = string
}

variable "cfRewardTransactionsFlowArn" {
  type        = string
}

variable "cfChangePinNewArn" {
  type        = string
}

variable "cfCreditLimitChangeArn" {
  type        = string
}

variable "cfAccountSummaryInfoArn" {
  type        = string
}

variable "cfVoiceMailCustomerWhisperArn" {
  type        = string
}

variable "cfVoiceMailCustomerQueueArn" {
  type        = string
}

variable "cfAgentWhisperQCArn" {
  type        = string
}

variable "cfAgentWhisperCallbackArn" {
  type        = string
}

variable "cfEnqueueCallbackArn" {
  type        = string
}

variable "cfCustomerQueueQCArn" {
  type        = string
}

variable "cfVoicemailModuleArn" {
  type        = string
}

variable "cfQueuesWithVoiceMailArn" {
  type        = string
}

variable "cfDefaultQueueTransferExtArn" {
  type        = string
}

variable "cfBackOfficeTaskFlowArn" {
  type = string
}

variable "cfLostAndStolenArn" {
  type        = string
}

variable "CfTransactionArn" {
  type        = string
}

variable "cfMainMenuCorporateArn" {
  type        = string
}

variable "cfMainMenuSMBArn" {
  type        = string
}

variable "cfRewardsArn" {
  type        = string
}

variable "cfVoiceMailCQArn" {
  type        = string
}

variable "cfVoicemailAgentWhisperArn" {
  type        = string
}

variable "cfAccountStatusArn" {
  type        = string
  description = "ARN of the Account Status Contact Flow"
}

variable "cfOutboundWhisperArn" {
  type = string
}

variable "cfElevationsTaskFlowArn" {
  type = string
}

#############################      contact flow modules variables      ################################# 

variable "moRbPinValidationArn" {
  type = string
}

variable "moRBsendOTCArn" {
  type = string
}

variable "moRBAccountLookupArn" {
  type = string
}

variable "moRBAccountLookupNoArn" {
  type = string
}

variable "moRBSetPINNoArn" {
  type        = string
}

variable "moRbDOBValidationNoArn" {
  type        = string
}

variable "moRBvalidatePhoneNumberNoArn" {
  type        = string
}

variable "moRBsendOTCNoArn" {
  type        = string
}

variable "moRbPinValidationNoArn" {
  type        = string
}

variable "moVoiceMailNoArn" {
  type        = string
}

variable "moGetQueueRoutingDataNoArn" {
  type        = string
}

variable "moSelectQueueNoArn" {
  type        = string
}

variable "SelectQueueLogicLambdaArn" {
  type = string
}

variable "cfCustomerQueueArn" {
  type = string
}


############################     Data table variables       #############################################

variable "dtGlobalSetNoArn" {
  type        = string
}

variable "dtQueuesMetricsNoArn" {
  type = string
}

variable "dtAgencyCodeConfigArn" {
  type = string
}

variable "dtVoiceMailNumberNoArn" {
  type = string
}

variable "dtVoiceMailDestinationNoArn" {
  type = string
}

#############################      Encryption variables      ################################# 

variable "KeyId" {
  type = string
}

variable "EncryptionKey" {
  type = string
}

#############################      Prompt variables      ################################# 

variable "BeepArn" {
  type = string
}

variable "CustomerqueuenewArn" {
  type = string
}

#############################      HOOP variables      ################################# 

variable "GS_HOOP_Arn" {
  type = string
}

#############################     queues variables  for routing profiles    ################################################

variable "rp_quickconnectsonly_queue_arn" {
  type = string
}


variable "rp_backoffice_en_queue_arn" {
  type = string 
}
variable "rp_manual_assignment_backoffice_task_queue_arn" {
  type = string
}
variable "rp_manual_assignment_backoffice_email_queue_arn" {
  type = string
}
variable "rp_backoffice_fr_queue_arn"  {
  type = string
}
variable "BackOffice_Task" {
  type = string
}

variable "rp_disputeInvestigator_en_queue_arn" {
  type = string 
}
variable "rp_disputeInvestigator_fr_queue_arn" {
  type = string
}

variable "rp_complaints_en_queue_arn" {
  type = string 
}
variable "rp_complaints_fr_queue_arn" {
  type = string
}

variable "rp_fraudInvestigator_en_queue_arn" {
  type = string 
}
variable "rp_fraudInvestigator_fr_queue_arn" {
  type = string
}

variable "rp_elevations_support_en_queue_arn" {
  type = string 
}
variable "rp_elevations_support_fr_queue_arn" {
  type = string
}

variable "rp_elevations_advisor_en_queue_arn" {
  type = string 
}
variable "rp_elevations_advisor_fr_queue_arn" {
  type = string
}

variable "rp_disputeInvestigator_en_v2_queue_arn" {
  type = string 
}
variable "rp_disputeInvestigator_fr_v2_queue_arn" {
  type = string
}

variable "rp_fraudInvestigator_en_v2_queue_arn" {
  type = string 
}
variable "rp_fraudInvestigator_fr_v2_queue_arn" {
  type = string
}
