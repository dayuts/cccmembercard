# -*- coding: utf-8 -*-
"""
Created on Sat Aug 25 15:02:40 2018

@author: Huang
"""
import json
from member import memberdata

cccmemberdata = memberdata.CCCMemberData()
cccmemberdata.initialize_with_credential_json_file('credential.json')
cccmemberdata.load_data()
cccmemberdata.get_new_card_member_contact()
cccmemberdata.write2csv_new_member_card_contact()

cccmemberdata.generate_file_to_print()



