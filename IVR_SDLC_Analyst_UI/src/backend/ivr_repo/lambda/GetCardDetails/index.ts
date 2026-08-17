import {
  RequestError,
  handleError,
  xpGet
} from "@ccrlayer/common"

import {
  EventType,
  ReturnType,
} from "./model"

const {
  CHANNEL,
  X_PLAT_PROFILE_ENDPOINT_URL,
  X_PLAT_CARDDETAILS_URL
} = process.env

export const handler = async (event: EventType): Promise<ReturnType> => {
  let response:ReturnType = {}
  try {

    if (!CHANNEL || !X_PLAT_PROFILE_ENDPOINT_URL || !X_PLAT_CARDDETAILS_URL) {
      throw new RequestError("Invalid env setup", 406)
    }

    const accountId = event.Details.Parameters.accountId
    const customerId = event.Details.Parameters.customerId
    const openDate = event.Details.Parameters.openedDate

    if (!accountId || !customerId) {
      throw new RequestError("Invalid input", 500)
    }

    const apiUrl: string = X_PLAT_PROFILE_ENDPOINT_URL + X_PLAT_CARDDETAILS_URL
      .replace("{accountId}", accountId)
      .replace("{customerId}", customerId)

    const data = await cardDetails(apiUrl, openDate, customerId)  
    response = {...data}

  } catch (err) {    
    const errRes = handleError(err)
    response.statusCode = `${errRes.statusCode}`
    response.message = errRes.message
  }
  return response
}

const cardDetails = async (apiUrl: string, openDate: string, customerId:string): Promise<ReturnType> => {
    let isCardActive:string = " "
    let reissuedReason:string =" "
    let lastIssuedDate:string = " "
    let customerType:string = " "

    const apiRes = await xpGet(apiUrl)
    if (apiRes.status != 200) {
      throw new RequestError(apiRes.data.message, apiRes.status)
    }
    const data = apiRes.data
    const statusCode = data.statusCode
    
    for (const x of data.cardDetails.cardDetails) {
      if(x.identifiers.customerId === customerId ){
        isCardActive = x.cardActivated
        reissuedReason = x.cardRequestReason
        lastIssuedDate = x.lastRequestDate
        customerType = x.customerType
        break
      }
    }
    
    //calculate no of days since last Issued 
    const lastIssueDateDiff: number | undefined = timeDifferenceCalculator(lastIssuedDate)
    
    //Calculates no of days since account opened
    const openDateDiff:number | undefined = timeDifferenceCalculator(openDate)

    return {
      statusCode: statusCode,
      cardActive: String(isCardActive),
      reissuedReason: reissuedReason,
      customerType: customerType,
      lastIssueDate: String(lastIssueDateDiff),
      openDate: String(openDateDiff)
    }
}

function timeDifferenceCalculator(givenDate: string | undefined): number{
    if (!givenDate) {
      return 0
    }
    const date: Date = new Date(givenDate)
    const today: Date = new Date()
    const timeDifference: number = today.getTime() - date.getTime()
    const differenceInDays: number = Math.floor(timeDifference / (1000 * 3600 * 24))
    return differenceInDays
  }


