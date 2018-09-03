# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
Created on Sat Aug 25 14:08:11 2018

@author: Huang
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

#!/bin/python
"""
Hello World, but with more meat.
"""
## Fixed the issue of how to determine a card has expired
## TO DO:Fill in expiration date

import wx
from wx import adv
from member import memberdata
import os

class GaugeExt(wx.Gauge):
    def __init__(self, *args, **kw):
         super(GaugeExt, self).__init__(*args, **kw)
         
    def inc(self):
        self.SetValue(self.GetValue()+1)
        wx.Yield()
        
class CCCMemberCardFrame(wx.Frame):
    """
    A Frame for CCC member card Printing
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(CCCMemberCardFrame, self).__init__(*args, **kw)

        # create a panel in the frame
        #pnl = wx.Panel(self)
        
        

        # and put some text with a larger bold font on it
        #st = wx.StaticText(pnl, label="Hello World!", pos=(25,25))
        #font = st.GetFont()
        #font.PointSize += 10
        #font = font.Bold()
        #st.SetFont(font)

        # create a button
        self.button_load_member_list = wx.Button(self, label='1. Load Member List', style =wx.BU_EXACTFIT)
        self.button_load_member_list.Bind(wx.EVT_BUTTON, self.OnButton_load_member_list)
        self.text_total_member = wx.StaticText(self, label="Number of member data records: TBD", pos=(0, 30))
        self.text_new_member = wx.StaticText(self, label="Number of members requiring new cards: TBD", pos=(0,60))        
        self.url_member_csv = adv.HyperlinkCtrl(self, label="csv (table) file of info of members requiring new card: Not Generated",
                                              url = '',
                                              pos=(0,90))
        
        
        
        self.button_create_letter_and_card_file = wx.Button(self, label='2. Create Card and Letter File', pos=(0,120), style =wx.BU_EXACTFIT)
        self.button_create_letter_and_card_file.Bind(wx.EVT_BUTTON, self.OnButton_create_letter_and_card_file)
        
        self.url_card_pdf = adv.HyperlinkCtrl(self, label="pdf file for card: Not Generated",
                                              url = '',
                                              pos=(0,150))
        
        self.url_letter_pdf = adv.HyperlinkCtrl(self, label="pdf file for letter: Not Generated",
                                              url = '',
                                              pos=(0,180))
        
        #file:///D:/proj/cccmembercard/output/2018-09-02_13_43_30/letter_to_print.pdf',
        self.button_update = wx.Button(self, label='3. Update Membership Card Last Sent Date To Website', pos=(0,210), style =wx.BU_EXACTFIT)
        self.button_update.Bind(wx.EVT_BUTTON, self.OnButton_update_website)
                         
        self.gauge_load_status = GaugeExt(self, pos=(200,5), range=4)
        self.gauge_file_status = GaugeExt(self, pos=(200,125), range=50)
        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Follow steps to print card. Click Step 1")
        self.cccmember = memberdata.CCCMemberData()
        

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)
    
    def OnButton_load_member_list(self, event):
        self.SetStatusText("Loading data from CCC website")
        self.gauge_load_status.inc()
        self.cccmember.initialize_with_credential_json_file('credential.json')
        self.gauge_load_status.inc()
        self.cccmember.load_data(progbar=self.gauge_load_status)        
        if self.cccmember.data is not None:
            self.text_total_member.SetLabel("Number of member data records: %d" % len(self.cccmember.data))
            self.cccmember.get_new_card_member_contact()
            self.text_new_member.SetLabel("Number of new members requiring cards: %d" % len(self.cccmember.member_new_card))
            self.cccmember.write2csv_new_member_card_contact()
            csv_path = os.path.abspath( self.cccmember.output_path['member_csv'])
            self.url_member_csv.SetURL('file:///'+csv_path)
            self.url_member_csv.SetLabel("csv (table) file of info of members requiring new card: Click to View")            
            self.Layout()            
            wx.MessageBox("Data loaded from website: %s Records" % len(self.cccmember.data))
        else:            
            wx.MessageBox("Unable to load data from website")
        self.SetStatusText("Follow steps to print card. Click Step 2 to generate Files")
            
    def OnButton_create_letter_and_card_file(self, event):
        self.SetStatusText("Generate files to print.")
        if self.cccmember.member_new_card is None:
             wx.MessageBox("No new card info is available")
        else:
            self.gauge_file_status.SetRange(len(self.cccmember.member_new_card)*2+5)
            self.gauge_file_status.inc()
            self.cccmember.generate_file_to_print(progbar=self.gauge_file_status)
            self.gauge_file_status.inc()
            
            card_path = os.path.abspath( self.cccmember.output_path['card_pdf'])
            letter_path = os.path.abspath( self.cccmember.output_path['letter_pdf'])

            self.url_card_pdf.SetURL('file:///'+card_path)
            self.url_letter_pdf.SetURL('file:///'+letter_path)
            self.url_card_pdf.SetLabel("pdf file for card: Click to View")
            self.url_letter_pdf.SetLabel("pdf file for letter: Click to View")            
            self.Layout()
                                    
            
            
            wx.MessageBox("File generated")
        self.SetStatusText("Follow steps to print card. Double check to makes sure you have the files. Click Step 3 to update the data back to the website")
        
    def OnButton_update_website(self, event):
        self.SetStatusText("Update website")
        #self.cccmember.update_card_sent_info_to_web()
        wx.MessageBox("Updated Website")        

    def OnHello(self, event):
        """Say hello to the user."""
        wx.MessageBox("CCC Membership Card Printing")


    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is program to prepare files for membership card", wx.OK)


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = CCCMemberCardFrame(None, title='CCC Membership Card Printing Assistant', size=(500, 300))
    frm.Show()
    app.MainLoop()
