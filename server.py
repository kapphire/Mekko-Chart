#!/usr/bin/python 
# -*- coding: UTF-8 -*-# enable debugging 
from tornado.ioloop import IOLoop, PeriodicCallback
import tornado.ioloop
import tornado.web
import tornado.websocket

import json
import os
import csv
import sqlite3

class MekkoDB:
    
    def get_cols(self):
        return json.load(open('cols.json'))
        
    def update_index(self, x, y):
        self.conn = sqlite3.connect('test.db')
        self.cur = self.conn.cursor()  
        self.cur.execute("DROP INDEX IF EXISTS mekko;")
        self.cur.execute("CREATE INDEX mekko on data(%s,%s)" % (x,y))
        self.conn.commit()      
        self.conn.close()          
        
    def save_cols(self, cols):
        json.dump(cols, open('cols.json', 'w'))   
        
        self.update_index(cols['x'], cols['y'])         
        
    def update_cols(self, x, y, v, region_type, ctm_type):
        cols = self.get_cols()
        cols['x'] = x
        cols['y'] = y
        cols['v'] = v
        
        cols['region_type'] = region_type
        cols['ctm_type'] = ctm_type
        json.dump(cols, open('cols.json', 'w'))
        
        self.update_index(x, y)
       
    
    def get_data(self):
        cols = self.get_cols()

        x = cols['xs'][cols['x']]
        y = cols['ys'][cols['y']]
        v = cols['vs'][cols['v']]
        conn = sqlite3.connect('test.db')
        cur = conn.cursor()
        cur.execute("""
            SELECT %s, %s, SUM( %s )
            FROM data
            GROUP BY %s , %s
        """ % ( x, y, v, x, y))
        data = {'Total': 0}
        rows = cur.fetchall()
        for row in rows:
            x = row[0]
            y = row[1]
            
            data['Total']+=row[2]
            if x not in data:
                data[x] = {'Total': 0}
                
            data[x]['Total']+=row[2]
            data[x][y]=row[2]   

        cut_type = cols['xs'][cols['x']]
        region = cols['ys'][cols['y']]

        crl_x = cols['customer_type'][cols['ctm_type']]     #Corporate
        crl_y = cols['region'][cols['region_type']]         #Germany

        collateral = cols['collateral'][0]
        collateral_type = cols['collateral'][1]

        cur.execute("""
            SELECT %s, %s, %s, %s, SUM( %s )
            FROM data
            WHERE %s='%s' AND %s='%s'
            GROUP BY %s , %s , %s , %s
        """ % ( cut_type, region, collateral, collateral_type, v, cut_type, crl_x, region, crl_y, cut_type, region, collateral, collateral_type))

        details = cur.fetchall()

        net_data = {"data": "", "details": ""}

        net_data['data'] = data
        net_data['details'] = details

        return net_data

    def get_data_details(self, x, y, v,region_type, ctm_type):

        cols = self.get_cols()
        x = cols['xs'][x]               #customer_type
        y = cols['ys'][y]               #Region
        v = cols['vs'][v]               #year

        region_type = cols['region'][region_type]           #Germany
        ctm_type = cols['customer_type'][ctm_type]          #Corporate

        collateral = cols['collateral'][0]
        collateral_type = cols['collateral'][1]

        conn = sqlite3.connect('test.db')
        cur = conn.cursor()

        cur.execute("""
            SELECT %s, %s, %s, %s, SUM( %s )
            FROM data
            WHERE %s='%s' AND %s='%s'
            GROUP BY %s , %s , %s , %s
        """ % ( x, y, collateral, collateral_type, v, x, ctm_type, y, region_type, x, y, collateral, collateral_type))

        details = cur.fetchall()
        

        return details
    

DB = MekkoDB()

