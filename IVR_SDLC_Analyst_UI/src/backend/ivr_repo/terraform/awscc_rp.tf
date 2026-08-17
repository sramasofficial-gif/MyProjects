
#################################Routing profile - Back Office -EN ##################################################################
# 1️⃣ Move EN Routing Profile
moved {
  from = awscc_connect_routing_profile.p_rogersbank_backoffice_awscc_en
  to   = awscc_connect_routing_profile.this["p_rogersbank_backoffice_awscc_en"]
}


# 2️⃣ Move FR Routing Profile
moved {
  from = awscc_connect_routing_profile.p_rogersbank_backoffice_awscc_fr
  to   = awscc_connect_routing_profile.this["p_rogersbank_backoffice_awscc_fr"]
}


/*
resource "awscc_connect_routing_profile" "p_rogersbank_backoffice_awscc_en" {

  name                       = "P_RogersBank_BackOffice_EN"
  description                = "P_RogersBank_BackOffice_EN"
  instance_arn               = var.connect_instance_arn
  default_outbound_queue_arn = var.rp_backoffice_default_outbound_queue_arn
  
  media_concurrencies = [{
    channel     = "TASK"
    concurrency = 1
  },
  {
    channel     = "VOICE"
    concurrency = 1 
  }

]

  queue_configs = [{
    delay    = 0
    priority = 4
    queue_reference = {
      channel   = "TASK"
      queue_arn = var.rp_queueconfig_backoffice_en_queue_arn
    }
  },
  {
    delay    = 0
    priority = 4
    queue_reference = {
      channel   = "VOICE"
      queue_arn = var.rp_queueconfig_backoffice_en_queue_arn
    }

  },

  {
     delay  = 0
     priority = 9
     queue_reference = {
       channel   = "VOICE"
       queue_arn = var.rp_queueconfig_quickconnectsonly_en_queue_arn
    }

  }
]
 # --- Manual Assignment (Worklist) Queue Configs ---
  # This is the capability the standard AWS provider does not support yet.
manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_manual_assignment_backoffice_task_queue_arn 
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



} 
*/

#################################Routing profile - Back Office -FR ##################################################################
/*
resource "awscc_connect_routing_profile" "p_rogersbank_backoffice_awscc_fr" {

  name                       = "P_RogersBank_BackOffice_FR"
  description                = "P_RogersBank_BackOffice_FR"
  instance_arn               = var.connect_instance_arn
  default_outbound_queue_arn = var.rp_backoffice_fr_default_outbound_queue_arn
  

 media_concurrencies = [{
    channel     = "TASK"
    concurrency = 1
  },
  {
    channel     = "VOICE"
    concurrency = 1 
  }

]

 queue_configs = [
    # Existing queue
    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "TASK"
        queue_arn = var.rp_queueconfig_backoffice_en_queue_arn
      }
    },

    {
      delay    = 0
      priority = 4
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_queueconfig_backoffice_en_queue_arn
      }
    },

    
    {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "TASK"
        queue_arn = var.rp_queueconfig_backoffice_fr_queue_arn
      }
    },

     {
      delay    = 0
      priority = 3
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_queueconfig_backoffice_fr_queue_arn
      }
    },
   
    {
      delay    = 0
      priority = 9
      queue_reference = {
        channel   = "VOICE"
        queue_arn = var.rp_queueconfig_quickconnectsonly_en_queue_arn
      }
    }
  ]



  # --- Manual Assignment (Worklist) Queue Configs ---
  # This is the capability the standard AWS provider does not support yet.
  manual_assignment_queue_configs   = [
    {
      queue_reference = {
          channel   = "TASK"
          queue_arn = var.rp_manual_assignment_backoffice_task_queue_arn 
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
}*/

