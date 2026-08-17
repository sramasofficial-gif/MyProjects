resource "awscc_connect_task_template" "rb-ccr-pci-task-template" {
  instance_arn = var.connect_instance_arn
  name         = "Backoffice Team Task"
  description  = "Backoffice Team Task"
  status       = "ACTIVE"

  contact_flow_arn = var.cfBackOfficeTaskFlowArn

  fields = [
    {
      description = "Task Name"
      id = {
        name = "Task Name"
      }
      type = "NAME"
    },
     {
      description = "Task Description"
      id = {
        name = "Description"
      }
      type = "DESCRIPTION"
    },
    {
      description = "Type of Work required"
      id = {
        name = "Type of Work required"
      }
      type = "SINGLE_SELECT"
      single_select_options = [
        "Disney Plus",
        "SMB Business Detail Update",
        "Credit Limit Decrease Requests",
        "Wireless Add-a-Line",
        "2x cash back rewards",
        "Preferred Name Request",
        "Delete Digital Profile Request",
        "Bank and Residential Xfinity",
        "Credit Marketing",
        "RLH",
        "2 Percent",
        "Rewards Redemption",
        "Statement Reprint",
        "Account Reinstatement",
        "Collateral Request",
        "Rogers Bank at Rogers Mobile Offer",
        "Welcome Bonus",
        "Manual CB Pull Request - ADM",
        "Credit Balance Refund - Cheque",
        "TSC Dyson 4 Percent Cashback",
        "Fido Student Offer",
        "1 Percent Red SMB Partners Bonus",
        "Rogers Entertainment Credit",
        "World Legend Roam Like Home"
      ]

    },
    
    {
      description = "Agent TSYS ID"
      id = {
        name = "TS2 ID"
      }
      type = "TEXT"
    },
    {
      description = "Account ID"
      id = {
        name = "Account ID"
      }
      type = "TEXT"
    },
    {
      description = "For Back Office Team"
      id = {
        name = "For Back Office Team"
      }
      type = "TEXT_AREA"
    },     
    
    {
      description = "Expiry Duration (seconds)"
      id = { 
        name = "Expiry Duration"
      }
      type = "EXPIRY_DURATION"
    }
    
    
     
]

  constraints = {
    required_fields = [
      {
        id = {
          name = "Task Name"
        }
      },
      {
        id = {
           name = "Description"
        }
      },
      {
        id = {
           name = "Type of Work required"
        }
      },
      {
        id = {
           name = "TS2 ID"
        }
      },
      {
        id = {
           name = "Account ID"
        }
      },
      {
        id = {
           name = "For Back Office Team" 
        }
        
      }
      
    ]

    
    read_only_fields = [
      { id = { 
          name = "Expiry Duration"
         } 
      }
    ]

   
    invisible_fields = [
      { id = { 
         name = "Expiry Duration"
        } 
      }
    ]

  }

  

  defaults = [
    {
      id = {
        name = "Type of Work required"
      }
      default_value = "Disney Plus"
    },
    {
      
      id = { 
        name = "For Back Office Team" 
      }
      default_value = "# Mandatory for Back Office Team # "
    },
    {
      
      id = { 
        name = "Expiry Duration" 
      }
      default_value = "129600"
    }
    

  ]

  
tags = [
    for k, v in var.tags : {
      key   = k
      value = v
    }
  ]

}

resource "awscc_connect_task_template" "rb-ccr-pci-task-template2" {
  instance_arn = var.connect_instance_arn
  name         = "Elevations Team Task"
  description  = "Elevations Team Task"
  status       = "ACTIVE"

  contact_flow_arn = var.cfElevationsTaskFlowArn

  fields = [
    {
      description = "Task Name"
      id = {
        name = "Task Name"
      }
      type = "NAME"
    },
     {
      description = "Task Description"
      id = {
        name = "Description"
      }
      type = "DESCRIPTION"
    },
    {
      description = "Type of Work required"
      id = {
        name = "Type of Work required"
      }
      type = "SINGLE_SELECT"
      single_select_options = [
        "Disney Plus",
        "SMB Business Detail Update",
        "Credit Limit Decrease Requests",
        "Wireless Add-a-Line",
        "2x cash back rewards",
        "Preferred Name Request",
        "Delete Digital Profile Request",
        "Bank and Residential Xfinity",
        "Credit Marketing",
        "RLH",
        "2 Percent",
        "Rewards Redemption",
        "Statement Reprint",
        "Account Reinstatement",
        "Collateral Request",
        "Rogers Bank at Rogers Mobile Offer",
        "Welcome Bonus",
        "Manual CB Pull Request - ADM",
        "Credit Balance Refund - Cheque",
        "TSC Dyson 4 Percent Cashback",
        "Fido Student Offer",
        "1 Percent Red SMB Partners Bonus",
        "Rogers Entertainment Credit",
        "World Legend Roam Like Home"
      ]

    },
    
    {
      description = "Agent TSYS ID"
      id = {
        name = "TS2 ID"
      }
      type = "TEXT"
    },
    {
      description = "Account ID"
      id = {
        name = "Account ID"
      }
      type = "TEXT"
    },
    {
      description = "For Elevations Team"
      id = {
        name = "For Elevations Team"
      }
      type = "TEXT_AREA"
    },     
    
    {
      description = "Expiry Duration (seconds)"
      id = { 
        name = "Expiry Duration"
      }
      type = "EXPIRY_DURATION"
    }
    
    
     
]

  constraints = {
    required_fields = [
      {
        id = {
          name = "Task Name"
        }
      },
      {
        id = {
           name = "Description"
        }
      },
      {
        id = {
           name = "Type of Work required"
        }
      },
      {
        id = {
           name = "TS2 ID"
        }
      },
      {
        id = {
           name = "Account ID"
        }
      },
      {
        id = {
           name = "For Elevations Team" 
        }
        
      }
      
    ]

    
    read_only_fields = [
      { id = { 
          name = "Expiry Duration"
         } 
      }
    ]

   
    invisible_fields = [
      { id = { 
         name = "Expiry Duration"
        } 
      }
    ]

  }

  

  defaults = [
    {
      id = {
        name = "Type of Work required"
      }
      default_value = "Disney Plus"
    },
    {
      
      id = { 
        name = "For Elevations Team" 
      }
      default_value = "# Mandatory for Elevations Team # "
    },
    {
      
      id = { 
        name = "Expiry Duration" 
      }
      default_value = "129600"
    }
    

  ]

  
tags = [
    for k, v in var.tags : {
      key   = k
      value = v
    }
  ]

}
