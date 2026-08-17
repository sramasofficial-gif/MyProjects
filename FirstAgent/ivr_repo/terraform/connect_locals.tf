/*
Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties dated 2024.
*/

locals {
  region_shortnames = {
    us-east-1 = "use1"
    us-west-2 = "usw2"
    ca-central-1 = "cac1"
  }
 

  ssm_prefix              = "/${var.env}/${local.region_shortnames[var.region]}"

  #file_names = { for name, file in data.local_file.files : trimsuffix(name, ".json") => file.content }
  file_names              = [  for name, file in data.local_file.files : trimsuffix(name, ".json") ]
  hoop_id                 = { for name in local.file_names : name => name }
  lambda_md5              = filemd5("${path.module}/scripts/replacer/src/index.ts")

  operating_hours_files   = fileset(var.operating_hours_dir, "*.json")
  queues_files            = fileset(var.queues_dir, "*.json")
  quick_connect_files     = fileset(var.quick_connect_dir, "*.json")
  routing_profiles_files  = fileset(var.routing_profiles_dir, "*.json")
  
  decode_operating_hours  = {for file in local.operating_hours_files : trimsuffix(file, ".json") => jsondecode(file("${var.operating_hours_dir}/${file}"))}
  decode_queues           = {for file in local.queues_files : file => jsondecode(file("${var.queues_dir}/${file}"))}
  decode_quick_connect    = {for file in local.quick_connect_files : file => jsondecode(file("${var.quick_connect_dir}/${file}"))}
  decode_routing_profiles = {for file in local.routing_profiles_files : file => jsondecode(file("${var.routing_profiles_dir}/${file}"))}

  # Extract unique HoursOfOperationId from queue files
  hours_of_operation_ids = distinct(flatten([for file, queues in local.decode_queues : queues.HoursOfOperationId]))


  # Extract unique OutboundCallerIdNumberId, OutboundFlowId from the queue file
  //outbound_caller_id_number_ids = distinct(flatten([for file, queues in local.decode_queues : queues.OutboundCallerConfig.OutboundCallerIdNumberId]))
 // outbound_flow_ids = distinct(flatten([for file, queues in local.decode_queues : queues.OutboundCallerConfig.OutboundFlowId]))
  default_hours_of_operation_id = split(":",data.aws_connect_hours_of_operation.basic_hours.id)[1]

  queue_hoop_map = {
    "Basic Hours" = "9ebd6db3-c51f-4cfe-b103-6202496d47c0"
    "M-F 8To5" = "5ab117b0-c2ec-45ef-8181-44a856b98a1a"
    "Open7Days - 8To12" = "50613e65-bb08-4a82-a9bb-c48b166201ba"
  }

#  outbound_flow_map = {
#    "cfoutboundwhisper" = data.aws_connect_contact_flow.cfOutboundWhispher.id
#    "default_outbound"  = data.aws_connect_contact_flow.basic_outbound.id
#  }


  outbound_flow_map = {
    "cfoutboundwhisper" = data.aws_connect_contact_flow.cfOutboundWhispher.id
    "default_outbound"  = data.aws_connect_contact_flow.basic_outbound.id
  }


  outbound_caller_id_number_map = {
  "+18335742320" = "047b6b10-1216-4eef-9809-d8344239f4fb"
  "+18333626006" = "18710e68-48e3-4ec4-a35f-002f37897203"
  "+18332947095" = "1d4f71e0-00d2-4f59-8dac-46e15e08dd45"
  "+18335743288" = "4f263ce9-be2a-4540-b2fb-c6edd2ad283a"
  "+18334856680" = "5d0fb8c7-a4a3-41be-8ac5-395cb0759033"
  "+18332947094" = "b390f7a6-91db-484a-86da-9a4e4617d536"
  "+18333620790" = "b6048358-cbb4-4ca2-ba34-3afd551a30d5"
  "+18335742324" = "dde291a4-1a2d-422d-a9d2-5f8f7c9b38cb"
  "+18333623288" = "f1a8f309-e746-41f7-824c-11d437b0e0a9"
  "+18665102270" = "f76540ca-d253-428d-9ade-40f80c011f98"
  }


  qc_flows_map = {
   "cfDefaultQueueTransfer" = split(":",data.aws_connect_contact_flow.cfDefaultQueueTransfer.id)[1]
    #"cfLegalDisclaimer"      = split(":",data.aws_connect_contact_flow.cfLegalDisclaimer.id)[1]
    "cfBalTransferQC_EN"  = split(":",data.aws_connect_contact_flow.cfBalTransferQC_EN.id)[1]
    "cfProductSwitchQC_EN"  = split(":",data.aws_connect_contact_flow.cfProductSwitchQC_EN.id)[1]
    #"cfProductSwitchQC_EN"  = split(":",data.aws_connect_contact_flow.cfDefaultQueueTransfer.id)[1]
    "cfProductSwitchQC_Fr"  = split(":",data.aws_connect_contact_flow.cfProductSwitchQC_Fr.id)[1]
    #"cfProductSwitchQC_Fr"  = split(":",data.aws_connect_contact_flow.cfDefaultQueueTransfer.id)[1]
    "cfInCallPinValidation_En"  = split(":",data.aws_connect_contact_flow.cfInCallPinValidation_En.id)[1]
    "cfInCallPinValidation_Fr"  = split(":",data.aws_connect_contact_flow.cfInCallPinValidation_Fr.id)[1] 
    "cfInCallStepUpAuthentication_EN"  = split(":",data.aws_connect_contact_flow.cfInCallStepUpAuthentication_EN.id)[1]
    "cfInCallStepUpAuthentication_FR"  = split(":",data.aws_connect_contact_flow.cfInCallStepUpAuthentication_FR.id)[1]
    "cfrogersPinChangeQuickConnect"  = split(":",data.aws_connect_contact_flow.cfrogersPinChangeQuickConnect.id)[1]
    "cfFraudInvestigatorQuickConnect"  = split(":",data.aws_connect_contact_flow.cfFraudInvestigatorQuickConnect.id)[1]
}

###################################################AWSCC Email config enabled Queues  #######################################################3
/*
awscc_queues = {
    BackOffice_EN = {
      name        = "BackOffice_EN"
      description = "BackOffice_EN"
      status      = "ENABLED"

      hours_of_operation_arn = var.MF8to5Arn

      outbound_caller_id_name       = "Rogers Bank"
      outbound_caller_id_number_arn = var.outbound_caller_id_number_arn
      outbound_flow_arn             = var.cfOutboundWhisperArn

      email_address              = "customerservice@rogersbank.com"
      email_outbound_flow_arn    = var.cfOutboundWhisperArn
      additional_email_addresses = [
        "Inbound Email <dispute@rb-pci-dev-connect.email.connect.aws>"
      ]

      #quick_connect_arns = []
      tags = [
        {
          key   = "vendor"
          value = "concentrix"
        }
      ]
    }

    BackOffice_FR = {
      name        = "BackOffice_FR"
      description = "BackOffice_FR"
      status      = "ENABLED"

      hours_of_operation_arn = var.MF8to5Arn

      outbound_caller_id_name       = "Rogers Bank"
      outbound_caller_id_number_arn = var.outbound_caller_id_number_arn
      outbound_flow_arn             = var.cfOutboundWhisperArn

      email_address              = "customerservice@rogersbank.com"
      email_outbound_flow_arn    = var.cfOutboundWhisperArn
      additional_email_addresses = [
        "Inbound Email <dispute@rb-pci-dev-connect.email.connect.aws>"
      ]

      #quick_connect_arns = []
      tags = [
        {
          key   = "vendor"
          value = "concentrix"
        }
      ]
    }
  }
*/
 ########################################################### AWSCC Routing Profiles ##########################################################################
   
awscc_routing_profiles = {
    p_rogersbank_backoffice_awscc_en = {
      name        = "P_RogersBank_BackOffice_EN"
      description = "P_RogersBank_BackOffice_EN"

      default_outbound_queue_arn = var.rp_backoffice_en_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 },
        { channel = "EMAIL", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_backoffice_en_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_manual_assignment_backoffice_task_queue_arn
          }
        },
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_backoffice_en_queue_arn
          }
        },
        {
          queue_reference = {
            channel   = "EMAIL"
            queue_arn = var.rp_backoffice_en_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_backoffice_awscc_fr = {
      name        = "P_RogersBank_BackOffice_FR"
      description = "P_RogersBank_BackOffice_FR"

      default_outbound_queue_arn = var.rp_backoffice_fr_queue_arn


     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 },
        { channel = "EMAIL", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_backoffice_en_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_backoffice_fr_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_manual_assignment_backoffice_task_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_backoffice_en_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_backoffice_fr_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "EMAIL"
          queue_arn = var.rp_backoffice_en_queue_arn 
      } 
    },
    {
      queue_reference = {
          channel   = "EMAIL"
          queue_arn = var.rp_backoffice_fr_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   

   p_rogersbank_disputeInvestigator_awscc_en = {
      name        = "P_RogersBank_DisputeInvestigator_EN"
      description = "P_RogersBank_DisputeInvestigator_EN"

      default_outbound_queue_arn = var.rp_disputeInvestigator_en_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_disputeInvestigator_en_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_disputeInvestigator_en_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_disputeInvestigator_awscc_fr = {
      name        = "P_RogersBank_DisputeInvestigator_FR"
      description = "P_RogersBank_DisputeInvestigator_FR"

      default_outbound_queue_arn = var.rp_disputeInvestigator_fr_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_disputeInvestigator_en_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_disputeInvestigator_fr_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_disputeInvestigator_en_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_disputeInvestigator_fr_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
    ]    
   },


   p_rogersbank_complaints_awscc_en = {
      name        = "P_RogersBank_Complaints_EN"
      description = "P_RogersBank_Complaints_EN"

      default_outbound_queue_arn = var.rp_complaints_en_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_complaints_en_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_complaints_en_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_complaints_awscc_fr = {
      name        = "P_RogersBank_Complaints_FR"
      description = "P_RogersBank_Complaints_FR"

      default_outbound_queue_arn = var.rp_complaints_fr_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_complaints_en_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_complaints_fr_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_complaints_en_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_complaints_fr_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
    ]    
   },


   p_rogersbank_fraudInvestigator_awscc_en = {
      name        = "P_RogersBank_FraudInvestigator_EN"
      description = "P_RogersBank_FraudInvestigator_EN"

      default_outbound_queue_arn = var.rp_fraudInvestigator_en_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_fraudInvestigator_en_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_fraudInvestigator_en_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_fraudInvestigator_awscc_fr = {
      name        = "P_RogersBank_FraudInvestigator_FR"
      description = "P_RogersBank_FraudInvestigator_FR"

      default_outbound_queue_arn = var.rp_fraudInvestigator_fr_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_fraudInvestigator_en_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_fraudInvestigator_fr_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_fraudInvestigator_en_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_fraudInvestigator_fr_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
    ]    
   },


   p_rogersbank_elevations_support_awscc_en = {
      name        = "P_RogersBank_Elevations_Support_EN"
      description = "P_RogersBank_Elevations_Support_EN"

      default_outbound_queue_arn = var.rp_elevations_support_en_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_elevations_support_en_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_elevations_support_en_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_elevations_support_awscc_fr = {
      name        = "P_RogersBank_Elevations_Support_FR"
      description = "P_RogersBank_Elevations_Support_FR"

      default_outbound_queue_arn = var.rp_elevations_support_fr_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_elevations_support_en_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_elevations_support_fr_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_elevations_support_en_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_elevations_support_fr_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
    ]    
   },


   p_rogersbank_elevations_advisor_awscc_en = {
      name        = "P_RogersBank_Elevations_Advisor_EN"
      description = "P_RogersBank_Elevations_Advisor_EN"

      default_outbound_queue_arn = var.rp_elevations_advisor_en_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_elevations_advisor_en_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_elevations_advisor_en_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_elevations_advisor_awscc_fr = {
      name        = "P_RogersBank_Elevations_Advisor_FR"
      description = "P_RogersBank_Elevations_Advisor_FR"

      default_outbound_queue_arn = var.rp_elevations_advisor_fr_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_elevations_advisor_en_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_elevations_advisor_fr_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_elevations_advisor_en_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_elevations_advisor_fr_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor"
        value = "concentrix"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
    ]    
   },


   p_rogersbank_disputeInvestigator_awscc_en_v2 = {
      name        = "P_RogersBank_DisputeInvestigator_EN_V2"
      description = "P_RogersBank_DisputeInvestigator_EN_V2"

      default_outbound_queue_arn = var.rp_disputeInvestigator_en_v2_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_disputeInvestigator_en_v2_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_disputeInvestigator_en_v2_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor2"
        value = "gatestone"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_disputeInvestigator_awscc_fr_v2 = {
      name        = "P_RogersBank_DisputeInvestigator_FR_V2"
      description = "P_RogersBank_DisputeInvestigator_FR_V2"

      default_outbound_queue_arn = var.rp_disputeInvestigator_fr_v2_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_disputeInvestigator_en_v2_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_disputeInvestigator_fr_v2_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_disputeInvestigator_en_v2_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_disputeInvestigator_fr_v2_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor2"
        value = "gatestone"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
    ]    
   },


   p_rogersbank_fraudInvestigator_awscc_en_v2 = {
      name        = "P_RogersBank_FraudInvestigator_EN_V2"
      description = "P_RogersBank_FraudInvestigator_EN_V2"

      default_outbound_queue_arn = var.rp_fraudInvestigator_en_v2_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
        {
          delay    = 0
          priority = 4
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_fraudInvestigator_en_v2_queue_arn
          }
        },
        {
          delay    = 0
          priority = 9
          queue_reference = {
            channel   = "VOICE"
            queue_arn = var.rp_quickconnectsonly_queue_arn
          }
        }
      ]

      manual_assignment_queue_configs = [
        {
          queue_reference = {
            channel   = "TASK"
            queue_arn = var.rp_fraudInvestigator_en_v2_queue_arn
          }
        }
      ]
    tags = [{
        key   = "vendor2"
        value = "gatestone"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
   ]    
   },
   p_rogersbank_fraudInvestigator_awscc_fr_v2 = {
      name        = "P_RogersBank_FraudInvestigator_FR_V2"
      description = "P_RogersBank_FraudInvestigator_FR_V2"

      default_outbound_queue_arn = var.rp_fraudInvestigator_fr_v2_queue_arn

     media_concurrencies = [      
        { channel = "TASK",  concurrency = 1 },
        { channel = "VOICE", concurrency = 1 }
      ]

      queue_configs = [
    
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_fraudInvestigator_en_v2_queue_arn
      }
    },
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_fraudInvestigator_fr_v2_queue_arn
      }
    },
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_quickconnectsonly_queue_arn
      }
    }
  ]
   manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_fraudInvestigator_en_v2_queue_arn 
      }
    },
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_fraudInvestigator_fr_v2_queue_arn 
      }
    }
  ]
    tags = [{
        key   = "vendor2"
        value = "gatestone"
     },
     {
        key = "applicationname"
        value = "RB-PCI-RBCONNECT"
     }    
    ]    
   }
 }


