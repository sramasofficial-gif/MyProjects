import { AxiosResponse } from "axios";

import {
    RequestError,
    handleError,
    xpGet
} from "@ccrlayer/common"

import { FinalResponse, Event, ApiResponse } from "./model"

const {
    ENDPOINT,
    X_PLAT_APIGATEWAY_URL,
} = process.env;

export const handler = async (event: Event): Promise<FinalResponse> => {
    const response: FinalResponse = { statusCode: 500 };
    try {
        if (!ENDPOINT || !X_PLAT_APIGATEWAY_URL) {
            throw new RequestError("Invalid env setup", 406)
        }
        
        const {accountId,customerType,customerId } =  event.Details.Parameters
    
        if (!accountId || !customerType || !customerId) {
            throw new RequestError("Invalid env input", 406)
        }

        const endpoint: string = X_PLAT_APIGATEWAY_URL + ENDPOINT.replace("{accountId}", accountId).replace("{customerType}", customerType);
        const apiRes = await xpGet(endpoint) as AxiosResponse;

        if (apiRes.status != 200) {
            throw new RequestError(apiRes.data.message, apiRes.status)
        }

        const data: ApiResponse = apiRes.data;
        response.statusCode = 404

        if (data?.accountInformation?.customerList && data?.accountInformation?.customerList.length > 0) {
            response.statusCode = data.statusCode;
            const customerList = data.accountInformation.customerList;
            for (const x of customerList) {
                if(x.customerId === customerId ){
                    response.dateOfBirth = x.dateOfBirth ? x.dateOfBirth : "undefined";
                    response.accountId = x.accountId ? x.accountId : "undefined";
                    response.customerType = x.customerType ? x.customerType : "undefined";
        }
    }
    }
    } catch (err) {        
        const errRes = handleError(err)
        response.statusCode = errRes.statusCode
        response.message = errRes.message
    }
    return response;
}