class ConnHandler(tornado.websocket.WebSocketHandler):
    
    
    def is_number(self,s):
        """ Returns True is string is a number. """
        try:
            float(s.replace(" ", ""))
            return True
        except ValueError:
            return False  

    def send_data(self, data):
        data = json.dumps(data)
        self.write_message(data)

    def process_rows(self, rows):
        for row in rows:
            self.rownum+=1
            for x in range(self.colnum):
                if self.is_number(row[x]):
                    self.nums[x] += 1
        self.cur.executemany("INSERT INTO data VALUES (%s);" % ", ".join(['?']*self.colnum), 
                             rows)
        self.progress+=1
        self.send_data({'type':'progress', 'progress': self.progress})
        self.check_finish()

    def on_message(self, data):        
        data = json.loads(data)

        if data['type']=='start':
            cols = data['cols']
            self.cols = [c.replace(" ", "_") for c in cols]

            self.colnum = len(self.cols)
            self.nums = [0] * self.colnum
            self.total = data['total']
            self.filename = data['filename']
            self.progress = 0
            self.rownum = 0
            
            if os.path.exists('test.db'):
                os.rename('test.db','old.db')
                
            self.conn = sqlite3.connect('test.db')
            self.cur = self.conn.cursor()                        
            self.cur.execute("CREATE TABLE data (%s);" % ','.join(self.cols))
            
            print "start"
            self.process_rows(data['rows'])
            
            
        if data['type']=='rows':
            self.process_rows(data['rows'])
                                 
            
                        
    def check_finish(self):
        if self.progress == self.total:
            cols = {'xs':[],'ys':[],'vs':[]}
            for x in range(self.colnum):
                if self.nums[x] == self.rownum:
                    cols['vs'].append(self.cols[x])
                else:
                    cols['xs'].append(self.cols[x])
                    cols['ys'].append(self.cols[x])
            
            cols['x'] = 0
            cols['y'] = 1
            cols['v'] = 0
            
            cols['f'] = self.filename

            cols['collateral'] = ["Collateral", "Collateral_type"]
            cols['region'] = ["Germany", "Nordics", "Sweden", "UK"]
            cols['customer_type'] = ["Corporate", "Financial institutions", "Retail", "SME", "States"]

            cols['region_type'] = 0
            cols['ctm_type'] = 0

            self.conn.commit()
            self.conn.close()  
            
            DB.save_cols(cols)
            data = DB.get_data()
            self.send_data({'type':'cols', 'cols': cols, 'data': data})
            
        
    def check_origin(self, origin):
        return True


class ColsHandler(tornado.web.RequestHandler):
    def get(self):
        try:        
            x = int(self.get_argument('x'))
            y = int(self.get_argument('y'))
            v = int(self.get_argument('v'))
            region_type = 1
            ctm_type = 1
            
            DB.update_cols(x,y,v,region_type,ctm_type)
            data = DB.get_data()            
            
            self.write(json.dumps({'success': 1, 'data': data}))
        except Exception as e:
            raise e
            self.write(json.dumps({'success': 0}))


class UploadHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            data = DB.get_data()
            cols = DB.get_cols()
        except Exception as e:
            data = 0
            cols = 0
        self.render("upload.html", data=json.dumps(data), cols=json.dumps(cols))
        
class AjaxHandler(tornado.web.RequestHandler):
    def get(self):
        try:        
            x = int(self.get_argument('x'))
            y = int(self.get_argument('y'))
            v = int(self.get_argument('v'))
            
            region_type = int(self.get_argument('region_type'))
            ctm_type = int(self.get_argument('ctm_type'))

            DB.update_cols(x,y,v,region_type,ctm_type)
            data = DB.get_data_details(x,y,v,region_type,ctm_type)
            self.write(json.dumps({'success': 1, 'data': data}))
        except Exception as e:
            raise e
            self.write(json.dumps({'success': 0}))        


args={}
settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}
app = tornado.web.Application([
    (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": ""}),
    (r'/cols', ColsHandler),
    (r'/ajax', AjaxHandler),
    (r'/', UploadHandler),
    (r'/conn', ConnHandler)],
    debug=True, **settings)

app.listen(11000)
IOLoop.instance().start()