############################################################End of AWSCC Routing Profiles ###################################################################
  security_profiles_without_hierarchy = {
    for k, v in local.security_profiles : k => v
     #if !contains(keys(v), "allowed_access_control_hierarchy_group_id") || v.allowed_access_control_hierarchy_group_id == ""
    if v.has_hierarchy == false
    }

  security_profiles_with_hierarchy = {
    for k, v in local.security_profiles : k => v
    if v.has_hierarchy == true
  }


  # Security profiles
 security_profiles = {
  "ITadmin" = {
    "permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentGrouping.Create",
        "AgentGrouping.Edit",
        "AgentGrouping.EnableAndDisable",
        "AgentGrouping.View",
        "AgentStates.Create",
        "AgentStates.Edit",
        "AgentStates.EnableAndDisable",
        "AgentStates.View",
        "AgentTimeCard.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "Bots.Create",
        "Bots.Edit",
        "Bots.View",
        "Campaigns.Create",
        "Campaigns.Delete",
        "Campaigns.Edit",
        "Campaigns.Manage",
        "Campaigns.View",
        "Capacity.Edit",
        "Capacity.Publish",
        "Capacity.View",
        "CaseFields.Create",
        "CaseFields.Edit",
        "CaseFields.View",
        "CaseHistory.View",
        "CaseTemplates.Create",
        "CaseTemplates.Edit",
        "CaseTemplates.View",
        "Cases.Create",
        "Cases.Edit",
        "Cases.View",
        "ChatTestMode",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactFlowModules.Create",
        "ContactFlowModules.Delete",
        "ContactFlowModules.Edit",
        "ContactFlowModules.Publish",
        "ContactFlowModules.View",
        "ContactFlows.Create",
        "ContactFlows.Delete",
        "ContactFlows.Edit",
        "ContactFlows.Publish",
        "ContactFlows.View",
        "ContactLensCustomVocabulary.Edit",
        "ContactLensCustomVocabulary.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "ContentManagement.Create",
        "ContentManagement.Delete",
        "ContentManagement.Edit",
        "ContentManagement.MessageTemplates.Create",
        "ContentManagement.MessageTemplates.Delete",
        "ContentManagement.MessageTemplates.Edit",
        "ContentManagement.MessageTemplates.View",
        "ContentManagement.View",
        "CustomViews.Access",
        "CustomerProfiles.CalculatedAttributes.Create",
        "CustomerProfiles.CalculatedAttributes.Delete",
        "CustomerProfiles.CalculatedAttributes.Edit",
        "CustomerProfiles.CalculatedAttributes.View",
        "CustomerProfiles.Create",
        "CustomerProfiles.Edit",
        "CustomerProfiles.Segments.Create",
        "CustomerProfiles.Segments.Delete",
        "CustomerProfiles.Segments.Export",
        "CustomerProfiles.Segments.View",
        "CustomerProfiles.View",
        "DownloadCallRecordings",
        "EmailAddresses.Create",
        "EmailAddresses.Edit",
        "EmailAddresses.Remove",
        "EmailAddresses.View",
        "Evaluation.Create",
        "Evaluation.Delete",
        "Evaluation.Edit",
        "Evaluation.View",
        "EvaluationAssistant.Access",
        "EvaluationCalibrationSessions.Create",
        "EvaluationCalibrationSessions.Delete",
        "EvaluationCalibrationSessions.Edit",
        "EvaluationCalibrationSessions.View",
        "EvaluationForms.Create",
        "EvaluationForms.Delete",
        "EvaluationForms.Edit",
        "EvaluationForms.View",
        "ForecastScheduleInterval.Edit",
        "ForecastScheduleInterval.View",
        "Forecasting.Edit",
        "Forecasting.Publish",
        "Forecasting.View",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "HoursOfOperation.Create",
        "HoursOfOperation.Delete",
        "HoursOfOperation.Edit",
        "HoursOfOperation.View",
        "ListenCallRecordings",
        "ManagerBargeIn",
        "ManagerListenIn",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "OutboundEmail.Create",
        "PhoneNumbers.Claim",
        "PhoneNumbers.Edit",
        "PhoneNumbers.Release",
        "PhoneNumbers.View",
        "PredefinedAttributes.Create",
        "PredefinedAttributes.Delete",
        "PredefinedAttributes.Edit",
        "PredefinedAttributes.View",
        "Prompts.Create",
        "Prompts.Delete",
        "Prompts.Edit",
        "Prompts.View",
        "Queues.Create",
        "Queues.Edit",
        "Queues.EnableAndDisable",
        "Queues.View",
        "RealtimeContactLens.View",
        "RedactedData.View",
        "ReportsAdmin.Access",
        "ReportsAdmin.Delete",
        "ReportsAdmin.Publish",
        "ReportsAdmin.Schedule",
        "ReportsAdmin.View",
        "RestrictTaskCreation.Access",
        "RoutingPolicies.Create",
        "RoutingPolicies.Edit",
        "RoutingPolicies.View",
        "Rules.Create",
        "Rules.Delete",
        "Rules.Edit",
        "Rules.View",
        "RulesGenerativeAI.Create",
        "RulesGenerativeAI.Delete",
        "RulesGenerativeAI.Edit",
        "RulesGenerativeAI.View",
        "Scheduling.Edit",
        "Scheduling.Publish",
        "Scheduling.View",
        "ScreenRecording.Access",
        "ScreenRecording.Download",
        "SecurityProfiles.Create",
        "SecurityProfiles.Delete",
        "SecurityProfiles.Edit",
        "SecurityProfiles.View",
        "SelfAssignContacts.Access",
        "StaffCalendar.Edit",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TaskTemplates.Create",
        "TaskTemplates.Delete",
        "TaskTemplates.Edit",
        "TaskTemplates.View",
        "TeamCalendar.Edit",
        "TeamCalendar.View",
        "ThemeDetection.Create",
        "ThemeDetection.Delete",
        "ThemeDetection.View",
        "TimeOff.Approve",
        "TimeOff.Edit",
        "TimeOff.View",
        "TimeOffBalance.Edit",
        "TimeOffBalance.View",
        "TransferContact.Enabled",
        "TransferDestinations.Create",
        "TransferDestinations.Delete",
        "TransferDestinations.Edit",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.Create",
        "Users.Delete",
        "Users.Edit",
        "Users.EditPermission",
        "Users.View",
        "VideoContact.Access",
        "Views.Create",
        "Views.Edit",
        "Views.Remove",
        "Views.View",
        "VoiceId.Access",
        "VoiceIdAttributesAndSearch.View",
        "Wisdom.View",
        "CallRecordings.Redacted.Access",
        "CallRecordings.Unredacted.Access",
        "CallRecordings.Unredacted.DownloadButton",
        "ContactTranscripts.Redacted.Access"
    ],
      "description"  = "An administrator can perform all actions available.",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"DevSupportProfile"={
    "permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentGrouping.View",
        "AgentStates.View",
        "AgentTimeCard.View",
        "Analytics.PerformanceMetrics.Access",
        "AudioDeviceSettings.Access",
        "BasicAgentAccess",
        "ContactAttributes.View",
        "ContactFlowModules.View",
        "ContactFlows.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "CustomViews.Access",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "HoursOfOperation.View",
        "ListenCallRecordings",
        "ManagerListenIn",
        "MetricsReports.View",
        "OutboundCallAccess",
        "PhoneNumbers.View",
        "Queues.View",
        "DataTables.View",
        "RealtimeContactLens.View",
        "RedactedData.View",
        "RoutingPolicies.View",
        "ScreenRecording.Access",
        "SecurityProfiles.View",
        "StopContact.Enabled",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "Users.View",
        "Views.View",
        "ForecastScheduleInterval.View",
        "Forecasting.View",
        "GraphTrends.View"
    ],
      "description"  = "Read only and view access",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"Rbconnectdeveloperaccess"={
    "permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentGrouping.View",
        "AgentStates.View",
        "AgentTimeCard.View",
        "Analytics.PerformanceMetrics.Access",
        "AudioDeviceSettings.Access",
        "BasicAgentAccess",
        "ContactAttributes.View",
        "ContactFlowModules.View",
        "ContactFlows.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "CustomViews.Access",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "HoursOfOperation.View",
        "ListenCallRecordings",
        "MetricsReports.View",
        "OutboundCallAccess",
        "PhoneNumbers.View",
        "Queues.View",
        "RealtimeContactLens.View",
        "RedactedData.View",
        "RoutingPolicies.View",
        "ScreenRecording.Access",
        "SecurityProfiles.View",
        "StopContact.Enabled",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "Users.View",
        "Views.View",
        "ForecastScheduleInterval.View",
        "Forecasting.View",
        "GraphTrends.View"
    ],
      "description"  = "Read only and view access",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"CCAdmin" = {
    "permissions" =  [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentGrouping.Create",
        "AgentGrouping.Edit",
        "AgentGrouping.EnableAndDisable",
        "AgentGrouping.View",
        "AgentStates.Create",
        "AgentStates.Edit",
        "AgentStates.EnableAndDisable",
        "AgentStates.View",
        "AgentTimeCard.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.DownloadButton",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "Bots.Create",
        "Bots.Edit",
        "Bots.View",
        "Campaigns.Create",
        "Campaigns.Delete",
        "Campaigns.Edit",
        "Campaigns.Manage",
        "Campaigns.View",
        "Capacity.Edit",
        "Capacity.View",
        "CaseFields.Create",
        "CaseFields.Edit",
        "CaseFields.View",
        "CaseHistory.View",
        "CaseTemplates.Create",
        "CaseTemplates.Edit",
        "CaseTemplates.View",
        "Cases.Create",
        "Cases.Edit",
        "Cases.View",
        "ChatTestMode",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactFlowModules.Create",
        "ContactFlowModules.Delete",
        "ContactFlowModules.Edit",
        "ContactFlowModules.Publish",
        "ContactFlowModules.View",
        "ContactFlows.Create",
        "ContactFlows.Delete",
        "ContactFlows.Edit",
        "ContactFlows.Publish",
        "ContactFlows.View",
        "ContactLensCustomVocabulary.Edit",
        "ContactLensCustomVocabulary.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "ContentManagement.Create",
        "ContentManagement.Delete",
        "ContentManagement.Edit",
        "ContentManagement.MessageTemplates.Create",
        "ContentManagement.MessageTemplates.Delete",
        "ContentManagement.MessageTemplates.Edit",
        "ContentManagement.MessageTemplates.View",
        "ContentManagement.View",
        "CustomViews.Access",
        "CustomerProfiles.CalculatedAttributes.Create",
        "CustomerProfiles.CalculatedAttributes.Delete",
        "CustomerProfiles.CalculatedAttributes.Edit",
        "CustomerProfiles.CalculatedAttributes.View",
        "CustomerProfiles.Create",
        "CustomerProfiles.Edit",
        "CustomerProfiles.Segments.Create",
        "CustomerProfiles.Segments.Delete",
        "CustomerProfiles.Segments.Export",
        "CustomerProfiles.Segments.View",
        "CustomerProfiles.View",
        "EmailAddresses.Create",
        "EmailAddresses.Edit",
        "EmailAddresses.Remove",
        "EmailAddresses.View",
        "Evaluation.Create",
        "Evaluation.Delete",
        "Evaluation.Edit",
        "Evaluation.View",
        "EvaluationAssistant.Access",
        "EvaluationCalibrationSessions.Create",
        "EvaluationCalibrationSessions.Delete",
        "EvaluationCalibrationSessions.Edit",
        "EvaluationCalibrationSessions.View",
        "EvaluationForms.Create",
        "EvaluationForms.Delete",
        "EvaluationForms.Edit",
        "EvaluationForms.View",
        "ForecastScheduleInterval.Edit",
        "ForecastScheduleInterval.View",
        "Forecasting.Publish",
        "Forecasting.Edit",
        "Forecasting.View",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "HoursOfOperation.Create",
        "HoursOfOperation.Delete",
        "HoursOfOperation.Edit",
        "HoursOfOperation.View",
        "ManagerBargeIn",
        "ManagerListenIn",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.Publish",
        "MetricsReports.Schedule",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "OutboundEmail.Create",
        "PhoneNumbers.Claim",
        "PhoneNumbers.Edit",
        "PhoneNumbers.Release",
        "PhoneNumbers.View",
        "PredefinedAttributes.Create",
        "PredefinedAttributes.Delete",
        "PredefinedAttributes.Edit",
        "PredefinedAttributes.View",
        "Prompts.Create",
        "Prompts.Delete",
        "Prompts.Edit",
        "Prompts.View",
        "Queues.Create",
        "Queues.Edit",
        "Queues.EnableAndDisable",
        "Queues.View",
        "DataTables.View",
        "DataTables.Edit",
        "DataTables.ManageValues",
        "DataTables.EditExpressionValues",
        "RealtimeContactLens.View",
        "ReportSchedules.Create",
        "ReportSchedules.Delete",
        "ReportSchedules.Edit",
        "ReportSchedules.View",
        "ReportsAdmin.Access",
        "ReportsAdmin.Delete",
        "ReportsAdmin.Publish",
        "ReportsAdmin.Schedule",
        "ReportsAdmin.View",
        "RestrictTaskCreation.Access",
        "RoutingPolicies.Create",
        "RoutingPolicies.Edit",
        "RoutingPolicies.View",
        "Rules.Create",
        "Rules.Delete",
        "Rules.Edit",
        "Rules.View",
        "RulesGenerativeAI.Create",
        "RulesGenerativeAI.Delete",
        "RulesGenerativeAI.Edit",
        "RulesGenerativeAI.View",
        "Scheduling.Edit",
        "Scheduling.Publish",
        "Scheduling.View",
        "ScreenRecording.Access",
        "ScreenRecording.Download",
        "SecurityProfiles.Create",
        "SecurityProfiles.Delete",
        "SecurityProfiles.Edit",
        "SecurityProfiles.View",
        "SelfAssignContacts.Access",
        "StaffCalendar.Edit",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TaskTemplates.Create",
        "TaskTemplates.Delete",
        "TaskTemplates.Edit",
        "TaskTemplates.View",
        "TeamCalendar.Edit",
        "TeamCalendar.View",
        "ThemeDetection.Create",
        "ThemeDetection.Delete",
        "ThemeDetection.View",
        "TimeOff.View",
        "TimeOffBalance.Edit",
        "TimeOffBalance.View",
        "TransferContact.Enabled",
        "TransferDestinations.Create",
        "TransferDestinations.Delete",
        "TransferDestinations.Edit",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.Create",
        "Users.Delete",
        "Users.Edit",
        "Users.EditPermission",
        "Users.View",
        "VideoContact.Access",
        "Views.Create",
        "Views.Edit",
        "Views.Remove",
        "Views.View",
        "VoiceId.Access",
        "VoiceIdAttributesAndSearch.View",
        "Wisdom.View",
        "CallRecordings.Redacted.Access",
        "CallRecordings.Unredacted.Access",
        "CallRecordings.Unredacted.DownloadButton",
        "ContactTranscripts.Redacted.Access",
        "ContactTranscripts.Unredacted.Access"
    ],
      "description"  = "A call center admin manages the day-to-day aspects of the call center, and can perform most actions available",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"CCManager" = {
 "permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentGrouping.View",
        "AgentStates.View",
        "AgentTimeCard.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "Bots.View",
        "Capacity.View",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactFlowModules.View",
        "ContactFlows.View",
        "ContactLensCustomVocabulary.Edit",
        "ContactLensCustomVocabulary.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "CustomViews.Access",
        "EmailAddresses.View",
        "Evaluation.Create",
        "Evaluation.Edit",
        "Evaluation.View",
        "EvaluationAssistant.Access",
        "EvaluationCalibrationSessions.Create",
        "EvaluationCalibrationSessions.Edit",
        "EvaluationCalibrationSessions.View",
        "EvaluationForms.Create",
        "EvaluationForms.Edit",
        "EvaluationForms.View",
        "ForecastScheduleInterval.View",
        "Forecasting.View",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "HoursOfOperation.View",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.Publish",
        "MetricsReports.Schedule",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "PhoneNumbers.View",
        "PredefinedAttributes.View",
        "Prompts.View",
        "Queues.View",
        "RealtimeContactLens.View",
        "ReportSchedules.Create",
        "ReportSchedules.Delete",
        "ReportSchedules.Edit",
        "ReportSchedules.View",
        "RestrictTaskCreation.Access",
        "RoutingPolicies.View",
        "Rules.Create",
        "Rules.Edit",
        "Rules.View",
        "RulesGenerativeAI.Create",
        "RulesGenerativeAI.Edit",
        "RulesGenerativeAI.View",
        "ScreenRecording.Access",
        "SecurityProfiles.View",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TaskTemplates.View",
        "ThemeDetection.Create",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "Views.View",
        "VoiceId.Access",
        "VoiceIdAttributesAndSearch.View",
        "ManagerListenIn",
        "CallRecordings.Unredacted.Access",
        "ContactTranscripts.Redacted.Access"
    ],
      "description"  = "A call center manager has complete viewer access of the day-to-day aspects of the call center.",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"CCSupervisor" = {
"permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentGrouping.View",
        "AgentStates.View",
        "AgentTimeCard.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "CallRecordings.Unredacted.Access",
        "Capacity.View",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactLensCustomVocabulary.Edit",
        "ContactLensCustomVocabulary.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "ContactTranscripts.Redacted.Access",
        "CustomViews.Access",
        "Evaluation.Create",
        "Evaluation.Edit",
        "Evaluation.View",
        "EvaluationAssistant.Access",
        "EvaluationCalibrationSessions.Create",
        "EvaluationCalibrationSessions.Edit",
        "EvaluationCalibrationSessions.View",
        "EvaluationForms.View",
        "ForecastScheduleInterval.View",
        "Forecasting.View",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "HoursOfOperation.View",
        "MetricsReports.Create",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "OutboundEmail.Create",
        "PredefinedAttributes.View",
        "Queues.View",
        "RealtimeContactLens.View",
        "RestrictTaskCreation.Access",
        "RoutingPolicies.View",
        "Rules.Create",
        "Rules.Edit",
        "Rules.View",
        "RulesGenerativeAI.Create",
        "RulesGenerativeAI.Edit",
        "RulesGenerativeAI.View",
        "ScreenRecording.Access",
        "SecurityProfiles.View",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TaskTemplates.View",
        "ThemeDetection.Create",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access",
        "VoiceIdAttributesAndSearch.View"
    ],
      "description"  = "A call center supervisor has complete viewer access of the day-to-day aspects of the call center specific to their team",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},
"CCComplaints" = {
"permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentGrouping.View",
        "AgentStates.View",
        "AgentTimeCard.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "Capacity.View",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactLensCustomVocabulary.Edit",
        "ContactLensCustomVocabulary.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "CustomViews.Access",
        "Evaluation.Create",
        "Evaluation.Edit",
        "Evaluation.View",
        "EvaluationAssistant.Access",
        "EvaluationCalibrationSessions.Create",
        "EvaluationCalibrationSessions.Edit",
        "EvaluationCalibrationSessions.View",
        "EvaluationForms.View",
        "ForecastScheduleInterval.View",
        "Forecasting.View",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "HoursOfOperation.View",
        "MetricsReports.Create",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "PredefinedAttributes.View",
        "Queues.View",
        "RealtimeContactLens.View",
        "RestrictTaskCreation.Access",
        "RoutingPolicies.View",
        "Rules.Create",
        "Rules.Edit",
        "Rules.View",
        "RulesGenerativeAI.Create",
        "RulesGenerativeAI.Edit",
        "RulesGenerativeAI.View",
        "ScreenRecording.Access",
        "SecurityProfiles.View",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TaskTemplates.View",
        "ThemeDetection.Create",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access",
        "VoiceIdAttributesAndSearch.View",
        "CallRecordings.Unredacted.Access",
        "CallRecordings.Unredacted.DownloadButton",
        "ContactTranscripts.Redacted.Access"
    ],
      "description"  = "A call center Complaints has complete viewer access of the day-to-day aspects of the call center specific to their team and can download Recordings.",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"CCAgent" = {
  "permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "CustomViews.Access",
        "HistoricalChanges.View",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "OutboundEmail.Create",
        "Queues.View",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "VoiceId.Access"
    ],
      "description"  = "An agent is a user of the system that is focused on customer care and/or sales. Their role is unlikely to be technical.",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"CCManagerV1" = {
    "permissions" = [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "CustomViews.Access",
        "CallRecordings.Unredacted.Access",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "ContactTranscripts.Redacted.Access",
        "GraphTrends.View",
        "HoursOfOperation.View",
        "ManagerListenIn",
        "MetricsReports.Create",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "Queues.View",
        "RealtimeContactLens.View",
        "RestrictContactAccessByHierarchy.View",
        "RestrictTaskCreation.Access",
        "RoutingPolicies.View",
        "ScreenRecording.Access",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "ThemeDetection.Create",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access",
        "VoiceIdAttributesAndSearch.View"     
     ],
      "description"  = "A call center manager has complete viewer access of the day-to-day aspects of the call center.",
      "allowed_access_control_tags" = [{
        key   = "vendor"
        value = "concentrix"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours","TransferDestination", "Queue","User"],
      "has_hierarchy"                              = true
    },

"Quality Training"={
    "permissions" = [
        "AccessMetrics",
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.Dashboards.Access",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactLensCustomVocabulary.Edit",
        "ContactLensCustomVocabulary.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "CustomViews.Access",
        "Evaluation.Create",
        "Evaluation.Delete",
        "Evaluation.Edit",
        "Evaluation.View",
        "EvaluationAssistant.Access",
        "EvaluationCalibrationSessions.Create",
        "EvaluationCalibrationSessions.Delete",
        "EvaluationCalibrationSessions.Edit",
        "EvaluationCalibrationSessions.View",
        "EvaluationForms.Create",
        "EvaluationForms.Delete",
        "EvaluationForms.Edit",
        "EvaluationForms.View",
        "GraphTrends.View",
        "HistoricalChanges.View",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "Queues.View",
        "ScreenRecording.Access",
        "StaffCalendar.View",
        "ThemeDetection.View",
        "StopContact.Enabled",
        "TransferContact.Enabled",
        "UpdateContactSchedule.Enabled",
        "VoiceId.Access",
        "CallRecordings.Unredacted.Access",
        "ContactTranscripts.Redacted.Access"
    ],
      "description"  = "A quality analyst works to improve the customer experience and keeps track of live service metrics.",
      "tags"                                      = [],
      "allowed_access_control_tags"               = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                              = false
},

"CCSupervisorV1" = {
  "permissions" = [
      "AccessMetrics.AgentActivityAudit.Access",
      "AccessMetrics.DashboardsWithMyData.View",
      "AccessMetrics.HistoricalMetrics.Access",
      "AccessMetrics.RealTimeMetrics.Access",
      "AgentStates.View",
      "AudioDeviceSettings.Access",
      "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
      "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
      "BasicAgentAccess",
      "CustomViews.Access",
      "CallRecordings.Unredacted.Access",
      "ConfigureContactAttributes.View",
      "ContactAttributes.View",
      "ContactLensPostContactSummary.View",
      "ContactSearch.View",
      "ContactSearchWithCharacteristics.View",
      "ContactSearchWithKeywords.View",
      "ContactTranscripts.Redacted.Access",
      "GraphTrends.View",
      "HoursOfOperation.View",
      "MetricsReports.Create",
      "MetricsReports.Edit",
      "MetricsReports.View",
      "MyContacts.View",
      "OutboundCallAccess",
      "Queues.View",
      "RealtimeContactLens.View",
      "RestrictContactAccessByHierarchy.View",
      "RestrictTaskCreation.Access",
      "RoutingPolicies.View",
      "ScreenRecording.Access",
      "StaffCalendar.View",
      "StopContact.Enabled",
      "ThemeDetection.Create",
      "ThemeDetection.View",
      "TransferContact.Enabled",
      "TransferDestinations.View",
      "UpdateContactSchedule.Enabled",
      "Users.View",
      "VoiceId.Access",
      "VoiceIdAttributesAndSearch.View"
    ],
    "description"  = "A call center manager has complete viewer access of the day-to-day aspects of the call center specific to their team",
    "allowed_access_control_tags" = [{
        key   = "vendor"
        value = "concentrix"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours","TransferDestination","Queue","User"],
      "has_hierarchy"                              = true
},


"CCAgentV1" = {
    "permissions" = [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "CustomViews.Access",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "EmailAddresses.View",
        "HoursOfOperation.View",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "Queues.View",
        "RestrictContactAccessByHierarchy.View",
        "RoutingPolicies.View",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access"
    ],
    "description"  = "An agent is a user of the system that is focused on customer care and/or sales. Their role is unlikely to be technical.",
    "allowed_access_control_tags" = [{
        key   = "vendor"
        value = "concentrix"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours", "TransferDestination", "Queue", "User", "EmailAddress"],
      "has_hierarchy"                              = true
},

"ReportingV1" = {
    "permissions": [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "MetricsReports.View",
        "Queues.View",
        "RoutingPolicies.View",
        "Users.View"
    ],
      "description"  = "The reporting analyst works to improve the reporting experience and keeps track of live service metrics.",
      "allowed_access_control_tags" = [{
        key   = "vendor"
        value = "concentrix"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile","Queue","User"],
      "has_hierarchy"                              = true
},

"WFMV1" = {
    "permissions": [
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.Edit",
        "AgentStates.View",
        "HoursOfOperation.View",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "Queues.View",
        "RoutingPolicies.View",
        "Users.Edit",
        "Users.View"
    ],
      "description"  = "A wfm analyst works to improve the customer experience, monitors queues, makes changes based on service metrics.",
      "allowed_access_control_tags" = [{
        key   = "vendor"
        value = "concentrix"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours", "Queue","User"],
      "has_hierarchy"                              = true
},

"TestV1" = {
    "permissions": [
        "AccessMetrics",
        "AccessMetrics.DashboardsWithMyData.View",
        "RestrictContactAccessByHierarchy.View",
        "RoutingPolicies.View",
        "ScreenRecording.Access",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "UpdateContactSchedule.Enabled"
    ],
      "description"  = "This Security Profile is created for Testing purposes..",
      "allowed_access_control_tags" = [{
        key   = "vendor2"
        value = "gatestone"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours", "Queue","User"],
      "has_hierarchy"                              = true
},

"Quality Training V1" = {
    "permissions" = [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "CustomViews.Access",
        "CallRecordings.Unredacted.Access",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "ContactTranscripts.Redacted.Access",
        "GraphTrends.View",
        "HoursOfOperation.View",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "Queues.View",
        "RestrictContactAccessByHierarchy.View",
        "RoutingPolicies.View",
        "ScreenRecording.Access",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access"
    ],
    "description"  = "A quality analyst works to improve the customer experience and keeps track of live service metric",
    "allowed_access_control_tags" = [{
        key   = "vendor"
        value = "concentrix"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours", "Queue","User"],
      "has_hierarchy"                              = true
},
"CCManagerV2" = {
    "permissions" = [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "CustomViews.Access",
        "CallRecordings.Unredacted.Access",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "ContactTranscripts.Redacted.Access",
        "GraphTrends.View",
        "HoursOfOperation.View",
        "ManagerListenIn",
        "MetricsReports.Create",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "Queues.View",
        "RealtimeContactLens.View",
        "RestrictContactAccessByHierarchy.View",
        "RestrictTaskCreation.Access",
        "RoutingPolicies.View",
        "ScreenRecording.Access",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "ThemeDetection.Create",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access",
        "VoiceIdAttributesAndSearch.View"     
     ],
      "description"  = "A call center manager has complete viewer access of the day-to-day aspects of the call center.",
      "allowed_access_control_tags" = [{
        key   = "vendor2"
        value = "gatestone"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.vendor2_teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours","TransferDestination", "Queue","User"],
      "has_hierarchy"                              = true
},
"CCSupervisorV2" = {
  "permissions" = [
      "AccessMetrics.AgentActivityAudit.Access",
      "AccessMetrics.DashboardsWithMyData.View",
      "AccessMetrics.HistoricalMetrics.Access",
      "AccessMetrics.RealTimeMetrics.Access",
      "AgentStates.View",
      "AudioDeviceSettings.Access",
      "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
      "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
      "BasicAgentAccess",
      "CustomViews.Access",
      "CallRecordings.Unredacted.Access",
      "ConfigureContactAttributes.View",
      "ContactAttributes.View",
      "ContactLensPostContactSummary.View",
      "ContactSearch.View",
      "ContactSearchWithCharacteristics.View",
      "ContactSearchWithKeywords.View",
      "ContactTranscripts.Redacted.Access",
      "GraphTrends.View",
      "HoursOfOperation.View",
      "MetricsReports.Create",
      "MetricsReports.Edit",
      "MetricsReports.View",
      "MyContacts.View",
      "OutboundCallAccess",
      "Queues.View",
      "RealtimeContactLens.View",
      "RestrictContactAccessByHierarchy.View",
      "RestrictTaskCreation.Access",
      "RoutingPolicies.View",
      "TeamCalendar.View",
      "ScreenRecording.Access",
      "StaffCalendar.View",
      "StopContact.Enabled",
      "ThemeDetection.Create",
      "ThemeDetection.View",
      "TransferContact.Enabled",
      "TransferDestinations.View",
      "UpdateContactSchedule.Enabled",
      "Users.View",
      "VoiceId.Access",
      "VoiceIdAttributesAndSearch.View"
    ],
    "description"  = "A call center manager has complete viewer access of the day-to-day aspects of the call center specific to their team",
    "allowed_access_control_tags" = [{
        key   = "vendor2"
        value = "gatestone"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.vendor2_teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours","TransferDestination", "Queue","User"],
      "has_hierarchy"                              = true
},
"CCAgentV2" = {
    "permissions" = [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "CustomViews.Access",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "HoursOfOperation.View",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "Queues.View",
        "RestrictContactAccessByHierarchy.View",
        "RoutingPolicies.View",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "TransferContact.Enabled",
        "TransferDestinations.View",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access"
    ],
    "description"  = "An agent is a user of the system that is focused on customer care and/or sales. Their role is unlikely to be technical.",
    "allowed_access_control_tags" = [{
        key   = "vendor2"
        value = "gatestone"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.vendor2_teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours","TransferDestination", "Queue","User"],
      "has_hierarchy"                              = true
},
"ReportingV2" = {
    "permissions" = [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "MetricsReports.View",
        "Queues.View",
        "RoutingPolicies.View",
        "Users.View"
    ],
      "description"  = "A reporting analyst works to improve the reporting experience and keeps track of live service metrics.",
      "allowed_access_control_tags" = [{
        key   = "vendor2"
        value = "gatestone"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.vendor2_teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "Queue","User"],
      "has_hierarchy"                              = true
},

"WFMV2" = {
    "permissions" = [
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.Edit",
        "AgentStates.View",
        "HoursOfOperation.View",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "Queues.View",
        "RoutingPolicies.View",
        "TeamCalendar.View",
        "Users.Edit",
        "Users.View"
    ],
      "description"  = "A wfm analyst works to improve the customer experience, monitors queues, makes changes based on service metrics.",
      "allowed_access_control_tags" = [{
        key   = "vendor2"
        value = "gatestone"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.vendor2_teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours", "Queue","User"],
      "has_hierarchy"                              = true
},
"CCHandleTask" = {
    "permissions": [
        "ManualAssignAnyContact.Enable",
        "RestrictTaskCreation.Access"
    ],
      "description"  = "The CCHandleTask is an extended permissions to be given to Assign Task.",
      "allowed_access_control_tags" = [],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = "",
      "hierarchy_restricted_resources"            = [],
      "tag_restricted_resources"                  = [],
      "has_hierarchy"                             = false
}
"Quality Training V2" = {
    "permissions" = [
        "AccessMetrics.AgentActivityAudit.Access",
        "AccessMetrics.DashboardsWithMyData.View",
        "AccessMetrics.HistoricalMetrics.Access",
        "AccessMetrics.RealTimeMetrics.Access",
        "AgentStates.View",
        "AudioDeviceSettings.Access",
        "AutomatedVoiceInteraction.Recordings.Unredacted.Access",
        "AutomatedVoiceInteraction.Transcripts.Unredacted.Access",
        "BasicAgentAccess",
        "CustomViews.Access",
        "CallRecordings.Unredacted.Access",
        "ConfigureContactAttributes.View",
        "ContactAttributes.View",
        "ContactLensPostContactSummary.View",
        "ContactSearch.View",
        "ContactSearchWithCharacteristics.View",
        "ContactSearchWithKeywords.View",
        "ContactTranscripts.Redacted.Access",
        "GraphTrends.View",
        "HoursOfOperation.View",
        "MetricsReports.Create",
        "MetricsReports.Delete",
        "MetricsReports.Edit",
        "MetricsReports.View",
        "MyContacts.View",
        "OutboundCallAccess",
        "Queues.View",
        "RestrictContactAccessByHierarchy.View",
        "RoutingPolicies.View",
        "ScreenRecording.Access",
        "StaffCalendar.View",
        "StopContact.Enabled",
        "ThemeDetection.View",
        "TransferContact.Enabled",
        "UpdateContactSchedule.Enabled",
        "Users.View",
        "VoiceId.Access"
    ],
    "description"  = "A quality analyst works to improve the customer experience and keeps track of live service metric",
    "allowed_access_control_tags" = [{
        key   = "vendor2"
        value = "gatestone"
      }],
      "tags" = [],
      "allowed_access_control_hierarchy_group_id" = data.aws_connect_user_hierarchy_group.vendor2_teamA.hierarchy_group_id,
      "hierarchy_restricted_resources"            = ["User"],
      "tag_restricted_resources"                  = ["RoutingProfile", "OperatingHours", "Queue","User"],
      "has_hierarchy"                              = true
},
}
}


