account-id = "207567788052"
role-id    = "pci-ccr-deployer"
region     = "ca-central-1"
env        = "dev"

#Artifactory URL
artifactory_url = "https://artifactory.rogers.com/artifactory"
artifactory_access_token = "empty"


#Artifactory URL
artifactory_user = "serv_svc_rb_pci"
//artifactory_user = "rohit.sahu1"

### Connect ###
identity_management_type      = "CONNECT_MANAGED"
saml_identity_management_type = "SAML"
#instance_alias                = "app"
saml_instance_new_alias           = "app"
saml_instance_alias           = "saml-app"
connect_instance_id       = "7c2d98cf-e3c5-465c-961e-59687f464167"
connect_instance_arn      = "arn:aws:connect:ca-central-1:207567788052:instance/efe17a4a-8711-4834-8bb7-3036473cdcd2"
is_saml                       = true


### S3 Bucket ###
target-bucket                        = "rogers-rbconnect-access-logs"
call-recording-bucket                = "callrecording"
kinesis-ctr-bucket                   = "ctr"
contact-flows-bucket                 = "contactflows"
s3-objects                           = ["CallRecordings"]
create-additional-bucket-policy-main = true

getaccountbycardlambda_sg      = ["sg-0aa454c9391f0a2ee"]
getaccountbyANI_sg            = ["sg-05837b0682d68a0ed"]
verifypin_sg                  = ["sg-06352159ecfeae963"]
changepin_sg                  = ["sg-006700b130da7a456"]
lambda-exec-role-arn          = "arn:aws:iam::207567788052:role/pci-ccr-GetAccountbyCard-execution-role"
rbconnect-pci-getaccountbycard-lambda = "fd06f42c4b7c02c74a450ffcb18409eec510b3ea" 
rbconnect-pci-getaccountbyani-lambda = "ba7616480e19760e7b99f246d90a1612e5f718c2"
rbconnect-pci-changepin-lambda = "a66f4737570998703f53ac530c3469d89e7b68ad"
rbconnect-pci-changepintest-lambda = "a66f4737570998703f53ac530c3469d89e7b68ad"
rbconnect-pci-verifypin-lambda = "13b813fef298df7b38adbcba924645d957a6ce8d"
rbconnect-pci-voicemailcopy-lambda = "e1d3fe769674890de127849e449ba3663174d7c1"
rbconnect-pci-voicemailcreatetask-lambda = "5f269237c581b1779a10665299260022551041a7"
rbconnect-pci-voicemailtranscriber-lambda = "363e5eb2d1f226d109a3566a4cc2ab8e1da2cfb8"
#artifact_hash_layer   = "73ab3cee1a379c17cb7f35403b567cc2ec81b653"
artifact_hash_layer   =  "774c8aa0f176c1eabc13f7605959a5aa7fe24fa7"
artifactory_env_path  = "dev-ado"
lambda_insights_layer_arn = "arn:aws:lambda:ca-central-1:580247275435:layer:LambdaInsightsExtension:55"


### Networking ###
vpc_id                              = "vpc-057c2f1e094d63aca"
security_group_ids                  = ["sg-0d817ba4e46bf57fa"]
subnet_ids                          = ["subnet-059ace10ab2c5a859", "subnet-0bc36206c042a4df5", "subnet-031085493e9808cec"]

environment-variables = {
  TSYS_URL = "https://test.tsysapi.com"
}

tags = {
  environment         = "dev"
  project-id          = "1991" 
  application-owner   = "hernan.morano@rci.rogers.com" 
  data-classification = "restricted"
  application-id      = "1991" 
  application-role    = "app"
  application-name    = "RB-PCI-RBCONNECT"
  PII                 = "NO"
  compliance          = "None"
  SCOA                = "912.1101.6501.0000.69025" 
  TFE                 = "YES"
  businessunit        = "rb"
  otl-value           = "" 
  task-code-value     = "1.12"
  applicationname     = "RB-PCI-RBCONNECT"
  costcenter          = "982.1101.8506"
  application-prefix  = "rbconnect"
}

###########################################################################################
####                   eventbus and event rule             ##############################
#############################################################################################

# Create a custom Event Bus
event_bus_name     = "rb-pci-dev-eventbus-rbconnect"
create_event_bus   = true

