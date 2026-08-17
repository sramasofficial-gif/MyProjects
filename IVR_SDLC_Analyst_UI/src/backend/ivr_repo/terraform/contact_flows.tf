locals {
  contact_flows = {
/*
    cfAccountStatus = {
      name       = "cfAccountStatus"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfAccountStatus.tftpl"
      variables  = {
        cfQueueConfigContactFlowArn    = var.cfQueueConfigContactFlowArn
        cfErrorHandlingArn             = var.cfErrorHandlingArn
        cfActivateCardArn              = var.cfActivateCardArn
        GetSsmParamsLambdaArn          = var.GetSsmParamsLambdaArn
        AccountMemosLambdaArn          = var.AccountMemosLambdaArn
        GetAccountStatusLambdaArn      = var.GetAccountStatusLambdaArn
        GetAccountSummaryInfoLambdaArn = var.GetAccountSummaryInfoLambdaArn
        moRBAccountLookupNoArn        = var.moRBAccountLookupNoArn
      }
    }
*/
    cfAccountStatus = {
      name       = "cfAccountStatus"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfAccountStatus.tftpl"
      variables  = {
        cfQueueConfigContactFlowArn    = var.cfQueueConfigContactFlowArn
        cfErrorHandlingArn             = var.cfErrorHandlingArn
        cfActivateCardArn              = var.cfActivateCardArn
        GetSsmParamsLambdaArn          = var.GetSsmParamsLambdaArn
        AccountMemosLambdaArn          = var.AccountMemosLambdaArn
        GetAccountStatusLambdaArn      = var.GetAccountStatusLambdaArn
        GetAccountSummaryInfoLambdaArn = var.GetAccountSummaryInfoLambdaArn
        moRBAccountLookupNoArn         = var.moRBAccountLookupNoArn
        dtAgencyCodeConfigArn             = var.dtAgencyCodeConfigArn
      }
    }

    cfLostAndStolen = {
      name       = "cfLostAndStolen"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfLostAndStolen.tftpl"
      variables  = {
        cfQueueConfigContactFlowArn    = var.cfQueueConfigContactFlowArn
        cfErrorHandlingArn             = var.cfErrorHandlingArn
        cfPreMenuArn                   = var.cfPreMenuArn
        cfMainMenuArn                  = var.cfMainMenuArn
        cfAgentUIArn                   = var.cfAgentUIArn 
        TemporaryblockCardLambdaArn    = var.TemporaryblockCardLambdaArn
        GetSsmParamsLambdaArn          = var.GetSsmParamsLambdaArn
        GetAccountStatusLambdaArn      = var.GetAccountStatusLambdaArn
        GetCardDetailsLambdaArn        = var.GetCardDetailsLambdaArn
        moRbPinValidationArn           = var.moRbPinValidationArn
        moRBsendOTCArn                 = var.moRBsendOTCArn
        moRBAccountLookupArn           = var.moRBAccountLookupArn
      }
    }

    cfRewards = {
      name       = "cfRewards"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfRewards.tftpl"
      variables  = {
        GetRewardsPointsLambdaArn     = var.GetRewardsPointsLambdaArn
        GetSsmParamsLambdaArn         = var.GetSsmParamsLambdaArn
        cfQueueConfigContactFlowArn   = var.cfQueueConfigContactFlowArn
        cfMainMenuArn                 = var.cfMainMenuArn
        cfRewardTransactionsFlowArn   = var.cfRewardTransactionsFlowArn
      }
    }

    cfBackOfficeTaskFlow = {
      name       = "cfBackOfficeTaskFlow"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfBackOfficeTaskFlow.tftpl"
      variables  = {
        BackOffice_Task               = var.BackOffice_Task
      }
    }

    cfActivateCard = {
      name       = "cfActivateCard"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfActivateCard.tftpl"
      variables  = {
        GetSsmParamsLambdaArn        = var.GetSsmParamsLambdaArn
        GetPrimaryCardDetailsLambdaArn = var.GetPrimaryCardDetailsLambdaArn
        GetCardDetailsLambdaArn      = var.GetCardDetailsLambdaArn
        ActivateCardLambdaArn        = var.ActivateCardLambdaArn

        cfMainMenuArn                = var.cfMainMenuArn
        cfQueueConfigContactFlowArn  = var.cfQueueConfigContactFlowArn
        cfChangePinNewArn            = var.cfChangePinNewArn
        cfCreditLimitChangeArn       = var.cfCreditLimitChangeArn
        cfAccountSummaryInfoArn      = var.cfAccountSummaryInfoArn
        cfErrorHandlingArn           = var.cfErrorHandlingArn
        moRBsendOTCNoArn             = var.moRBsendOTCNoArn
        moRbPinValidationNoArn       = var.moRbPinValidationNoArn
        moRBSetPINNoArn              = var.moRBSetPINNoArn
        moRbDOBValidationNoArn       = var.moRbDOBValidationNoArn
        moRBvalidatePhoneNumberNoArn = var.moRBvalidatePhoneNumberNoArn
      }
    }

    cfMainMenu = {
      name       = "cfMainMenu"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfMainMenu.tftpl"
      variables  = {
        GetSsmParamsLambdaArn        = var.GetSsmParamsLambdaArn

        cfMainMenuSMBArn             = var.cfMainMenuSMBArn
        cfQueueConfigContactFlowArn  = var.cfQueueConfigContactFlowArn
        cfLostAndStolenArn           = var.cfLostAndStolenArn
        cfCreditLimitChangeArn       = var.cfCreditLimitChangeArn
        cfAccountSummaryInfoArn      = var.cfAccountSummaryInfoArn
        CfTransactionArn             = var.CfTransactionArn
        cfActivateCardArn            = var.cfActivateCardArn
        cfMainMenuCorporateArn       = var.cfMainMenuCorporateArn
        cfRewardsArn                 = var.cfRewardsArn
        cfActivateCardArn            = var.cfActivateCardArn
      }
    }

    cfQueuesWithVoiceMail = {
      name       = "cfQueuesWithVoiceMail"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfQueuesWithVoiceMail.tftpl"
      variables  = {
        GetSsmParamsLambdaArn           = var.GetSsmParamsLambdaArn

        cfVoiceMailCustomerWhisperArn   = var.cfVoiceMailCustomerWhisperArn
        cfVoiceMailCustomerQueueArn     = var.cfVoiceMailCustomerQueueArn
        moVoiceMailNoArn                = var.moVoiceMailNoArn
        moGetQueueRoutingDataNoArn      = var.moGetQueueRoutingDataNoArn
        moSelectQueueNoArn              = var.moSelectQueueNoArn
        cfAgentWhisperQCArn             = var.cfAgentWhisperQCArn
        dtGlobalSetNoArn                = var.dtGlobalSetNoArn
        BeepArn                         = var.BeepArn
      }
    }

    cfEnqueueCallback = {
      name       = "cfEnqueueCallback"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfEnqueueCallback.tftpl"
      variables  = {
        dtQueuesMetricsNoArn            = var.dtQueuesMetricsNoArn
        dtGlobalSetNoArn                = var.dtGlobalSetNoArn
        GS_HOOP_Arn                     = var.GS_HOOP_Arn
      }
    }

    cfChangePinNew = {
      name       = "cfChangePinNew"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfChangePinNew.tftpl"
      variables  = {
        cfQueueConfigContactFlowArn     = var.cfQueueConfigContactFlowArn
        moRBAccountLookupNoArn          = var.moRBAccountLookupNoArn
        moRbDOBValidationNoArn          = var.moRbDOBValidationNoArn
        cfPreMenuArn                    = var.cfPreMenuArn
        cfAgentUIArn                    = var.cfAgentUIArn
        moRBvalidatePhoneNumberNoArn    = var.moRBvalidatePhoneNumberNoArn
        moRBsendOTCNoArn                = var.moRBsendOTCNoArn
        cfErrorHandlingArn              = var.cfErrorHandlingArn
        moRBSetPINNoArn                 = var.moRBSetPINNoArn
      }
    }

    cfCallback = {
      name       = "cfCallback"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfCallback.tftpl"
      variables  = {
        cfEnqueueCallbackArn            = var.cfEnqueueCallbackArn
        cfAgentWhisperCallbackArn       = var.cfAgentWhisperCallbackArn
        BeepArn                         = var.BeepArn
        AgentDetailsLambdaArn           = var.AgentDetailsLambdaArn
        dtGlobalSetNoArn                = var.dtGlobalSetNoArn
        dtQueuesMetricsNoArn            = var.dtQueuesMetricsNoArn
      }
    }

    cfVoiceMailRouting = {
      name       = "cfVoiceMailRouting"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfVoiceMailRouting.tftpl"
      variables  = {
        cfVoiceMailCQArn                = var.cfVoiceMailCQArn
        cfVoicemailAgentWhisperArn      = var.cfVoicemailAgentWhisperArn
      }
    }
    
    cfOutboundWhisper = {
      name       = "cfOutboundWhisper"
      type       = "OUTBOUND_WHISPER"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfOutboundWhisper.tftpl"
      variables  = {
        SecureCallLambdaArn        = var.SecureCallLambdaArn
      }
    }

    cfAgentWhisperQC = {
      name       = "cfAgentWhisperQC"
      type       = "AGENT_WHISPER"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfAgentWhisperQC.tftpl"
      variables  = {}
    }

    cfAgentWhisper = {
      name       = "cfAgentWhisper"
      type       = "AGENT_WHISPER"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfAgentWhisper.tftpl"
      variables  = {
        AgentDetailsLambdaArn       = var.AgentDetailsLambdaArn
        CreateInteractionLambdaArn  = var.CreateInteractionLambdaArn
      }
    }
    
    cfDefaultQueueTransfer = {
      name       = "cfDefaultQueueTransfer"
      type       = "QUEUE_TRANSFER"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfDefaultQueueTransfer.tftpl"
      variables  = {
        cfDefaultQueueTransferExtArn       = var.cfDefaultQueueTransferExtArn
      }
    }

    cfInboundEmailFlow = {
      name       = "cfInboundEmailFlow"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfInboundEmailFlow.tftpl"
      variables  = {
        BackOffice_EN       = var.rp_backoffice_en_queue_arn
        cfCustomerQueueArn  = var.cfCustomerQueueArn
        cfAgentWhisperQCArn = var.cfAgentWhisperQCArn
      }
    }

    cfDefaultQueueTransferExt = {
      name       = "cfDefaultQueueTransferExt"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfDefaultQueueTransferExt.tftpl"
      variables  = {
        cfAgentWhisperQCArn       = var.cfAgentWhisperQCArn
        cfCustomerQueueQCArn      = var.cfCustomerQueueQCArn
        GetHolidayParamsLambdaArn = var.GetHolidayParamsLambdaArn
        GetSsmParamsLambdaArn     = var.GetSsmParamsLambdaArn
        moSelectQueueNoArn        = var.moSelectQueueNoArn
        dtGlobalSetNoArn          = var.dtGlobalSetNoArn
        cfCustomerQueueArn        = var.cfCustomerQueueArn
        dtQueuesMetricsNoArn      = var.dtQueuesMetricsNoArn
      }
    }

    cfProductSwitchQC_EN = {
      name       = "cfProductSwitchQC_EN"
      type       = "QUEUE_TRANSFER"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfProductSwitchQC_EN.tftpl"
      variables  = {}
    }

    cfProductSwitchQC_Fr = {
      name       = "cfProductSwitchQC_Fr"
      type       = "QUEUE_TRANSFER"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfProductSwitchQC_Fr.tftpl"
      variables  = {}
    }

    cfCustomerQueue = {
      name       = "cfCustomerQueue"
      type       = "CUSTOMER_QUEUE"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfCustomerQueue.tftpl"
      variables  = {
        CustomerqueuenewArn     = var.CustomerqueuenewArn
        GS_HOOP_Arn             = var.GS_HOOP_Arn
        dtGlobalSetNoArn          = var.dtGlobalSetNoArn
        dtQueuesMetricsNoArn    = var.dtQueuesMetricsNoArn
      }
    }

    cfVoicemailModule = {
      name       = "cfVoicemailModule"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfVoicemailModule.tftpl"
      variables  = {
        BeepArn = var.BeepArn
        dtVoiceMailDestinationNoArn = var.dtVoiceMailDestinationNoArn
      }
    }

    cfElevationsTaskFlow = {
      name       = "cfElevationsTaskFlow"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfElevationsTaskFlow.tftpl"
      variables  = {
        Elevations_Advisor_EN = var.rp_elevations_support_en_queue_arn
        Elevations_Advisor_FR = var.rp_elevations_support_fr_queue_arn
      }
    }

    cfFraudInvestigatorQuickConnect = {
      name       = "cfFraudInvestigatorQuickConnect"
      type       = "QUEUE_TRANSFER"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfFraudInvestigatorQuickConnect.tftpl"
      variables  = {
        GetHolidayParamsLambdaArn = var.GetHolidayParamsLambdaArn
        cfAgentWhisperQCArn       = var.cfAgentWhisperQCArn
        GetSsmParamsLambdaArn     = var.GetSsmParamsLambdaArn
        BeepArn                      = var.BeepArn
        cfCustomerQueueQCArn      = var.cfCustomerQueueQCArn
        cfVoicemailModuleArn      = var.cfVoicemailModuleArn
        cfQueuesWithVoiceMailArn  = var.cfQueuesWithVoiceMailArn
        dtQueuesMetricsNoArn      = var.dtQueuesMetricsNoArn
        dtGlobalSetNoArn          = var.dtGlobalSetNoArn
      }
    }
    cfPreMenu = {
      name       = "cfPreMenu"
      type       = "CONTACT_FLOW"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/cfPreMenu.tftpl"
      variables  = {
        AgentDetailsLambdaArn      = var.AgentDetailsLambdaArn
        cfAccountStatusArn         = var.cfAccountStatusArn
        cfChangePinNewArn          = var.cfChangePinNewArn
        cfLostAndStolenArn         = var.cfLostAndStolenArn
        GetSsmParamsLambdaArn      = var.GetSsmParamsLambdaArn
        cfQueueConfigContactFlowArn = var.cfQueueConfigContactFlowArn
        cfAgentUIArn               = var.cfAgentUIArn
      }
    }
  }

  contact_flow_modules = {
    moRbPinValidation = {
      name       = "moRbPinValidation"
      type       = "CONTACT_FLOW_MODULE"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/moRbPinValidation.tftpl"
      variables  = {
        KeyId                          = var.KeyId
        EncryptionKey                  = jsonencode(var.EncryptionKey)
        AccountMemosLambdaArn          = var.AccountMemosLambdaArn
        VerifyPinLambdaArn             = var.VerifyPinLambdaArn
      }
    }

    moRBSetPIN = {
      name       = "moRBSetPIN"
      type       = "CONTACT_FLOW_MODULE"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/moRBSetPIN.tftpl"
      variables  = {
        KeyId                          = var.KeyId
        EncryptionKey                  = jsonencode(var.EncryptionKey)
        AccountMemosLambdaArn          = var.AccountMemosLambdaArn
        VerifyPinLambdaArn             = var.VerifyPinLambdaArn
        changepinLambdaArn             = var.changepinLambdaArn
        GetSsmParamsLambdaArn          = var.GetSsmParamsLambdaArn
      }
    }

    moRbDOBValidation = {
      name       = "moRbDOBValidation"
      type       = "CONTACT_FLOW_MODULE"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/moRbDOBValidation.tftpl"
      variables  = {
        GetSsmParamsLambdaArn          = var.GetSsmParamsLambdaArn
        GetDOBLambdaArn                = var.GetDOBLambdaArn
        validateDOBLambdaArn           = var.validateDOBLambdaArn
      }
    }

    moVoiceMail = {
      name       = "moVoiceMail"
      type       = "CONTACT_FLOW_MODULE"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/moVoiceMail.tftpl"
      variables  = {
        BeepArn = var.BeepArn
      }
    }

     moRBvalidatePhoneNumber = {
      name       = "moRBvalidatePhoneNumber"
      type       = "CONTACT_FLOW_MODULE"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/moRBvalidatePhoneNumber.tftpl"
      variables  = {
        ValidatePhoneNumberLambdaARN = var.ValidatePhoneNumberLambdaARN
        
      }
    }

    moSelectQueue = {
      name       = "moSelectQueue"
      type       = "CONTACT_FLOW_MODULE"
      tftpl_file = "${path.module}/exports/contact-flows-tftpl/moSelectQueue.tftpl"
      variables  = {
        dtQueuesMetricsNoArn      = var.dtQueuesMetricsNoArn
        SelectQueueLogicLambdaArn = var.SelectQueueLogicLambdaArn
        dtGlobalSetNoArn          = var.dtGlobalSetNoArn
        GS_HOOP_Arn               = var.GS_HOOP_Arn                   
      }
    }
  }
}

