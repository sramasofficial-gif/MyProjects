import {
    RequestError,
    handleError,
    xpGet
} from "@ccrlayer/common"

import {
    EventType,
    ReturnType
} from "./model"

const {
    X_PLAT_PROFILE_ENDPOINT_URL,
    X_PLAT_COREBANK_ENDPOINT_URL,
    CHANNEL,
    X_PLAT_CARDDETAIL_URL,
    X_PLAT_PRIMARYUSER_URL,
} = process.env


export const handler = async (event: EventType): Promise<ReturnType> => {
    let response: ReturnType = {}
    try {
        if (!CHANNEL || !X_PLAT_PROFILE_ENDPOINT_URL || !X_PLAT_COREBANK_ENDPOINT_URL || !X_PLAT_PRIMARYUSER_URL || !X_PLAT_CARDDETAIL_URL) {
            throw new RequestError("Invalid env", 406)
        }
        const accountId: string = event.Details.Parameters.accountId
        const customerId: string = event.Details.Parameters.customerId

        if (!accountId || !customerId) {
            throw new RequestError("Invalid input", 406)
        }
        const data: ReturnType = await primaryCard(accountId, customerId, X_PLAT_COREBANK_ENDPOINT_URL, X_PLAT_PRIMARYUSER_URL, X_PLAT_PROFILE_ENDPOINT_URL, X_PLAT_CARDDETAIL_URL)
        response = {...data}

    } catch (err: any) {        
        const errRes = handleError(err)        
        response.statusCode = `${errRes.statusCode}`
        response.message = errRes.message
    }
    return response
}

const primaryCard = async (accountId: string, customerId:string, coreUrl:string, pUserUrl:string, profileUrl:string, cardDetail:string): Promise<ReturnType> => {

    const primUserUrl: string = `${coreUrl}${pUserUrl}`
            .replace("{accountId}", accountId)
            .replace("{customerId}", customerId)
    

    const apiCoreRes = await xpGet(primUserUrl)
    if (apiCoreRes.status != 200) {
        throw new RequestError(apiCoreRes?.data.message, apiCoreRes.status)
    }
    const coreData = apiCoreRes.data;
    // const statusCode = coreData.statusCode
    const primaryCardDetails = coreData.accountCardDetails.customerInfo.customerList

    let isPrimaryActive: string = "false"
    let newCustomerId: string | null = null

    for (const x of primaryCardDetails) {
        if (x.customerType === "PRIMARY") {
            newCustomerId = x.customerId
            break
        }
    }

    const cardUrl = `${profileUrl}${cardDetail}`
        .replace("{accountId}", accountId)
        .replace("{customerId}", newCustomerId!)

    const apiPorfileRes = await xpGet(cardUrl)

    if (apiPorfileRes.status != 200) {
        throw new RequestError(apiPorfileRes?.data.message, apiPorfileRes.status)
    }

    const profileData = apiPorfileRes.data
    if (profileData?.cardDetails?.cardDetails && profileData?.cardDetails?.cardDetails.length<0) {
        throw new RequestError("Primary cust not found", apiPorfileRes.status)
    }else{
        for (const x of profileData.cardDetails.cardDetails) {
            if(x.identifiers.customerId === newCustomerId)
                isPrimaryActive = x.cardActivated ? "true" : "false"   
            break             
    }
    }  
    
    const response: ReturnType = {
        statusCode: `${apiPorfileRes.status}`,
        isPrimaryActive: isPrimaryActive,
        newCustomerId: newCustomerId
    }
    return response
}