# Enable rule creation
create_event_rules = true

rules = {
  "ctr-c-rule" = {
    name           = "rb-pci-dev-eventrule-rbconnect-ctr-calls"
    description    = "Matches CTR-C events"
    event_pattern  = {
      "source" : ["rb-pci-dev-eventpipe-rbconnect-ctr-calls"]
    }
    event_bus_name = "default"
    state          = "ENABLED"
    role_arn       = null
  }

  "ctr-v-rule" = {
    name           = "rb-pci-dev-eventrule-rbconnect-ctr-voicemail"
    description    = "Matches CTR-V events"
   event_pattern  = {
      "source" : ["rb-pci-dev-eventpipe-rbconnect-ctr-voicemail"]
    }
    event_bus_name = "default"
    state          = "ENABLED"
    role_arn       = null
  }

  "ae-a-rule" = {
    name           = "rb-pci-dev-eventrule-rbconnect-ae-cnx"
    description    = "Matches AE-A events"
    event_pattern  = {
      "source" : ["rb-pci-dev-eventpipe-rbconnect-ae-cnx"]
    }
    event_bus_name = "default"
    state          = "ENABLED"
    role_arn       = null
  }

  "ae-b-rule" = {
    name           = "rb-pci-dev-eventrule-rbconnect-ae-rogers"
    description    = "Matches AE-B events"
    event_pattern  = {
      "source" : ["rb-pci-dev-eventpipe-rbconnect-ae-cnx"]
    }
    event_bus_name = "default"
    state          = "ENABLED"
    role_arn       = null
  }

}

# Enable target creation
create_event_targets = true

targets = {
  "ctr-c-target" = {
    name               = "rb-pci-dev-eventtarget-rbconnect-ctr-calls"
    rule_name          = "rb-pci-dev-eventrule-rbconnect-ctr-calls"
    event_bus_name     = "default"
    arn                = "arn:aws:kinesis:ca-central-1:489551464761:stream/rb-dev-kds-rbconnect-ctr-calls"
    target_id          = "ctr-c-kinesis-target"
    role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbusrule-kinesis-execution-role"

  input_path     = "$.detail.data"  # <== THIS is what you need
  }

  "ctr-v-target" = {
    name               = "rb-pci-dev-eventtarget-rbconnect-ctr-voicemail"
    rule_name          = "rb-pci-dev-eventrule-rbconnect-ctr-voicemail"
    event_bus_name     = "default"
    arn                = "arn:aws:kinesis:ca-central-1:489551464761:stream/rb-dev-kds-rbconnect-ctr-voicemail"
    target_id          = "ctr-v-kinesis-target"
    role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbusrule-kinesis-execution-role"

  input_path     = "$.detail.data"  # <== THIS is what you need
  }

  "ae-a-target" = {
    name               = "rb-pci-dev-eventtarget-rbconnect-ae-cnx"
    rule_name          = "rb-pci-dev-eventrule-rbconnect-ae-cnx"
    event_bus_name     = "default"
    arn                = "arn:aws:kinesis:ca-central-1:489551464761:stream/rb-dev-kds-rbconnect-ae-cnx"
    target_id          = "ae-a-kinesis-target"
    role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbusrule-kinesis-execution-role"

  input_path     = "$.detail.data"  # <== THIS is what you need
  }

  "ae-b-target" = {
    name               = "rb-pci-dev-eventtarget-rbconnect-ae-rogers"
    rule_name          = "rb-pci-dev-eventrule-rbconnect-ae-rogers"
    event_bus_name     = "default"
    arn                = "arn:aws:kinesis:ca-central-1:489551464761:stream/rb-dev-kds-rbconnect-ae-rogers"
    target_id          = "ae-b-kinesis-target"
    role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbusrule-kinesis-execution-role"

  input_path     = "$.detail.data"  # <== THIS is what you need
  }

}

#####################################################################################
####            Pipes                                         ######################
##################################################################################

create_pipes = true

