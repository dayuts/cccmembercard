from member import WaApi
import urllib.parse
import json
import time
import numpy as np
import pandas as pd

from fdfgen import forge_fdf
import os
import sys
import tempfile
from datetime import datetime
from dateutil import relativedelta
import subprocess
import dateutil
from dateutil import tz
import logging
import pandas as pd
import pdb


def _discard_member_with_incomplete_information(contact_dict):
    return([x for x in contact_dict if not x["City"]==''])
def _add_id(contact_dict, max_regular_id, max_lifemember_id):
    c_regular_id = max_regular_id
    c_life_id = max_lifemember_id
    for jj in range(0,len(contact_dict)):
        if contact_dict[jj]["MembershipLevel"] in ['Family Member', 'Individual Member', 'Student Member']:
            c_regular_id=c_regular_id+1            
            contact_dict[jj]["Membership ID"] = 'U'+'0'*(5-len(str(c_regular_id)))+str(c_regular_id)
        elif contact_dict[jj]["MembershipLevel"] in ['Lifetime Member']:
            c_life_id = c_life_id+1
            contact_dict[jj]["Membership ID"] = 'U'+'0'*(5-len(str(c_life_id)))+str(c_life_id)
        else:
            pass
    return contact_dict, c_regular_id, c_life_id
def _remove_spousename_if_same_as_main(contact_dict):
    output_list = []
    for x in contact_dict:
        y = x
        if 'Spouse First Name' in y:
            if y['Spouse First Name']==y['First name'] and y['Spouse Last Name']==y['Last name']:
                # remove Spouse's name is the name is identical.
                y['Spouse First Name']=''
                y['Spouse Last Name']=''
        output_list.append(y)
    return output_list


def _prepare_card_data(contact_dict, expiration_date):
    data =  []
    for x in contact_dict:
        field = []
#            field.append(('MEM_ID', x["Membership ID"]))
#            field.append(('MEMBER_NAME', (x['First name']+x['Last name'])))
#            if 'Spouse First Name' in x:
#                field.append(('SPOUSE_NAME', (x['Spouse First Name']+x['Spouse Last Name'])))
#            field.append(('MEM_TYPE', x['MembershipLevel']))
        
        # previous fdfgen has a bug that requires the key to be encoded. It is fixed after Sep 2016. 
        #field.append(('MEM_ID'.encode('utf-8'), x["Membership ID"]))
        #field.append(('MEMBER_NAME'.encode('utf-8'), (x['First name']+' ' + x['Last name']).upper()))
        field.append(('MEM_ID', x["Membership ID"]))
        field.append(('MEMBER_NAME', (x['First name']+' ' + x['Last name']).upper()))
        if 'Spouse First Name' in x:
            #field.append(('SPOUSE_NAME'.encode('utf-8'), (x['Spouse First Name']+' '+x['Spouse Last Name']).upper()))
            field.append(('SPOUSE_NAME', (x['Spouse First Name']+' '+x['Spouse Last Name']).upper()))
        #field.append(('MEM_TYPE'.encode('utf-8'), x['MembershipLevel']))
        field.append(('MEM_TYPE', x['MembershipLevel']))
        field.append(('EXPIRATION', expiration_date.strftime('%Y.%m.%d')))                        
        
        data.append(field)
        if 'Spouse First Name' in x: # two cards for two people in a family
            if not (x['Spouse First Name'] is None or x['Spouse First Name']==''):
                data.append(field)            
    return(data)

