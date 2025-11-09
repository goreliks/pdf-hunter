/**
 * Author: 037
 * return data to the partnerStack
 * 
 */
// get the search string part of the URL
const searchString = document.location.search;
// create a new URLSearchParams instance
const urlSearchParams = new URLSearchParams(searchString);
// get the ClickID from the search params
const partnerStackClickID = urlSearchParams.get('ps_xid');

console.log(partnerStackClickID, partnerStackCustomerKey)
if (partnerStackCustomerKey != 0 && partnerStackClickID) {
    console.log('action')
    requirePartnerLinks(partnerStackClickID, partnerStackCustomerKey);
}

function requirePartnerLinks(xid, customer_key) {
    stackData = {
        "customer_key": customer_key,
        "xid": xid
    };
    var jsonData = JSON.stringify(stackData);
    $.ajax({
        type: 'post',
        url: 'https://partnerlinks.io/conversion/xid',
        data: jsonData,
        dataType: "json",
        beforeSend: function (xhr) {
            xhr.setRequestHeader("Authorization", "Bearer gjCenLmSyEwUXFdSiPxHSLnmOruVD3Jw")
            xhr.setRequestHeader("Content-Type", "application/json")
        },
        success: function (data) {
            console.log('send partnerStack', 'success');
        },
        error: function (data) {
            console.log('send partnerStack', data.status, data.responseJSON);
        }

    });
}
