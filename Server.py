from zipfile import ZipFile as z
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import sys
import os
import time
import random
import zlib

# Init user settings
global Bad_level_filter
global Server_port
global Random_levels
global No_intro
with open("Settings.txt","r") as settings:
    Bad_level_filter = settings.readline().replace("\n","").split(" = ")[1].lower()
    Server_port = settings.readline().replace("\n","").split(" = ")[1].lower()
    Random_levels = settings.readline().replace("\n","").split(" = ")[1].lower()
    No_intro = settings.readline().replace("\n","").split(" = ")[1].lower()
#

# Trace function instead of print so all prints can be disabled with the blink of an eye.
dev=True
def tr(i):
    if dev:
        print(("%s"%i)[:100])
#

# Gets the leveldata from zip file
global leveldata
with z("Data/leveldata.zip","r") as zipped:
    zipped = zipped.open("leveldata.txt")
    leveldataunitraw = zipped.read().split("\n")
    leveldataunit=[]
    leveldatazero=[]

    # Temp fix for double \n
    for i in leveldataunitraw:
        if len(i)>6:
            leveldataunit.append(i)
    #

                    
    leveldata=[]

    leveldataIDS=[]

    for i in leveldataunit:
        leveldataIDS.append(i[0])
    

    for i in leveldataunit:
        leveldata.append(i.split("|"))

    for x in range(0,len(leveldata)-1):
        leveldatazero.append(leveldata[x][0])
    
#                                 #



