# -*- coding: utf-8 -*-


__author__ = 'jun'

import sqlite3
import datetime

class DBConn:
    def __init__(self):
        self.conn = sqlite3.connect('envo.db')
        self.cur = self.conn.cursor()
        # self.check()

    def startup(self):
        self.cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='app_stat'");
        print("STEP 1.....")
        # if self.cur.fetchone()[0] == 0:
        if True:
            print("app started for the first time, db initializing...")
            print("STEP 2.....")

            self.cur.execute("DROP TABLE IF EXISTS app_stat")
            
            #create necessary tables
            self.cur.execute('''
                CREATE TABLE app_stat(
                    firstStartUp TEXT,
                    configured  INTEGER,
                    synced  INTEGER,
                    last_sync TEXT)
                    ''')

            self.cur.execute("DROP TABLE IF EXISTS stores")
            self.cur.execute("DROP TABLE IF EXISTS programs")
            self.cur.execute("DROP TABLE IF EXISTS tracks")

            self.cur.execute('''
                CREATE TABLE stores(
                    id INTEGER PRIMARY KEY,
                    sid TEXT,
                    sname TEXT,
                    sreference TEXT,
                    deviceId    TEXT,
                    channelId   TEXT,
                    channelName TEXT,
                    brandId TEXT,
                    brandName   TEXT,
                    lastSync    TEXT,
                    license     TEXT
                )
            ''')

            self.cur.execute('''
                CREATE TABLE programs(
                    id INTEGER PRIMARY KEY,
                    pid TEXT,
                    pname TEXT,
                    pstartDate  TEXT,
                    pendDate    TEXT,
                    totalTracks INTEGER,
                    brandId TEXT,
                    brandName   TEXT,
                    channelId   TEXT,
                    valid   INTEGER,
                    exported    INTEGER,
                    trackList   BLOB,
                    trackListRemote BLOB
                )
            ''')

            self.cur.execute('''
                CREATE TABLE tracks(
                    id INTEGER PRIMARY KEY,
                    tid TEXT,
                    name TEXT,
                    duration  REAL,
                    path    TEXT,
                    cached  INTEGER,
                    valid   INTEGER,
                    format  TEXT,
                    last_sync   TEXT
                )
            ''')


            et = (datetime.datetime.utcnow(),0,0,'')

            self.cur.execute("INSERT INTO app_stat VALUES (?,?,?,?)",et)
            self.conn.commit()

    def getProgramList(self):
        res = self.cur.execute("SELECT pid FROM programs").fetchall()
        if len(res) > 0:
            return res
        else:
            return None

    def getProgramListMeta(self):
        res = self.cur.execute("SELECT pid,pname,pstartDate,pendDate,exported FROM programs").fetchall()
        if len(res) > 0:
            return res
        else:
            return None

    def addPrograms(self,pgmList):
        res = self.cur.executemany("INSERT INTO programs (pid,pname,pstartDate,pendDate,channelId,trackList,trackListRemote) VALUES (?,?,?,?,?,?,?)",pgmList)
        self.conn.commit()
        print('Program update DONE....')

    def getProgram(self,pid=None):

        res = self.cur.execute("SELECT pid,pname FROM programs WHERE pid=?",pid).fetchall()
        if len(res) > 0:
            print('PROGRAM in local')
            return res[0]
        else:
            return None

    #return all tracks if no pid is provided
    def getProgramTrackList(self,pid=None):
        if pid is not None:
            res = self.cur.execute("SELECT pid,pname,pstartDate,pendDate,brandName,channelId,trackListRemote FROM programs WHERE pid=?",(pid,)).fetchone()

            if len(res) > 0:
                print('FOUND program detail with programId')
                return res
            else:
                return None
        else:
            return None

    def getProgramTrackForExport(self,pid=None):
        if pid is not None:
            res = self.cur.execute("SELECT pid,pname,brandName,trackList,trackListRemote FROM programs WHERE pid=?",(pid,)).fetchone()

            if len(res) > 0:
                print('FOUND program for export with programId')
                return res
            else:
                return None
        else:
            return None

    def updateProgramExportStatus(self,pid=None):
        if pid is not None:
            self.cur.execute("UPDATE programs SET exported=1 WHERE pid = ?",(pid,))
            self.conn.commit()


    def getTrackById(self,tid=None):
        if tid is not None:
            res = self.cur.execute("SELECT tid,name,duration,cached FROM tracks WHERE tid=?",(tid,)).fetchone()
            if len(res) > 0 :
                # print("TRACK FOUND")
                return res
        else:
            return None

    def updateTrackCacheStatusById(self,tid=None):
        if tid is not None:
            print('Updating caching status for '+tid)
            self.cur.execute("UPDATE tracks SET cached = 1 WHERE tid = ?",(tid,))
            self.conn.commit()

    def getTrackList(self):
        res = self.cur.execute("SELECT tid from tracks").fetchall()
        if len(res) > 0 :
            # print("TRACK FOUND")
            return res
        else:
            return None

    def getTrackCacheStatus(self,tid=None):
        if tid is not None:
            res = self.cur.execute("SELECT cached FROM tracks WHERE tid = ?",(tid,)).fetchall()
            if res is not None and len(res)>0:
                return res

    def addTracks(self,tracks):

        res = self.cur.executemany("INSERT INTO tracks(tid,name,duration,cached,valid) VALUES (?,?,?,?,?)",tracks)
        self.conn.commit()
        print("Tracks update done...")

    def getStoreById(self,sid=None):
        pass

    def getStoresByChannelId(self,cid=None):
        res = self.cur.execute("SELECT * FROM stores WHERE channelId=?",(cid,)).fetchall()
        if len(res)>0:
            return res
        else:
            return None

    def clearStores(self,cid=None):
        '''
        Remove all stores list of a channel
        :param cid:
        :return:
        '''
        self.cur.execute("DELETE FROM stores WHERE channelId=?",(cid,))
        self.conn.commit()

    def addStores(self,stores=None):

        res = self.cur.executemany("INSERT INTO stores "
                                   "(sid,sname,sreference,deviceId,channelId,channelName,brandId,brandName,license) "
                                   "VALUES (?,?,?,?,?,?,?,?,?)",stores)
        self.conn.commit()
        print('Stores update DONE....')

    def check(self):
        self.cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='app_stat'");
        if self.cur.fetchone()[0] != 0:
            print('Database exist.')
        else:
            print('Initializing....')
            self.startup()
            print('Initializing OK...Database and tables created.')

    def clear(self):
        print('Initializing....')
        self.startup()
        print('Initializing OK...Database and tables created.')


if __name__ == '__main__':
    db = DBConn()
    db.startup()
    db.check()