pipes = {
    "rbconnect-ae-cnx" = {
      name         = "rb-pci-dev-eventpipe-rbconnect-ae-cnx"
      role_arn     = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
      source       = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-agentevents"
      target       = "arn:aws:events:ca-central-1:207567788052:event-bus/default"
      desired_state = "RUNNING"

      disable_default_cloudwatch_logging = true

      source_parameters = {
        kinesis_stream_parameters = {
          batch_size                         = 5
          starting_position                  = "LATEST"
        }

        filter_criteria = {
          filter = [
            {
              pattern = <<-EOF
              {
                "data" : {
                  "CurrentAgentSnapshot" : {
                    "Configuration" : {
                      "Username" : [{
                        "suffix" : "@concentrix.com"
                         }]
                       }
                     }
                   }
                 }
              EOF
            }
          ]
        }
      }

      target_parameters = {
        input_template = <<EOT
{
  "data": <$.data>
}
EOT

        eventbridge_event_bus_parameters = {
          detail_type = ""
          source      = "rb-pci-dev-eventpipe-rbconnect-ae-cnx"
          resources = []
        }
      }
    },

"eventpipe_ctr_voicemail" = {
    name         = "rb-pci-dev-eventpipe-rbconnect-ctr-voicemail"
    role_arn     = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
    source       = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-ctr"
    target       = "arn:aws:events:ca-central-1:207567788052:event-bus/default"
    desired_state = "RUNNING"
    disable_default_cloudwatch_logging = true

    source_parameters = {
      kinesis_stream_parameters = {
        batch_size                         = 5
        starting_position                  = "LATEST"
      }

      filter_criteria = {
        filter = [
          {
            pattern = <<-EOF
            {
              "data": {
                "Channel": [
                  "VOICE"
                ],
                "SegmentAttributes": {   
                  "voicemail": {     
                    "ValueString": [ "true" ]   
                  } 
                }
              }
            }
            EOF
          }
        ]
      }
    }

    target_parameters = {
      input_template = <<EOT
{
  "data": <$.data>
}
EOT
      eventbridge_event_bus_parameters = {
        detail_type = ""
        source      = "rb-pci-dev-eventpipe-rbconnect-ctr-voicemail"
        resources = []
      }
    }
  }

  "eventpipe-ctr-calls" = {
    name         = "rb-pci-dev-eventpipe-rbconnect-ctr-calls"
    role_arn     = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
    source       = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-ctr"
    target       = "arn:aws:events:ca-central-1:207567788052:event-bus/default"
    desired_state = "RUNNING"
    disable_default_cloudwatch_logging = true

    source_parameters = {
      kinesis_stream_parameters = {
        batch_size                         = 5
        starting_position                  = "LATEST"
      }

      filter_criteria = {
        filter = [
          {
            pattern = <<-EOF
            {
              "data" : {
                "Attributes" : {
                  "voicemail" : [{ "exists": false }]
                },
                "Channel" : ["VOICE", "EMAIL", "TASK"]
                }
              }
            EOF
          }
        ]
      }
    }

    target_parameters = {
      input_template = <<EOT
{
  "data": <$.data>
}
EOT
      eventbridge_event_bus_parameters = {
        detail_type = ""
        source      = "rb-pci-dev-eventpipe-rbconnect-ctr-calls"
        resources   = []
      }
    }
  },

  "eventpipe-ae-rogers" = {
    name         = "rb-pci-dev-eventpipe-rbconnect-ae-rogers"
    role_arn     = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
    source       = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-agentevents"
    target       = "arn:aws:events:ca-central-1:207567788052:event-bus/default"
    desired_state = "RUNNING"
    disable_default_cloudwatch_logging = true

    source_parameters = {
      kinesis_stream_parameters = {
        batch_size                         = 5
        starting_position                  = "LATEST"
      }

      filter_criteria = {
        filter = [
          {
            pattern = <<-EOF
            {
              "data" : {
                "Attributes" : {
                  "voicemail" : [null]
                },
                "Channel" : ["VOICE", "EMAIL", "TASK"]
              }
            }
            EOF
          }
        ]
      }
    }

    target_parameters = {
      input_template = <<EOT
{
  "data": <$.data>
}
EOT
      eventbridge_event_bus_parameters = {
        detail_type = ""
        source      = "rb-pci-dev-eventpipe-rbconnect-ae-rogers"
        resources   = []
      }
    }
  }
}

#########################################################################################################################
##     Amazon Connect Data Tables                                                                                      ##
##########################################################################################################################


instance_arn = "arn:aws:connect:us-east-1:123456789012:instance/11111111-1111-1111-1111-111111111111"