def _prepare_letter_data(contact_dict):
    data =  []
    for x in contact_dict:
        field = []           
        
        #field.append(('MEM_ID'.encode('utf-8'), x["Membership ID"]))
        #field.append(('FIRSTNAME'.encode('utf-8'), x['First name'].title()+', ')) 
        #field.append(('EMAIL'.encode('utf-8'), x["Email"]))
        #field.append(('FULLNAME'.encode('utf-8'), 'To: '+(x['First name']+' '+x['Last name']).title()))
        #field.append(('STREET'.encode('utf-8'), x['Street Address'].title()))            
        #field.append(('CITYPAIR'.encode('utf-8'), x['City'].title()+', '+ x['State'].Label+ ' '+x['Zip Code']))
        field.append(('MEM_ID', x["Membership ID"]))
        field.append(('FIRSTNAME', x['First name'].title()+', ')) 
        field.append(('EMAIL', x["Email"]))
        field.append(('FULLNAME', 'To: '+(x['First name']+' '+x['Last name']).title()))
        field.append(('STREET', x['Street Address'].title()))            
        field.append(('CITYPAIR', x['City'].title()+', '+ x['State']+ ' '+x['Zip Code']))        
        data.append(field)
    return(data)

def _form_fill(fields, pdf_file, temp_folder, count, pdftk_path, logger=None):
    tmp_file, filename = tempfile.mkstemp()
    if logger:
        logger.info('Fill form fields %s' %(str(fields)))
    
    fdf = forge_fdf("",fields,[],[],[])   
    fdf_file = open(tmp_file,"wb") 
    fdf_file.write(fdf)                     
    fdf_file.close()
    output_file = '%s\\k %05d.pdf'%(temp_folder, count)
    
    cmd = '{0} "{1}" fill_form "{2}" output "{3}" flatten dont_ask'.format(pdftk_path, pdf_file, filename, output_file)
    cmd_status = subprocess.call(cmd, shell=True)      
    if logger:
        logger.info('pdf cmd %s %s' %(cmd, str(cmd_status)))
    os.remove(filename)    
    

def _form_fill_wrapper(data, pdf_file, final_output_file, pdftk_path, logger=None, progbar=None):
    temp_folder = tempfile.mkdtemp()
    count = 0
    for xrecord in data:         
        _form_fill(xrecord, pdf_file, temp_folder, count, pdftk_path, logger=logger)
        if progbar is not None: progbar.inc()
        count = count+1        
        
    cmd = '{0} {1}/*.pdf cat output {2}'.format(pdftk_path, temp_folder, final_output_file)
    cmd_status = subprocess.call(cmd, shell=True)      
    if progbar is not None: progbar.inc()
    if logger:
        logger.info('pdf cmd %s %s' %(cmd, str(cmd_status)))    
def _process_into_dictionary(contactlist):
    """ Process the Wildapricot API returned id into dictionary
    
    Args:
        contactlit (list): list of contact return by wildapricot API
        
    Returns:
        list of contact dictionaries
    """
        
    output = []
    for s in contactlist:
        p={t.FieldName: t.Value for t in s.FieldValues}
        p.update({'MembershipLevel':s.MembershipLevel.Name}) 
        p.update({'ID':s.Id}) 
        if 'State' in p.keys() and p['State'] is not None:
            p.update({'State': p['State'].Label})
        if 'Membershpip status' in p.keys() and p['Membership status'] is not None:
            p.update({'Membershpip Status': vars(p['Membership status'])['Value']})
        output.append(p)        
    return(output)  
    
    
    
def _add_card_sent_date(contact_dict, timestamp):
    """ add card sent date to the dictionary
    """
    for jj in range(0,len(contact_dict)):
        contact_dict[jj]['Last Membership Card Sent Date']=timestamp.strftime('%Y-%m-%dT00:00:00')
    return(contact_dict)    