resource "aws_connect_contact_flow" "flows" {
  for_each      = local.contact_flows
  instance_id   = aws_connect_instance.saml_instance.id
  name          = each.value.name
  type          = each.value.type

  content       = templatefile(each.value.tftpl_file, each.value.variables)
  content_hash  = filebase64sha256(each.value.tftpl_file)

  tags = {
    Environment = "dev"
  }
}

resource "aws_connect_contact_flow_module" "modules" {
  for_each     = local.contact_flow_modules
  instance_id  = aws_connect_instance.saml_instance.id
  name         = each.value.name
  description  = "Provisioned via Terraform"
 
  content      = templatefile(each.value.tftpl_file, each.value.variables)
  content_hash = filebase64sha256(each.value.tftpl_file)
 
  tags = {
    Environment = "dev"
  }
}

/*
resource "aws_connect_contact_flow" "account_status_flow" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfAccountStatus"
  type        = "CONTACT_FLOW"

  # Render the template with ARN values
  content = templatefile("${path.module}/exports/contact-flows-tftpl/cfAccountStatus.tftpl", {
    GetSsmParamsLambdaArn          = var.GetSsmParamsLambdaArn
    AccountMemosLambdaArn          = var.AccountMemosLambdaArn
    GetAccountStatusLambdaArn      = var.GetAccountStatusLambdaArn
    GetAccountSummaryInfoLambdaArn = var.GetAccountSummaryInfoLambdaArn
    cfQueueConfigContactFlowArn    = var.cfQueueConfigContactFlowArn
    cfErrorHandlingArn             = var.cfErrorHandlingArn
    cfActivateCardArn              = var.cfActivateCardArn
  })

  description = "Account Status contact flow deployment"
}
*/
