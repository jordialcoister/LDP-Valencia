#!/usr/bin/python
# 
# This file is part of the Lampadas Documentation System.
# 
# Copyright (c) 2000, 2001, 2002 David Merrill <david@lupercalia.net>.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# 
"""
Lampadas HTML Primitives Module

This module generates HTML primitives and web pages for the WWW front-end
to the Lampadas system.
"""

# Modules ##################################################################

from Globals import *
from Config import config
from Log import log
from URLParse import URI

from Tables import tables, tablemap
from Widgets import widgets
from Sessions import sessions

from Lintadas import lintadas
import commands
import string
import sys
import os
import time
import fpformat

from CoreDM import dms

class PageFactory:

    elapsed_time = 0

    def __init__(self):
        dms.preload()

    def page_exists(self, key):
        uri = URI(key)
        if uri.path=='' and dms.page.get_by_id(uri.code):
            return 1
        return

    def page(self, uri):
        if state.session:
            log(3, 'user: ' + state.session.username)

        page = dms.page.get_by_id(uri.page_code)
        if page==None:
            page = dms.page.get_by_id('404')
        html = self.build_page(page, uri)
        return html
    
    def build_page(self, page, uri):
        start_time = time.time()
        template = page.template
        html = template.template

        self.blocks = dms.block.get_all()

        html = self.replace_tokens(page, uri, html)

        end_time = time.time()
        self.elapsed_time = end_time - start_time
        html = html.replace('DCM_ELAPSED_TIME', fpformat.fix(self.elapsed_time, 3))
        html = html.replace('DCM_PIPE', '|')
        return html

    def replace_tokens(self, page, uri, html):
        temp = html.replace('\|', 'DCM_PIPE')
        pos = temp.find('|')
        while pos <> -1 :
            temp = temp.replace('\|', 'DCM_PIPE')
            pos2 = temp.find('|', pos+1)
            if pos2==-1:
                pos = -1
            else:
                token = temp[pos+1:pos2]

                newstring = None

                # System diagnostic tokens
                if token=='elapsed_time':
                    newstring = 'DCM_ELAPSED_TIME'
                    
                # Session Tokens
                elif token=='session_id':
                    if state.session:
                        newstring = state.user.session_id
                    else:
                        newstring = ''
                elif token=='session_username':
                    if state.session:
                        newstring = state.session.username
                    else:
                        newstring = ''
                elif token=='session_name':
                    if state.session:
                        newstring = state.user.name
                    else:
                        newstring = ''
                elif token=='session_user_docs':
                    if state.session:
                        newstring = tables.userdocs(uri, username=state.session.username)
                    else:
                        newstring = self.blocks['blknopermission'].block

                # Page Meta-data
                elif token=='title':
                    newstring = page.title[uri.lang]
                elif token=='body':
                    if page.only_registered==1 and state.session==None:
                        newstring = self.blocks['blknopermission'].block
                    elif page.only_admin==1 and (state.session==None or state.user.admin==0):
                        newstring = self.blocks['blknopermission'].block
                    elif page.only_sysadmin==1 and (state.session==None or state.user.sysadmin==0):
                        newstring = self.blocks['blknopermission'].block
                    else:
                        newstring = page.page[uri.lang]
                elif token=='base':
                    newstring = 'http://' + config.hostname
                    if config.port > '':
                        newstring = newstring + ':' + config.port
                    newstring = newstring + config.root_dir

                # URI Meta-data
                elif token=='uri.lang_ext':
                    newstring = uri.lang_ext
                elif token=='uri.base':
                    newstring = uri.base
                elif token=='uri.page_code':
                    newstring = uri.page_code
                elif token=='uri.id':
                    newstring = str(uri.id)
                elif token=='uri.code':
                    newstring = uri.code
                elif token=='uri.filename':
                    newstring = uri.filename


                # Configuration Tokens
                elif token=='hostname':
                    newstring = config.hostname
                elif token=='rootdir':
                    newstring = config.root_dir
                elif token=='port':
                    newstring = str(config.port)
                elif token=='theme':
                    newstring = config.theme
                elif token=='version':
                    newstring = VERSION

                ###########################################
                # Tokens for when a page embeds an object #
                ###########################################
                
                # Embedded User
                elif token=='user.username':
                    newstring = uri.username
                elif token=='user.name':
                    user = dms.username.get_by_id(uri.username)
                    if user:
                        newstring = user.name
                    else:
                        newstring = ''
                elif token=='user.docs':
                    newstring = tables.userdocs(uri, uri.username)

                # Embedded Type
                elif token=='type.name':
                    type = dms.type.get_by_id(uri.code)
                    if not type:
                        newstring = self.blocks['blknotfound'].block
                    else:
                        newstring = type.name[uri.lang]

                # Embedded Topic
                elif token=='topic.name':
                    topic = dms.topic.get_by_id(uri.code)
                    if not topic:
                        newstring = self.blocks['blknotfound'].block
                    else:
                        newstring = topic.name[uri.lang]
                elif token=='topic.description':
                    topic = dms.topic.get_by_id(uri.code)
                    if not topic:
                        newstring = self.blocks['blknotfound'].block
                    else:
                        newstring = topic.description[uri.lang]

                # Embedded Collection
                elif token=='collection.name':
                    collection = dms.collection.get_by_id(uri.code)
                    if not collection:
                        newstring = self.blocks['blknotfound'].block
                    else:
                        newstring = collection.name[uri.lang]
                elif token=='collection.description':
                    collection = dms.collection.get_by_id(uri.code)
                    if not collection:
                        newstring = self.blocks['blknotfound'].block
                    else:
                        newstring = collection.description[uri.lang]

                # Embedded Document
                elif token=='doc.title':
                    doc = dms.document.get_by_id(uri.id)
                    if doc==None:
                        newstring = self.blocks['blknotfound'].block
                    else:
                        newstring = doc.title
                        if newstring=='':
                            topfile = doc.top_file
                            if topfile:
                                newstring = topfile.title
                elif token=='doc.abstract':
                    doc = dms.document.get_by_id(uri.id)
                    if doc==None:
                        newstring = self.blocks['blknotfound'].block
                    else:
                        newstring = doc.abstract
                        if newstring=='':
                            topfile = doc.top_file
                            if topfile:
                                newstring = topfile.abstract
                
                # Navigation Boxes
                elif token=='navlogin':
                    newstring = tables.navlogin(uri)
                elif token=='navmenus':
                    newstring = tables.section_menus(uri)
                elif token=='navtopics':
                    newstring = tables.navtopics(uri)
                elif token=='navtypes':
                    newstring = tables.navtypes(uri)
                elif token=='navcollections':
                    newstring = tables.navcollections(uri)
                elif token=='navsessions':
                    newstring = tables.navsessions(uri)
                elif token=='navlanguages':
                    newstring = tables.navlanguages(uri)

                # Tables
                elif token=='tabcollections':
                    newstring = tables.tabcollections(uri)
                elif token=='tabcollection':
                    newstring = tables.tabcollection(uri)
                elif token=='tabtopics':
                    newstring = tables.tabtopics(uri)
                elif token=='tabtopic':
                    newstring = tables.tabtopic(uri)
                elif token=='tabmaint_wanted':
                    docs = dms.document.get_by_keys([['maintainer_wanted', '=', 1]])
                    newstring = tables.doctable2(docs)
                elif token=='tabunmaintained':
                    docs = dms.document.get_by_keys([['maintained', '=', 0]])
                    newstring = tables.doctable2(docs)
                elif token=='tabpending':
                    docs = dms.document.get_by_keys([['pub_status_code', '=', 'P']])
                    newstring = tables.doctable2(docs)
                elif token=='tabwishlist':
                    docs = dms.document.get_by_keys([['pub_status_code', '=', 'W']])
                    newstring = tables.doctable2(docs)
                elif token=='tabdocfileerrors':
                    newstring = tables.docfileerrors(uri)
                elif token=='tabfile_reports':
                    newstring = tables.filereports(uri)
                elif token=='tabfile_report':
                    newstring = tables.filereport(uri)
                elif token=='tabdocerrors':
                    newstring = tables.docerrors(uri)

                elif token=='tabeditdoc':
                    newstring = tables.editdoc(uri)
                elif token=='tabeditdocfiles':
                    newstring = tables.editdocfiles(uri)
                elif token=='tabeditdocversions':
                    newstring = tables.editdocversions(uri)
                elif token=='tabeditdoctopics':
                    newstring = tables.editdoctopics(uri)
                elif token=='tabeditdocusers':
                    newstring = tables.editdocusers(uri)
                elif token=='tabeditdocnotes':
                    newstring = tables.editdocnotes(uri)
                elif token=='tabdoctranslations':
                    newstring = tables.doctranslations(uri)
                
                elif token=='tabviewdoc':
                    newstring = tables.viewdoc(uri)
                elif token=='tabviewdocfiles':
                    newstring = tables.viewdocfiles(uri)
                elif token=='tabviewdocversions':
                    newstring = tables.viewdocversions(uri)
                elif token=='tabviewdocusers':
                    newstring = tables.viewdocusers(uri)
                elif token=='tabviewdoctopics':
                    newstring = tables.viewdoctopics(uri)
                elif token=='tabviewdocnotes':
                    newstring = tables.viewdocnotes(uri)

                elif token=='tabcvslog':
                    newstring = tables.cvslog(uri)
                elif token=='tabletters':
                    newstring = tables.letters(uri)
                elif token=='tabusers':
                    newstring = tables.users(uri)
                elif token=='tabuser':
                    newstring = tables.user(uri)
                elif token=='tabtypedocs':
                    docs = dms.document.get_by_keys([['type_code', '=', uri.code]])
                    newstring = tables.doctable2(docs)
                elif token=='tabtopicdocs':
                    topic = dms.topic.get_by_id(uri.code)
                    newstring = tables.doctable2(topic.documents)
                elif token=='tabsitemap':
                    newstring = tables.sitemap(uri)
                elif token=='tabsessions':
                    newstring = tables.tabsessions(uri)
                elif token=='tabmailpass':
                    newstring = tables.tabmailpass(uri)
                elif token=='taberrors':
                    newstring = tables.errors(uri)
                elif token=='tabsearch':
                    newstring = tables.tabsearch(uri, lang=uri.lang)
                elif token=='tabsplashlanguages':
                    newstring = tables.tabsplashlanguages(uri)
                elif token=='tabdocument_tabs':
                    newstring = tables.tabdocument_tabs(uri)
                elif token=='tabdocument_icon_box':
                    newstring = tables.tabdocument_icon_box(uri)
            

                # Tables, Blocks and Strings
                if newstring==None:
                    if tablemap.has_key(token):
                        tablegen = tablemap[token]
                        newstring = tablegen(uri)
                    else:
                        block = dms.block.get_by_id(token)
                        if block==None:
                            webstring = dms.string.get_by_id(token)
                            if webstring==None:
                                log(1, 'Could not replace token ' + token)
                            else:
                                newstring = webstring.string[uri.lang]
                        else:
                            newstring = block.block
                
                # Just use the token if the token was not found
                if newstring==None:
                    log(1, 'Could not replace token ' + token)
                    newstring = token
                
                # Call myself recursively before replacing, so we do replacement on it only once,
                # while it is still small. Replacing text in large pages is more costly on large
                # strings.
                # 
                # Routines that build potentially very large tables should be caching their
                # static portions during page build.
                temp = temp.replace(temp[pos:pos2+1], self.replace_tokens(page, uri, newstring))
                
                temp = temp.replace('\|', 'DCM_PIPE')
                pos = temp.find('|')
        
        return temp
        

page_factory = PageFactory()

def benchmark(url, reps):
    for x in range(0, reps):
        page = page_factory.page(url)

def main():
    import profile
    import pstats

    if len(sys.argv[1:]):
        profile_it = 0
        reps_flag = 0
        profile_reps = 100
        for arg in sys.argv[1:]:
            if reps_flag:
                profile_reps = int(arg)
                reps_flag = 0
            elif arg=='-p' or arg=='--profile':
                profile_it = 1
            elif arg=='-r' or arg=='--reps':
                reps_flag = 1
            elif profile_it > 0:
                print 'Profiling, ' + str(profile_reps) + ' repetitions...'
                page = page_factory.page(arg)
                profile.run('benchmark("' + arg + '", ' + str(profile_reps) + ')', 'profile_stats')
                p = pstats.Stats('profile_stats')
                p.sort_stats('time').print_stats()
            else:
                print page_factory.page(URI(arg))
    else:
        profile()

# USAGE:
#
#   HTML.py page -p --reps 10

if __name__=="__main__":
    main()