class CCCMemberData:

    
    def __init__(self, path_config_json=None, path_config=None):
        self.api = None
        self.contactsUrl = None
        self.data = None  
        self.member_new_card = None
        self.card_template_file = 'card_letter_template/CCCMembershipCard_front_template.pdf'
        self.letter_template_file = 'card_letter_template/MembershipLetter_template.pdf'
        self.pdftk_path = '"pdftk/pdftk.exe"'        
        self.logging_path = 'output/membercard.log'        
        self.output_base_dir = 'output/'        
        self.timestamp = datetime.now()
        self.output_dir = self.output_base_dir + '/' + self.timestamp.strftime('%Y-%m-%d_%H_%M_%S');
        
        
        self.update_path(path_config_json=path_config_json, path_config=path_config)
        
        today_midnight = self.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        member_card_resent_date = today_midnight.replace(month=7, day=1)
        if member_card_resent_date >= today_midnight:
            member_card_resent_date = member_card_resent_date - relativedelta.relativedelta(years=1)        
        self.member_card_resent_date = member_card_resent_date
        self.member_card_expiration_date = self.member_card_resent_date + relativedelta.relativedelta(years=1) - relativedelta.relativedelta(days=1) 
        
        self.output_path = dict()        
        self.logger = logging.getLogger('card_application')
        self.logger.setLevel(logging.DEBUG)            
        # create file handler which logs even debug messages
        fh = logging.FileHandler(self.logging_path)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        # add the handlers to the logger
        self.logger.addHandler(fh)
    def update_path(self, path_config_json=None, path_config=None):
        """ Update path setting from config file
        """
        
        if (path_config is None) and (path_config_json is not None):        
            with open(path_config_json, 'r') as file:
                path_config = json.load(file)
        if path_config:
            if 'card_template_file' in path_config.keys():
                self.card_template_file = path_config['card_template_file']
            if 'letter_template_file' in path_config.keys():
                self.letter_template_file = path_config['letter_template_file']
            if 'pdftk_path' in path_config.keys():
                self.pdftk_path = path_config['pdftk_path']
            if 'logging_path' in path_config.keys():
                self.logging_path = path_config['logging_path']        
            if 'output_base_dir' in path_config.keys():
                self.output_base_dir = path_config['output_base_dir']  
                self.output_dir = self.output_base_dir + '/' + self.timestamp.strftime('%Y-%m-%d_%H_%M_%S');
            if 'output_dir' in path_config.keys():
                self.output_dir = path_config['output_dir']  
        
    def initialize_with_credentials(self, credential):
        """ initialize member data with credentials provided
        
        Args:
            credential (dict): dictionary holding credential information            
        """
        self.logger.info('Connect to WildApricot API')
        self.api = WaApi.WaApiClient(credential['client_id'],
                                     credential['client_secret'])                                                                         
        try:
          self.api.authenticate_with_contact_credentials(credential['username'],
                                                          credential['password'])        
        
          accounts = self.api.execute_request("/v2/accounts")
          account = accounts[0]
          self.contactsUrl = next(res for res in account.Resources if res.Name == 'Contacts').Url
          return True
        except Exception:
          self.logger.exception("Unable to initialize connection with wildapricot") 
          return False
        
    def initialize_with_credential_json_file(self, file_name):
        """ initialize member data with credentials stored in json file
        
        Args:
            file_name (str): filename of the json file for credential
            
        """     
        self.logger.info('Load credential from {}'.format(file_name))
        with open(file_name, 'r') as file:
            credentials = json.load(file)        
        return self.initialize_with_credentials(credentials)            

    def _get_specific_members_list(self, fields=None):
        if fields is None:
            fields=['User ID','First Name', 'Last Name',
                    'Email','Spouse First Name', 'Spouse Last Name',
                    'Street Address', 'City', 'State', 'Zip Code', 
                    'Renewal date last changed', 
                    'Renewal due',                    
                    'Last Membership Card Sent Date', 'Membership ID', 'Membership Status',
                    'Membership level ID']
        params = {'$filter': 'member eq true',
                  '$select': ', '.join(["'"+x+"'" for x in fields])}
        request_url = self.contactsUrl + '?' + urllib.parse.urlencode(params)
        result_info = self.api.execute_request(request_url, method = 'GET')
        
        request_url = self.contactsUrl + '?resultID=' + result_info.ResultId
        self.logger.info('Retrive member infomation from WildApricot API')
        result = self.api.execute_request(request_url, method = 'GET')
        while not result.State=='Complete':
            time.sleep(0.5)
            result = self.api.execute_request(request_url, method = 'GET')
            
        return(result.Contacts)

 
        
    def load_data(self, progbar=None):
        """ load member data            
        
        Returns:
            (boolean) : True if successfully loaded
        """
        try:            
            contact_raw_data = self._get_specific_members_list()
            if progbar is not None:                
                progbar.inc()
            self.logger.info('Process member information into dictionary')
            self.data = _process_into_dictionary(contact_raw_data)            
            self.logger.info('Load data finished')
            if progbar is not None:
                progbar.inc()          
            return True
        except:
            return False
        
    
        
    def _get_largest_regular_member_id(self):
        """ Return the largest regular member id
        
        Returns:
            (int): member id, None if no regular member found
        """
        try:
            all_id = [x["Membership ID"] for x in self.data if x["MembershipLevel"] in ['Family Member', 'Individual Member', 'Student Member', 'Lifetime Member']]
            max_id = max([int(a[1:]) for a in all_id if not a is None and not a=='' and not (a[1]).isalpha()])                        
            return max_id
        except:
            return None
        
    def _get_largest_life_member_id(self):
        """ Return the largest life member id
        
        Returns:
            (int): member id, None if no regular member found
        """        
        try:
            all_lifemember_id = [x["Membership ID"] for x in self.data if x["MembershipLevel"]=='Lifetime Member']
            max_lifemember_id = max([int(a[1:]) for a in all_lifemember_id if not a is None and not a==''])              
            return max_lifemember_id
        except:
            return None        
       
    
    def get_member_without_id(self):
        """ return member dictionary that does not have id
        """
        return([x for x in self.data 
                if x["MembershipLevel"] in ['Family Member', 'Individual Member', 'Student Member', 'Lifetime Member'] 
                and (x["Membership ID"] is None or x["Membership ID"]=='') 
                and x['Membership status'].Value =='Active'])

    def get_member_withid_without_card(self):
        """ return member dictionary that does not have card
        """

        
        contact_list = (
            [
                x for x in self.data 
                if (
                    #(x["MembershipLevel"] in ['Family Member', 'Individual Member', 'Student Member']
                    #    and not (x["Membership ID"] is None or x["Membership ID"]=='')
                    #    and (x['Membership status'].Value =='Active')
                    #    and (
                    #            (x['Last Membership Card Sent Date'] is None)                          
                    #            or (datetime.strptime(x['Last Membership Card Sent Date'], '%Y-%m-%dT00:00:00') <
                    #                dateutil.parser.parse(x['Renewal due'])-relativedelta.relativedelta(years=1)
                    #                )
                    #        )
                    #)
                    #or 
                    (x["MembershipLevel"] in ['Family Member', 'Individual Member', 'Student Member', 'Lifetime Member']
                        and not (x["Membership ID"] is None or x["Membership ID"]=='')
                        and (x['Membership status'].Value =='Active')
                        and (
                                (x['Last Membership Card Sent Date'] is None)                          
                                or (datetime.strptime(x['Last Membership Card Sent Date'], '%Y-%m-%dT00:00:00') <
                                    self.member_card_resent_date
                                    )
                            )
                        )
                        )
            ])
        return contact_list   

    def get_new_card_member_contact(self):
        """ Return the list of member contacts with new card and new id generated
        """
        self.logger.info('Extract list of members that need new card')
        member_wihtout_card = self.get_member_withid_without_card()
        member_without_id = _discard_member_with_incomplete_information(self.get_member_without_id())

        max_regular_id = self._get_largest_regular_member_id()
        max_life_id = self._get_largest_life_member_id()
        # generate new id
        member_added_id, new_id_max, new_life_max = _add_id(member_without_id, max_regular_id,max_life_id)
        members_selected = member_added_id + member_wihtout_card
        members_selected_filtered = _remove_spousename_if_same_as_main(members_selected)
        
        #sort member id
        members_selected_filtered_dict_fmt = {w['Membership ID']:w for w in members_selected_filtered}
        members_selected_filtered_sorted = [w[1] for w in sorted(members_selected_filtered_dict_fmt.items())]        
        self.member_new_card = members_selected_filtered_sorted
        self.logger.info('Number of members needing new card is {}'.format(len(self.member_new_card)))

               
    def write2csv_new_member_card_contact(self):
        """ Generate csv file for new card
        """
        if self.member_new_card is None:
            self.logger.error('A list of new member card info is not available yet. Can not generate csv file.')
        else:
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
            self.output_path['member_csv'] = self.output_dir+'/members_requiring_new_card.csv'
            new_card_df = pd.DataFrame(self.member_new_card)
            column_to_print_list = [                    
                    'First name', 'Last name',
                    'Email','Spouse First Name', 'Spouse Last Name',
                    'Street Address', 'City', 'State', 'Zip Code', 
                    'Membership ID',
                    'MembershipLevel',
                    'Renewal date last changed', 
                    'Profile last updated',
                    'Renewal due',                    
                    'Membership Status',
                    'Last Membership Card Sent Date',                     
                    'User ID'
                    ]
            
            new_card_df.loc[:, new_card_df.columns.isin(column_to_print_list)].to_csv(self.output_path['member_csv'])
            #pdb.set_trace()
            #return new_card_df
            #new_card_df.to_csv(self.output_path['member_csv'])
            
        
            
    
    def generate_file_to_print(self, progbar=None):        
        """ Generate card and letter pdf file
        
        Args:
            dir_name (str): directory for output files
                Default: '../output/'
        """
        self.logger.info('Prepare card data')
        if self.member_new_card is None:
            self.logger.error('A list of new member card info is not available yet. Can not generate file to print.')
        else:                        
            card_data = _prepare_card_data(self.member_new_card, expiration_date=self.member_card_expiration_date)
            letter_data = _prepare_letter_data(self.member_new_card)
            if progbar is not None: progbar.inc()                                  
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
           
            self.output_path['card_pdf'] = self.output_dir+'/card_to_print.pdf'
            self.logger.info('Generate card pdf at {}'.format(self.output_path['card_pdf']))              
            _form_fill_wrapper(card_data, self.card_template_file,  self.output_path['card_pdf'], 
                               self.pdftk_path, self.logger, progbar=progbar)
            self.output_path['letter_pdf'] = self.output_dir+'/letter_to_print.pdf'
            self.logger.info('Generate letter pdf at {}'.format(self.output_path['letter_pdf']))
            _form_fill_wrapper(letter_data, self.letter_template_file, self.output_path['letter_pdf'],
            self.pdftk_path, self.logger, progbar=progbar)
    
    def update_card_sent_info_to_web(self):
        """ update card sent info to the web
        
        """
        self.logger.info('Update card info to the web')
        if self.member_new_card is not None:            
            member_added_id_date = _add_card_sent_date(self.member_new_card, self.timestamp)        
    
            result_list = []
            chunk_size = 50
            for k in range(0, len(member_added_id_date), chunk_size):        
                result0 =  self.update_card_id_and_date(member_added_id_date[k: k+chunk_size])
                result_list.append(result0)
                time.sleep(60)
            self.web_update_status = result_list


    def get_member_from_id_range(self, contact_dict, id_range):
        return([x for x in self.data if x["MembershipLevel"] in ['Family Member', 'Individual Member', 'Student Member', 'Lifetime Member'] and (x["Membership ID"] in id_range)])

    

        
    def update_specific_id_membershipID(self, fields):
        contactID = fields['ID']
        data = {
            "Id": str(contactID),
            "FieldValues":[
                {"FieldName":'Membership ID', "Value":fields['Membership ID']},
                {"FieldName":'Last Membership Card Sent Date', "Value":fields['Last Membership Card Sent Date']}
                            ]}
            
        request = urllib.request.Request(self.contactsUrl+ str(contactID),method='PUT')
        request.data=json.dumps(data).encode()
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        request.add_header('Authorization', 'Bearer '+ self.api._get_access_token())
        response = urllib.request.urlopen(request) 
        return(response)    
        
    def update_card_id_and_date(self, contact_dict):
        """ update card id and date information
        """
        responselist = []
        for fields in contact_dict:
            
            response = self.update_specific_id_membershipID(fields)
            responselist=responselist+[response]
        return responselist
            

