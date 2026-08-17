import {
    xpPut,
    RequestError
} from '@ccrlayer/common'

const { 
    ENDPOINT,
    BASE_URL
} = process.env

import { FinalResponse } from './model'

export const activateCard = async (accountId: string, customerId: string): Promise<FinalResponse> => {

    const response: FinalResponse = {}
    
    if (!ENDPOINT) throw new RequestError('ENDPOINT is missing!', 406)

    const relUrl: string = ENDPOINT.replace("{accountId}", accountId).replace("{customerId}", customerId)
    const apiEp: string = `${BASE_URL}${relUrl}`
    const res = await xpPut('API_ARN', apiEp, JSON.stringify({ accountId, customerId }))
    
    if (res.status != 200) {
        throw new RequestError(res.data.message, res.status)
    }
    
    const data = res.data
    response.statusCode = `${res.status}`
    response.status = data.activateStatus.status
    response.confirmationNumber = data.activateStatus.confirmationNumber
    response.referenceNumber = data.activateStatus.referenceNumber	

    return response
}