data_tables = {
  dtGlobalPrompts = {
    name             = "dtGlobalPrompts"
    description      = "This table is used to store Global Prompts"
    time_zone        = "Canada/Central"
    value_lock_level = "NONE"

    attributes = [
      {
        name        = "MsgId"
        value_type  = "TEXT"
        primary     = true
        description = "MsgId"
      },
      {
        name        = "AdvisoryMessageEn"
        value_type  = "TEXT"
        primary     = false
        description = "AdvisoryMessageEn"
      },
      {
        name        = "AdvisoryMessageFr"
        value_type  = "TEXT"
        primary     = false
        description = "AdvisoryMessageFr"
      }
    ]
  }

  dtQueuesMetrics = {
    name             = "dtQueuesMetrics"
    description      = "Data Table to store AHT of queues"
    time_zone        = "Canada/Central"
    value_lock_level = "NONE"

    attributes = [
      {
        name        = "QueueName"
        value_type  = "TEXT"
        primary     = true
        description = "QueueName"
      },
      {
        name        = "AHT1"
        value_type  = "NUMBER"
        primary     = false
        description = "AHT1"
      },
      {
        name        = "AHT2"
        value_type  = "NUMBER"
        primary     = false
        description = "AHT2"
      },
      {
        name        = "QueueARN1"
        value_type  = "TEXT"
        primary     = false
        description = "QueueARN1"
      },
      {
        name        = "QueueARN2"
        value_type  = "TEXT"
        primary     = false
        description = "QueueARN2"
      },
      {
        name        = "QueueDescription"
        value_type  = "TEXT"
        primary     = false
        description = "QueueDescription"
      }
    ]
  }
  dtGlobalSet = {
    name             = "dtGlobalSet"
    description      = "Global Set"
    time_zone        = "Canada/Eastern"
    value_lock_level = "NONE"

    attributes = [
      {
        name        = "featureID"
        value_type  = "TEXT"
        primary     = true
        description = "featureID"
      },
      {
        name        = "Attr1"
        value_type  = "TEXT"
        primary     = false
        description = "Attr1"
      },
      {
        name        = "Attr2"
        value_type  = "TEXT"
        primary     = false
        description = "Attr2"
      },
      {
        name        = "Attr3"
        value_type  = "TEXT"
        primary     = false
        description = "Attr3"
      },
      {
        name        = "Attr4"
        value_type  = "TEXT"
        primary     = false
        description = "Attr4"
      }
    ]    
  } 
  dtAgencyCodeConfig = {
    name             = "dtAgencyCodeConfig"
    description      = "Agency Code Configuration"
    time_zone        = "Canada/Central"
    value_lock_level = "NONE"

    attributes = [
     {
       name        = "agencyCode"
       value_type  = "TEXT"
       primary     = true
       description = "agencyCode"
     },
     {
       name        = "externalNumber1"
       value_type  = "TEXT"
       primary     = false
       description = "externalNumber1"
     },
     {
       name        = "externalNumber2"
       value_type  = "TEXT"
       primary     = false
       description = "externalNumber2"
     },
     {
       name        = "isActive"
       value_type  = "BOOLEAN"
       primary     = false
       description = "isActive"
     }
   ]
 }
  dtVoiceMailDestination = {
    name             = "dtVoiceMailDestination"
    description      = "Stores voicemail external numbers mapped to queue destinations"
    time_zone        = "Canada/Central"
    value_lock_level = "NONE"

    attributes = [
      {
        name        = "externalNumber"
        value_type  = "TEXT"
        primary     = true
        description = "External phone number used for voicemail routing"
      },
      {
        name        = "queueDestination"
        value_type  = "TEXT"
        primary     = false
        description = "Queue ARN destination for voicemail"
      }
    ]
  }

  dtVoiceMailNumber = {
    name             = "dtVoiceMailNumber"
    description      = "Stores queue ARN to voicemail external number mapping"
    time_zone        = "Canada/Central"
    value_lock_level = "NONE"

    attributes = [
      {
        name        = "queueARN"
        value_type  = "TEXT"
        primary     = true
        description = "Queue ARN"
      },
      {
        name        = "externalNumber"
        value_type  = "TEXT"
        primary     = false
        description = "External phone number associated with the queue"
      }
    ]
  }
}