tr("Done loading level data,")
class S(BaseHTTPRequestHandler):

    def savedata(self, datatype, mode, data="", encryption=False):
        with open("Savedata/%s.txt"%datatype,"rb") as file_r:
            file_r = file_r.read()
        if encryption:
            try:
                file_r = zlib.decompress(file_r)
            except:
                pass
        file_r = str(file_r)
        if mode == "add":
            if str(data) not in file_r.split("\n"):
                if len(file_r) == 0:
                    file_r+=str(data)
                else:
                    file_r+="\n"+str(data)
                with open("Savedata/%s.txt"%datatype,"wb") as file_w:
                    if encryption:
                        file_w.write(zlib.compress(file_r))
                    else:
                        file_w.write(file_r)
            else:
                tr("savedata is already in file.")
        elif mode == "remove":
            file_r=file_r.split("\n")
            del file_r[file_r.index(str("data"))]
            file_restore=""
            for i in file_r:
                file_restore+="\n"+str(i)
            file_restore = file_restore[1:]
            with open("Savedata/%s.txt"%datatype,"wb") as file_w:
                if encryption:
                    file_w.write(zlib.compress(file_restore))
                else:
                    file_w.write(file_restore)
        elif mode == "read":
            return file_r.split("\n")
    
    def makesearch(self, data, searchtype):
        result = ""
        
        basemessage ='''
        <tr>
        <td><a href="http://localhost/M_LEVELID/pick">M_LEVELNAME</a></td>
        <td>By M_AUTHOR &nbsp;</td>
        <td>Index: M_LEVELID</td>
        </tr>'''

        tr(data)

        for i in data:
            cur_data = leveldata[i]

            M_AUTHOR="%s"%cur_data[5]
            M_LEVELNAME="%s"%cur_data[1]
            M_LEVELID=str(i)

            b = basemessage.replace("M_AUTHOR",M_AUTHOR)
            b = b.replace("M_LEVELNAME",M_LEVELNAME)
            b = b.replace("M_LEVELID",M_LEVELID)
            
            result+="%s"%b

        with open("Data/Search.html","r") as searchhtml:
            s = searchhtml.read()

        s = s.replace("M_SEARCHSPOT",str(result))
        s = s.replace("M_COPYRIGHT","Bloonsworld Archive")
        s = s.replace("M_LEVELCOUNT",str(len(data)))
        
        if searchtype == "author":    
            s = s.replace("M_AUTHOR","%s"%M_AUTHOR)
            s = s.replace("M_BELOW","%s's levels:"%M_AUTHOR)
        elif searchtype == "levelname":
            s = s.replace("M_AUTHOR","Search results")
            s = s.replace("M_BELOW","")
        
        return s
        
    

    def search(self, want, itemtype, strict=False):
        results=[]
        if itemtype.lower() == "author":
            index = 5
        if itemtype.lower() == "levelname":
            index = 1
        try:
            if strict == False:
                for i in range(0, len(leveldata)-1):
                    if str(want).lower().replace("_"," ") in str(leveldata[i][index]).lower().replace("_"," "):
                        results.append(i)
            elif strict == True:
                for i in range(0, len(leveldata)-1):
                    if str(want).lower().replace("_"," ") == str(leveldata[i][index]).lower().replace("_"," "):
                        results.append(i)
        except:
            tr(leveldata[i+1])
        return results


    def postdict(self, x): # turn stuff like potato=123&cool=yo into dict
        x=str(x)
        dict1={}
        if "&" in x:
            x=x.split("&")
            for m in x:
                m=m.split("=")
                dict1[str(m[0])] = str(m[1])
        else:
            x=x.split("=")
            dict1[str(x[0])] = str(x[1])
        return dict1

    def mime(x,path):
        mimetype=None
        if path.endswith(".css"):
            mimetype="text/css"
        elif path.endswith(".html"):
            mimetype="text/html"
        elif path.endswith(".swf"):
            mimetype="application/x-shockwave-flash"
        elif path.endswith(".gif"):
            mimetype="image/gif"
        elif path.endswith(".png"):
            mimetype="image/png"
        elif path.endswith(".ico"):
            mimetype="image/x-icon"
        if mimetype == None:
            mimetype="text/html"
            tr("mimetype undefined")
        return mimetype

    def makeplay(self, html, index=None, message="Welcome to Bloonsworld Archive!"):

        if index==None:
            index=random.randint(0,len(leveldataunit)-1)

        with open("Data/Play.html","r") as html:
            html=html.read()

            cur = leveldata[int(index)]
            # RealLevelID, Levelname, Dartcount, Target, Leveldata,
            # Author, Playcount, Completed, Rating
            
            html=html.replace("M_AUTHOR","%s"%cur[5])# Level creator name
            html=html.replace("M_LEVELNAME","%s"%cur[1])# Level name
            html=html.replace("M_LEVELID","%s"%cur[0])# LevelID (Should use this as index for Bloonsworld Archive)
            html=html.replace("M_LEVELDATA","%s"%cur[4])# Basegame2 level data
            html=html.replace("M_DARTS","%s"%cur[2])# Ingame darts to start with
            html=html.replace("M_TARGET","%s"%cur[3])# Ingame pop target
            html=html.replace("M_AUTHORID","123456")# Author user ID
            html=html.replace("M_PLAYCOUNT","%s"%cur[6])# Playcount before archival
            html=html.replace("M_RATING","%s"%cur[8])# level rating
            html=html.replace("M_LONGDESC","%s"%message) # Long description below game in Play.html
            html=html.replace("M_COPYRIGHT","Bloonsworld Archive version v1.00") # Copyright text at bottom of page
            
                              
            if len(self.savedata("Completed","read",encryption=True)) is not 0:
                if Bad_level_filter == "true":
                    levels_completed=[]
                    for i in self.savedata("Completed","read",encryption=True):
                        if i in leveldataIDS:
                            levels_completed.append(i)
                else:
                    levels_completed = self.savedata("Completed","read",encryption=True)
            else:
                levels_completed = "0"
            html=html.replace("M_COMPLETED","%s"%len(levels_completed))
            #html=html.replace("M_COMPLETED","idk")

            
            html=html.replace("M_DATABASELEN","%s"%len(leveldataunit))
            if Random_levels == "false":
                progmode = "Progress mode enabled<br>"
            else:
                progmode = ""
            html=html.replace("M_PROGMODE","%s"%progmode)
            if Bad_level_filter == "true":
                afilter = "Bad level filter enabled<br>"
            else:
                afilter = ""
            html=html.replace("M_AFILTER","%s"%afilter)

            if "M_" in html:
                tr("99% chance of M_ leftovers in html. Ignoring.")
            return html
    
    def _set_headers(self,mimetype):
        self.send_response(200)
        self.send_header('Content-type', mimetype)
        self.end_headers()

    def do_GET(self):
        mimetype = self.mime(self.path)
        self._set_headers(mimetype)
        try:
            if len(self.path[1:])==0:
                with open("Data/Redirect.html","rb") as redir:
                    self.wfile.write(redir.read())

            elif self.path.endswith("/cmd"):
                name = self.path.split("/")[-2].replace("%20"," ")
                results = self.search(str(name), "author", strict=True)
                tr("Results: %s"%results)
                search_html = self.makesearch(results,"author")
                self.wfile.write(search_html)

            elif self.path.endswith("/pick"):
                levelid = self.path.split("/")[-2]
                self.wfile.write(self.makeplay(self, index=levelid))

            else:
                with open(self.path[1:],"rb") as req:
                    if "Play.html" in self.path:
                        self.wfile.write(self.makeplay(self))
                    else:
                        self.wfile.write(req.read())
        except IOError as error:
            tr(error)

    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        self._set_headers("text/html")
        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        postdata = self.postdict(post_body)
        try:
            if "search=" in post_body:
                if "wanttype=" in post_body: # Handler for level / index searches
                    postdata["search"] = postdata["search"].replace("+"," ") # fix for spaces
                    tr("Search: %s\nwanttype: %s"%(postdata["search"],postdata["wanttype"]))
                    if postdata["wanttype"] == "index":
                        self.wfile.write(self.makeplay(int(postdata["search"])))
                    elif postdata["wanttype"] == "levelname":
                        results = self.search(str(postdata["search"]), "levelname", strict=False)
                        tr("Results: %s"%results)
                        search_html = self.makesearch(results,"levelname")
                        self.wfile.write(search_html)
                else:
                    tr("wanttype= is not inside post_body")

            if "rating=" in post_body: # Save rating when received by user
                rating = postdata["rating"]
                levelID = postdata["levelID"]
                self.savedata("Ratings","add","%s|%s"%(levelID,rating))
                tr("Rating: %s received for level id: %s"%(rating,levelID))
                
            elif "level%5Fnum" in post_body:
                tr("Completed level: %s"%postdata["level%5Fnum"])
                self.savedata("Completed","add",str(postdata["level%5Fnum"]),encryption=True)
            
        except Exception as a:
            tr(a)
            tr("Pretty severe error in do_POST(self) inside first try block.")

            
    def log_message(self, format, *args): # let this only do return to stop massive http message spam
        #print(format%args)
        return
        
    
def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    tr("Local server started.")
    httpd.serve_forever()


run(port=int(Server_port))
