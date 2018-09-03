__author__ = 'dsmirnov@wildapricot.com'

import WaApi
import urllib.parse
import json
import time
def get_specific_id(contactID):
    request_url = contactsUrl + str(contactID)
    return api.execute_request(request_url)
    
def update_specific_id(contactID, lastname):
    data = {
        "Id": str(contactID),
        "LastName": 'B'}
    return api.execute_request(contactsUrl+ str(contactID), api_request_object=data, method='PUT')

def get_all_fields():
    result =api.execute_request(contactfields)
    return([x.FieldName for x in result])




def get_all_members_list():
    params = {'$filter': 'member eq true'}
    request_url = contactsUrl + '?' + urllib.parse.urlencode(params)
    result_info = api.execute_request(request_url, method = 'GET')
    
    request_url = contactsUrl + '?resultID=' + result_info.ResultId
    result = api.execute_request(request_url, method = 'GET')
    return(result.Contacts)

def get_specific_members_list(fields=None):
    if fields is None:
        fields=['User ID','First Name', 'Last Name', 'Email','Spouse First Name', 'Spouse Last Name','Street Address', 'City', 'State', 'Zip Code', 'Last Membership Card Sent Date', 'Membership ID', 'Membership Status','Membership level ID']
    params = {'$filter': 'member eq true',
              '$select': ', '.join(["'"+x+"'" for x in fields])}
    request_url = contactsUrl + '?' + urllib.parse.urlencode(params)
    result_info = api.execute_request(request_url, method = 'GET')
    
    request_url = contactsUrl + '?resultID=' + result_info.ResultId
    result = api.execute_request(request_url, method = 'GET')
    while not result.State=='Complete':
        time.sleep(0.5)
        result = api.execute_request(request_url, method = 'GET')
        
    return(result.Contacts)
    
def process_sub_fields(list_item):
    if list_item.FieldName == 'Membership status'
def process_into_dictionary(contactlist):
    return([{t.FieldName: t.Value for t in s.FieldValues}.update({'MembershipLevel':s.MembershipLevel.Name}) for s in contactlist])
    
def get_member_wihtout_id(contact_dict):
    return [x for x in contact_dict if xMembership ID
    
def get_10_active_members():
    params = {'$filter': 'member eq true',
              '$top': '10',
              '$async': 'false'}
    request_url = contactsUrl + '?' + urllib.parse.urlencode(params)
    print(request_url)
    return api.execute_request(request_url).Contacts


def print_contact_info(contact):
    print('Contact details for ' + contact.DisplayName + ', ' + contact.Email)
    print('Main info:')
    print('\tID:' + str(contact.Id))
    print('\tFirst name:' + contact.FirstName)
    print('\tLast name:' + contact.LastName)
    print('\tEmail:' + contact.Email)
    print('\tAll contact fields:')
    for field in contact.FieldValues:
        if field.Value is not None:
            print('\t\t' + field.FieldName + ':' + repr(field.Value))


def create_contact(email, name):
    data = {
        'Email': email,
        'FirstName': name}
    return api.execute_request(contactsUrl, api_request_object=data, method='POST')


def archive_contact(contact_id):
    data = {
        'Id': contact_id,
        'FieldValues': [
            {
                'FieldName': 'Archived',
                'Value': 'true'}]
    }
    return api.execute_request(contactsUrl + str(contact_id), api_request_object=data, method='PUT')

# How to obtain application credentials: https://help.wildapricot.com/display/DOC/API+V2+authentication#APIV2authentication-Authorizingyourapplication
api = WaApi.WaApiClient("jcr3o65mqy", "sm7nzyjzbnzwgfvkgoef80k9xf9jj7")
api.authenticate_with_contact_credentials("info@cccalbany.org", "CCC11AvisDr@)!^")
accounts = api.execute_request("/v2/accounts")
account = accounts[0]

print(account.PrimaryDomainName)

contactsUrl = next(res for res in account.Resources if res.Name == 'Contacts').Url
contactfields = next(res for res in account.Resources if res.Name == 'Contact fields').Url


# get top 10 active members and print their details
contacts = get_10_active_members()
for contact in contacts:
    print_contact_info(contact)

# create new contact
new_copntact = create_contact('some_email1@invaliddomain.org', 'John Doe')
print_contact_info(new_copntact)

# finally archive it
archived_contact = archive_contact(new_copntact.Id)
print_contact_info(archived_contact)